Python Automation & Combination Generator
This script is a versatile Python-based automation tool that combines a powerful string combination generator with robust mouse macro and typing capabilities. It's designed to automate repetitive tasks, generate character combinations, and process text files with customizable precision.

Features
Combination Generation:
Generates all possible string combinations based on a user-defined character set (e.g., a, A, 0-9, symbols).
Supports minimum and maximum combination lengths.
Resumes generation from the last saved point, preventing loss of progress.
Macro Clicking:
Allows users to define multiple mouse click coordinates, click types (left, right, middle), and delays between clicks.
Ideal for automating interactions with applications or web pages.
Text File Processing:
Reads and types content line-by-line from a specified text file.
Maintains progress, resuming from the last processed line.
Customizable Settings:
Adjustable delays for repetitions, macro clicks, and initial automation startup.
Configurable file paths for saving progress and settings.
User-defined character set for combination generation.
Toggleable debug mode for troubleshooting.
Customizable UI messages, menu titles, and options for a personalized experience.
Hotkey & Fail-Safe:
Set a custom hotkey to instantly stop the script at any time.
PyAutoGUI Fail-Safe mechanism can be enabled/disabled and customized to trigger on mouse movement to screen corners.
Typing Options:
Choose between various typing methods (pyautogui.write, pyautogui.typewrite, pyperclip_safe, pyperclip_all) to handle different characters and optimize performance.
Global PyAutoGUI pause setting for fine-grained control over automation speed.
Persistent Configuration:
All settings and progress are automatically saved to JSON files in your user's home directory (script_settings.json, progress.txt, progressforcustomlist.txt).
Requirements
The script requires the following Python libraries:

pyautogui
pynput
keyboard
pyperclip
You can install them using pip:

Bash

pip install pyautogui pynput keyboard pyperclip
How to Use
Run the Script:
Bash

python Booty.py
Initial Setup: On the first launch, the script will guide you through an initial setup process to configure basic settings like the stop hotkey and initial delays.
Main Menu: After setup, you will be presented with a main menu allowing you to choose from various operations:
Run Combination Generator (with or without macro clicks)
Process a Text File (with or without macro clicks)
Run Only Macro Clicks
Access Settings (to customize delays, character sets, file paths, UI, hotkeys, typing methods, and combination generator options)
Reset Combination or Custom List Progress
View Credits
Quit Script
Macro Click Setup (if applicable): If you choose to run with macro clicks, the script will prompt you to define the number of clicks and then guide you to click on the screen locations where you want the automated clicks to occur. You can also specify a number of "ignored clicks" before the actual coordinates are captured.
Stopping the Script:
Press the configured stop hotkey (default: ctrl+shift+c+v).
If enabled, move your mouse cursor to any of the fail-safe corners of the screen (default: all four corners).
Configuration
Settings are saved in script_settings.json in your user's home directory. Progress for combination generation is saved in progress.txt and for custom list processing in progressforcustomlist.txt, also in your home directory.

You can modify most settings directly through the script's in-app menus.

Key Settings
chars: The character set used for combination generation. Can be changed via the "Change Character Set" menu.
delay_between_repetitions: Delay after each combination is typed or each line is processed.
delay_between_macro_clicks: Default delay between individual macro clicks.
pyautogui_write_interval: Interval between characters when using PyAutoGUI's typing methods.
initial_delay_before_automation: Initial countdown before automation begins, allowing you to switch to the target application.
stop_hotkey: The keyboard shortcut to stop the script.
pyautogui_failsafe_enabled: Boolean to enable/disable PyAutoGUI's built-in fail-safe.
pyautogui_failsafe_corners: List of screen corners that trigger the fail-safe.
typing_method: Selects how the script types text (pyautogui_write, pyautogui_typewrite, pyperclip_safe, pyperclip_all). pyperclip_safe is generally recommended for special characters.
pyautogui_global_pause: A general pause applied after every PyAutoGUI call.
min_combination_length / max_combination_length: Define the length range for generated combinations.
macro_click_data: Stores the x, y coordinates, click_type, and delay_after for each defined macro click.
debug_mode: Enable for detailed console output.
Development & Contribution
The main coding was done by Gemini, with contributions from MrCookie. Feel free to explore the code, report issues, or suggest improvements.

License
This project is open-source. 
