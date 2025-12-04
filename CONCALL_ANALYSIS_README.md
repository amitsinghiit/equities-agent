# Concall Analysis Feature Setup

## Overview
The concall analysis feature automatically downloads and analyzes the latest investor presentation (concall PPT) from Screener.in using Google's Gemini AI.

## Features
- Automatically scrapes the most recent concall presentation link
- Downloads the PDF/PPT file
- Analyzes it using Gemini AI to extract:
  - Future Guidance & Outlook
  - Key Achievements & Highlights
  - Risks & Challenges
  - Strategic Focus Areas
- Generates a comprehensive 30-40 sentence summary
- Displays the analysis in the Streamlit frontend

## Setup Instructions

### 1. Get a Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

### 2. Set the Environment Variable

**On macOS/Linux:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

To make it permanent, add to your `~/.zshrc` or `~/.bashrc`:
```bash
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**On Windows:**
```cmd
set GEMINI_API_KEY=your-api-key-here
```

### 3. Restart the Backend Server
After setting the API key, restart the backend:
```bash
cd backend
python3 main.py
```

### 4. Test the Feature
```bash
./test_concall.sh BALKRISIND
```

Or use the Streamlit app and search for any company with recent concalls.

## How It Works

1. **Scraping**: The system scrapes the "Concalls" section on Screener.in
2. **Download**: Downloads the most recent PPT/PDF file
3. **Upload**: Uploads the file to Gemini API
4. **Analysis**: Gemini analyzes the presentation with a structured prompt
5. **Display**: The 30-40 sentence summary is displayed in the Streamlit app

## Supported Companies
Any company listed on Screener.in that has uploaded concall presentations.

## Limitations
- Requires a valid Gemini API key
- Analysis time: 10-30 seconds depending on file size
- Free tier Gemini API has rate limits (check Google's documentation)

## Troubleshooting

**Error: "Gemini API key not configured"**
- Make sure you've set the `GEMINI_API_KEY` environment variable
- Restart the backend server after setting the variable

**Error: "No concall presentation found"**
- The company may not have uploaded any presentations to Screener.in
- Try a different company (e.g., BALKRISIND, RELIANCE, TCS)

**Error: "Failed to download presentation"**
- The link may be broken or require authentication
- Try again later or with a different company

## Example Output
The analysis will include:
- Revenue and profit projections
- Growth targets and expansion plans
- Recent achievements and milestones
- Market risks and challenges
- Strategic priorities and investments
- ESG initiatives

All formatted in a clear, investor-friendly summary of 30-40 sentences.
