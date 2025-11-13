"""
Utility functions for data management and blog post discovery
"""

import re
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import config
import feedparser
from datetime import datetime
import time


def generate_bibtex(paper: Dict) -> str:
    """Generate BibTeX citation for a paper"""
    # Use provided bibtex if available
    if paper.get('bibtex'):
        return paper['bibtex']

    # Otherwise, generate basic bibtex
    title = paper.get('title', 'Untitled').replace('{', '').replace('}', '')
    year = paper.get('year', 'n.d.')

    # Create author list
    authors = paper.get('authors', [])
    if authors:
        author_names = ' and '.join([a.get('name', 'Unknown') for a in authors[:5]])
    else:
        author_names = 'Unknown'

    # Generate citation key
    first_author = authors[0].get('name', 'Unknown').split()[-1] if authors else 'Unknown'
    cite_key = f"{first_author}{year}"

    venue = paper.get('venue', 'Unknown')

    bibtex = f"""@article{{{cite_key},
  title={{{title}}},
  author={{{author_names}}},
  year={{{year}}},
  venue={{{venue}}}
}}"""

    return bibtex


def format_authors(authors: List[Dict], max_authors: int = 5) -> str:
    """Format author list for display"""
    if not authors:
        return "Unknown authors"

    author_names = [a.get('name', 'Unknown') for a in authors[:max_authors]]
    formatted = ', '.join(author_names)

    if len(authors) > max_authors:
        formatted += f" +{len(authors) - max_authors} more"

    return formatted


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text with ellipsis"""
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length].rsplit(' ', 1)[0] + '...'


def extract_year_from_query(query: str) -> Optional[int]:
    """Extract year from search query if present"""
    # Look for 4-digit year
    year_match = re.search(r'\b(19|20)\d{2}\b', query)
    if year_match:
        return int(year_match.group())
    return None


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Highlight keywords in text (for markdown display)"""
    highlighted = text
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        highlighted = pattern.sub(f"**{keyword}**", highlighted)
    return highlighted


