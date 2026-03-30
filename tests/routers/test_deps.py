import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from jose import JWTError

from sim_server.deps import get_current_user


def _make_user(is_active=True):
    user = MagicMock()
    user.is_active = is_active
    return user


async def _call(token: str) -> object:
    return await get_current_user(token=token)


class TestValidToken:
    async def test_returns_user(self, mocker):
        user = _make_user()
        mocker.patch("sim_server.deps.decode_token", return_value={"type": "access", "sub": str(uuid.uuid4())})
        mocker.patch("sim_server.deps.User.get_or_none", AsyncMock(return_value=user))

        result = await _call("valid-token")

        assert result is user

    async def test_inactive_user_raises_403(self, mocker):
        mocker.patch("sim_server.deps.decode_token", return_value={"type": "access", "sub": str(uuid.uuid4())})
        mocker.patch("sim_server.deps.User.get_or_none", AsyncMock(return_value=_make_user(is_active=False)))

        with pytest.raises(HTTPException) as exc:
            await _call("valid-token")
        assert exc.value.status_code == 403

    async def test_user_not_found_raises_403(self, mocker):
        mocker.patch("sim_server.deps.decode_token", return_value={"type": "access", "sub": str(uuid.uuid4())})
        mocker.patch("sim_server.deps.User.get_or_none", AsyncMock(return_value=None))

        with pytest.raises(HTTPException) as exc:
            await _call("valid-token")
        assert exc.value.status_code == 403


class TestInvalidToken:
    async def test_jwt_error_raises_401(self, mocker):
        mocker.patch("sim_server.deps.decode_token", side_effect=JWTError("bad"))

        with pytest.raises(HTTPException) as exc:
            await _call("garbage")
        assert exc.value.status_code == 401

    async def test_refresh_token_type_raises_401(self, mocker):
        mocker.patch("sim_server.deps.decode_token", return_value={"type": "refresh", "sub": str(uuid.uuid4())})

        with pytest.raises(HTTPException) as exc:
            await _call("refresh-token")
        assert exc.value.status_code == 401

    async def test_missing_sub_raises_401(self, mocker):
        mocker.patch("sim_server.deps.decode_token", return_value={"type": "access"})

        with pytest.raises(HTTPException) as exc:
            await _call("no-sub-token")
        assert exc.value.status_code == 401

    async def test_invalid_uuid_sub_raises_401(self, mocker):
        mocker.patch("sim_server.deps.decode_token", return_value={"type": "access", "sub": "not-a-uuid"})

        with pytest.raises(HTTPException) as exc:
            await _call("bad-uuid-token")
        assert exc.value.status_code == 401

    async def test_401_includes_www_authenticate_header(self, mocker):
        mocker.patch("sim_server.deps.decode_token", side_effect=JWTError("bad"))

        with pytest.raises(HTTPException) as exc:
            await _call("garbage")
        assert "WWW-Authenticate" in exc.value.headers
