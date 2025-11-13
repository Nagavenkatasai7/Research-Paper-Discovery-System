"""
Web Scraper for Academic Papers
Fallback when PDF download fails - scrapes content from paper URLs
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re


class PaperWebScraper:
    """Scrape academic paper content from web pages"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def scrape_paper(self, url: str, paper_id: str) -> Dict:
        """
        Scrape paper content from URL
        Returns: {
            'success': bool,
            'content': str,
            'title': str,
            'abstract': str,
            'message': str
        }
        """
        try:
            # Detect source and use appropriate scraper
            if 'arxiv.org' in url:
                return self._scrape_arxiv(url)
            elif 'semanticscholar.org' in url:
                return self._scrape_semantic_scholar(url)
            else:
                # Generic scraper for other sources
                return self._scrape_generic(url)

        except Exception as e:
            return {
                'success': False,
                'content': None,
                'title': None,
                'abstract': None,
                'message': f"Scraping failed: {str(e)}"
            }

    def _scrape_arxiv(self, url: str) -> Dict:
        """Scrape arXiv paper page"""
        try:
            # Convert PDF URL to abstract URL if needed
            if '/pdf/' in url:
                url = url.replace('/pdf/', '/abs/').replace('.pdf', '')

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_elem = soup.find('h1', class_='title')
            title = title_elem.text.replace('Title:', '').strip() if title_elem else "Unknown"

            # Extract abstract
            abstract_elem = soup.find('blockquote', class_='abstract')
            abstract = abstract_elem.text.replace('Abstract:', '').strip() if abstract_elem else ""

            # Build full content
            content = f"Title: {title}\n\nAbstract:\n{abstract}\n\n"

            # Try to get more details if available
            authors_elem = soup.find('div', class_='authors')
            if authors_elem:
                content += f"Authors: {authors_elem.text.strip()}\n\n"

            return {
                'success': True,
                'content': content,
                'title': title,
                'abstract': abstract,
                'message': 'Successfully scraped from arXiv'
            }

        except Exception as e:
            return {
                'success': False,
                'content': None,
                'title': None,
                'abstract': None,
                'message': f"arXiv scraping failed: {str(e)}"
            }

    def _scrape_semantic_scholar(self, url: str) -> Dict:
        """Scrape Semantic Scholar paper page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else "Unknown"

            # Extract abstract
            abstract_elem = soup.find('div', {'data-selenium-selector': 'paper-abstract'})
            if not abstract_elem:
                abstract_elem = soup.find('div', class_='abstract')
            abstract = abstract_elem.text.strip() if abstract_elem else ""

            # Build content
            content = f"Title: {title}\n\nAbstract:\n{abstract}\n\n"

            return {
                'success': True,
                'content': content,
                'title': title,
                'abstract': abstract,
                'message': 'Successfully scraped from Semantic Scholar'
            }

        except Exception as e:
            return {
                'success': False,
                'content': None,
                'title': None,
                'abstract': None,
                'message': f"Semantic Scholar scraping failed: {str(e)}"
            }

    def _scrape_generic(self, url: str) -> Dict:
        """Generic scraper for other academic paper URLs"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to find title (common patterns)
            title = None
            for tag in ['h1', 'title']:
                title_elem = soup.find(tag)
                if title_elem:
                    title = title_elem.text.strip()
                    break

            # Try to find abstract (common patterns)
            abstract = ""
            for class_name in ['abstract', 'Abstract', 'summary']:
                abstract_elem = soup.find(['div', 'p', 'section'], class_=class_name)
                if abstract_elem:
                    abstract = abstract_elem.text.strip()
                    break

            # Get main text content
            # Remove script and style tags
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = '\n'.join(chunk for chunk in chunks if chunk)

            # Limit content size
            content = content[:5000]

            return {
                'success': True,
                'content': content,
                'title': title or "Unknown",
                'abstract': abstract,
                'message': 'Successfully scraped from generic source'
            }

        except Exception as e:
            return {
                'success': False,
                'content': None,
                'title': None,
                'abstract': None,
                'message': f"Generic scraping failed: {str(e)}"
            }


def create_text_file_from_scraped_content(content: str, paper_id: str, output_dir: str = "papers_scraped") -> str:
    """
    Create a text file from scraped content
    Returns: file path
    """
    import os

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{paper_id}.txt")

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path
