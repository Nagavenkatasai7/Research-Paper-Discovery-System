"""
Enhanced RAG System with Advanced Retrieval Techniques
=======================================================
Implements cutting-edge RAG features:
- Vector database with embeddings
- Contextual retrieval
- Hybrid search (BM25 + Semantic)
- Query expansion
- Multi-hop QA
- Self-reflective RAG
- Citation context extraction
"""

import os
import re
from typing import List, Dict, Tuple, Optional
import numpy as np

# Import required libraries
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    from rank_bm25 import BM25Okapi
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️ Enhanced RAG dependencies not installed. Run: pip install chromadb sentence-transformers rank-bm25")


class EnhancedRAGSystem:
    """
    Advanced RAG system for research paper Q&A.

    Features:
    - Phase 1: Vector DB + Embeddings + Contextual Retrieval + Hybrid Search
    - Phase 2: Query Expansion + Multi-hop QA + Citation Extraction
    - Phase 3: Self-Reflective RAG + Confidence Scores
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Enhanced RAG System.

        Args:
            model_name: Name of the sentence-transformer model
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Enhanced RAG dependencies not installed")

        # Initialize embedding model
        print(f"📦 Loading embedding model: {model_name}...")
        self.embedding_model = SentenceTransformer(model_name)

        # Initialize ChromaDB (in-memory for now)
        self.chroma_client = chromadb.Client()
        self.collection = None

        # BM25 for hybrid search
        self.bm25 = None
        self.bm25_corpus = []

        # Paper data
        self.paper_data = None
        self.sections = []

        print("✅ Enhanced RAG System initialized")

    def index_paper(self, paper_title: str, sections_data: Dict[str, str]):
        """
        Index a research paper for retrieval.

        Args:
            paper_title: Title of the paper
            sections_data: Dictionary of section_name -> section_text
        """
        print(f"📄 Indexing paper: {paper_title[:50]}...")

        self.paper_data = {
            'title': paper_title,
            'sections': sections_data
        }

        # Create unique collection for this paper
        collection_name = f"paper_{hash(paper_title) % 10000}"

        # Delete existing collection if it exists
        try:
            self.chroma_client.delete_collection(name=collection_name)
        except Exception as e:
            # Collection doesn't exist - this is expected on first run
            print(f"Note: Could not delete collection (may not exist): {e}")

        # Create new collection
        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Prepare documents with contextual enrichment
        documents = []
        metadatas = []
        ids = []

        for section_name, section_text in sections_data.items():
            if not section_text or len(section_text.strip()) < 50:
                print(f"⚠️ Skipping section '{section_name}' (too short: {len(section_text.strip()) if section_text else 0} chars)")
                continue

            # Split long sections into chunks (500 chars each with 100 char overlap)
            chunks = self._chunk_text(section_text, chunk_size=500, overlap=100)

            for i, chunk in enumerate(chunks):
                # **PHASE 1.3: Contextual Retrieval**
                # Add context to each chunk before embedding
                contextual_chunk = f"[Paper: {paper_title}] [Section: {section_name}] {chunk}"

                documents.append(contextual_chunk)
                metadatas.append({
                    'section': section_name,
                    'chunk_id': i,
                    'original_text': chunk  # Store original without context
                })
                ids.append(f"{section_name}_{i}")

        # Edge case: No valid content to index
        if len(documents) == 0:
            print(f"⚠️ Warning: No valid content to index (all sections < 50 chars)")
            # Create a minimal placeholder to prevent ChromaDB errors
            placeholder = f"[Paper: {paper_title}] This paper has minimal extractable content."
            documents.append(placeholder)
            metadatas.append({
                'section': 'placeholder',
                'chunk_id': 0,
                'original_text': 'No extractable content available.'
            })
            ids.append('placeholder_0')

        # **PHASE 1.2: Create embeddings**
        print(f"🔢 Creating embeddings for {len(documents)} chunks...")
        embeddings = self.embedding_model.encode(documents, show_progress_bar=False)

        # **PHASE 1.1: Add to vector database**
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        # **PHASE 1.4: Prepare BM25 for hybrid search**
        print(f"🔍 Preparing BM25 index...")
        self.bm25_corpus = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(self.bm25_corpus)
        self.sections = documents

        print(f"✅ Indexed {len(documents)} chunks from {len(sections_data)} sections")

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # At least 50% of chunk
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def retrieve(self, query: str, top_k: int = 5, hybrid_alpha: float = 0.5) -> List[Dict]:
        """
        **PHASE 1.4: Hybrid Search** - Retrieve relevant chunks using hybrid search.

        Args:
            query: User query
            top_k: Number of chunks to retrieve
            hybrid_alpha: Weight for semantic vs keyword (0.5 = equal weight)

        Returns:
            List of retrieved chunks with metadata
        """
        if not self.collection:
            return []

        # **Semantic Search** (using embeddings)
        query_embedding = self.embedding_model.encode([query])[0]
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k * 2  # Get more candidates
        )

        # **Keyword Search** (using BM25)
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # **Hybrid Fusion**: Combine scores
        semantic_docs = semantic_results['documents'][0]
        semantic_distances = semantic_results['distances'][0]

        # Normalize scores to [0, 1]
        semantic_scores = [1 - dist for dist in semantic_distances]  # Convert distance to similarity
        bm25_scores_normalized = self._normalize_scores(bm25_scores)

        # Combine scores
        combined_scores = {}
        for i, doc in enumerate(semantic_docs):
            doc_idx = self.sections.index(doc)
            semantic_score = semantic_scores[i]
            bm25_score = bm25_scores_normalized[doc_idx]

            # Weighted combination
            combined_scores[doc] = (
                hybrid_alpha * semantic_score +
                (1 - hybrid_alpha) * bm25_score
            )

        # Sort by combined score
        sorted_docs = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Prepare results
        results = []
        for doc, score in sorted_docs:
            idx = self.sections.index(doc)
            metadata = semantic_results['metadatas'][0][semantic_docs.index(doc)]

            results.append({
                'content': metadata['original_text'],  # Return original text without context prefix (standardized to 'content')
                'text': metadata['original_text'],  # Keep 'text' for backward compatibility
                'section': metadata['section'],
                'chunk_id': metadata['chunk_id'],
                'score': score,
                'contextual_text': doc  # Keep contextual version for reference
            })

        return results

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """Normalize scores to [0, 1] range."""
        if len(scores) == 0:
            return scores
        min_score = scores.min()
        max_score = scores.max()
        if max_score - min_score == 0:
            return np.ones_like(scores)
        return (scores - min_score) / (max_score - min_score)

    def format_retrieval_context(self, retrieved_chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context for LLM.

        Args:
            retrieved_chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        if not retrieved_chunks:
            return "No relevant content found in the paper."

        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Source {i} - Section: {chunk['section']}, Relevance: {chunk['score']:.2f}]\n{chunk['text']}\n"
            )

        return "\n---\n".join(context_parts)

    def get_paper_stats(self) -> Dict:
        """Get statistics about the indexed paper."""
        if not self.collection:
            return {}

        count = self.collection.count()
        return {
            'total_chunks': count,
            'sections': len(self.paper_data['sections']) if self.paper_data else 0,
            'title': self.paper_data['title'] if self.paper_data else 'Unknown'
        }


# ============================================================================
# PHASE 2: Query Expansion & Multi-hop QA
# ============================================================================

class QueryExpander:
    """
    **PHASE 2.1: Query Expansion/Refinement**
    Uses LLM to expand and clarify vague queries before retrieval.
    """

    def __init__(self, llm_client):
        """
        Initialize query expander.

        Args:
            llm_client: LLM client (e.g., Grok)
        """
        self.llm = llm_client

    def expand_query(self, query: str, paper_title: str) -> Dict[str, str]:
        """
        Expand and refine user query for better retrieval.

        Args:
            query: Original user query
            paper_title: Title of the paper being queried

        Returns:
            Dict with 'original', 'expanded', and 'keywords'
        """
        prompt = f"""You are helping a researcher understand a scientific paper titled: "{paper_title}"

