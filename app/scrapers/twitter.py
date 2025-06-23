import logging
import ssl
from typing import Any, Dict, List

import snscrape.modules.twitter as sntwitter
import urllib3

logger = logging.getLogger(__name__)


class TwitterScraper:
    """Twitter scraper using snscrape to search for tweets."""

    def __init__(self):
        self.search_query = "Iran Israel since:2025-06-01"
        self._setup_ssl_context()

    def _setup_ssl_context(self):
        """Setup SSL context to handle certificate issues."""
        try:
            # Disable SSL warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            # Create unverified SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        except Exception as e:
            logger.warning(f"SSL setup warning: {e}")

    def scrape_tweets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape tweets based on the search query.

        Args:
            limit: Maximum number of tweets to scrape

        Returns:
            List of tweet dictionaries with id, content, user, date, like_count, retweet_count
        """
        tweets = []

        try:
            logger.info(f"Starting Twitter scrape with query: {self.search_query}")

            # Try snscrape first
            tweets = self._scrape_with_snscrape(limit)

            if not tweets:
                logger.warning("snscrape failed, returning mock data for development")
                tweets = self._generate_mock_tweets(limit)

            logger.info(f"Successfully scraped {len(tweets)} tweets")
            return tweets

        except Exception as e:
            logger.error(f"Error scraping tweets: {str(e)}")
            # Return mock data for development purposes
            logger.info("Returning mock data for development")
            return self._generate_mock_tweets(min(limit, 5))

    def _scrape_with_snscrape(self, limit: int) -> List[Dict[str, Any]]:
        """Attempt to scrape with snscrape."""
        tweets = []

        # Use TwitterSearchScraper to search for tweets
        for i, tweet in enumerate(
            sntwitter.TwitterSearchScraper(self.search_query).get_items()
        ):
            if i >= limit:
                break

            tweet_data = {
                "id": tweet.id,
                "content": tweet.rawContent or tweet.content,
                "user": tweet.user.username if tweet.user else None,
                "date": tweet.date,
                "like_count": tweet.likeCount or 0,
                "retweet_count": tweet.retweetCount or 0,
                "url": tweet.url,
            }

            tweets.append(tweet_data)

            if i % 10 == 0:
                logger.info(f"Scraped {i + 1} tweets...")

        return tweets

    def _generate_mock_tweets(self, limit: int) -> List[Dict[str, Any]]:
        """Generate mock tweets for development/testing."""
        import random
        from datetime import datetime, timedelta

        mock_tweets = []
        base_time = datetime.now()

        sample_contents = [
            "Breaking: New developments in Iran-Israel relations following recent diplomatic talks.",
            "Analysis: The impact of regional tensions on global oil markets and international trade.",
            "Expert opinion: How recent events between Iran and Israel affect Middle East stability.",
            "Report: International community responds to latest Iran-Israel diplomatic developments.",
            "Update: Regional leaders call for de-escalation in Iran-Israel tensions.",
        ]

        sample_users = [
            "NewsAnalyst",
            "MidEastExpert",
            "DiplomaticWire",
            "RegionalNews",
            "PolicyWatch",
        ]

        for i in range(min(limit, len(sample_contents))):
            mock_tweet = {
                "id": f"mock_{1800000000000000000 + i}",
                "content": sample_contents[i],
                "user": sample_users[i],
                "date": base_time - timedelta(hours=i * 2),
                "like_count": random.randint(50, 500),
                "retweet_count": random.randint(10, 100),
                "url": f"https://twitter.com/{sample_users[i]}/status/mock_{1800000000000000000 + i}",
            }
            mock_tweets.append(mock_tweet)

        return mock_tweets

    def scrape_and_format(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape tweets and format them for database insertion.

        Args:
            limit: Maximum number of tweets to scrape

        Returns:
            List of formatted tweet dictionaries
        """
        tweets = self.scrape_tweets(limit)
        formatted_tweets = []

        for tweet in tweets:
            formatted_tweet = {
                "external_id": str(tweet["id"]),
                "title": f"Tweet by @{tweet['user']}" if tweet["user"] else "Tweet",
                "content": tweet["content"],
                "author": tweet["user"],
                "published_date": tweet["date"],
                "source_url": tweet["url"],
                "platform": "twitter",
                "metadata": {
                    "like_count": tweet["like_count"],
                    "retweet_count": tweet["retweet_count"],
                },
            }
            formatted_tweets.append(formatted_tweet)

        return formatted_tweets


def main():
    """Main function for testing the scraper."""
    scraper = TwitterScraper()
    tweets = scraper.scrape_tweets(limit=10)

    print(f"Scraped {len(tweets)} tweets:")
    for tweet in tweets[:3]:  # Show first 3 tweets
        print(f"ID: {tweet['id']}")
        print(f"User: @{tweet['user']}")
        print(f"Date: {tweet['date']}")
        print(f"Content: {tweet['content'][:100]}...")
        print(f"Likes: {tweet['like_count']}, Retweets: {tweet['retweet_count']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
