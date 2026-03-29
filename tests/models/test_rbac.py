import pytest
from tortoise.exceptions import IntegrityError

from sim_server.models.rbac import Permission, Role
from sim_server.models.user import User


async def make_user(email="rbac@example.com") -> User:
    return await User.create(email=email)


class TestPermission:
    async def test_create(self):
        perm = await Permission.create(codename="post:delete")
        assert perm.codename == "post:delete"

    async def test_codename_unique(self):
        await Permission.create(codename="user:ban")
        with pytest.raises(IntegrityError):
            await Permission.create(codename="user:ban")


class TestRole:
    async def test_create(self):
        role = await Role.create(name="admin")
        assert role.name == "admin"

    async def test_name_unique(self):
        await Role.create(name="editor")
        with pytest.raises(IntegrityError):
            await Role.create(name="editor")

    async def test_assign_permission(self):
        role = await Role.create(name="moderator")
        perm = await Permission.create(codename="comment:delete")

        await role.permissions.add(perm)

        perms = await role.permissions.all()
        assert len(perms) == 1
        assert perms[0].codename == "comment:delete"

    async def test_assign_multiple_permissions(self):
        role = await Role.create(name="supermod")
        p1 = await Permission.create(codename="post:edit")
        p2 = await Permission.create(codename="post:delete")
        p3 = await Permission.create(codename="user:view")

        await role.permissions.add(p1, p2, p3)

        assert await role.permissions.all().count() == 3

    async def test_remove_permission(self):
        role = await Role.create(name="junior-mod")
        perm = await Permission.create(codename="report:view")
        await role.permissions.add(perm)

        await role.permissions.remove(perm)

        assert await role.permissions.all().count() == 0


class TestUserRoles:
    async def test_assign_role_to_user(self):
        user = await make_user()
        role = await Role.create(name="viewer")

        await user.roles.add(role)

        roles = await user.roles.all()
        assert len(roles) == 1
        assert roles[0].name == "viewer"

    async def test_user_multiple_roles(self):
        user = await make_user(email="multi@example.com")
        r1 = await Role.create(name="writer")
        r2 = await Role.create(name="reviewer")

        await user.roles.add(r1, r2)

        assert await user.roles.all().count() == 2

    async def test_remove_role_from_user(self):
        user = await make_user(email="remove-role@example.com")
        role = await Role.create(name="temp-role")
        await user.roles.add(role)

        await user.roles.remove(role)

        assert await user.roles.all().count() == 0

    async def test_role_shared_across_users(self):
        role = await Role.create(name="member")
        u1 = await make_user(email="u1@example.com")
        u2 = await make_user(email="u2@example.com")

        await u1.roles.add(role)
        await u2.roles.add(role)

        users = await role.users.all()  # type: ignore
        assert len(users) == 2
