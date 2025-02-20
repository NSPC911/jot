import curses
import os
import shutil
import webbrowser
import json
import subprocess
import threading
import time

# NerdFont icons
icons = {
    "folder": "  ",
    "file": "  ",
    "image": " 󰋩 ",
    "markdown": "  ",
    "text": "  ",
    "pdf": "  ",
    "default": "  ",
}

# Load the ~~cannon~~ config
with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as f:
    config = json.load(f)

# support system vars
main_dir = os.path.expandvars(config["main_dir"])
keybinds = config["keybinds"]


def draw_input_box(stdscr, prompt):
    h, w = stdscr.getmaxyx()
    box_h, box_w = 3, w // 2
    box_y, box_x = (h - box_h) // 2, (w - box_w) // 2
    input_win = curses.newwin(box_h, box_w, box_y, box_x)
    input_win.box()
    input_win.addstr(0, 2, f" {prompt} ")
    input_win.refresh()
    curses.echo()
    input_win.addstr(1, 2, "> ")
    input_win.refresh()

    user_input = ""
    while True:
        key = input_win.getch()
        if key in [10, 13]:  # Enter key
            break
        elif key in [27]:  # Escape key
            user_input = ""
            break
        elif key in [127, 8, curses.KEY_BACKSPACE]:  # Backspace
            if len(user_input) > 0:
                user_input = user_input[:-1]
        elif 32 <= key <= 126:  # printable chars
            user_input += chr(key)
        input_win.addstr(1, 0, f"│ > {user_input} ")
        input_win.refresh()
    curses.noecho()
    return user_input.strip()


def get_folders():
    folders = {"folders": {}, "files": []}
    for root, _, files in os.walk(main_dir):
        folder = os.path.relpath(root, main_dir)
        if folder == ".":
            folders["files"] = files
        else:
            folders["folders"][folder] = files
    return folders


def truncate_text(text, max_width):
    if len(text) > max_width:
        return text[: max_width - 3] + "..."
    return text


def confirm_deletion(stdscr, item):
    prompt = f"Are you sure you want to delete '{item}'? (y/n)"
    return draw_input_box(stdscr, prompt).lower() == "y"


def open_markdown(file_path):
    def convert_and_open():
        html_path = file_path.replace(".md", ".html")
        subprocess.run(["pandoc", file_path, "-o", html_path])
        webbrowser.open(html_path)
        time.sleep(2)
        os.remove(html_path)

    thread = threading.Thread(target=convert_and_open)
    thread.start()
    thread.join()


def rename_item(stdscr, old_path):
    new_name = draw_input_box(stdscr, "Enter new name")
    if new_name:
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        os.rename(old_path, new_path)


def get_icon(file_name):
    ext = file_name.split(".")[-1].lower()
    if ext in ["png", "jpg", "jpeg", "gif"]:
        return icons["image"]
    elif ext == "md":
        return icons["markdown"]
    elif ext == "txt":
        return icons["text"]
    elif ext == "pdf":
        return icons["pdf"]
    else:
        return icons["default"]


def show_keybinds(stdscr):
    h, w = stdscr.getmaxyx()
    box_h, box_w = (
        len(keybinds) + 4,
        max(len(k) + len(v) + 4 for k, v in keybinds.items()) + 4,
    )
    box_y, box_x = (h - box_h) // 2, (w - box_w) // 2

    keybind_win = curses.newwin(box_h, box_w, box_y, box_x)
    keybind_win.box()
    keybind_win.addstr(0, 2, " Keybinds ")
    for i, (key, action) in enumerate(keybinds.items(), start=1):
        keybind_win.addstr(i + 1, 2, f"{key}: {action}")
    keybind_win.refresh()
    keybind_win.getch()


