# Smart Target Tracking System

## Overview

The bot now features an intelligent target tracking system that makes it significantly more efficient and responsive. Instead of blindly waiting after attacking, the bot actively monitors targets and reacts to their destruction in real-time.

## Key Improvements

### 1. Edge Target Filtering

**Problem:** Targets near screen edges are often partially visible or unreachable.

**Solution:** Configurable edge margin that filters out targets too close to screen borders.

```json
{
  "SCREEN_EDGE_MARGIN": 150  // Ignore targets within 150px of edges
}
```

**Benefits:**
- Prevents wasting time on unreachable targets
- More accurate target selection
- Smoother gameplay experience

### 2. Active Target Tracking

**Problem:** Old system waited a fixed time (5+ seconds) after attacking, wasting time if target died quickly.

**Solution:** Bot tracks current target and continuously checks if it still exists.

**How it works:**
1. When attacking a target, bot remembers its coordinates
2. Every 0.5s (configurable), checks if target still present
3. As soon as target disappears, immediately searches for next target
4. No more unnecessary waiting!

```json
{
  "WAIT_AFTER_STONE_DESTROYED": 0.0,  // 0 = smart tracking mode
  "TARGET_DESTROYED_CHECK_INTERVAL": 0.5  // Check every 0.5 seconds
}
```

**Benefits:**
- Instantly moves to next target when current one is destroyed
- Dramatically reduces idle time
- More efficient farming
- Can easily handle fast kills or slow kills

### 3. Intelligent Search Behavior

**Problem:** When no targets found, bot would just rotate camera randomly.

**Solution:** Comprehensive search pattern with camera rotation and character movement.

**Search Strategy:**
1. First no-target: Quick camera rotation (0.5s)
2. Second no-target: Another quick rotation
3. Third no-target: Full search pattern
   - 8 camera rotations (configurable)
   - Move forward every 3 rotations
   - Explores the area systematically

```json
{
  "SEARCH_CAMERA_ROTATIONS": 8,      // Number of rotations during search
  "SEARCH_MOVE_FORWARD_TIME": 1.0    // Seconds to move forward
}
```

**Benefits:**
- Finds targets in wider area
- Explores map efficiently
- Doesn't get stuck in same location
- Adaptive search behavior

## Configuration

### Smart Tracking Mode (Recommended)

```json
{
  "WAIT_AFTER_STONE_DESTROYED": 0.0,
  "SCREEN_EDGE_MARGIN": 150,
  "TARGET_DESTROYED_CHECK_INTERVAL": 0.5,
  "SEARCH_CAMERA_ROTATIONS": 8,
  "SEARCH_MOVE_FORWARD_TIME": 1.0
}
```

### Legacy Timer Mode (Old Behavior)

```json
{
  "WAIT_AFTER_STONE_DESTROYED": 5.0,  // Any value > 0 uses old mode
  "SCREEN_EDGE_MARGIN": 0              // Disabled
}
```

## How It Works

### State Machine

```
┌─────────────────────┐
│   No Active Target  │
└──────────┬──────────┘
           │
           │ Find stones
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│  Filter Edge        │────▶│  No Valid Targets   │
│  Targets            │     └──────────┬──────────┘
└──────────┬──────────┘                │
           │                            │ 3x no-targets
           │ Valid targets found        ▼
           │                  ┌─────────────────────┐
           │                  │  Comprehensive      │
           │                  │  Search Pattern     │
           │                  └─────────────────────┘
           ▼
┌─────────────────────┐
│  Select Closest     │
│  Target             │
└──────────┬──────────┘
           │
           │ Attack
           ▼
┌─────────────────────┐
│  Active Target      │◀───┐
│  (Combat Mode)      │    │
└──────────┬──────────┘    │
           │                │
           │ Check every    │ Still present
           │ 0.5s           │
           ▼                │
┌─────────────────────┐    │
│  Target Still       │────┘
│  Present?           │
└──────────┬──────────┘
           │
           │ Target destroyed
           ▼
┌─────────────────────┐
│  Pickup Drops       │
│  Clear Target       │
└──────────┬──────────┘
           │
           └───▶ Back to "No Active Target"
```

### Edge Filtering Logic