Original Query: "{query}"

Your task: Expand this query to make it more specific and comprehensive for retrieving relevant information from the paper.

Guidelines:
1. For vague queries (e.g., "quantum computing"), expand with specific aspects (e.g., "quantum computing algorithms, applications, and theoretical foundations")
2. For acronyms (e.g., "VQE"), expand to full terms (e.g., "Variational Quantum Eigensolver algorithm")
3. For broad topics (e.g., "AI"), add relevant subtopics (e.g., "artificial intelligence machine learning neural networks")
4. Add related technical terms and synonyms
5. Make it AT LEAST 50% longer than the original

Format your response EXACTLY as:
EXPANDED: [your expanded query here - must be significantly longer]
KEYWORDS: [keyword1, keyword2, keyword3, keyword4, keyword5]

Now expand the query:"""

        try:
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=250,  # Increased to allow longer expansions
                temperature=0.4  # Slightly higher for more creative expansions
            ).strip()

            # Parse response
            expanded = query  # fallback
            keywords = []

            if "EXPANDED:" in response:
                expanded = response.split("EXPANDED:")[1].split("KEYWORDS:")[0].strip()
            else:
                # LLM didn't follow format - try to extract meaningful expansion anyway
                if len(response) > len(query) * 1.5:
                    expanded = response.strip()
                    print(f"⚠️ Query expansion: LLM didn't use EXPANDED: format, using raw response")

            if "KEYWORDS:" in response:
                keywords_str = response.split("KEYWORDS:")[1].strip()
                keywords = [k.strip() for k in keywords_str.split(',')]

            # Ensure expansion is actually longer
            if len(expanded) <= len(query):
                print(f"⚠️ Query expansion failed to expand query (original: {len(query)} chars, expanded: {len(expanded)} chars)")
                # Try to use the full response if it's longer
                if len(response) > len(query):
                    expanded = response.strip()

            return {
                'original': query,
                'expanded': expanded,
                'keywords': keywords
            }

        except Exception as e:
            print(f"❌ Query expansion failed: {e}")
            return {
                'original': query,
                'expanded': query,
                'keywords': []
            }


class MultiHopQA:
    """
    **PHASE 2.2: Multi-hop Question Answering**
    Handles questions that require retrieving from multiple sections.
    """

    def __init__(self, rag_system: EnhancedRAGSystem, llm_client):
        """
        Initialize multi-hop QA system.

        Args:
            rag_system: Enhanced RAG system
            llm_client: LLM client
        """
        self.rag = rag_system
        self.llm = llm_client

    def detect_multi_hop(self, query: str) -> bool:
        """
        Detect if query requires multi-hop reasoning.

        Examples:
        - "How does this compare to the baseline in the intro?"
        - "What methods were used and what were the results?"
        - "What problem is addressed and how is it solved?"
        """
        multi_hop_indicators = [
            'compare', 'relationship', 'difference', 'how does', 'and what',
            'as mentioned', 'contradiction', 'consistent with', 'versus'
        ]

        query_lower = query.lower()
        return any(indicator in query_lower for indicator in multi_hop_indicators)

    def answer_multi_hop(self, query: str, paper_title: str) -> Dict:
        """
        Answer multi-hop question by retrieving from multiple sections.

        Args:
            query: User query
            paper_title: Paper title

        Returns:
            Dict with answer and supporting evidence
        """
        # Step 1: Break down query into sub-questions
        sub_questions = self._decompose_query(query)

        # Step 2: Retrieve evidence for each sub-question
        evidence = []
        for sub_q in sub_questions:
            chunks = self.rag.retrieve(sub_q, top_k=2)
            evidence.extend(chunks)

        # Step 3: Remove duplicates and re-rank
        unique_evidence = self._deduplicate_chunks(evidence)

        # Step 4: Synthesize answer
        context = self.rag.format_retrieval_context(unique_evidence[:5])

        answer_prompt = f"""You are answering a complex research question that requires reasoning across multiple sections of a paper.

