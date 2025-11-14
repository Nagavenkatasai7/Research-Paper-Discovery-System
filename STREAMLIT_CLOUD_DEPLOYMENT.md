# Streamlit Cloud Deployment Guide

## 🚀 Quick Start Deployment

This guide will help you deploy the Research Paper Discovery System to Streamlit Cloud.

---

## 📋 Prerequisites

- GitHub account with access to this repository
- Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
- API keys for the services you want to use

---

## 🔑 Required API Keys

### Essential (Required for Core Features):
- **GROK_API_KEY** - Get from [console.x.ai](https://console.x.ai/)
  - Required for: AI-powered analysis, query enhancement, chat features
  - Without this: Most AI features will not work

### Highly Recommended:
- **SEMANTIC_SCHOLAR_API_KEY** - Get from [Semantic Scholar API](https://www.semanticscholar.org/product/api)
  - Without key: 100 requests per 5 minutes (VERY SLOW)
  - With key: 1 request per second (300x FASTER)
  - Get yours at: https://www.semanticscholar.org/product/api#api-key

### Optional (Improves Functionality):
- **OPENAI_API_KEY** - For embeddings and alternative LLM features
- **CORE_API_KEY** - For CORE academic database access
- **PUBMED_API_KEY** - For faster PubMed access
- **EMAIL** - Your email for OpenAlex polite pool (better rate limits)

---

## 📦 Step 1: Verify Repository is Ready

The repository includes all necessary deployment files:
- ✅ `requirements.txt` - Python dependencies (UPDATED with all fixes)
- ✅ `runtime.txt` - Python version specification (3.11)
- ✅ `packages.txt` - System-level packages (chromium for Selenium)
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `.streamlit/secrets.toml.example` - Template for secrets

---

## 🌐 Step 2: Deploy to Streamlit Cloud

### Method 1: Deploy from Streamlit Cloud Dashboard

1. **Go to [share.streamlit.io](https://share.streamlit.io)**
   - Sign in with your GitHub account

2. **Click "New app"**

3. **Fill in deployment details:**
   - **Repository:** `Nagavenkatasai7/Research-Paper-Discovery-System`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** Choose a custom URL (e.g., `research-paper-discovery`)

4. **Click "Deploy!"**
   - Initial deployment will take 5-10 minutes

### Method 2: Deploy via URL

Direct link (customize with your details):
```
https://share.streamlit.io/deploy?repository=Nagavenkatasai7/Research-Paper-Discovery-System&branch=main&mainModule=app.py
```

---

## 🔐 Step 3: Configure Secrets (CRITICAL)

After deployment starts, you MUST configure API keys:

1. **In Streamlit Cloud Dashboard:**
   - Click on your deployed app
   - Go to **Settings** → **Secrets**

2. **Add the following secrets** (copy this template):

```toml
# Required for AI features
GROK_API_KEY = "your_actual_grok_api_key_here"

# Highly recommended for better performance
SEMANTIC_SCHOLAR_API_KEY = "your_actual_semantic_scholar_api_key_here"
S2_API_KEY = "your_actual_semantic_scholar_api_key_here"

# Optional but recommended
OPENAI_API_KEY = "your_openai_api_key_here"
OPENALEX_EMAIL = "your.email@example.com"

# Optional API keys
CORE_API_KEY = "your_core_api_key_here"
PUBMED_API_KEY = "your_pubmed_api_key_here"
```

3. **Click "Save"**
   - The app will automatically restart with new secrets

---

## 🎯 Step 4: Verify Deployment

### Check Application Status:
1. Wait for deployment to complete (green checkmark)
2. Click "View app" to open your deployed application
3. Test basic functionality:
   - ✅ Homepage loads
   - ✅ Search functionality works
   - ✅ Multi-Agent Search page accessible
   - ✅ Document Analysis page works
   - ✅ Chat With Paper feature loads

### Verify API Key Configuration:
1. Try a search query to test Semantic Scholar integration
2. Test AI features (query enhancement, summarization)
3. Check browser console (F12) for any errors

---

## 🐛 Troubleshooting

### Common Issues:

#### 1. **"ModuleNotFoundError"**
- **Cause:** Missing dependency in requirements.txt
- **Solution:** requirements.txt has been updated with all dependencies
- If still occurs, check Streamlit Cloud logs for the specific module

#### 2. **"API Key Not Found" or Features Not Working**
- **Cause:** Secrets not configured in Streamlit Cloud
- **Solution:**
  1. Go to Settings → Secrets in Streamlit Cloud dashboard
  2. Add all required API keys
  3. Click Save (app will restart automatically)

#### 3. **"Package Installation Failed"**
- **Cause:** System package (chromium) installation issues
- **Solution:**
  - packages.txt includes chromium and chromium-driver
  - If fails, remove Selenium-dependent features or update packages.txt

#### 4. **"Application Error" on Startup**
- **Cause:** Python version incompatibility
- **Solution:**
  - runtime.txt specifies python-3.11
  - Ensure this matches requirements.txt specifications
  - Check Streamlit Cloud logs for detailed error

#### 5. **Slow Search Performance**
- **Cause:** Missing SEMANTIC_SCHOLAR_API_KEY
- **Solution:** Add Semantic Scholar API key to secrets
- Performance improvement: 300x faster (1 req/sec vs 100 req/5min)

---

## 📊 Monitoring and Logs

### View Application Logs:
1. In Streamlit Cloud dashboard, click on your app
2. Go to **Manage app** → **Logs**
3. Monitor for errors or warnings

### Check Resource Usage:
- Streamlit Cloud free tier: 1 GB RAM
- If hitting limits, consider:
  - Optimizing FAISS index size
  - Reducing concurrent multi-agent searches
  - Implementing pagination more aggressively

---

## 🔄 Updating the Deployment

### Automatic Deployments:
- Any push to `main` branch triggers automatic redeployment
- Changes typically take 2-3 minutes to go live

### Manual Redeployment:
1. Go to Streamlit Cloud dashboard
2. Click **Reboot app** to restart with latest code

### Rolling Back:
1. In GitHub, revert the problematic commit
2. Push to main branch
3. Wait for automatic redeployment

---

## ⚙️ Advanced Configuration

### Custom Domain:
1. In Streamlit Cloud dashboard: Settings → General
2. Add your custom domain
3. Configure DNS CNAME record pointing to Streamlit

### Resource Optimization:
- Reduce `MULTI_AGENT_CONFIG['max_workers']` in config.py for lower memory usage
- Adjust `results_per_source` to reduce API calls
- Enable caching more aggressively

### Analytics:
- Streamlit Cloud provides basic analytics
- For advanced tracking, integrate Google Analytics or Plausible

---

## 📝 Environment Variables Reference

All configuration is in `config.py` and can be overridden via Streamlit secrets:

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GROK_API_KEY` | ✅ Yes | None | AI features, chat, analysis |
| `SEMANTIC_SCHOLAR_API_KEY` | ⚠️ Recommended | None | Paper search (300x faster) |
| `OPENAI_API_KEY` | ❌ Optional | None | Embeddings, alternative LLM |
| `CORE_API_KEY` | ❌ Optional | None | CORE database access |
| `PUBMED_API_KEY` | ❌ Optional | None | PubMed access |
| `EMAIL` | ⚠️ Recommended | None | OpenAlex polite pool |

---

## 🎉 Success Checklist

- [ ] Repository deployed to Streamlit Cloud
- [ ] Application loads without errors
- [ ] API keys configured in Secrets
- [ ] Search functionality works
- [ ] Multi-agent search returns results
- [ ] Document analysis page functional
- [ ] Chat features work (with GROK_API_KEY)
- [ ] No errors in logs
- [ ] Performance acceptable (with SEMANTIC_SCHOLAR_API_KEY)

---

## 📞 Support

### Issues with Deployment:
- Check Streamlit Cloud status: [status.streamlit.io](https://status.streamlit.io)
- Streamlit Community: [discuss.streamlit.io](https://discuss.streamlit.io)

### Issues with Application:
- Check GitHub Issues: [Repository Issues](https://github.com/Nagavenkatasai7/Research-Paper-Discovery-System/issues)
- Review audit report: See COMPREHENSIVE_AUDIT_SUMMARY.md

---

## 🔒 Security Notes

1. **Never commit API keys to GitHub**
   - Always use Streamlit Cloud Secrets
   - .env and secrets.toml are gitignored

2. **API Key Rotation**
   - Regularly rotate API keys
   - Update in Streamlit Cloud Secrets only

3. **Rate Limiting**
   - Application implements rate limiting for APIs
   - Monitor usage to avoid hitting limits

4. **Data Privacy**
   - No user data is stored persistently
   - Cached results are temporary and in-memory
   - PDFs are stored locally in embeddings/ directory (not persistent on Streamlit Cloud)

---

## 📈 Post-Deployment Optimization

### Week 1: Monitor and Stabilize
- Watch logs for errors
- Monitor API usage and costs
- Collect user feedback

### Week 2: Optimize Performance
- Fine-tune cache TTL values
- Adjust multi-agent worker count
- Optimize FAISS index parameters

### Week 3: Enhance Features
- Add requested features from users
- Improve error handling
- Enhance UI/UX based on feedback

---

**🎊 Your Research Paper Discovery System is now live on Streamlit Cloud!**

Share your deployment: `https://your-app-name.streamlit.app`
