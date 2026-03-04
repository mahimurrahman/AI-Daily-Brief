"""Streamlit entrypoint for the AI Daily Brief app."""

from __future__ import annotations

from dotenv import load_dotenv
import streamlit as st

from agent_brief import run_agent_brief
from ai_summary import generate_summary
from news import get_news
from weather import get_weather


load_dotenv()


def _render_weather_section(
    weather_data: dict | None,
    weather_error: str = "",
    no_data_message: str = "Unable to fetch weather data right now.",
) -> None:
    """Render weather section in a consistent dashboard style."""
    st.markdown("### Weather")
    if weather_data:
        metric_cols = st.columns(3)
        metric_cols[0].metric("Temperature", f"{weather_data.get('temperature', 'N/A')} C")
        metric_cols[1].metric("Humidity", f"{weather_data.get('humidity', 'N/A')}%")
        metric_cols[2].metric("Wind Speed", f"{weather_data.get('wind_speed', 'N/A')} km/h")
        st.markdown(f"**Condition:** {weather_data.get('condition', 'N/A')}")
        return

    if weather_error:
        st.info(weather_error)
    else:
        st.info(no_data_message)


def _render_news_section(
    headlines: list[str] | None,
    news_error: str = "",
    no_data_message: str = "No headlines found for this topic.",
) -> None:
    """Render news headlines section."""
    st.markdown("### News")
    with st.container(border=True):
        if headlines:
            st.markdown("\n".join(f"- {headline}" for headline in headlines))
            return

        if news_error:
            st.info(news_error)
        else:
            st.info(no_data_message)


def main() -> None:
    """Render the Streamlit interface and handle user actions."""
    st.set_page_config(page_title="AI Daily Brief", layout="centered")
    st.title("AI Daily Brief")
    st.caption("Weather, News, and AI insights in one place")

    st.markdown("## Ask AI Brief")
    ask_prompt = st.text_input(
        "Ask AI Brief",
        key="ask_ai_brief_input",
        placeholder="e.g., What's happening in Dhaka today?",
    )

    if st.button("Generate AI Brief", key="generate_ai_brief_btn"):
        user_prompt = ask_prompt.strip()
        if not user_prompt:
            st.warning("Please enter a prompt for Ask AI Brief.")
        else:
            with st.spinner("Understanding prompt and generating brief..."):
                result = run_agent_brief(user_prompt)

            with st.container():
                st.divider()
                if result.get("city"):
                    st.caption(f"Detected city: {result['city']}")

                _render_weather_section(
                    weather_data=result.get("weather", {}),
                    weather_error=result.get("weather_error", ""),
                    no_data_message="Weather was not requested in this prompt.",
                )

                st.divider()
                _render_news_section(
                    headlines=result.get("news", []),
                    news_error=result.get("news_error", ""),
                    no_data_message="News was not requested in this prompt.",
                )

                st.divider()
                st.markdown("### AI Insight")
                with st.container(border=True):
                    st.markdown(result.get("summary", "No summary generated."))

    st.divider()
    st.markdown("## Manual Input")

    col1, col2 = st.columns(2)
    with col1:
        city = st.text_input("City", key="manual_city_input", placeholder="e.g., Dhaka")
    with col2:
        topic = st.text_input(
            "News topic",
            key="manual_topic_input",
            placeholder="e.g., Artificial Intelligence",
        )

    if st.button("Generate Brief", key="manual_generate_btn"):
        city = city.strip()
        topic = topic.strip()

        if not city or not topic:
            st.warning("Please enter both a city and a news topic.")
            return

        weather_data = None
        news_headlines: list[str] | None = None
        weather_success = False
        news_success = False
        weather_error = ""
        news_error = ""

        with st.container():
            st.divider()
            with st.spinner("Fetching weather..."):
                try:
                    weather_data = get_weather(city)
                    weather_success = True
                except RuntimeError as exc:
                    weather_error = str(exc)

            _render_weather_section(
                weather_data=weather_data,
                weather_error=weather_error,
            )

            st.divider()
            with st.spinner("Fetching news..."):
                try:
                    news_headlines = get_news(topic)
                    news_success = True
                except RuntimeError as exc:
                    news_error = str(exc)

            _render_news_section(
                headlines=news_headlines,
                news_error=news_error,
            )

            st.divider()
            st.markdown("### AI Summary")
            if weather_success or news_success:
                with st.spinner("Generating AI summary..."):
                    try:
                        summary = generate_summary(
                            weather=weather_data if weather_success else None,
                            news=news_headlines if news_success else None,
                        )
                        with st.container(border=True):
                            st.markdown(summary)
                    except RuntimeError as exc:
                        st.error(str(exc))
            else:
                st.info("Summary skipped because weather and news could not be fetched.")


if __name__ == "__main__":
    main()
