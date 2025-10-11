import time

import keyboard
import pyautogui
import pydirectinput

from utils import attack_stone, calculate_closest_stone, log, move_camera, search_ores

IS_SCRIPT_RUNNING = True

# global vars used, CONFIG required
# default for vm resolution
CENTER_X = 1280
CENTER_Y = 720
OFFSET_X = -50
OFFSET_Y = 40
LAST_SELECTED = None
STUCK_FOR_ITERATIONS = 0
MAX_PERMITTED_STUCK_ITERATIONS = 3
MAX_SECONDS_STUCK = 1
ASPECT_RATIO = 1.78  # 16/9 converted to z
STONE_NAMES = ["ore"]
PICKUP_DROP = True
LURE_KEY = "3"
# in hours
DEADLINE = 6

# quality of life change
log("Waiting 1 sec for alt tab!")
time.sleep(1)
start_time = time.time()


def farm_ores(ores: list, offset_x: int, offset_y: int):
    # global LAST_SELECTED, STUCK_FOR_ITERATIONS
    stones_found = len(ores)
    # hp_bar, top_bar = find_top_bar()
    # broke_ore = pyautogui.locateOnScreen('./mining/ore_drop.png', region=(
    #     100, 100, 2500, 1200), grayscale=True, confidence=0.7)

    if stones_found == 0:
        move_camera()
        return

    # if broke_ore is None:
    if stones_found > 0:
        pydirectinput.keyDown("s")
        time.sleep(0.01)
        pydirectinput.keyUp("s")

        time.sleep(0.1)

        destroy_closest_ore(ores, offset_x, offset_y)
        time.sleep(13)

    # otherwise move camera until we see at least 1
    # otherwise it means we are already fighting

    pyautogui.press("z")


def destroy_closest_ore(ores: list, offset_x: int, offset_y: int):
    # global STUCK_FOR_ITERATIONS, LAST_SELECTED
    # STUCK_FOR_ITERATIONS = 0
    log("Breaking new ore!")

    min_distance_stone = calculate_closest_stone(
        ores, CENTER_X, CENTER_Y, ASPECT_RATIO, offset_x, offset_y
    )

    print(min_distance_stone["coords"])
    # time.sleep(0.25)
    attack_stone(min_distance_stone["coords"])


def main():
    global IS_SCRIPT_RUNNING, STUCK_FOR_ITERATIONS
    while IS_SCRIPT_RUNNING:

        # Exit the script
        if keyboard.is_pressed("esc"):
            IS_SCRIPT_RUNNING = False
            log("Exiting script!")
            raise KeyboardInterrupt

        # stop after 6H of farming
        # log(time.time() - start_time)
        if time.time() - start_time >= 3600 * DEADLINE:
            break

        # in testing, subject to change. Basic idea is search for UI element to pause the script, TASKS object is not the best choice
        on_screen_check = pyautogui.locateOnScreen(
            "./utils/on_screen_check.png", region=(), confidence=0.8, grayscale=True
        )
        if on_screen_check is not None:
            log(
                "Inventory on screen, pausing features until I find it... Retrying in 1s"
            )
            time.sleep(1)
            continue

        metin_stones = search_ores(STONE_NAMES)
        farm_ores(metin_stones, OFFSET_X, OFFSET_Y)


if __name__ == "__main__":
    main()
