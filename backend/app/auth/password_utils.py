# backend/app/auth/password_utils.py

"""Utility functions for password hashing and verification using passlib.
"""

from passlib.context import CryptContext

# Use bcrypt algorithm, standard for production security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password.

    Args:
        password: Plaintext password provided by the user.
    Returns:
        A bcrypt hash string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Returns True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)