Paper: {paper_title}

Question: {query}

Retrieved Evidence:
{context}

Instructions:
1. Synthesize information from ALL provided sources
2. Show how information connects across sections
3. Be comprehensive but concise (3-5 sentences)
4. Cite which sections you're using

Answer:"""

        try:
            answer = self.llm.generate(
                prompt=answer_prompt,
                max_tokens=400,
                temperature=0.5
            ).strip()

            return {
                'answer': answer,
                'evidence': unique_evidence[:5],
                'multi_hop': True,
                'sub_questions': sub_questions
            }

        except Exception as e:
            return {
                'answer': f"Error in multi-hop reasoning: {e}",
                'evidence': [],
                'multi_hop': True,
                'sub_questions': []
            }

    def _decompose_query(self, query: str) -> List[str]:
        """Break down complex query into simpler sub-questions."""
        # Simple heuristic decomposition
        sub_questions = [query]  # Always include original

        # Extract comparison terms
        if 'compare' in query.lower():
            sub_questions.append(query.replace('compare', 'what is').replace('comparison', 'description'))

        # Extract conjunctions
        if ' and ' in query:
            parts = query.split(' and ')
            sub_questions.extend(parts)

        return sub_questions[:3]  # Max 3 sub-questions

    def _deduplicate_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Remove duplicate chunks based on text similarity."""
        if not chunks:
            return []

        unique = []
        seen_texts = set()

        for chunk in chunks:
            text_hash = hash(chunk['text'][:100])  # Hash first 100 chars
            if text_hash not in seen_texts:
                unique.append(chunk)
                seen_texts.add(text_hash)

        return unique


