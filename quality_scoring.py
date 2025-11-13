"""
Paper quality scoring and ranking algorithms
"""

from typing import Dict, List
import config
from datetime import datetime


class PaperQualityScorer:
    """Calculate quality scores for research papers"""

    def __init__(self, current_year: int = None):
        self.current_year = current_year or datetime.now().year

    def calculate_score(self, paper: Dict) -> float:
        """
        Calculate comprehensive quality score for a paper

        Combines multiple signals:
        - Citations (40%): Age-adjusted citations + citation velocity
        - Author reputation (25%): H-index and institutional affiliations
        - Venue quality (20%): Conference/journal rankings
        - Recency (10%): Publication date
        - Additional signals (5%): GitHub stars, etc.
        """

        # Citation component (40%)
        citation_score = self._calculate_citation_score(paper)

        # Author component (25%)
        author_score = self._calculate_author_score(paper)

        # Venue component (20%)
        venue_score = self._calculate_venue_score(paper)

        # Recency component (10%)
        recency_score = self._calculate_recency_score(paper)

        # Additional signals (5%)
        additional_score = self._calculate_additional_signals(paper)

        # Weighted combination
        final_score = (
            config.QUALITY_WEIGHTS['citations'] * citation_score +
            config.QUALITY_WEIGHTS['author_reputation'] * author_score +
            config.QUALITY_WEIGHTS['venue_quality'] * venue_score +
            config.QUALITY_WEIGHTS['recency'] * recency_score +
            config.QUALITY_WEIGHTS['additional_signals'] * additional_score
        )

        return round(final_score, 3)

    def _calculate_citation_score(self, paper: Dict) -> float:
        """Calculate citation-based score"""
        citations = paper.get('citations', 0) or 0

        # Handle invalid citation counts (negative values)
        if citations < 0:
            citations = 0

        year = paper.get('year', self.current_year)

        # Age-adjusted normalization
        normalized_citations = self._normalize_citations_by_age(citations, year)

        # Citation velocity bonus (if available)
        velocity_bonus = 0
        influential_citations = paper.get('influential_citations', 0) or 0

        # Handle invalid influential citations
        if influential_citations < 0:
            influential_citations = 0

        if influential_citations > 0 and citations > 0:
            # Use influential citations as proxy for velocity
            velocity_ratio = influential_citations / max(citations, 1)
            velocity_bonus = min(velocity_ratio * 0.5, 0.3)  # Max 30% bonus

        # Combine: 70% normalized citations + 30% velocity
        citation_component = min(0.7 * normalized_citations + velocity_bonus, 1.0)

        return citation_component

    def _normalize_citations_by_age(self, citations: int, pub_year: int) -> float:
        """Normalize citations based on paper age"""
        # Handle None or negative citations (from arXiv, PubMed, or invalid data)
        if citations is None or citations < 0:
            citations = 0

        if not pub_year or pub_year > self.current_year:
            return 0

        years_old = self.current_year - pub_year

        # Get age-appropriate threshold
        threshold = self._get_citation_threshold(years_old)

        # Normalize to 0-1 scale (threshold * 2 for generous scoring)
        normalized = min(float(citations) / (threshold * 2), 1.0)

        return normalized

    def _get_citation_threshold(self, years_old: int) -> int:
        """Get expected citation count for paper age"""
        for max_years, threshold in sorted(config.CITATION_THRESHOLDS.items()):
            if years_old <= max_years:
                return threshold
        return config.CITATION_THRESHOLDS[100]  # Default for very old papers

    def _calculate_author_score(self, paper: Dict) -> float:
        """Calculate author reputation score"""
        authors = paper.get('authors', [])

        if not authors:
            return 0.3  # Default for unknown authors

        # Check for top institutions
        has_top_institution = self._has_top_institution(paper)

        # Base score
        author_score = 0.4

        # Bonus for recognized institution
        if has_top_institution:
            author_score += 0.4

        # Bonus for multiple authors (collaboration signal)
        if len(authors) >= 3:
            author_score += 0.1

        # Bonus if author H-index available
        max_h_index = 0
        for author in authors:
            h_index = author.get('hIndex', 0) or 0
            max_h_index = max(max_h_index, h_index)

        if max_h_index > 0:
            h_index_score = min(max_h_index / 50, 0.3)  # Max 30% bonus
            author_score += h_index_score

        return min(author_score, 1.0)

    def _has_top_institution(self, paper: Dict) -> bool:
        """Check if any author is from a top institution"""
        authors = paper.get('authors', [])

        for author in authors:
            affiliation = author.get('affiliation', '') or ''
            for institution in config.TOP_INSTITUTIONS:
                if institution.lower() in affiliation.lower():
                    return True

        # Also check venue for institutional signals
        venue = paper.get('venue', '') or ''
        for institution in config.TOP_INSTITUTIONS:
            if institution.lower() in venue.lower():
                return True

        return False

    def _calculate_venue_score(self, paper: Dict) -> float:
        """Calculate venue quality score"""
        venue = paper.get('venue', '').strip()

        if not venue or venue == 'Unknown':
            return 0.3  # Default for unknown venue

        # Check tier 1 venues
        for top_venue in config.TIER_1_VENUES:
            if top_venue.lower() in venue.lower():
                return 1.0

        # Check tier 2 venues
        for mid_venue in config.TIER_2_VENUES:
            if mid_venue.lower() in venue.lower():
                return 0.7

        # arXiv preprints (not peer-reviewed)
        if 'arxiv' in venue.lower():
            return 0.3

        # Workshop or poster
        if any(word in venue.lower() for word in ['workshop', 'poster', 'demo']):
            return 0.4

        # Default for other venues
        return 0.5

    def _calculate_recency_score(self, paper: Dict) -> float:
        """Calculate recency score (newer papers scored higher)"""
        year = paper.get('year')

        if not year:
            return 0.3  # Default for unknown year

        years_old = self.current_year - year

        if years_old < 0:
            return 0  # Future date (error)
        elif years_old <= 1:
            return 1.0  # Very recent
        elif years_old <= 3:
            return 0.8  # Recent
        elif years_old <= 5:
            return 0.6  # Moderate
        elif years_old <= 10:
            return 0.4  # Older
        else:
            return 0.2  # Classic (may still be valuable)

    def _calculate_additional_signals(self, paper: Dict) -> float:
        """Calculate score from additional signals"""
        score = 0.0

        # GitHub implementation available
        if paper.get('implementations'):
            repos = paper['implementations'].get('repositories', [])
            if repos:
                # Use stars from most popular repo
                max_stars = max([r.get('stars', 0) for r in repos], default=0)
                star_score = min(max_stars / 1000, 0.5)  # Max 50% from stars
                score += star_score

                # Bonus for official implementation
                has_official = any(r.get('is_official') for r in repos)
                if has_official:
                    score += 0.3

        # PDF availability
        if paper.get('pdf_url'):
            score += 0.2

        return min(score, 1.0)

    def rank_papers(self, papers: List[Dict]) -> List[Dict]:
        """Rank papers by quality score"""
        # Calculate scores
        for paper in papers:
            paper['quality_score'] = self.calculate_score(paper)

        # Sort by score (descending)
        ranked = sorted(papers, key=lambda x: x['quality_score'], reverse=True)

        return ranked

    def filter_by_quality(self, papers: List[Dict], min_score: float = 0.3) -> List[Dict]:
        """Filter papers by minimum quality score"""
        return [p for p in papers if p.get('quality_score', 0) >= min_score]


