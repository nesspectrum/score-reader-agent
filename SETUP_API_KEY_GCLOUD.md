# Getting Google API Key Using gcloud CLI

## Important: Two Different APIs

Your application can use either:
1. **Gemini API** (`google.generativeai`) - Requires API key from Google AI Studio
2. **Vertex AI** (`google.cloud.aiplatform`) - Uses gcloud authentication

## Option 1: Vertex AI with gcloud (Recommended for GCP Projects)

If you want to use Vertex AI with gcloud authentication:

### Step 1: Install and Authenticate gcloud

```bash
# Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### Step 2: Enable Required APIs

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Generative AI API (if needed)
gcloud services enable generativelanguage.googleapis.com
```

### Step 3: Set Up Application Default Credentials (ADC)

```bash
# Set up ADC for local development
gcloud auth application-default login

# This will:
# 1. Open browser for authentication
# 2. Store credentials in ~/.config/gcloud/application_default_credentials.json
```

### Step 4: Verify Setup

```bash
# Check current project
gcloud config get-value project

# List enabled APIs
gcloud services list --enabled | grep -E "(aiplatform|generative)"
```

### Step 5: Update Your Code

If using Vertex AI, you need to modify `extraction_agent.py` to use Vertex AI instead:

```python
from google.cloud import aiplatform

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)

# Use Vertex AI models instead of generativeai
```

## Option 2: Create API Key via gcloud (For Gemini API)

For Gemini API, you still need to get the key from Google AI Studio, but you can manage it via gcloud:

### Step 1: Create API Key Using gcloud

```bash
# List existing API keys
gcloud alpha services api-keys list

# Create a new API key for Generative AI API
gcloud alpha services api-keys create \
    --display-name="Gemini API Key" \
    --api-target=service=generativelanguage.googleapis.com

# This will output the key - save it!
```

### Step 2: Restrict the API Key (Recommended)

```bash
# Get the key name from previous step
API_KEY_NAME="projects/YOUR_PROJECT/locations/global/keys/KEY_ID"

# Restrict to Generative AI API only
gcloud alpha services api-keys update $API_KEY_NAME \
    --api-targets=service=generativelanguage.googleapis.com

# Restrict to specific IPs (optional)
gcloud alpha services api-keys update $API_KEY_NAME \
    --allowed-ips=YOUR_IP_ADDRESS
```

### Step 3: Add to .env

```bash
# Get the key string
gcloud alpha services api-keys get-key-string $API_KEY_NAME

# Add to .env
echo "GOOGLE_API_KEY=$(gcloud alpha services api-keys get-key-string $API_KEY_NAME --format='value(keyString)')" >> .env
```

## Option 3: Service Account (For Production/CI/CD)

For production environments or CI/CD:

### Step 1: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create sheet-reader-agent \
    --display-name="Sheet Reader Agent Service Account"

# Get the email
SA_EMAIL=$(gcloud iam service-accounts list \
    --filter="displayName:Sheet Reader Agent" \
    --format="value(email)")
```

### Step 2: Grant Permissions

```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user"

# Or for Generative AI API
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/ml.developer"
```

### Step 3: Create and Download Key

```bash
# Create key file
gcloud iam service-accounts keys create key.json \
    --iam-account=$SA_EMAIL

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
```

## Quick Setup Script

Create a script to automate setup:

```bash
#!/bin/bash
# setup_gcloud.sh

PROJECT_ID=$(gcloud config get-value project)

echo "Setting up Google Cloud for Sheet Reader Agent..."
echo "Project: $PROJECT_ID"

# Enable APIs
echo "Enabling APIs..."
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com

# Set up ADC
echo "Setting up Application Default Credentials..."
gcloud auth application-default login

echo "✅ Setup complete!"
echo "You can now use Vertex AI with ADC, or create an API key for Gemini API"
```

## Verify Your Setup

```bash
# Check authentication
gcloud auth list

# Check ADC
gcloud auth application-default print-access-token

# Test Vertex AI access
python3 -c "
from google.cloud import aiplatform
aiplatform.init(project='$PROJECT_ID', location='us-central1')
print('✅ Vertex AI initialized successfully')
"
```

## Current Application Status

Your current code uses `google.generativeai`, which requires:
- **API Key from Google AI Studio** (simplest)
- OR **API Key created via gcloud** (Option 2 above)

To use Vertex AI instead (which works better with gcloud), you would need to modify the code to use `google.cloud.aiplatform`.

## Recommendation

For your current setup:
1. **Quickest**: Get API key from https://aistudio.google.com/app/apikey
2. **gcloud way**: Use Option 2 above to create API key via gcloud
3. **Production**: Use Option 3 (Service Account) with Vertex AI


