import json
import os
import time

import keyboard
import pyautogui
import pydirectinput

from utils import (
    attack_stone,
    calculate_closest_stone,
    find_top_bar,
    get_monitor_region,
    list_monitors,
    log,
    move_camera,
    press_buff_keys,
    search_stones,
    unstuck,
)

IS_SCRIPT_RUNNING = True

# global vars used, CONFIG required
CENTER_X = 960
CENTER_Y = 540
OFFSET_X = 70
OFFSET_Y = 45
LAST_SELECTED = None
STUCK_FOR_ITERATIONS = 0
MAX_PERMITTED_STUCK_ITERATIONS = 3
MAX_SECONDS_STUCK = 1
ASPECT_RATIO = 1.78  # 16/9 converted to ratio
STONE_NAMES = []
PICKUP_DROP = True
LURE_KEY = ""
# in hours
DEADLINE = 10
DEBUG = False
# wait time in seconds after stone is destroyed before searching for next stone
WAIT_AFTER_STONE_DESTROYED = 0.5
# monitor index (0 = primary monitor, 1 = second monitor, etc.)
# set to None to use all monitors
MONITOR_INDEX = None
# keep buff uptime - automatically press buff keys at regular intervals
KEEP_BUFF_UPTIME = False
# buff interval in seconds (random between min and max)
BUFF_INTERVAL_MIN = 30
BUFF_INTERVAL_MAX = 60
# buff key combination (e.g., "ctrl+v")
BUFF_KEYS = "ctrl+v"


def read_config(file_path):
    global CENTER_X, CENTER_Y, OFFSET_X, OFFSET_Y, ASPECT_RATIO, STONE_NAMES, PICKUP_DROP, LURE_KEY, DEADLINE, DEBUG, WAIT_AFTER_STONE_DESTROYED, MONITOR_INDEX, KEEP_BUFF_UPTIME, BUFF_INTERVAL_MIN, BUFF_INTERVAL_MAX, BUFF_KEYS
    with open(file_path, "r") as file:
        config = json.load(file)
        CENTER_X = config.get("CENTER_X", CENTER_X)
        CENTER_Y = config.get("CENTER_Y", CENTER_Y)
        OFFSET_X = config.get("OFFSET_X", OFFSET_X)
        OFFSET_Y = config.get("OFFSET_Y", OFFSET_Y)
        ASPECT_RATIO = config.get("ASPECT_RATIO", ASPECT_RATIO)
        STONE_NAMES = config.get("STONE_NAMES", STONE_NAMES)
        PICKUP_DROP = config.get("PICKUP_DROP", PICKUP_DROP)
        LURE_KEY = config.get("LURE_KEY", LURE_KEY)
        DEADLINE = config.get("DEADLINE", DEADLINE)
        DEBUG = config.get("DEBUG", DEBUG)
        WAIT_AFTER_STONE_DESTROYED = config.get("WAIT_AFTER_STONE_DESTROYED", WAIT_AFTER_STONE_DESTROYED)
        MONITOR_INDEX = config.get("MONITOR_INDEX", MONITOR_INDEX)
        KEEP_BUFF_UPTIME = config.get("KEEP_BUFF_UPTIME", KEEP_BUFF_UPTIME)
        BUFF_INTERVAL_MIN = config.get("BUFF_INTERVAL_MIN", BUFF_INTERVAL_MIN)
        BUFF_INTERVAL_MAX = config.get("BUFF_INTERVAL_MAX", BUFF_INTERVAL_MAX)
        BUFF_KEYS = config.get("BUFF_KEYS", BUFF_KEYS)


# Read configuration from file
read_config("config.json")

# Create debug folder if DEBUG mode is enabled
if DEBUG:
    from utils import ensure_debug_folder
    ensure_debug_folder()

# quality of life change
log("Waiting 1 sec for alt tab!")
time.sleep(1)
start_time = time.time()

# Buff tracking - will be initialized in main()
import random
last_buff_time = None
next_buff_interval = None


def destroy_closest_stone(metin_stones: list, offset_x: int, offset_y: int):
    global STUCK_FOR_ITERATIONS, LAST_SELECTED
    STUCK_FOR_ITERATIONS = 0
    log("Breaking new stone!")

    min_distance_stone = calculate_closest_stone(
        metin_stones, CENTER_X, CENTER_Y, ASPECT_RATIO, offset_x, offset_y
    )

    if LAST_SELECTED is None:
        if DEBUG:
            log(f"Closest stone coordinates: {min_distance_stone['coords']}, distance: {min_distance_stone['d']}")
        print(min_distance_stone["coords"])
        # time.sleep(0.25)
        attack_stone(min_distance_stone["coords"])
        LAST_SELECTED = min_distance_stone
        LAST_SELECTED["selected_at"] = time.time()
        if DEBUG:
            log(f"Stone selected and attacked at {time.time()}")


