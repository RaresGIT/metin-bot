# Adding Poetry to PATH

Poetry is installed but not in your system PATH. Here's how to fix it:

## Option 1: Automated Script (Recommended)

Run the provided batch script:

```batch
add_poetry_to_path.bat
```

This will permanently add Poetry to your user PATH.

**After running the script:**
1. Close and reopen your terminal/PowerShell/Command Prompt
2. Verify by running: `poetry --version`
3. You should see: `Poetry (version 2.2.1)`

## Option 2: Manual Setup (GUI)

1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", select "Path" and click "Edit"
5. Click "New" and add this path:
   ```
   C:\Users\Rares\AppData\Roaming\Python\Python313\Scripts
   ```
6. Click "OK" on all dialogs
7. Restart your terminal

## Option 3: PowerShell Command (Administrator)

Run PowerShell as Administrator and execute:

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";C:\Users\Rares\AppData\Roaming\Python\Python313\Scripts",
    "User"
)
```

Then restart your terminal.

## Verification

After restarting your terminal, verify the installation:

```batch
poetry --version
poetry env info
```

## Current Workaround (No Restart Needed)

Until you restart your terminal, you can use:

```batch
# Instead of: poetry install
python -m poetry install

# Instead of: poetry shell
python -m poetry shell

# Instead of: poetry run
python -m poetry run
```

Or use the helper scripts:
- `activate.bat` - Activate virtual environment
- `run.bat` - Run the bot directly
