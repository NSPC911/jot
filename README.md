# jot.

## Overview
jot. is a note manager through the CLI. It is a simple two-panel app to show everything you need

## Install
1. Clone the repository
2. Enter into `jot/src`
3. Based on your terminal
  - If you are using bash/zsh, make `jot.sh` an executable file and add it to <kbd>$PATH</kbd>
  - If you are using pwsh/cmd, add `path/to/jot/src` to <kbd>%PATH%</kbd>
4. Edit `config.json` to your preference

## Default config
  - `main_dir`: Houses the notes
  - `open_with`: Uses the app of your choice to open the markdown files. This can be Vim, VSCode `code --wait` or any other editor you want

### Keybinds
  - `q`: Quit
  - `n`: Create a new file
  - `N`: Create a new folder
  - `d`: Delete the selected file or folder
  - `v`: View the selected markdown file in the browser using pandoc
  - <kbd>Enter</kbd>: Open the file with `open_with` or your default set editor for other types of files (like PDFs or DOCX)

## License
This project is licensed under the MIT License.
