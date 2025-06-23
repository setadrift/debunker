from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.scraper import NewsItem, RssScraper, collect_latest_news


class TestNewsScraperDeduplication:
    """Test suite for news scraper deduplication functionality."""

    def test_collect_latest_news_basic_functionality(self):
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
            mock_feed_obj.bozo = False
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

    def test_collect_latest_news_deduplication_by_url(self):
        """Test that duplicate articles with same URL are removed."""
        now = datetime.now(timezone.utc)
        recent_entry_time = now - timedelta(hours=1)

        with patch("app.scraper.feedparser.parse") as mock_parse, patch(
            "app.scraper.Article"
        ) as mock_article_class:
            # Mock feedparser to return duplicate URLs across different feeds
            mock_feed_obj = MagicMock()
            mock_feed_obj.feed = {"title": "Mock News Source"}
            mock_feed_obj.bozo = False
            mock_feed_obj.entries = [
                {
                    "title": "Duplicate Article",
                    "link": "http://example.com/duplicate",
                    "published_parsed": recent_entry_time.timetuple(),
                },
                {
                    "title": "Unique Article",
                    "link": "http://example.com/unique",
                    "published_parsed": recent_entry_time.timetuple(),
                },
            ]
            mock_parse.return_value = mock_feed_obj

            # Configure the mock for newspaper.Article
            mock_article_instance = MagicMock()
            mock_article_instance.text = "Article content."
            mock_article_class.return_value = mock_article_instance

            # Mock RSS_FEEDS with two feeds that return the same article
            with patch(
                "app.scraper.RSS_FEEDS",
                ["http://feed1.com/rss", "http://feed2.com/rss"],
            ):
                results = collect_latest_news()

            # Should have 2 unique articles (duplicate removed)
            assert len(results) == 2
            urls = [item.url for item in results]
            assert "http://example.com/duplicate" in urls
            assert "http://example.com/unique" in urls

    def test_collect_latest_news_empty_feeds(self):
        """Test behavior with empty RSS feeds."""
        with patch("app.scraper.feedparser.parse") as mock_parse, patch(
            "app.scraper.Article"
        ):
            # Mock empty feed
            mock_feed_obj = MagicMock()
            mock_feed_obj.feed = {"title": "Empty Feed"}
            mock_feed_obj.bozo = False
            mock_feed_obj.entries = []
            mock_parse.return_value = mock_feed_obj

            with patch("app.scraper.RSS_FEEDS", ["http://emptyfeed.com/rss"]):
                results = collect_latest_news()

            assert len(results) == 0

    def test_collect_latest_news_multiple_feeds_with_duplicates(self):
        """Test deduplication across multiple feeds with various duplicates."""
        now = datetime.now(timezone.utc)
        recent_time = now - timedelta(hours=1)

        # Track which feed is being called to return different content
        feed_call_count = 0

        def mock_parse_side_effect(url):
            nonlocal feed_call_count
            feed_call_count += 1

            mock_feed_obj = MagicMock()
            mock_feed_obj.bozo = False

            if feed_call_count == 1:  # First feed
                mock_feed_obj.feed = {"title": "Feed One"}
                mock_feed_obj.entries = [
                    {
                        "title": "Article A",
                        "link": "http://example.com/article-a",
                        "published_parsed": recent_time.timetuple(),
                    },
                    {
                        "title": "Article B",
                        "link": "http://example.com/article-b",
                        "published_parsed": recent_time.timetuple(),
                    },
                ]
            elif feed_call_count == 2:  # Second feed
                mock_feed_obj.feed = {"title": "Feed Two"}
                mock_feed_obj.entries = [
                    {
                        "title": "Article A (duplicate)",
                        "link": "http://example.com/article-a",  # Duplicate URL
                        "published_parsed": recent_time.timetuple(),
                    },
                    {
                        "title": "Article C",
                        "link": "http://example.com/article-c",
                        "published_parsed": recent_time.timetuple(),
                    },
                ]
            else:  # Third feed
                mock_feed_obj.feed = {"title": "Feed Three"}
                mock_feed_obj.entries = [
                    {
                        "title": "Article B (another duplicate)",
                        "link": "http://example.com/article-b",  # Another duplicate
                        "published_parsed": recent_time.timetuple(),
                    },
                    {
                        "title": "Article D",
                        "link": "http://example.com/article-d",
                        "published_parsed": recent_time.timetuple(),
                    },
                ]

            return mock_feed_obj

        with patch(
            "app.scraper.feedparser.parse", side_effect=mock_parse_side_effect
        ), patch("app.scraper.Article") as mock_article_class:
            # Configure the mock for newspaper.Article
            mock_article_instance = MagicMock()
            mock_article_instance.text = "Article content."
            mock_article_class.return_value = mock_article_instance

            # Mock three feeds
            with patch(
                "app.scraper.RSS_FEEDS",
                [
                    "http://feed1.com/rss",
                    "http://feed2.com/rss",
                    "http://feed3.com/rss",
                ],
            ):
                results = collect_latest_news()

            # Should have 4 unique articles (A, B, C, D)
            assert len(results) == 4
            urls = [item.url for item in results]
            expected_urls = [
                "http://example.com/article-a",
                "http://example.com/article-b",
                "http://example.com/article-c",
                "http://example.com/article-d",
            ]
            assert set(urls) == set(expected_urls)

    def test_rss_scraper_article_download_parse_called(self):
        """Test that Article.download() and Article.parse() are called correctly."""
        now = datetime.now(timezone.utc)
        recent_time = now - timedelta(hours=1)

        with patch("app.scraper.feedparser.parse") as mock_parse, patch(
            "app.scraper.Article"
        ) as mock_article_class:
            # Setup feed mock
            mock_feed_obj = MagicMock()
            mock_feed_obj.feed = {"title": "Test Feed"}
            mock_feed_obj.bozo = False
            mock_feed_obj.entries = [
                {
                    "title": "Test Article",
                    "link": "http://example.com/test",
                    "published_parsed": recent_time.timetuple(),
                }
            ]
            mock_parse.return_value = mock_feed_obj

            # Setup article mock
            mock_article_instance = MagicMock()
            mock_article_instance.text = "Test article content"
            mock_article_class.return_value = mock_article_instance

            # Test RssScraper directly
            scraper = RssScraper("http://test.com/rss")
            results = scraper.fetch()

            # Verify Article methods were called
            mock_article_instance.download.assert_called_once()
            mock_article_instance.parse.assert_called_once()

            # Verify Article constructor was called with correct URL and config
            mock_article_class.assert_called_once()
            call_args = mock_article_class.call_args
            assert call_args[0][0] == "http://example.com/test"  # URL
            assert call_args[1]["config"] is not None  # Config object

            assert len(results) == 1
            assert results[0].url == "http://example.com/test"

    def test_rss_scraper_handles_article_download_failure(self):
        """Test that scraper handles Article.download() failures gracefully."""
        now = datetime.now(timezone.utc)
        recent_time = now - timedelta(hours=1)

        with patch("app.scraper.feedparser.parse") as mock_parse, patch(
            "app.scraper.Article"
        ) as mock_article_class:
            # Setup feed mock
            mock_feed_obj = MagicMock()
            mock_feed_obj.feed = {"title": "Test Feed"}
            mock_feed_obj.bozo = False
            mock_feed_obj.entries = [
                {
                    "title": "Failing Article",
                    "link": "http://example.com/fail",
                    "published_parsed": recent_time.timetuple(),
                }
            ]
            mock_parse.return_value = mock_feed_obj

            # Setup article mock to raise exception on download
            mock_article_instance = MagicMock()
            mock_article_instance.download.side_effect = Exception("Download failed")
            mock_article_class.return_value = mock_article_instance

            # Test RssScraper directly
            scraper = RssScraper("http://test.com/rss")
            results = scraper.fetch()

            # Should handle the exception and return empty list
            assert len(results) == 0
            mock_article_instance.download.assert_called_once()

    def test_rss_scraper_filters_old_articles(self):
        """Test that scraper filters out articles older than max_age_hours."""
        now = datetime.now(timezone.utc)
        recent_time = now - timedelta(hours=1)  # Within 24 hours
        old_time = now - timedelta(hours=48)  # Older than 24 hours

        with patch("app.scraper.feedparser.parse") as mock_parse, patch(
            "app.scraper.Article"
        ) as mock_article_class:
            # Setup feed mock with both recent and old articles
            mock_feed_obj = MagicMock()
            mock_feed_obj.feed = {"title": "Test Feed"}
            mock_feed_obj.bozo = False
            mock_feed_obj.entries = [
                {
                    "title": "Recent Article",
                    "link": "http://example.com/recent",
                    "published_parsed": recent_time.timetuple(),
                },
                {
                    "title": "Old Article",
                    "link": "http://example.com/old",
                    "published_parsed": old_time.timetuple(),
                },
            ]
            mock_parse.return_value = mock_feed_obj

            # Setup article mock
            mock_article_instance = MagicMock()
            mock_article_instance.text = "Article content"
            mock_article_class.return_value = mock_article_instance

            # Test RssScraper with default 24-hour filter
            scraper = RssScraper("http://test.com/rss")
            results = scraper.fetch()

            # Should only return the recent article
            assert len(results) == 1
            assert results[0].title == "Recent Article"
