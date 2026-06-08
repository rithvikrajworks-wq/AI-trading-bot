# backend/app/auth/models/user.py

"""User model definition for authentication.
Stored in the same SQLite DB used for memory.
"""

import uuid
import time

class User:
    def __init__(self, email: str, hashed_password: str):
        self.id = uuid.uuid4().hex
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = time.time()

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "created_at": self.created_at,
        }
