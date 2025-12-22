# Duty Backup Application - User Guide

## Overview

The Duty Backup Application is a standalone Windows executable that allows you to run the NetCHB duty service locally without requiring the main FastAPI backend server. The application provides a user-friendly GUI interface matching the frontend design with dark theme, glassmorphism effects, and amber accents.

## Features

- **Authentication**: Login with your Supabase credentials
- **Duty Processing**: Process single MAWBs with full section support (AMS, Entries, Custom Report, PDF)
- **Results Viewing**: View and search processed results
- **Local Session Storage**: Broker login sessions saved locally (not in Supabase)
- **Read-Only Brokers/Formats**: Select from existing brokers/formats (managed in main app)

## Installation

### Prerequisites

- Windows 10 or later
- No Python installation required (all dependencies bundled)

### Setup Steps

1. **Extract the Application**
   - Extract `duty_backup_app.exe` and all accompanying files to a folder
   - Example: `C:\FTE-Operations\duty-backup-app\`

2. **Create Configuration File**
   - Create a file named `.env` in the same directory as the executable
   - Copy the template from `.env.example` if provided
   - Add your credentials:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

3. **Run the Application**
   - Double-click `duty_backup_app.exe`
   - The login window will appear

## Usage

### First Time Setup

1. **Launch Application**
   - Run `duty_backup_app.exe`
   - Login screen appears

2. **Login**
   - Enter your email (Supabase user email)
   - Enter your password
   - Click "Sign In"
   - Main window appears after successful authentication

### Daily Usage

1. **Launch Application**
   - Run `duty_backup_app.exe`
   - If you have a valid session, you may be auto-logged in
   - Otherwise, login screen appears

2. **Process a MAWB**
   - Go to the **Process** tab
   - Select a **Broker** from the dropdown (loaded from Supabase)
   - Select a **Format** from the dropdown (loaded from Supabase)
   - Check the sections you want to process:
     - ☑ AMS
     - ☑ Entries
     - ☑ Custom Report
     - ☐ Download 7501 PDF (optional)
   - Enter the **MAWB** number (11 digits)
   - Click **Process**
   - Watch progress in the logs area
   - Results are saved automatically

3. **View Results**
   - Go to the **Results** tab
   - View all processed results
   - Use the search box to filter by MAWB
   - Click **Refresh** to reload results

4. **Logout**
   - Click **Logout** button in the header
   - Returns to login screen

## How Everything Works

### Authentication Flow

1. **Login Process**:
   - User enters email/password in login window
   - Application sends credentials to Supabase Auth API
   - Supabase validates credentials and returns JWT token
   - Token is stored securely in `.session` file
   - Main window is displayed

2. **Session Management**:
   - JWT token stored in `.session` file (encrypted)
   - Token automatically included in all Supabase requests
   - Token refresh handled automatically
   - Logout clears token and returns to login screen

### Data Flow

#### Brokers & Formats (Read-Only)

- **Loading**: Supabase Database → Application → Dropdown Lists
- **NO Create/Update/Delete**: Users cannot modify brokers/formats in the executable
- **Management**: Brokers/formats are managed only in the main backend/frontend application
- **Selection**: Users select from dropdown lists of existing brokers/formats

#### Broker Login Sessions (Local Storage)

- **Save**: After successful NetCHB login, Playwright session state is saved to `sessions/broker_{broker_id}.json`
- **Load**: When processing a MAWB, the app checks for a local session file
- **Validation**: If session exists, it's validated by opening a protected page
- **Reuse**: If valid, session is reused (skips login)
- **NOT in Supabase**: Sessions stored locally to avoid conflicts with backend server
- **Per User**: Each executable instance has its own independent session storage

#### Duty Processing Results

- **Processing**: GUI → Service → Playwright → NetCHB Website
- **Data Extraction**: Playwright extracts data from website sections
- **Excel Reports**: Generated and uploaded to AWS S3
- **PDF Files**: Downloaded and uploaded to AWS S3
- **Results Saved**: All data saved to Supabase (`netchb_duty_results` table)
- **Artifact URLs**: S3 URLs stored in database for download
- **Shared Data**: Results are shared with the main application (same database)

#### File Storage

- **Excel Reports**: Uploaded to S3 at `netchb-duty/customizable-reports/{mawb} {airport_code} {customer}.xlsx`
- **PDF Files**: Uploaded to S3 at `netchb-duty/7501-batch-pdfs/{mawb} {airport_code} {customer}.pdf`
- **S3 URLs**: Presigned URLs generated and stored in database
- **Local Files**: Temporary files cleaned up after upload

### Configuration Storage

- **Supabase Credentials**: Stored in `.env` file
- **AWS S3 Credentials**: Stored in `.env` file
- **User Session**: JWT token stored in `.session` file
- **Broker Sessions**: Stored in `sessions/` folder as JSON files

## File Structure

```
duty-backup-app/
├── duty_backup_app.exe          # Main executable
├── .env                         # Configuration file (you create this)
├── .session                     # User authentication session
├── sessions/                    # Broker login sessions (auto-created)
│   ├── broker_{id1}.json
│   └── broker_{id2}.json
├── duty_backup_app.log          # Application log file
└── README.txt                   # Quick start guide
```

## Troubleshooting

### Login Issues

**Problem**: "Login failed. Please check your credentials"
- **Solution**: Verify your email/password are correct
- Check that your Supabase user account is active
- Ensure `.env` file has correct `SUPABASE_URL`

**Problem**: "Supabase client not initialized"
- **Solution**: Check `.env` file exists and has `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`

### Processing Issues

**Problem**: "Broker not found" or "Format not found"
- **Solution**: Brokers/formats must be created in the main application first
- Refresh the application to reload brokers/formats

**Problem**: "Failed to load brokers/formats"
- **Solution**: Check internet connection
- Verify Supabase credentials in `.env` file
- Check `duty_backup_app.log` for detailed error messages

**Problem**: Processing hangs or times out
- **Solution**: Check internet connection
- Verify NetCHB website is accessible
- Check `duty_backup_app.log` for errors
- Try clearing broker session: Delete `sessions/broker_{broker_id}.json` file

### File Upload Issues

**Problem**: "Failed to upload to S3"
- **Solution**: Verify AWS credentials in `.env` file
- Check AWS S3 bucket name and region are correct
- Ensure AWS credentials have S3 write permissions

### Session Issues

**Problem**: "Session expired" or frequent re-logins
- **Solution**: This is normal - sessions expire after inactivity
- Simply login again when prompted
- Broker sessions are separate and saved locally

## Logs

Application logs are saved to `duty_backup_app.log` in the same directory as the executable. Check this file for detailed error messages and debugging information.

## Security Notes

- **Credentials**: Never share your `.env` file or `.session` file
- **Broker Sessions**: Broker login sessions are stored locally and not shared
- **Token Storage**: JWT tokens are stored in `.session` file (keep secure)
- **Network**: All communication with Supabase and AWS uses HTTPS

## Limitations

- **Read-Only Brokers/Formats**: Cannot create/edit/delete brokers or formats in the executable
- **Single User**: Each executable instance is for one user
- **No Batch Processing UI**: Currently supports single MAWB processing (batch can be added later)
- **Windows Only**: Executable is built for Windows (can be built for Mac/Linux if needed)

## Support

For issues or questions:
1. Check `duty_backup_app.log` for error details
2. Verify `.env` configuration is correct
3. Ensure all required credentials are present
4. Contact your system administrator

## Version

Version 1.0.0





