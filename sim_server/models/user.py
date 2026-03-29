from tortoise import fields, models


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

    # Relations
    roles = fields.ManyToManyField("models.Role", related_name="users")
    oauth_accounts = fields.ReverseRelation["OAuthAccount"]

    class Meta:
        table = "users"


class UserProfile(models.Model):
    user = fields.OneToOneField(
        "models.User",
        related_name="profile",
        primary_key=True,
        on_delete=fields.CASCADE,
    )
    display_name = fields.CharField(max_length=100, null=True)
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
        "models.User",
        related_name="oauth_accounts",
        on_delete=fields.CASCADE,
    )
    provider = fields.CharField(max_length=50)  # "google", "github", etc.
    provider_user_id = fields.CharField(max_length=255)
    access_token = fields.TextField(null=True)  # optional, if you need API access
    expires_at = fields.DatetimeField(null=True)

    class Meta:
        unique_together = (("provider", "provider_user_id"),)
