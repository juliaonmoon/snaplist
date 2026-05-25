"""
POST /analyze/category — map a listing to its best FB Marketplace leaf category.
Used by the Chrome extension to drive FB's category modal step-by-step.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.category_mapper import map_to_fb_category

router = APIRouter(prefix="/analyze", tags=["analyze"])


class CategorizeRequest(BaseModel):
    title: str
    category: str | None = None
    keywords: list[str] | None = None


class CategorizeResponse(BaseModel):
    path: list[str]
    leaf: str
    confidence: float


@router.post("/category", response_model=CategorizeResponse)
async def categorize(req: CategorizeRequest):
    result = await map_to_fb_category(req.title, req.category, req.keywords)
    if not result:
        raise HTTPException(status_code=404, detail="No matching FB category found")
    return CategorizeResponse(**result)
