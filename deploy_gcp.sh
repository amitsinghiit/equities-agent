#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Google Cloud Run Deployment Assistant            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Check for gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI (gcloud) is not installed.${NC}"
    echo ""
    echo -e "${YELLOW}Please install it first:${NC}"
    echo "1. Download: https://cloud.google.com/sdk/docs/install"
    echo "2. Initialize: gcloud init"
    echo ""
    echo "Once installed, run this script again!"
    exit 1
fi

# 2. Check for Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  No active Google Cloud project found.${NC}"
    echo "Please run 'gcloud init' or 'gcloud config set project YOUR_PROJECT_ID'"
    exit 1
fi

echo -e "${GREEN}✅ Using Project: ${PROJECT_ID}${NC}"
echo ""

# 3. Check for Gemini API Key
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GEMINI_API_KEY is not set in your environment.${NC}"
    read -p "Enter your Gemini API Key: " GEMINI_API_KEY
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${RED}❌ API Key is required.${NC}"
        exit 1
    fi
fi

# 4. Enable required services
echo -e "${YELLOW}🔄 Enabling Cloud Run and Container Registry APIs...${NC}"
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com
echo -e "${GREEN}✅ APIs enabled.${NC}"
echo ""

# 5. Deploy Backend
echo -e "${YELLOW}🚀 Deploying Backend... (This may take a few minutes)${NC}"
gcloud run deploy equities-backend \
    --source ./backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY="$GEMINI_API_KEY" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Backend deployment failed.${NC}"
    exit 1
fi

# Get Backend URL
BACKEND_URL=$(gcloud run services describe equities-backend --platform managed --region us-central1 --format 'value(status.url)')
echo -e "${GREEN}✅ Backend deployed at: ${BACKEND_URL}${NC}"
echo ""

# 6. Deploy Frontend
echo -e "${YELLOW}🚀 Deploying Frontend...${NC}"
gcloud run deploy equities-frontend \
    --source ./frontend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars BACKEND_URL="$BACKEND_URL" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Frontend deployment failed.${NC}"
    exit 1
fi

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe equities-frontend --platform managed --region us-central1 --format 'value(status.url)')

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 🎉 Deployment Successful!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📱 **App URL:** ${FRONTEND_URL}"
echo -e "⚙️  **Backend:** ${BACKEND_URL}"
echo ""
