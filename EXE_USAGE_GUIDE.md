# 📦 Using the Built Executable - Complete Guide

## Step 1: Download the Executable

### From GitHub Actions:

1. Go to your GitHub repository
2. Click on **"Actions"** tab
3. Find the latest successful workflow run (green checkmark)
4. Scroll down to **"Artifacts"** section
5. Click **"duty-backup-app-windows"** to download
6. Extract the ZIP file

### What You'll Get:

```
duty-backup-app-windows/
├── duty_backup_app.exe          ← Main executable
├── _internal/                    ← Required libraries
│   ├── Python runtime
│   ├── PyQt6 libraries
│   ├── Playwright browsers
│   └── All dependencies
├── *.dll                         ← Windows DLLs
├── .env.example                  ← Configuration template
└── README.txt                    ← Usage instructions
```

---

## Step 2: Setup Configuration

### Option A: Using Encrypted Config (If Bundled)

If `config.encrypted` is included, the app will automatically decrypt it on first run.

**No action needed** - just run the executable!

### Option B: Create .env File (Manual Setup)

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   AWS_S3_BUCKET_NAME=your_bucket_name
   AWS_REGION=us-east-1
   ```

**⚠️ Important**: Never share `.env` file - it contains secrets!

---

## Step 3: Run the Application

### Windows:

1. **Double-click** `duty_backup_app.exe`
   - OR right-click → "Run as administrator" (if needed)

2. **First Launch**:
   - Application window should open
   - Login window appears

3. **Login**:
   - Enter your Supabase email
   - Enter your password
   - Click "Login"

4. **Main Window**:
   - **Process Tab**: Select broker/format, add MAWBs, process
   - **Results Tab**: View processed results, download reports
   - **Search Tab**: Search historical MAWBs

---

## Step 4: Using the Application

### Process a MAWB:

1. Go to **"Process"** tab
2. Select **Broker** from dropdown
3. Select **Format** from dropdown
4. Check sections to process (AMS, Entries, Custom)
5. Enter MAWB in input field (or paste multiple):
   ```
   JFK HYJ M3 3391 160-05034083
   JFK BFE M3 1328 205-32304296
   ```
6. Click **"Parse & Add"**
7. Review parsed items in table
8. Click **"Process"** button
9. Wait for processing to complete

### View Results:

1. Go to **"Results"** tab
2. See all processed MAWBs in table
3. Click **"Download Excel"** to export
4. Click **"Download PDF"** to get PDF report
5. Click **"Download Report"** to get Excel report

### Search Historical MAWBs:

1. Go to **"Search"** tab
2. Enter MAWB number
3. Click **"Search"**
4. View results and download files

---

## Step 5: Distribution to Employees

### Method 1: Share ZIP File

1. Download artifact ZIP from GitHub Actions
2. Upload to secure location (OneDrive, Google Drive, etc.)
3. Share download link with employees
4. Employees extract and run

### Method 2: Create Installer (Optional)

For easier distribution, you can create an installer using:
- **Inno Setup** (free)
- **NSIS** (free)
- **Advanced Installer** (paid)

### Method 3: Network Share

1. Place EXE folder on network drive
2. Employees run from network location
3. Or copy to their local machines

---

## Step 6: Troubleshooting

### "Application won't start"

**Solution**:
- Check Windows Defender / Antivirus (may block first run)
- Right-click → "Run as administrator"
- Check Windows Event Viewer for errors

### "Configuration Error"

**Solution**:
- Ensure `.env` file exists in same folder as `.exe`
- Check `.env` has all required keys
- Verify no typos in `.env` file

### "Login Failed"

**Solution**:
- Verify Supabase credentials in `.env`
- Check internet connection
- Verify Supabase URL is correct

### "Playwright browser not found"

**Solution**:
- This shouldn't happen (browsers are bundled)
- If it does, re-download the artifact
- Check `_internal/` folder exists

### "File download failed"

**Solution**:
- Check AWS credentials in `.env`
- Verify S3 bucket name is correct
- Check AWS permissions

---

## Step 7: Updates

### When New Version is Available:

1. Download new artifact from GitHub Actions
2. **Backup** your `.env` file
3. Extract new version
4. Copy `.env` to new folder
5. Run new executable

**Note**: Your `.env` and `sessions/` folder are preserved locally.

---

## File Locations

### Application Files:
```
C:\Users\YourName\Desktop\duty-backup-app\
├── duty_backup_app.exe
├── .env                    ← Your config (create this)
├── .env.example            ← Template
├── duty_backup_app.log     ← Log file (created on run)
└── sessions/              ← Broker sessions (created on use)
    └── broker_*.json
```

### Log File:
- Location: Same folder as `.exe`
- Name: `duty_backup_app.log`
- Contains: Application logs, errors, debug info

---

## Security Notes

### ✅ Safe to Share:
- `duty_backup_app.exe`
- `_internal/` folder
- `.env.example`
- `README.txt`

### ❌ NEVER Share:
- `.env` file (contains secrets)
- `sessions/` folder (contains broker login sessions)
- `duty_backup_app.log` (may contain sensitive info)

---

## Quick Start Checklist

- [ ] Downloaded artifact ZIP from GitHub Actions
- [ ] Extracted ZIP file
- [ ] Created `.env` file (or using encrypted config)
- [ ] Added Supabase credentials to `.env`
- [ ] Added AWS credentials to `.env`
- [ ] Double-clicked `duty_backup_app.exe`
- [ ] Logged in successfully
- [ ] Tested processing a MAWB

---

## Support

If you encounter issues:

1. Check `duty_backup_app.log` file
2. Verify `.env` configuration
3. Check GitHub Actions build logs
4. Review error messages in application

---

## Next Steps After Setup

1. **Test with sample MAWB** to verify everything works
2. **Train employees** on how to use the application
3. **Set up regular updates** (download new versions from GitHub Actions)
4. **Monitor logs** for any issues

---

**🎉 You're all set! The application is ready to use.**

