from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryResponse, CategoryListResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=CategoryListResponse, summary="Get Active Categories")
def get_categories(db: Session = Depends(get_db)):
    categories = (
        db.query(Category)
        .filter(Category.is_active == True)
        .order_by(Category.display_order.asc(), Category.name.asc())
        .all()
    )
    return CategoryListResponse(
        total=len(categories),
        categories=categories,
    )
