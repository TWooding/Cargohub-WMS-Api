from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

_hasher = PasswordHasher()  # Argon2id; parameters zitten in de hash-string
DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify(hash_: str, password: str) -> bool:
    try:
        return _hasher.verify(hash_, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hash_: str) -> bool:
    return _hasher.check_needs_rehash(hash_)


def validate_new_password(password: str, min_length: int) -> None:
    if len(password) < min_length:
        raise ValueError(f"wachtwoord moet minimaal {min_length} tekens zijn")
