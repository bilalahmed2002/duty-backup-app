# Duty Backup App - Standalone GUI for NetCHB Duty Service

A standalone Windows GUI application for processing NetCHB duty requests, functioning as a backup without relying on the main FastAPI backend server.

## Features

- 🔐 **Supabase Authentication** - Email/password login
- 💾 **Local Session Storage** - Broker login sessions saved locally (per broker)
- 📊 **Process Tab** - Select broker/format, add MAWBs, select sections, process
- 📈 **Results Tab** - View current session results, export Excel, download reports/PDFs
- 🔍 **Search Tab** - Search historical MAWBs and download reports/PDFs
- 🔒 **Encrypted Config** - Secure credential bundling for employee distribution
- 🪟 **Windows Executable** - Standalone `.exe` file (built via GitHub Actions)

## Quick Start

### For Users

1. Download the latest release from GitHub Actions
2. Extract the ZIP file
3. Run `duty_backup_app.exe`
4. Login with your Supabase credentials

### For Developers

See `GIT_SETUP.md` for setting up the repository and `DEPLOYMENT_STEPS.md` for building the executable.

## Repository Structure

```
duty-backup-app/
├── .github/workflows/        # GitHub Actions build workflow
├── auth/                     # Authentication (Supabase)
├── gui/                      # PyQt6 GUI components
├── service/                  # Business logic (duty processing)
├── utils/                    # Utilities (parsing, styles)
├── main.py                   # Application entry point
├── build_standalone.py       # PyInstaller build script
└── requirements_standalone.txt
```

## Requirements

- Python 3.13+
- Windows (for executable)
- Supabase account
- AWS S3 access (for file storage)

## Backend Dependency

This app requires `FTE-Operations-backend` to be available as a sibling directory during development/build:

```
OPERATIONS-FTE/
├── duty-backup-app/          ← This repo
└── FTE-Operations-backend/   ← Required for imports
```

For GitHub Actions builds, the backend is automatically checked out if available.

## Configuration

Create a `.env` file (or use encrypted `config.encrypted`):

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET_NAME=your_bucket
AWS_REGION=us-east-1
```

See `.env.example` for template.

## Security

- `.env` files are **never** committed (in `.gitignore`)
- Encrypted config (`config.encrypted`) can be bundled for employee distribution
- Broker sessions stored locally in `sessions/` (not committed)
- See `ENCRYPTION_GUIDE.md` for encryption details

## Building

The Windows executable is built automatically via GitHub Actions on push to `main`/`master`.

To build manually:

```bash
python build_standalone.py
```

## Documentation

- `GIT_SETUP.md` - Setting up this repository
- `DEPLOYMENT_STEPS.md` - Step-by-step deployment guide
- `ENCRYPTION_GUIDE.md` - Encrypted configuration guide
- `SESSION_AND_CONFIG_FAQ.md` - FAQ about sessions and config
- `QUICK_START_GIT.md` - Quick git setup reference

## License

[Your License Here]



