from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class UserModel:

    def __init__(
        self,
        name,
        email,
        password,
        role="buyer",
        user_id=None,
        created_at=None
    ):
        self.user_id = user_id
        self.name = name
        self.email = email.lower().strip()
        self.password = password
        self.role = role
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self, include_password=False):
        user = {
            "userId": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "createdAt": self.created_at
        }

        if include_password:
            user["password"] = self.password

        return user

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password,
            password
        )