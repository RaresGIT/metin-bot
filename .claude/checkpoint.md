# Metin Bot - Project Checkpoint

**Date:** 2025-10-10
**Project:** Metin2 Stone Farming Bot
**Location:** `c:\metin-bot\`

## Project Overview

This is a Python automation bot for Metin2 game that automatically searches for and destroys metin stones. The bot uses computer vision (PyAutoGUI + OpenCV) to detect stones on screen and automates combat, camera movement, and buff management.

## Core Files

### Main Files
- **`metin.py`** - Main bot script with game loop logic
- **`utils.py`** - Helper functions for stone detection, combat, camera movement
- **`config.json`** - Configuration file (user-created, not in repo)

### Directory Structure
```
c:\metin-bot\
├── metin.py              # Main script
├── utils.py              # Utility functions
├── config.json           # Configuration (user-created)
├── stones/               # Stone template images
│   └── *_stone.png       # e.g., blue_stone.png, red_stone.png
├── utils/                # UI element images
│   ├── hp_bar.png        # HP bar detection
│   ├── top_bar.png       # Combat UI detection
│   └── on_screen_check.png  # Inventory/UI pause detection
└── debug/                # Debug screenshots (auto-created)
```

## Dependencies Installed

```bash
pip install keyboard pyautogui pydirectinput pywin32 Pillow opencv-python screeninfo
```

**Package List:**
- `keyboard` - Keyboard input detection (ESC to exit)
- `pyautogui` - Screen capture and image recognition
- `pydirectinput` - Direct input for game controls
- `pywin32` - Windows API for window management
- `Pillow` - Image processing (PIL)
- `opencv-python` - Computer vision for template matching
- `screeninfo` - Multi-monitor support

## Features Implemented

### 1. Core Bot Functionality
- **Stone Detection** - Uses template matching to find stones on screen
- **Closest Stone Selection** - Calculates distance with aspect ratio correction
- **Auto Attack** - Clicks on stones to initiate combat
- **Camera Movement** - Rotates camera when no stones found
- **Pickup/Drop** - Presses 'Z' after combat to loot items

### 2. Combat Modes

#### Timer-Based Mode (Recommended)
- Set `WAIT_AFTER_STONE_DESTROYED > 0` in config
- Waits configured time after attacking before searching for next stone
- **No UI detection needed** - faster and more reliable
- Ignores HP/top bar checking

#### Top Bar Mode (Legacy)
- Set `WAIT_AFTER_STONE_DESTROYED = 0` in config
- Uses image recognition to detect HP/top bar
- Waits for top bar to disappear (stone destroyed)
- Includes stuck detection and unstuck logic

### 3. Multi-Monitor Support
- `MONITOR_INDEX` config option
- `0` = primary monitor, `1` = second monitor, etc.
- `null` = search all monitors (default)
- Uses `screeninfo` library to detect monitor bounds

### 4. Debug Mode
- Detailed console logging
- Screenshots saved to `debug/` folder with timestamps
- Shows configuration, monitor info, and execution flow
- Logs stone detection results and timings

### 5. Buff Auto-Refresh
- Automatically presses buff keys at regular intervals
- Randomized interval (30-60s default) for natural behavior
- Supports single keys (`"f5"`) or combos (`"ctrl+v"`)
- Configurable keys and intervals

### 6. Error Handling
- Graceful handling of `ImageNotFoundException`
- Catches low-confidence matches without crashing
- Falls back to camera movement when stones not found
- Exception handling for monitor detection failures

## Configuration Options

### config.json Structure
```json
{
  // Screen Configuration
  "CENTER_X": 960,
  "CENTER_Y": 540,
  "OFFSET_X": 70,
  "OFFSET_Y": 45,
  "ASPECT_RATIO": 1.78,

  // Combat Mode
  "WAIT_AFTER_STONE_DESTROYED": 5.0,  // 0 = top bar mode, >0 = timer mode

  // Stone Settings
  "STONE_NAMES": ["blue", "red", "gold"],  // Looks for stones/blue_stone.png, etc.

  // Features
  "PICKUP_DROP": true,
  "LURE_KEY": "",
  "DEADLINE": 10,  // Hours to run before auto-stopping

  // Multi-Monitor
  "MONITOR_INDEX": null,  // null = all monitors, 0 = primary, 1 = second, etc.

  // Buff Management
  "KEEP_BUFF_UPTIME": true,
  "BUFF_INTERVAL_MIN": 30,
  "BUFF_INTERVAL_MAX": 60,
  "BUFF_KEYS": "ctrl+v",

  // Debug
  "DEBUG": false
}
```

### Global Variables (metin.py)

**Combat Configuration:**
- `CENTER_X`, `CENTER_Y` - Screen center for distance calculations
- `OFFSET_X`, `OFFSET_Y` - Click offset from detected stone position
- `ASPECT_RATIO` - Screen aspect ratio for distance correction (16:9 = 1.78)
- `MAX_PERMITTED_STUCK_ITERATIONS` - Max unstuck attempts (3)
- `MAX_SECONDS_STUCK` - Time before considering stuck (1s)

**Bot Behavior:**
- `STONE_NAMES` - List of stone types to search for
- `PICKUP_DROP` - Auto-press Z after combat
- `LURE_KEY` - Reserved for future use
- `DEADLINE` - Hours to run before stopping
- `WAIT_AFTER_STONE_DESTROYED` - Combat mode selector

**Advanced:**
- `MONITOR_INDEX` - Target specific monitor
- `KEEP_BUFF_UPTIME` - Enable buff auto-refresh
- `BUFF_INTERVAL_MIN/MAX` - Buff timing range
- `BUFF_KEYS` - Key combination for buffs
- `DEBUG` - Enable debug logging and screenshots

## Key Functions

### metin.py Functions

**`read_config(file_path)`**
- Loads configuration from JSON file
- Updates global variables
- Called once at startup

**`destroy_closest_stone(metin_stones, offset_x, offset_y)`**
- Finds closest stone using `calculate_closest_stone()`
- Clicks on stone coordinates
- Sets `LAST_SELECTED` with timestamp

**`farm_stones(metin_stones, offset_x, offset_y)`**
- Main game logic function
- Two modes: timer-based or top bar-based
- Handles stone selection, camera movement, stuck detection
- Called every loop iteration

**`main()`**
- Main bot loop
- Handles:
  - ESC key exit
  - Deadline checking
  - Inventory/UI pause detection
  - Buff refresh timing
  - Stone search and farming

### utils.py Functions

**Image Recognition:**
- `search_stones(stone_names, debug, monitor_index)` - Find stones on screen
- `find_top_bar(debug, monitor_index)` - Detect HP/combat UI
- `get_monitor_region(monitor_index)` - Get monitor bounds
- `list_monitors(debug)` - List all available monitors

**Combat & Movement:**
- `attack_stone(stone_coords)` - Move mouse and click stone
- `unstuck(coords, center_x, center_y)` - Attempt to unstuck character
- `move_camera()` - Rotate camera and move forward
- `calculate_closest_stone(...)` - Find nearest stone with distance formula

**Buff Management:**
- `press_buff_keys(buff_keys)` - Press key combo for buffs

**Utilities:**
- `log(msg)` - Timestamped console logging
- `ensure_debug_folder()` - Create debug directory
- `save_debug_screenshot(image, filename)` - Save debug images

**Window Management:**
- `global_to_client(hwnd, x, y)` - Screen to client coords
- `send_click(global_x, global_y)` - Send click to window
- `send_click_relative(local_x, local_y, hwnd)` - Relative click

## Bot Flow Logic

### Main Loop (Simplified)
```
1. Check ESC key → Exit if pressed
2. Check deadline → Stop if time exceeded
3. Check inventory UI → Pause if open
4. Check buff timer → Refresh buffs if needed
5. Search for stones → search_stones()
6. Farm stones → farm_stones()
7. Sleep 0.5s
8. Repeat
```

### Timer-Based Mode Flow
```
If LAST_SELECTED is set:
  If wait_time elapsed:
    → Clear selection
    → Press Z to pickup
    → Search for new stone
  Else:
    → Wait (don't search yet)

If LAST_SELECTED is None:
  If stones found:
    → Attack closest stone
  Else:
    → Move camera to search
```

### Top Bar Mode Flow
```
Check HP/top bar:
  If top_bar disappeared:
    → Clear selection
    → Press Z to pickup
  If top_bar visible + stuck:
    → Run unstuck logic
  If no top_bar + stones found + no selection:
    → Attack closest stone
  If no top_bar + no stones:
    → Move camera to search
```

## Important Notes

### Image Recognition
- **Confidence threshold:** 0.7 for stones, 0.9 for HP bar, 0.9 for UI check
- **Grayscale matching** used for better performance
- **Region-based search** for multi-monitor support
- **Exception handling** for low-confidence matches

### Stuck Detection
- Only active in top bar mode
- Checks if stone hasn't taken damage after `MAX_SECONDS_STUCK`
- Attempts movement (W/A/D keys) to unstuck
- Max 3 attempts before selecting new stone

### Randomization
- Buff intervals randomized between min/max
- Unstuck movement timings randomized (0.05-0.08s)
- Camera movement forward time randomized (0.25-0.75s)

### Keyboard Controls
- **ESC** - Emergency stop (exits script)
- All other keys controlled by pydirectinput

## Recent Changes & Fixes

### Session 1 (2025-10-10)

1. **Package Installation**
   - Installed all required dependencies
   - Fixed Pillow missing error
   - Fixed OpenCV missing error

2. **Debug Mode Implementation**
   - Added DEBUG configuration
   - Screenshot capture to debug/ folder
   - Detailed logging throughout execution
   - Monitor detection logging

3. **Timer-Based Combat Mode**
   - Added WAIT_AFTER_STONE_DESTROYED config
   - Implemented dual-mode system (timer vs top bar)
   - Bypasses UI detection for faster operation

4. **Multi-Monitor Support**
   - Added MONITOR_INDEX configuration
   - Integrated screeninfo library
   - Region-based search for specific monitors
   - Fallback to all monitors if index invalid

5. **Image Not Found Fix**
   - Added exception handling for ImageNotFoundException
   - Catches pyscreeze.ImageNotFoundException
   - Returns empty list instead of crashing
   - Bot continues with camera movement

6. **Buff Auto-Refresh Feature**
   - Added KEEP_BUFF_UPTIME toggle
   - Configurable buff keys and intervals
   - Randomized timing for natural behavior
   - Key combination support (ctrl+v, alt+f1, etc.)

## Common Issues & Solutions

### Issue: "Could not locate the image (highest confidence = 0.189)"
**Solution:** Now handled gracefully - bot will move camera and keep searching

### Issue: Bot searches wrong monitor
**Solution:** Set `MONITOR_INDEX` in config.json (0 for primary, 1 for second, etc.)

### Issue: Bot too slow between stones
**Solution:** Use timer-based mode (`WAIT_AFTER_STONE_DESTROYED > 0`) instead of top bar mode

### Issue: Need to find template images
**Solution:**
1. Take screenshot of game
2. Crop image to just the stone/UI element
3. Save to appropriate folder with correct naming

### Issue: Bot clicks wrong position on stone
**Solution:** Adjust `OFFSET_X` and `OFFSET_Y` in config to fine-tune click position

## Development Environment

- **OS:** Windows (win32)
- **Python:** 3.12
- **Working Directory:** `C:\metin-bot`
- **Game Window:** "Honor2.net!" (hardcoded in utils.py line 15)

## Future Enhancement Ideas

- Multiple buff key sequences
- Potion auto-use based on HP detection
- Discord webhook notifications
- Statistics tracking (stones destroyed, time elapsed)
- GUI configuration editor
- Auto-restart on disconnect
- Path recording for movement between zones

## How to Resume Development

1. **Read this checkpoint** to understand current state
2. **Check config.json** for current configuration
3. **Review metin.py** for main game loop
4. **Review utils.py** for helper functions
5. **Enable DEBUG mode** to see detailed execution flow
6. **Check debug/ folder** for recent screenshots if issues

## Quick Start Commands

```bash
# Navigate to project
cd C:\metin-bot

# Run the bot
python metin.py

# Emergency stop
# Press ESC key while bot is running
```

## Testing Checklist

When making changes, test:
- [ ] Stone detection works
- [ ] Camera moves when no stones found
- [ ] Combat completes and moves to next stone
- [ ] ESC key exits gracefully
- [ ] DEBUG mode shows useful information
- [ ] Multi-monitor targeting works
- [ ] Buff keys press correctly
- [ ] Exception handling doesn't crash bot

---

**Last Updated:** 2025-10-10
**Status:** Fully Functional
**Next Session:** Ready to resume with any enhancements or bug fixes needed