class PaperFilter:
    """Filter papers based on various criteria"""

    @staticmethod
    def filter_by_year(papers: List[Dict], min_year: int, max_year: int) -> List[Dict]:
        """Filter papers by publication year range"""
        return [
            p for p in papers
            if p.get('year') and min_year <= p['year'] <= max_year
        ]

    @staticmethod
    def filter_by_citations(papers: List[Dict], min_citations: int) -> List[Dict]:
        """Filter papers by minimum citation count"""
        return [
            p for p in papers
            if (p.get('citations') or 0) >= min_citations
        ]

    @staticmethod
    def filter_by_venue(papers: List[Dict], venues: List[str]) -> List[Dict]:
        """Filter papers by venue"""
        if not venues:
            return papers

        filtered = []
        for paper in papers:
            paper_venue = (paper.get('venue') or '').lower()
            for venue in venues:
                if venue.lower() in paper_venue:
                    filtered.append(paper)
                    break

        return filtered

    @staticmethod
    def filter_by_domain(papers: List[Dict], domains: List[str]) -> List[Dict]:
        """Filter papers by research domain keywords"""
        if not domains:
            return papers

        filtered = []
        for paper in papers:
            # Check title and abstract for domain keywords
            text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

            for domain in domains:
                domain_keywords = config.DOMAIN_KEYWORDS.get(domain, [])
                for keyword in domain_keywords:
                    if keyword.lower() in text:
                        filtered.append(paper)
                        break
                else:
                    continue
                break

        return filtered

    @staticmethod
    def apply_filters(
        papers: List[Dict],
        min_year: int = None,
        max_year: int = None,
        min_citations: int = None,
        venues: List[str] = None,
        domains: List[str] = None
    ) -> List[Dict]:
        """Apply multiple filters to papers"""
        filtered = papers

        if min_year is not None and max_year is not None:
            filtered = PaperFilter.filter_by_year(filtered, min_year, max_year)

        if min_citations is not None:
            filtered = PaperFilter.filter_by_citations(filtered, min_citations)

        if venues:
            filtered = PaperFilter.filter_by_venue(filtered, venues)

        if domains:
            filtered = PaperFilter.filter_by_domain(filtered, domains)

        return filtered
