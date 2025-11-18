# Deployment Guide - Medical Record Processor

This guide provides step-by-step instructions for deploying the Medical Record Processor to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Anthropic API Key**: Get one from [Anthropic Console](https://console.anthropic.com/settings/keys)
3. **GitHub Account**: For connecting your repository (optional but recommended)

## Deployment Methods

### Method 1: Deploy via Vercel CLI (Recommended for Developers)

#### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

Or use npx without installation:
```bash
npx vercel
```

#### Step 2: Login to Vercel

```bash
vercel login
```

This will open a browser window for authentication.

#### Step 3: Set Environment Variables

Before deploying, set the required environment variables:

```bash
# Set Anthropic API Key
vercel env add ANTHROPIC_API_KEY

# When prompted, paste your Anthropic API key
# Select: Production, Preview, and Development

# Set Claude Model
vercel env add CLAUDE_MODEL

# When prompted, enter: claude-sonnet-4-5
# Select: Production, Preview, and Development
```

#### Step 4: Deploy to Production

```bash
vercel --prod
```

Follow the prompts:
- **Set up and deploy**: Yes
- **Which scope**: Select your account/team
- **Link to existing project**: No (first time) or Yes (subsequent deploys)
- **What's your project's name**: medical-record-processor (or your preferred name)
- **In which directory is your code located**: ./ (press Enter)

The CLI will:
1. Build your project
2. Deploy to Vercel
3. Provide you with a production URL

#### Step 5: Verify Deployment

Visit the provided URL and test the application:
1. Upload a sample PDF
2. Verify the extraction works
3. Check the health endpoint: `https://your-app.vercel.app/api/health`

---

### Method 2: Deploy via Vercel Dashboard (Recommended for Beginners)

#### Step 1: Push Code to GitHub

Ensure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

#### Step 2: Import Project in Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **Import Git Repository**
3. Select your repository: `MedicalRecord_Processor`
4. Click **Import**

#### Step 3: Configure Project

Vercel will auto-detect the framework settings. Verify:

- **Framework Preset**: Other
- **Build Command**: (leave empty)
- **Output Directory**: (leave empty)
- **Install Command**: `pip install -r requirements.txt`

#### Step 4: Add Environment Variables

Before deploying, click **Environment Variables** and add:

| Name | Value | Environments |
|------|-------|--------------|
| `ANTHROPIC_API_KEY` | `your-api-key-here` | Production, Preview, Development |
| `CLAUDE_MODEL` | `claude-sonnet-4-5` | Production, Preview, Development |

#### Step 5: Deploy

1. Click **Deploy**
2. Wait for the build to complete (2-3 minutes)
3. Once deployed, click **Visit** to see your application

---

### Method 3: Deploy with Vercel Token (CI/CD)

For automated deployments or CI/CD pipelines:

#### Step 1: Get Vercel Token

1. Go to [Vercel Account Settings](https://vercel.com/account/tokens)
2. Click **Create Token**
3. Name it (e.g., "Medical Record Processor Deploy")
4. Copy the token

#### Step 2: Deploy with Token

```bash
npx vercel --token YOUR_VERCEL_TOKEN --prod --yes
```

Or set it as an environment variable:

```bash
export VERCEL_TOKEN=your-token-here
npx vercel --prod --yes
```

---

## Post-Deployment Configuration

### Update Environment Variables

To update environment variables after deployment:

**Via CLI:**
```bash
vercel env rm ANTHROPIC_API_KEY production
vercel env add ANTHROPIC_API_KEY production
```

**Via Dashboard:**
1. Go to your project in Vercel
2. Click **Settings** → **Environment Variables**
3. Edit or add new variables
4. Click **Save**
5. Redeploy for changes to take effect

### Custom Domain (Optional)

1. In Vercel dashboard, go to your project
2. Click **Settings** → **Domains**
3. Add your custom domain
4. Follow DNS configuration instructions

### View Logs

**Via CLI:**
```bash
vercel logs
```

**Via Dashboard:**
1. Go to your project
2. Click on a deployment
3. Click **Logs** tab

---

## Troubleshooting

### Issue: "Build failed - Unable to install dependencies"

**Solution:**
- Verify `requirements.txt` is properly formatted
- Check that all dependencies are available on PyPI
- Ensure Python version compatibility (3.8+)

### Issue: "Runtime error - Module not found"

**Solution:**
- Ensure all imports in `app.py` match the installed packages
- Check that relative imports are correct
- Verify `vercel.json` configuration

### Issue: "API Error - Invalid Anthropic API Key"

**Solution:**
1. Verify the API key in Vercel environment variables
2. Check the key is valid at [Anthropic Console](https://console.anthropic.com/)
3. Ensure the key has the correct permissions
4. Redeploy after updating the key

### Issue: "Timeout - Function exceeded time limit"

**Solution:**
- Increase `maxDuration` in `vercel.json` (currently set to 60s)
- Optimize PDF processing for large files
- Consider using Vercel Pro for longer timeouts (up to 300s)

### Issue: "Memory limit exceeded"

**Solution:**
- Increase `memory` in `vercel.json` (currently 1024MB)
- Optimize memory usage in PDF processing
- Consider Vercel Pro for higher memory limits

---

## Vercel Project Configuration

The project includes a `vercel.json` file with the following configuration:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "ANTHROPIC_API_KEY": "@anthropic_api_key",
    "CLAUDE_MODEL": "@claude_model"
  },
  "functions": {
    "app.py": {
      "maxDuration": 60,
      "memory": 1024
    }
  }
}
```

### Configuration Notes:

- **Python Runtime**: Uses `@vercel/python` for serverless functions
- **Timeout**: Set to 60 seconds (adjust if needed for large PDFs)
- **Memory**: 1024MB allocated (adjust based on usage)
- **Environment Variables**: Loaded from Vercel secrets

---

## Security Best Practices

1. **Never commit `.env` files**: Already in `.gitignore`
2. **Use Vercel secrets**: For sensitive environment variables
3. **Enable HTTPS**: Automatically enabled by Vercel
4. **Regular updates**: Keep dependencies updated
5. **Monitor logs**: Check for suspicious activity
6. **API key rotation**: Rotate Anthropic API keys regularly

---

## Scaling Considerations

### Free Tier Limits
- 100GB bandwidth per month
- 100 hours of serverless function execution
- 60-second maximum function duration

### Upgrading to Pro
Consider upgrading if you need:
- Custom domains
- Higher function timeout (300s)
- More bandwidth
- Team collaboration features

---

## Monitoring and Analytics

### View Usage Metrics

1. Go to Vercel dashboard
2. Select your project
3. Click **Analytics** tab

Metrics available:
- Request count
- Response times
- Error rates
- Bandwidth usage

### Set Up Alerts

1. Go to **Settings** → **Notifications**
2. Configure alerts for:
   - Deployment failures
   - Error spikes
   - Quota limits

---

## Continuous Deployment

### Automatic Deployments

Once connected to GitHub, Vercel automatically deploys:
- **Production**: Pushes to `main` branch
- **Preview**: Pull requests and other branches

### Disable Auto-Deploy

If needed:
1. Go to **Settings** → **Git**
2. Toggle **Production Branch** or **Preview Deployments**

---

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Vercel Support**: [vercel.com/support](https://vercel.com/support)
- **Anthropic Docs**: [docs.anthropic.com](https://docs.anthropic.com)

---

## Quick Reference

### Common Commands

```bash
# Login
vercel login

# Deploy to production
vercel --prod

# Deploy to preview
vercel

# View logs
vercel logs

# List environment variables
vercel env ls

# Pull environment variables locally
vercel env pull

# Check deployment status
vercel ls

# Remove a deployment
vercel remove <deployment-url>
```

### Environment Variables Required

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `CLAUDE_MODEL`: Claude model name (default: claude-sonnet-4-5)
- `DEBUG_MODE`: Enable debug outputs (default: false)

---

**Ready to deploy?** Start with **Method 2** (Vercel Dashboard) if you're new to Vercel, or **Method 1** (CLI) if you prefer command-line tools.
