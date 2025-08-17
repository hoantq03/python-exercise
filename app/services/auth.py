import hashlib, uuid

from app.models.storage import JsonStorage
import os
from dotenv import load_dotenv


load_dotenv()


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

class AuthService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def ensure_admin_seed(self):
        # Lấy tất cả người dùng, sau đó lọc ra những ai có role là 'staff'
        all_users = self.storage.all()
        admin_users = [user for user in all_users if user.get("role") == "administrator"]
        if not admin_users:
            admin_username =  os.getenv("ADMIN_USERNAME", "administrator").lower()
            admin_password = os.getenv("ADMIN_PASSWORD", "Strongp@ssword123").lower()
            self.storage.create({
                "id": str(uuid.uuid4()),
                "username": admin_username,
                "password_hash": hash_password(admin_password),
                "role": "administrator"
            })

    def login(self, username: str, password: str):
        hpw = hash_password(password)
        for u in self.storage.all():
            if u["username"] == username and u["password_hash"] == hpw:
                return u
        return None

    def authorize(self, user: dict, required_roles):
        return user and user.get("role") in required_roles
