import uuid

from app.models.storage import JsonStorage


class CustomerService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def list(self, keyword: str = ""):
        data = self.storage.all()
        if keyword:
            k = keyword.lower()
            data = [c for c in data if k in c["name"].lower() or k in c["phone"]]
        return data

    def create(self, payload: dict):
        payload["id"] = str(uuid.uuid4())
        return self.storage.create(payload)

    def update(self, _id: str, payload: dict):
        return self.storage.update(_id, payload)

    def delete(self, _id: str):
        return self.storage.delete(_id)
