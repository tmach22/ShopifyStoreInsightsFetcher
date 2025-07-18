import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from schemas.brand import BrandInsights, FAQ
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

def find_privacy_policy_url(home_html: str, base_url: str) -> str:
    soup = BeautifulSoup(home_html, "lxml")

    keywords = ["privacy", "privacy-policy"]
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(keyword in href for keyword in keywords):
            return urljoin(base_url, href)

    return None

def extract_text_from_policy_page(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    
    # Get main visible content
    policy_section = soup.find("main") or soup.find("body") or soup

    text = policy_section.get_text(separator="\n", strip=True)
    return text  # Limit if needed

def find_faq_candidate_links_with_llm(soup: BeautifulSoup, website_url: str):
    links = list(set(a['href'] for a in soup.find_all('a', href=True)))
    short_html = str(soup)[:5000]

    prompt = f"""
You're a smart web analyst. The following anchor hrefs and HTML are from the homepage of a Shopify store.

Your job is to return a list of URLs (relative or absolute) that most likely lead to a page containing FAQs, Help Center, Customer Service, or similar information.

Use common clues like the link text ('FAQs', 'Help', 'Support', etc.), and analyze the HTML for context.

**Output Format (Strict JSON - Single Line):**

Your response MUST be a single line of JSON, starting with `{{` and ending with `}}`. No other text, comments, or formatting outside this JSON object:

{'{"faq_links": ["/pages/faqs", "/pages/help", ...]}'}

Links:
{links}

Homepage HTML:
{short_html}
"""

    OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            
        })
    )

    if not response.ok:
        raise RuntimeError(f"LLM call failed: {response.status_code} {response.text}")
    
    content = response.json()["choices"][0]["message"]["content"]
    # Define the delimiters
    start_delimiter = "```json"
    end_delimiter = "```"

    cleaned_string = content.strip() # Remove any leading/trailing whitespace/newlines from the whole string

    # Remove the starting delimiter if present
    if cleaned_string.startswith(start_delimiter):
        cleaned_string = cleaned_string[len(start_delimiter):].strip() # Remove delimiter and re-strip

    # Remove the ending delimiter if present
    if cleaned_string.endswith(end_delimiter):
        cleaned_string = cleaned_string[:-len(end_delimiter)].strip() # Remove delimiter and re-strip
    parsed_json = json.loads(cleaned_string)
    return parsed_json["faq_links"]

def extract_faqs_from_html_with_llm(html: str, url: str) -> list:
    prompt = f"""
You are an expert web extractor.

This is an HTML page from a Shopify site, likely containing FAQs or Help Center content. Your job is to extract structured Q/A pairs.

Return an array of objects, each with:
- "question": the FAQ question
- "answer": the full answer text

HTML Content from {url}:
{html[:6000]}

Respond ONLY in this format:
{'[{"question": "...", "answer": "..."},...]'}
"""
    OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            
        })
    )

    if not response.ok:
        raise RuntimeError(f"LLM call failed: {response.status_code} {response.text}")
    
    content = response.json()["choices"][0]["message"]["content"]
    print(f"Content: {content}")
    return None

def extract_contact_details_from_homepage(home_html: str):
    soup = BeautifulSoup(home_html, "lxml")
    text = soup.get_text(" ", strip=True)  # all visible text on page

    # Email regex
    email_pattern = r"\b[\w\.-]+@[\w\.-]+\.\w+\b"
    emails = re.findall(email_pattern, text)

    # Phone regex — captures mobile & international numbers
    phone_pattern = r"""
        (?:(?:\+?\d{1,3})?[\s\-.\(]*)?  # country code
        (?:\d{2,4})                     # area code
        [\s\-.\)]*                     # separator
        \d{3,5}                        # prefix
        [\s\-.\)]*                     # separator
        \d{3,5}                        # line number
    """
    phones = re.findall(phone_pattern, text, re.VERBOSE)

    # Deduplicate and clean
    emails = list(set(emails))
    phones = list(set(filter(lambda x: len(x.strip()) >= 7, phones)))

    return {
        "emails": emails,
        "phones": phones
    }

def extract_social_handles_from_homepage(home_html: str):
    soup = BeautifulSoup(home_html, "lxml")
    social_links = []

    social_domains = {
        "instagram.com": "Instagram",
        "facebook.com": "Facebook",
        "tiktok.com": "TikTok",
        "youtube.com": "YouTube",
        "twitter.com": "Twitter",
        "x.com": "Twitter",
        "pinterest.com": "Pinterest",
        "linkedin.com": "LinkedIn"
    }

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        for domain, platform in social_domains.items():
            if domain in href.lower():
                social_links.append(href)
                break  # avoid duplicates if multiple domains match

    # Deduplicate
    return list(set(social_links))

