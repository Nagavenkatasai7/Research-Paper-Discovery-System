"""
Text Chunking Module
====================

Splits document text into chunks for embedding and retrieval.
Uses semantic chunking with overlap for better context preservation.
"""

from typing import List, Dict
import tiktoken
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter


class TextChunker:
    """Chunks text for embedding and retrieval"""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separator: str = " "
    ):
        """
        Initialize text chunker

        Args:
            chunk_size: Target size for each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
            separator: Text separator (default: space)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

        # Initialize tokenizer for accurate token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Initialize LlamaIndex sentence splitter
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separator=separator
        )

    def chunk_document(
        self,
        text: str,
        pages: List[Dict] = None,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Chunk document text into semantic chunks with page tracking

        Args:
            text: Full document text
            pages: Optional list of page dicts with page_number and text
            metadata: Optional document metadata

        Returns:
            List of chunk dictionaries with:
            {
                'chunk_id': int,
                'text': str,
                'token_count': int,
                'page_numbers': List[int],
                'start_char': int,
                'end_char': int,
                'metadata': Dict
            }
        """
        if not text or not text.strip():
            return []

        # Create LlamaIndex document
        doc = Document(text=text, metadata=metadata or {})

        # Split into nodes (chunks)
        nodes = self.splitter.get_nodes_from_documents([doc])

        # Convert nodes to our chunk format
        chunks = []
        for i, node in enumerate(nodes):
            chunk_text = node.get_content()

            # Count tokens
            token_count = len(self.tokenizer.encode(chunk_text))

            # Find which pages this chunk appears on
            page_numbers = self._find_page_numbers(chunk_text, pages) if pages else []

            chunk_dict = {
                'chunk_id': i,
                'text': chunk_text,
                'token_count': token_count,
                'page_numbers': page_numbers,
                'start_char': node.start_char_idx,
                'end_char': node.end_char_idx,
                'metadata': metadata or {}
            }

            chunks.append(chunk_dict)

        return chunks

    def _find_page_numbers(self, chunk_text: str, pages: List[Dict]) -> List[int]:
        """
        Find which pages a chunk appears on

        Args:
            chunk_text: Text of the chunk
            pages: List of page dictionaries

        Returns:
            List of page numbers (1-indexed)
        """
        if not pages:
            return []

        page_numbers = []

        # Take first ~100 chars of chunk as signature
        signature = chunk_text[:100].strip()

        for page in pages:
            if signature in page['text']:
                page_numbers.append(page['page_number'])

        return page_numbers if page_numbers else [1]  # Default to page 1 if not found

    def chunk_by_pages(
        self,
        pages: List[Dict],
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Chunk document with explicit page boundaries

        Args:
            pages: List of page dicts from PDFProcessor
            metadata: Optional document metadata

        Returns:
            List of chunk dictionaries
        """
        all_chunks = []
        chunk_id = 0

        for page in pages:
            page_text = page['text']

            if not page_text.strip():
                continue

            # Chunk each page separately
            doc = Document(text=page_text, metadata=metadata or {})
            nodes = self.splitter.get_nodes_from_documents([doc])

            for node in nodes:
                chunk_text = node.get_content()
                token_count = len(self.tokenizer.encode(chunk_text))

                chunk_dict = {
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'token_count': token_count,
                    'page_numbers': [page['page_number']],
                    'start_char': node.start_char_idx,
                    'end_char': node.end_char_idx,
                    'metadata': metadata or {}
                }

                all_chunks.append(chunk_dict)
                chunk_id += 1

        return all_chunks

    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunks

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_tokens_per_chunk': 0,
                'min_tokens': 0,
                'max_tokens': 0,
                'total_tokens': 0
            }

        token_counts = [c['token_count'] for c in chunks]

        return {
            'total_chunks': len(chunks),
            'avg_tokens_per_chunk': sum(token_counts) / len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'total_tokens': sum(token_counts),
            'pages_covered': len(set(
                page_num
                for chunk in chunks
                for page_num in chunk.get('page_numbers', [])
            ))
        }

    def merge_small_chunks(
        self,
        chunks: List[Dict],
        min_tokens: int = 100
    ) -> List[Dict]:
        """
        Merge chunks that are too small

        Args:
            chunks: List of chunk dictionaries
            min_tokens: Minimum tokens per chunk

        Returns:
            List of merged chunks
        """
        if not chunks:
            return []

        merged_chunks = []
        current_chunk = None

        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk.copy()
                continue

            # If current chunk is too small, merge with next
            if current_chunk['token_count'] < min_tokens:
                # Merge texts
                current_chunk['text'] += ' ' + chunk['text']

                # Recalculate token count
                current_chunk['token_count'] = len(
                    self.tokenizer.encode(current_chunk['text'])
                )

                # Merge page numbers
                current_chunk['page_numbers'] = list(set(
                    current_chunk['page_numbers'] + chunk['page_numbers']
                ))

                # Update end character
                current_chunk['end_char'] = chunk['end_char']

            else:
                # Current chunk is big enough, save it
                merged_chunks.append(current_chunk)
                current_chunk = chunk.copy()

        # Add last chunk
        if current_chunk:
            merged_chunks.append(current_chunk)

        # Re-index chunks
        for i, chunk in enumerate(merged_chunks):
            chunk['chunk_id'] = i

        return merged_chunks


if __name__ == "__main__":
    # Test the chunker
    chunker = TextChunker(chunk_size=512, chunk_overlap=50)

    # Sample text
    sample_text = """
    This is a sample research paper abstract. It discusses important findings in machine learning.
    The paper presents a novel approach to neural network optimization.
    """ * 50  # Repeat to create longer text

    # Test basic chunking
    chunks = chunker.chunk_document(sample_text)

    print(f"Created {len(chunks)} chunks")
    print(f"\nChunk stats:")
    stats = chunker.get_chunk_stats(chunks)
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print(f"\nFirst chunk preview:")
    print(f"  Text: {chunks[0]['text'][:100]}...")
    print(f"  Tokens: {chunks[0]['token_count']}")
