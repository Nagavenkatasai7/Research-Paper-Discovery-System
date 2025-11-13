"""
Embeddings and Vector Search Module
====================================

Generates embeddings using sentence-transformers and manages FAISS vector index.
Free, local, no API costs.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import pickle
import time


class EmbeddingsManager:
    """Manages embeddings generation and FAISS vector search"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        embeddings_dir: str = "embeddings"
    ):
        """
        Initialize embeddings manager

        Args:
            model_name: Sentence-transformers model name
                       'all-MiniLM-L6-v2' is fast and lightweight (384 dimensions)
            embeddings_dir: Directory to store FAISS indexes
        """
        self.model_name = model_name
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(exist_ok=True)

        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✓ Model loaded (dimension: {self.embedding_dim})")

    def generate_embeddings(
        self,
        texts: List[str],
        show_progress: bool = True
    ) -> np.ndarray:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of text strings to embed
            show_progress: Show progress bar

        Returns:
            numpy array of embeddings (shape: [n_texts, embedding_dim])
        """
        if not texts:
            return np.array([])

        # Generate embeddings
        embeddings = self.model.encode(
            texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )

        return embeddings

    def create_faiss_index(
        self,
        chunks: List[Dict],
        doi: str,
        force_rebuild: bool = False
    ) -> Dict:
        """
        Create FAISS index from document chunks

        Args:
            chunks: List of chunk dictionaries from TextChunker
            doi: Document DOI (used for filename)
            force_rebuild: Rebuild even if index exists

        Returns:
            Dictionary with index creation results
        """
        if not chunks:
            return {
                'success': False,
                'message': 'No chunks to index',
                'index_path': None
            }

        # Generate index filename from DOI
        index_filename = self._get_index_filename(doi)
        index_path = self.embeddings_dir / f"{index_filename}.index"
        metadata_path = self.embeddings_dir / f"{index_filename}.pkl"

        # Check if index already exists
        if index_path.exists() and not force_rebuild:
            return {
                'success': True,
                'message': 'Index already exists (cached)',
                'index_path': str(index_path),
                'metadata_path': str(metadata_path),
                'cached': True
            }

        start_time = time.time()

        # Extract texts from chunks
        texts = [chunk['text'] for chunk in chunks]

        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.generate_embeddings(texts, show_progress=True)

        # Create FAISS index (using L2 distance for normalized vectors = cosine similarity)
        print("Creating FAISS index...")
        index = faiss.IndexFlatL2(self.embedding_dim)
        index.add(embeddings)

        # Save index
        faiss.write_index(index, str(index_path))

        # Save metadata (chunks info)
        with open(metadata_path, 'wb') as f:
            pickle.dump(chunks, f)

        elapsed_time = time.time() - start_time

        print(f"✓ Index created: {len(chunks)} chunks in {elapsed_time:.2f}s")

        return {
            'success': True,
            'message': 'Index created successfully',
            'index_path': str(index_path),
            'metadata_path': str(metadata_path),
            'num_chunks': len(chunks),
            'embedding_dim': self.embedding_dim,
            'elapsed_time': elapsed_time,
            'cached': False
        }

    def search_similar_chunks(
        self,
        query: str,
        doi: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar chunks using FAISS

        Args:
            query: Query text
            doi: Document DOI
            top_k: Number of top results to return

        Returns:
            List of dictionaries with:
            {
                'chunk': Dict (original chunk),
                'score': float (similarity score),
                'rank': int
            }
        """
        # Load index
        index_filename = self._get_index_filename(doi)
        index_path = self.embeddings_dir / f"{index_filename}.index"
        metadata_path = self.embeddings_dir / f"{index_filename}.pkl"

        if not index_path.exists():
            return []

        # Load FAISS index
        index = faiss.read_index(str(index_path))

        # Load chunks metadata
        with open(metadata_path, 'rb') as f:
            chunks = pickle.load(f)

        # Generate query embedding
        query_embedding = self.generate_embeddings([query], show_progress=False)

        # Search
        distances, indices = index.search(query_embedding, min(top_k, len(chunks)))

        # Convert to results
        results = []
        for rank, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            # Convert L2 distance to similarity score (0-1, higher is better)
            # For normalized vectors: similarity = 1 - (distance^2 / 2)
            similarity = 1 - (distance ** 2 / 2)

            results.append({
                'chunk': chunks[idx],
                'score': float(similarity),
                'distance': float(distance),
                'rank': rank + 1
            })

        return results

    def _get_index_filename(self, doi: str) -> str:
        """Generate filename from DOI"""
        import hashlib
        if not doi:
            return f"index_{int(time.time())}"
        doi_hash = hashlib.md5(doi.encode()).hexdigest()
        return f"index_{doi_hash}"

    def index_exists(self, doi: str) -> bool:
        """Check if FAISS index exists for a document"""
        index_filename = self._get_index_filename(doi)
        index_path = self.embeddings_dir / f"{index_filename}.index"
        return index_path.exists()

    def delete_index(self, doi: str) -> bool:
        """Delete FAISS index and metadata for a document"""
        index_filename = self._get_index_filename(doi)
        index_path = self.embeddings_dir / f"{index_filename}.index"
        metadata_path = self.embeddings_dir / f"{index_filename}.pkl"

        deleted = False

        if index_path.exists():
            index_path.unlink()
            deleted = True

        if metadata_path.exists():
            metadata_path.unlink()
            deleted = True

        return deleted

    def get_storage_stats(self) -> Dict:
        """Get statistics about embedding storage"""
        index_files = list(self.embeddings_dir.glob("*.index"))
        metadata_files = list(self.embeddings_dir.glob("*.pkl"))

        total_size = sum(f.stat().st_size for f in index_files + metadata_files)

        return {
            'total_indexes': len(index_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'embeddings_dir': str(self.embeddings_dir),
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim
        }


class HybridRetriever:
    """Combines semantic search with keyword matching for better results"""

    def __init__(self, embeddings_manager: EmbeddingsManager):
        """
        Initialize hybrid retriever

        Args:
            embeddings_manager: EmbeddingsManager instance
        """
        self.embeddings_manager = embeddings_manager

    def hybrid_search(
        self,
        query: str,
        doi: str,
        top_k: int = 5,
        semantic_weight: float = 0.7
    ) -> List[Dict]:
        """
        Hybrid search combining semantic and keyword matching

        Args:
            query: Query text
            doi: Document DOI
            top_k: Number of results
            semantic_weight: Weight for semantic score (0-1)

        Returns:
            List of ranked results
        """
        # Get semantic search results
        semantic_results = self.embeddings_manager.search_similar_chunks(
            query, doi, top_k=top_k * 2  # Get more for reranking
        )

        if not semantic_results:
            return []

        # Calculate keyword scores
        query_terms = set(query.lower().split())

        for result in semantic_results:
            chunk_text = result['chunk']['text'].lower()
            chunk_terms = set(chunk_text.split())

            # Keyword overlap score
            overlap = len(query_terms & chunk_terms)
            keyword_score = min(overlap / len(query_terms), 1.0) if query_terms else 0

            # Combine scores
            semantic_score = result['score']
            hybrid_score = (semantic_weight * semantic_score +
                          (1 - semantic_weight) * keyword_score)

            result['keyword_score'] = keyword_score
            result['hybrid_score'] = hybrid_score

        # Re-rank by hybrid score
        semantic_results.sort(key=lambda x: x['hybrid_score'], reverse=True)

        # Return top k
        return semantic_results[:top_k]


if __name__ == "__main__":
    # Test embeddings manager
    print("Testing EmbeddingsManager...")

    manager = EmbeddingsManager()

    # Test embedding generation
    sample_texts = [
        "Machine learning is a subset of artificial intelligence.",
        "Neural networks are inspired by biological neurons.",
        "Deep learning uses multiple layers of neural networks."
    ]

    embeddings = manager.generate_embeddings(sample_texts, show_progress=False)
    print(f"\nGenerated embeddings shape: {embeddings.shape}")
    print(f"Embedding dimension: {manager.embedding_dim}")

    # Test storage stats
    stats = manager.get_storage_stats()
    print(f"\nStorage stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
