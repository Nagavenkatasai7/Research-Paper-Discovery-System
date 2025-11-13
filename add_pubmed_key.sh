#!/bin/bash
# Helper script to add PubMed API key

echo "======================================================================"
echo "PubMed API Key Configuration"
echo "======================================================================"
echo ""
echo "Current email configured: chennunagavenkatasai@gmail.com"
echo ""
echo "Please paste your PubMed API key (from NCBI Account Settings):"
read -p "API Key: " api_key

if [ -z "$api_key" ]; then
    echo "❌ No API key provided"
    exit 1
fi

# Add to secrets file
cd "/Users/nagavenkatasaichennu/Desktop/Research Paper Discovery System"

# Remove the commented line and add the real key
sed -i '' '/# PUBMED_API_KEY/d' .streamlit/secrets.toml
echo "PUBMED_API_KEY = \"$api_key\"" >> .streamlit/secrets.toml

echo ""
echo "✅ PubMed API key added successfully!"
echo ""
echo "Testing PubMed agent..."

# Test PubMed
python3 << 'PYTEST'
try:
    from extended_api_clients import PubMedClient
    import sys

    client = PubMedClient("chennunagavenkatasai@gmail.com", open('.streamlit/secrets.toml').read().split('PUBMED_API_KEY = "')[1].split('"')[0])
    results = client.search_papers("cancer research", max_results=3)

    print(f"✅ PubMed agent working! Found {len(results)} papers")
    print("\nSample result:")
    if results:
        print(f"   Title: {results[0].get('title', 'N/A')[:70]}...")
        print(f"   Year: {results[0].get('year', 'N/A')}")

except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
PYTEST

echo ""
echo "======================================================================"
echo "Next steps:"
echo "1. Restart your Streamlit app"
echo "2. Run: python test_6_agents_quick.py"
echo "======================================================================"
