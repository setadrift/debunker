import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class YouTubeScraper:
    """YouTube scraper that fetches video transcripts and extracts keyword-relevant excerpts."""

    def __init__(self):
        self.search_query = "Iran Israel news"
        self.keywords = [
            "Iran",
            "Israel",
            "conflict",
            "tension",
            "diplomacy",
            "strike",
            "nuclear",
            "Gaza",
        ]
        self.max_results = 15
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY", "")
        self.youtube = self._initialize_youtube_api()

    def _initialize_youtube_api(self):
        """Initialize YouTube API client."""
        if not self.youtube_api_key:
            logger.warning("No YouTube API key provided, will use mock data")
            return None

        try:
            youtube = build("youtube", "v3", developerKey=self.youtube_api_key)
            logger.info("YouTube API initialized successfully")
            return youtube
        except Exception as e:
            logger.warning(f"YouTube API initialization failed: {e}")
            return None

    def search_videos(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Search for YouTube videos from the last week.

        Args:
            days_back: Number of days to look back for videos

        Returns:
            List of video metadata dictionaries
        """
        if not self.youtube:
            logger.warning("YouTube API not available, using mock data")
            return self._generate_mock_videos()

        try:
            logger.info(
                f"Searching YouTube for '{self.search_query}' in last {days_back} days"
            )

            # Calculate date filter (publishedAfter parameter)
            published_after = (
                datetime.now() - timedelta(days=days_back)
            ).isoformat() + "Z"
            logger.info(f"Searching for videos published after: {published_after}")

            # Search for videos
            search_response = (
                self.youtube.search()
                .list(
                    q=self.search_query,
                    part="id,snippet",
                    maxResults=self.max_results,
                    order="relevance",
                    type="video",
                    publishedAfter=published_after,
                    regionCode="US",  # Can be adjusted
                )
                .execute()
            )

            logger.info(
                f"YouTube API returned {len(search_response.get('items', []))} search results"
            )

            videos = []

            for search_result in search_response.get("items", []):
                video_id = search_result["id"]["videoId"]
                snippet = search_result["snippet"]

                # Get additional video statistics
                video_response = (
                    self.youtube.videos()
                    .list(part="statistics,contentDetails", id=video_id)
                    .execute()
                )

                video_stats = (
                    video_response["items"][0] if video_response["items"] else {}
                )
                statistics = video_stats.get("statistics", {})
                content_details = video_stats.get("contentDetails", {})

                video_data = {
                    "id": video_id,
                    "title": snippet["title"],
                    "channel": snippet["channelTitle"],
                    "duration": content_details.get("duration", "Unknown"),
                    "views": statistics.get("viewCount", "0"),
                    "published": snippet["publishedAt"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": snippet["thumbnails"].get("medium", {}).get("url", ""),
                    "description": snippet.get("description", "")[
                        :200
                    ],  # Limit description length
                }
                videos.append(video_data)
                logger.info(f"Added video: {snippet['title'][:50]}...")

            logger.info(f"Found {len(videos)} relevant videos")
            return videos

        except Exception as e:
            logger.error(f"Error searching YouTube videos: {str(e)}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._generate_mock_videos()

    def _parse_published_time(self, published_text: str) -> Optional[datetime]:
        """Parse YouTube's published time format to datetime."""
        try:
            now = datetime.now()

            if "hour" in published_text:
                hours = int(re.search(r"(\d+)", published_text).group(1))
                return now - timedelta(hours=hours)
            elif "day" in published_text:
                days = int(re.search(r"(\d+)", published_text).group(1))
                return now - timedelta(days=days)
            elif "week" in published_text:
                weeks = int(re.search(r"(\d+)", published_text).group(1))
                return now - timedelta(weeks=weeks)
            elif "month" in published_text:
                # Approximate months as 30 days
                months = int(re.search(r"(\d+)", published_text).group(1))
                return now - timedelta(days=months * 30)

        except (AttributeError, ValueError):
            pass

        return None

    def get_video_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            List of transcript segments or None if unavailable
        """
        try:
            # Try to get transcript in English first, then any available language
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            try:
                transcript = transcript_list.find_transcript(["en"])
                return transcript.fetch()
            except Exception:
                # Try any available transcript
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    transcript = available_transcripts[0]
                    return transcript.fetch()

        except Exception as e:
            logger.debug(f"Could not fetch transcript for video {video_id}: {str(e)}")

        return None

    def extract_keyword_excerpts(
        self, transcript: List[Dict[str, Any]], video_title: str
    ) -> List[str]:
        """
        Extract 3-sentence excerpts around keywords from transcript.

        Args:
            transcript: List of transcript segments
            video_title: Title of the video for context

        Returns:
            List of relevant excerpts
        """
        if not transcript:
            return []

        # Combine transcript into sentences - handle both dict and object formats
        try:
            if hasattr(transcript[0], "text"):
                # transcript segments are objects with .text attribute
                full_text = " ".join([segment.text for segment in transcript])
            else:
                # transcript segments are dictionaries
                full_text = " ".join([segment["text"] for segment in transcript])
        except (IndexError, KeyError, AttributeError):
            return []

        sentences = re.split(r"[.!?]+", full_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        excerpts = []

        for i, sentence in enumerate(sentences):
            # Check if sentence contains any keywords
            if any(keyword.lower() in sentence.lower() for keyword in self.keywords):
                # Extract 3-sentence excerpt (previous, current, next)
                start_idx = max(0, i - 1)
                end_idx = min(len(sentences), i + 2)

                excerpt_sentences = sentences[start_idx:end_idx]
                excerpt = ". ".join(excerpt_sentences) + "."

                # Clean up the excerpt
                excerpt = re.sub(r"\s+", " ", excerpt).strip()

                if len(excerpt) > 50:  # Only include substantial excerpts
                    excerpts.append(excerpt)

        # Remove duplicates and limit to top excerpts
        unique_excerpts = list(dict.fromkeys(excerpts))
        return unique_excerpts[:3]  # Top 3 excerpts

    def scrape_videos(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Scrape YouTube videos and their transcript excerpts.

        Args:
            limit: Maximum number of videos to process

        Returns:
            List of video data with transcript excerpts
        """
        try:
            videos = self.search_videos()

            # Check if we got mock data (which already has excerpts)
            if videos and videos[0]["id"].startswith("mock_"):
                logger.info("Using mock data with pre-generated excerpts")
                return videos[:limit]

            processed_videos = []

            for i, video in enumerate(videos[:limit]):
                logger.info(
                    f"Processing video {i+1}/{len(videos[:limit])}: {video['title'][:50]}..."
                )

                # Get transcript
                transcript = self.get_video_transcript(video["id"])

                # Extract excerpts
                excerpts = self.extract_keyword_excerpts(transcript, video["title"])

                video_data = {
                    "id": video["id"],
                    "title": video["title"],
                    "channel": video["channel"],
                    "url": video["url"],
                    "published": video["published"],
                    "duration": video["duration"],
                    "views": video["views"],
                    "description": video["description"],
                    "transcript_available": transcript is not None,
                    "excerpts": excerpts,
                    "excerpt_count": len(excerpts),
                }

                processed_videos.append(video_data)

            logger.info(
                f"Successfully processed {len(processed_videos)} YouTube videos"
            )
            return processed_videos

        except Exception as e:
            logger.error(f"Error scraping YouTube videos: {str(e)}")
            return self._generate_mock_videos()

    def _generate_mock_videos(self) -> List[Dict[str, Any]]:
        """Generate mock YouTube video data for development/testing."""
        mock_videos = [
            {
                "id": "mock_yt_1",
                "title": "Iran-Israel Tensions: Latest Diplomatic Developments Analysis",
                "channel": "News Channel International",
                "url": "https://youtube.com/watch?v=mock_yt_1",
                "published": "2 days ago",
                "duration": "15:32",
                "views": "125K views",
                "description": "Expert analysis on recent Iran-Israel diplomatic developments...",
                "transcript_available": True,
                "excerpts": [
                    "The recent escalation between Iran and Israel has raised concerns across the region. Diplomatic sources suggest that both nations are seeking de-escalation. International mediators are working around the clock.",
                    "Nuclear negotiations remain at the forefront of discussions. Iran has indicated willingness to return to talks. Israel maintains its security concerns are paramount.",
                    "Regional stability depends on finding common ground between these two nations. The conflict has implications far beyond their borders. Economic markets are closely watching developments.",
                ],
                "excerpt_count": 3,
            },
            {
                "id": "mock_yt_2",
                "title": "Breaking: Iran Israel Conflict Update - Security Council Meeting",
                "channel": "Global News Network",
                "url": "https://youtube.com/watch?v=mock_yt_2",
                "published": "1 day ago",
                "duration": "8:45",
                "views": "89K views",
                "description": "Live coverage of UN Security Council emergency session...",
                "transcript_available": True,
                "excerpts": [
                    "The UN Security Council convened an emergency session to address Iran-Israel tensions. Member states called for immediate de-escalation. Diplomatic solutions remain the preferred path forward.",
                    "Iran representative emphasized their commitment to regional peace. Israel delegation highlighted security concerns and defensive measures. Both sides agreed to continue dialogue through international channels.",
                ],
                "excerpt_count": 2,
            },
            {
                "id": "mock_yt_3",
                "title": "Middle East Analysis: Iran-Israel Nuclear Negotiations",
                "channel": "Policy Institute",
                "url": "https://youtube.com/watch?v=mock_yt_3",
                "published": "3 days ago",
                "duration": "22:15",
                "views": "67K views",
                "description": "In-depth analysis of nuclear negotiations between Iran and Israel...",
                "transcript_available": True,
                "excerpts": [
                    "Iran nuclear program remains a central issue in regional tensions. Israel has expressed ongoing security concerns about nuclear capabilities. Both nations face pressure from international community.",
                    "The diplomatic strike against escalation requires careful coordination. Regional stability depends on nuclear non-proliferation efforts. Gaza situation adds complexity to Iran-Israel relations.",
                ],
                "excerpt_count": 2,
            },
        ]

        return mock_videos

    def scrape_and_format(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Scrape YouTube videos and format them for database insertion.

        Args:
            limit: Maximum number of videos to process

        Returns:
            List of formatted video dictionaries
        """
        videos = self.scrape_videos(limit)
        formatted_videos = []

        for video in videos:
            # Combine excerpts into content
            content = (
                " | ".join(video["excerpts"])
                if video["excerpts"]
                else video["description"]
            )

            formatted_video = {
                "external_id": video["id"],
                "title": video["title"],
                "content": content,
                "author": video["channel"],
                "published_date": None,  # YouTube date parsing is complex, could be improved
                "source_url": video["url"],
                "platform": "youtube",
                "metadata": {
                    "duration": video["duration"],
                    "views": video["views"],
                    "transcript_available": video["transcript_available"],
                    "excerpt_count": video["excerpt_count"],
                    "description": video["description"],
                },
            }
            formatted_videos.append(formatted_video)

        return formatted_videos


def main():
    """Main function for testing the scraper."""
    scraper = YouTubeScraper()
    videos = scraper.scrape_videos(limit=3)

    print(f"Scraped {len(videos)} YouTube videos:")
    for video in videos:
        print(f"ID: {video['id']}")
        print(f"Title: {video['title']}")
        print(f"Channel: {video['channel']}")
        print(f"Duration: {video['duration']}")
        print(f"Transcript Available: {video['transcript_available']}")
        print(f"Excerpts ({video['excerpt_count']}):")
        for i, excerpt in enumerate(video["excerpts"][:2], 1):
            print(f"  {i}. {excerpt[:100]}...")
        print("-" * 50)


if __name__ == "__main__":
    main()
