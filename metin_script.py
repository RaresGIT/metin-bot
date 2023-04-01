import random
import time
from datetime import datetime
from math import sqrt

import keyboard
import pyautogui

from utils import (attack_stone, calculate_closest_stone, find_top_bar, log,
                   move_camera, search_stones, unstuck)

IS_SCRIPT_RUNNING = True

# global vars used, CONFIG required
CENTER_X = 1280
CENTER_Y = 720
OFFSET_X = 75
OFFSET_Y = 85
LAST_SELECTED = None
STUCK_FOR_ITERATIONS = 0
MAX_PERMITTED_STUCK_ITERATIONS = 3
MAX_SECONDS_STUCK = 1
ASPECT_RATIO = 1.78  # 16/9 converted to z
STONE_NAMES = ['chronos', 'shiva', 'fatalis']
PICKUP_DROP = True
LURE_KEY = '3'
# in hours
DEADLINE = 10

# quality of life change
log('Waiting 1 sec for alt tab!')
time.sleep(1)
start_time = time.time()


def dungeon_runs():
    while True:
        dungeon_end_phase = pyautogui.locateOnScreen(
            "./dungeons/dungeon_end.png", region=(), confidence=0.7, grayscale=True)

        click_stone_phase = pyautogui.locateOnScreen(
            "./dungeons/click_stone.png", region=(), confidence=0.7, grayscale=True)

        defeat_final_boss_phase = pyautogui.locateOnScreen(
            "./dungeons/defeat_final_boss.png", region=(), confidence=0.7, grayscale=True)

        kill_3_stones_phase = pyautogui.locateOnScreen(
            "./dungeons/kill_3_stones.png", region=(), confidence=0.7, grayscale=True)

        stones_for_stone_phase = pyautogui.locateOnScreen(
            "./dungeons/stones_for_stone.png", region=(), confidence=0.7, grayscale=True)

        if dungeon_end_phase:
            log('Finished dungeon')

        if click_stone_phase:
            log('In click_stone phase')
            stone = pyautogui.locateOnScreen(
                "./dungeons/stone.png", region=(), confidence=0.7, grayscale=True)

            if stone is None:
                log('Cannot see stone, waiting for user input...')

            else:
                pyautogui.moveTo(stone)
                time.sleep(0.1)
                pyautogui.click(button='secondary')

        if kill_3_stones_phase or stones_for_stone_phase:
            pyautogui.keyUp('space')
            log('In destroy stones phase')
            stones = search_stones(['generic'])
            farm_stones(stones, -10, 85)
        else:
            log('Other dungeon step that doesnt require me to do anything XD')
            pyautogui.press('z')
            pyautogui.press(LURE_KEY)
            pyautogui.keyDown('space')
            time.sleep(0.5)


def destroy_closest_stone(metin_stones: list, offset_x: int, offset_y: int):
    global STUCK_FOR_ITERATIONS, LAST_SELECTED
    STUCK_FOR_ITERATIONS = 0
    log('Breaking new stone!')

    min_distance_stone = calculate_closest_stone(
        metin_stones, CENTER_X, CENTER_Y, ASPECT_RATIO, offset_x, offset_y)

    if LAST_SELECTED is None:
        print(min_distance_stone['coords'])
        # time.sleep(0.25)
        attack_stone(min_distance_stone['coords'])
        LAST_SELECTED = min_distance_stone
        LAST_SELECTED['selected_at'] = time.time()


def destroy_closest_ore(ores: list, offset_x: int, offset_y: int):
    # global STUCK_FOR_ITERATIONS, LAST_SELECTED
    # STUCK_FOR_ITERATIONS = 0
    log('Breaking new ore!')

    min_distance_stone = calculate_closest_stone(
        ores, CENTER_X, CENTER_Y, ASPECT_RATIO, offset_x, offset_y)

    print(min_distance_stone['coords'])
    # time.sleep(0.25)
    attack_stone(min_distance_stone['coords'])


def farm_stones(metin_stones: list, offset_x: int, offset_y: int):
    global LAST_SELECTED, STUCK_FOR_ITERATIONS
    stones_found = len(metin_stones)
    hp_bar, top_bar = find_top_bar()

    # cleanup for last_selected check
    if top_bar is None:
        LAST_SELECTED = None
        if PICKUP_DROP:
            pyautogui.press('z')
        time.sleep(0.1)

    # if stuck for more than max allowed time and stone didnt get damaged, try to get unstuck
    # max STUCK_FOR_ITERATIONS retries. If not unstuck, deselect stone
    if top_bar is not None and hp_bar is not None:
        if LAST_SELECTED is not None:
            if time.time() - LAST_SELECTED['selected_at'] > MAX_SECONDS_STUCK:
                unstuck(LAST_SELECTED['coords'], CENTER_X, CENTER_Y)
                STUCK_FOR_ITERATIONS += 1
                log(f'Tried {STUCK_FOR_ITERATIONS} times!')
    else:
        #  main code, parse stones, find closest and attack
        if top_bar is None and stones_found > 0 and LAST_SELECTED is None:
            destroy_closest_stone(metin_stones, offset_x, offset_y)
        # otherwise move camera until we see at least 1
        elif stones_found == 0 and top_bar is None:
            move_camera()
        # otherwise it means we are already fighting
        else:
            log('Search Paused!')

    # if stuck for too long, select another stone
    if STUCK_FOR_ITERATIONS == MAX_PERMITTED_STUCK_ITERATIONS:
        pyautogui.press('esc')
        move_camera()
        STUCK_FOR_ITERATIONS = 0


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
        pyautogui.keyDown('s')
        time.sleep(0.01)
        pyautogui.keyUp('s')

        time.sleep(0.1)

        destroy_closest_ore(ores, offset_x, offset_y)
        time.sleep(13)

    # otherwise move camera until we see at least 1
    # otherwise it means we are already fighting

    pyautogui.press('z')


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

        metin_stones = search_stones(STONE_NAMES)
        farm_stones(metin_stones, OFFSET_X, OFFSET_Y)


if __name__ == '__main__':
    main()
