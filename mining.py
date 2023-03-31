
import time

import keyboard
import pyautogui

from metin_script import farm_ores
from utils import log, search_ores

IS_SCRIPT_RUNNING = True

# global vars used, CONFIG required
CENTER_X = 1280
CENTER_Y = 720
OFFSET_X = 50
OFFSET_Y = 75
LAST_SELECTED = None
STUCK_FOR_ITERATIONS = 0
MAX_PERMITTED_STUCK_ITERATIONS = 3
MAX_SECONDS_STUCK = 1
ASPECT_RATIO = 1.78  # 16/9 converted to z
STONE_NAMES = ['ore']
PICKUP_DROP = True
LURE_KEY = '3'
# in hours
DEADLINE = 99999

# quality of life change
log('Waiting 1 sec for alt tab!')
time.sleep(1)
start_time = time.time()


def main():
    global IS_SCRIPT_RUNNING, STUCK_FOR_ITERATIONS
    while IS_SCRIPT_RUNNING:

        # Exit the script
        if keyboard.is_pressed("esc"):
            IS_SCRIPT_RUNNING = False
            log('Exiting script!')
            raise KeyboardInterrupt

        # stop after 6H of farming
        # log(time.time() - start_time)
        if time.time() - start_time >= 3600 * DEADLINE:
            break

        # in testing, subject to change. Basic idea is search for UI element to pause the script, TASKS object is not the best choice
        on_screen_check = pyautogui.locateOnScreen(
            "./utils/on_screen_check.png", region=(), confidence=0.9, grayscale=True)
        if on_screen_check is not None:
            log('Inventory on screen, pausing features until I find it... Retrying in 1s')
            time.sleep(1)
            continue

        metin_stones = search_ores(STONE_NAMES)
        farm_ores(metin_stones, OFFSET_X, OFFSET_Y)


if __name__ == '__main__':
    main()
