from enum import StrEnum

from tortoise import fields, models


class RefreshToken(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="refresh_tokens", on_delete=fields.CASCADE
    )
    token_hash = fields.CharField(max_length=255, unique=True)  # store hash, not raw
    expires_at = fields.DatetimeField()
    revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)


class TokenPurpose(StrEnum):
    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


class VerificationToken(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField(
        "models.User", related_name="verification_tokens", on_delete=fields.CASCADE
    )
    token_hash = fields.CharField(max_length=255, unique=True)
    purpose = fields.CharEnumField(enum_type=TokenPurpose)
    expires_at = fields.DatetimeField()
    used_at = fields.DatetimeField(null=True)  # mark as used rather than delete