def extract_hero_products_from_homepage(home_html: str, base_url: str):
    soup = BeautifulSoup(home_html, "lxml")
    hero_products = []

    # Match typical Shopify homepage featured product cards
    sections = soup.select(
        ".featured-collection, .homepage-products, .product-card, .grid-product, .product-item"
    )

    for section in sections:
        try:
            # Try to extract <a href="/products/..."> containing the name
            link_tag = section.select_one("a[href*='/products/']")
            product_url = urljoin(base_url, link_tag['href']) if link_tag else None
            name = link_tag.get_text(strip=True) if link_tag else None

            # Image
            img_tag = section.select_one("img")
            image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
            if image_url:
                image_url = urljoin(base_url, image_url)

            # Price
            price_tag = section.select_one(".price, .product-price, .grid-product__price")
            price = price_tag.get_text(strip=True) if price_tag else None

            # Check for valid hero product
            if name and product_url:
                hero_products.append({
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "product_url": product_url
                })

        except Exception:
            continue  # Skip malformed entries

    return hero_products


def discover_product_endpoints_via_llm(soup: BeautifulSoup, website_url: str):
    # Step 1: Extract links and some page structure
    links = list(set(a['href'] for a in soup.find_all('a', href=True)))
    short_html = str(soup)[:5000]  # Truncate to avoid token overload
    full_urls = []
    
    prompt = f"""
You are an expert web analyst specializing in e-commerce site structure and product data extraction, specifically for Shopify stores. Your task is to analyze the provided HTML content and extracted links from a website's homepage to identify potential product listing endpoints and extract "Hero Products" directly displayed on the homepage.

You must provide your analysis strictly in a single-line JSON format.

**Input:**
You will receive two pieces of information:
1.  `short_html`: The truncated, prettified HTML content of the website's homepage (up to 5000 characters), enclosed within triple backticks (```).
2.  `links`: A JSON array of all unique `href` values from anchor tags found on the homepage.

**Analysis Phases:**

**PHASE 1: Analyze Homepage Structure and Content for Hero Products**
* Carefully examine the `short_html` for elements commonly associated with individual product displays (e.g., product names, prices, main images, "Add to Cart" buttons, "Shop Now" links, specific product titles). These are considered "Hero Products" (or "featured products", "new arrivals", "best sellers" directly on the homepage).
* For each discernible "Hero Product" found directly on the homepage, extract the following details:
    * `name`: The product's name.
    * `price`: The product's price (as a string, e.g., "$19.99", "€50", "Free"). If not found, use `null`.
    * `image_url`: The URL of the product's main image. Prioritize absolute URLs. If relative, note it. If not found, use `null`.
    * `product_url`: The URL to the individual product's dedicated page. Prioritize absolute URLs. If relative, note it. If not found, use `null`.
* If no direct "Hero Products" are found on the homepage, the `hero_products` list should be empty.

**PHASE 2: Analyze Links for Potential Product Listing Endpoints**
* Examine the provided `links` array. Look for URL patterns that are highly likely to lead to product collections, categories, or a general shop page.
* Common Shopify patterns to prioritize:
    * `/products.json` (for the full product catalog API)
    * `/products`
    * `/collections` or `/collections/some-category`
    * `/shop`
    * `/store`
    * `/items`
    * `/categories`
    * Any link containing keywords like "shop", "products", "collections", "store", "items", "categories", "all".
* For each identified potential endpoint URL:
    * `url`: The extracted URL (absolute or relative).
    * `description`: A brief explanation of why this URL is considered a potential product listing.
    * `confidence`: An integer score (0-100) reflecting your certainty.
* If a URL is relative (e.g., `/shop`), assume it's relative to the base domain of the homepage.
* Avoid including URLs that clearly lead to single product pages, cart pages, checkout, or account pages.

**PHASE 3: Overall Confidence and Summary**
* `overall_confidence`: An integer score (0-100) for the entire analysis.
* `analysis_summary`: A concise summary of your findings, including any challenges or ambiguities.

**Output Format (Strict JSON - Single Line):**

Your response MUST be a single line of JSON, starting with `{{` and ending with `}}`. No other text, comments, or formatting outside this JSON object.

{'{"hero_products": [{"name": "string","price": "string | null","image_url": "string | null (absolute or relative)","product_url": "string | null (absolute or relative)"} // ... more hero product objects if found],"potential_product_endpoints": [{"url": "string (absolute or relative)","description": "string","confidence": "integer (0-100)"} // ... more endpoint objects if found],"analysis_summary": "string","overall_confidence": "integer (0-100)"}'}

Input:
short_html: {short_html},
links: {links}

Create the output as described before.
"""
    OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            
        })
    )

    if not response.ok:
        raise RuntimeError(f"LLM call failed: {response.status_code} {response.text}")
    
    content = response.json()["choices"][0]["message"]["content"]
    loaded_data = json.loads(content)

    hero_products_links = []
    potential_product_endpoints = []

    for product in loaded_data["hero_products"]:
        if(product["product_url"]):
            hero_products_links.append(urljoin(website_url, product["product_url"]))

    for link in loaded_data["potential_product_endpoints"]:
        if(link["url"]):
            potential_product_endpoints.append(urljoin(website_url, link["url"]))

    return {"hero_product_links": hero_products_links, "potential_product_endpoints": potential_product_endpoints}


