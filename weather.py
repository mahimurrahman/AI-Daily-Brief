"""Weather module for fetching current conditions from Visual Crossing."""

from __future__ import annotations

import os
from urllib.parse import quote

from dotenv import load_dotenv
import requests


load_dotenv()


def get_weather(city: str) -> dict:
    """
    Fetch current weather data for a city.

    Returns:
        dict: {
            "temperature": float | int,
            "humidity": float | int,
            "wind_speed": float | int,
            "condition": str
        }
    """
    if not city or not city.strip():
        raise RuntimeError("City is required to fetch weather.")

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing WEATHER_API_KEY. Add it to your .env file.")

    endpoint = (
        "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/"
        f"timeline/{quote(city.strip())}"
    )
    params = {
        "unitGroup": "metric",
        "include": "current",
        "key": api_key,
        "contentType": "json",
    }

    try:
        response = requests.get(endpoint, params=params, timeout=15)
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(
            "Weather API returned an error. Check city name and WEATHER_API_KEY."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError("Could not connect to the weather service.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Weather API returned invalid JSON data.") from exc

    current = payload.get("currentConditions")
    if not isinstance(current, dict):
        raise RuntimeError("Weather data format was unexpected.")

    temperature = current.get("temp")
    humidity = current.get("humidity")
    wind_speed = current.get("windspeed")
    condition = current.get("conditions")

    if any(item is None for item in [temperature, humidity, wind_speed, condition]):
        raise RuntimeError("Weather API response did not include all required fields.")

    return {
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "condition": str(condition),
    }
