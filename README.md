# Metin2 Bot

Automated Metin2 stone farming bot with computer vision and clean architecture.

## Features

- 🎯 **Stone Farming** - Automatically detect and destroy metin stones
- ⛏️ **Ore Mining** - Mine ore nodes with precision
- 🏰 **Dungeon Runner** - Automate dungeon runs
- 🖥️ **Multi-Monitor** - Support for multiple displays
- 🔄 **Auto Buffs** - Automatic buff refresh with randomized timing
- 🐛 **Debug Mode** - Detailed logging and screenshot capture
- 🏗️ **Clean Architecture** - Layered design with dependency injection

## Architecture

```
src/
├── core/          # Configuration, state, logging
├── vision/        # Computer vision and target detection
├── input/         # Keyboard and mouse abstraction
├── game/          # Combat, movement, buff management
├── strategies/    # Bot strategies (farming, mining, dungeons)
├── bot.py         # Main orchestrator
└── main.py        # Entry point
```

## Installation

### Prerequisites

- Python 3.12 or higher
- Windows OS (uses Win32 API)
- Poetry (recommended) or pip

### Using Poetry (Recommended)

```bash
# Install dependencies
python -m poetry install

# Activate virtual environment (Windows)
.\.venv\Scripts\activate

# Or use Poetry shell
python -m poetry shell

# Run the bot
python -m poetry run metin-bot

# Or directly if venv is activated
python src/main.py
```

**Note:** If `poetry` command isn't recognized, always use `python -m poetry` instead.

### Using pip

```bash
# Install dependencies
pip install keyboard pyautogui pydirectinput pywin32 Pillow opencv-python screeninfo

# Run the bot
python src/main.py
```

## Configuration

Create a `config.json` file in the project root:

```json
{
  "CENTER_X": 960,
  "CENTER_Y": 540,
  "OFFSET_X": 90,
  "OFFSET_Y": 50,
  "ASPECT_RATIO": 1.78,
  "STONE_NAMES": ["blue", "red", "gold"],
  "PICKUP_DROP": true,
  "LURE_KEY": "",
  "DEADLINE": 10,
  "DEBUG": false,
  "WAIT_AFTER_STONE_DESTROYED": 5,
  "MONITOR_INDEX": null,
  "BUFF_KEYS": "ctrl+v",
  "KEEP_BUFF_UPTIME": true,
  "BUFF_INTERVAL_MIN": 30,
  "BUFF_INTERVAL_MAX": 60
}
```

### Configuration Options

- **CENTER_X/Y** - Screen center coordinates for distance calculations
- **OFFSET_X/Y** - Click offset from detected stone position
- **ASPECT_RATIO** - Screen aspect ratio (16:9 = 1.78)
- **STONE_NAMES** - List of stone types to search for
- **PICKUP_DROP** - Auto-press Z after combat
- **DEADLINE** - Hours to run before stopping
- **WAIT_AFTER_STONE_DESTROYED** - Combat mode (0 = UI detection, >0 = timer)
- **MONITOR_INDEX** - Target specific monitor (null = all)
- **BUFF_KEYS** - Key combination for buffs
- **KEEP_BUFF_UPTIME** - Enable auto buff refresh
- **DEBUG** - Enable debug logging and screenshots

## Usage

### Stone Farming

```bash
poetry run metin-bot

# Or with Python
python src/main.py
```

### Ore Mining

```python
from src.bot import MetinBot

bot = MetinBot.create_ore_mining_bot("config.json")
bot.run()
```

### Dungeon Running

```python
from src.bot import MetinBot

bot = MetinBot.create_dungeon_bot("config.json")
bot.run()
```

### Emergency Stop

Press **ESC** key to stop the bot at any time.

## Development

### Setting Up Development Environment

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black src/
poetry run isort src/

# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/
```

### Adding a New Strategy

1. Create a new file in `src/strategies/`
2. Inherit from `BotStrategy` ABC
3. Implement required methods
4. Add factory method to `MetinBot`

Example:

```python
from src.strategies.base import BotStrategy

class MyStrategy(BotStrategy):
    def execute(self):
        # Your logic here
        pass

    def should_continue(self):
        return self.state.is_running

    def cleanup(self):
        self.logger.info("Strategy stopped")
```

## Project Structure

```
metin-bot/
├── src/                    # Refactored codebase
│   ├── core/              # Core components
│   ├── vision/            # Computer vision
│   ├── input/             # Input handling
│   ├── game/              # Game logic
│   ├── strategies/        # Bot strategies
│   ├── bot.py             # Main orchestrator
│   └── main.py            # Entry point
├── stones/                # Stone template images
├── mining/                # Ore template images
├── dungeons/              # Dungeon template images
├── utils/                 # UI template images
├── debug/                 # Debug screenshots
├── config.json            # Configuration
├── pyproject.toml         # Poetry config
└── README.md              # This file
```

## Combat Modes

### Timer-Based Mode (Recommended)

Set `WAIT_AFTER_STONE_DESTROYED > 0`:
- Waits configured time after attacking
- No UI detection needed
- Faster and more reliable

### UI-Based Mode

Set `WAIT_AFTER_STONE_DESTROYED = 0`:
- Uses HP/top bar detection
- Stuck detection and recovery
- Handles edge cases better

## Troubleshooting

### Bot clicks wrong position

Adjust `OFFSET_X` and `OFFSET_Y` in config.json

### Bot searches wrong monitor

Set `MONITOR_INDEX` to your monitor (0 = primary, 1 = second, etc.)

### Stone not detected

1. Enable `DEBUG` mode
2. Check `debug/` folder for screenshots
3. Verify template images in `stones/` folder
4. Adjust confidence threshold if needed

### Import errors

Make sure you're in the project root and virtual environment is activated:

```bash
poetry shell
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The authors are not responsible for any consequences of using this software.
