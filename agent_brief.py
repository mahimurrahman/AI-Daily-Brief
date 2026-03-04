"""Agent-style orchestration for prompt-driven AI Daily Brief generation."""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
import requests

from ai_summary import generate_summary
from news import get_news
from weather import get_weather


load_dotenv()


def _sanitize_prompt(prompt: str) -> str:
    """Remove common prompt-injection phrases and cap length."""
    cleaned = prompt.strip()
    dangerous_patterns = [
        r"ignore\s+all\s+previous\s+instructions",
        r"ignore\s+previous\s+instructions",
        r"system\s+prompt",
        r"developer\s+message",
        r"tool\s+instructions?",
        r"jailbreak",
        r"<script.*?>.*?</script>",
        r"rm\s+-rf\s+/?",
    ]
    for pattern in dangerous_patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"[`<>]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:300]


def _extract_json(text: str) -> dict | None:
    """Parse JSON from plain or markdown-wrapped model output."""
    candidates = [text.strip()]
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _heuristic_plan(prompt: str) -> dict:
    """Fallback extraction if the model cannot return a valid tool plan."""
    lower = prompt.lower()
    weather_words = ["weather", "temperature", "forecast", "rain", "wind", "humid"]
    news_words = ["news", "headline", "happening", "biggest", "today", "summary"]

    use_weather = any(word in lower for word in weather_words)
    use_news = any(word in lower for word in news_words)
    if not use_weather and not use_news:
        use_weather = True
        use_news = True

    city = ""
    city_match = re.search(
        r"\b(?:in|for|at)\s+([A-Za-z][A-Za-z\s\-]{1,40})",
        prompt,
        flags=re.IGNORECASE,
    )
    if city_match:
        city_candidate = city_match.group(1).strip(" .,!?")
        city_candidate = re.split(
            r"\b(today|tomorrow|weather|news|headlines|and|with)\b",
            city_candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip(" .,!?")
        city = city_candidate.title()

    topic = city if city else prompt
    if not use_news:
        topic = ""

    if use_weather and not city:
        use_weather = False

    if not use_weather and not use_news:
        use_news = True
        topic = prompt

    return {
        "city": city,
        "topic": topic,
        "use_weather": use_weather,
        "use_news": use_news,
    }


def _plan_from_llm(safe_prompt: str) -> dict | None:
    """Ask Groq to select tools and extract city/topic as JSON."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Agent Error] GROQ_API_KEY is missing for routing.")
        return None

    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    routing_instruction = (
        "You are a routing assistant for a weather+news app. "
        "Return JSON only with keys: city, topic, use_weather, use_news. "
        "city: detected city/location name or empty string. "
        "topic: short news search topic phrase or empty string. "
        "use_weather/use_news: booleans. "
        "If user asks what is happening today in a city, set both true. "
        "No markdown, no explanation, only JSON."
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
                    {"role": "system", "content": routing_instruction},
                    {"role": "user", "content": safe_prompt},
                ],
                "temperature": 0,
                "max_tokens": 120,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        content = (
            payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        parsed = _extract_json(content)
        if not parsed:
            return None
        return parsed
    except Exception as exc:
        print(f"[Agent Error] Routing failed: {exc!r}")
        return None


def _normalize_plan(raw_plan: dict, safe_prompt: str) -> dict:
    """Normalize potentially noisy model output into strict routing fields."""
    city_raw = raw_plan.get("city", "")
    topic_raw = raw_plan.get("topic", "")

    city = city_raw.strip() if isinstance(city_raw, str) else ""
    topic = topic_raw.strip() if isinstance(topic_raw, str) else ""
    use_weather = bool(raw_plan.get("use_weather", False))
    use_news = bool(raw_plan.get("use_news", False))

    if use_weather and not city:
        use_weather = False

    if use_news and not topic:
        topic = city if city else safe_prompt

    if not use_weather and not use_news:
        use_news = True
        topic = safe_prompt

    return {
        "city": city,
        "topic": topic,
        "use_weather": use_weather,
        "use_news": use_news,
    }


def run_agent_brief(prompt: str) -> dict:
    """
    Execute prompt-driven brief generation.

    Returns:
        dict: {
            "city": str,
            "weather": dict,
            "news": list[str],
            "summary": str
        }
    """
    safe_prompt = _sanitize_prompt(prompt)
    if not safe_prompt:
        return {
            "city": "",
            "weather": {},
            "news": [],
            "summary": "Please enter a valid prompt.",
            "weather_error": "",
            "news_error": "",
        }

    raw_plan = _plan_from_llm(safe_prompt)
    if raw_plan is None:
        plan = _heuristic_plan(safe_prompt)
    else:
        plan = _normalize_plan(raw_plan, safe_prompt)

    city = plan["city"]
    topic = plan["topic"]
    use_weather = plan["use_weather"]
    use_news = plan["use_news"]

    weather_data: dict = {}
    news_data: list[str] = []
    weather_error = ""
    news_error = ""

    if use_weather:
        if city:
            try:
                weather_data = get_weather(city)
            except RuntimeError as exc:
                print(f"[Agent Error] Weather failed: {exc!r}")
                weather_error = "Unable to fetch weather data right now."
        else:
            weather_error = "Unable to fetch weather data right now."

    if use_news:
        news_topic = topic if topic else (city if city else safe_prompt)
        try:
            news_data = get_news(news_topic)
        except RuntimeError as exc:
            print(f"[Agent Error] News failed: {exc!r}")
            news_error = "Unable to fetch news data right now."

    summary = generate_summary(weather_data or None, news_data or None)
    if weather_error and not weather_data:
        summary = f"{weather_error} {summary}".strip()
    if news_error and not news_data:
        summary = f"{summary} {news_error}".strip()

    return {
        "city": city,
        "weather": weather_data or {},
        "news": news_data,
        "summary": summary,
        "weather_error": weather_error,
        "news_error": news_error,
    }
