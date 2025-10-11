import math
import time

import cv2
import numpy as np
import win32con
import win32gui
import win32ui
from PIL import Image

from utils import send_click, send_click_relative


def capture_window(hwnd):

    # Get the window's device context (DC)
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)

    # BitBlt to capture the window
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    img = Image.frombuffer(
        "RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1
    )

    # Free resources
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)

    return img


def find_all_images(haystack, needle):
    haystack_gray = cv2.cvtColor(haystack, cv2.COLOR_BGR2GRAY)
    needle_gray = cv2.cvtColor(needle, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(haystack_gray, needle_gray, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    locations = np.where(result >= threshold)

    rectangles = []
    for loc in zip(*locations[::-1]):
        rect = [int(loc[0]), int(loc[1]), needle.shape[1], needle.shape[0]]
        rectangles.append(rect)
        rectangles.append(rect)  # Append twice for grouping

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.5)
    return rectangles


# Capture the window content
window_title = "Honor2.net!"

hwnd = win32gui.FindWindow(None, window_title)
if not hwnd:
    raise Exception("Window not found: {}".format(window_title))
window_image = capture_window(hwnd)

# Load the needle image (template)
needle_image_path = "stones/90_stone.png"
needle_image = cv2.imread(needle_image_path)

# Convert the window image to a format suitable for OpenCV
window_image_cv = cv2.cvtColor(np.array(window_image), cv2.COLOR_RGB2BGR)

# Find all occurrences of the needle image in the window image
rectangles = find_all_images(window_image_cv, needle_image)

# Draw rectangles around found occurrences
for x, y, w, h in rectangles:
    cv2.rectangle(window_image_cv, (x, y), (x + w, y + h), (0, 255, 0), 2)


# Get the window's rectangle coordinates
left, top, right, bottom = win32gui.GetWindowRect(hwnd)

# Calculate the center of the window
center_x = (left + right) // 2
center_y = (top + bottom) // 2

# Calculate the width and height of the window
width = right - left
height = bottom - top

# Calculate the aspect ratio
aspect_ratio = width / height


def calculate_closest_stone(
    rectangles: list,
    CENTER_X: int,
    CENTER_Y: int,
    ASPECT_RATIO: float,
    offset_x: int,
    offset_y: int,
):
    parsed_stones = []
    for rect in rectangles:
        x, y, w, h = rect
        distance = math.sqrt(
            math.pow(x - CENTER_X, 2) + (math.pow(ASPECT_RATIO * (y - CENTER_Y), 2))
        )
        print("Distance to stone: ", distance, rect)
        parsed_stones.append(
            {
                "d": distance,
                # Adjusting coordinates with the given offsets
                "coords": (x + offset_x, y + offset_y),
            }
        )

    # Return the closest stone found based on the distance calculation
    min_distance_stone = min(parsed_stones, key=lambda value: value["d"])

    return min_distance_stone


closest_stone = calculate_closest_stone(
    rectangles, center_x, center_y, aspect_ratio, 70, 50
)
print(closest_stone)

time.sleep(2)
send_click_relative(closest_stone["coords"][0], closest_stone["coords"][1], hwnd)
# Convert back to PIL Image and show/save
# result_image = Image.fromarray(cv2.cvtColor(window_image_cv, cv2.COLOR_BGR2RGB))
# result_image.show()
# result_image.save("result_image.png")
