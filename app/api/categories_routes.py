"""Category CRUD (stubs until persistence is wired)."""

from fastapi import APIRouter

from app.db.models import Category, CategoryCreate, CategoryUpdate

categories_router = APIRouter(prefix="/categories")


@categories_router.get("")
async def list_categories() -> list[Category]:
    return []


@categories_router.post("", response_model=Category, status_code=201)
async def create_category(category_create: CategoryCreate) -> Category:
    return []


@categories_router.get("/{category_id}", response_model=Category)
async def get_category(category_id: str) -> Category:
    return []


@categories_router.patch("/{category_id}", response_model=Category)
async def update_category(category_id: str, category_update: CategoryUpdate) -> Category:
    return []


@categories_router.delete("/{category_id}")
async def delete_category(category_id: str) -> dict[str, str]:
    return []
