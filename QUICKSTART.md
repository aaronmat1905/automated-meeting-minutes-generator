## 🚀 QUICK START GUIDE - Meeting Minutes Generator

### ✨ What You Need (Simplified!)

**NO Google Cloud Account Required!**

You only need:
1. ✅ Python 3.9+ installed
2. ✅ A **free** Gemini API key (takes 2 minutes to get)
3. ✅ ~2GB disk space for Whisper model

---

## 📝 Step 1: Get Your FREE Gemini API Key (2 minutes)

1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with any Google account (Gmail)
3. Click "**Create API Key**"
4. Copy the key (looks like: `AIzaSyD...`)

That's it! No credit card, no billing, completely free!

---

## 💻 Step 2: Install (5 minutes)

### Windows:
```bash
# Clone or download the project
git clone <your-repo-url>
cd PESU_RR_AIML_A_P34_Automated_Meeting_Minutes_Generator_Ramen-Noodles

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Mac/Linux:
```bash
# Clone or download the project
git clone <your-repo-url>
cd PESU_RR_AIML_A_P34_Automated_Meeting_Minutes_Generator_Ramen-Noodles

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Step 3: Configure (1 minute)

1. Copy the example environment file:
```bash
cp .env.simple .env
```

2. Open `.env` in any text editor and add your Gemini API key:
```bash
GEMINI_API_KEY=paste-your-key-here
```

That's the ONLY required configuration! 🎉

---

## 🎬 Step 4: Run the App!

```bash
# Make sure your virtual environment is activated
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Run the application
python src/app_simple.py
```

You should see:
```
============================================================
Meeting Minutes Generator - Simplified Version
============================================================
Starting on http://localhost:5000
Whisper Model: base
Gemini Configured: True
============================================================
```

---

## 🌐 Step 5: Open in Browser

1. Open your web browser
2. Go to: **http://localhost:5000**
3. You'll see a beautiful web interface! 🎨

---

## 🎯 How to Use

### Method 1: Web Interface (Easiest!)

1. **Upload** your meeting audio file (MP3, WAV, MP4, etc.)
2. **Fill in** meeting details (title, date, participants)
3. **Click** "Process Meeting"
4. **Wait** 2-5 minutes (depends on audio length)
5. **Download** your generated minutes!

### Method 2: API (For Developers)

```python
import requests

url = "http://localhost:5000/api/process-meeting"

with open("meeting.mp3", "rb") as audio:
    files = {
        'file': audio,
        'metadata': (None, '{"title":"Team Meeting"}'),
        'template': (None, 'MRS'),
        'formats': (None, 'pdf,markdown')
    }

    response = requests.post(url, files=files)
    result = response.json()

    print(f"Transcript: {result['transcript']}")
    print(f"Action Items: {len(result['analysis']['action_items'])}")
    print(f"Files: {result['minutes_files']}")
```

---

## 🎨 Features You Get

✅ **Audio Transcription** - Using OpenAI Whisper (runs locally!)
✅ **AI Analysis** - Action items, decisions, summaries via Gemini
✅ **Multiple Templates** - MRS, MTQP, MSAD formats
✅ **Export Formats** - PDF, Markdown, Text, Word
✅ **Beautiful Web UI** - Modern, responsive design
✅ **No Cloud Required** - Everything runs on your computer!

---

## 🔧 Configuration Options

### Whisper Model Sizes

Edit `.env` to change model:

```bash
WHISPER_MODEL_SIZE=base  # Change this
```

**Options:**
- `tiny` - Super fast, okay accuracy (~1GB RAM) ⚡
- `base` - **RECOMMENDED** - Good balance (~1GB RAM) 👍
- `small` - Better accuracy (~2GB RAM)
- `medium` - Great accuracy (~5GB RAM)
- `large` - Best accuracy (~10GB RAM) 🚀

**First run** will download the model (happens automatically).

### Languages Supported

