#!/bin/bash
# Startup script for Research Paper Discovery System

echo "🚀 Starting Research Paper Discovery System..."
echo "📍 Running on port 8502 (to avoid conflict with other apps)"
echo "🌐 Open http://localhost:8502 in your browser"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Run Streamlit app
streamlit run app.py --server.port=8502
