"""
Real-Time News, Weather & Web Search Skills for S.H.I.V.A.
Fetches live headlines, current events, weather conditions, and web snippets
in real-time without requiring paid API keys!
"""

import re
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def _clean_headline(raw_title: str) -> str:
    """Strips trailing news outlet attribution from title (e.g. 'Headline - The Hindu' -> 'Headline')."""
    if not raw_title:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", "", raw_title).strip()
    # Strip trailing " - Publisher Name"
    clean = re.sub(r"\s+-\s+[^-]+$", "", clean).strip()
    return clean


def build_conversational_news_briefing(headlines: List[Dict[str, str]], category_label: str = "Top Headlines") -> str:
    """Builds a sharp, fluent, natural conversational executive news briefing."""
    if not headlines:
        return "Boss, abhi koi naya news update fetch nahi ho paya. Internet connection check karein."

    count = len(headlines)
    parts = [f"Boss, aaj ke {category_label} maine fetch kar liye hain:"]

    for idx, item in enumerate(headlines[:4]):
        title = item["title"]
        source = item.get("source", "")
        source_suffix = f" ({source})" if source else ""

        if idx == 0:
            parts.append(f"Pehli badi khabar: '{title}'{source_suffix}.")
        elif idx == 1:
            parts.append(f"Doosri khabar: '{title}'{source_suffix}.")
        elif idx == 2:
            parts.append(f"Teesri update: '{title}'{source_suffix}.")
        elif idx == 3:
            parts.append(f"Chauthi khabar: '{title}'{source_suffix}.")

    if count > 4:
        parts.append(f"Iske alava {count - 4} aur news updates available hain.")

    parts.append("Kya aap kisi specific khabar ke baare mein detail jaanna chahte hain, Boss?")
    return " ".join(parts)


def get_latest_news(category: str = "general", limit: int = 5) -> Dict[str, Any]:
    """
    Fetches real-time news headlines from Google News RSS.
    Categories supported:
    - 'general' / 'top': Top India & Global news
    - 'technology' / 'tech': Latest tech & AI news
    - 'business' / 'finance': Business, economy, and market news
    - 'sports' / 'cricket': Sports & cricket news
    - Any custom topic (e.g. 'artificial intelligence', 'elections', 'space')
    """
    cat_lower = category.lower().strip()

    if cat_lower in ["general", "top", "india", "today", "latest", "aaj"]:
        rss_url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        label = "Top News Headlines"
    elif cat_lower in ["technology", "tech", "ai", "coding", "software"]:
        rss_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-IN&gl=IN&ceid=IN:en"
        label = "Tech & AI Headlines"
    elif cat_lower in ["business", "finance", "economy", "market", "stock"]:
        rss_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-IN&gl=IN&ceid=IN:en"
        label = "Business & Finance News"
    elif cat_lower in ["sports", "cricket", "football", "khel"]:
        rss_url = "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-IN&gl=IN&ceid=IN:en"
        label = "Sports Updates"
    else:
        # Search for custom topic
        encoded_topic = urllib.parse.quote(category)
        rss_url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-IN&gl=IN&ceid=IN:en"
        label = f"News updates for '{category}'"

    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=6) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        headlines = []
        for item in items[:limit]:
            raw_title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            source_elem = item.find("source")
            source = source_elem.text if source_elem is not None else ""

            clean_title = _clean_headline(raw_title)
            if clean_title:
                headlines.append({
                    "title": clean_title,
                    "source": source,
                    "date": pub_date,
                    "link": link,
                })

        message = build_conversational_news_briefing(headlines, label)
        return {
            "status": "success",
            "category": category,
            "total": len(headlines),
            "message": message,
            "headlines": headlines,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Boss, live news fetch karne mein network issue aaya: {e}",
            "headlines": [],
        }


def get_weather(city: str = "Bhopal") -> Dict[str, Any]:
    """
    Fetches real-time weather conditions for any city (default: Bhopal).
    """
    clean_city = city.strip() or "Bhopal"
    encoded_city = urllib.parse.quote(clean_city)
    url = f"https://wttr.in/{encoded_city}?format=%C+%t+%w+%h"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read().decode("utf-8").strip()

        # wttr.in format gives: "Condition +Temp Wind Humidity" e.g. "Sunny +25°C ↙14km/h 26%"
        parts = data.split()
        condition = parts[0] if parts else "Clear"
        temp = parts[1] if len(parts) > 1 else ""
        wind = parts[2] if len(parts) > 2 else ""
        humidity = parts[3] if len(parts) > 3 else ""

        message = (
            f"Boss, {clean_city} mein aaj mausam {condition} hai. "
            f"Temperature {temp} hai, hawa ki speed {wind} aur humidity {humidity} chal rahi hai."
        )

        return {
            "status": "success",
            "city": clean_city,
            "condition": condition,
            "temperature": temp,
            "wind": wind,
            "humidity": humidity,
            "message": message,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Boss, {clean_city} ka live weather fetch nahi ho saka: {e}",
        }


def search_web_realtime(query: str, limit: int = 3) -> Dict[str, Any]:
    """
    Performs real-time web retrieval for facts, current events, or questions
    using DuckDuckGo instant answers and Google News topic search.
    """
    clean_query = query.strip()
    if not clean_query:
        return {"status": "error", "message": "Boss, please specify what to search."}

    # 1. Try DuckDuckGo Instant Answer for factual definitions/entities
    try:
        encoded_q = urllib.parse.quote(clean_query)
        ddg_url = f"https://api.duckduckgo.com/?q={encoded_q}&format=json&no_html=1"
        req = urllib.request.Request(ddg_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))

        abstract = data.get("AbstractText", "").strip()
        if abstract:
            return {
                "status": "success",
                "query": clean_query,
                "source": "Instant Fact Database",
                "message": f"Boss, '{clean_query}' ke baare mein live information yeh hai:\n{abstract}",
            }
    except Exception:
        pass

    # 2. Try Google News Live Search for current events/topics
    news_res = get_latest_news(category=clean_query, limit=limit)
    if news_res.get("status") == "success" and news_res.get("headlines"):
        return {
            "status": "success",
            "query": clean_query,
            "source": "Live Web Updates",
            "message": news_res["message"],
        }

    return {
        "status": "not_found",
        "message": f"Boss, '{clean_query}' ke liye real-time information fetch nahi ho saki.",
    }

