import os
import random
import time
from datetime import datetime
from math import sqrt

import pyautogui
import pydirectinput
import pyscreeze
import win32api
import win32con
import win32gui
from screeninfo import get_monitors

hwnd = win32gui.FindWindow(None, "Honor2.net!")


def get_monitor_region(monitor_index=None):
    """
    Get the screen region for a specific monitor.

    Args:
        monitor_index: Index of monitor (0 = primary, 1 = second, etc.)
                      None = use all monitors (default PyAutoGUI behavior)

    Returns:
        tuple: (x, y, width, height) or None for all monitors
    """
    if monitor_index is None:
        return None

    try:
        monitors = list(get_monitors())
        if monitor_index < 0 or monitor_index >= len(monitors):
            log(
                f"Warning: Monitor index {monitor_index} out of range. Available monitors: {len(monitors)}"
            )
            log("Falling back to all monitors")
            return None

        monitor = monitors[monitor_index]
        # Return (x, y, width, height) for the monitor
        return (monitor.x, monitor.y, monitor.width, monitor.height)
    except Exception as e:
        log(f"Error getting monitor info: {e}")
        log("Falling back to all monitors")
        return None


def list_monitors(debug=False):
    """List all available monitors with their properties"""
    try:
        monitors = list(get_monitors())
        if debug:
            log(f"Found {len(monitors)} monitor(s):")
            for i, monitor in enumerate(monitors):
                log(
                    f"  Monitor {i}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})"
                )
                if monitor.is_primary:
                    log(f"    ^ PRIMARY monitor")
        return monitors
    except Exception as e:
        log(f"Error listing monitors: {e}")
        return []


def ensure_debug_folder():
    """Create debug folder if it doesn't exist"""
    if not os.path.exists("debug"):
        os.makedirs("debug")
        log("Created debug folder")


def save_debug_screenshot(image, filename):
    """Save screenshot to debug folder with timestamp"""
    ensure_debug_folder()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filepath = os.path.join("debug", f"{timestamp}_{filename}")
    image.save(filepath)
    log(f"Saved debug screenshot: {filepath}")


def unstuck(coords: tuple[int, int], center_x: int, center_y: int):
    log("stuck, trying to get out!")
    # targeted stone coords
    x, y = coords
    if y < center_y:
        pydirectinput.keyDown("s")
        time.sleep(random.uniform(0.05, 0.08))
        pydirectinput.keyUp("s")

        pydirectinput.keyDown("a")
        time.sleep(random.uniform(0.05, 0.08))
        pydirectinput.keyUp("a")

        pydirectinput.keyDown("d")
        time.sleep(random.uniform(0.05, 0.08))
        pydirectinput.keyUp("d")
    else:
        pydirectinput.keyDown("w")
        time.sleep(random.uniform(0.05, 0.08))
        pydirectinput.keyUp("w")

        pydirectinput.keyDown("a")
        time.sleep(random.uniform(0.05, 0.08))
        pydirectinput.keyUp("a")

        pydirectinput.keyDown("d")
        time.sleep(random.uniform(0.05, 0.08))
        pydirectinput.keyUp("d")


def global_to_client(hwnd, x, y):
    # Convert the global screen coordinates to client area coordinates
    client_pos = win32gui.ScreenToClient(hwnd, (x, y))
    return client_pos


def send_click(global_x, global_y):
    client_x, client_y = global_to_client(hwnd, global_x, global_y)

    print((global_x, global_y), (client_x, client_y), win32gui.GetClientRect(hwnd))
    lParam = win32api.MAKELONG(client_x, client_y)
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)


def send_click_relative(local_x, local_y, hwnd):
    lParam = win32api.MAKELONG(local_x, local_y)

    print(local_x, local_y, lParam)
    win32api.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)


def attack_stone(stone_coords):
    pyautogui.moveTo(stone_coords)
    # needed sleep otherwise game doesnt register hitbox collision with click
    time.sleep(0.2)
    pyautogui.click()


def move_camera():
    log("Moving camera")

    pydirectinput.keyDown("q")
    time.sleep(1)
    pydirectinput.keyUp("q")

    pydirectinput.keyDown("w")
    time.sleep(random.uniform(0.5, 0.75))
    pydirectinput.keyUp("w")

    # Wait for camera to settle before next action
    time.sleep(0.5)


def log(msg):
    print(str(datetime.now()) + ": " + str(msg))


