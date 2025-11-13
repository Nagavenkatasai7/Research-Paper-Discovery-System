"""
Document Chat System
====================
Intelligent Q&A system that combines:
1. RAG (vector search over document chunks)
2. Comprehensive multi-agent analysis
3. Grok-4 for generating contextual answers
"""

import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import config
from rag_system.database import RAGDatabase
from rag_system.rag_engine import RAGEngine


class DocumentChatSystem:
    """
    Comprehensive document Q&A system combining RAG and analysis.
    """

    def __init__(self, db: Optional[RAGDatabase] = None):
        """
        Initialize chat system

        Args:
            db: Optional database instance (will create new if not provided)
        """
        self.db = db or RAGDatabase()
        self.rag_engine = RAGEngine(db=self.db)

        # Initialize Grok-4 client
        self.grok_client = OpenAI(
            api_key=config.GROK_SETTINGS['api_key'],
            base_url="https://api.x.ai/v1"
        )

    def get_document_context(
        self,
        document_id: int,
        question: str,
        use_analysis: bool = True,
        use_rag: bool = True,
        top_k: int = 5
    ) -> Dict:
        """
        Retrieve comprehensive context for answering a question.

        Args:
            document_id: Document ID
            question: User's question
            use_analysis: Include comprehensive analysis context
            use_rag: Include RAG search results
            top_k: Number of RAG chunks to retrieve

        Returns:
            Dictionary with context information
        """
        context = {
            'document_id': document_id,
            'question': question,
            'has_analysis': False,
            'has_rag_results': False,
            'analysis_context': None,
            'rag_context': None
        }

        # Get document metadata
        document = self.db.get_document_by_id(document_id)
        if document:
            context['document'] = {
                'title': document.get('title', ''),
                'authors': document.get('authors', []),
                'year': document.get('year', ''),
                'abstract': document.get('abstract', '')
            }

        # Retrieve comprehensive analysis if available
        if use_analysis:
            analysis = self.db.get_analysis_by_document_id(document_id)
            if analysis:
                context['has_analysis'] = True
                context['analysis_context'] = {
                    'executive_summary': analysis.get('executive_summary', ''),
                    'key_contributions': analysis.get('key_contributions', []),
                    'methodology_summary': self._extract_methodology_summary(analysis),
                    'results_summary': self._extract_results_summary(analysis),
                    'strengths': analysis.get('strengths', []),
                    'limitations': analysis.get('limitations', []),
                    'quality_rating': analysis.get('quality_rating', ''),
                    'novelty_rating': analysis.get('novelty_rating', ''),
                }

        # Retrieve RAG results
        if use_rag:
            rag_results = self.rag_engine.query(question, document_id=document_id, top_k=top_k)
            if rag_results and rag_results.get('chunks'):
                context['has_rag_results'] = True
                context['rag_context'] = {
                    'relevant_chunks': [
                        {
                            'text': chunk['text'],
                            'page': chunk.get('page_num', 'N/A'),
                            'score': chunk.get('score', 0)
                        }
                        for chunk in rag_results['chunks']
                    ]
                }

        return context

    def _extract_methodology_summary(self, analysis: Dict) -> str:
        """Extract methodology summary from agent results"""
        try:
            agent_results = analysis.get('agent_results', {})
            methodology = agent_results.get('methodology', {})

            if methodology and methodology.get('success'):
                method_analysis = methodology.get('analysis', {})
                design = method_analysis.get('research_design', '')
                techniques = method_analysis.get('analysis_techniques', [])

                if design:
                    summary = f"Research Design: {design[:200]}..."
                    if techniques:
                        summary += f" Techniques: {', '.join(techniques[:3])}"
                    return summary

            return ""
        except Exception:
            return ""

    def _extract_results_summary(self, analysis: Dict) -> str:
        """Extract results summary from agent results"""
        try:
            agent_results = analysis.get('agent_results', {})
            results = agent_results.get('results', {})

            if results and results.get('success'):
                results_analysis = results.get('analysis', {})
                findings = results_analysis.get('main_findings', [])

                if findings:
                    return "Key Findings: " + "; ".join(findings[:3])

            return ""
        except Exception:
            return ""

    def build_system_prompt(self) -> str:
        """Build system prompt for the chat assistant"""
        return """You are an expert research assistant helping users understand academic papers.

Your role:
1. Answer questions about research papers accurately and comprehensively
2. Use the provided context (paper analysis + relevant excerpts) to give informed answers
3. Cite specific sections or findings when possible
4. If information isn't in the context, acknowledge uncertainty
5. Be concise but thorough
6. Use clear, accessible language

Guidelines:
- Prioritize the comprehensive analysis for high-level questions
- Use RAG excerpts for specific details or quotes
- Distinguish between what the paper says vs. your interpretation
- Highlight key contributions, findings, and limitations when relevant"""

    def build_user_prompt(self, question: str, context: Dict) -> str:
        """
        Build user prompt with question and context

        Args:
            question: User's question
            context: Context dictionary from get_document_context

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Add document metadata
        if 'document' in context:
            doc = context['document']
            prompt_parts.append(f"""PAPER INFORMATION:
