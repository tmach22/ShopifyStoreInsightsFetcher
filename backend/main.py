from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from store import router as store_router

app = FastAPI(
    title="Shopify Store Insights-Fetcher",
    description="Extracts brand insights from a Shopify URL without the official API",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(store_router, prefix="/api/store", tags=["Shopify Insights"])