# ✅ Setup & Run Checklist

Use this checklist to get started quickly!

---

## 🎯 Pre-Requirements

- [ ] Python 3.9 or higher installed
- [ ] pip package manager available
- [ ] ~5GB free disk space
- [ ] Internet connection (for initial setup)

---

## 🔑 Step 1: Get Gemini API Key (2 minutes)

- [ ] Go to https://makersuite.google.com/app/apikey
- [ ] Sign in with Google account
- [ ] Click "Create API Key"
- [ ] Copy the API key (looks like: `AIzaSyD...`)
- [ ] Keep it safe - you'll need it in Step 3

---

## 💻 Step 2: Install (5 minutes)

### Windows:
- [ ] Open Command Prompt or PowerShell
- [ ] Navigate to project folder
- [ ] Run: `python -m venv venv`
- [ ] Run: `venv\Scripts\activate`
- [ ] Run: `pip install -r requirements.txt`

### Mac/Linux:
- [ ] Open Terminal
- [ ] Navigate to project folder
- [ ] Run: `python3 -m venv venv`
- [ ] Run: `source venv/bin/activate`
- [ ] Run: `pip install -r requirements.txt`

**Note:** First install takes 5-10 minutes. Be patient!

---

## ⚙️ Step 3: Configure (1 minute)

- [ ] Copy `.env.simple` to `.env`: `cp .env.simple .env`
- [ ] Open `.env` in text editor
- [ ] Paste your Gemini API key: `GEMINI_API_KEY=your-key-here`
- [ ] Save the file

**Optional customization:**
- [ ] Change Whisper model size (default: `base`)
- [ ] Set default language (default: `en`)
- [ ] Adjust max file size (default: 100MB)

---

## 🚀 Step 4: Run (30 seconds)

### Option A: Using scripts (easiest)
**Windows:**
- [ ] Double-click `run.bat`

**Mac/Linux:**
- [ ] Make executable: `chmod +x run.sh`
- [ ] Run: `./run.sh`

### Option B: Manual
- [ ] Activate venv (see Step 2)
- [ ] Run: `python src/app_simple.py`

**You should see:**
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

## 🌐 Step 5: Open Web UI

- [ ] Open web browser
- [ ] Go to: `http://localhost:5000`
- [ ] You should see the Meeting Minutes Generator interface

**If page doesn't load:**
- Check if app is running (look for errors in terminal)
- Try `http://127.0.0.1:5000`
- Check firewall settings

---

## 🎤 Step 6: Test with Sample Audio (Optional)

### Create test audio:
- [ ] Record a short voice memo on your phone (10-30 seconds)
- [ ] Transfer to computer
- [ ] Or use this command: `ffmpeg -f lavfi -i sine=frequency=1000:duration=10 test.mp3`

### Process in UI:
- [ ] Click "Choose File" and select audio
- [ ] Fill in meeting title: "Test Meeting"
- [ ] Set date (default is today)
- [ ] Add participants (optional)
- [ ] Click "Process Meeting"
- [ ] Wait for processing (1-3 minutes for first run)
- [ ] Check results!

**First transcription takes longer** (downloads Whisper model, ~200MB for base)

---

## ✅ Verification

Check that everything works:

- [ ] Audio file uploads successfully
- [ ] Progress bar shows processing steps
- [ ] Transcript appears in results
- [ ] Action items are extracted (if mentioned in audio)
- [ ] Download buttons work for PDF/Markdown
- [ ] Files appear in `data/exports/` folder

---

## 🎯 Ready to Use!

You're all set! Now you can:

- [ ] Process real meeting recordings
- [ ] Customize templates in `document_generator.py`
- [ ] Adjust AI prompts in `gemini_agent.py`
- [ ] Share with your team
- [ ] Add to your SCRUM project documentation

---

## 🆘 Troubleshooting

### "GEMINI_API_KEY not configured"
- [ ] Check `.env` file exists
- [ ] Verify API key is correctly pasted
- [ ] No quotes around the key
- [ ] Restart application

### "Module not found" error
- [ ] Activate virtual environment
- [ ] Run: `pip install -r requirements.txt` again
- [ ] Check Python version (must be 3.9+)

### "Out of memory" error
- [ ] Change to smaller model in `.env`: `WHISPER_MODEL_SIZE=tiny`
- [ ] Close other applications
- [ ] Process shorter audio files

### Audio file won't upload
- [ ] Check file size (<100MB by default)
- [ ] Verify format (MP3, WAV, MP4, M4A, FLAC, OGG, WebM)
- [ ] Try converting: `ffmpeg -i input.xxx output.mp3`

### Processing takes forever
**First time:** Whisper model downloads (~200MB), this is normal
**Subsequent times:**
- [ ] Use smaller Whisper model
- [ ] Check audio duration
- [ ] Monitor system resources

### Page won't load
- [ ] Check app is running (terminal shows no errors)
- [ ] Try different URL: `http://127.0.0.1:5000`
- [ ] Check firewall/antivirus
- [ ] Try different browser

---

## 📚 Need More Help?

- [ ] Read [QUICKSTART.md](QUICKSTART.md) for detailed guide
- [ ] Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture
- [ ] Review code comments for specific features
- [ ] Ask your team members
- [ ] Create GitHub issue

---

## 🎉 Success Indicators

You'll know it's working when you see:

✅ No errors in terminal
✅ Web UI loads at http://localhost:5000
✅ "Gemini Configured: True" in startup message
✅ Audio upload shows green checkmark
✅ Progress bar moves through stages
✅ Transcript appears in results
✅ Download buttons generate files
✅ PDF/Markdown files open correctly

---

## 🔄 Daily Usage

After initial setup, starting the app is easy:

### Windows:
```bash
# Option 1: Double-click
run.bat

# Option 2: Manual
venv\Scripts\activate
python src/app_simple.py
```

### Mac/Linux:
```bash
# Option 1: Script
./run.sh

# Option 2: Manual
source venv/bin/activate
python src/app_simple.py
```

**Bookmark:** http://localhost:5000

---

## 📊 Performance Tips

For better performance:

- [ ] Use `base` model (best balance)
- [ ] Process audio in quiet environment
- [ ] Convert to MP3 before upload
- [ ] Keep audio files <50MB
- [ ] Close unnecessary applications
- [ ] Use wired internet connection
- [ ] Batch process multiple meetings

---

## 🎓 For Your SCRUM Project

Make sure to document:

- [ ] Add this system to your sprint artifacts
- [ ] Update Jira user stories as "Done"
- [ ] Take screenshots for demo
- [ ] Record video walkthrough
- [ ] Note any customizations made
- [ ] List team contributions
- [ ] Prepare retrospective notes

---

## ✨ You're Done!

Congratulations! Your AI Meeting Minutes Generator is ready to use! 🎊

**Next Steps:**
1. Process a real meeting recording
2. Review the generated minutes
3. Customize as needed
4. Share with your team
5. Include in your project demo

---

**Happy transcribing!** 🎤📝✨

*Checklist by Ramen Noodles Team*
