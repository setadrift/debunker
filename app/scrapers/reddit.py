import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import praw
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RedditScraper:
    """Reddit scraper using PRAW to search for posts in specific subreddits."""

    def __init__(self):
        self.search_terms = "Iran Israel"
        self.subreddits = ["worldnews", "MiddleEast"]
        self.reddit = self._initialize_reddit()

    def _initialize_reddit(self):
        """Initialize Reddit instance with read-only credentials."""
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID", ""),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
                user_agent="ii-misinformation-tracker/1.0",
            )

            # Test the connection
            reddit.user.me()
            logger.info("Reddit API connection established")
            return reddit

        except Exception as e:
            logger.warning(f"Reddit API connection failed: {e}")
            logger.info("Will use mock data for development")
            return None

    def scrape_posts(self, limit_per_subreddit: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape posts from specified subreddits in the last 24 hours.

        Args:
            limit_per_subreddit: Maximum number of posts to scrape per subreddit

        Returns:
            List of post dictionaries with title, content, metadata
        """
        if not self.reddit:
            logger.warning("Reddit API not available, using mock data")
            return self._generate_mock_posts(limit_per_subreddit)

        all_posts = []
        yesterday = datetime.now() - timedelta(days=1)

        try:
            for subreddit_name in self.subreddits:
                logger.info(f"Scraping r/{subreddit_name} for '{self.search_terms}'")

                subreddit = self.reddit.subreddit(subreddit_name)

                # Search for posts containing our search terms
                search_results = subreddit.search(
                    self.search_terms,
                    sort="new",
                    time_filter="day",
                    limit=limit_per_subreddit,
                )

                for post in search_results:
                    # Check if post is from last 24 hours
                    post_time = datetime.fromtimestamp(post.created_utc)
                    if post_time < yesterday:
                        continue

                    # Get top comment if available
                    top_comment_text = None
                    try:
                        if post.num_comments > 0:
                            post.comments.replace_more(limit=0)
                            if post.comments:
                                top_comment = post.comments[0]
                                top_comment_text = top_comment.body[
                                    :500
                                ]  # Limit length
                    except Exception as e:
                        logger.debug(
                            f"Could not fetch comments for post {post.id}: {e}"
                        )

                    post_data = {
                        "id": post.id,
                        "title": post.title,
                        "content": post.selftext if post.selftext else top_comment_text,
                        "author": str(post.author) if post.author else "[deleted]",
                        "subreddit": subreddit_name,
                        "created_utc": post_time,
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "url": f"https://reddit.com{post.permalink}",
                        "upvote_ratio": getattr(post, "upvote_ratio", None),
                        "is_self_post": post.is_self,
                    }

                    all_posts.append(post_data)

                logger.info(
                    f"Found {len([p for p in all_posts if p['subreddit'] == subreddit_name])} posts in r/{subreddit_name}"
                )

            logger.info(f"Successfully scraped {len(all_posts)} total Reddit posts")
            return all_posts

        except Exception as e:
            logger.error(f"Error scraping Reddit: {str(e)}")
            return self._generate_mock_posts(
                limit_per_subreddit // len(self.subreddits)
            )

    def _generate_mock_posts(self, limit: int) -> List[Dict[str, Any]]:
        """Generate mock Reddit posts for development/testing."""
        import random

        mock_posts = []
        base_time = datetime.now()

        sample_titles = [
            "Iran-Israel tensions escalate following latest diplomatic developments",
            "Analysis: How Iran-Israel conflict affects regional stability in Middle East",
            "Breaking: International community responds to Iran-Israel situation",
            "Expert discussion: Iran-Israel relations and their global implications",
            "Update: New developments in Iran-Israel diplomatic communications",
        ]

        sample_comments = [
            "This is a concerning development that could affect the entire region...",
            "The international community needs to step in before this escalates further.",
            "Historical context is important to understand these current tensions.",
            "Economic implications of this conflict are far-reaching.",
            "Both sides need to return to diplomatic solutions.",
        ]

        sample_authors = [
            "NewsWatcher",
            "MiddleEastExpert",
            "DiplomaticAnalyst",
            "RegionalObserver",
            "PolicyStudent",
        ]

        for i, subreddit in enumerate(self.subreddits):
            for j in range(min(limit, len(sample_titles))):
                idx = i * len(sample_titles) + j
                if idx >= len(sample_titles):
                    break

                mock_post = {
                    "id": f"mock_reddit_{idx}",
                    "title": sample_titles[j],
                    "content": sample_comments[j] if j < len(sample_comments) else None,
                    "author": sample_authors[j % len(sample_authors)],
                    "subreddit": subreddit,
                    "created_utc": base_time - timedelta(hours=j * 2),
                    "score": random.randint(50, 1000),
                    "num_comments": random.randint(10, 200),
                    "url": f"https://reddit.com/r/{subreddit}/comments/mock_reddit_{idx}/",
                    "upvote_ratio": round(random.uniform(0.7, 0.95), 2),
                    "is_self_post": j % 2 == 0,
                }
                mock_posts.append(mock_post)

        return mock_posts

    def scrape_and_format(self, limit_per_subreddit: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape Reddit posts and format them for database insertion.

        Args:
            limit_per_subreddit: Maximum number of posts to scrape per subreddit

        Returns:
            List of formatted post dictionaries
        """
        posts = self.scrape_posts(limit_per_subreddit)
        formatted_posts = []

        for post in posts:
            # Use title as content if no self-text or comment available
            content = post["content"] or post["title"]

            formatted_post = {
                "external_id": post["id"],
                "title": post["title"],
                "content": content,
                "author": post["author"],
                "published_date": post["created_utc"],
                "source_url": post["url"],
                "platform": "reddit",
                "metadata": {
                    "subreddit": post["subreddit"],
                    "score": post["score"],
                    "num_comments": post["num_comments"],
                    "upvote_ratio": post["upvote_ratio"],
                    "is_self_post": post["is_self_post"],
                },
            }
            formatted_posts.append(formatted_post)

        return formatted_posts


def main():
    """Main function for testing the scraper."""
    scraper = RedditScraper()
    posts = scraper.scrape_posts(limit_per_subreddit=5)

    print(f"Scraped {len(posts)} Reddit posts:")
    for post in posts[:3]:  # Show first 3 posts
        print(f"ID: {post['id']}")
        print(f"Subreddit: r/{post['subreddit']}")
        print(f"Author: u/{post['author']}")
        print(f"Title: {post['title']}")
        print(f"Content: {(post['content'] or 'No content')[:100]}...")
        print(f"Score: {post['score']}, Comments: {post['num_comments']}")
        print(f"Created: {post['created_utc']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
