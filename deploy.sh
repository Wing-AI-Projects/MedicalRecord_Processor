#!/bin/bash

# Medical Record Processor - Vercel Deployment Script
# This script helps deploy the application to Vercel

set -e  # Exit on error

echo "========================================="
echo "Medical Record Processor - Vercel Deploy"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Vercel CLI is available
if ! command -v vercel &> /dev/null && ! command -v npx &> /dev/null; then
    echo -e "${RED}Error: Neither 'vercel' nor 'npx' found.${NC}"
    echo "Please install Node.js and npm first:"
    echo "  https://nodejs.org/"
    exit 1
fi

# Determine which command to use
if command -v vercel &> /dev/null; then
    VERCEL_CMD="vercel"
else
    VERCEL_CMD="npx vercel"
fi

echo -e "${GREEN}Using command: $VERCEL_CMD${NC}"
echo ""

# Check if user is logged in
echo "Checking Vercel authentication..."
if ! $VERCEL_CMD whoami &> /dev/null; then
    echo -e "${YELLOW}You are not logged in to Vercel.${NC}"
    echo "Please login to continue..."
    $VERCEL_CMD login
fi

echo -e "${GREEN}✓ Authenticated with Vercel${NC}"
echo ""

# Check for environment variables
echo "Checking environment variables..."
ENV_VARS_SET=true

if ! $VERCEL_CMD env ls | grep -q "ANTHROPIC_API_KEY"; then
    echo -e "${YELLOW}⚠ ANTHROPIC_API_KEY not set${NC}"
    ENV_VARS_SET=false
fi

if ! $VERCEL_CMD env ls | grep -q "CLAUDE_MODEL"; then
    echo -e "${YELLOW}⚠ CLAUDE_MODEL not set${NC}"
    ENV_VARS_SET=false
fi

if [ "$ENV_VARS_SET" = false ]; then
    echo ""
    echo -e "${YELLOW}Required environment variables are missing.${NC}"
    echo "Would you like to set them now? (y/n)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Setting ANTHROPIC_API_KEY..."
        echo "Please enter your Anthropic API key:"
        read -r -s API_KEY
        echo "$API_KEY" | $VERCEL_CMD env add ANTHROPIC_API_KEY production preview development

        echo ""
        echo "Setting CLAUDE_MODEL..."
        echo "claude-sonnet-4-5" | $VERCEL_CMD env add CLAUDE_MODEL production preview development

        echo -e "${GREEN}✓ Environment variables set${NC}"
    else
        echo ""
        echo "Please set environment variables manually:"
        echo "  $VERCEL_CMD env add ANTHROPIC_API_KEY"
        echo "  $VERCEL_CMD env add CLAUDE_MODEL"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
fi

echo ""
echo "========================================="
echo "Ready to deploy!"
echo "========================================="
echo ""
echo "Deployment options:"
echo "  1. Deploy to production (recommended)"
echo "  2. Deploy to preview"
echo "  3. Cancel"
echo ""
echo -n "Choose an option (1-3): "
read -r choice

case $choice in
    1)
        echo ""
        echo "Deploying to production..."
        $VERCEL_CMD --prod
        ;;
    2)
        echo ""
        echo "Deploying to preview..."
        $VERCEL_CMD
        ;;
    3)
        echo "Deployment cancelled."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option. Deployment cancelled.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Visit your deployment URL to test the application"
echo "  2. Upload a sample PDF to verify functionality"
echo "  3. Check the /api/health endpoint"
echo ""
echo "To view logs:"
echo "  $VERCEL_CMD logs"
echo ""
echo "To manage environment variables:"
echo "  $VERCEL_CMD env ls"
echo ""