Change in `.env`:
```bash
WHISPER_LANGUAGE=en  # en, es, fr, de, zh, ja, hi, etc.
```

Or select in web UI!

---

## 📊 System Requirements

### Minimum:
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 2GB free
- **Model:** `tiny` or `base`

### Recommended:
- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Storage:** 5GB free
- **Model:** `base` or `small`

---

## ❓ Troubleshooting

### "GEMINI_API_KEY not configured"
**Solution:** Make sure you:
1. Created `.env` file (copy from `.env.simple`)
2. Pasted your API key without quotes
3. Restarted the application

### "Whisper model download failed"
**Solution:**
- Check internet connection
- Model downloads on first use (~200MB for base model)
- Wait a few minutes, it's downloading!

### "Out of memory" error
**Solution:** Use a smaller Whisper model:
```bash
# In .env file
WHISPER_MODEL_SIZE=tiny
```

### "Module not found" error
**Solution:** Make sure virtual environment is activated:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Then reinstall
pip install -r requirements.txt
```

### Audio file not processing
**Solution:**
- Supported formats: MP3, WAV, MP4, M4A, FLAC, OGG, WebM
- Max size: 100MB (change in `.env` if needed)
- Try converting: `ffmpeg -i input.xxx output.mp3`

---

## 🧪 Test It Out

Try with a short test:

```bash
# Create a 10-second test audio (requires ffmpeg)
ffmpeg -f lavfi -i sine=frequency=1000:duration=10 -ac 1 test.mp3

# Then upload test.mp3 through the web UI!
```

Or record a quick voice memo on your phone and upload it!

---

## 📁 Project Structure

```
├── src/
│   ├── app_simple.py          # Main Flask app (USE THIS!)
│   ├── config_simple.py       # Simple configuration
│   ├── static/                # CSS & JavaScript
│   ├── templates/             # HTML templates
│   └── services/              # Business logic
│       ├── audio_processor.py
│       ├── whisper_transcription.py  # Local transcription
│       ├── gemini_agent.py           # AI analysis
│       └── document_generator.py     # PDF/Markdown export
├── data/                      # Your uploaded files & exports
├── .env                       # Your configuration (create this!)
└── requirements.txt           # Dependencies
```

---

## 🎓 For Your SCRUM Project

This meets all your requirements:

✅ **EPIC 1: Meeting Capture & Transcription**
- Audio upload support (US-001) ✓
- High-accuracy transcription (US-004) ✓
- Audio quality detection (US-006) ✓

✅ **EPIC 2: AI-Powered Content Extraction**
- Action item extraction (US-008) ✓
- Auto-assign owners & dates (US-009) ✓
- Generate summaries (US-010, US-012) ✓
- Detect commitments (US-011) ✓
- Professional minutes (US-013) ✓
- Multiple export formats (US-014) ✓

---

## 🚀 Next Steps

1. **Test it** with your team's actual meeting recordings
2. **Customize** the templates in `document_generator.py`
3. **Deploy** to a server (see `DEPLOYMENT.md`)
4. **Add features** from your backlog

---

## 💡 Pro Tips

1. **Batch Processing:** Process multiple meetings by running the API in a loop
2. **Quality:** Better audio = better transcripts. Use a good mic!
3. **Privacy:** Everything runs locally - your audio never leaves your computer
4. **Speed:** First run is slow (downloads model), subsequent runs are fast!

---

## 🆘 Need Help?

- **Documentation:** Check `docs/` folder
- **Issues:** Create GitHub issue
- **Team:** Contact Ramen Noodles team

---

## 🎉 You're Ready!

Now go generate some amazing meeting minutes!

**Remember:**
- First transcription takes longer (downloading model)
- Gemini API is free but has rate limits
- Audio quality matters!

Happy transcribing! 🎤📝✨

---

*Made with ❤️ by Ramen Noodles Team*
*PES University - AIML Section A*
