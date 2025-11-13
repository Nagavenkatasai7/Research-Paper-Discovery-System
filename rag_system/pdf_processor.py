"""
PDF Processor Module
====================

Extracts text from PDFs with page-level granularity using PyMuPDF (fitz).
Maintains page numbers for accurate citation in Q&A.
"""

import fitz  # PyMuPDF
from typing import Dict, List, Optional
from pathlib import Path
import re


class PDFProcessor:
    """Processes PDF files and extracts text with metadata"""

    def __init__(self):
        """Initialize PDF processor"""
        pass

    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """
        Extract text from PDF with page-level granularity

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary containing:
            {
                'success': bool,
                'pages': List[Dict] with page_number, text, char_count,
                'total_pages': int,
                'full_text': str,
                'metadata': Dict with title, author, etc.,
                'message': str
            }
        """
        doc = None
        try:
            # Open PDF
            doc = fitz.open(pdf_path)

            # Extract metadata
            metadata = {
                'title': doc.metadata.get('title', 'Unknown'),
                'author': doc.metadata.get('author', 'Unknown'),
                'subject': doc.metadata.get('subject', ''),
                'keywords': doc.metadata.get('keywords', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', '')
            }

            # Extract text from each page
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]

                # Get text from page
                text = page.get_text()

                # Clean text (remove excessive whitespace)
                text = self._clean_text(text)

                pages.append({
                    'page_number': page_num + 1,  # 1-indexed
                    'text': text,
                    'char_count': len(text),
                    'word_count': len(text.split())
                })

            # Combine all text
            full_text = '\n\n'.join([p['text'] for p in pages])

            # Calculate stats
            total_chars = sum(p['char_count'] for p in pages)
            total_words = sum(p['word_count'] for p in pages)

            return {
                'success': True,
                'pages': pages,
                'total_pages': len(pages),
                'full_text': full_text,
                'metadata': metadata,
                'stats': {
                    'total_characters': total_chars,
                    'total_words': total_words,
                    'avg_chars_per_page': total_chars / len(pages) if pages else 0,
                    'avg_words_per_page': total_words / len(pages) if pages else 0
                },
                'message': f'Successfully extracted text from {len(pages)} pages'
            }

        except Exception as e:
            return {
                'success': False,
                'pages': [],
                'total_pages': 0,
                'full_text': '',
                'metadata': {},
                'stats': {},
                'message': f'Error extracting text: {str(e)}'
            }
        finally:
            # Always close the document to prevent file handle leak
            if doc is not None:
                try:
                    doc.close()
                except Exception as e:
                    # Log but don't fail - document processing already complete
                    print(f"Warning: Error closing PDF document: {e}")

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace and artifacts

        Args:
            text: Raw text from PDF

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove form feed characters
        text = text.replace('\f', '\n')

        # Remove zero-width spaces and other invisible chars
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)

        # Normalize whitespace (but preserve single newlines)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    def extract_text_by_sections(self, pdf_path: str) -> Dict:
        """
        Extract text and attempt to identify sections (Abstract, Introduction, etc.)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with extracted sections
        """
        result = self.extract_text_from_pdf(pdf_path)

        if not result['success']:
            return result

        full_text = result['full_text']

        # Common section headers in research papers
        section_patterns = [
            (r'(?i)^\s*abstract\s*$', 'abstract'),
            (r'(?i)^\s*introduction\s*$', 'introduction'),
            (r'(?i)^\s*related\s+work\s*$', 'related_work'),
            (r'(?i)^\s*methodology\s*$', 'methodology'),
            (r'(?i)^\s*methods?\s*$', 'methods'),
            (r'(?i)^\s*experiments?\s*$', 'experiments'),
            (r'(?i)^\s*results?\s*$', 'results'),
            (r'(?i)^\s*discussion\s*$', 'discussion'),
            (r'(?i)^\s*conclusion\s*$', 'conclusion'),
            (r'(?i)^\s*references?\s*$', 'references'),
        ]

        sections = {}

        # Try to identify sections (basic implementation)
        lines = full_text.split('\n')
        current_section = 'header'
        current_text = []

        for line in lines:
            matched = False
            for pattern, section_name in section_patterns:
                if re.match(pattern, line):
                    # Save previous section
                    if current_text:
                        sections[current_section] = '\n'.join(current_text)
                    # Start new section
                    current_section = section_name
                    current_text = []
                    matched = True
                    break

            if not matched:
                current_text.append(line)

        # Save last section
        if current_text:
            sections[current_section] = '\n'.join(current_text)

        result['sections'] = sections
        return result

    def get_page_text(self, pdf_path: str, page_number: int) -> Optional[str]:
        """
        Get text from a specific page

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            Text from the page or None if error
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)

            if page_number < 1 or page_number > len(doc):
                return None

            page = doc[page_number - 1]  # Convert to 0-indexed
            text = page.get_text()

            return self._clean_text(text)

        except Exception as e:
            print(f"Error getting page {page_number}: {e}")
            return None
        finally:
            # Always close document to prevent resource leak
            if doc is not None:
                try:
                    doc.close()
                except Exception as e:
                    print(f"Warning: Error closing PDF in get_page_text: {e}")

    def get_page_count(self, pdf_path: str) -> int:
        """
        Get total number of pages in PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages or 0 if error
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            return count
        except Exception as e:
            print(f"Error getting page count: {e}")
            return 0
        finally:
            # Always close document to prevent resource leak
            if doc is not None:
                try:
                    doc.close()
                except Exception as e:
                    print(f"Warning: Error closing PDF in get_page_count: {e}")

    def extract_images_info(self, pdf_path: str) -> List[Dict]:
        """
        Extract information about images in the PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of dictionaries with image info
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            images_info = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    images_info.append({
                        'page': page_num + 1,
                        'index': img_index,
                        'xref': img[0],
                        'width': img[2],
                        'height': img[3]
                    })

            return images_info

        except Exception as e:
            print(f"Error extracting image info: {e}")
            return []
        finally:
            # Always close document to prevent resource leak
            if doc is not None:
                try:
                    doc.close()
                except Exception as e:
                    print(f"Warning: Error closing PDF in extract_images_info: {e}")


if __name__ == "__main__":
    # Test the processor
    processor = PDFProcessor()

    # Test with a PDF (you need to have a PDF file to test)
    test_pdf = "documents/test.pdf"

    if Path(test_pdf).exists():
        result = processor.extract_text_from_pdf(test_pdf)
        print(f"\nExtraction result: {result['success']}")
        print(f"Total pages: {result['total_pages']}")
        print(f"Total words: {result['stats']['total_words']}")
        print(f"\nFirst 500 chars:\n{result['full_text'][:500]}")
    else:
        print(f"Test PDF not found at {test_pdf}")
        print("Download a sample PDF first using pdf_downloader.py")
