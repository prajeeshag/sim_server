import uuid

from sim_server.models.audit import EventType, LoginAttempt, LoginResult, UserEvent
from sim_server.models.user import User


async def make_user(email="audit@example.com") -> User:
    return await User.create(id=uuid.uuid4(), email=email)


class TestLoginAttempt:
    async def test_create_success(self):
        attempt = await LoginAttempt.create(
            id=uuid.uuid4(),
            email="user@example.com",
            ip_address="192.168.1.1",
            result=LoginResult.SUCCESS,
        )
        assert attempt.result == LoginResult.SUCCESS
        assert attempt.user_agent is None

    async def test_create_failed(self):
        attempt = await LoginAttempt.create(
            id=uuid.uuid4(),
            email="unknown@example.com",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
            result=LoginResult.WRONG_PASSWORD,
        )
        assert attempt.result == LoginResult.WRONG_PASSWORD

    async def test_no_user_fk_logs_unknown_email(self):
        # LoginAttempt has no FK — unknown emails are recorded
        attempt = await LoginAttempt.create(
            id=uuid.uuid4(),
            email="nobody@example.com",
            ip_address="1.2.3.4",
            result=LoginResult.USER_NOT_FOUND,
        )
        fetched = await LoginAttempt.get(id=attempt.id)
        assert fetched.email == "nobody@example.com"

    async def test_ipv6_address(self):
        attempt = await LoginAttempt.create(
            id=uuid.uuid4(),
            email="ipv6@example.com",
            ip_address="2001:db8::1",
            result=LoginResult.SUCCESS,
        )
        assert attempt.ip_address == "2001:db8::1"


class TestUserEvent:
    async def test_create_with_user(self):
        user = await make_user()
        event = await UserEvent.create(
            id=uuid.uuid4(),
            user=user,
            event_type=EventType.REGISTERED,
        )
        assert event.event_type == EventType.REGISTERED

    async def test_create_without_user(self):
        event = await UserEvent.create(
            id=uuid.uuid4(),
            user=None,
            event_type=EventType.LOGIN_FAILED,
            ip_address="1.2.3.4",
        )
        assert event.user_id is None

    async def test_with_metadata(self):
        user = await make_user(email="meta@example.com")
        event = await UserEvent.create(
            id=uuid.uuid4(),
            user=user,
            event_type=EventType.ROLE_ASSIGNED,
            metadata={"role": "editor", "changed_by": "admin"},
        )
        fetched = await UserEvent.get(id=event.id)
        assert fetched.metadata["role"] == "editor"

    async def test_set_null_on_user_delete(self):
        user = await make_user(email="deleteme@example.com")
        event = await UserEvent.create(
            id=uuid.uuid4(),
            user=user,
            event_type=EventType.ACCOUNT_DELETED,
        )
        event_id = event.id

        await user.delete()

        # audit record survives, FK is nulled
        surviving = await UserEvent.get(id=event_id)
        assert surviving.user_id is None

    async def test_multiple_events_set_null_on_user_delete(self):
        user = await make_user(email="multi-event@example.com")
        ids = []
        for etype in [EventType.LOGIN_SUCCESS, EventType.PASSWORD_CHANGED, EventType.LOGOUT]:
            e = await UserEvent.create(id=uuid.uuid4(), user=user, event_type=etype)
            ids.append(e.id)

        await user.delete()

        for eid in ids:
            e = await UserEvent.get(id=eid)
            assert e.user_id is None
