# src/news_scraper.py
import feedparser
from datetime import datetime, timedelta, date
import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import time

# ensure VADER data is available
try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

analyzer = SentimentIntensityAnalyzer()

def parse_rss_for_ticker(ticker: str, months: int = 3, max_entries: int = 500):
    """
    Parse Yahoo Finance RSS feed for `ticker` and return a DataFrame:
    columns = ['date', 'title', 'summary', 'sentiment']
    Only entries within the last `months` months are included.
    """
    rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}"
    feed = feedparser.parse(rss_url)

    cutoff = datetime.utcnow().date() - timedelta(days=int(months * 30))  # approx months -> days
    rows = []

    for i, entry in enumerate(feed.entries):
        if i >= max_entries:
            break

        # attempt to get published date
        if 'published_parsed' in entry and entry.published_parsed:
            published_dt = datetime(*entry.published_parsed[:6])
        elif 'updated_parsed' in entry and entry.updated_parsed:
            published_dt = datetime(*entry.updated_parsed[:6])
        else:
            # fallback: skip if no date
            continue

        published_date = published_dt.date()
        if published_date < cutoff:
            # older than required window
            continue

        title = entry.get('title', '').strip()
        summary = entry.get('summary', '').strip()  # some RSS include short summary

        text_for_sentiment = (title + " " + summary).strip()
        if not text_for_sentiment:
            continue

        # compute VADER compound score
        score = analyzer.polarity_scores(text_for_sentiment)['compound']

        rows.append({
            'date': published_date.isoformat(),
            'title': title,
            'summary': summary,
            'sentiment': score
        })

        # be polite / avoid hammering if feedparser later fetches web pages (RSS is light)
        time.sleep(0.01)

    if not rows:
        return pd.DataFrame(columns=['date', 'title', 'summary', 'sentiment'])

    df = pd.DataFrame(rows)
    return df

def build_daily_sentiment(ticker: str, months: int = 3):
    """
    Returns a DataFrame indexed by date (YYYY-MM-DD) with one column 'daily_sentiment'
    which is the mean compound sentiment of all articles published on that day.
    Also saves to data/news_sentiment.csv
    """
    df = parse_rss_for_ticker(ticker, months=months)
    if df.empty:
        # return empty but with proper index
        empty = pd.DataFrame({'daily_sentiment': []})
        empty.index.name = 'date'
        return empty

    # group by date and average
    daily = df.groupby('date')['sentiment'].mean().reset_index()
    daily = daily.rename(columns={'sentiment': 'daily_sentiment'})
    daily['date'] = pd.to_datetime(daily['date']).dt.date
    daily = daily.set_index(daily['date'])
    daily = daily[['daily_sentiment']]
    daily.index.name = 'date'

    # save CSV for inspection
    daily.to_csv("data/news_sentiment.csv", index=True)

    return daily