def press_buff_keys(buff_keys: str):
    """
    Press buff key combination (e.g., 'ctrl+v')

    Args:
        buff_keys: Key combination string (e.g., 'ctrl+v', 'alt+f1', 'f5')
    """
    keys = buff_keys.lower().split("+")

    if len(keys) == 1:
        # Single key
        pydirectinput.press(keys[0])
        log(f"Pressed buff key: {keys[0]}")
    else:
        # Key combination
        # Hold down modifier keys
        for key in keys[:-1]:
            pydirectinput.keyDown(key)
            time.sleep(0.05)

        # Press the final key
        pydirectinput.press(keys[-1])
        time.sleep(0.05)

        # Release modifier keys in reverse order
        for key in reversed(keys[:-1]):
            pydirectinput.keyUp(key)
            time.sleep(0.05)

        log(f"Pressed buff keys: {buff_keys}")


def calculate_closest_stone(
    metin_stones: list,
    CENTER_X: int,
    CENTER_Y: int,
    ASPECT_RATIO: float,
    offset_x: int,
    offset_y: int,
):
    parsed_stones = []
    for metin in metin_stones:
        distance = sqrt(
            pow(metin.left - CENTER_X, 2)
            + (pow(ASPECT_RATIO * (metin.top - CENTER_Y), 2))
        )
        print("distance to metin: ", distance, metin)
        parsed_stones.append(
            {
                "d": distance,
                # 75 x 85 rough metin estimation for click, might need to be tweaked
                "coords": (metin.left + offset_x, metin.top + offset_y),
            }
        )

    # returns closest stone found from distance calc
    min_distance_stone = min(parsed_stones, key=lambda value: value["d"])

    return min_distance_stone


def search_stones(stone_names: list, debug=False, monitor_index=None):
    stones_found = []

    # Get the monitor region to search in
    monitor_region = get_monitor_region(monitor_index)

    # Define search region - either specific monitor or fallback to hardcoded region
    if monitor_region:
        # Use the entire monitor
        search_region = monitor_region
        if debug:
            log(f"Searching on monitor {monitor_index}: region={search_region}")
    else:
        # Fallback to original hardcoded region
        search_region = (100, 100, 2500, 1200)
        if debug:
            log(f"Searching in hardcoded region: {search_region}")

    # Save screenshot if debug mode is enabled
    if debug:
        screenshot = pyautogui.screenshot(region=search_region)
        save_debug_screenshot(screenshot, "search_stones_region.png")
        log(f"Searching for stones: {stone_names}")

    for stone_name in stone_names:
        try:
            generator = pyautogui.locateAllOnScreen(
                f"./stones/{stone_name}_stone.png",
                region=search_region,
                confidence=0.7,
                grayscale=True,
            )

            found_list = list(generator)
            if debug and found_list:
                log(f"Found {len(found_list)} instances of {stone_name}_stone")

            [stones_found.append(x) for x in found_list]
        except (
            pyautogui.ImageNotFoundException,
            pyscreeze.ImageNotFoundException,
        ) as e:
            if debug:
                log(f"{stone_name}_stone not found (confidence too low)")
            pass

    if debug:
        log(f"Total stones found: {len(stones_found)}")
    return stones_found


def search_ores(stone_names: list):
    stones_found = []
    for stone_name in stone_names:
        generator = pyautogui.locateAllOnScreen(
            f"./mining/{stone_name}_stone.png",
            region=(100, 100, 2500, 1200),
            confidence=0.7,
            grayscale=True,
        )

        [stones_found.append(x) for x in list(generator)]

    return stones_found


def find_top_bar(debug=False, monitor_index=None):
    # Get the monitor region to search in
    monitor_region = get_monitor_region(monitor_index)

    if debug:
        if monitor_region:
            screenshot = pyautogui.screenshot(region=monitor_region)
            log(f"Searching for hp_bar and top_bar on monitor {monitor_index}")
        else:
            screenshot = pyautogui.screenshot()
            log("Searching for hp_bar and top_bar on all monitors")
        save_debug_screenshot(screenshot, "find_top_bar_fullscreen.png")

    hp_bar = None
    top_bar = None

    try:
        hp_bar = pyautogui.locateOnScreen(
            "./utils/hp_bar.png", region=monitor_region, confidence=0.9, grayscale=True
        )
    except pyautogui.ImageNotFoundException:
        if debug:
            log("hp_bar not found")
        pass

    try:
        top_bar = pyautogui.locateOnScreen(
            "./utils/top_bar.png", region=monitor_region, confidence=0.7, grayscale=True
        )
    except pyautogui.ImageNotFoundException:
        if debug:
            log("top_bar not found")
        pass

    if debug:
        log(f"hp_bar found: {hp_bar is not None}, top_bar found: {top_bar is not None}")

    return hp_bar, top_bar
