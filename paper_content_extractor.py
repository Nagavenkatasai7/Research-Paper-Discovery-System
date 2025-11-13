"""
Paper Content Extractor - 2025 Enhancement
Extracts rich content from paper metadata (TLDR + Abstract) without PDF download
"""

from typing import Dict, Optional
import os


class PaperContentExtractor:
    """
    Extract analyzable content from paper metadata
    No PDF download needed - uses TLDR + Abstract + Metadata
    """

    def __init__(self):
        self.output_dir = "papers_metadata"
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_content(self, paper: Dict, paper_id: str) -> Dict:
        """
        Extract rich content from paper metadata

        Args:
            paper: Paper metadata dict with title, abstract, tldr, authors, etc.
            paper_id: Unique identifier for the paper

        Returns:
            {
                'success': bool,
                'content': str,  # Rich formatted content
                'file_path': str,  # Path to saved content file
                'content_type': str,  # 'metadata' or 'pdf' or 'scraped'
                'has_tldr': bool,
                'has_abstract': bool,
                'message': str
            }
        """
        try:
            # Build rich content from metadata
            content_parts = []

            # Title
            title = paper.get('title', 'Unknown Title')
            content_parts.append(f"# {title}\n")

            # Authors
            authors = paper.get('authors', [])
            if authors:
                author_names = [a.get('name', 'Unknown') for a in authors]
                content_parts.append(f"**Authors:** {', '.join(author_names)}\n")

            # Year and Venue
            year = paper.get('year', 'N/A')
            venue = paper.get('venue', 'Unknown')
            content_parts.append(f"**Year:** {year} | **Venue:** {venue}\n")

            # Citations
            citations = paper.get('citations', 0)
            influential = paper.get('influential_citations', 0)
            content_parts.append(f"**Citations:** {citations:,} (Influential: {influential:,})\n")

            # TL;DR (AI-Generated Summary)
            has_tldr = False
            tldr = paper.get('tldr')
            if tldr:
                has_tldr = True
                content_parts.append(f"\n## TL;DR (AI Summary)\n{tldr}\n")

            # Abstract
            has_abstract = False
            abstract = paper.get('abstract')
            if abstract and abstract != 'No abstract available':
                has_abstract = True
                content_parts.append(f"\n## Abstract\n{abstract}\n")

            # Fields of Study
            fields = paper.get('fields_of_study', [])
            if fields:
                content_parts.append(f"\n**Fields of Study:** {', '.join(fields)}\n")

            # DOI and Links
            doi = paper.get('doi')
            if doi:
                content_parts.append(f"\n**DOI:** {doi}\n")

            arxiv_id = paper.get('arxiv_id')
            if arxiv_id:
                content_parts.append(f"**arXiv ID:** {arxiv_id}\n")

            # Combine all parts
            full_content = '\n'.join(content_parts)

            # Save to file
            file_path = os.path.join(self.output_dir, f"{paper_id}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            # Determine quality level
            if has_tldr and has_abstract:
                quality = "excellent"
                message = "✅ Rich content extracted: TLDR + Abstract + Metadata"
            elif has_abstract:
                quality = "good"
                message = "✅ Good content extracted: Abstract + Metadata"
            elif has_tldr:
                quality = "fair"
                message = "⚠️ Fair content extracted: TLDR + Metadata (no abstract)"
            else:
                quality = "minimal"
                message = "⚠️ Minimal content: Metadata only (no TLDR or abstract)"

            return {
                'success': True,
                'content': full_content,
                'file_path': file_path,
                'content_type': 'metadata',
                'has_tldr': has_tldr,
                'has_abstract': has_abstract,
                'quality': quality,
                'message': message,
                'word_count': len(full_content.split())
            }

        except Exception as e:
            return {
                'success': False,
                'content': None,
                'file_path': None,
                'content_type': None,
                'has_tldr': False,
                'has_abstract': False,
                'quality': 'error',
                'message': f"Content extraction failed: {str(e)}"
            }

    def can_analyze(self, extraction_result: Dict) -> bool:
        """
        Check if extracted content is sufficient for analysis
        """
        if not extraction_result.get('success'):
            return False

        quality = extraction_result.get('quality', 'minimal')

        # We can analyze if we have at least abstract OR tldr
        return quality in ['excellent', 'good', 'fair']

    def get_content_summary(self, extraction_result: Dict) -> str:
        """
        Get human-readable summary of content quality
        """
        if not extraction_result.get('success'):
            return "❌ No content available"

        quality = extraction_result.get('quality', 'minimal')
        word_count = extraction_result.get('word_count', 0)

        quality_labels = {
            'excellent': '🌟 Excellent',
            'good': '✅ Good',
            'fair': '⚠️ Fair',
            'minimal': '⚠️ Minimal',
            'error': '❌ Error'
        }

        label = quality_labels.get(quality, '❓ Unknown')
        return f"{label} content quality ({word_count:,} words)"
