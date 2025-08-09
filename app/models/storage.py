import json, os, threading
from typing import List, Dict, Any

class JsonStorage:
    def __init__(self, path: str):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(base_dir, '..', path)
        self.path = os.path.abspath(self.path)
        self._lock = threading.Lock()
        dir_path = os.path.dirname(self.path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        if not os.path.exists(self.path) or os.path.getsize(self.path) == 0:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        print('[DEBUG] path : ', self.path)

    def _read(self) -> List[Dict[str, Any]]:
        with self._lock:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write(self, data: List[Dict[str, Any]]):
        with self._lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def all(self) -> List[Dict[str, Any]]:
        return self._read()

    def get_by_id(self, _id: str):
        return next((x for x in self._read() if x["id"] == _id), None)

    def create(self, obj: Dict[str, Any]):
        data = self._read()
        data.append(obj)
        self._write(data)
        return obj

    def update(self, _id: str, patch: Dict[str, Any]):
        data = self._read()
        for i, x in enumerate(data):
            if x["id"] == _id:
                x.update(patch)
                data[i] = x
                self._write(data)
                return x
        return None

    def delete(self, _id: str):
        data = self._read()
        new_data = [x for x in data if x["id"] != _id]
        self._write(new_data)
        return len(new_data) != len(data)
