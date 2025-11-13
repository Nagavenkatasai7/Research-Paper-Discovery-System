# Deployment Guide - Research Paper Discovery System

## Overview
This guide explains how to deploy the Research Paper Discovery System to Streamlit Cloud and configure it for production use.

## Prerequisites

1. GitHub account
2. Streamlit Cloud account (sign up at https://streamlit.io/cloud)
3. Required API Keys:
   - Grok API Key (Required for LLM features)
   - Semantic Scholar API Key (Optional but recommended)
   - OpenAI API Key (Optional for embeddings)

## Deployment Steps

### 1. Push to GitHub

This repository is already configured for deployment. The following files are properly set up:

- `requirements.txt` - All dependencies with pinned versions
- `.gitignore` - Excludes sensitive files (.env, secrets.toml, etc.)
- `.streamlit/secrets.toml.example` - Template for API keys

Make sure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 2. Configure Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your GitHub repository: `Nagavenkatasai7/Research-Paper-Discovery-System`
4. Set the main file path: `app.py`
5. Click "Advanced settings"

### 3. Configure Secrets

In the Streamlit Cloud dashboard, go to Settings > Secrets and add:

```toml
# Grok API Key (Required for LLM features)
GROK_API_KEY = "your_grok_api_key_here"

# Semantic Scholar API Key (Get from: https://www.semanticscholar.org/product/api)
SEMANTIC_SCHOLAR_API_KEY = "your_semantic_scholar_api_key_here"
S2_API_KEY = "your_semantic_scholar_api_key_here"

# Optional: OpenAI API Key (for embeddings and alternative LLM features)
OPENAI_API_KEY = "your_openai_api_key_here"

# Optional: Email for OpenAlex polite pool (better rate limits)
OPENALEX_EMAIL = "your.email@example.com"
```

### 4. Deploy

Click "Deploy" and wait for the build to complete. This may take 5-10 minutes on first deployment.

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/Nagavenkatasai7/Research-Paper-Discovery-System.git
cd "Research Paper Discovery System"
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Secrets

Copy the example secrets file and add your API keys:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and add your API keys.

### 5. Run Locally

```bash
streamlit run app.py
```

The app will be available at http://localhost:8501

## Environment Variables

The application uses the following environment variables (configured via .streamlit/secrets.toml or environment):

| Variable | Required | Description |
|----------|----------|-------------|
| `GROK_API_KEY` | Yes | API key for Grok LLM features |
| `SEMANTIC_SCHOLAR_API_KEY` | No | Semantic Scholar API for paper search |
| `S2_API_KEY` | No | Alternative name for Semantic Scholar API |
| `OPENAI_API_KEY` | No | OpenAI API for embeddings |
| `OPENALEX_EMAIL` | No | Email for OpenAlex API polite pool |

## Features

### Core Features
- Google-like search interface for academic papers
- Multi-source paper search (arXiv, Semantic Scholar, etc.)
- Quality scoring and filtering
- BibTeX generation
- Paper analysis and summarization

### Document Analysis
- 11-agent comprehensive analysis system
- PDF upload and processing
- Detailed multi-paragraph reports
- PDF report generation and download

### RAG System
- Vector-based document storage
- Contextual chat with papers
- Advanced retrieval algorithms

### Multi-Agent Search
- Specialized agents for different search tasks
- Parallel processing
- Enhanced result quality

## Troubleshooting

### Build Fails on Streamlit Cloud

1. Check that all dependencies in `requirements.txt` are compatible
2. Verify Python version compatibility (3.8-3.11 recommended)
3. Check the build logs for specific error messages

### Missing API Keys Error

Make sure all required secrets are configured in Streamlit Cloud Settings > Secrets.

### Slow Performance

- The first run may be slow as models download and cache
- Subsequent runs will be faster
- Consider upgrading to Streamlit Cloud Pro for better performance

### PDF Generation Issues

If PDF generation fails:
1. Check that fpdf2 is properly installed
2. Verify file permissions for temporary files
3. Check available disk space

## File Structure

```
Research Paper Discovery System/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
├── .streamlit/
│   ├── config.toml           # Streamlit configuration
│   ├── secrets.toml          # API keys (not in git)
│   └── secrets.toml.example  # Template for secrets
├── pages/                     # Multi-page app pages
│   ├── Chat_With_Paper.py
│   ├── Document_Analysis.py
│   └── Multi_Agent_Search.py
├── rag_system/               # RAG and analysis system
│   ├── analysis_agents/      # 11 specialized agents
│   ├── pdf_processor.py
│   ├── rag_engine.py
│   └── database.py
├── report_utils/             # PDF report generation
│   ├── report_generator.py
│   └── __init__.py
└── [other modules]
```

## Security Notes

- Never commit `.env` or `.streamlit/secrets.toml` files
- API keys are loaded from environment variables or Streamlit secrets
- Sensitive files are excluded via `.gitignore`
- Use Streamlit Cloud secrets management for production

## Support

For issues or questions:
- GitHub Issues: https://github.com/Nagavenkatasai7/Research-Paper-Discovery-System/issues
- Check existing documentation files in the repository

## License

[Add your license here]

---

Last Updated: November 12, 2025
