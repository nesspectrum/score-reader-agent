# Environment Setup Guide

This guide explains how to set up the environment variables needed for the sheet-reader-agent project.

## Required Environment Variables

### 1. Google Cloud Project Configuration

```bash
# Your Google Cloud Project ID
GOOGLE_CLOUD_PROJECT=kaggle-capstone-112025

# Google Cloud Location (default: us-central1)
GOOGLE_CLOUD_LOCATION=us-central1

# Optional: Model name (default: gemini-2.5-flash-lite)
GOOGLE_CLOUD_MODEL=gemini-2.5-flash-lite
```

### 2. Authentication Options

You have two options for authentication:

#### Option A: Application Default Credentials (Recommended)

This uses `gcloud` authentication and is recommended for local development:

```bash
# Authenticate with gcloud
gcloud auth login

# Set your project
gcloud config set project kaggle-capstone-112025

# Set up Application Default Credentials
gcloud auth application-default login
```

No additional environment variables needed - the code will automatically use ADC.

#### Option B: Service Account Key File

For production or CI/CD environments:

```bash
# Path to your service account JSON key file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json
```

## Setup Steps

### Step 1: Create `.env` File

Create a `.env` file in the project root:

```bash
cd /home/ness/nesspectrum/codes/gc/sheet-reader-agent
touch .env
```

### Step 2: Add Environment Variables

Edit the `.env` file and add:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=kaggle-capstone-112025
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_MODEL=gemini-2.5-flash-lite

# Optional: If using service account instead of ADC
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Step 3: Enable Required APIs

Make sure the following APIs are enabled in your Google Cloud project:

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=kaggle-capstone-112025

# Enable Generative AI API
gcloud services enable generativelanguage.googleapis.com --project=kaggle-capstone-112025

# Enable Discovery Engine API (for PDMX search)
gcloud services enable discoveryengine.googleapis.com --project=kaggle-capstone-112025

# Enable Cloud Storage API (for PDMX datastore)
gcloud services enable storage.googleapis.com --project=kaggle-capstone-112025
```

### Step 4: Verify Setup

Test your environment setup:

```bash
# Check if environment variables are loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))"

# Verify gcloud authentication
gcloud auth list

# Verify Application Default Credentials
gcloud auth application-default print-access-token
```

## Quick Setup Script

You can use this script to set up everything:

```bash
#!/bin/bash
# Run this from the project root

PROJECT_ID="kaggle-capstone-112025"
LOCATION="us-central1"

echo "Setting up environment for sheet-reader-agent..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_LOCATION=$LOCATION
GOOGLE_CLOUD_MODEL=gemini-2.5-flash-lite
EOF
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

# Set gcloud project
echo "Setting gcloud project..."
gcloud config set project $PROJECT_ID

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
gcloud services enable generativelanguage.googleapis.com --project=$PROJECT_ID
gcloud services enable discoveryengine.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID

# Set up Application Default Credentials
echo "Setting up Application Default Credentials..."
gcloud auth application-default login

echo ""
echo "✅ Setup complete!"
echo ""
echo "Environment variables:"
cat .env
echo ""
echo "Next steps:"
echo "1. Verify APIs are enabled: gcloud services list --enabled"
echo "2. Test the setup by running: python examples/pdmx_search_example.py"
```

## Troubleshooting

### Error: "GOOGLE_CLOUD_PROJECT not set"

Make sure your `.env` file exists and contains `GOOGLE_CLOUD_PROJECT`. The code uses `python-dotenv` to load it automatically.

### Error: "Authentication failed"

1. Run `gcloud auth application-default login` again
2. Check that your project ID is correct: `gcloud config get-value project`
3. Verify APIs are enabled: `gcloud services list --enabled`

### Error: "API not enabled"

Enable the required APIs:
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable discoveryengine.googleapis.com
gcloud services enable storage.googleapis.com
```

### Error: "Permission denied"

Make sure your account has the necessary roles:
```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding kaggle-capstone-112025 \
    --member="user:$(gcloud config get-value account)" \
    --role="roles/aiplatform.user"

# Grant Storage Admin role (for PDMX datastore)
gcloud projects add-iam-policy-binding kaggle-capstone-112025 \
    --member="user:$(gcloud config get-value account)" \
    --role="roles/storage.admin"
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Yes | - | Your Google Cloud Project ID |
| `GOOGLE_CLOUD_LOCATION` | No | `us-central1` | GCP region for Vertex AI |
| `GOOGLE_CLOUD_MODEL` | No | `gemini-2.5-flash-lite` | Model name to use |
| `GOOGLE_APPLICATION_CREDENTIALS` | No* | - | Path to service account key (if not using ADC) |

*Required if not using Application Default Credentials

## Testing Your Setup

After setup, test with:

```bash
# Test PDMX search example
python examples/pdmx_search_example.py

# Test main extraction
python main.py path/to/music_sheet.pdf
```

