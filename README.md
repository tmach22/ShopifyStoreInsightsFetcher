# 🛒 Shopify Store Insights-Fetcher

### Live ENDPOINT: https://shopifystoreinsightsfetcher.onrender.com/api/store/extract-brand-insights

A FastAPI-powered backend to extract structured brand insights from any Shopify-based store — **without using the official Shopify API**.  
This project uses HTML scraping and LLMs (via OpenRouter) to extract:

- ✅ Full product catalog (including non-standard endpoints)
- ✅ Hero products on homepage
- ✅ privacy policy
- ✅ Contact details (email, phone)
- ✅ Social media links

---

## ⚙️ Features

| Feature                       | Method                   |
|------------------------------|--------------------------|
| Product discovery            | Rule-based + LLM         |
| Hero products                | Rule-based               |
| Privacy & refund policies    | Rule-based               |
| Social & contact info        | Regex & HTML scraping    |
| Generalization               | Works across any Shopify site |
| API                          | REST (FastAPI JSON POST) |

---

## 🚀 Quickstart (Local)

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/shopify-insights-fetcher.git
cd shopify-insights-fetcher
```

2. Create and Activate a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
3. Install Requirements
```bash
pip install -r requirements.txt
```

4. Set OpenRouter API Key
- create .env file with temp api key `OPEN_ROUTER_API_KEY = <your_open_router_api_key>`
- This is uses deepseek v3 free tier model as the LLM, so it won't incurr any costs

5. Run the Server
```bash
cd backend
uvicorn main:app --reload
```
The FastAPI server will be available at:

```bash
http://localhost:8000/docs
```

📦 Example Usage
- Request (JSON)
```json
POST /api/store/extract-brand-insights
{
  "website_url": "https://colourpop.com/"
}
```

- Response (JSON)
```json
{
  "product_catalog": [...],
  "hero_products": [...],
  "privacy_policy": "...",
  "contact_details": ["support@brand.com", "+1-234-567-8901"],
  "social_handles": ["https://instagram.com/brand", "https://tiktok.com/@brand"],
  ...
}
```

🧠 LLMs Used
This project uses the OpenRouter API with models like:
- deepseek/deepseek-chat
