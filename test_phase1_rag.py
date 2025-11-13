"""
Phase 1 RAG System End-to-End Test
====================================

Tests the complete RAG pipeline:
1. Download PDF
2. Extract text
3. Chunk text
4. Generate embeddings
5. Create FAISS index
6. Test search
7. Save to database
"""

import sys
from rag_system.pdf_downloader import PDFDownloader
from rag_system.pdf_processor import PDFProcessor
from rag_system.text_chunker import TextChunker
from rag_system.embeddings import EmbeddingsManager
from rag_system.database import RAGDatabase
import time


def test_phase1_complete():
    """Test complete Phase 1 RAG pipeline"""

    print("=" * 80)
    print("PHASE 1 RAG SYSTEM - END-TO-END TEST")
    print("=" * 80)

    # Test paper: "Attention Is All You Need" (Transformer paper) - Open Access on arXiv
    test_paper = {
        'doi': '10.48550/arXiv.1706.03762',
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017,
        'pdf_url': 'https://arxiv.org/pdf/1706.03762.pdf',
        'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...'
    }

    start_time = time.time()

    try:
        # Step 1: Download PDF
        print("\n" + "=" * 80)
        print("STEP 1: DOWNLOADING PDF")
        print("=" * 80)

        downloader = PDFDownloader()
        download_result = downloader.download_pdf(
            pdf_url=test_paper['pdf_url'],
            doi=test_paper['doi'],
            title=test_paper['title']
        )

        if not download_result['success']:
            print(f"❌ Download failed: {download_result['message']}")
            return False

        pdf_path = download_result['pdf_path']
        print(f"✓ PDF downloaded: {pdf_path}")
        print(f"  Size: {download_result['file_size'] / 1024:.1f} KB")
        print(f"  Cached: {download_result.get('cached', False)}")

        # Step 2: Extract text from PDF
        print("\n" + "=" * 80)
        print("STEP 2: EXTRACTING TEXT FROM PDF")
        print("=" * 80)

        processor = PDFProcessor()
        extraction_result = processor.extract_text_from_pdf(pdf_path)

        if not extraction_result['success']:
            print(f"❌ Text extraction failed: {extraction_result['message']}")
            return False

        pages = extraction_result['pages']
        full_text = extraction_result['full_text']
        stats = extraction_result['stats']

        print(f"✓ Text extracted successfully")
        print(f"  Total pages: {extraction_result['total_pages']}")
        print(f"  Total words: {stats['total_words']:,}")
        print(f"  Total characters: {stats['total_characters']:,}")
        print(f"  Avg words per page: {stats['avg_words_per_page']:.1f}")

        # Step 3: Chunk text
        print("\n" + "=" * 80)
        print("STEP 3: CHUNKING TEXT")
        print("=" * 80)

        chunker = TextChunker(chunk_size=512, chunk_overlap=50)
        chunks = chunker.chunk_by_pages(pages, metadata=test_paper)

        chunk_stats = chunker.get_chunk_stats(chunks)

        print(f"✓ Text chunked successfully")
        print(f"  Total chunks: {chunk_stats['total_chunks']}")
        print(f"  Avg tokens per chunk: {chunk_stats['avg_tokens_per_chunk']:.1f}")
        print(f"  Min tokens: {chunk_stats['min_tokens']}")
        print(f"  Max tokens: {chunk_stats['max_tokens']}")
        print(f"  Total tokens: {chunk_stats['total_tokens']:,}")

        # Step 4 & 5: Generate embeddings and create FAISS index
        print("\n" + "=" * 80)
        print("STEP 4 & 5: GENERATING EMBEDDINGS AND CREATING FAISS INDEX")
        print("=" * 80)

        embeddings_manager = EmbeddingsManager()
        index_result = embeddings_manager.create_faiss_index(
            chunks=chunks,
            doi=test_paper['doi'],
            force_rebuild=False
        )

        if not index_result['success']:
            print(f"❌ Index creation failed: {index_result['message']}")
            return False

        print(f"✓ FAISS index created successfully")
        print(f"  Index path: {index_result['index_path']}")
        print(f"  Num chunks indexed: {index_result['num_chunks']}")
        print(f"  Embedding dimension: {index_result['embedding_dim']}")
        print(f"  Time taken: {index_result.get('elapsed_time', 0):.2f}s")
        print(f"  Cached: {index_result.get('cached', False)}")

        # Step 6: Test search
        print("\n" + "=" * 80)
        print("STEP 6: TESTING VECTOR SEARCH")
        print("=" * 80)

        test_queries = [
            "What is the transformer architecture?",
            "How does attention mechanism work?",
            "What are the main contributions of this paper?"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: \"{query}\"")

            results = embeddings_manager.search_similar_chunks(
                query=query,
                doi=test_paper['doi'],
                top_k=3
            )

            print(f"  Found {len(results)} results:")

            for j, result in enumerate(results, 1):
                chunk = result['chunk']
                score = result['score']
                pages = chunk.get('page_numbers', [])

                print(f"\n  Result {j} (Score: {score:.3f}, Pages: {pages}):")
                print(f"    {chunk['text'][:150]}...")

        # Step 7: Save to database
        print("\n" + "=" * 80)
        print("STEP 7: SAVING TO DATABASE")
        print("=" * 80)

        db = RAGDatabase()

        # Check if document already exists
        existing_doc = db.get_document_by_doi(test_paper['doi'])

        if existing_doc:
            doc_id = existing_doc['id']
            print(f"✓ Document already exists in database (ID: {doc_id})")
            # Update with PDF path
            db.update_document(
                doc_id,
                pdf_path=pdf_path,
                page_count=extraction_result['total_pages'],
                processing_status='completed'
            )
        else:
            # Add new document
            doc_id = db.add_document(
                doi=test_paper['doi'],
                title=test_paper['title'],
                authors=test_paper['authors'],
                year=test_paper['year'],
                abstract=test_paper['abstract'],
                pdf_path=pdf_path,
                pdf_url=test_paper['pdf_url']
            )
            print(f"✓ Document added to database (ID: {doc_id})")

            # Update page count and status
            db.update_document(
                doc_id,
                page_count=extraction_result['total_pages'],
                processing_status='completed'
            )

        # Add embedding info
        existing_embedding = db.get_embedding_info(doc_id)

        if not existing_embedding:
            db.add_embedding_info(
                document_id=doc_id,
                faiss_index_path=index_result['index_path'],
                chunk_count=len(chunks),
                embedding_model='all-MiniLM-L6-v2',
                embedding_dim=index_result['embedding_dim']
            )
            print(f"✓ Embedding info added to database")
        else:
            print(f"✓ Embedding info already exists in database")

        # Get database statistics
        print("\n" + "=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)

        stats = db.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        db.close()

        # Final summary
        elapsed_time = time.time() - start_time

        print("\n" + "=" * 80)
        print("✅ PHASE 1 TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Total time: {elapsed_time:.2f}s")
        print(f"\nAll systems operational:")
        print(f"  ✓ PDF Download")
        print(f"  ✓ Text Extraction")
        print(f"  ✓ Text Chunking")
        print(f"  ✓ Embeddings Generation")
        print(f"  ✓ FAISS Vector Index")
        print(f"  ✓ Semantic Search")
        print(f"  ✓ Database Storage")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_phase1_complete()
    sys.exit(0 if success else 1)
