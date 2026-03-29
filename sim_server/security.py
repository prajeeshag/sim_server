from pwdlib import PasswordHash

pwd_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> tuple[bool, str | None]:
    """Returns (is_valid, new_hash_if_needs_rehash)."""
    ok, new_hash = pwd_hasher.verify_and_update(plain, hashed)
    return ok, new_hash
