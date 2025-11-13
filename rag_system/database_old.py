"""
Database Module for RAG System
===============================

Manages SQLite database for storing document metadata, embeddings info, and chat history.
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import threading


class RAGDatabase:
    """Manages SQLite database for RAG system with thread-safe connections"""

    def __init__(self, db_path: str = "database/rag_documents.db"):
        """
        Initialize database connection with thread-safety

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

        # Thread-local storage for connections
        self._local = threading.local()
        # Lock for write operations
        self._write_lock = threading.Lock()

        # Initialize tables using a connection
        self._create_tables()

    def _get_connection(self):
        """Get thread-local connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self.db_path))
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doi TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                venue TEXT,
                abstract TEXT,
                pdf_path TEXT,
                pdf_url TEXT,
                page_count INTEGER,
                processing_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Document embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                faiss_index_path TEXT NOT NULL,
                chunk_count INTEGER NOT NULL,
                embedding_model TEXT NOT NULL,
                embedding_dim INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Document summaries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                summary_text TEXT NOT NULL,
                model_used TEXT NOT NULL,
                summary_type TEXT DEFAULT 'comprehensive',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Chat history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                user_question TEXT NOT NULL,
                assistant_answer TEXT NOT NULL,
                sources_used TEXT,
                retrieval_method TEXT,
                response_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Processing logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                elapsed_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Comprehensive multi-agent analyses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                analysis_type TEXT DEFAULT 'multi_agent',

                -- Analysis results JSON (from all 7 agents)
                agent_results TEXT NOT NULL,

                -- Synthesis results JSON
                synthesis_result TEXT NOT NULL,

                -- Performance metrics
                total_time REAL NOT NULL,
                total_tokens INTEGER NOT NULL,
                estimated_cost REAL NOT NULL,
                successful_agents INTEGER NOT NULL,
                total_agents INTEGER NOT NULL,

                -- Overall assessment (from synthesis)
                quality_rating TEXT,
                novelty_rating TEXT,
                impact_rating TEXT,
                rigor_rating TEXT,

                -- Key insights (for quick access)
                executive_summary TEXT,
                key_contributions TEXT,
                strengths TEXT,
                limitations TEXT,
                future_directions TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Document chunks table (for RAG)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                start_idx INTEGER,
                end_idx INTEGER,
                page_num INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # Agent context table (for Week 2: Context Manager integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                analysis_id INTEGER,
                agent_name TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                finding_content TEXT NOT NULL,
                relevance_to TEXT,
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (analysis_id) REFERENCES document_analyses(id) ON DELETE CASCADE
            )
        """)

        # Progressive summaries table (for Week 4: Multi-level summarization)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progressive_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                analysis_id INTEGER,
                level INTEGER NOT NULL,
                summary_content TEXT NOT NULL,
                section_name TEXT,
                parent_summary_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (analysis_id) REFERENCES document_analyses(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_summary_id) REFERENCES progressive_summaries(id) ON DELETE SET NULL
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyses_document
            ON document_analyses(document_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyses_quality
            ON document_analyses(quality_rating)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analyses_created
            ON document_analyses(created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_document
            ON document_chunks(document_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_context_document
            ON agent_context(document_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_context_analysis
            ON agent_context(analysis_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_context_agent
            ON agent_context(agent_name)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_progressive_summaries_document
            ON progressive_summaries(document_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_progressive_summaries_analysis
            ON progressive_summaries(analysis_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_progressive_summaries_level
            ON progressive_summaries(level)
        """)

        self.conn.commit()

    # Document operations

    def add_document(
        self,
        doi: str,
        title: str,
        authors: List[str] = None,
        year: int = None,
        venue: str = None,
        abstract: str = None,
        pdf_path: str = None,
        pdf_url: str = None
    ) -> int:
        """
        Add a new document to database

        Returns:
            Document ID
        """
        cursor = self.conn.cursor()

        authors_str = json.dumps(authors) if authors else None

        cursor.execute("""
            INSERT INTO documents (doi, title, authors, year, venue, abstract, pdf_path, pdf_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (doi, title, authors_str, year, venue, abstract, pdf_path, pdf_url))

        self.conn.commit()
        return cursor.lastrowid

    def get_document_by_doi(self, doi: str) -> Optional[Dict]:
        """Get document by DOI"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE doi = ?", (doi,))
        row = cursor.fetchone()

        if row:
            doc = dict(row)
            if doc.get('authors'):
                doc['authors'] = json.loads(doc['authors'])
            return doc
        return None

    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get document by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        if row:
            doc = dict(row)
            if doc.get('authors'):
                doc['authors'] = json.loads(doc['authors'])
            return doc
        return None

    def update_document(self, doc_id: int, **kwargs):
        """Update document fields"""
        cursor = self.conn.cursor()

        # Build UPDATE query dynamically
        fields = []
        values = []
        for key, value in kwargs.items():
            if key == 'authors' and isinstance(value, list):
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            values.append(value)

        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(doc_id)

        query = f"UPDATE documents SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
        self.conn.commit()

    def delete_document(self, doc_id: int):
        """Delete document and all related records"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self.conn.commit()

    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all documents"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM documents
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        docs = []
        for row in cursor.fetchall():
            doc = dict(row)
            if doc.get('authors'):
                doc['authors'] = json.loads(doc['authors'])
            docs.append(doc)

        return docs

    # Embeddings operations

    def add_embedding_info(
        self,
        document_id: int,
        faiss_index_path: str,
        chunk_count: int,
        embedding_model: str,
        embedding_dim: int
    ) -> int:
        """Add embedding information"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO document_embeddings
            (document_id, faiss_index_path, chunk_count, embedding_model, embedding_dim)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, faiss_index_path, chunk_count, embedding_model, embedding_dim))

        self.conn.commit()
        return cursor.lastrowid

    def get_embedding_info(self, document_id: int) -> Optional[Dict]:
        """Get embedding information for a document"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM document_embeddings WHERE document_id = ?
        """, (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # Summary operations

    def add_summary(
        self,
        document_id: int,
        summary_text: str,
        model_used: str,
        summary_type: str = 'comprehensive'
    ) -> int:
        """Add document summary"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO document_summaries
            (document_id, summary_text, model_used, summary_type)
            VALUES (?, ?, ?, ?)
        """, (document_id, summary_text, model_used, summary_type))

        self.conn.commit()
        return cursor.lastrowid

    def get_summary(self, document_id: int) -> Optional[Dict]:
        """Get summary for a document"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM document_summaries WHERE document_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (document_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # Chat history operations

    def add_chat_message(
        self,
        document_id: int,
        user_question: str,
        assistant_answer: str,
        sources_used: List[int] = None,
        retrieval_method: str = None,
        response_time: float = None
    ) -> int:
        """Add chat message to history"""
        cursor = self.conn.cursor()

        sources_str = json.dumps(sources_used) if sources_used else None

        cursor.execute("""
            INSERT INTO chat_history
            (document_id, user_question, assistant_answer, sources_used, retrieval_method, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (document_id, user_question, assistant_answer, sources_str, retrieval_method, response_time))

        self.conn.commit()
        return cursor.lastrowid

    def get_chat_history(
        self,
        document_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get chat history for a document"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chat_history
            WHERE document_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (document_id, limit))

        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            if msg.get('sources_used'):
                msg['sources_used'] = json.loads(msg['sources_used'])
            messages.append(msg)

        return messages

    def clear_chat_history(self, document_id: int):
        """Clear chat history for a document"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE document_id = ?", (document_id,))
        self.conn.commit()

    # Processing logs

    def add_processing_log(
        self,
        document_id: int,
        stage: str,
        status: str,
        message: str = None,
        elapsed_time: float = None
    ):
        """Add processing log entry"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO processing_logs
            (document_id, stage, status, message, elapsed_time)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, stage, status, message, elapsed_time))

        self.conn.commit()

    def get_processing_logs(self, document_id: int) -> List[Dict]:
        """Get processing logs for a document"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM processing_logs
            WHERE document_id = ?
            ORDER BY created_at ASC
        """, (document_id,))

        return [dict(row) for row in cursor.fetchall()]

    # Statistics

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        cursor = self.conn.cursor()

        stats = {}

        # Total documents
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        stats['total_documents'] = cursor.fetchone()['count']

        # Documents with embeddings
        cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM document_embeddings")
        stats['documents_with_embeddings'] = cursor.fetchone()['count']

        # Documents with summaries
        cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM document_summaries")
        stats['documents_with_summaries'] = cursor.fetchone()['count']

        # Total chat messages
        cursor.execute("SELECT COUNT(*) as count FROM chat_history")
        stats['total_chat_messages'] = cursor.fetchone()['count']

        # Processing status breakdown
        cursor.execute("""
            SELECT processing_status, COUNT(*) as count
            FROM documents
            GROUP BY processing_status
        """)
        stats['status_breakdown'] = {row['processing_status']: row['count']
                                    for row in cursor.fetchall()}

        return stats

    # Comprehensive Analysis operations

    def store_comprehensive_analysis(
        self,
        document_id: int,
        analysis_result: Dict,
        synthesis_result: Dict
    ) -> int:
        """
        Store comprehensive multi-agent analysis result

        Args:
            document_id: ID of the document
            analysis_result: Full orchestrator analysis result
            synthesis_result: Full synthesis result

        Returns:
            Analysis ID
        """
        cursor = self.conn.cursor()

        # Extract metrics
        metrics = analysis_result.get('metrics', {})
        synthesis = synthesis_result.get('synthesis', {})
        assessment = synthesis.get('overall_assessment', {})

        # Serialize JSON data
        agent_results_json = json.dumps(analysis_result.get('analysis_results', {}))
        synthesis_json = json.dumps(synthesis)

        # Extract key insights as separate fields for easy querying
        contributions_json = json.dumps(synthesis.get('key_contributions', []))
        strengths_json = json.dumps(synthesis.get('strengths', []))
        limitations_json = json.dumps(synthesis.get('limitations', []))
        future_json = json.dumps(synthesis.get('future_directions', []))

        cursor.execute("""
            INSERT INTO document_analyses (
                document_id, analysis_type, agent_results, synthesis_result,
                total_time, total_tokens, estimated_cost,
                successful_agents, total_agents,
                quality_rating, novelty_rating, impact_rating, rigor_rating,
                executive_summary, key_contributions, strengths, limitations, future_directions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            'multi_agent',
            agent_results_json,
            synthesis_json,
            metrics.get('total_time', 0) + synthesis_result.get('elapsed_time', 0),
            metrics.get('total_tokens', 0) + synthesis_result.get('tokens_used', 0),
            metrics.get('estimated_cost', 0) + (synthesis_result.get('tokens_used', 0) * 0.000009),
            metrics.get('successful_agents', 0),
            metrics.get('total_agents', 7),
            assessment.get('quality', ''),
            assessment.get('novelty', ''),
            assessment.get('impact', ''),
            assessment.get('rigor', ''),
            synthesis.get('executive_summary', ''),
            contributions_json,
            strengths_json,
            limitations_json,
            future_json
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_analysis_by_document_id(self, document_id: int) -> Optional[Dict]:
        """
        Get the latest comprehensive analysis for a document

        Args:
            document_id: Document ID

        Returns:
            Analysis dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM document_analyses
            WHERE document_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (document_id,))

        row = cursor.fetchone()
        if row:
            analysis = dict(row)
            # Deserialize JSON fields
            analysis['agent_results'] = json.loads(analysis['agent_results'])
            analysis['synthesis_result'] = json.loads(analysis['synthesis_result'])
            analysis['key_contributions'] = json.loads(analysis['key_contributions'])
            analysis['strengths'] = json.loads(analysis['strengths'])
            analysis['limitations'] = json.loads(analysis['limitations'])
            analysis['future_directions'] = json.loads(analysis['future_directions'])
            return analysis
        return None

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Get analysis by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM document_analyses WHERE id = ?", (analysis_id,))

        row = cursor.fetchone()
        if row:
            analysis = dict(row)
            # Deserialize JSON fields
            analysis['agent_results'] = json.loads(analysis['agent_results'])
            analysis['synthesis_result'] = json.loads(analysis['synthesis_result'])
            analysis['key_contributions'] = json.loads(analysis['key_contributions'])
            analysis['strengths'] = json.loads(analysis['strengths'])
            analysis['limitations'] = json.loads(analysis['limitations'])
            analysis['future_directions'] = json.loads(analysis['future_directions'])
            return analysis
        return None

    def list_analyses(
        self,
        quality_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List all comprehensive analyses with optional filters

        Args:
            quality_filter: Filter by quality rating ('high', 'medium', 'low')
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of analysis dictionaries
        """
        cursor = self.conn.cursor()

        query = """
            SELECT a.*, d.title, d.authors, d.year
            FROM document_analyses a
            JOIN documents d ON a.document_id = d.id
        """

        params = []
        if quality_filter:
            query += " WHERE a.quality_rating = ?"
            params.append(quality_filter)

        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)

        analyses = []
        for row in cursor.fetchall():
            analysis = dict(row)
            # Deserialize JSON fields
            if analysis.get('agent_results'):
                analysis['agent_results'] = json.loads(analysis['agent_results'])
            if analysis.get('synthesis_result'):
                analysis['synthesis_result'] = json.loads(analysis['synthesis_result'])
            if analysis.get('key_contributions'):
                analysis['key_contributions'] = json.loads(analysis['key_contributions'])
            if analysis.get('strengths'):
                analysis['strengths'] = json.loads(analysis['strengths'])
            if analysis.get('limitations'):
                analysis['limitations'] = json.loads(analysis['limitations'])
            if analysis.get('future_directions'):
                analysis['future_directions'] = json.loads(analysis['future_directions'])
            if analysis.get('authors'):
                analysis['authors'] = json.loads(analysis['authors'])
            analyses.append(analysis)

        return analyses

    def search_analyses_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        Search analyses by keyword in executive summary or contributions

        Args:
            keyword: Search keyword
            limit: Maximum results

        Returns:
            List of matching analyses
        """
        cursor = self.conn.cursor()

        query = """
            SELECT a.*, d.title, d.authors, d.year
            FROM document_analyses a
            JOIN documents d ON a.document_id = d.id
            WHERE a.executive_summary LIKE ?
               OR a.key_contributions LIKE ?
               OR d.title LIKE ?
            ORDER BY a.created_at DESC
            LIMIT ?
        """

        search_term = f"%{keyword}%"
        cursor.execute(query, (search_term, search_term, search_term, limit))

        analyses = []
        for row in cursor.fetchall():
            analysis = dict(row)
            # Deserialize JSON fields
            if analysis.get('agent_results'):
                analysis['agent_results'] = json.loads(analysis['agent_results'])
            if analysis.get('synthesis_result'):
                analysis['synthesis_result'] = json.loads(analysis['synthesis_result'])
            if analysis.get('key_contributions'):
                analysis['key_contributions'] = json.loads(analysis['key_contributions'])
            if analysis.get('strengths'):
                analysis['strengths'] = json.loads(analysis['strengths'])
            if analysis.get('limitations'):
                analysis['limitations'] = json.loads(analysis['limitations'])
            if analysis.get('future_directions'):
                analysis['future_directions'] = json.loads(analysis['future_directions'])
            if analysis.get('authors'):
                analysis['authors'] = json.loads(analysis['authors'])
            analyses.append(analysis)

        return analyses

    def delete_analysis(self, analysis_id: int):
        """Delete a comprehensive analysis"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM document_analyses WHERE id = ?", (analysis_id,))
        self.conn.commit()

    def get_analysis_statistics(self) -> Dict:
        """
        Get statistics about stored analyses

        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()

        stats = {}

        # Total analyses
        cursor.execute("SELECT COUNT(*) as count FROM document_analyses")
        stats['total_analyses'] = cursor.fetchone()['count']

        # By quality
        cursor.execute("""
            SELECT quality_rating, COUNT(*) as count
            FROM document_analyses
            GROUP BY quality_rating
        """)
        stats['by_quality'] = {row['quality_rating']: row['count']
                              for row in cursor.fetchall() if row['quality_rating']}

        # Average metrics
        cursor.execute("""
            SELECT
                AVG(total_time) as avg_time,
                AVG(total_tokens) as avg_tokens,
                AVG(estimated_cost) as avg_cost,
                AVG(successful_agents) as avg_success_rate
            FROM document_analyses
        """)
        row = cursor.fetchone()
        stats['average_time'] = row['avg_time'] or 0
        stats['average_tokens'] = row['avg_tokens'] or 0
        stats['average_cost'] = row['avg_cost'] or 0
        stats['average_success_rate'] = row['avg_success_rate'] or 0

        # Recent analyses (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM document_analyses
            WHERE created_at >= datetime('now', '-7 days')
        """)
        stats['recent_analyses_7d'] = cursor.fetchone()['count']

        return stats

    # Chunk management operations

    def add_chunk(
        self,
        document_id: int,
        text: str,
        start_idx: int = 0,
        end_idx: int = 0,
        page_num: int = 1
    ) -> int:
        """
        Add a text chunk to database

        Args:
            document_id: Document ID
            text: Chunk text
            start_idx: Start character index in document
            end_idx: End character index in document
            page_num: Page number

        Returns:
            Chunk ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO document_chunks (document_id, text, start_idx, end_idx, page_num)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, text, start_idx, end_idx, page_num))

        self.conn.commit()
        return cursor.lastrowid

    def get_chunks_by_document(self, document_id: int) -> List[Dict]:
        """
        Get all chunks for a document

        Args:
            document_id: Document ID

        Returns:
            List of chunk dictionaries
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM document_chunks
            WHERE document_id = ?
            ORDER BY start_idx
        """, (document_id,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_chunk_by_id(self, chunk_id: int) -> Optional[Dict]:
        """
        Get a chunk by ID

        Args:
            chunk_id: Chunk ID

        Returns:
            Chunk dictionary or None
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM document_chunks
            WHERE id = ?
        """, (chunk_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    # Agent context operations (Week 2: Context Manager)

    def store_agent_context(
        self,
        document_id: int,
        agent_name: str,
        finding_type: str,
        finding_content: Dict,
        analysis_id: Optional[int] = None,
        relevance_to: Optional[List[str]] = None,
        priority: str = 'medium'
    ) -> int:
        """
        Store context finding from an agent

        Args:
            document_id: Document ID
            agent_name: Name of the agent
            finding_type: Type of finding (methodology, result, limitation, etc.)
            finding_content: Finding data as dictionary
            analysis_id: Optional analysis ID to link to
            relevance_to: List of agent names this is relevant to
            priority: Priority level (high, medium, low)

        Returns:
            Context ID
        """
        cursor = self.conn.cursor()

        finding_json = json.dumps(finding_content)
        relevance_json = json.dumps(relevance_to) if relevance_to else None

        cursor.execute("""
            INSERT INTO agent_context
            (document_id, analysis_id, agent_name, finding_type, finding_content, relevance_to, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (document_id, analysis_id, agent_name, finding_type, finding_json, relevance_json, priority))

        self.conn.commit()
        return cursor.lastrowid

    def get_agent_context(
        self,
        document_id: int,
        agent_name: Optional[str] = None,
        finding_type: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """
        Get agent context findings with optional filters

        Args:
            document_id: Document ID
            agent_name: Filter by agent name (optional)
            finding_type: Filter by finding type (optional)
            priority: Filter by priority (optional)

        Returns:
            List of context dictionaries
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM agent_context WHERE document_id = ?"
        params = [document_id]

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if finding_type:
            query += " AND finding_type = ?"
            params.append(finding_type)

        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)

        contexts = []
        for row in cursor.fetchall():
            context = dict(row)
            context['finding_content'] = json.loads(context['finding_content'])
            if context.get('relevance_to'):
                context['relevance_to'] = json.loads(context['relevance_to'])
            contexts.append(context)

        return contexts

    def get_context_by_analysis(self, analysis_id: int) -> List[Dict]:
        """
        Get all context findings for a specific analysis

        Args:
            analysis_id: Analysis ID

        Returns:
            List of context dictionaries
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM agent_context
            WHERE analysis_id = ?
            ORDER BY agent_name, created_at
        """, (analysis_id,))

        contexts = []
        for row in cursor.fetchall():
            context = dict(row)
            context['finding_content'] = json.loads(context['finding_content'])
            if context.get('relevance_to'):
                context['relevance_to'] = json.loads(context['relevance_to'])
            contexts.append(context)

        return contexts

    # Progressive summaries operations (Week 4: Multi-level summarization)

    def store_progressive_summary(
        self,
        document_id: int,
        level: int,
        summary_content: str,
        section_name: Optional[str] = None,
        analysis_id: Optional[int] = None,
        parent_summary_id: Optional[int] = None
    ) -> int:
        """
        Store a progressive summary at a specific granularity level

        Args:
            document_id: Document ID
            level: Granularity level (1=most detailed, higher=more condensed)
            summary_content: Summary text
            section_name: Section name this summarizes (optional)
            analysis_id: Optional analysis ID to link to
            parent_summary_id: Optional parent summary for hierarchy

        Returns:
            Summary ID
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO progressive_summaries
            (document_id, analysis_id, level, summary_content, section_name, parent_summary_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (document_id, analysis_id, level, summary_content, section_name, parent_summary_id))

        self.conn.commit()
        return cursor.lastrowid

    def get_progressive_summaries(
        self,
        document_id: int,
        level: Optional[int] = None
    ) -> List[Dict]:
        """
        Get progressive summaries for a document

        Args:
            document_id: Document ID
            level: Optional filter by granularity level

        Returns:
            List of summary dictionaries
        """
        cursor = self.conn.cursor()

        if level is not None:
            cursor.execute("""
                SELECT * FROM progressive_summaries
                WHERE document_id = ? AND level = ?
                ORDER BY section_name, created_at
            """, (document_id, level))
        else:
            cursor.execute("""
                SELECT * FROM progressive_summaries
                WHERE document_id = ?
                ORDER BY level, section_name, created_at
            """, (document_id,))

        return [dict(row) for row in cursor.fetchall()]

    def get_summary_by_level(
        self,
        document_id: int,
        level: int,
        section_name: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get summary at a specific granularity level

        Args:
            document_id: Document ID
            level: Granularity level
            section_name: Optional section name filter

        Returns:
            Summary dictionary or None
        """
        cursor = self.conn.cursor()

        if section_name:
            cursor.execute("""
                SELECT * FROM progressive_summaries
                WHERE document_id = ? AND level = ? AND section_name = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (document_id, level, section_name))
        else:
            cursor.execute("""
                SELECT * FROM progressive_summaries
                WHERE document_id = ? AND level = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (document_id, level))

        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_agent_context(self, document_id: int):
        """Delete all agent context for a document"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM agent_context WHERE document_id = ?", (document_id,))
        self.conn.commit()

    def delete_progressive_summaries(self, document_id: int):
        """Delete all progressive summaries for a document"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM progressive_summaries WHERE document_id = ?", (document_id,))
        self.conn.commit()

    def close(self):
        """Close database connection"""
        self.conn.close()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.close()


if __name__ == "__main__":
    # Test database
    print("Testing RAGDatabase...")

    with RAGDatabase() as db:
        # Add a test document
        doc_id = db.add_document(
            doi="10.1234/test",
            title="Test Paper",
            authors=["Alice", "Bob"],
            year=2024,
            abstract="This is a test abstract."
        )

        print(f"✓ Document added with ID: {doc_id}")

        # Retrieve document
        doc = db.get_document_by_doi("10.1234/test")
        print(f"✓ Document retrieved: {doc['title']}")

        # Get statistics
        stats = db.get_statistics()
        print(f"\nDatabase statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
