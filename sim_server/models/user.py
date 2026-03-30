from enum import StrEnum

from tortoise import fields, models
from tortoise.signals import post_save


class Permission(models.Model):
    codename = fields.CharField(
        max_length=100, unique=True
    )  # "post:delete", "user:ban"


class Role(models.Model):
    name = fields.CharField(max_length=50, unique=True)
    permissions = fields.ManyToManyField("models.Permission")


class User(models.Model):
    id = fields.UUIDField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(
        max_length=255, null=True
    )  # null for OAuth-only users
    is_active = fields.BooleanField(default=False)  # False until email verified
    is_verified = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    roles = fields.ManyToManyField("models.Role", related_name="users")
    oauth_accounts = fields.ReverseRelation["OAuthAccount"]

    class Meta:
        table = "users"


class UserProfile(models.Model):
    user = fields.OneToOneField(
        User,
        related_name="profile",
        primary_key=True,
        on_delete=fields.CASCADE,
    )
    display_name = fields.CharField(max_length=100)
    avatar_url = fields.CharField(max_length=500, null=True)
    bio = fields.TextField(null=True)
    timezone = fields.CharField(max_length=50, default="UTC")
    locale = fields.CharField(max_length=10, default="en")
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_profiles"


class OAuthAccount(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField(
        User,
        related_name="oauth_accounts",
        on_delete=fields.CASCADE,
    )
    provider = fields.CharField(max_length=50)  # "google", "github", etc.
    provider_user_id = fields.CharField(max_length=255)
    access_token = fields.TextField(null=True)
    expires_at = fields.DatetimeField(null=True)

    class Meta:
        unique_together = (("provider", "provider_user_id"),)


class TokenPurpose(StrEnum):
    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


class RefreshToken(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField(
        User,
        related_name="refresh_tokens",
        on_delete=fields.CASCADE,
    )
    token_hash = fields.CharField(max_length=255, unique=True)  # store hash, not raw
    expires_at = fields.DatetimeField()
    revoked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)


class VerificationToken(models.Model):
    id = fields.UUIDField(primary_key=True)
    user = fields.ForeignKeyField(
        User,
        related_name="verification_tokens",
        on_delete=fields.CASCADE,
    )
    token_hash = fields.CharField(max_length=255, unique=True)
    purpose = fields.CharEnumField(enum_type=TokenPurpose)
    expires_at = fields.DatetimeField()
    used_at = fields.DatetimeField(null=True)  # mark as used rather than delete


@post_save(User)
async def create_user_profile(
    sender, instance: User, created: bool, using_db, update_fields
) -> None:
    if created:
        await UserProfile.create(
            user=instance,
            display_name=instance.email.split("@")[0],
        )