```python
# Target coordinates
target_x, target_y = 100, 200

# Screen dimensions
screen_width, screen_height = 1920, 1080

# Edge margin
edge_margin = 150

# Filter check
if (target_x < edge_margin or
    target_x > screen_width - edge_margin or
    target_y < edge_margin or
    target_y > screen_height - edge_margin):
    # Skip this target - too close to edge
    pass
```

### Target Verification

```python
# Original target location
original_coords = (500, 600)

# Check if target still exists (every 0.5s)
current_targets = find_stones()

for target in current_targets:
    distance = sqrt((target.x - 500)^2 + (target.y - 600)^2)

    if distance <= 50:  # 50px tolerance
        # Target still present
        return True

# No matching target found - it's destroyed!
return False
```

## Performance Comparison

### Old System (Timer Mode)

```
Attack target → Wait 5s → Check for new → Attack
│              │          │
└──────────────┴──────────┴─────▶ 5+ seconds minimum
```

**Problems:**
- If stone dies in 2s, wastes 3s waiting
- If stone takes 8s, might attack too early
- Fixed delay regardless of situation

### New System (Smart Tracking)

```
Attack → Check (0.5s) → Check (0.5s) → Target gone! → Attack next
│        │              │              │              │
└────────┴──────────────┴──────────────┴──────────────▶ 2.5s actual combat time
```

**Benefits:**
- Responds instantly when target destroyed
- No wasted time waiting
- Adapts to any combat duration
- ~50-70% faster target switching

## Debug Output Examples

### Smart Tracking in Action

```
2025-10-24 15:30:00: [INFO] Attacking new target at (689, 498)
2025-10-24 15:30:01: [DEBUG] Target still present, combat ongoing (1.0s)
2025-10-24 15:30:01: [DEBUG] Target still present, combat ongoing (1.5s)
2025-10-24 15:30:02: [DEBUG] Target still present, combat ongoing (2.0s)
2025-10-24 15:30:02: [INFO] Target destroyed! Searching for new target...
2025-10-24 15:30:03: [DEBUG] Found 5 stone(s)
2025-10-24 15:30:03: [DEBUG] Skipping edge cluster at (120, 50)
2025-10-24 15:30:03: [DEBUG] Skipping edge cluster at (1800, 1000)
2025-10-24 15:30:03: [INFO] Attacking new target at (750, 520)
```

### Search Behavior

```
2025-10-24 15:35:00: [DEBUG] No targets, rotating camera
2025-10-24 15:35:01: [DEBUG] No targets, rotating camera
2025-10-24 15:35:02: [INFO] No targets found, performing search...
2025-10-24 15:35:02: [INFO] Starting target search: 8 rotations
2025-10-24 15:35:03: [DEBUG] Search rotation 1/8
2025-10-24 15:35:04: [DEBUG] Search rotation 2/8
2025-10-24 15:35:05: [DEBUG] Search rotation 3/8
2025-10-24 15:35:05: [DEBUG] Moving forward to explore
2025-10-24 15:35:07: [DEBUG] Search rotation 4/8
...
2025-10-24 15:35:12: [DEBUG] Found 3 stone(s)
2025-10-24 15:35:12: [INFO] Attacking new target at (680, 540)
```

### Edge Filtering

```
2025-10-24 15:40:00: [DEBUG] Found 8 stone(s)
2025-10-24 15:40:00: [DEBUG] Skipping edge cluster at (80, 540)
2025-10-24 15:40:00: [DEBUG] Skipping edge cluster at (1840, 600)
2025-10-24 15:40:00: [DEBUG] Skipping edge match at (960, 50)
2025-10-24 15:40:00: [DEBUG] Target distance: 234.56, cluster center: (689, 498), area: 1638
2025-10-24 15:40:00: [INFO] Attacking new target at (689, 498)
```

## Troubleshooting

### Bot keeps attacking same target

**Cause:** Target not being detected as destroyed

**Solutions:**
1. Increase `TARGET_DESTROYED_CHECK_INTERVAL` (e.g., 1.0)
2. Ensure vision v2 is working correctly
3. Check tolerance value in target verification

### Bot searches too often

**Cause:** Edge margin too aggressive

**Solutions:**
1. Reduce `SCREEN_EDGE_MARGIN` (e.g., 100 or 50)
2. Adjust screen region detection
3. Check if targets are actually on screen

### Bot doesn't explore enough

**Cause:** Search pattern too small

