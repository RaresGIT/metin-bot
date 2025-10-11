import time

import pyautogui
import pydirectinput

from metin import farm_stones
from utils import log, search_stones


def dungeon_runs():
    while True:
        dungeon_end_phase = pyautogui.locateOnScreen(
            "./dungeons/dungeon_end.png", region=(), confidence=0.7, grayscale=True
        )

        click_stone_phase = pyautogui.locateOnScreen(
            "./dungeons/click_stone.png", region=(), confidence=0.7, grayscale=True
        )

        defeat_final_boss_phase = pyautogui.locateOnScreen(
            "./dungeons/defeat_final_boss.png",
            region=(),
            confidence=0.7,
            grayscale=True,
        )

        kill_3_stones_phase = pyautogui.locateOnScreen(
            "./dungeons/kill_3_stones.png", region=(), confidence=0.7, grayscale=True
        )

        stones_for_stone_phase = pyautogui.locateOnScreen(
            "./dungeons/stones_for_stone.png", region=(), confidence=0.7, grayscale=True
        )

        if dungeon_end_phase:
            log("Finished dungeon")

        if click_stone_phase:
            log("In click_stone phase")
            stone = pyautogui.locateOnScreen(
                "./dungeons/stone.png", region=(), confidence=0.7, grayscale=True
            )

            if stone is None:
                log("Cannot see stone, waiting for user input...")

            else:
                pyautogui.moveTo(stone)
                time.sleep(0.1)
                pyautogui.click(button="secondary")

        if kill_3_stones_phase or stones_for_stone_phase:
            pydirectinput.keyUp("space")
            log("In destroy stones phase")
            stones = search_stones(["generic"])
            farm_stones(stones, -10, 85)
        else:
            log("Other dungeon step that doesnt require me to do anything XD")
            pydirectinput.press("z")
            pydirectinput.press("3")
            pydirectinput.keyDown("space")
            time.sleep(0.5)
