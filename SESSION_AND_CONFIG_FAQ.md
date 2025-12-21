# Session & Configuration FAQ

## 1. Broker Sessions - Are Old Sessions Replaced?

**YES** ✅ - Old broker sessions are automatically replaced to avoid storage bloat.

### How It Works:

- Each broker has **one session file**: `sessions/broker_{broker_id}.json`
- When a new session is saved, it **overwrites** the old file (using `'w'` mode)
- No accumulation of old sessions - only the latest session is kept
- Matches backend behavior: sessions are updated, not appended

### Example:
```
sessions/
  ├── broker_123e4567-e89b-12d3-a456-426614174000.json  (Broker 1 - latest session)
  ├── broker_223e4567-e89b-12d3-a456-426614174001.json  (Broker 2 - latest session)
  └── ...
```

Each file contains only the **most recent** session state for that broker.

---

## 2. Safer Approach for Bundling .env (Employee Distribution)

Since you're distributing to **employees only** (not public), we've implemented an **encrypted configuration** system.

### ✅ Solution: Encrypted Config Bundling

Instead of bundling plain `.env` (unsafe), we now:

1. **Encrypt** `.env` → `config.encrypted` (using Fernet encryption)
2. **Bundle** `config.encrypted` into the executable
3. **Auto-decrypt** at runtime (transparent to users)

### Security Level:

- ✅ **Better than plain text**: Credentials are encrypted
- ⚠️ **Not perfect**: Encryption key is embedded in code (can be extracted)
- ✅ **Suitable for**: Internal employee distribution, low-to-medium security needs
- ❌ **Not suitable for**: Public distribution, high-security requirements

### How to Use:

#### Automatic (Recommended):
```bash
cd duty-backup-app
# Just have .env file present
python build_standalone.py
# Build script automatically encrypts and bundles it
```

#### Custom Encryption Key (More Secure):
```bash
# Generate a unique key
python -c "from service.encrypted_config import generate_encryption_key; generate_encryption_key()"

# Set it as environment variable
export ENCRYPTION_KEY='your_generated_key_here'

# Build
python build_standalone.py
```

### Files:

- `.env` - Plain text (DO NOT commit, DO NOT bundle)
- `config.encrypted` - Encrypted config (DO NOT commit, CAN bundle)
- `.env.example` - Template (safe to commit)

### What Happens at Runtime:

1. App looks for `config.encrypted` first
2. If found, decrypts it automatically
3. Falls back to `.env` if encrypted config not found
4. Users don't need to do anything - it just works!

---

## Alternative Approaches (If Needed)

If encrypted config doesn't meet your security needs:

### Option A: Employees Create Their Own .env
- Bundle only `.env.example` (template)
- Employees copy it to `.env` and fill in credentials
- Most secure, but requires manual setup

### Option B: Windows Registry (Windows Only)
- Store credentials in Windows Registry
- More secure, but Windows-specific

### Option C: Environment Variables
- IT sets environment variables on employee machines
- Very secure, but requires IT setup

---

## Summary

✅ **Sessions**: Automatically replaced (no storage bloat)  
✅ **Config**: Encrypted bundling for employee distribution  
✅ **Security**: Reasonable protection for internal use  
⚠️ **Note**: Not perfect security (key can be extracted), but suitable for employees

See `ENCRYPTION_GUIDE.md` for detailed encryption instructions.


