# 🚀 Quick Start Guide for Concall Analysis

## ✅ What's Working
- ✅ Scraper successfully finds PPT links from Screener.in
- ✅ Backend integration complete
- ✅ Frontend display ready
- ⏳ Waiting for Gemini API key to enable AI analysis

## 📋 Setup Steps

### 1. Get Your Gemini API Key (2 minutes)

**Option A: Using Google AI Studio (Recommended)**
1. Open: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key" (or "Get API Key")
4. Copy the generated key (starts with "AIza...")

**Option B: Using Google Cloud Console**
1. Go to: https://console.cloud.google.com/
2. Enable the "Generative Language API"
3. Create credentials → API Key
4. Copy the key

### 2. Set the Environment Variable

**In your current terminal session:**
```bash
export GEMINI_API_KEY="AIza...your-key-here"
```

**To make it permanent (recommended):**
```bash
# Add to your shell config
echo 'export GEMINI_API_KEY="AIza...your-key-here"' >> ~/.zshrc

# Reload the config
source ~/.zshrc

# Verify it's set
echo $GEMINI_API_KEY
```

### 3. Restart the Backend Server

**Stop the current backend:**
- Find the terminal running `python3 main.py`
- Press `Ctrl+C` to stop it

**Start it again:**
```bash
cd /Users/amitsingh/Documents/Google\ Antigrqavity\ Agent
./restart_backend.sh
```

Or manually:
```bash
cd backend
python3 main.py
```

### 4. Test the Feature

**Option A: Using the test script**
```bash
./test_concall.sh BALKRISIND
```

**Option B: Using the Streamlit app**
1. Open the Streamlit app (should already be running at http://localhost:8501)
2. Search for "Balkrishna Industries" or "BALKRISIND"
3. Click "Analyze"
4. Scroll down to see "📊 Latest Concall Analysis"
5. Wait 10-30 seconds for the AI analysis to complete

## 🎯 Expected Results

When successful, you'll see a comprehensive analysis with:

### 1. Future Guidance & Outlook (8-10 sentences)
- Revenue and profit projections
- Growth targets with timelines
- Expansion plans and capex details
- Market opportunities being targeted
- Strategic initiatives planned

### 2. Key Achievements & Highlights (8-10 sentences)
- Recent financial performance
- Operational milestones
- Market share gains
- Product launches
- Awards and recognitions

### 3. Risks & Challenges (8-10 sentences)
- Market and competitive threats
- Regulatory challenges
- Supply chain risks
- Financial risks
- Industry headwinds

### 4. Strategic Focus Areas (6-8 sentences)
- Key priorities
- Investment areas
- Sustainability initiatives
- Geographic focus

## 🔍 Troubleshooting

### Issue: "Gemini API key not configured"
**Solution:**
```bash
# Check if it's set
echo $GEMINI_API_KEY

# If empty, set it
export GEMINI_API_KEY="your-key-here"

# Restart backend
cd backend && python3 main.py
```

### Issue: "No concall presentation found"
**Cause:** Company hasn't uploaded presentations to Screener.in

**Try these companies instead:**
- BALKRISIND (Balkrishna Industries)
- RELIANCE (Reliance Industries)
- TCS (Tata Consultancy Services)
- INFY (Infosys)
- HDFCBANK (HDFC Bank)

### Issue: Analysis takes too long
**Normal:** First analysis may take 20-30 seconds
**If > 1 minute:** Check your internet connection

### Issue: Rate limit errors
**Cause:** Free tier Gemini API has limits
**Solution:** Wait a few minutes and try again

## 📊 Testing Different Companies

```bash
# Test multiple companies
./test_concall.sh BALKRISIND
./test_concall.sh RELIANCE
./test_concall.sh TCS
```

## 🎓 How It Works

```
User searches for company
         ↓
Backend scrapes Screener.in for latest PPT link
         ↓
Downloads the PDF/PPT file
         ↓
Uploads to Gemini AI
         ↓
Gemini analyzes with structured prompt
         ↓
Returns 30-40 sentence summary
         ↓
Displayed in Streamlit frontend
```

## 💡 Pro Tips

1. **Best companies to test**: Look for companies with recent quarterly results
2. **Analysis quality**: More detailed presentations = better analysis
3. **Caching**: Consider adding caching to avoid re-analyzing the same presentation
4. **Cost**: Gemini API free tier is generous, but monitor usage

## 📞 Need Help?

If you encounter issues:
1. Check the backend logs for detailed error messages
2. Verify your API key is valid
3. Ensure you have internet connectivity
4. Try with a different company

---

**Ready to test?** Run:
```bash
export GEMINI_API_KEY="your-key-here"
./restart_backend.sh
```

Then open the Streamlit app and search for BALKRISIND!
