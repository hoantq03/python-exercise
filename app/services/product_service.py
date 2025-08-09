import uuid

from app.models.storage import JsonStorage


class ProductService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def list(self, keyword: str = ""):
        data = self.storage.all()
        if keyword:
            k = keyword.lower()
            data = [p for p in data if k in p["name"].lower() or k in p["sku"].lower()]
        return data

    def create(self, payload: dict):
        payload["id"] = str(uuid.uuid4())
        payload["stock"] = int(payload.get("stock", 0))
        payload["price"] = float(payload.get("price", 0))
        return self.storage.create(payload)

    def update(self, _id: str, payload: dict):
        if "stock" in payload: payload["stock"] = int(payload["stock"])
        if "price" in payload: payload["price"] = float(payload["price"])
        return self.storage.update(_id, payload)

    def delete(self, _id: str):
        return self.storage.delete(_id)