def farm_stones(metin_stones: list, offset_x: int, offset_y: int):
    global LAST_SELECTED, STUCK_FOR_ITERATIONS
    stones_found = len(metin_stones)

    if DEBUG:
        log(f"farm_stones called with {stones_found} stones found")

    # Timer-based mode: ignore top bar, use configured wait time
    if WAIT_AFTER_STONE_DESTROYED > 0:
        # If we have a stone selected, check if enough time has passed
        if LAST_SELECTED is not None:
            elapsed_time = time.time() - LAST_SELECTED["selected_at"]

            if elapsed_time >= WAIT_AFTER_STONE_DESTROYED:
                # Enough time has passed, stone should be destroyed
                if DEBUG:
                    log(f"Wait time elapsed ({elapsed_time:.2f}s >= {WAIT_AFTER_STONE_DESTROYED}s), clearing selection")
                LAST_SELECTED = None

                if PICKUP_DROP:
                    if DEBUG:
                        log("Pressing Z to pick up/drop items")
                    pydirectinput.press("z")
                    time.sleep(0.1)
            else:
                # Still waiting for stone to be destroyed
                if DEBUG:
                    remaining = WAIT_AFTER_STONE_DESTROYED - elapsed_time
                    log(f"Waiting for stone destruction: {elapsed_time:.2f}s / {WAIT_AFTER_STONE_DESTROYED}s (remaining: {remaining:.2f}s)")
                return  # Don't search for new stones yet

        # No stone selected, look for next target
        if LAST_SELECTED is None:
            if stones_found > 0:
                if DEBUG:
                    log(f"Ready to attack! {stones_found} stone(s) visible, no stone selected")
                destroy_closest_stone(metin_stones, offset_x, offset_y)
            else:
                if DEBUG:
                    log("No stones found, moving camera to search")
                move_camera()

    # Original top bar-based mode
    else:
        hp_bar, top_bar = find_top_bar(DEBUG, MONITOR_INDEX)

        # cleanup for last_selected check
        if top_bar is None:
            if DEBUG and LAST_SELECTED is not None:
                log("Top bar disappeared, stone destroyed. Clearing selection.")
            LAST_SELECTED = None
            if PICKUP_DROP:
                if DEBUG:
                    log("Pressing Z to pick up/drop items")
                pydirectinput.press("z")

            time.sleep(0.1)

        # if stuck for more than max allowed time and stone didnt get damaged, try to get unstuck
        # max STUCK_FOR_ITERATIONS retries. If not unstuck, deselect stone
        if top_bar is not None and hp_bar is not None:
            if LAST_SELECTED is not None:
                if time.time() - LAST_SELECTED["selected_at"] > MAX_SECONDS_STUCK:
                    if DEBUG:
                        log(f"Stuck detected! Time elapsed: {time.time() - LAST_SELECTED['selected_at']:.2f}s")
                    unstuck(LAST_SELECTED["coords"], CENTER_X, CENTER_Y)
                    STUCK_FOR_ITERATIONS += 1
                    log(f"Tried {STUCK_FOR_ITERATIONS} times!")
        else:
            #  main code, parse stones, find closest and attack
            if top_bar is None and stones_found > 0 and LAST_SELECTED is None:
                if DEBUG:
                    log(f"Ready to attack! {stones_found} stone(s) visible, no stone selected")
                destroy_closest_stone(metin_stones, offset_x, offset_y)
            # otherwise move camera until we see at least 1
            elif stones_found == 0 and top_bar is None:
                if DEBUG:
                    log("No stones found, moving camera to search")
                move_camera()
            # otherwise it means we are already fighting
            else:
                if DEBUG:
                    log(f"Search Paused! top_bar: {top_bar is not None}, stones_found: {stones_found}, LAST_SELECTED: {LAST_SELECTED is not None}")

        # if stuck for too long, select another stone
        if STUCK_FOR_ITERATIONS == MAX_PERMITTED_STUCK_ITERATIONS:
            if DEBUG:
                log(f"Max stuck iterations reached ({MAX_PERMITTED_STUCK_ITERATIONS}), deselecting and moving camera")
            pydirectinput.press("esc")
            move_camera()
            STUCK_FOR_ITERATIONS = 0


