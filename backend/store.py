from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from services.extractor import extract_brand_insights

class StoreRequest(BaseModel):
    website_url: HttpUrl

router = APIRouter()

@router.post("/extract-brand-insights")
async def extract_insights(request: StoreRequest):
    try:
        insights = extract_brand_insights(str(request.website_url))
        return insights
    except ValueError as ve:
        raise HTTPException(status_code=401, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")