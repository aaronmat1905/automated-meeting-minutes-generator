# 🤖 AI Meeting Minutes Generator - Simplified Version

> **NO GOOGLE CLOUD REQUIRED!** Just a free Gemini API key!

Transform your meeting recordings into professional minutes with AI - all running locally on your computer!

## ⚡ Quick Start (3 Steps!)

### 1️⃣ Get FREE Gemini API Key
Visit https://makersuite.google.com/app/apikey (2 minutes)

### 2️⃣ Install
```bash
pip install -r requirements.txt
cp .env.simple .env
# Edit .env and add your GEMINI_API_KEY
```

### 3️⃣ Run!
```bash
python src/app_simple.py
```

Open **http://localhost:5000** in your browser! 🎉

📖 **Full Guide:** See [QUICKSTART.md](QUICKSTART.md)

---

## ✨ Features

🎤 **Audio Transcription** - Whisper AI (runs locally, no cloud!)
🧠 **AI Analysis** - Extract action items, decisions, summaries
📄 **Multiple Formats** - Export as PDF, Markdown, Text, Word
🎨 **Beautiful Web UI** - Modern, easy-to-use interface
🔒 **Privacy First** - Everything runs on your computer
🌍 **Multi-Language** - Supports 14+ languages

---

## 📊 What You Get

Upload your meeting audio and get:
- ✅ Full transcript with timestamps
- ✅ Action items with owners & due dates
- ✅ Key decisions made
- ✅ Executive summary
- ✅ Open questions
- ✅ Professional formatted minutes (MRS/MTQP/MSAD templates)

---

## 💻 System Requirements

**Minimum:** Python 3.9, 4GB RAM, 2GB disk space
**Recommended:** Python 3.10+, 8GB RAM, 5GB disk space

---

## 🎯 Usage

### Web Interface (Easiest!)
1. Open http://localhost:5000
2. Upload audio file
3. Fill meeting details
4. Click "Process Meeting"
5. Download your minutes!

### API (For Developers)
```python
import requests

with open("meeting.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:5000/api/process-meeting",
        files={'file': f},
        data={
            'metadata': '{"title":"Team Meeting"}',
            'template': 'MRS',
            'formats': 'pdf,markdown'
        }
    )

result = response.json()
print(f"Minutes saved to: {result['minutes_files']}")
```

---

## 📁 Project Structure

```
├── src/
│   ├── app_simple.py              # 👈 Main app (USE THIS!)
│   ├── config_simple.py           # Simple config
│   ├── templates/index.html       # Web UI
│   ├── static/                    # CSS & JS
│   └── services/                  # Core services
│       ├── whisper_transcription.py  # Local transcription
│       ├── gemini_agent.py          # AI analysis
│       ├── audio_processor.py       # Audio handling
│       └── document_generator.py    # Export to PDF/Markdown
├── .env.simple                    # Config template
├── QUICKSTART.md                  # 👈 Detailed guide
├── requirements.txt               # Dependencies
└── README_SIMPLE.md              # This file
```

---

## 🔧 Configuration

Edit `.env` to customize:

```bash
# Required
GEMINI_API_KEY=your-key-here

# Optional
WHISPER_MODEL_SIZE=base  # tiny/base/small/medium/large
WHISPER_LANGUAGE=en      # en/es/fr/de/zh/ja/hi/...
MAX_AUDIO_FILE_SIZE_MB=100
```

---

## 🎓 For SCRUM Project

Implements all user stories from EPIC 1 & EPIC 2:
- ✅ Audio upload & validation
- ✅ High-accuracy transcription (Whisper)
- ✅ AI-powered content extraction (Gemini)
- ✅ Action item tracking
- ✅ Professional minutes generation
- ✅ Multiple export formats

See your JIRA backlog requirements fully met! 🎯

---

## 🆘 Troubleshooting

**"GEMINI_API_KEY not configured"**
→ Edit `.env` and add your API key

**"Out of memory"**
→ Use smaller Whisper model: `WHISPER_MODEL_SIZE=tiny`

**"Module not found"**
→ Activate venv: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)

**More help:** See [QUICKSTART.md](QUICKSTART.md)

---

## 🚀 Technology Stack

- **Flask** - Web framework
- **Whisper** - Speech-to-text (OpenAI)
- **Gemini 1.5 Pro** - AI analysis (Google)
- **ReportLab** - PDF generation
- **python-docx** - Word export

**Zero** cloud services required! Everything runs locally.

---

## 👥 Team

**Ramen Noodles** - PES University AIML Section A

- [@aaronmat1905](https://github.com/aaronmat1905) - Scrum Master
- [@pranavganesh1](https://github.com/pranavganesh1) - Developer
- [@pes1ug23am4](https://github.com/pes1ug23am4) - Developer
- [@PreethamVJ](https://github.com/PreethamVJ) - Developer

---

## 📄 License

Educational project for UE23CS341A - PES University

---

## 🎉 Get Started Now!

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.simple .env
# Edit .env with your GEMINI_API_KEY

# 3. Run
python src/app_simple.py

# 4. Open browser
# http://localhost:5000
```

**That's it!** Start generating meeting minutes in minutes! 🚀

---

**Questions?** Read [QUICKSTART.md](QUICKSTART.md) or contact the team!

*Made with ❤️ and lots of ☕*
