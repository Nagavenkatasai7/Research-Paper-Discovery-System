"""
RAG Engine
==========
Core RAG functionality for document processing and retrieval.
Integrates PDF processing, text chunking, embeddings, and FAISS search.
"""

import time
import numpy as np
from typing import Dict, List, Optional
from pathlib import Path
import faiss

from rag_system.database import RAGDatabase
from rag_system.pdf_processor import PDFProcessor
from rag_system.text_chunker import TextChunker
from rag_system.embeddings import EmbeddingsManager


class RAGEngine:
    """
    RAG (Retrieval-Augmented Generation) Engine

    Handles:
    1. Document processing (PDF → chunks → embeddings)
    2. Vector storage in FAISS
    3. Similarity search for retrieval
    """

    def __init__(self, db: Optional[RAGDatabase] = None):
        """
        Initialize RAG engine

        Args:
            db: Optional database instance
        """
        self.db = db or RAGDatabase()
        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker()
        self.embedding_model = EmbeddingsManager()

        # FAISS indexes (document_id -> index)
        self.indexes = {}

    def process_document(
        self,
        pdf_path: str,
        document_id: int,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> Dict:
        """
        Process a document: extract text → chunk → embed → store

        Args:
            pdf_path: Path to PDF file
            document_id: Document ID in database
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()

        try:
            # Step 1: Extract text from PDF
            print(f"Extracting text from PDF...")
            pdf_result = self.pdf_processor.extract_text_with_metadata(pdf_path)

            if not pdf_result['success']:
                return {
                    'success': False,
                    'error': f"PDF extraction failed: {pdf_result.get('error')}",
                    'elapsed_time': time.time() - start_time
                }

            full_text = pdf_result['full_text']
            pages = pdf_result.get('pages', [])

            print(f"✓ Extracted {len(full_text)} characters from {len(pages)} pages")

            # Step 2: Chunk text
            print(f"Chunking text (size={chunk_size}, overlap={chunk_overlap})...")
            chunks = self.chunker.chunk_text(
                text=full_text,
                chunk_size=chunk_size,
                overlap=chunk_overlap
            )

            if not chunks:
                return {
                    'success': False,
                    'error': 'No chunks created',
                    'elapsed_time': time.time() - start_time
                }

            print(f"✓ Created {len(chunks)} chunks")

            # Step 3: Generate embeddings
            print(f"Generating embeddings...")
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_model.generate_embeddings(texts, show_progress=False)

            print(f"✓ Generated {len(embeddings)} embeddings (dim={embeddings.shape[1]})")

            # Step 4: Create FAISS index
            print(f"Creating FAISS index...")
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype('float32'))

            print(f"✓ FAISS index created with {index.ntotal} vectors")

            # Step 5: Store chunks in database
            print(f"Storing chunks in database...")
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = self.db.add_chunk(
                    document_id=document_id,
                    text=chunk['text'],
                    start_idx=chunk.get('start_idx', 0),
                    end_idx=chunk.get('end_idx', 0),
                    page_num=self._get_page_for_chunk(chunk, pages)
                )
                chunk_ids.append(chunk_id)

            print(f"✓ Stored {len(chunk_ids)} chunks")

            # Step 6: Save FAISS index
            index_path = f"faiss_indexes/doc_{document_id}.index"
            Path("faiss_indexes").mkdir(exist_ok=True)
            faiss.write_index(index, index_path)

            print(f"✓ FAISS index saved to {index_path}")

            # Cache index in memory
            self.indexes[document_id] = {
                'index': index,
                'chunk_ids': chunk_ids,
                'dimension': dimension
            }

            elapsed_time = time.time() - start_time

            return {
                'success': True,
                'num_chunks': len(chunks),
                'num_pages': len(pages),
                'index_path': index_path,
                'dimension': dimension,
                'elapsed_time': elapsed_time
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'elapsed_time': time.time() - start_time
            }

    def _get_page_for_chunk(self, chunk: Dict, pages: List[Dict]) -> int:
        """Estimate page number for a chunk based on character position"""
        start_idx = chunk.get('start_idx', 0)

        # Calculate cumulative character positions for each page
        cumulative_chars = 0
        for page in pages:
            page_text = page.get('text', '')
            cumulative_chars += len(page_text)

            if start_idx < cumulative_chars:
                return page.get('page_num', 1)

        # If not found, return last page
        return pages[-1].get('page_num', 1) if pages else 1

    def load_index(self, document_id: int) -> bool:
        """
        Load FAISS index from disk into memory

        Args:
            document_id: Document ID

        Returns:
            True if successful
        """
        try:
            # Check if already loaded
            if document_id in self.indexes:
                return True

            # Load from disk
            index_path = f"faiss_indexes/doc_{document_id}.index"
            if not Path(index_path).exists():
                print(f"Index not found: {index_path}")
                return False

            index = faiss.read_index(index_path)

            # Get chunk IDs from database
            chunks = self.db.get_chunks_by_document(document_id)
            chunk_ids = [chunk['id'] for chunk in chunks]

            # Cache in memory
            self.indexes[document_id] = {
                'index': index,
                'chunk_ids': chunk_ids,
                'dimension': index.d
            }

            print(f"✓ Loaded FAISS index for document {document_id} ({index.ntotal} vectors)")
            return True

        except Exception as e:
            print(f"Error loading index: {e}")
            return False

    def query(
        self,
        query_text: str,
        document_id: Optional[int] = None,
        top_k: int = 5
    ) -> Dict:
        """
        Query for relevant chunks using semantic search

        Args:
            query_text: Search query
            document_id: Optional document ID to search within
            top_k: Number of results to return

        Returns:
            Dictionary with search results
        """
        start_time = time.time()

        try:
            if document_id:
                # Search within specific document
                if not self.load_index(document_id):
                    return {
                        'success': False,
                        'error': f'Index not found for document {document_id}',
                        'elapsed_time': time.time() - start_time
                    }

                index_data = self.indexes[document_id]
                index = index_data['index']
                chunk_ids = index_data['chunk_ids']

                # Generate query embedding
                query_embedding = self.embedding_model.generate_embeddings([query_text], show_progress=False)

                # Search FAISS index
                distances, indices = index.search(query_embedding.astype('float32'), top_k)

                # Retrieve chunks from database
                chunks = []
                for i, idx in enumerate(indices[0]):
                    if idx >= 0 and idx < len(chunk_ids):
                        chunk_id = chunk_ids[idx]
                        chunk = self.db.get_chunk_by_id(chunk_id)

                        if chunk:
                            chunk['score'] = float(1 / (1 + distances[0][i]))  # Convert distance to score
                            chunks.append(chunk)

                elapsed_time = time.time() - start_time

                return {
                    'success': True,
                    'query': query_text,
                    'document_id': document_id,
                    'chunks': chunks,
                    'num_results': len(chunks),
                    'elapsed_time': elapsed_time
                }

            else:
                # Search across all documents (not implemented yet)
                return {
                    'success': False,
                    'error': 'Cross-document search not yet implemented',
                    'elapsed_time': time.time() - start_time
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'elapsed_time': time.time() - start_time
            }

    def get_document_stats(self, document_id: int) -> Dict:
        """
        Get statistics about a processed document

        Args:
            document_id: Document ID

        Returns:
            Dictionary with statistics
        """
        chunks = self.db.get_chunks_by_document(document_id)

        if not chunks:
            return {
                'success': False,
                'error': 'No chunks found for document'
            }

        total_chars = sum(len(chunk['text']) for chunk in chunks)
        avg_chunk_size = total_chars / len(chunks) if chunks else 0

        return {
            'success': True,
            'num_chunks': len(chunks),
            'total_characters': total_chars,
            'avg_chunk_size': avg_chunk_size,
            'pages': set(chunk.get('page_num', 1) for chunk in chunks)
        }


if __name__ == "__main__":
    # Test RAG engine
    print("Testing RAGEngine...")

    engine = RAGEngine()

    print("\n✓ RAGEngine initialized")
    print("\nAvailable methods:")
    print("  - process_document(pdf_path, document_id, ...) - Process PDF and create index")
    print("  - query(query_text, document_id, top_k) - Search for relevant chunks")
    print("  - load_index(document_id) - Load FAISS index from disk")
    print("  - get_document_stats(document_id) - Get document statistics")
