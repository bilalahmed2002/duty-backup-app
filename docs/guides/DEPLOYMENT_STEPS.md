# Step-by-Step Deployment Guide

## 🎯 Goal: Build Windows Executable via GitHub Actions

Follow these steps **one by one**:

---

## STEP 1: Verify Your .env File

**Location**: `/Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app/.env`

**Action**: Make sure your `.env` file exists and has all required values:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
cat .env
```

**Required values**:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (or `SUPABASE_SERVICE_ROLE_KEY`)
- `SUPABASE_SERVICE_ROLE_KEY` (for database access)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_BUCKET_NAME`
- `AWS_REGION`

**✅ Check**: File exists and has all values? → Continue to Step 2

---

## STEP 2: Test the Application Locally (Optional but Recommended)

**Action**: Make sure the app works before building:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app

# Activate virtual environment (if using one)
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Test imports
python test_imports.py

# Test the app
python test_app.py
```

**✅ Check**: App opens and works correctly? → Continue to Step 3

---

## STEP 3: Clean Test/Waste Files

**Action**: Remove or verify test files are in `.gitignore`:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app

# Check what will be ignored
git status --ignored

# Remove test files if they exist (optional - they're already in .gitignore)
rm -f test_*.py setup_test.sh run_dev.py TESTING_GUIDE.md QUICK_START.md
rm -rf test_output/ test_data/
rm -f *.log *.pdf *.xlsx
rm -rf sessions/ .session
```

**✅ Check**: Test files removed or ignored? → Continue to Step 4

---

## STEP 4: Initialize Git Repository (If Not Already Done)

**⚠️ IMPORTANT**: Git repository must be at the **ROOT** level (`OPERATIONS-FTE`), NOT inside `duty-backup-app`!

**Action**: Initialize git at the root level:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE

# Check if git repo already exists
git status 2>&1 | head -1

# If it says "not a git repository", initialize it:
git init

# Add remote (if you have one)
# git remote add origin https://github.com/yourusername/yourrepo.git
```

**✅ Check**: Git repo initialized at root level? → Continue to Step 5

---

## STEP 5: Verify .gitignore is Correct

**Action**: Check that sensitive files are ignored:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app

# Check .gitignore
cat .gitignore | grep -E "\.env|config\.encrypted|sessions|\.session"

# Should show:
# .env
# config.encrypted
# sessions/
# .session
```

**✅ Check**: All sensitive files are in `.gitignore`? → Continue to Step 6

---

## STEP 6: Test Encryption (Optional - For Employee Distribution)

**Action**: If you want to bundle encrypted config, test encryption:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app

# Make sure cryptography is installed
pip install cryptography

# Test encryption (creates config.encrypted)
python -c "from service.encrypted_config import EncryptedConfigManager; from pathlib import Path; EncryptedConfigManager().encrypt_env_file(Path('.env'), Path('config.encrypted'))"

# Verify it was created
ls -la config.encrypted
```

**Note**: If you skip this, the build script will auto-encrypt during build.

**✅ Check**: Encryption works (or you'll skip it)? → Continue to Step 7

---

## STEP 7: Check Git Status

**Action**: See what will be committed:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app

# Check status
git status

# Should NOT show:
# ❌ .env
# ❌ config.encrypted
# ❌ sessions/
# ❌ .session
# ❌ *.log, *.pdf, *.xlsx
# ❌ test_*.py

# Should show:
# ✅ All source code files
# ✅ .env.example
# ✅ .gitignore
# ✅ build_standalone.py
# ✅ requirements_standalone.txt
# ✅ All .py files in service/, gui/, auth/, utils/
```

**✅ Check**: Only safe files will be committed? → Continue to Step 8

---

## STEP 8: Add Files to Git

**Action**: Add the duty-backup-app folder to Git:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE

# Add the entire folder (Git will respect .gitignore)
git add duty-backup-app/

# Verify what was added
git status
```

**✅ Check**: Only safe files were added (no .env, no sessions)? → Continue to Step 9

---

## STEP 9: Commit Changes

**Action**: Commit the files:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE

git commit -m "Add duty-backup-app: Standalone GUI application for NetCHB duty service

- PyQt6 GUI with Process, Results, and Search tabs
- Supabase authentication and local session storage
- Encrypted config support for employee distribution
- GitHub Actions workflow for Windows executable build
- All test files and sensitive data excluded via .gitignore"
```

**✅ Check**: Commit successful? → Continue to Step 10

---

## STEP 10: Verify GitHub Actions Workflow Exists

**Action**: Check that the workflow file exists:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE

# Check workflow file
ls -la .github/workflows/build-windows-exe.yml

# Or if it's in duty-backup-app/.github/workflows/
ls -la duty-backup-app/.github/workflows/build-windows-exe.yml
```

**Note**: GitHub Actions requires workflows at `.github/workflows/` in the **root** of the repository.

**✅ Check**: Workflow file exists? → Continue to Step 11

---

## STEP 11: Push to GitHub

**Action**: Push your changes:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE

# Push to GitHub
git push origin main
# OR
git push origin master
# (Use your branch name)
```

**✅ Check**: Push successful? → Continue to Step 12

---

## STEP 12: Monitor GitHub Actions Build

**Action**: Check the build status:

1. Go to your GitHub repository
2. Click on **"Actions"** tab
3. Find the workflow run: **"Build Windows Executable"**
4. Click on it to see the build progress

**What to expect**:
- ✅ Workflow triggers on push
- ✅ Installs Python 3.13
- ✅ Installs dependencies
- ✅ Installs Playwright browsers
- ✅ Runs `build_standalone.py`
- ✅ Creates `duty_backup_app.exe`
- ✅ Creates ZIP package
- ✅ Uploads as artifact

**✅ Check**: Build completes successfully? → Continue to Step 13

---

## STEP 13: Download the Executable

**Action**: Download the built executable:

1. In GitHub Actions, go to the completed workflow run
2. Scroll down to **"Artifacts"** section
3. Download the ZIP file (e.g., `duty-backup-app-windows.zip`)
4. Extract it on a Windows machine
5. Run `duty_backup_app.exe`

**✅ Check**: Executable runs on Windows? → **DONE!** 🎉

---

## Troubleshooting

### Build Fails in GitHub Actions

**Check**:
- Workflow file is at `.github/workflows/build-windows-exe.yml` (root level)
- Workflow triggers on changes to `duty-backup-app/`
- All dependencies are in `requirements_standalone.txt`

### Executable Doesn't Run

**Check**:
- Running on Windows (required)
- `.env` file exists (if not using encrypted config)
- Or `config.encrypted` exists (if using encrypted config)
- Playwright browsers are bundled (should be automatic)

### Missing Files in Build

**Check**:
- Files are in `duty-backup-app/` directory
- Files are not in `.gitignore`
- Files are committed to Git

---

## Quick Reference Commands

```bash
# Full workflow (after setup)
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
git status                    # Check what will be committed
git add duty-backup-app/      # Add files
git commit -m "Your message"   # Commit
git push origin main          # Push to GitHub
```

---

## Need Help?

- Check `ENCRYPTION_GUIDE.md` for encryption details
- Check `SESSION_AND_CONFIG_FAQ.md` for session/config questions
- Check GitHub Actions logs for build errors

