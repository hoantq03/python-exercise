from dataclasses import dataclass, field

@dataclass
class Category:
    id: str
    categoryId: int
    categoryName: str
    categoryUri: str
    created_at: str = ""
    updated_at: str = ""
