from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

pwd_hasher = PasswordHash([Argon2Hasher()])


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_hasher.verify(plain, hashed)


def needs_rehash(hashed: str) -> bool:
    return pwd_hasher.check_needs_rehash(hashed)