# ============================================================================
# PHASE 3: Self-Reflective RAG & Confidence Scoring
# ============================================================================

class SelfReflectiveRAG:
    """
    **PHASE 3.1: Self-Reflective RAG**
    AI evaluates its own answers and retrieves more if needed.
    """

    def __init__(self, rag_system: EnhancedRAGSystem, llm_client):
        """Initialize self-reflective RAG."""
        self.rag = rag_system
        self.llm = llm_client

    def answer_with_reflection(self, query: str, paper_title: str, max_iterations: int = 2) -> Dict:
        """
        Answer question with self-reflection.

        Args:
            query: User query
            paper_title: Paper title
            max_iterations: Max reflection iterations

        Returns:
            Dict with answer, confidence, and reflection notes
        """
        iteration = 0
        current_answer = ""
        confidence = 0.0
        reflection_notes = []

        while iteration < max_iterations:
            iteration += 1

            # Retrieve relevant content
            chunks = self.rag.retrieve(query, top_k=5)
            context = self.rag.format_retrieval_context(chunks)

            # Generate answer
            answer_prompt = f"""Answer this question about the paper "{paper_title}":

Question: {query}

Retrieved Context:
{context}

Answer (2-4 sentences):"""

            try:
                current_answer = self.llm.generate(
                    prompt=answer_prompt,
                    max_tokens=300,
                    temperature=0.4
                ).strip()
            except Exception as e:
                print(f"Warning: Answer refinement iteration failed: {e}")
                break

            # **Self-Reflection**: Evaluate answer quality
            reflection = self._reflect_on_answer(query, current_answer, context)
            reflection_notes.append(reflection)

            confidence = reflection['confidence']

            # If confident enough, stop
            if confidence >= 0.7:
                break

            # Otherwise, refine query and try again
            query = reflection['refined_query']

        return {
            'answer': current_answer,
            'confidence': confidence,
            'iterations': iteration,
            'reflection_notes': reflection_notes,
            'final_evaluation': reflection_notes[-1] if reflection_notes else {}
        }

    def _reflect_on_answer(self, query: str, answer: str, context: str) -> Dict:
        """
        Reflect on answer quality.

        Returns:
            Dict with confidence score and suggestions
        """
        reflection_prompt = f"""Evaluate this answer's quality:

Question: {query}
Answer: {answer}

Rate confidence (0-1): Is the answer:
1. Directly supported by the context?
2. Comprehensive enough?
3. Addressing the actual question?

Respond with just a number between 0 and 1:"""

        try:
            confidence_str = self.llm.generate(
                prompt=reflection_prompt,
                max_tokens=10,
                temperature=0.1
            ).strip()

            # Extract number
            confidence = float(re.findall(r'0?\.\d+|[01]', confidence_str)[0])
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, IndexError) as e:
            # Default to 0.5 if parsing fails
            confidence = 0.5

        return {
            'confidence': confidence,
            'refined_query': query,  # Could be enhanced
            'needs_more_info': confidence < 0.7
        }


