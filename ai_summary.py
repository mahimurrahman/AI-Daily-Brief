"""Groq AI summary module."""

from __future__ import annotations

import os

from dotenv import load_dotenv
import requests


load_dotenv()


def generate_summary(weather: dict | None, news: list[str] | None) -> str:
    """
    Generate a short AI summary for weather and news.

    Args:
        weather: Weather dictionary from get_weather() or None.
        news: Headline list from get_news() or None.

    Returns:
        str: Bullet-point summary text.
    """
    temperature = weather.get("temperature") if weather else "N/A"
    condition = weather.get("condition") if weather else "unknown conditions"
    top_headlines = (news or [])[:3]
    major_topic = top_headlines[0] if top_headlines else "general events"

    fallback_summary = (
        f"Weather is {temperature}C with {condition}. "
        f"Major news today focuses on {major_topic}."
    )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Groq Error] GROQ_API_KEY is missing.")
        return fallback_summary

    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    weather_summary = f"{temperature}C, {condition}" if weather else "unavailable"
    headlines_summary = " | ".join(top_headlines) if top_headlines else "unavailable"

    prompt = (
        "You are a professional daily news briefing assistant.\n"
        f"Weather data: {weather_summary}\n"
        f"Top 3 headlines: {headlines_summary}\n"
        "Create a concise daily brief in clear professional language.\n"
        "Synthesize headline themes instead of repeating headlines word-for-word.\n"
        "If news data is missing, still generate a weather-focused insight.\n"
        "If weather data is missing, summarize only the news and provide an insight.\n"
        "Keep the full response between 80 and 120 words.\n"
        "Use exactly this format:\n"
        "- Weather Brief - one short sentence.\n"
        "- News Brief - one short sentence about the main theme.\n"
        "- Insight - one short sentence about what the trend suggests."
    )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You write concise, high-quality daily briefings.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 220,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        text = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if text:
            return text
    except Exception as exc:
        print(f"[Groq Error] {exc!r}")

    return fallback_summary
