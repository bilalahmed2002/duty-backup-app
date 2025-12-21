# 🚀 Quick Start - Git Setup

## ⚠️ CRITICAL: Git Repository Location

**Git repository MUST be INSIDE `duty-backup-app/`:**
```
OPERATIONS-FTE/          
├── duty-backup-app/    ← Git repo should be HERE
│   ├── .git/           ← Git repository
│   ├── .github/
│   │   └── workflows/
│   │       └── build-windows-exe.yml
│   ├── auth/
│   ├── gui/
│   └── ... (all app files)
├── FTE-Operations-backend/  ← NOT in git repo
└── FTE-Operations-frontend/  ← NOT in git repo
```

**ONLY `duty-backup-app/` goes to GitHub, not the entire OPERATIONS-FTE folder!**

---

## Step-by-Step Commands

### 1. Go to duty-backup-app Folder
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
pwd
# Should show: /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
```

### 2. Initialize Git Repository
```bash
git init
```

### 3. Add All Files
```bash
git add .
```

### 4. Verify What Will Be Committed
```bash
git status
```

**Check for:**
- ✅ NO `.env` file
- ✅ NO `config.encrypted` file  
- ✅ NO `sessions/` folder
- ✅ YES all `.py` files
- ✅ YES `.env.example`
- ✅ YES `.gitignore`
- ✅ YES `.github/workflows/build-windows-exe.yml`

### 5. Commit
```bash
git commit -m "Initial commit: Duty Backup App - Standalone GUI for NetCHB duty service"
```

### 6. Create GitHub Repository
1. Go to GitHub.com
2. Click "New repository"
3. Name it: `duty-backup-app`
4. **DO NOT** initialize with README, .gitignore, or license
5. Click "Create repository"

### 7. Add Remote and Push
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/duty-backup-app.git

git branch -M main
git push -u origin main
```

---

## ✅ Verification

After setup, verify the structure:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
ls -la .git
# Should show: .git directory exists

git status
# Should work (duty-backup-app is the git repo)
```

---

## ❌ Common Mistakes

**WRONG:**
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE
git init  # ❌ NO! This would include all folders
```

**CORRECT:**
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
git init  # ✅ YES! Only duty-backup-app in repo
```

---

## 📁 Final Structure

```
OPERATIONS-FTE/                    
├── duty-backup-app/              ← Git repo root (ONLY this in GitHub)
│   ├── .git/                     ← Git repository
│   ├── .github/
│   │   └── workflows/
│   │       └── build-windows-exe.yml ← GitHub Actions workflow
│   ├── .gitignore                ← Ignores .env, sessions, etc.
│   ├── .env.example              ← Template (safe to commit)
│   ├── .env                      ← NOT tracked (in .gitignore)
│   ├── config.encrypted           ← NOT tracked (in .gitignore)
│   ├── sessions/                 ← NOT tracked (in .gitignore)
│   ├── auth/
│   ├── gui/
│   ├── service/
│   └── ... (all source files)
├── FTE-Operations-backend/        ← NOT in git repo
└── FTE-Operations-frontend/       ← NOT in git repo
```

---

## 🎯 One-Liner Setup (If Starting Fresh)

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app && \
git init && \
git add . && \
git status && \
echo "✅ Review the status above, then commit and push!"
```

