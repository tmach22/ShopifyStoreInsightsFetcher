from fastapi import FastAPI
import os
import sys
from store import router as store_router

app = FastAPI(
    title="Shopify Store Insights-Fetcher",
    description="Extracts brand insights from a Shopify URL without the official API",
    version="1.0.0"
)

app.include_router(store_router, prefix="/api/store", tags=["Shopify Insights"])