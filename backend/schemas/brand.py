from pydantic import BaseModel
from typing import List, Optional

class FAQ(BaseModel):
    question: str
    answer: str

class BrandInsights(BaseModel):
    brand_name: Optional[str]
    product_catalog: List[dict]
    hero_products: List[dict]
    privacy_policy: Optional[str]
    return_policy: Optional[str]
    refund_policy: Optional[str]
    faqs: List[FAQ]
    contact_details: List[dict]
    social_handles: List[str]
    brand_about: Optional[str]
    important_links: List[str]