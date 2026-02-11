#!/bin/bash
# Setup script for Google Cloud authentication

set -e

echo "=========================================="
echo "Google Cloud Setup for Score Reader Agent"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
    echo "⚠️  No project set. Please set one:"
    echo "   gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project: $PROJECT_ID"
echo ""

# Enable APIs
echo "🔧 Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable generativelanguage.googleapis.com --project=$PROJECT_ID
echo "✅ APIs enabled"
echo ""

# Set up Application Default Credentials
echo "🔐 Setting up Application Default Credentials..."
echo "   (This will open your browser for authentication)"
gcloud auth application-default login
echo "✅ ADC configured"
echo ""

# Option: Create API Key
read -p "Do you want to create an API key for Gemini API? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔑 Creating API key..."
    KEY_NAME="score-reader-agent-$(date +%s)"
    
    # Create API key
    gcloud alpha services api-keys create \
        --display-name="$KEY_NAME" \
        --api-target=service=generativelanguage.googleapis.com \
        --project=$PROJECT_ID
    
    echo ""
    echo "✅ API key created: $KEY_NAME"
    echo ""
    echo "To get the key string, run:"
    echo "  gcloud alpha services api-keys list --filter=\"displayName:$KEY_NAME\""
    echo ""
    echo "Then add it to your .env file:"
    echo "  GOOGLE_API_KEY=<key-string>"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If using Vertex AI: Your code should work with ADC"
echo "2. If using Gemini API: Add GOOGLE_API_KEY to .env file"
echo "3. Test with: python3 check_api_key.py"