# Week 4: Analysis-Aware RAG Extensions

class AnalysisAwareRetriever:
    """
    Enhances RAG with agent analysis results for context-aware retrieval.

    Integrates findings from multi-agent analysis to:
    - Boost retrieval of key sections identified by agents
    - Filter results based on analysis priorities
    - Provide analysis-enriched context
    """

    def __init__(self, rag_system: EnhancedRAGSystem):
        """Initialize with RAG system"""
        self.rag_system = rag_system
        self.analysis_results = None
        self.key_sections = {}
        self.findings_index = {}

    def set_analysis_results(self, analysis_results: Dict):
        """
        Set agent analysis results for context-aware retrieval.

        Args:
            analysis_results: Results from DocumentAnalysisOrchestrator
        """
        self.analysis_results = analysis_results

        # Extract key sections from successful agents
        if analysis_results.get('success'):
            agent_results = analysis_results.get('analysis_results', {})

            for agent_name, agent_result in agent_results.items():
                if agent_result.get('success'):
                    analysis = agent_result.get('analysis', {})
                    self.key_sections[agent_name] = analysis

                    # Index findings for fast lookup
                    self._index_findings(agent_name, analysis)

    def _index_findings(self, agent_name: str, analysis: Dict):
        """Index key findings from agent analysis"""
        # Extract key terms from analysis
        findings = []

        # Extract from various fields based on agent type
        for key, value in analysis.items():
            if isinstance(value, list):
                findings.extend([str(v) for v in value])
            elif isinstance(value, str):
                findings.append(value)

        self.findings_index[agent_name] = findings

    def retrieve_with_analysis(
        self,
        query: str,
        top_k: int = 5,
        boost_analyzed_sections: bool = True,
        include_findings: bool = True
    ) -> Dict:
        """
        Retrieve with analysis-aware boosting.

        Args:
            query: User query
            top_k: Number of chunks to retrieve
            boost_analyzed_sections: Boost chunks from high-priority sections
            include_findings: Include agent findings in context

        Returns:
            Dictionary with retrieved chunks and analysis context
        """
        # Standard retrieval
        retrieved_chunks = self.rag_system.retrieve(query, top_k=top_k)

        # Boost chunks from important sections
        if boost_analyzed_sections and self.key_sections:
            retrieved_chunks = self._boost_important_sections(retrieved_chunks, query)

        # Add analysis context
        analysis_context = {}
        if include_findings and self.key_sections:
            analysis_context = self._get_relevant_findings(query)

        return {
            'chunks': retrieved_chunks,
            'analysis_context': analysis_context,
            'num_chunks': len(retrieved_chunks),
            'analysis_available': bool(self.key_sections)
        }

    def _boost_important_sections(self, chunks: List[Dict], query: str) -> List[Dict]:
        """Boost chunks from sections identified as important by agents"""
        # Determine query topic
        query_lower = query.lower()

        # Mapping of topics to relevant sections
        section_priority = {
            'method': ['methodology', 'abstract'],
            'result': ['results', 'tables', 'figures'],
            'conclusion': ['conclusion', 'discussion'],
            'limitation': ['discussion', 'conclusion'],
            'contribution': ['abstract', 'conclusion']
        }

        # Find relevant sections for query
        relevant_sections = []
        for topic, sections in section_priority.items():
            if topic in query_lower:
                relevant_sections.extend(sections)

        # Boost scores for relevant sections
        for chunk in chunks:
            section = chunk.get('metadata', {}).get('section', '')
            if section in relevant_sections:
                chunk['score'] = chunk.get('score', 0) * 1.3  # 30% boost

        # Re-sort by boosted scores
        chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)

        return chunks

    def _get_relevant_findings(self, query: str) -> Dict:
        """Get relevant findings from agent analysis for query"""
        query_lower = query.lower()
        relevant_findings = {}

        # Find agents with relevant findings
        for agent_name, analysis in self.key_sections.items():
            # Check if agent is relevant to query
            if self._is_agent_relevant(agent_name, query_lower):
                # Extract relevant fields
                relevant_data = {}

                if agent_name == 'methodology' and ('method' in query_lower or 'approach' in query_lower):
                    relevant_data = {
                        'research_design': analysis.get('research_design'),
                        'approach': analysis.get('approach')
                    }
                elif agent_name == 'results' and ('result' in query_lower or 'finding' in query_lower):
                    relevant_data = {
                        'main_findings': analysis.get('main_findings', [])[:3],
                        'performance_metrics': analysis.get('performance_metrics', {})
                    }
                elif agent_name == 'discussion' and ('limitation' in query_lower or 'implication' in query_lower):
                    relevant_data = {
                        'limitations': analysis.get('limitations', []),
                        'implications': analysis.get('theoretical_implications', [])[:2]
                    }
                elif agent_name == 'conclusion' and ('contribution' in query_lower or 'future' in query_lower):
                    relevant_data = {
                        'contributions': analysis.get('main_contributions', []),
                        'future_work': analysis.get('future_directions', [])[:2]
                    }

                if relevant_data:
                    relevant_findings[agent_name] = relevant_data

        return relevant_findings

    def _is_agent_relevant(self, agent_name: str, query_lower: str) -> bool:
        """Check if agent is relevant to query"""
        relevance_map = {
            'methodology': ['method', 'approach', 'technique', 'design'],
            'results': ['result', 'finding', 'performance', 'metric', 'accuracy'],
            'discussion': ['limitation', 'implication', 'impact', 'discuss'],
            'conclusion': ['contribution', 'future', 'conclude', 'summary'],
            'abstract': ['objective', 'goal', 'purpose', 'summary'],
            'tables': ['table', 'metric', 'performance', 'comparison'],
            'figures': ['figure', 'plot', 'diagram', 'visualization']
        }

        keywords = relevance_map.get(agent_name, [])
        return any(keyword in query_lower for keyword in keywords)

    def format_analysis_context(self, analysis_context: Dict) -> str:
        """Format analysis context for LLM prompt"""
        if not analysis_context:
            return ""

        lines = ["**Analysis Context:**"]

        for agent_name, data in analysis_context.items():
            lines.append(f"\n**{agent_name.title()}:**")
            for key, value in data.items():
                if isinstance(value, list):
                    lines.append(f"- {key}: {', '.join(map(str, value))}")
                else:
                    lines.append(f"- {key}: {value}")

        return '\n'.join(lines)


