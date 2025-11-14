"""
Configuration settings for Research Paper Discovery System
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Helper function to get secrets from both Streamlit Cloud and .env
def get_secret(key: str, default: str = '') -> str:
    """Get secret from Streamlit secrets or environment variable"""
    try:
        import streamlit as st
        # Try Streamlit secrets first (for Streamlit Cloud)
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    # Fall back to environment variable (for local development)
    return os.getenv(key, default)

# Semantic Scholar API Key (FREE - Get yours at: https://www.semanticscholar.org/product/api#api-key)
# Without API key: 100 requests per 5 minutes (VERY SLOW!)
# With API key: 1 request per second (300x FASTER!)
SEMANTIC_SCHOLAR_API_KEY = get_secret('SEMANTIC_SCHOLAR_API_KEY', '')

# API Rate Limits (seconds between requests)
RATE_LIMITS = {
    'arxiv': 3.0,  # ArXiv requires 3 seconds between requests
    'semantic_scholar': 1.0,  # With API key: 1 request/second
    'openalex': 0.1,  # Polite pool: ~10 requests/second
    'papers_with_code': 1.0
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    'search_results': 600,  # 10 minutes
    'paper_details': 3600,  # 1 hour
    'author_info': 7200,  # 2 hours
    'venue_rankings': 86400  # 24 hours
}

# Pagination
RESULTS_PER_PAGE = 10
MAX_RESULTS_PER_API = 50

# LLM Settings - Ollama REMOVED, using only Grok-4
LLM_SETTINGS = {
    'enabled': False,  # Disabled - now using only Grok-4 for all AI features
    'default_model': None,  # Ollama removed
    'available_models': [],  # Ollama removed
    'embedding_model': None,  # Ollama removed
    'features': {
        'summarization': False,  # Now handled by Grok-4
        'insights_extraction': False,  # Now handled by Grok-4
        'qa': False,  # Now handled by Grok-4
        'query_enhancement': False,  # Now handled by Grok-4
        'semantic_search': False  # Disabled (requires embeddings)
    },
    'cache_ttl': {
        'summaries': 7200,  # 2 hours
        'insights': 7200,   # 2 hours
        'queries': 1800,    # 30 minutes
        'embeddings': 86400 # 24 hours
    }
}

# Grok API Settings (xAI) - PRIMARY AND ONLY LLM
GROK_SETTINGS = {
    'enabled': True,  # ✅ ONLY LLM in use (Ollama removed)
    'api_key': get_secret('GROK_API_KEY', ''),
    'model': 'grok-4-fast-reasoning',
    'available_models': [
        'grok-4-fast-reasoning',
        'grok-4',
        'grok-3'
    ],
    'use_for_everything': True,  # All AI features now use Grok-4 exclusively
    'timeout': 30,
    'max_tokens': 1000,
    'temperature': 0.7,
    'features': {
        'query_enhancement': True,
        'paper_summarization': True,
        'insights_extraction': True,
        'multi_agent_orchestration': True,
        'search_planning': True
    }
}

# Streamlit Server Configuration
STREAMLIT_PORT = 8502  # Use 8502 instead of default 8501

# Quality Scoring Weights
QUALITY_WEIGHTS = {
    'citations': 0.40,
    'author_reputation': 0.25,
    'venue_quality': 0.20,
    'recency': 0.10,
    'additional_signals': 0.05
}

# Venue Rankings (Tier 1 = 1.0, Tier 2 = 0.7, arXiv = 0.3)
TIER_1_VENUES = {
    'NeurIPS', 'ICML', 'ICLR', 'ACL', 'EMNLP', 'NAACL',
    'CVPR', 'ICCV', 'ECCV', 'SIGIR', 'WWW', 'KDD',
    'Nature', 'Science', 'PNAS', 'Cell'
}

TIER_2_VENUES = {
    'AAAI', 'IJCAI', 'WSDM', 'RecSys', 'CIKM',
    'COLING', 'EACL', 'CoNLL', 'SIGCHI', 'UIST'
}

# Top Research Institutions
TOP_INSTITUTIONS = {
    'Stanford', 'MIT', 'CMU', 'Berkeley', 'Oxford', 'Cambridge',
    'Harvard', 'Princeton', 'Yale', 'ETH Zurich', 'Imperial College',
    'Google', 'DeepMind', 'OpenAI', 'Anthropic', 'Meta AI',
    'Microsoft Research', 'IBM Research', 'Allen Institute'
}

# Age-adjusted citation thresholds
CITATION_THRESHOLDS = {
    1: 5,      # 0-1 years
    2: 15,     # 1-2 years
    3: 30,     # 2-3 years
    5: 50,     # 3-5 years
    10: 100,   # 5-10 years
    100: 200   # 10+ years (classics)
}

# Research Domains and Keywords
DOMAIN_KEYWORDS = {
    'LLMs': [
        'large language model', 'GPT', 'BERT', 'transformer',
        'language model', 'natural language processing', 'NLP',
        'text generation', 'language understanding', 'prompt engineering',
        'in-context learning', 'few-shot learning', 'instruction tuning',
        'RLHF', 'chain of thought', 'reasoning'
    ],
    'AI Agents': [
        'autonomous agent', 'AI agent', 'multi-agent', 'agent system',
        'ReAct', 'tool use', 'planning', 'reasoning and acting',
        'agent architecture', 'agent framework', 'AutoGPT',
        'LangChain', 'agent coordination', 'task planning'
    ],
    'Quantum Computing': [
        'quantum computing', 'quantum machine learning', 'QML',
        'quantum neural network', 'quantum algorithm', 'NISQ',
        'quantum supremacy', 'quantum annealing', 'variational quantum',
        'quantum circuit', 'qubit', 'quantum entanglement'
    ],
    'Computer Vision': [
        'computer vision', 'image recognition', 'object detection',
        'image segmentation', 'visual understanding', 'CNN',
        'vision transformer', 'ViT', 'image generation', 'diffusion model'
    ],
    'Reinforcement Learning': [
        'reinforcement learning', 'RL', 'deep RL', 'Q-learning',
        'policy gradient', 'actor-critic', 'RLHF', 'reward modeling'
    ]
}

# ArXiv Categories
ARXIV_CATEGORIES = {
    'cs.CL': 'Computation and Language (NLP/LLMs)',
    'cs.AI': 'Artificial Intelligence',
    'cs.LG': 'Machine Learning',
    'cs.CV': 'Computer Vision',
    'cs.RO': 'Robotics',
    'quant-ph': 'Quantum Physics',
    'stat.ML': 'Machine Learning (Statistics)'
}

# Known Research Blogs and Sources
TRUSTED_BLOG_SOURCES = {
    'arxiv.org',
    'openai.com/blog',
    'anthropic.com/research',
    'deepmind.google/blog',
    'ai.googleblog.com',
    'research.google/blog',
    'ai.meta.com/blog',
    'microsoft.com/en-us/research/blog',
    'distill.pub',
    'thegradient.pub',
    'towardsdatascience.com',
    'blog.research.google',
    'huggingface.co/blog',
    'lilianweng.github.io',
    'karpathy.github.io',
    'jalammar.github.io',
    'sebastianraschka.com/blog',
    'colah.github.io'
}

# Multi-Agent System Configuration
MULTI_AGENT_CONFIG = {
    'enabled': True,
    'default_sources': [
        'semantic_scholar',  # 200M+ papers, rich metadata
        'arxiv',            # Preprints, CS/Physics/Math
        'openalex',         # 240M+ papers, completely free
        'crossref',         # 150M+ DOI records
        'core',             # Open access focus (requires API key)
        'pubmed'            # Biomedical (requires email)
    ],
    'all_sources': [
        'semantic_scholar',  # 200M+ papers, rich metadata
        'arxiv',            # Preprints, CS/Physics/Math
        'openalex',         # 240M+ papers, completely free
        'crossref',         # 150M+ DOI records
        'core',             # Open access focus (requires API key)
        'pubmed'            # Biomedical (requires email)
    ],
    'source_descriptions': {
        'semantic_scholar': 'Rich metadata, citations, h-index (200M+ papers)',
        'arxiv': 'Latest preprints in CS, AI, Physics, Math',
        'openalex': 'Largest coverage, 240M+ papers, completely free',
        'crossref': 'DOI metadata, 150M+ records',
        'core': 'Open access focus, full-text available',
        'pubmed': 'Biomedical and life sciences (35M+ papers)'
    },
    'parallel_execution': True,
    'max_workers': 6,  # Use ALL 6 workers for comprehensive results from all sources
    'timeout_per_source': 15,  # Reduced from 30 to 15 seconds - fail fast
    'enable_llm_planning': True,
    'enable_synthesis': True,
    'results_per_source': 20,  # Reduced from 50 to 20 - 40% speed improvement
    'retry_attempts': 3,  # Number of retry attempts for failed requests
    'use_exponential_backoff': True,  # Enable smart retry logic
    'enable_progressive_loading': False,  # Can be enabled for streaming results
    'cache_ttl': 1800,  # Cache results for 30 minutes
    'smart_source_selection': False  # DISABLED - use ALL sources for comprehensive results
}
