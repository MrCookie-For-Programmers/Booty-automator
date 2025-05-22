ALL CREDITS: google gemini, dont worry i was involed a bit too (wich is why i  fucked up the readme at the beginning lmao) 


CHANGELOGS: Added settings menu (very useful), Added saving progress, added changing amount of macro clicks. have fun! New: Check it out, too many changes to list here. overall important: booty debug is now merged into normal booty, check out the settings!

Automated Combinatorial Typist & Macro

This Python script is designed to systematically generate all possible character combinations (lowercase letters, uppercase letters, digits, and special characters), type each combination twice, and optionally perform a sequence of user-defined mouse clicks twice. It's a continuous automation tool, perfect for tasks that require repetitive input generation and interaction.

Features

Comprehensive Generation: Generates all string combinations using a-z, A-Z, 0-9, and common special characters (punctuation), starting from length 1 and incrementally increasing length indefinitely.
Double Repetition: Each generated combination is typed twice, and the associated macro clicks (if enabled) are also performed twice.
Flexible Operation: An interactive main menu allows you to choose between:
"With Macro Clicks": Types the string and then performs 3 configurable mouse clicks.
"Without Macro Clicks": Only types the string, skipping all click actions.
User-Defined Clicks: If running with macro clicks, you'll be prompted to click on your screen to define the three mouse click coordinates interactively at the start of the script.
No Progress Saving: The script always starts fresh from the beginning of its combination sequence ('a' at length 1) each time it's launched.
Graceful Stopping: The script can be stopped at any time by pressing Ctrl+Shift+C+V, moving your mouse to any screen corner (pyautogui's built-in fail-safe), or pressing Ctrl+C in the terminal.
Persistent Terminal Output: The console window will remain open after the script stops, allowing you to review the full output.
Debug Version: A special version provides verbose, technical output for detailed troubleshooting and understanding the script's internal workings.
Prerequisites

Before running the script, ensure you have Python installed and the following libraries. You can install them using pip:

pip install pyautogui pynput keyboard

How to Use (Standard Version)

Download the Script: Save the standard script file (Booty.py) to your computer.
Run the Script: Open your terminal or command prompt, navigate to the directory where you saved the script, and run it using: python Booty.py (Alternatively, you can usually double-click the .py file if your system is configured for it.)
Main Menu Selection: The script will present a menu. Enter 1 to run with macro clicks or 2 to run without, then press Enter.
Initial Countdown: The script will pause for 10 seconds. Use this time to open and prepare the application where you want the script to type.
Define Click Coordinates (if 'With Macro' chosen): If you selected to run with macro clicks, you'll be prompted to click on your screen to define the three coordinates for the macro. Follow the on-screen instructions.
Automation Begins: The script will start generating combinations, typing them, and performing actions.
Stop the Script: To stop it gracefully, press Ctrl+Shift+C+V. You can also move your mouse to any screen corner to trigger pyautogui's fail-safe, or press Ctrl+C in your terminal. The terminal window will stay open for you to review the output.
How to Use (Debug Version for Nerds)

The debug version (booty debug.py) functions identically to the standard version but provides extremely verbose output in the terminal. This is useful for:

Troubleshooting: Pinpointing exactly where the script might be encountering an issue.
Understanding Flow: Seeing step-by-step what functions are being called, what variables hold, and which conditional paths are taken.
To use it, follow the same steps as the "Standard Version," but run the specific debug script file:

python "booty debug.py"

Be prepared for a lot of text in your terminal!

Disclaimer

This script performs automated actions on your computer. Use it responsibly and understand its behavior. Moving your mouse to a screen corner is a universal fail-safe for pyautogui scripts, allowing you to regain control if the script behaves unexpectedly. The author is not responsible for any unintended consequences of using this script.
