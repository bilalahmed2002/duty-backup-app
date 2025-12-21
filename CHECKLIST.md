# ✅ Pre-Deployment Checklist

## Quick Checklist - Do These Steps in Order

### ☐ STEP 1: Verify .env File
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
ls -la .env
```
**Status**: ✅ .env file exists (verified)

---

### ☐ STEP 2: Verify .gitignore
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
cat .gitignore | grep -E "\.env|config\.encrypted|sessions"
```
**Should show**: `.env`, `config.encrypted`, `sessions/`

---

### ☐ STEP 3: Clean Test Files (Optional)
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
rm -f *.log *.pdf *.xlsx
rm -rf test_output/ test_data/ 2>/dev/null
```
**Note**: These are already in `.gitignore`, but cleaning is good practice.

---

### ☐ STEP 4: Initialize Git at ROOT Level (If Not Already)
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE  # ⚠️ ROOT level, NOT duty-backup-app!
git init  # Only if not already a git repo

# Verify you're at the right level
pwd
# Should show: /Users/bilalahmed/Desktop/OPERATIONS-FTE
```
**⚠️ CRITICAL**: Git repo must be at `OPERATIONS-FTE` level, NOT inside `duty-backup-app`!

---

### ☐ STEP 5: Check What Will Be Committed
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE
git add duty-backup-app/
git status
```
**Verify**: 
- ✅ NO `.env` file
- ✅ NO `config.encrypted` file
- ✅ NO `sessions/` folder
- ✅ NO `*.log`, `*.pdf`, `*.xlsx` files
- ✅ YES all `.py` files
- ✅ YES `.env.example`
- ✅ YES `.gitignore`

---

### ☐ STEP 6: Commit
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE
git commit -m "Add duty-backup-app: Standalone GUI for NetCHB duty service"
```

---

### ☐ STEP 7: Verify GitHub Actions Workflow
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE
ls -la .github/workflows/build-windows-exe.yml
```
**Status**: ✅ Workflow exists at root (verified)

---

### ☐ STEP 8: Push to GitHub
```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE
git remote -v  # Check if remote exists
git push origin main  # Or your branch name
```

---

### ☐ STEP 9: Monitor Build
1. Go to GitHub → Your Repository → Actions tab
2. Watch the "Build Windows Executable" workflow
3. Wait for completion (usually 5-10 minutes)

---

### ☐ STEP 10: Download Executable
1. In GitHub Actions, find completed workflow
2. Download the artifact ZIP
3. Extract and test on Windows

---

## 🚀 Quick Start (All Steps at Once)

If you're confident everything is ready:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE

# 1. Add files
git add duty-backup-app/

# 2. Check status (VERIFY no .env, no sessions, etc.)
git status

# 3. Commit
git commit -m "Add duty-backup-app: Standalone GUI for NetCHB duty service"

# 4. Push
git push origin main
```

Then go to GitHub → Actions → Monitor the build!

---

## ⚠️ Important Reminders

1. **NEVER commit `.env`** - It's in `.gitignore` but double-check!
2. **NEVER commit `config.encrypted`** - Also in `.gitignore`
3. **NEVER commit `sessions/`** - Contains sensitive broker sessions
4. **Workflow must be at root**: `.github/workflows/build-windows-exe.yml` ✅

---

## 📚 Reference Documents

- `DEPLOYMENT_STEPS.md` - Detailed step-by-step guide
- `ENCRYPTION_GUIDE.md` - How encryption works
- `SESSION_AND_CONFIG_FAQ.md` - FAQ about sessions and config

