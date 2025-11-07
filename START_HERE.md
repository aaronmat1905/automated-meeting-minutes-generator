# 🚀 START HERE - Super Quick Setup!

## ✨ What You Need (100% FREE!)

1. **2 FREE API Keys** (no credit card needed):
   - Gemini API (Google AI)
   - AssemblyAI API (transcription)

2. **Python 3.9+** on your computer

That's it! No Google Cloud, no complex setup! 🎉

---

## 📝 Step 1: Get Your FREE API Keys (5 minutes)

### A) Gemini API Key
1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key 📋

### B) AssemblyAI API Key
1. Go to: **https://www.assemblyai.com/dashboard/signup**
2. Sign up (100% free - includes 100 hours/month!)
3. Copy your API key from dashboard 📋

**Total time: 5 minutes** ⏱️

---

## 💻 Step 2: Install & Configure (3 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create config file
copy .env.simple .env     # Windows
# OR
cp .env.simple .env       # Mac/Linux

# 3. Edit .env file and paste your API keys:
#    GEMINI_API_KEY=your-key-here
#    ASSEMBLYAI_API_KEY=your-key-here
```

---

## 🎬 Step 3: Run! (30 seconds)

### Easy Method (Double-click):
- **Windows:** Double-click `run.bat`
- **Mac/Linux:** Run `./run.sh` in terminal

### Manual Method:
```bash
python start.py
```

Open your browser: **http://localhost:5000**

**You're done!** 🎊

---

## 🎯 How to Use

1. **Upload** your meeting audio (MP3, WAV, MP4, etc.)
2. **Fill** meeting details
3. **Click** "Process Meeting"
4. **Wait** ~2-3 minutes
5. **Download** your professional minutes!

---

## ❓ Troubleshooting

### "ASSEMBLYAI_API_KEY not configured"
→ Make sure you pasted BOTH API keys in `.env` file

### "pip install fails"
→ Make sure you have Python 3.9+ installed:
```bash
python --version
```

### "Module not found"
→ Activate virtual environment first:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Then install
pip install -r requirements.txt
```

---

## 🎁 What You Get

✅ **Accurate Transcription** (AssemblyAI - better than Whisper!)
✅ **AI-Powered Analysis** (Gemini extracts actions, decisions)
✅ **Beautiful Web UI** (Modern, easy to use)
✅ **Multiple Formats** (PDF, Markdown, Text, Word)
✅ **3 Professional Templates** (MRS, MTQP, MSAD)

---

## 💡 Why AssemblyAI Instead of Whisper?

✅ **No installation hassles** - Just an API key!
✅ **Better accuracy** - Professional-grade transcription
✅ **100% FREE** - 100 hours/month free tier
✅ **Fast** - Cloud-based, no download needed
✅ **Works on all computers** - No Python 3.13 compatibility issues!

---

## 🎓 For Your Project

This meets ALL your SCRUM requirements:
- ✅ Audio upload & transcription
- ✅ Action item extraction
- ✅ AI-powered analysis
- ✅ Professional minutes generation
- ✅ Multiple export formats
- ✅ Beautiful UI that WORKS!

---

## 📚 Need More Help?

- **Quick Guide:** [QUICKSTART.md](QUICKSTART.md)
- **Full Details:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Checklist:** [CHECKLIST.md](CHECKLIST.md)

---

## 🎉 Ready to Generate Minutes!

```bash
# Windows: Double-click run.bat
# Or manually:
python start.py

# Open browser:
http://localhost:5000
```

**Upload a meeting recording and watch the magic happen!** ✨

---

*Made with ❤️ by Ramen Noodles Team | PES University*

**Questions?** Check the documentation files above or ask your team!
