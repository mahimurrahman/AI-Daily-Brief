"""News module for fetching top headlines from NewsAPI."""

from __future__ import annotations

import os

from dotenv import load_dotenv
import requests


load_dotenv()


def get_news(topic: str) -> list[str]:
    """
    Fetch top five news headlines for a topic.

    Returns:
        list[str]: Up to five headline strings.
    """
    if not topic or not topic.strip():
        raise RuntimeError("News topic is required to fetch headlines.")

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NEWS_API_KEY. Add it to your .env file.")

    endpoint = "https://newsapi.org/v2/everything"
    params = {
        "q": topic.strip(),
        "pageSize": 5,
        "sortBy": "relevancy",
        "language": "en",
        "apiKey": api_key,
    }

    try:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            "News API returned an error. Check NEWS_API_KEY and request limits."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError("Could not connect to the news service.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("News API returned invalid JSON data.") from exc

    if payload.get("status") != "ok":
        message = payload.get("message", "Unknown News API error.")
        raise RuntimeError(f"News API error: {message}")

    articles = payload.get("articles", [])
    if not isinstance(articles, list):
        raise RuntimeError("News data format was unexpected.")

    headlines: list[str] = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        title = article.get("title")
        if isinstance(title, str):
            cleaned_title = title.strip()
            if cleaned_title and cleaned_title != "[Removed]":
                headlines.append(cleaned_title)
        if len(headlines) == 5:
            break

    return headlines