def main():
    global IS_SCRIPT_RUNNING, STUCK_FOR_ITERATIONS, last_buff_time, next_buff_interval

    # Initialize buff tracking
    last_buff_time = time.time()
    next_buff_interval = random.uniform(BUFF_INTERVAL_MIN, BUFF_INTERVAL_MAX) if KEEP_BUFF_UPTIME else float('inf')

    if DEBUG:
        log("=" * 50)
        log("DEBUG MODE ENABLED")
        log(f"Configuration: CENTER=({CENTER_X}, {CENTER_Y}), OFFSET=({OFFSET_X}, {OFFSET_Y})")
        log(f"ASPECT_RATIO={ASPECT_RATIO}, DEADLINE={DEADLINE}h")
        log(f"STONE_NAMES={STONE_NAMES}")
        log(f"PICKUP_DROP={PICKUP_DROP}, LURE_KEY={LURE_KEY}")

        # Monitor info
        monitors = list_monitors(debug=True)
        if MONITOR_INDEX is not None:
            log(f"MONITOR_INDEX={MONITOR_INDEX} (targeting specific monitor)")
            monitor_region = get_monitor_region(MONITOR_INDEX)
            if monitor_region:
                log(f"  Monitor region: {monitor_region}")
        else:
            log("MONITOR_INDEX=None (searching all monitors)")

        # Mode info
        if WAIT_AFTER_STONE_DESTROYED > 0:
            log(f"WAIT_AFTER_STONE_DESTROYED={WAIT_AFTER_STONE_DESTROYED}s (Timer-based mode)")
            log("Top bar checking is DISABLED - using timer-based stone destruction detection")
        else:
            log(f"WAIT_AFTER_STONE_DESTROYED={WAIT_AFTER_STONE_DESTROYED}s (Top bar mode)")
            log("Using top bar checking for stone destruction detection")

        # Buff info
        if KEEP_BUFF_UPTIME:
            log(f"KEEP_BUFF_UPTIME=True")
            log(f"  Buff keys: {BUFF_KEYS}")
            log(f"  Buff interval: {BUFF_INTERVAL_MIN}-{BUFF_INTERVAL_MAX}s")
            log(f"  Next buff in: {next_buff_interval:.1f}s")
        else:
            log("KEEP_BUFF_UPTIME=False (buff refresh disabled)")

        log("=" * 50)

    while IS_SCRIPT_RUNNING:

        # Exit the script
        if keyboard.is_pressed("esc"):
            IS_SCRIPT_RUNNING = False
            log("Exiting script!")
            raise KeyboardInterrupt

        # stop after 6H of farming
        # log(time.time() - start_time)
        elapsed_hours = (time.time() - start_time) / 3600
        if time.time() - start_time >= 3600 * DEADLINE:
            if DEBUG:
                log(f"Deadline reached! Elapsed time: {elapsed_hours:.2f}h / {DEADLINE}h")
            break

        # in testing, subject to change. Basic idea is search for UI element to pause the script, TASKS object is not the best choice
        try:
            monitor_region = get_monitor_region(MONITOR_INDEX)
            on_screen_check = pyautogui.locateOnScreen(
                "./utils/on_screen_check.png", region=monitor_region, confidence=0.9, grayscale=True
            )
            if on_screen_check is not None:
                if DEBUG:
                    log("on_screen_check detected (inventory/UI open)")
                log(
                    "Inventory on screen, pausing features until I find it... Retrying in 1s"
                )
                time.sleep(1)
                continue
        except pyautogui.ImageNotFoundException:
            # Image not found, continue with normal flow
            if DEBUG:
                log("on_screen_check not found, continuing normal operation")
            pass

        # Check if it's time to refresh buffs
        if KEEP_BUFF_UPTIME:
            time_since_last_buff = time.time() - last_buff_time
            if time_since_last_buff >= next_buff_interval:
                if DEBUG:
                    log(f"Refreshing buffs (last buff was {time_since_last_buff:.1f}s ago)")
                press_buff_keys(BUFF_KEYS)
                last_buff_time = time.time()
                next_buff_interval = random.uniform(BUFF_INTERVAL_MIN, BUFF_INTERVAL_MAX)
                if DEBUG:
                    log(f"Next buff refresh in {next_buff_interval:.1f}s")
                time.sleep(0.2)  # Small delay after pressing buff keys

        time.sleep(0.5)
        metin_stones = search_stones(STONE_NAMES, DEBUG, MONITOR_INDEX)
        farm_stones(metin_stones, OFFSET_X, OFFSET_Y)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("Something went wrong! Auto exiting in 10s!")
        log(e)
        time.sleep(10)

        raise e
