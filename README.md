# Meridian Commodity Hedge Desk — Streamlit

Free-deployment commodity hedge-desk terminal.

## Data sources
- Yahoo Finance / yfinance: commodity futures, FX, volatility and index-futures price layer.
- FRED (Federal Reserve Bank of St. Louis): US rates and macro history through its public graph CSV endpoint.
- CFTC COT: reserved as an official-data integration point; no invented positioning values.

Yahoo data can be delayed and is not an exchange-direct execution feed.

## Deploy
1. Use Local Host..

2. Deploy through Streamlit : https://commodity-hedge-desk-terminal-macros.streamlit.app/

** No API key is required for the default data layer.

## Local test
```bash
pip install -r requirements.txt
streamlit run app.py
```

Prices are cached for 60 seconds. FRED data is cached for 15 minutes. The app shows `—` rather than fabricating missing provider values.
