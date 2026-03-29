from tortoise import fields, models


class Permission(models.Model):
    codename = fields.CharField(
        max_length=100, unique=True
    )  # "post:delete", "user:ban"


class Role(models.Model):
    name = fields.CharField(max_length=50, unique=True)
    permissions = fields.ManyToManyField("models.Permission")