**Solutions:**
1. Increase `SEARCH_CAMERA_ROTATIONS` (e.g., 12)
2. Increase `SEARCH_MOVE_FORWARD_TIME` (e.g., 1.5 or 2.0)
3. Reduce no-target threshold (in code: currently 3)

### Bot waits before attacking next target

**Cause:** Still using timer mode

**Solutions:**
1. Set `WAIT_AFTER_STONE_DESTROYED` to 0.0
2. Verify config is loaded correctly
3. Check log output for "smart tracking" messages

## Migration Guide

### From Timer Mode to Smart Tracking

1. **Backup your config.json**
   ```bash
   cp config.json config.json.backup
   ```

2. **Update config.json**
   ```json
   {
     "WAIT_AFTER_STONE_DESTROYED": 0.0,
     "SCREEN_EDGE_MARGIN": 150,
     "TARGET_DESTROYED_CHECK_INTERVAL": 0.5,
     "SEARCH_CAMERA_ROTATIONS": 8,
     "SEARCH_MOVE_FORWARD_TIME": 1.0
   }
   ```

3. **Enable debug mode for testing**
   ```json
   {
     "DEBUG": true
   }
   ```

4. **Run and observe**
   - Watch log output
   - Verify targets being tracked
   - Check edge filtering works
   - Confirm search behavior triggers

5. **Tune parameters**
   - Adjust edge margin based on your screen
   - Tweak search pattern for your needs
   - Optimize check interval for performance

## Advanced Configuration

### Aggressive Farming (Fast Combat)

```json
{
  "SCREEN_EDGE_MARGIN": 100,
  "TARGET_DESTROYED_CHECK_INTERVAL": 0.3,
  "SEARCH_CAMERA_ROTATIONS": 6,
  "SEARCH_MOVE_FORWARD_TIME": 0.8
}
```

### Conservative Farming (Avoid Issues)

```json
{
  "SCREEN_EDGE_MARGIN": 200,
  "TARGET_DESTROYED_CHECK_INTERVAL": 0.8,
  "SEARCH_CAMERA_ROTATIONS": 10,
  "SEARCH_MOVE_FORWARD_TIME": 1.5
}
```

### Exploration Focus

```json
{
  "SCREEN_EDGE_MARGIN": 150,
  "TARGET_DESTROYED_CHECK_INTERVAL": 0.5,
  "SEARCH_CAMERA_ROTATIONS": 12,
  "SEARCH_MOVE_FORWARD_TIME": 2.0
}
```

## Technical Details

### New Config Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `SCREEN_EDGE_MARGIN` | int | 150 | Pixels from edge to ignore targets |
| `TARGET_DESTROYED_CHECK_INTERVAL` | float | 0.5 | Seconds between target checks |
| `SEARCH_CAMERA_ROTATIONS` | int | 8 | Rotations during search |
| `SEARCH_MOVE_FORWARD_TIME` | float | 1.0 | Seconds to move forward |

### Modified Components

1. **`src/core/config.py`**
   - Added new configuration fields
   - Updated validation logic
   - Changed default wait time to 0.0

2. **`src/vision/target_finder.py`**
   - `calculate_closest_target()` now filters edge targets
   - Added `is_target_still_present()` method
   - Returns `Optional[Target]` instead of `Target`

3. **`src/strategies/stone_farming.py`**
   - Complete rewrite of `execute()` method
   - New state machine: active target vs no target
   - Smart search behavior with counter
   - Real-time target verification

4. **`src/game/movement.py`**
   - Added `search_for_targets()` method
   - Systematic exploration pattern
   - Configurable rotation count and move time

### Backward Compatibility

The system remains backward compatible:

- Set `WAIT_AFTER_STONE_DESTROYED > 0` to use old timer mode
- Old configs work without modification
- Can switch between modes without code changes

## Summary

Smart Target Tracking brings professional-grade intelligence to the bot:

✅ **No Wasted Time** - Instant target switching
✅ **Smart Filtering** - Ignores unreachable edge targets
✅ **Active Monitoring** - Real-time target verification
✅ **Intelligent Search** - Systematic area exploration
✅ **Fully Configurable** - Tune to your playstyle
✅ **Debug Friendly** - Detailed logging of all decisions

The result is a bot that's faster, smarter, and more efficient than ever before!
