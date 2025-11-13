"""
Paper Analysis Workflow Manager
================================
Complete workflow integration for Phase 4:
1. Download PDF → Process → Analyze → Store → Enable Chat
2. Unified API for all backend operations
3. Error handling and recovery
"""

import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from rag_system.database import RAGDatabase
from rag_system.pdf_downloader import PDFDownloader
from rag_system.pdf_processor import PDFProcessor
from rag_system.rag_engine import RAGEngine
from rag_system.analysis_agents import DocumentAnalysisOrchestrator, SynthesisAgent
from rag_system.document_chat import DocumentChatSystem


class PaperAnalysisWorkflow:
    """
    Complete workflow manager integrating all Phase 4 components.

    Provides unified API for:
    - Complete paper processing and analysis
    - Storing and retrieving comprehensive analyses
    - Intelligent document chat with hybrid context
    """

    def __init__(self, db: Optional[RAGDatabase] = None):
        """
        Initialize workflow manager

        Args:
            db: Optional database instance (will create new if not provided)
        """
        self.db = db or RAGDatabase()

        # Initialize all components
        self.downloader = PDFDownloader()
        self.pdf_processor = PDFProcessor()
        self.rag_engine = RAGEngine(db=self.db)
        self.orchestrator = DocumentAnalysisOrchestrator()
        self.synthesizer = SynthesisAgent()
        self.chat_system = DocumentChatSystem(db=self.db)

    def process_and_analyze_paper(
        self,
        arxiv_id: str,
        paper_metadata: Optional[Dict] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        parallel_agents: bool = True,
        store_analysis: bool = True
    ) -> Dict:
        """
        Complete workflow: Download → Process → RAG → Analyze → Store

        Args:
            arxiv_id: ArXiv paper ID
            paper_metadata: Optional metadata (title, authors, year, etc.)
            chunk_size: Size of text chunks for RAG
            chunk_overlap: Overlap between chunks
            parallel_agents: Use parallel agent execution
            store_analysis: Store analysis results in database

        Returns:
            Dictionary with complete results and metadata
        """
        start_time = time.time()
        workflow_result = {
            'success': False,
            'arxiv_id': arxiv_id,
            'steps_completed': [],
            'errors': []
        }

        try:
            # Step 1: Download PDF
            print(f"\n{'='*80}")
            print(f"STEP 1: Downloading PDF for {arxiv_id}")
            print(f"{'='*80}")

            download_result = self.downloader.download_pdf(
                f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                arxiv_id
            )

            if not download_result['success']:
                workflow_result['errors'].append(f"PDF download failed: {download_result.get('error')}")
                return workflow_result

            pdf_path = download_result['file_path']
            workflow_result['pdf_path'] = pdf_path
            workflow_result['steps_completed'].append('download')
            print(f"✓ PDF downloaded: {pdf_path}")

            # Step 2: Add document to database (if not exists)
            print(f"\n{'='*80}")
            print(f"STEP 2: Adding document to database")
            print(f"{'='*80}")

            if not paper_metadata:
                paper_metadata = {
                    'title': f'Paper {arxiv_id}',
                    'authors': [],
                    'year': '',
                    'arxiv_id': arxiv_id
                }

            # Check if document already exists
            existing_doc = self.db.get_document_by_arxiv_id(arxiv_id)
            if existing_doc:
                document_id = existing_doc['id']
                print(f"✓ Document already exists (ID: {document_id})")
            else:
                document_id = self.db.add_document(
                    title=paper_metadata.get('title', f'Paper {arxiv_id}'),
                    authors=paper_metadata.get('authors', []),
                    year=paper_metadata.get('year', ''),
                    arxiv_id=arxiv_id,
                    pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    abstract=paper_metadata.get('abstract', '')
                )
                print(f"✓ Document added (ID: {document_id})")

            workflow_result['document_id'] = document_id
            workflow_result['steps_completed'].append('database_add')

            # Step 3: Process PDF and create RAG embeddings
            print(f"\n{'='*80}")
            print(f"STEP 3: Processing PDF and creating embeddings")
            print(f"{'='*80}")

            process_result = self.rag_engine.process_document(
                pdf_path=pdf_path,
                document_id=document_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            if not process_result['success']:
                workflow_result['errors'].append(f"RAG processing failed: {process_result.get('error')}")
                return workflow_result

            workflow_result['rag_stats'] = {
                'num_chunks': process_result.get('num_chunks', 0),
                'processing_time': process_result.get('elapsed_time', 0)
            }
            workflow_result['steps_completed'].append('rag_processing')
            print(f"✓ RAG processing complete: {process_result.get('num_chunks', 0)} chunks")

            # Step 4: Multi-agent comprehensive analysis
            print(f"\n{'='*80}")
            print(f"STEP 4: Running multi-agent analysis")
            print(f"{'='*80}")

            analysis_result = self.orchestrator.analyze_paper(
                pdf_path=pdf_path,
                paper_metadata=paper_metadata,
                parallel=parallel_agents,
                max_workers=7
            )

            if not analysis_result['success']:
                workflow_result['errors'].append(f"Multi-agent analysis failed: {analysis_result.get('error')}")
                return workflow_result

            workflow_result['analysis_stats'] = {
                'successful_agents': analysis_result['metrics']['successful_agents'],
                'total_agents': analysis_result['metrics']['total_agents'],
                'total_time': analysis_result['metrics']['total_time'],
                'total_tokens': analysis_result['metrics']['total_tokens']
            }
            workflow_result['steps_completed'].append('multi_agent_analysis')
            print(f"✓ Multi-agent analysis complete: {analysis_result['metrics']['successful_agents']}/7 agents")

            # Step 5: Synthesis
            print(f"\n{'='*80}")
            print(f"STEP 5: Synthesizing findings")
            print(f"{'='*80}")

            synthesis_result = self.synthesizer.synthesize(analysis_result)

            if not synthesis_result['success']:
                workflow_result['errors'].append(f"Synthesis failed: {synthesis_result.get('error')}")
                return workflow_result

            workflow_result['synthesis_stats'] = {
                'time': synthesis_result.get('elapsed_time', 0),
                'tokens': synthesis_result.get('tokens_used', 0)
            }
            workflow_result['steps_completed'].append('synthesis')
            print(f"✓ Synthesis complete")

            # Step 6: Store comprehensive analysis in database
            if store_analysis:
                print(f"\n{'='*80}")
                print(f"STEP 6: Storing analysis in database")
                print(f"{'='*80}")

                analysis_id = self.db.store_comprehensive_analysis(
                    document_id=document_id,
                    analysis_result=analysis_result,
                    synthesis_result=synthesis_result
                )

                workflow_result['analysis_id'] = analysis_id
                workflow_result['steps_completed'].append('store_analysis')
                print(f"✓ Analysis stored (ID: {analysis_id})")

            # Calculate total workflow time
            total_time = time.time() - start_time
            workflow_result['total_workflow_time'] = total_time
            workflow_result['success'] = True

            # Add results
            workflow_result['analysis_result'] = analysis_result
            workflow_result['synthesis_result'] = synthesis_result

            print(f"\n{'='*80}")
            print(f"WORKFLOW COMPLETE")
            print(f"{'='*80}")
            print(f"Total time: {total_time:.2f}s")
            print(f"Steps completed: {', '.join(workflow_result['steps_completed'])}")
            print(f"Document ID: {document_id}")
            if store_analysis:
                print(f"Analysis ID: {analysis_id}")

            return workflow_result

        except Exception as e:
            workflow_result['errors'].append(f"Workflow exception: {str(e)}")
            workflow_result['total_workflow_time'] = time.time() - start_time
            return workflow_result

    def analyze_existing_document(
        self,
        document_id: int,
        parallel_agents: bool = True,
        store_analysis: bool = True
    ) -> Dict:
        """
        Run comprehensive analysis on existing document (already in database with RAG)

        Args:
            document_id: Document ID
            parallel_agents: Use parallel agent execution
            store_analysis: Store analysis results

        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        result = {
            'success': False,
            'document_id': document_id
        }

        try:
            # Get document info
            document = self.db.get_document_by_id(document_id)
            if not document:
                result['error'] = f"Document {document_id} not found"
                return result

            # Check if PDF exists
            pdf_path = f"documents/{document['arxiv_id']}.pdf"
            if not Path(pdf_path).exists():
                result['error'] = f"PDF not found: {pdf_path}"
                return result

            # Prepare metadata
            paper_metadata = {
                'title': document['title'],
                'authors': document.get('authors', []),
                'year': document.get('year', ''),
                'arxiv_id': document['arxiv_id']
            }

            # Run analysis
            print(f"\nRunning comprehensive analysis for: {document['title']}")
            analysis_result = self.orchestrator.analyze_paper(
                pdf_path=pdf_path,
                paper_metadata=paper_metadata,
                parallel=parallel_agents,
                max_workers=7
            )

            if not analysis_result['success']:
                result['error'] = 'Analysis failed'
                return result

            # Run synthesis
            synthesis_result = self.synthesizer.synthesize(analysis_result)

            if not synthesis_result['success']:
                result['error'] = 'Synthesis failed'
                return result

            # Store if requested
            if store_analysis:
                analysis_id = self.db.store_comprehensive_analysis(
                    document_id=document_id,
                    analysis_result=analysis_result,
                    synthesis_result=synthesis_result
                )
                result['analysis_id'] = analysis_id

            result['success'] = True
            result['analysis_result'] = analysis_result
            result['synthesis_result'] = synthesis_result
            result['elapsed_time'] = time.time() - start_time

            return result

        except Exception as e:
            result['error'] = str(e)
            result['elapsed_time'] = time.time() - start_time
            return result

    def chat_with_paper(
        self,
        document_id: int,
        question: str,
        use_analysis: bool = True,
        use_rag: bool = True,
        temperature: float = 0.3,
        save_to_history: bool = True
    ) -> Dict:
        """
        Ask questions about a paper using hybrid context (analysis + RAG)

        Args:
            document_id: Document ID
            question: User's question
            use_analysis: Include comprehensive analysis as context
            use_rag: Include RAG search results as context
            temperature: LLM temperature
            save_to_history: Save to chat history

        Returns:
            Dictionary with answer and metadata
        """
        return self.chat_system.chat(
            document_id=document_id,
            question=question,
            use_analysis=use_analysis,
            use_rag=use_rag,
            temperature=temperature,
            save_to_history=save_to_history
        )

    def get_stored_analysis(self, document_id: int) -> Optional[Dict]:
        """
        Retrieve stored comprehensive analysis for a document

        Args:
            document_id: Document ID

        Returns:
            Analysis dictionary or None
        """
        return self.db.get_analysis_by_document_id(document_id)

    def get_chat_history(self, document_id: int, limit: int = 50) -> List[Dict]:
        """
        Get chat history for a document

        Args:
            document_id: Document ID
            limit: Maximum number of messages

        Returns:
            List of chat messages
        """
        return self.chat_system.get_chat_history(document_id, limit=limit)

    def list_analyzed_papers(
        self,
        quality_filter: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        List all papers with stored comprehensive analyses

        Args:
            quality_filter: Filter by quality rating (high/medium/low)
            limit: Maximum number of results

        Returns:
            List of analysis summaries
        """
        return self.db.list_analyses(quality_filter=quality_filter, limit=limit)

    def get_analysis_statistics(self) -> Dict:
        """
        Get statistics about stored analyses

        Returns:
            Dictionary with statistics
        """
        return self.db.get_analysis_statistics()


if __name__ == "__main__":
    # Test workflow manager
    print("Testing PaperAnalysisWorkflow...")

    workflow = PaperAnalysisWorkflow()

    print("\n✓ PaperAnalysisWorkflow initialized")
    print("\nAvailable methods:")
    print("  - process_and_analyze_paper(arxiv_id, ...) - Complete workflow")
    print("  - analyze_existing_document(document_id, ...) - Analyze existing doc")
    print("  - chat_with_paper(document_id, question, ...) - Ask questions")
    print("  - get_stored_analysis(document_id) - Retrieve analysis")
    print("  - get_chat_history(document_id) - Get chat history")
    print("  - list_analyzed_papers() - List all analyses")
    print("  - get_analysis_statistics() - Get stats")
