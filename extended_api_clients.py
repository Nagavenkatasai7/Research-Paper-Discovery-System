"""
Extended API clients for OpenAlex, CORE, Crossref, and PubMed
"""

import time
import requests
from typing import List, Dict, Optional
from api_clients import RateLimiter
import config


class OpenAlexClient:
    """Client for OpenAlex API - 240M+ papers, completely free"""

    def __init__(self, email: Optional[str] = None):
        self.base_url = "https://api.openalex.org"
        self.email = email
        self.rate_limiter = RateLimiter(0.1)  # 10 requests/second

    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search OpenAlex papers"""
        self.rate_limiter.wait()

        try:
            params = {
                'search': query,
                'per_page': min(max_results, 200),
                'filter': 'type:article',
                'sort': 'cited_by_count:desc'
            }

            # Add polite pool access
            if self.email:
                params['mailto'] = self.email

            response = requests.get(
                f"{self.base_url}/works",
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                papers = []

                for work in data.get('results', [])[:max_results]:
                    papers.append(self._normalize_paper(work))

                return papers
            else:
                print(f"OpenAlex error: {response.status_code}")
                return []

        except Exception as e:
            print(f"OpenAlex search error: {e}")
            return []

    def _normalize_paper(self, work: Dict) -> Dict:
        """Normalize OpenAlex paper to standard format"""
        # Extract DOI
        doi = work.get('doi', '').replace('https://doi.org/', '') if work.get('doi') else None

        # Extract authors
        authors = []
        for authorship in work.get('authorships', []):
            author_info = authorship.get('author') or {}
            institutions = authorship.get('institutions', [])
            affiliation = institutions[0].get('display_name') if institutions else None

            authors.append({
                'name': author_info.get('display_name', 'Unknown'),
                'authorId': author_info.get('id'),
                'affiliation': affiliation
            })

        # Extract venue
        venue = 'Unknown'
        if work.get('primary_location'):
            source = work['primary_location'].get('source') or {}
            venue = source.get('display_name', 'Unknown')

        # Extract PDF URL
        pdf_url = None
        if work.get('open_access', {}).get('is_oa'):
            pdf_url = work.get('primary_location', {}).get('pdf_url')

        # Extract year
        year = work.get('publication_year')

        return {
            'title': work.get('title', 'Untitled'),
            'authors': authors,
            'abstract': work.get('abstract', 'No abstract available'),
            'year': year,
            'citations': work.get('cited_by_count', 0),
            'influential_citations': None,
            'venue': venue,
            'pdf_url': pdf_url,
            'doi': doi,
            'arxiv_id': None,
            'paper_id': work.get('id'),
            'fields_of_study': [concept.get('display_name') for concept in work.get('concepts', [])[:5]],
            'source': 'OpenAlex',
            'bibtex': None,
            'open_access': work.get('open_access', {}).get('is_oa', False)
        }


class CrossrefClient:
    """Client for Crossref API - 150M+ DOI records"""

    def __init__(self, email: Optional[str] = None):
        self.base_url = "https://api.crossref.org"
        self.email = email
        self.rate_limiter = RateLimiter(1.0)  # Be polite

    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search Crossref papers"""
        self.rate_limiter.wait()

        try:
            params = {
                'query': query,
                'rows': min(max_results, 1000),
                'sort': 'score',
                'order': 'desc'
            }

            headers = {}
            if self.email:
                headers['User-Agent'] = f'ResearchPaperDiscovery/1.0 (mailto:{self.email})'

            response = requests.get(
                f"{self.base_url}/works",
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                papers = []

                for item in data.get('message', {}).get('items', [])[:max_results]:
                    papers.append(self._normalize_paper(item))

                return papers
            else:
                print(f"Crossref error: {response.status_code}")
                return []

        except Exception as e:
            print(f"Crossref search error: {e}")
            return []

    def _normalize_paper(self, item: Dict) -> Dict:
        """Normalize Crossref paper to standard format"""
        # Extract authors
        authors = []
        for author in item.get('author', []):
            authors.append({
                'name': f"{author.get('given', '')} {author.get('family', '')}".strip(),
                'authorId': None,
                'affiliation': author.get('affiliation', [{}])[0].get('name') if author.get('affiliation') else None
            })

        # Extract year
        year = None
        if item.get('published'):
            date_parts = item['published'].get('date-parts', [[]])[0]
            year = date_parts[0] if date_parts else None

        # Extract title
        titles = item.get('title', [])
        title = titles[0] if titles else 'Untitled'

        # Extract venue
        venue = item.get('container-title', ['Unknown'])[0] if item.get('container-title') else 'Unknown'

        return {
            'title': title,
            'authors': authors,
            'abstract': item.get('abstract', 'No abstract available'),
            'year': year,
            'citations': item.get('is-referenced-by-count', 0),
            'influential_citations': None,
            'venue': venue,
            'pdf_url': None,  # Crossref doesn't provide direct PDF links
            'doi': item.get('DOI'),
            'arxiv_id': None,
            'paper_id': item.get('DOI'),
            'fields_of_study': item.get('subject', []),
            'source': 'Crossref',
            'bibtex': None,
            'publisher': item.get('publisher')
        }


class COREClient:
    """Client for CORE API - Open Access papers"""

    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://api.core.ac.uk/v3"
        self.api_key = api_key
        self.rate_limiter = RateLimiter(2.0)  # 1 request per 2 seconds for free tier

    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search CORE papers"""
        if not self.api_key:
            print("CORE API key not configured, skipping")
            return []

        self.rate_limiter.wait()

        try:
            # CORE API v3 uses API key as query parameter, NOT bearer token
            # Endpoint: /search/works with q, apiKey, and limit as query parameters
            params = {
                'q': query,
                'apiKey': self.api_key,
                'limit': min(max_results, 100)
            }

            response = requests.get(
                f"{self.base_url}/search/works",
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                papers = []

                for result in data.get('results', [])[:max_results]:
                    papers.append(self._normalize_paper(result))

                return papers
            else:
                print(f"CORE error: {response.status_code} - {response.text[:200]}")
                return []

        except Exception as e:
            print(f"CORE search error: {e}")
            return []

    def _normalize_paper(self, result: Dict) -> Dict:
        """Normalize CORE paper to standard format"""
        # Extract authors
        authors = []
        for author in result.get('authors', []):
            authors.append({
                'name': author.get('name', 'Unknown'),
                'authorId': None
            })

        return {
            'title': result.get('title') or 'Untitled',
            'authors': authors,
            'abstract': result.get('abstract') or 'No abstract available',
            'year': result.get('yearPublished'),
            'citations': None,  # CORE doesn't provide citation counts
            'influential_citations': None,
            'venue': result.get('publisher') or 'Unknown',
            'pdf_url': result.get('downloadUrl'),
            'doi': result.get('doi'),
            'arxiv_id': None,
            'paper_id': result.get('id'),
            'fields_of_study': result.get('subjects') or [],
            'source': 'CORE',
            'bibtex': None,
            'open_access': True  # CORE focuses on OA
        }


class PubMedClient:
    """Client for PubMed/NCBI E-utilities - Biomedical papers"""

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.email = email
        self.api_key = api_key
        self.rate_limiter = RateLimiter(0.34 if not api_key else 0.1)  # 3/sec or 10/sec with key

    def search_papers(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search PubMed papers"""
        if not self.email:
            print("PubMed requires email, skipping")
            return []

        try:
            # First, search for IDs
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'email': self.email
            }

            if self.api_key:
                search_params['api_key'] = self.api_key

            self.rate_limiter.wait()
            search_response = requests.get(
                f"{self.base_url}/esearch.fcgi",
                params=search_params,
                timeout=15
            )

            if search_response.status_code != 200:
                return []

            search_data = search_response.json()
            id_list = search_data.get('esearchresult', {}).get('idlist', [])

            if not id_list:
                return []

            # Fetch details for IDs
            self.rate_limiter.wait()
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(id_list),
                'retmode': 'xml',
                'email': self.email
            }

            if self.api_key:
                fetch_params['api_key'] = self.api_key

            fetch_response = requests.get(
                f"{self.base_url}/efetch.fcgi",
                params=fetch_params,
                timeout=15
            )

            if fetch_response.status_code == 200:
                return self._parse_pubmed_xml(fetch_response.text)
            else:
                return []

        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict]:
        """Parse PubMed XML response"""
        from xml.etree import ElementTree as ET

        papers = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall('.//PubmedArticle'):
                paper = self._extract_paper_from_xml(article)
                if paper:
                    papers.append(paper)

        except Exception as e:
            print(f"PubMed XML parsing error: {e}")

        return papers

    def _extract_paper_from_xml(self, article) -> Optional[Dict]:
        """Extract paper info from XML element"""
        try:
            # Title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else 'Untitled'

            # Abstract
            abstract_elem = article.find('.//Abstract/AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else 'No abstract available'

            # Authors
            authors = []
            for author in article.findall('.//Author'):
                last_name = author.find('LastName')
                fore_name = author.find('ForeName')
                if last_name is not None:
                    name = f"{fore_name.text if fore_name is not None else ''} {last_name.text}".strip()
                    authors.append({'name': name, 'authorId': None})

            # Year
            year_elem = article.find('.//PubDate/Year')
            year = int(year_elem.text) if year_elem is not None else None

            # Journal
            journal_elem = article.find('.//Journal/Title')
            venue = journal_elem.text if journal_elem is not None else 'Unknown'

            # PMID
            pmid_elem = article.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else None

            # DOI
            doi = None
            for article_id in article.findall('.//ArticleId'):
                if article_id.get('IdType') == 'doi':
                    doi = article_id.text

            return {
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'year': year,
                'citations': None,
                'influential_citations': None,
                'venue': venue,
                'pdf_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
                'doi': doi,
                'arxiv_id': None,
                'paper_id': pmid,
                'fields_of_study': ['Biomedical'],
                'source': 'PubMed',
                'bibtex': None
            }

        except Exception as e:
            print(f"Error extracting paper from XML: {e}")
            return None