def extract_products_from_html_rule_based(page_html: str, base_url: str):
    soup = BeautifulSoup(page_html, "lxml")
    product_cards = []

    # Try multiple CSS patterns commonly used in Shopify themes
    containers = soup.select(".product-card, .grid-product, .product-item")

    for container in containers:
        try:
            # Product name
            name_tag = container.select_one("a, .product-title, h2")
            name = name_tag.get_text(strip=True) if name_tag else None

            # Price
            price_tag = container.select_one(".price, .product-price, .grid-product__price")
            price = price_tag.get_text(strip=True) if price_tag else None

            # Image
            img_tag = container.select_one("img")
            image_url = img_tag['src'] if img_tag and 'src' in img_tag.attrs else None
            if image_url:
                image_url = urljoin(base_url, image_url)

            # Product URL
            link_tag = container.select_one("a")
            product_url = link_tag['href'] if link_tag and 'href' in link_tag.attrs else None
            if product_url:
                product_url = urljoin(base_url, product_url)

            if name and product_url:
                product_cards.append({
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "product_url": product_url
                })

        except Exception:
            continue  # skip malformed cards

    return product_cards

def extract_brand_insights(website_url: str) -> dict:
    try:
        # Step 1: Validate site and load homepage
        homepage = requests.get(website_url, timeout=10)
        if homepage.status_code != 200:
            raise ValueError("Website not reachable")
        
        soup = BeautifulSoup(homepage.text, "lxml")

        privacy_policy = None
        privacy_url = find_privacy_policy_url(homepage.text, website_url)
        if privacy_url:
            res = requests.get(privacy_url, timeout=10)
            if res.ok:
                privacy_policy = extract_text_from_policy_page(res.text)
                print(f"Privacy policy: {privacy_policy}")

        social_handles = extract_social_handles_from_homepage(homepage.text)

        contact_details = []
        contact_dict = extract_contact_details_from_homepage(homepage.text)
        contact_details.append(contact_dict)
        
        possible_urls = discover_product_endpoints_via_llm(soup, website_url)

        product_catalog = []
        seen_urls = set()
        for product_url in possible_urls["potential_product_endpoints"]:
            if product_url in seen_urls:
                continue
            try:
                resp = requests.get(product_url, timeout=10)
                if not resp.ok:
                    continue

                products = extract_products_from_html_rule_based(resp.text, product_url)
                product_catalog.extend(products)

            except Exception as e:
                print(f"Failed to parse {product_url}: {e}")

        hero_products = []
        hero_seen_urls = set()
        for product_url in possible_urls["hero_product_links"]:
            if product_url in hero_seen_urls:
                continue
            try:
                resp = requests.get(product_url, timeout=10)
                if not resp.ok:
                    continue

                products = extract_hero_products_from_homepage(resp.text, product_url)
                hero_products.extend(products)
            except Exception as e:
                print(f"Failed to parse {product_url}: {e}")

        return BrandInsights(
            brand_name=None, 
            hero_products=hero_products,
            product_catalog=product_catalog,
            privacy_policy=privacy_policy,
            return_policy=None,
            refund_policy=None,
            faqs=[],
            contact_details=contact_details,
            social_handles=social_handles,
            brand_about=None,
            important_links=[]
        )
    except Exception as e:
        raise e