def create_enhanced_rag_system(paper_data: Optional[Dict] = None, llm_client=None) -> Dict:
    """
    Factory function to create and initialize all enhanced RAG components.

    Args:
        paper_data: Optional dictionary with 'title' and 'sections' (dict of section_name -> text)
                   If not provided, components are created but paper is not indexed yet
        llm_client: Optional LLM client for query expansion. If None, creates default Grok client.

    Returns:
        Dictionary with all RAG components
    """
    # Initialize core RAG system
    rag = EnhancedRAGSystem()

    # Index the paper if data provided
    if paper_data:
        rag.index_paper(
            paper_title=paper_data['title'],
            sections_data=paper_data['sections']
        )

    # Create default Grok client if none provided
    if llm_client is None:
        try:
            import sys
            sys.path.append('..')
            from grok_client import GrokClient
            import config
            llm_client = GrokClient(
                api_key=config.GROK_SETTINGS['api_key'],
                model=config.GROK_SETTINGS['model'],
                validate=False  # Skip validation for faster initialization
            )
        except Exception as e:
            print(f"⚠️ Could not create default Grok client: {e}")
            llm_client = None

    components = {
        'rag': rag,
        'query_expander': None,
        'multi_hop_qa': None,
        'self_reflective': None,
        'analysis_aware': None  # Week 4: Analysis-aware retriever
    }

    # Initialize advanced components if LLM client available
    if llm_client:
        components['query_expander'] = QueryExpander(llm_client)
        components['multi_hop_qa'] = MultiHopQA(rag, llm_client)
        components['self_reflective'] = SelfReflectiveRAG(rag, llm_client)

    # Initialize analysis-aware retriever (Week 4)
    components['analysis_aware'] = AnalysisAwareRetriever(rag)

    return components
