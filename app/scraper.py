from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List

import feedparser
from newspaper import Article, Config

# Hard-coded list of RSS feeds to scrape
# Diverse sources to capture conflicting narratives on Iran-Israel issues
RSS_FEEDS = [
    # Western Mainstream (Working)
    "https://feeds.bbci.co.uk/news/world/rss.xml",  # BBC World News
    # Middle Eastern Perspectives (Working)
    "https://www.aljazeera.com/xml/rss/all.xml",  # Al Jazeera (Qatar)
    "https://www.timesofisrael.com/feed/",  # Times of Israel
    "https://www.jpost.com/rss/rssfeedsfrontpage.aspx",  # Jerusalem Post (Fixed URL)
    # Iranian/Pro-Iran Sources (Working)
    "https://en.mehrnews.com/rss",  # Mehr News (Iran)
    # Regional/Alternative (Working)
    "https://www.middleeasteye.net/rss",  # Middle East Eye
    "https://www.al-monitor.com/rss.xml",  # Al-Monitor
    # Additional Working Sources
    "https://www.reuters.com/world/rss",  # Reuters World (Fixed URL)
    "https://rss.cnn.com/rss/edition.rss",  # CNN International
    "https://feeds.ap.org/ap/general",  # AP General
    "https://www.debka.com/feed/",  # DEBKAfile (Israel security analysis)
    "https://israelnationalnews.com/Rss.aspx",  # Israel National News
    # Iran-focused feeds
    "https://www.jpost.com/rss/rssfeedsiran",  # Jerusalem Post Iran coverage
    "https://www.jpost.com/rss/rssfeedsmiddleeastnews.aspx",  # Jerusalem Post Middle East
]


@dataclass
class NewsItem:
    """Standardized dataclass for a scraped news article."""

    title: str
    text: str
    url: str
    source_name: str
    published_at: datetime = field(default_factory=datetime.now)


class BaseScraper:
    def __init__(self, feed_url: str):
        self.feed_url = feed_url

    def fetch(self) -> List[NewsItem]:
        raise NotImplementedError


class RssScraper(BaseScraper):
    def fetch(self, max_age_hours: int = 24) -> List[NewsItem]:
        collected_items: List[NewsItem] = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

        print(f"Fetching RSS feed: {self.feed_url}")
        feed = feedparser.parse(self.feed_url)

        if feed.bozo:
            print(f"Warning: RSS feed may be malformed: {self.feed_url}")

        source_name = feed.feed.get(
            "title", self.feed_url.split("//")[-1].split("/")[0]
        )
        entries_processed = 0

        for entry in feed.entries:
            published_tuple = entry.get("published_parsed")
            if not published_tuple:
                continue

            published_dt = datetime.fromtimestamp(
                time.mktime(published_tuple), tz=timezone.utc
            )

            if published_dt >= cutoff_date:
                try:
                    config = Config()
                    config.browser_user_agent = (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/118.0.0.0 Safari/537.36"
                    )
                    article = Article(entry.get("link"), config=config)
                    article.download()
                    article.parse()

                    if article.text:
                        item = NewsItem(
                            title=entry.get("title"),
                            text=article.text,
                            url=entry.get("link"),
                            published_at=published_dt,
                            source_name=source_name,
                        )
                        collected_items.append(item)
                        entries_processed += 1
                except Exception as e:
                    print(
                        f"Failed to download or parse article {entry.get('link')}: {e}"
                    )

        print(f"Processed {entries_processed} articles from {source_name}")
        return collected_items


def collect_latest_news() -> List[NewsItem]:
    all_items = []
    for feed in RSS_FEEDS:
        scraper = RssScraper(feed)
        all_items.extend(scraper.fetch())
    return all_items