def main(stdscr):
    curses.curs_set(0)  # disappear among a sea of butterflies
    curses.start_color()

    # start the screen
    stdscr.clear()
    stdscr.refresh()

    # Get folders and files
    folders = get_folders()

    # make screen
    h, w = stdscr.getmaxyx()
    margin_h = h // 6
    margin_w = w // 6
    separation = 0
    box_h = max(2, h - (2 * margin_h))
    box_w = max(2, (w - (2 * margin_w) - separation) // 2)

    # Create le panels
    left_x, left_y = margin_w, margin_h
    left_win = curses.newwin(box_h, box_w, left_y, left_x)
    right_x = left_x + box_w + separation
    right_y = margin_h
    right_win = curses.newwin(box_h, box_w, right_y, right_x)
    left_win.box()
    right_win.box()

    left_items = list(folders["folders"].keys()) + folders["files"]

    # scroll
    left_selected = 0
    left_scroll = 0
    right_selected = 0
    right_scroll = 0

    focused_left = True  # Start on left panel

    prev_h, prev_w = h, w

    while True:
        # Check if terminal size has changed
        h, w = stdscr.getmaxyx()
        if h != prev_h or w != prev_w:
            margin_h = h // 6
            margin_w = w // 6
            box_h = max(2, h - (2 * margin_h))
            box_w = max(2, (w - (2 * margin_w) - separation) // 2)
            left_x, left_y = margin_w, margin_h
            left_win = curses.newwin(box_h, box_w, left_y, left_x)
            right_x = left_x + box_w + separation
            right_y = margin_h
            right_win = curses.newwin(box_h, box_w, right_y, right_x)
            left_win.box()
            right_win.box()
            prev_h, prev_w = h, w

        # Clear windows
        left_win.clear()
        right_win.clear()

        # Set border based on focus
        if focused_left:
            left_win.border(
                curses.ACS_VLINE,
                curses.ACS_VLINE,
                curses.ACS_HLINE,
                curses.ACS_HLINE,
                curses.ACS_ULCORNER,
                curses.ACS_URCORNER,
                curses.ACS_LLCORNER,
                curses.ACS_LRCORNER,
            )
            right_win.border(" ", " ", " ", " ", " ", " ", " ", " ")
        else:
            left_win.border(" ", " ", " ", " ", " ", " ", " ", " ")
            right_win.border(
                curses.ACS_VLINE,
                curses.ACS_VLINE,
                curses.ACS_HLINE,
                curses.ACS_HLINE,
                curses.ACS_ULCORNER,
                curses.ACS_URCORNER,
                curses.ACS_LLCORNER,
                curses.ACS_LRCORNER,
            )

        # Draw left-side panel
        for i in range(box_h - 2):
            idx = left_scroll + i
            if idx < len(left_items):
                if idx < len(folders["folders"]):
                    item_text = icons["folder"] + left_items[idx] + " "
                else:
                    item_text = get_icon(left_items[idx]) + left_items[idx] + " "
                item_text = truncate_text(item_text, box_w - 4)
                if idx == left_selected:
                    left_win.attron(curses.A_REVERSE)
                left_win.addstr(i + 1, 2, item_text)
                if idx == left_selected:
                    left_win.attroff(curses.A_REVERSE)

        # Get right-side content
        if left_selected < len(folders["folders"]):
            right_content = folders["folders"].get(left_items[left_selected], [])
        else:
            right_content = []

        # Draw right-side panel
        for i in range(box_h - 2):
            idx = right_scroll + i
            if idx < len(right_content):
                item_text = get_icon(right_content[idx]) + right_content[idx] + " "
                item_text = truncate_text(item_text, box_w - 4)
                if focused_left:
                    right_win.addstr(i + 1, 2, item_text)
                elif idx == right_selected:
                    right_win.attron(curses.A_REVERSE)
                    right_win.addstr(i + 1, 2, item_text)
                    right_win.attroff(curses.A_REVERSE)
                else:
                    right_win.addstr(i + 1, 2, item_text)

        # Refresher
        left_win.refresh()
        right_win.refresh()

        # Get input
        key = stdscr.getch()

        if key == ord(keybinds["quit"]):  # Quit
            break
        elif key == ord(keybinds["refresh"]):  # Refresh
            folders = get_folders()
            left_items = list(folders["folders"].keys()) + folders["files"]
            left_win.box()
            right_win.box()
        elif key in [ord("h"), ord("?")]:  # Show keybinds
            show_keybinds(stdscr)

        if focused_left:
            if key == curses.KEY_DOWN and left_selected < len(left_items) - 1:
                left_selected += 1
                if left_selected >= left_scroll + (box_h - 2):
                    left_scroll += 1
            elif key == curses.KEY_UP and left_selected > 0:
                left_selected -= 1
                if left_selected < left_scroll:
                    left_scroll -= 1
            elif key in [curses.KEY_RIGHT, 10, 32]:  # Right Arrow, Enter, Space
                if left_selected < len(folders["folders"]):
                    focused_left = False
                    right_selected = 0
                    right_scroll = 0
                else:
                    file = left_items[left_selected]
                    file_path = os.path.join(main_dir, file)
                    if os.path.isdir(file_path):
                        right_content = folders["folders"].get(file, [])
                    else:
                        if file.endswith((".txt", ".md")):
                            os.system(f"nano {file_path}")
                        else:
                            os.system(f"{config['open_with']} \"{file_path}\"")
            elif key == ord(keybinds["delete"]):
                item = left_items[left_selected]
                if confirm_deletion(stdscr, item):
                    if left_selected < len(folders["folders"]):
                        folder = item
                        try:
                            shutil.rmtree(os.path.join(main_dir, folder))
                        except FileNotFoundError:
                            pass
                    else:
                        file = item
                        try:
                            os.remove(os.path.join(main_dir, file))
                        except FileNotFoundError:
                            pass
                folders = get_folders()
                left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["new_folder"]):
                folder_name = draw_input_box(stdscr, "Enter folder name")
                if folder_name:
                    try:
                        os.mkdir(os.path.join(main_dir, folder_name))
                    except FileExistsError:
                        pass
                    folders = get_folders()
                    left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["new_file"]):
                file_name = draw_input_box(stdscr, "Enter file name")
                if file_name:
                    try:
                        with open(os.path.join(main_dir, file_name), "w") as f:
                            f.write(f"# {'.'.join(file_name.split('.')[:-1])}")
                    except PermissionError:  # Same name as a folder
                        pass
                    folders = get_folders()
                    left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["view_markdown"]):
                file = left_items[left_selected]
                if file.endswith(".md"):
                    open_markdown(os.path.join(main_dir, file))
            elif key == ord(keybinds["rename"]):
                item = left_items[left_selected]
                old_path = os.path.join(main_dir, item)
                rename_item(stdscr, old_path)
                folders = get_folders()
                left_items = list(folders["folders"].keys()) + folders["files"]
        else:
            if key == curses.KEY_DOWN and right_selected < len(right_content) - 1:
                right_selected += 1
                if right_selected >= right_scroll + (box_h - 2):
                    right_scroll += 1
            elif key == curses.KEY_UP and right_selected > 0:
                right_selected -= 1
                if right_selected < right_scroll:
                    right_scroll -= 1
            elif key in [curses.KEY_LEFT, 127]:  # Left Arrow or Backspace
                focused_left = True
            elif key in [curses.KEY_RIGHT, 10, 32]:
                file = right_content[right_selected]
                file_path = os.path.join(main_dir, left_items[left_selected], file)
                if os.path.isdir(file_path):
                    right_content = folders["folders"].get(
                        os.path.join(left_items[left_selected], file), []
                    )
                else:
                    if file.endswith((".txt", ".md", ".html")):
                        os.system(f"{config['open_with']} \"{file_path}\"")
                    else:
                        os.system(f'"{file_path}"')
            elif key == ord(keybinds["delete"]):
                file = right_content[right_selected]
                if confirm_deletion(stdscr, file):
                    os.remove(os.path.join(main_dir, left_items[left_selected], file))
                    folders = get_folders()
                    left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["new_file"]):
                file_name = draw_input_box(stdscr, "Enter file name")
                if file_name:
                    with open(
                        os.path.join(main_dir, left_items[left_selected], file_name),
                        "w",
                    ) as f:
                        f.write(f"# {'.'.join(file_name.split('.')[:-1])}")
                    folders = get_folders()
                    left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["view_markdown"]):
                file = right_content[right_selected]
                if file.endswith(".md"):
                    open_markdown(
                        os.path.join(main_dir, left_items[left_selected], file)
                    )
            elif key == ord(keybinds["rename"]):
                file = right_content[right_selected]
                old_path = os.path.join(main_dir, left_items[left_selected], file)
                rename_item(stdscr, old_path)
                folders = get_folders()
                left_items = list(folders["folders"].keys()) + folders["files"]


curses.wrapper(main)
