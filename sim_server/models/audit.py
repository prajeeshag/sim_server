from enum import StrEnum

from tortoise import fields, models


class LoginResult(StrEnum):
    SUCCESS = "success"
    WRONG_PASSWORD = "wrong_password"
    USER_NOT_FOUND = "user_not_found"
    ACCOUNT_LOCKED = "account_locked"
    UNVERIFIED = "unverified"


class LoginAttempt(models.Model):
    id = fields.UUIDField(primary_key=True)
    email = fields.CharField(max_length=255)  # not FK — log even unknown emails
    ip_address = fields.CharField(max_length=45)  # supports IPv6
    user_agent = fields.CharField(max_length=500, null=True)
    result = fields.CharEnumField(LoginResult)
    attempted_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "login_attempts"
        indexes = [("email", "attempted_at"), ("ip_address", "attempted_at")]


class EventType(StrEnum):
    REGISTERED = "registered"
    EMAIL_VERIFIED = "email_verified"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    OAUTH_LINKED = "oauth_linked"
    OAUTH_UNLINKED = "oauth_unlinked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    ACCOUNT_DELETED = "account_deleted"
    ACCOUNT_RESTORED = "account_restored"


class UserEvent(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="events", null=True, on_delete=fields.SET_NULL
    )
    event_type = fields.CharEnumField(EventType)
    ip_address = fields.CharField(max_length=45, null=True)
    user_agent = fields.CharField(max_length=500, null=True)
    metadata = fields.JSONField(
        null=True
    )  # e.g. {"role": "editor", "changed_by": "..."}
    occurred_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_events"
        indexes = [("user_id", "occurred_at"), ("event_type", "occurred_at")]
