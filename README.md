# SCRIPT IS CURRENTLY BROKEN, PLEASE WAIT FOR A REUPLOAD!
# Python Automation & Combination Generator
This script is a versatile Python-based automation tool that combines a powerful string combination generator with robust mouse macro and typing capabilities. It's designed to automate repetitive tasks, generate character combinations, and process text files with customizable precision.
Features
 * Combination Generation:
   * Generates all possible string combinations based on a user-defined character set (e.g., a, A, 0-9, symbols).
   * Supports minimum and maximum combination lengths.
   * Resumes generation from the last saved point, preventing loss of progress.
 * Macro Clicking:
   * Allows users to define multiple mouse click coordinates, click types (left, right, middle), and delays between clicks.
   * Ideal for automating interactions with applications or web pages.
 * Text File Processing:
   * Reads and types content line-by-line from a specified text file.
   * Maintains progress, resuming from the last processed line.
 * Customizable Settings:
   * Adjustable delays for repetitions, macro clicks, and initial automation startup.
   * Configurable file paths for saving progress and settings.
   * User-defined character set for combination generation.
   * Toggleable debug mode for troubleshooting.
   * Customizable UI messages, menu titles, and options for a personalized experience.
 * Hotkey & Fail-Safe:
   * Set a custom hotkey to instantly stop the script at any time.
   * PyAutoGUI Fail-Safe mechanism can be enabled/disabled and customized to trigger on mouse movement to screen corners.
 * Typing Options:
   * Choose between various typing methods (pyautogui.write, pyautogui.typewrite, pyperclip_safe, pyperclip_all) to handle different characters and optimize performance.
   * Global PyAutoGUI pause setting for fine-grained control over automation speed.
 * Persistent Configuration:
   * All settings and progress are automatically saved to JSON files in your user's home directory (script_settings.json, progress.txt, progressforcustomlist.txt).
Requirements
The script requires the following Python libraries:
 * pyautogui
 * pynput
 * keyboard
 * pyperclip
You can install them using pip:
pip install pyautogui pynput keyboard pyperclip

How to Use
 * Run the Script:
   python Booty.py

 * Initial Setup: On the first launch, the script will guide you through an initial setup process to configure basic settings like the stop hotkey and initial delays.
 * Main Menu: After setup, you will be presented with a main menu allowing you to choose from various operations:
   * Run Combination Generator (with or without macro clicks)
   * Process a Text File (with or without macro clicks)
   * Run Only Macro Clicks
   * Access Settings (to customize delays, character sets, file paths, UI, hotkeys, typing methods, and combination generator options)
   * Reset Combination or Custom List Progress
   * View Credits
   * Quit Script
 * Macro Click Setup (if applicable): If you choose to run with macro clicks, the script will prompt you to define the number of clicks and then guide you to click on the screen locations where you want the automated clicks to occur. You can also specify a number of "ignored clicks" before the actual coordinates are captured.
 * Stopping the Script:
   * Press the configured stop hotkey (default: ctrl+shift+c+v).
   * If enabled, move your mouse cursor to any of the fail-safe corners of the screen (default: all four corners).
Configuration
Settings are saved in script_settings.json in your user's home directory. Progress for combination generation is saved in progress.txt and for custom list processing in progressforcustomlist.txt, also in your home directory.
You can modify most settings directly through the script's in-app menus.
Key Settings
 * chars: The character set used for combination generation. Can be changed via the "Change Character Set" menu.
 * delay_between_repetitions: Delay after each combination is typed or each line is processed.
 * delay_between_macro_clicks: Default delay between individual macro clicks.
 * pyautogui_write_interval: Interval between characters when using PyAutoGUI's typing methods.
 * initial_delay_before_automation: Initial countdown before automation begins, allowing you to switch to the target application.
 * stop_hotkey: The keyboard shortcut to stop the script.
 * pyautogui_failsafe_enabled: Boolean to enable/disable PyAutoGUI's built-in fail-safe.
 * pyautogui_failsafe_corners: List of screen corners that trigger the fail-safe.
 * typing_method: Selects how the script types text (pyautogui_write, pyautogui_typewrite, pyperclip_safe, pyperclip_all). pyperclip_safe is generally recommended for special characters.
 * pyautogui_global_pause: A general pause applied after every PyAutoGUI call.
 * min_combination_length / max_combination_length: Define the length range for generated combinations.
 * macro_click_data: Stores the x, y coordinates, click_type, and delay_after for each defined macro click.
 * debug_mode: Enable for detailed console output.
License
This project is open-source and distributed under the terms of the GNU General Public License v3.0 (GPLv3).
The GPLv3 is a "copyleft" license, which means:
 * You are free to use, study, modify, and distribute this software.
 * If you redistribute the software (with or without modifications), you must also make it available under the same GPLv3 terms.
 * This explicitly prevents others from taking the code, modifying it, and then selling that modified, proprietary version. Any distributed version must remain free and open.
Warranty and Liability
The GPLv3 license inherently includes clauses regarding warranty and liability. To the extent permitted by applicable law:
 * There is NO WARRANTY for this program. It is provided "as is" without any guarantee of performance, merchantability, or fitness for a particular purpose.
 * The copyright holders (MrCookie and Gemini) shall NOT be liable for any damages (direct, indirect, incidental, special, exemplary, or consequential) arising from the use or inability to use this program.
For the full text of the license, please refer to the LICENSE file in this repository.
Copyright
Copyright (C) 2025 MrCookie and Gemini

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
Development & Contribution
The main coding was done by Gemini, with contributions from MrCookie. Feel free to explore the code, report issues, or suggest improvements.
