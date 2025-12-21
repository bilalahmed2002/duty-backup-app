# Quick Start - Testing the Application

## Quick Setup (3 Steps)

### Step 1: Install Dependencies

Run the setup script:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
./setup_test.sh
```

Or manually:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_standalone.txt
playwright install chromium
```

### Step 2: Create .env File

Copy your backend `.env` file or create a new one with these required values:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/duty-backup-app
cp ../FTE-Operations-backend/.env .env
```

Or create manually with minimum required values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
# OR
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

### Step 3: Test and Run

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Test imports
python test_imports.py

# Run the application
python test_app.py
```

## What You Should See

1. **Login Window**: Dark theme window with email/password fields
2. **After Login**: Main window with Process, Results, Settings tabs
3. **Process Tab**: Broker/Format dropdowns, section checkboxes, MAWB input
4. **Results Tab**: Table of processed results

## Troubleshooting

**"No module named 'PyQt6'"**
→ Run: `pip install PyQt6`

**"Configuration Error"**
→ Check `.env` file exists and has all required keys

**"Backend imports failed"**
→ Make sure `FTE-Operations-backend` directory exists at the same level

**"Playwright browser not found"**
→ Run: `playwright install chromium`

## Files Created During Testing

- `duty_backup_app.log` - Application logs
- `sessions/broker_*.json` - Local broker session files
- `.session` - User authentication session

## Next: Build Executable

Once testing is successful:

```bash
cd /Users/bilalahmed/Desktop/OPERATIONS-FTE/FTE-Operations-backend
python build_standalone.py
```

The executable will be in: `duty-backup-app/dist/duty_backup_app.exe`