Title: {doc.get('title', 'Unknown')}
Authors: {', '.join(doc.get('authors', [])[:5])}
Year: {doc.get('year', 'N/A')}
""")

        # Add comprehensive analysis context
        if context.get('has_analysis') and context.get('analysis_context'):
            analysis_ctx = context['analysis_context']

            prompt_parts.append("COMPREHENSIVE ANALYSIS:")

            # Executive summary
            if analysis_ctx.get('executive_summary'):
                prompt_parts.append(f"\nExecutive Summary:\n{analysis_ctx['executive_summary'][:800]}")

            # Key contributions
            if analysis_ctx.get('key_contributions'):
                contributions = analysis_ctx['key_contributions']
                prompt_parts.append(f"\nKey Contributions:\n" + "\n".join(f"- {c}" for c in contributions[:3]))

            # Methodology
            if analysis_ctx.get('methodology_summary'):
                prompt_parts.append(f"\nMethodology: {analysis_ctx['methodology_summary']}")

            # Results
            if analysis_ctx.get('results_summary'):
                prompt_parts.append(f"\nResults: {analysis_ctx['results_summary']}")

            # Strengths and Limitations
            if analysis_ctx.get('strengths'):
                strengths = analysis_ctx['strengths']
                prompt_parts.append(f"\nStrengths:\n" + "\n".join(f"- {s}" for s in strengths[:2]))

            if analysis_ctx.get('limitations'):
                limitations = analysis_ctx['limitations']
                prompt_parts.append(f"\nLimitations:\n" + "\n".join(f"- {l}" for l in limitations[:2]))

            # Quality ratings
            quality = analysis_ctx.get('quality_rating', '')
            novelty = analysis_ctx.get('novelty_rating', '')
            if quality or novelty:
                prompt_parts.append(f"\nAssessment: Quality={quality}, Novelty={novelty}")

        # Add RAG context
        if context.get('has_rag_results') and context.get('rag_context'):
            rag_ctx = context['rag_context']
            chunks = rag_ctx.get('relevant_chunks', [])

            if chunks:
                prompt_parts.append("\nRELEVANT EXCERPTS FROM PAPER:")

                for i, chunk in enumerate(chunks[:5], 1):
                    text = chunk['text'][:400]  # Limit chunk size
                    page = chunk.get('page', 'N/A')
                    prompt_parts.append(f"\n[Excerpt {i} - Page {page}]:\n{text}")

        # Add the question
        prompt_parts.append(f"\nUSER QUESTION:\n{question}")

        prompt_parts.append("\nPlease provide a comprehensive answer based on the information above:")

        return "\n".join(prompt_parts)

    def chat(
        self,
        document_id: int,
        question: str,
        use_analysis: bool = True,
        use_rag: bool = True,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        save_to_history: bool = True
    ) -> Dict:
        """
        Answer a question about a document

        Args:
            document_id: Document ID
            question: User's question
            use_analysis: Use comprehensive analysis as context
            use_rag: Use RAG search results as context
            temperature: LLM temperature
            max_tokens: Maximum response tokens
            save_to_history: Save to chat history

        Returns:
            Dictionary with answer and metadata
        """
        start_time = time.time()

        try:
            # Get context
            context = self.get_document_context(
                document_id=document_id,
                question=question,
                use_analysis=use_analysis,
                use_rag=use_rag
            )

            # Check if we have any context
            if not context.get('has_analysis') and not context.get('has_rag_results'):
                return {
                    'success': False,
                    'message': 'No context available for this document. Please process the document first.',
                    'elapsed_time': time.time() - start_time
                }

            # Build prompts
            system_prompt = self.build_system_prompt()
            user_prompt = self.build_user_prompt(question, context)

            # Call Grok-4
            response = self.grok_client.chat.completions.create(
                model=config.GROK_SETTINGS['model'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            answer = response.choices[0].message.content
            elapsed_time = time.time() - start_time

            # Prepare sources used
            sources = []
            if context.get('has_analysis'):
                sources.append('comprehensive_analysis')
            if context.get('has_rag_results'):
                sources.append('rag_search')
                # Add page numbers
                if context['rag_context'] and context['rag_context'].get('relevant_chunks'):
                    pages = set(chunk['page'] for chunk in context['rag_context']['relevant_chunks'])
                    sources.append(f"pages: {', '.join(map(str, sorted(pages)))}")

            # Save to chat history
            if save_to_history:
                try:
                    self.db.add_chat_history(
                        document_id=document_id,
                        user_question=question,
                        assistant_answer=answer,
                        sources_used='; '.join(sources),
                        retrieval_method='hybrid' if (use_analysis and use_rag) else ('analysis' if use_analysis else 'rag'),
                        response_time=elapsed_time
                    )
                except Exception as e:
                    print(f"Warning: Failed to save chat history: {e}")

            return {
                'success': True,
                'question': question,
                'answer': answer,
                'sources_used': sources,
                'context_used': {
                    'has_analysis': context.get('has_analysis', False),
                    'has_rag': context.get('has_rag_results', False),
                    'num_excerpts': len(context.get('rag_context', {}).get('relevant_chunks', []))
                },
                'elapsed_time': elapsed_time,
                'tokens_used': response.usage.total_tokens,
                'message': 'Answer generated successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Chat failed: {str(e)}',
                'elapsed_time': time.time() - start_time
            }

    def get_chat_history(
        self,
        document_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get chat history for a document

        Args:
            document_id: Document ID
            limit: Maximum number of messages

        Returns:
            List of chat messages
        """
        return self.db.get_chat_history(document_id, limit=limit)

    def clear_chat_history(self, document_id: int):
        """Clear chat history for a document"""
        # Use database method with proper write lock protection
        self.db.clear_chat_history(document_id)


if __name__ == "__main__":
    # Test document chat system
    print("Testing DocumentChatSystem...")

    chat_system = DocumentChatSystem()

    # This would need a processed document in the database
    print("✓ DocumentChatSystem initialized")
    print("\nNote: To fully test, you need:")
    print("  1. A document processed with RAG (embeddings + FAISS)")
    print("  2. Comprehensive analysis stored for the document")
    print("  3. Then you can use chat() to ask questions")