class BlogPostSearcher:
    """Search for research blog posts from trusted sources using RSS feeds"""

    def __init__(self):
        self.trusted_sources = config.TRUSTED_BLOG_SOURCES
        # Map of blog sources to their RSS feed URLs
        self.rss_feeds = {
            'Lilian Weng\'s Blog': 'https://lilianweng.github.io/index.xml',
            'OpenAI Research': 'https://openai.com/blog/rss.xml',
            'Hugging Face Blog': 'https://huggingface.co/blog/feed.xml',
            'Google AI Blog': 'https://blog.research.google/feeds/posts/default',
            'Distill.pub': 'https://distill.pub/rss.xml',
            'The Gradient': 'https://thegradient.pub/rss/',
            'Sebastian Raschka': 'https://sebastianraschka.com/blog/index.xml',
        }
        self.cache = {}  # Simple cache to avoid re-fetching feeds
        self.cache_ttl = 3600  # 1 hour cache

    def search_blogs(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for blog posts related to query using RSS feeds
        Real implementation using feedparser
        """
        all_posts = []
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        # Fetch from RSS feeds
        for source_name, feed_url in self.rss_feeds.items():
            try:
                posts = self._fetch_rss_feed(feed_url, source_name)
                # Filter posts by relevance to query
                relevant_posts = [
                    post for post in posts
                    if self._is_relevant(post, query_terms)
                ]
                all_posts.extend(relevant_posts)
            except Exception as e:
                print(f"Error fetching {source_name}: {e}")
                continue

        # Sort by relevance score and date
        all_posts.sort(key=lambda x: (x.get('relevance_score', 0), x.get('date', '')), reverse=True)

        return all_posts[:max_results]

    def _fetch_rss_feed(self, feed_url: str, source_name: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        cache_key = feed_url
        current_time = time.time()

        # Check cache
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if current_time - cache_time < self.cache_ttl:
                return cached_data

        # Fetch feed
        try:
            feed = feedparser.parse(feed_url)
            posts = []

            for entry in feed.entries[:20]:  # Limit to recent 20 posts per feed
                # Parse date
                date_str = 'N/A'
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        date_obj = datetime(*entry.published_parsed[:6])
                        date_str = date_obj.strftime('%Y-%m-%d')
                    except (TypeError, ValueError) as e:
                        # Invalid date format - keep default 'N/A'
                        pass
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    try:
                        date_obj = datetime(*entry.updated_parsed[:6])
                        date_str = date_obj.strftime('%Y-%m-%d')
                    except (TypeError, ValueError) as e:
                        # Invalid date format - keep default 'N/A'
                        pass

                # Extract snippet from summary or description
                snippet = ''
                if hasattr(entry, 'summary'):
                    snippet = entry.summary
                elif hasattr(entry, 'description'):
                    snippet = entry.description

                # Clean HTML from snippet
                if snippet:
                    snippet = clean_html(snippet)[:300]

                post = {
                    'title': entry.get('title', 'Untitled'),
                    'url': entry.get('link', ''),
                    'source': source_name,
                    'snippet': snippet,
                    'date': date_str,
                    'type': 'blog_post'
                }

                posts.append(post)

            # Update cache
            self.cache[cache_key] = (posts, current_time)
            return posts

        except Exception as e:
            print(f"Error parsing feed {feed_url}: {e}")
            return []

    def _is_relevant(self, post: Dict, query_terms: set) -> bool:
        """
        Check if blog post is relevant to query
        Returns True if query terms appear in title or snippet
        """
        title = post.get('title', '').lower()
        snippet = post.get('snippet', '').lower()

        # Combine title and snippet for searching
        content = f"{title} {snippet}"

        # Calculate relevance score
        matches = sum(1 for term in query_terms if term in content)

        if matches > 0:
            # Calculate relevance score (0-1)
            relevance = matches / len(query_terms) if query_terms else 0
            post['relevance_score'] = relevance
            return True

        return False

    def _search_site(self, query: str, site: str, max_results: int = 2) -> List[Dict]:
        """
        Legacy method - now uses RSS feeds instead
        Kept for backward compatibility
        """
        return self.search_blogs(query, max_results)

    def get_arxiv_blog_posts(self, paper_id: str) -> List[Dict]:
        """Get blog posts discussing a specific arXiv paper"""
        # Search for blog posts mentioning the arXiv ID
        return self.search_blogs(f"arxiv {paper_id}", max_results=5)


def calculate_relevance_score(paper: Dict, query: str) -> float:
    """
    Calculate relevance score between paper and query
    Based on keyword matching in title and abstract
    """
    query_terms = query.lower().split()

    title = (paper.get('title') or '').lower()
    abstract = (paper.get('abstract') or '').lower()

    # Count matches in title (weighted higher)
    title_matches = sum(1 for term in query_terms if term in title)
    abstract_matches = sum(1 for term in query_terms if term in abstract)

    # Calculate score
    max_possible_matches = len(query_terms)
    if max_possible_matches == 0:
        return 0.0

    title_score = (title_matches / max_possible_matches) * 0.6
    abstract_score = (abstract_matches / max_possible_matches) * 0.4

    return min(title_score + abstract_score, 1.0)


def clean_html(html_text: str) -> str:
    """Clean HTML tags from text"""
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.get_text()


def validate_url(url: str) -> bool:
    """Validate if URL is accessible"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except (requests.RequestException, Exception) as e:
        # URL is not accessible (network error, timeout, invalid URL, etc.)
        return False


def deduplicate_by_title(items: List[Dict], title_key: str = 'title') -> List[Dict]:
    """Remove duplicates based on normalized title"""
    seen_titles = set()
    unique = []

    for item in items:
        title = item.get(title_key, '')
        normalized = re.sub(r'[^a-z0-9]', '', title.lower())

        if normalized and normalized not in seen_titles:
            seen_titles.add(normalized)
            unique.append(item)

    return unique


def parse_arxiv_id(text: str) -> Optional[str]:
    """Extract arXiv ID from text"""
    # Pattern: arxiv:YYMM.NNNNN or YYMM.NNNNN
    pattern = r'(?:arxiv:)?(\d{4}\.\d{4,5})'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None


def format_venue(venue: str) -> str:
    """Format venue name for display"""
    if not venue or venue == 'Unknown':
        return 'N/A'

    # Truncate long venue names
    if len(venue) > 30:
        return venue[:27] + '...'

    return venue


def get_paper_age_category(year: int, current_year: int = None) -> str:
    """Categorize paper by age"""
    import datetime
    current_year = current_year or datetime.datetime.now().year

    age = current_year - year

    if age < 0:
        return 'Future'
    elif age <= 1:
        return 'Very Recent'
    elif age <= 3:
        return 'Recent'
    elif age <= 5:
        return 'Moderate'
    elif age <= 10:
        return 'Established'
    else:
        return 'Classic'
