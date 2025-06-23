from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.scraper import NewsItem, collect_latest_news


def test_collect_latest_news():
    """Verify that the scraper correctly processes a mocked RSS feed."""
    # Mock data for a fake RSS feed entry
    now = datetime.now(timezone.utc)
    recent_entry_time = now - timedelta(hours=1)
    old_entry_time = now - timedelta(hours=48)

    # Mock the external libraries
    with patch("app.scraper.feedparser.parse") as mock_parse, patch(
        "app.scraper.Article"
    ) as mock_article_class:
        # Configure the mock for feedparser to return an object with attributes,
        # mimicking the actual behavior of feedparser.
        mock_feed_obj = MagicMock()
        mock_feed_obj.feed = {"title": "Mock News Source"}
        mock_feed_obj.entries = [
            {
                "title": "Recent Article",
                "link": "http://example.com/recent",
                "published_parsed": recent_entry_time.timetuple(),
            },
            {
                "title": "Old Article",
                "link": "http://example.com/old",
                "published_parsed": old_entry_time.timetuple(),
            },
        ]
        mock_parse.return_value = mock_feed_obj

        # Configure the mock for newspaper.Article
        mock_article_instance = MagicMock()
        mock_article_instance.text = "This is the full article text."
        mock_article_class.return_value = mock_article_instance

        # Mock the RSS_FEEDS to use our test URL
        with patch("app.scraper.RSS_FEEDS", ["http://mockfeed.com/rss"]):
            # Run the scraper
            results = collect_latest_news()

        # Assertions
        assert len(results) == 1
        item = results[0]
        assert isinstance(item, NewsItem)
        assert item.title == "Recent Article"
        assert item.text == "This is the full article text."
        assert item.url == "http://example.com/recent"
        assert item.source_name == "Mock News Source"

        # Verify that download and parse were called on the article
        mock_article_instance.download.assert_called_once()
        mock_article_instance.parse.assert_called_once()
