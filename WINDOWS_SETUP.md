# 🪟 GetMyHouse - Windows Setup Guide

## 📁 Project Directory
```
C:\Users\josef\My_Documents\_Projects\getmyhouse
```

## 🔧 Prerequisites

### 1. Install Python 3.10+
Download from: https://www.python.org/downloads/

**Important:** Check "Add Python to PATH" during installation

Verify installation:
```cmd
python --version
```

### 2. Install Git (Optional but recommended)
Download from: https://git-scm.com/download/win

## 🚀 Setup Instructions

### Step 1: Open Command Prompt
- Press `Win + R`
- Type `cmd` and press Enter
- Navigate to project directory:
```cmd
cd C:\Users\josef\My_Documents\_Projects\getmyhouse
```

### Step 2: Create Virtual Environment
```cmd
python -m venv venv
```

### Step 3: Activate Virtual Environment
```cmd
venv\Scripts\activate
```

You should see `(venv)` at the beginning of your command prompt.

### Step 4: Upgrade pip
```cmd
python -m pip install --upgrade pip
```

### Step 5: Install Dependencies
```cmd
pip install -r requirements.txt
```

**Note:** This may take 5-10 minutes. Be patient!

### Step 6: Configure Environment Variables

1. Copy `.env.example` to `.env`:
```cmd
copy .env.example .env
```

2. Open `.env` in a text editor (Notepad, VSCode, etc.)

3. Add your Google API key:
```
GOOGLE_API_KEY=your_actual_api_key_here
```

**Get your API key from:** https://makersuite.google.com/app/apikey

### Step 7: Create Data Directory
```cmd
mkdir data
mkdir logs
```

## ▶️ Running the Application

### Run Streamlit App
```cmd
streamlit run app.py
```

The app will open automatically in your browser at:
```
http://localhost:8501
```

## 🛠️ Development Tools

### Run Tests
```cmd
pytest tests\ -v
```

### Check Code Style
```cmd
black src\
flake8 src\
```

## 🔍 Troubleshooting

### Issue: "python is not recognized"
**Solution:** Add Python to PATH:
1. Search for "Environment Variables" in Windows
2. Edit PATH variable
3. Add: `C:\Users\josef\AppData\Local\Programs\Python\Python3XX`
4. Restart Command Prompt

### Issue: "pip install fails"
**Solution 1:** Try with `--user` flag:
```cmd
pip install --user -r requirements.txt
```

**Solution 2:** Run Command Prompt as Administrator

### Issue: "Module not found"
**Solution:** Make sure virtual environment is activated:
```cmd
venv\Scripts\activate
```

### Issue: "Access denied" when installing packages
**Solution:** Run Command Prompt as Administrator or use `--user` flag

### Issue: Streamlit shows "Connection error"
**Solution:** Check if port 8501 is available:
```cmd
netstat -ano | findstr :8501
```

If port is busy, specify a different port:
```cmd
streamlit run app.py --server.port 8502
```

## 📝 VS Code Setup (Optional)

### Install VS Code
Download from: https://code.visualstudio.com/

### Recommended Extensions
1. Python (Microsoft)
2. Pylance (Microsoft)
3. Python Debugger (Microsoft)
4. GitLens (if using Git)

### Open Project in VS Code
```cmd
cd C:\Users\josef\My_Documents\_Projects\getmyhouse
code .
```

### Select Python Interpreter
1. Press `Ctrl + Shift + P`
2. Type "Python: Select Interpreter"
3. Choose: `.\venv\Scripts\python.exe`

### VS Code Integrated Terminal
- Press `` Ctrl + ` `` to open terminal
- Activate venv:
```cmd
venv\Scripts\activate
```

## 🐳 Docker on Windows (Optional - for Day 5)

### Install Docker Desktop
Download from: https://www.docker.com/products/docker-desktop/

### Build Docker Image
```cmd
docker build -t getmyhouse:latest .
```

### Run Docker Container
```cmd
docker run -p 8501:8501 --env-file .env getmyhouse:latest
```

## 📊 Directory Structure Check

After setup, your directory should look like this:
```
C:\Users\josef\My_Documents\_Projects\getmyhouse\
├── venv\                    (created by you)
├── data\                    (created by you)
├── logs\                    (created by you)
├── src\
│   ├── agents\
│   ├── tools\
│   ├── memory\
│   ├── evaluation\
│   └── config.py
├── tests\
├── .env                     (created by you from .env.example)
├── .env.example
├── .gitignore
├── app.py                   (to be created)
├── requirements.txt
├── Dockerfile               (to be created)
└── README.md
```

## 🔗 Useful Commands

### Deactivate Virtual Environment
```cmd
deactivate
```

### Clean Python Cache
```cmd
del /s /q __pycache__
del /s /q *.pyc
```

### Update All Packages
```cmd
pip install --upgrade -r requirements.txt
```

### Check Installed Packages
```cmd
pip list
```

### Check Package Version
```cmd
pip show google-adk
```

## 🆘 Getting Help

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Check Python error messages carefully
3. Verify virtual environment is activated
4. Ensure all dependencies are installed
5. Check `.env` file is configured correctly

## 📚 Additional Resources

- **Google ADK Docs:** https://google.github.io/adk-docs/
- **Streamlit Docs:** https://docs.streamlit.io/
- **Python Windows Guide:** https://docs.python.org/3/using/windows.html

---

**Ready to start development!** 🚀

Next step: Create `app.py` (Streamlit UI)
