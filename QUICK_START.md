# Quick Start Guide - Research Paper Discovery System

## 🚀 3-Minute Setup

### Option 1: Run Locally

```bash
# 1. Clone repository
git clone https://github.com/Nagavenkatasai7/Research-Paper-Discovery-System.git
cd Research-Paper-Discovery-System

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and add your GROK_API_KEY (required)
# Add SEMANTIC_SCHOLAR_API_KEY (highly recommended)

# 5. Run application
streamlit run app.py
```

**Access at:** http://localhost:8501

---

### Option 2: Deploy to Streamlit Cloud (Recommended)

**One-Click Deploy:**
[![Deploy to Streamlit Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=Nagavenkatasai7/Research-Paper-Discovery-System&branch=main&mainModule=app.py)

**After deployment:**
1. Go to Settings → Secrets in Streamlit Cloud dashboard
2. Add your API keys (see STREAMLIT_CLOUD_DEPLOYMENT.md for details)
3. Click Save and wait for app to restart

---

## 🔑 Get Your API Keys (5 minutes)

### Essential:
1. **Grok API** (Required): https://console.x.ai/
   - Sign up → Generate API key → Copy

### Recommended:
2. **Semantic Scholar** (300x faster searches): https://www.semanticscholar.org/product/api
   - Create account → Request API key → Verify email

### Optional:
3. **OpenAI** (For embeddings): https://platform.openai.com/api-keys

---

## ✅ Verify Installation

```bash
# Test imports
python3 -c "import app; import config; print('✅ All imports successful')"

# Start application
streamlit run app.py
```

**Test features:**
1. Search for "quantum computing"
2. Try multi-agent search
3. Upload a PDF for analysis
4. Chat with a paper

---

## 📚 Full Documentation

- **Deployment Guide:** See [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md)
- **Audit Report:** See audit report from pre-deployment check
- **Comprehensive Setup:** See [DEPLOYMENT_README.md](DEPLOYMENT_README.md)

---

## 🐛 Common Issues

**"ModuleNotFoundError"**
```bash
pip install -r requirements.txt --upgrade
```

**"API Key Not Found"**
- Make sure you edited .env file
- For Streamlit Cloud: Add keys in Settings → Secrets

**Application won't start**
- Check Python version: `python3 --version` (requires 3.11+)
- Verify all dependencies: `pip list`

---

## 🎯 What Works Without API Keys

✅ Basic UI navigation
✅ OpenAlex searches (no key needed)
✅ ArXiv searches
⚠️ Semantic Scholar (very slow without key)
❌ AI features (require GROK_API_KEY)
❌ Chat functionality (requires GROK_API_KEY)

---

**Need help?** Check the full deployment guide or open an issue on GitHub.
