import win32gui


def enum_windows_callback(hwnd, window_titles):
    if win32gui.IsWindowVisible(hwnd):
        window_title = win32gui.GetWindowText(hwnd)
        if window_title:
            window_titles.append(window_title)


def get_window_titles():
    window_titles = []
    win32gui.EnumWindows(enum_windows_callback, window_titles)
    return window_titles


# Example usage
titles = get_window_titles()
for title in titles:
    print(title)
