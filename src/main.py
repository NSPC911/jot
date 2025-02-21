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


def get_folders(current_dir):
    folders = {"folders": {}, "files": []}
    for root, _, files in os.walk(current_dir):
        folder = os.path.relpath(root, current_dir)
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

    current_dir = main_dir

    # Get folders and files
    folders = get_folders(current_dir)

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

    left_items = list(folders["folders"].keys()) + folders["files"]

    # scroll
    left_selected = 0
    left_scroll = 0

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
            prev_h, prev_w = h, w

        # Clear windows
        left_win.clear()
        right_win.clear()

        # Draw current path label
        current_path_label = truncate_text(current_dir, box_w - 4)
        left_win.addstr(0, 2, f" {current_path_label} ")

        # Draw left-side panel
        for i in range(box_h - 3):
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
        right_content = ""
        if left_selected < len(folders["folders"]):
            right_content = "Folder"
        else:
            file = left_items[left_selected]
            file_path = os.path.join(current_dir, file)
            if os.path.isfile(file_path):
                with open(file_path, "r") as f:
                    right_content = f.read()
            else:
                right_content = f"Opens with: {config['open_with']}"

        # Draw right-side panel
        right_lines = right_content.splitlines()
        for i in range(box_h - 2):
            if i < len(right_lines):
                right_win.addstr(i + 1, 2, truncate_text(right_lines[i], box_w - 4))

        # Draw borders
        left_win.box()
        right_win.box()

        # Refresher
        left_win.refresh()
        right_win.refresh()

        # Get input
        key = stdscr.getch()

        if key == ord(keybinds["quit"]):  # Quit
            break
        elif key == ord(keybinds["refresh"]):  # Refresh
            folders = get_folders(current_dir)
            left_items = list(folders["folders"].keys()) + folders["files"]
        elif key in [ord("h"), ord("?")]:  # Show keybinds
            show_keybinds(stdscr)

        if focused_left:
            if key == curses.KEY_DOWN and left_selected < len(left_items) - 1:
                left_selected += 1
                if left_selected >= left_scroll + (box_h - 3):
                    left_scroll += 1
            elif key == curses.KEY_UP and left_selected > 0:
                left_selected -= 1
                if left_selected < left_scroll:
                    left_scroll -= 1
            elif key in [curses.KEY_RIGHT, 10, 32]:  # Right Arrow, Enter, Space
                if left_selected < len(folders["folders"]):
                    current_dir = os.path.join(current_dir, left_items[left_selected])
                    folders = get_folders(current_dir)
                    left_items = list(folders["folders"].keys()) + folders["files"]
                    left_selected = 0
                    left_scroll = 0
                else:
                    file = left_items[left_selected]
                    file_path = os.path.join(current_dir, file)
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
                            shutil.rmtree(os.path.join(current_dir, folder))
                        except FileNotFoundError:
                            pass
                    else:
                        file = item
                        try:
                            os.remove(os.path.join(current_dir, file))
                        except FileNotFoundError:
                            pass
                folders = get_folders(current_dir)
                left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["new_folder"]):
                folder_name = draw_input_box(stdscr, "Enter folder name")
                if folder_name:
                    try:
                        os.mkdir(os.path.join(current_dir, folder_name))
                    except FileExistsError:
                        pass
                    folders = get_folders(current_dir)
                    left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["new_file"]):
                file_name = draw_input_box(stdscr, "Enter file name")
                if file_name:
                    try:
                        with open(os.path.join(current_dir, file_name), "w") as f:
                            f.write(f"# {'.'.join(file_name.split('.')[:-1])}")
                    except PermissionError:  # Same name as a folder
                        pass
                    folders = get_folders(current_dir)
                    left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == ord(keybinds["view_markdown"]):
                file = left_items[left_selected]
                if file.endswith(".md"):
                    open_markdown(os.path.join(current_dir, file))
            elif key == ord(keybinds["rename"]):
                item = left_items[left_selected]
                old_path = os.path.join(current_dir, item)
                rename_item(stdscr, old_path)
                folders = get_folders(current_dir)
                left_items = list(folders["folders"].keys()) + folders["files"]
            elif key == curses.KEY_LEFT and current_dir != main_dir:
                current_dir = os.path.dirname(current_dir)
                folders = get_folders(current_dir)
                left_items = list(folders["folders"].keys()) + folders["files"]
                left_selected = 0
                left_scroll = 0


curses.wrapper(main)
