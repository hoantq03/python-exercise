import uuid, datetime

from app.models.storage import JsonStorage


class OrderService:
    def __init__(self, order_store: JsonStorage, product_store: JsonStorage):
        self.order_store = order_store
        self.product_store = product_store

    def list(self, status: str = "", keyword: str = ""):
        data = self.order_store.all()
        if status:
            data = [o for o in data if o["status"] == status]
        if keyword:
            k = keyword.lower()
            data = [o for o in data if k in o["id"].lower() or k in o["customer_id"].lower()]
        return data

    def create(self, customer_id: str, items: list, created_by: str):
        # items: [{product_id, qty}]
        prods = {p["id"]: p for p in self.product_store.all()}
        order_items = []
        total = 0.0
        for it in items:
            p = prods.get(it["product_id"])
            if not p: raise ValueError("Sản phẩm không tồn tại")
            qty = int(it["qty"])
            if qty <= 0: raise ValueError("Số lượng không hợp lệ")
            if p["stock"] < qty: raise ValueError(f"Tồn kho không đủ cho {p['name']}")
            order_items.append({"product_id": p["id"], "qty": qty, "price": float(p["price"])})
            total += qty * float(p["price"])
        oid = str(uuid.uuid4())
        order = {
            "id": oid,
            "customer_id": customer_id,
            "items": order_items,
            "total": round(total, 2),
            "status": "NEW",
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "created_by": created_by
        }
        return self.order_store.create(order)

    def update_status(self, order_id: str, status: str):
        if status not in ("NEW","PAID","CANCELED"):
            raise ValueError("Trạng thái không hợp lệ")
        return self.order_store.update(order_id, {"status": status})

    def delete(self, order_id: str):
        return self.order_store.delete(order_id)

    def fulfill_and_update_stock(self, order_id: str):
        """Khi chuyển PAID: trừ kho."""
        order = self.order_store.get_by_id(order_id)
        if not order: raise ValueError("Đơn hàng không tồn tại")
        if order["status"] != "NEW": return order
        prods = {p["id"]: p for p in self.product_store.all()}
        for it in order["items"]:
            p = prods[it["product_id"]]
            if p["stock"] < it["qty"]:
                raise ValueError(f"Tồn kho thiếu khi duyệt {p['name']}")
        # trừ kho
        for it in order["items"]:
            p = prods[it["product_id"]]
            self.product_store.update(p["id"], {"stock": p["stock"] - it["qty"]})
        return self.order_store.update(order_id, {"status": "PAID"})
