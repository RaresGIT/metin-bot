import time

import pydirectinput

while True:
    print("lure")
    pydirectinput.press("3")

    print("attack")
    pydirectinput.keyDown("space")
    time.sleep(5)
    pydirectinput.keyUp("space")
