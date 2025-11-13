"""
PDF Downloader Module
=====================

Downloads research paper PDFs from URLs and stores them locally.
Handles duplicate prevention using DOI hashing.
"""

import os
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict
import time


class PDFDownloader:
    """Downloads and manages PDF files for research papers"""

    def __init__(self, download_dir: str = "documents"):
        """
        Initialize PDF downloader

        Args:
            download_dir: Directory to store downloaded PDFs
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)

    def _get_filename_from_doi(self, doi: str) -> str:
        """
        Generate filename from DOI using hash

        Args:
            doi: Paper's DOI

        Returns:
            Filename based on DOI hash
        """
        if not doi:
            # If no DOI, use timestamp
            return f"paper_{int(time.time())}.pdf"

        # Create hash of DOI for filename
        doi_hash = hashlib.md5(doi.encode()).hexdigest()
        return f"{doi_hash}.pdf"

    def download_pdf(
        self,
        pdf_url: str,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, any]:
        """
        Download PDF from URL and save to local storage

        Args:
            pdf_url: URL of the PDF to download
            doi: Paper's DOI (used for filename)
            title: Paper title (for logging)
            timeout: Download timeout in seconds

        Returns:
            Dictionary with download status:
            {
                'success': bool,
                'pdf_path': str or None,
                'message': str,
                'file_size': int (bytes)
            }
        """
        try:
            # Generate filename
            filename = self._get_filename_from_doi(doi)
            pdf_path = self.download_dir / filename

            # Check if PDF already exists
            if pdf_path.exists():
                file_size = pdf_path.stat().st_size
                return {
                    'success': True,
                    'pdf_path': str(pdf_path),
                    'message': 'PDF already exists (cached)',
                    'file_size': file_size,
                    'cached': True
                }

            # Download PDF
            print(f"Downloading PDF from {pdf_url[:50]}...")

            headers = {
                'User-Agent': 'ResearchPaperDiscovery/1.0 (Educational Purpose)'
            }

            response = requests.get(
                pdf_url,
                headers=headers,
                timeout=timeout,
                stream=True
            )

            # Check if response is actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'application/pdf' not in content_type and 'octet-stream' not in content_type:
                return {
                    'success': False,
                    'pdf_path': None,
                    'message': f'URL does not point to a PDF (Content-Type: {content_type})',
                    'file_size': 0,
                    'cached': False
                }

            response.raise_for_status()

            # Write PDF to file
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = pdf_path.stat().st_size

            # Verify file size
            if file_size < 1024:  # Less than 1KB is suspicious
                pdf_path.unlink()  # Delete the file
                return {
                    'success': False,
                    'pdf_path': None,
                    'message': 'Downloaded file is too small (likely not a valid PDF)',
                    'file_size': file_size,
                    'cached': False
                }

            print(f"✓ PDF downloaded successfully ({file_size / 1024:.1f} KB)")

            return {
                'success': True,
                'pdf_path': str(pdf_path),
                'message': 'PDF downloaded successfully',
                'file_size': file_size,
                'cached': False
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'pdf_path': None,
                'message': f'Download timeout after {timeout} seconds',
                'file_size': 0,
                'cached': False
            }

        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'pdf_path': None,
                'message': f'HTTP error: {e.response.status_code}',
                'file_size': 0,
                'cached': False
            }

        except Exception as e:
            return {
                'success': False,
                'pdf_path': None,
                'message': f'Error downloading PDF: {str(e)}',
                'file_size': 0,
                'cached': False
            }

    def get_pdf_path(self, doi: str) -> Optional[str]:
        """
        Get path to PDF if it exists locally

        Args:
            doi: Paper's DOI

        Returns:
            Path to PDF file or None if not found
        """
        filename = self._get_filename_from_doi(doi)
        pdf_path = self.download_dir / filename

        if pdf_path.exists():
            return str(pdf_path)
        return None

    def delete_pdf(self, doi: str) -> bool:
        """
        Delete PDF file from local storage

        Args:
            doi: Paper's DOI

        Returns:
            True if deleted, False if not found
        """
        filename = self._get_filename_from_doi(doi)
        pdf_path = self.download_dir / filename

        if pdf_path.exists():
            pdf_path.unlink()
            return True
        return False

    def list_downloaded_pdfs(self) -> list:
        """
        List all downloaded PDFs

        Returns:
            List of PDF file paths
        """
        return [str(p) for p in self.download_dir.glob("*.pdf")]

    def get_storage_stats(self) -> Dict[str, any]:
        """
        Get statistics about PDF storage

        Returns:
            Dictionary with storage stats
        """
        pdf_files = list(self.download_dir.glob("*.pdf"))
        total_size = sum(p.stat().st_size for p in pdf_files)

        return {
            'total_pdfs': len(pdf_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'download_dir': str(self.download_dir)
        }


if __name__ == "__main__":
    # Test the downloader
    downloader = PDFDownloader()

    # Test with a sample arXiv paper (open access)
    test_url = "https://arxiv.org/pdf/2103.14030.pdf"
    test_doi = "10.48550/arXiv.2103.14030"

    result = downloader.download_pdf(test_url, test_doi, "Test Paper")
    print(f"\nDownload result: {result}")

    # Check storage stats
    stats = downloader.get_storage_stats()
    print(f"\nStorage stats: {stats}")
