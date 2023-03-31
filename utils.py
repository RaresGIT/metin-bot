import random
import time
from datetime import datetime
from math import sqrt
from typing import Tuple

import pyautogui


def unstuck(coords: tuple[int, int], center_x: int, center_y: int):
    log('stuck, trying to get out!')
    # targeted stone coords
    x, y = coords
    if y < center_y:
        pyautogui.keyDown('s')
        time.sleep(random.uniform(0.05, 0.08))
        pyautogui.keyUp('s')

        pyautogui.keyDown('a')
        time.sleep(random.uniform(0.05, 0.08))
        pyautogui.keyUp('a')

        pyautogui.keyDown('d')
        time.sleep(random.uniform(0.05, 0.08))
        pyautogui.keyUp('d')
    else:
        pyautogui.keyDown('w')
        time.sleep(random.uniform(0.05, 0.08))
        pyautogui.keyUp('w')

        pyautogui.keyDown('a')
        time.sleep(random.uniform(0.05, 0.08))
        pyautogui.keyUp('a')

        pyautogui.keyDown('d')
        time.sleep(random.uniform(0.05, 0.08))
        pyautogui.keyUp('d')


def attack_stone(stone_coords):
    pyautogui.moveTo(stone_coords)
    # needed sleep otherwise game doesnt register hitbox collision with click
    time.sleep(0.2)
    pyautogui.click()


def move_camera():
    log('Moving camera')

    pyautogui.keyDown('q')
    time.sleep(1)
    pyautogui.keyUp('q')

    pyautogui.press('z')

    pyautogui.keyDown('w')
    time.sleep(random.uniform(0.25, 0.75))
    pyautogui.keyUp('w')


def log(msg):
    print(str(datetime.now()) + ': ' + str(msg))


def calculate_closest_stone(metin_stones: list, CENTER_X: int, CENTER_Y: int, ASPECT_RATIO: float, offset_x: int, offset_y: int):
    parsed_stones = []
    for metin in metin_stones:
        distance = sqrt(
            pow(metin.left - CENTER_X, 2) + (pow(ASPECT_RATIO * (metin.top - CENTER_Y), 2)))
        print('distance to metin: ', distance, metin)
        parsed_stones.append({
            'd': distance,
            # 75 x 85 rough metin estimation for click, might need to be tweaked
            'coords': (metin.left + offset_x, metin.top + offset_y)
        })

    # returns closest stone found from distance calc
    min_distance_stone = min(parsed_stones, key=lambda value: value['d'])

    return min_distance_stone


def search_stones(stone_names: list):
    stones_found = []
    for stone_name in stone_names:
        generator = pyautogui.locateAllOnScreen(
            f"./stones/{stone_name}_stone.png", region=(100, 100, 2500, 1200), confidence=0.7, grayscale=True)

        [stones_found.append(x) for x in list(generator)]

    return stones_found


def search_ores(stone_names: list):
    stones_found = []
    for stone_name in stone_names:
        generator = pyautogui.locateAllOnScreen(
            f"./mining/{stone_name}_stone.png", region=(100, 100, 2500, 1200), confidence=0.7, grayscale=True)

        [stones_found.append(x) for x in list(generator)]

    return stones_found


def find_top_bar():
    hp_bar = pyautogui.locateOnScreen(
        "./utils/hp_bar.png", region=(), confidence=0.9, grayscale=True)
    top_bar = pyautogui.locateOnScreen(
        "./utils/top_bar.png", region=(), confidence=0.7, grayscale=True)

    return hp_bar, top_bar
