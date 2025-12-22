# 🔧 Build Fix: Missing utils/styles.py

## Problem
The executable was failing with:
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\...\\_MEI240362\\utils\\styles.py'
```

## Root Cause
`utils/styles.py` is loaded dynamically using `importlib.util.spec_from_file_location()`, which PyInstaller doesn't detect automatically. The file needs to be explicitly bundled.

## Solution
Updated `build_standalone.py` to bundle the entire `utils/` directory:

```python
# Bundle entire utils directory (required for dynamic imports like styles.py)
utils_dir = APP_DIR / "utils"
if utils_dir.exists():
    utils_str = str(utils_dir.resolve()).replace("\\", "/")
    datas_list.append(f"(r'{utils_str}', 'utils')")
```

Also added to `hiddenimports`:
```python
'utils.styles',
'utils.mawb_parser',
```

## Files Changed
- `build_standalone.py` - Added utils directory to datas list
- `build_standalone.py` - Added utils modules to hiddenimports

## Next Steps
1. Commit the fix
2. Push to GitHub
3. Wait for GitHub Actions to rebuild
4. Download new executable
5. Test again

The new build should include `utils/styles.py` and work correctly!

