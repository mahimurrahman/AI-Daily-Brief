# AI Daily Brief

AI Daily Brief is a beginner-friendly Streamlit app that combines:

- current weather for a city
- top news headlines for a topic
- an AI-generated daily summary using Groq

The app is split into small Python modules so each part is easy to understand and maintain.

## Project Structure

```text
P1-ai-daily-brief/
|-- app.py
|-- weather.py
|-- news.py
|-- ai_summary.py
|-- agent_brief.py
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Prerequisites

- Python 3.10+ recommended
- API keys for:
  - Visual Crossing Weather
  - NewsAPI
  - Groq

## Installation

1. Create and activate a virtual environment (optional, but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your keys:

```env
NEWS_API_KEY=your_news_api_key
WEATHER_API_KEY=your_weather_api_key
GROQ_API_KEY=your_groq_api_key
```

Optional:

```env
GROQ_MODEL=llama-3.1-8b-instant
```

## Run the App

```bash
streamlit run app.py
```

Then open the local URL shown in your terminal.

## How It Works

- `weather.py` calls Visual Crossing and returns temperature, humidity, wind speed, and condition.
- `news.py` calls NewsAPI and returns top 5 headlines.
- `ai_summary.py` sends weather + news context to Groq and returns a short bullet-point summary.
- `agent_brief.py` accepts one user prompt, selects weather/news tool calls, and returns structured output.
- `app.py` renders everything in Streamlit and handles section-level errors.

## Error Handling

- API keys are loaded only from environment variables.
- If one API fails, the app still shows other successful sections.
- If both weather and news fail, the AI summary is skipped.

## Troubleshooting

- `Missing ... API_KEY`:
  - Ensure `.env` exists and contains the key.
- `... returned an error`:
  - Verify API key validity, quotas, and network connectivity.
- Empty news list:
  - Try a broader topic keyword.
