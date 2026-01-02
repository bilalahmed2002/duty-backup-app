# Git Setup - duty-backup-app as Separate Repository

## 🎯 Goal: Make `duty-backup-app/` its own Git repository

You want ONLY the `duty-backup-app/` folder in GitHub, not the entire OPERATIONS-FTE directory.

---

## ✅ Step-by-Step Setup

### STEP 1: Go to duty-backup-app folder
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
pwd
# Should show: /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
```

### STEP 2: Initialize Git Repository
```bash
git init
```

### STEP 3: Verify .gitignore
```bash
cat .gitignore | grep -E "\.env|config\.encrypted|sessions"
# Should show: .env, config.encrypted, sessions/
```

### STEP 4: Add All Files
```bash
git add .
```

### STEP 5: Check What Will Be Committed
```bash
git status
```

**Verify:**
- ✅ NO `.env` file
- ✅ NO `config.encrypted` file
- ✅ NO `sessions/` folder
- ✅ NO `*.log`, `*.pdf`, `*.xlsx` files
- ✅ YES all `.py` files
- ✅ YES `.env.example`
- ✅ YES `.gitignore`
- ✅ YES `.github/workflows/build-windows-exe.yml`

### STEP 6: Commit
```bash
git commit -m "Initial commit: Duty Backup App - Standalone GUI for NetCHB duty service

- PyQt6 GUI with Process, Results, and Search tabs
- Supabase authentication and local session storage
- Encrypted config support for employee distribution
- GitHub Actions workflow for Windows executable build
- All test files and sensitive data excluded via .gitignore"
```

### STEP 7: Create GitHub Repository
1. Go to GitHub.com
2. Click "New repository"
3. Name it: `duty-backup-app` (or your preferred name)
4. **DO NOT** initialize with README, .gitignore, or license
5. Click "Create repository"

### STEP 8: Add Remote and Push
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/duty-backup-app.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## 📁 Repository Structure

After setup, your repository will contain:

```
duty-backup-app/                    ← Git repo root
├── .git/                          ← Git repository
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml  ← GitHub Actions workflow
├── .gitignore                     ← Ignores .env, sessions, etc.
├── .env.example                    ← Template (safe to commit)
├── .env                            ← NOT tracked (in .gitignore)
├── config.encrypted                ← NOT tracked (in .gitignore)
├── sessions/                       ← NOT tracked (in .gitignore)
├── auth/
├── gui/
├── service/
├── utils/
├── main.py
├── build_standalone.py
├── requirements_standalone.txt
└── ... (all source files)
```

---

## ⚠️ Important Notes

### Backend Dependency

The app needs `FTE-Operations-backend` for imports. Options:

**Option 1: Submodule (Recommended)**
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
git submodule add https://github.com/YOUR_USERNAME/FTE-Operations-backend.git backend
```

**Option 2: Manual Setup**
- Users need to have `FTE-Operations-backend` in the parent directory
- Or modify `build_standalone.py` to handle different paths

**Option 3: Bundle Backend Code**
- Copy required backend modules into `duty-backup-app/`
- Not recommended (code duplication)

### GitHub Actions Workflow

The workflow at `.github/workflows/build-windows-exe.yml` is configured to:
- Build from the root of `duty-backup-app/`
- Look for backend at `../FTE-Operations-backend/` (parent directory)
- If backend is a submodule, it will be checked out automatically

---

## 🚀 Quick Start Commands

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app

# Initialize git
git init

# Add files
git add .

# Verify (check no .env, no sessions)
git status

# Commit
git commit -m "Initial commit: Duty Backup App"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/duty-backup-app.git

# Push
git branch -M main
git push -u origin main
```

---

## ✅ Verification

After pushing, verify:

1. Go to GitHub → Your repository
2. Check that:
   - ✅ All source files are there
   - ✅ `.env` is NOT there
   - ✅ `sessions/` is NOT there
   - ✅ `.github/workflows/build-windows-exe.yml` exists
3. Go to Actions tab
4. The workflow should be available

---

## 🔧 Troubleshooting

**"Backend not found during build"**
- Add backend as submodule, OR
- Update workflow to checkout backend separately

**".env file was committed"**
- Remove it: `git rm --cached .env`
- Commit: `git commit -m "Remove .env file"`
- Push: `git push`

**"Workflow not showing in Actions"**
- Make sure `.github/workflows/build-windows-exe.yml` exists
- Push the file to GitHub
- Check Actions tab







