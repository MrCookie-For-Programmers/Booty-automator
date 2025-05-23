import pyautogui
import string
import time
import os
import sys
import json
from pynput import mouse
import keyboard
import itertools
import pyperclip # Import pyperclip for safer special character handling

# --- Global Flags and Data ---
STOP_SCRIPT = False # Flag to signal the main loop to stop
current_coord_capture_index = 0 # Helper for the setup phase
mouse_listener_active = False # Flag to control pynput listener

# These are global for setup, but their effective values depends on user input in get_clicks_for_setup
num_macro_clicks_for_setup = 0 # Renamed for clarity to avoid conflict with future 'macro_click_data' parsing
num_ignored_clicks_setup = 0

# --- DEBUG MODE (Controlled by settings) ---
DEBUG_MODE = False # This will be updated by load_settings based on user's saved preference

# --- Performance-related Constants ---
# Save progress only every N iterations to reduce disk I/O.
# Adjust this value based on how frequently you want to save progress vs. performance.
PROGRESS_SAVE_INTERVAL = 100 

def clear_terminal():
    """Clears the terminal screen."""
    if settings.get('clear_screen_on_menu_display', DEFAULT_SETTINGS['clear_screen_on_menu_display']):
        os.system('cls' if os.name == 'nt' else 'clear')

def handle_enter_to_continue():
    """Prompts user to press enter if setting is enabled."""
    if settings.get('press_enter_to_exit_enabled', DEFAULT_SETTINGS['press_enter_to_exit_enabled']):
        input("Press Enter to continue...")

def debug_print(message):
    """Prints a debug message only if DEBUG_MODE is True."""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

# --- Settings and Configuration ---
# Define the default settings file path within the user's home directory
USER_HOME_DIR = os.path.expanduser('~')
DEFAULT_SETTINGS_FILE = os.path.join(USER_HOME_DIR, 'script_settings.json')

# Default settings values
DEFAULT_SETTINGS = {
    'chars': string.ascii_letters + string.digits + string.punctuation,
    'delay_between_repetitions': 0.1,
    'delay_between_macro_clicks': 0.01, # This will become a default for newly added clicks
    'pyautogui_write_interval': 0.0,
    'initial_delay_before_automation': 10.0,
    'progress_file_path': os.path.join(USER_HOME_DIR, 'progress.txt'),
    'progress_file_for_custom_list_path': os.path.join(USER_HOME_DIR, 'progressforcustomlist.txt'),
    'settings_file_path': DEFAULT_SETTINGS_FILE,
    'debug_mode': False,
    # --- New UI/Customization Settings ---
    'clear_screen_on_menu_display': True, # New: Clear terminal before showing menus
    'press_enter_to_exit_enabled': True, # New: Control "Press Enter to continue..." prompts
    'launch_message': "--- Python Combination Generator & Automation Script ---", # New: Customizable launch message
    'exit_message': "[INFO] Script has quit. Goodbye!", # New: Customizable exit message
    'menu_titles': { # New: Customizable menu titles
        'main_menu': "--- Main Menu ---",
        'settings_menu': "--- Settings Menu ---",
        'file_paths_menu': "--- File Paths Settings ---",
        'intervals_menu': "--- Interval Settings ---",
        'character_set_menu': "--- Change Character Set ---",
        'credits_page': "--- Credits ---",
        'customization_menu': "--- Customization Settings ---", # New: Title for the new customization menu
        'hotkey_failsafe_menu': "--- Hotkey & Fail-Safe Settings ---", # New: For hotkey/failsafe
        'typing_options_menu': "--- Typing Options ---", # New: For typing method
        'combo_gen_settings_menu': "--- Combination Generator Settings ---", # New: For combo gen
        'macro_click_settings_menu': "--- Macro Click Settings ---", # New: For macro clicks
    },
    'menu_options': { # New: Customizable menu options
        'main_menu_1': "1. Run Combination Generator WITH Macro Clicks",
        'main_menu_2': "2. Run Combination Generator WITHOUT Macro Clicks",
        'main_menu_3': "3. Access Settings",
        'main_menu_4': "4. Reset Combination Progress (starts from 'a')",
        'main_menu_5': "5. Process Text File (types content from a .txt file)",
        'main_menu_6': "6. Reset Custom List Progress (resets the 'progressforcustomlist.txt' file)",
        'main_menu_7': "7. Run Only Macro Clicks (no typing)",
        'main_menu_8': "8. View Credits",
        'main_menu_9': "9. Quit Script",
        'settings_menu_1': "1. Change File Paths",
        'settings_menu_2': "2. Change Intervals",
        'settings_menu_3': "3. Change Character Set",
        'settings_menu_4': "4. Toggle Debug Mode",
        'settings_menu_5': "5. Customization Options", # New option in settings menu
        'settings_menu_6': "6. Hotkey & Fail-Safe Options", # New option in settings menu
        'settings_menu_7': "7. Typing Options", # New option in settings menu
        'settings_menu_8': "8. Combination Generator Options", # New option in settings menu
        'settings_menu_9': "9. Macro Click Options", # New option in settings menu
        'settings_menu_10': "10. Reset All Settings to Default", # New reset option
        'settings_menu_B': "B. Back to Main Menu",
        'file_paths_menu_1': "1. Current Settings File Path",
        'file_paths_menu_2': "2. Current Combination Progress File Path",
        'file_paths_menu_3': "3. Current Custom List Progress File Path",
        'file_paths_menu_B': "B. Back to Settings Menu",
        'intervals_menu_1': "1. Delay Between Repetitions",
        'intervals_menu_2': "2. Delay Between Macro Clicks",
        'intervals_menu_3': "3. PyAutoGUI Write Interval",
        'intervals_menu_4': "4. Initial Delay Before Automation",
        'intervals_menu_B': "B. Back to Settings Menu",
        'customization_menu_1': "1. Toggle 'Press Enter to Continue' Prompts",
        'customization_menu_2': "2. Edit Launch Message",
        'customization_menu_3': "3. Edit Exit Message",
        'customization_menu_4': "4. Edit Menu Titles and Options",
        'customization_menu_5': "5. Toggle Clear Screen on Menu Display",
        'customization_menu_B': "B. Back to Settings Menu",
        'hotkey_failsafe_menu_1': "1. Change Stop Hotkey",
        'hotkey_failsafe_menu_2': "2. Toggle PyAutoGUI Fail-Safe",
        'hotkey_failsafe_menu_3': "3. Customize Fail-Safe Corners",
        'hotkey_failsafe_menu_B': "B. Back to Settings Menu",
        'typing_options_menu_1': "1. Change Typing Method",
        'typing_options_menu_2': "2. Change Global PyAutoGUI Pause",
        'typing_options_menu_B': "B. Back to Settings Menu",
        'combo_gen_settings_menu_1': "1. Set Minimum Combination Length",
        'combo_gen_settings_menu_2': "2. Set Maximum Combination Length",
        'combo_gen_settings_menu_3': "3. Select Character Set Preset",
        'combo_gen_settings_menu_B': "B. Back to Settings Menu",
        'macro_click_settings_menu_1': "1. Customize Individual Macro Clicks (Type & Delay)", # This will be complex
        'macro_click_settings_menu_2': "2. Set Macro Click Repetitions (for 'Only Macro Clicks' mode)",
        'macro_click_settings_menu_B': "B. Back to Settings Menu",
    },
    # --- New Functional Settings ---
    'stop_hotkey': 'ctrl+shift+c+v', # Customizable stop hotkey
    'pyautogui_failsafe_enabled': True, # Enable/disable pyautogui failsafe
    'pyautogui_failsafe_corners': ['top_left', 'top_right', 'bottom_left', 'bottom_right'], # Which corners trigger failsafe
    'typing_method': 'pyperclip_safe', # 'pyautogui_write', 'pyautogui_typewrite', 'pyperclip_safe', 'pyperclip_all'
    'pyautogui_global_pause': 0.0, # General pause for ALL pyautogui actions
    'min_combination_length': 1, # Minimum length for combination generation
    'max_combination_length': 0, # 0 means no max length (infinite)
    'only_macro_clicks_repetitions': 0, # 0 means infinite repetitions
    # Macro click data structure will change from `click_coords` to `macro_click_data`
    # each item in macro_click_data will be {'x': int, 'y': int, 'click_type': str, 'delay_after': float}
    'macro_click_data': [] # Stores detailed click information
}

# Global dictionary to hold current settings
settings = {}

# --- Settings File Functions ---
def load_settings(file_path):
    """
    Loads settings from the specified JSON file.
    Merges with DEFAULT_SETTINGS to ensure all keys are present.
    """
    global settings, DEBUG_MODE # Need to modify global DEBUG_MODE here
    loaded_settings = {}
    debug_print(f"Attempting to load settings from '{file_path}'.")
    
    if os.path.exists(file_path):
        if os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r') as f:
                    loaded_settings = json.load(f)
                debug_print(f"Successfully loaded raw settings: {loaded_settings}")
            except json.JSONDecodeError as e:
                print(f"[WARNING] Settings file '{file_path}' is corrupted or invalid JSON ({e}). Using default settings.")
                debug_print(f"JSONDecodeError: {e}")
            except Exception as e:
                print(f"[WARNING] Could not read settings file '{file_path}': {e}. Using default settings.")
                debug_print(f"General error reading settings: {e}")
        else:
            print(f"[INFO] Settings file '{file_path}' is empty. Using default settings.")
            debug_print("Settings file is empty.")
    else:
        print(f"[INFO] Settings file '{file_path}' not found. Using default settings.")
        debug_print("Settings file not found.")

    # Merge loaded settings with defaults to ensure all keys are present.
    # This also handles new settings introduced in DEFAULT_SETTINGS.
    current_settings = DEFAULT_SETTINGS.copy()
    
    # Recursive update for nested dictionaries like 'menu_titles' and 'menu_options'
    def update_dict_recursive(d_base, d_update):
        for k, v in d_update.items():
            if isinstance(v, dict) and k in d_base and isinstance(d_base[k], dict):
                d_base[k] = update_dict_recursive(d_base[k], v)
            else:
                d_base[k] = v
        return d_base

    settings_to_merge = {}
    if loaded_settings:
        settings_to_merge = loaded_settings # Use the loaded settings to merge

    settings = update_dict_recursive(current_settings, settings_to_merge)

    # Ensure 'chars' is string
    if not isinstance(settings.get('chars'), str):
        print("[WARNING] 'chars' setting invalid. Resetting to default character set.")
        debug_print("Invalid 'chars' setting, resetting to default.")
        settings['chars'] = DEFAULT_SETTINGS['chars']

    # Update global DEBUG_MODE based on loaded settings BEFORE assigning to 'settings'
    DEBUG_MODE = settings.get('debug_mode', DEFAULT_SETTINGS['debug_mode'])
    debug_print(f"DEBUG_MODE set to {DEBUG_MODE} based on loaded settings.")
    
    # Re-register hotkey if it was loaded or changed
    register_stop_hotkey()

    return settings

def save_settings(file_path, settings_data):
    """Saves the current settings to the specified JSON file."""
    debug_print(f"Attempting to save settings to '{file_path}'. Data: {settings_data}")
    try:
        # Ensure the directory for the settings file exists
        settings_dir = os.path.dirname(file_path)
        if settings_dir and not os.path.exists(settings_dir):
            os.makedirs(settings_dir, exist_ok=True)
            debug_print(f"Created directory for settings: '{settings_dir}'")

        with open(file_path, 'w') as f:
            json.dump(settings_data, f, indent=4)
        print(f"[INFO] Settings saved to '{file_path}'.")
        debug_print("Settings successfully saved.")
    except Exception as e:
        print(f"[ERROR] Could not save settings to '{file_path}': {e}")
        debug_print(f"Error saving settings: {e}")

def reset_settings_section(section_key=None):
    """
    Resets a specific section of settings or all settings to their default values.
    If section_key is None, all settings are reset.
    """
    global settings, DEBUG_MODE
    
    if section_key is None:
        print("\n[INFO] Resetting ALL settings to default values...")
        debug_print("Resetting all settings.")
        settings = DEFAULT_SETTINGS.copy()
        DEBUG_MODE = settings['debug_mode'] # Update global debug flag
        save_settings(settings['settings_file_path'], settings)
        print("[INFO] All settings have been reset to default.")
        handle_enter_to_continue()
        register_stop_hotkey() # Re-register hotkey in case it was changed
        return

    # For specific sections (e.g., 'menu_titles', 'menu_options')
    if section_key in DEFAULT_SETTINGS:
        settings[section_key] = DEFAULT_SETTINGS[section_key].copy() if isinstance(DEFAULT_SETTINGS[section_key], dict) else DEFAULT_SETTINGS[section_key]
        print(f"[INFO] Settings for '{section_key}' have been reset to default.")
    elif section_key == 'all_menu_text': # Special key to reset both menu_titles and menu_options
        settings['menu_titles'] = DEFAULT_SETTINGS['menu_titles'].copy()
        settings['menu_options'] = DEFAULT_SETTINGS['menu_options'].copy()
        print("[INFO] All menu titles and options have been reset to default.")
    else:
        print(f"[WARNING] Unknown settings section '{section_key}' to reset.")
        debug_print(f"Unknown settings section '{section_key}' requested for reset.")
        return

    save_settings(settings['settings_file_path'], settings)
    handle_enter_to_continue()


# --- Progress File Functions (for combination generation) ---
def load_progress(file_path):
    """
    Loads the last saved combination from the progress file.
    Returns None if file doesn't exist, is empty, or has invalid content.
    """
    debug_print(f"Attempting to load combination progress from '{file_path}'.")
    if not os.path.exists(file_path):
        print(f"[INFO] Progress file '{file_path}' not found. Starting from 'a'.")
        debug_print("Combination progress file does not exist.")
        return None # No previous progress
    
    if os.path.getsize(file_path) == 0:
        print(f"[INFO] Progress file '{file_path}' is empty. Starting from 'a'.")
        debug_print("Combination progress file is empty.")
        return None

    try:
        with open(file_path, 'r') as f:
            last_progress = f.readline().strip()
            if not last_progress:
                print(f"[INFO] Progress file '{file_path}' is empty after read. Starting from 'a'.")
                debug_print("Combination progress file empty after read.")
                return None
            
            # Basic validation: ensure all chars in last_progress are in CHARS set
            configured_chars = settings.get('chars', DEFAULT_SETTINGS['chars'])
            if not all(char in configured_chars for char in last_progress):
                print(f"[ERROR] Invalid characters found in progress file: '{last_progress}'. Starting from 'a'.")
                debug_print(f"Invalid characters '{last_progress}' found in combination progress file.")
                return None

            print(f"[INFO] Resuming from last saved combination progress: '{last_progress}'")
            debug_print(f"Loaded combination progress: '{last_progress}'.")
            return last_progress
    except Exception as e:
        print(f"[ERROR] Could not read combination progress file '{file_path}': {e}. Starting from 'a'.")
        debug_print(f"Error reading combination progress file: {e}.")
        return None

def save_progress(file_path, current_string):
    """Saves the current combination to the progress file, overwriting previous content."""
    debug_print(f"Attempting to save combination progress '{current_string}' to '{file_path}'.")
    try:
        # Ensure the directory for the progress file exists
        progress_dir = os.path.dirname(file_path)
        if progress_dir and not os.path.exists(progress_dir):
            os.makedirs(progress_dir, exist_ok=True)
            debug_print(f"Created directory for combination progress file: '{progress_dir}'")

        with open(file_path, 'w') as f: # Overwrite mode 'w'
            f.write(current_string + '\n')
        debug_print("Combination progress successfully saved.")
    except Exception as e:
        print(f"[ERROR] Could not save combination progress to '{file_path}': {e}")
        debug_print(f"Error saving combination progress: {e}")

def reset_progress(file_path):
    """Resets the combination progress by deleting the progress file and immediately creating an empty one."""
    debug_print(f"Attempting to reset combination progress for '{file_path}'.")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] Combination progress file '{file_path}' deleted.")
            debug_print("Existing combination progress file deleted.")
        except OSError as e:
            print(f"[ERROR] Could not delete combination progress file '{file_path}': {e}. Please delete it manually if needed.")
            debug_print(f"Error deleting combination progress file: {e}.")
    else:
        print(f"[INFO] Combination progress file '{file_path}' does not exist. No deletion needed.")
        debug_print("Combination progress file did not exist, no deletion needed.")
    
    # Always create a new empty file after deletion or if it didn't exist
    try:
        # Ensure the directory exists before creating the file
        progress_dir = os.path.dirname(file_path)
        if progress_dir and not os.path.exists(progress_dir):
            os.makedirs(progress_dir, exist_ok=True)
            debug_print(f"Created directory for new combination progress file: '{progress_dir}'")
        with open(file_path, 'w') as f:
            f.write('') # Create an empty file
        print(f"[INFO] New empty combination progress file created at '{file_path}'. Combination progress reset.")
        debug_print("New empty combination progress file created.")
    except Exception as e:
        print(f"[ERROR] Could not create new empty combination progress file at '{file_path}': {e}")
        debug_print(f"Error creating new empty combination progress file: {e}")

    handle_enter_to_continue() # Pause for user to read

# --- Progress File Functions (for custom list processing) ---
def initialize_custom_list_progress_file():
    """
    Checks if the custom list progress file exists. If not, it creates a new empty one.
    """
    file_path = settings.get('progress_file_for_custom_list_path', DEFAULT_SETTINGS['progress_file_for_custom_list_path'])
    debug_print(f"Initializing custom list progress file at '{file_path}'.")
    if not os.path.exists(file_path):
        try:
            # Ensure the directory exists
            progress_dir = os.path.dirname(file_path)
            if progress_dir and not os.path.exists(progress_dir):
                os.makedirs(progress_dir, exist_ok=True)
                debug_print(f"Created directory for custom list progress file: '{progress_dir}'")

            with open(file_path, 'w') as f:
                f.write("") # Create an empty file
            print(f"[INFO] Created new custom list progress file: {file_path}")
            debug_print("Custom list progress file created.")
        except IOError as e:
            print(f"[ERROR] Error creating custom list progress file: {e}")
            debug_print(f"Error creating custom list progress file: {e}")

def reset_custom_list_progress():
    """Resets the custom list progress by deleting the file and instantly making a new one."""
    file_path = settings.get('progress_file_for_custom_list_path', DEFAULT_SETTINGS['progress_file_for_custom_list_path'])
    print("\n--- Resetting Custom List Progress ---")
    debug_print(f"Attempting to reset custom list progress for '{file_path}'.")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] Successfully deleted existing custom list progress file: {file_path}")
            debug_print("Existing custom list progress file deleted.")
            initialize_custom_list_progress_file() # Re-create an empty one immediately
        except OSError as e:
            print(f"[ERROR] Error deleting custom list progress file: {e}")
            debug_print(f"Error deleting custom list progress file: {e}")
    else:
        print(f"[INFO] Custom list progress file not found at '{file_path}'. No need to reset.")
        debug_print("Custom list progress file did not exist, no deletion needed.")
        initialize_custom_list_progress_file() # Ensure it's created if it didn't exist
    handle_enter_to_continue() # Pause for user to read

# --- Mouse Listener Callback for Setup ---
def on_click_for_setup(x, y, button, pressed):
    """
    Callback function for pynput mouse listener during the setup phase.
    Captures the specified number of coordinates after ignoring initial clicks.
    """
    global current_coord_capture_index, mouse_listener_active, num_macro_clicks_for_setup, num_ignored_clicks_setup

    if pressed: # Only act on mouse down event
        debug_print(f"Mouse click detected at ({x}, {y}). Button: {button}. Pressed: {pressed}")
        current_coord_capture_index += 1

        # If we are still in the 'ignored clicks' phase
        if current_coord_capture_index <= num_ignored_clicks_setup:
            print(f"  Click {current_coord_capture_index} received. This click is ignored ({num_ignored_clicks_setup - current_coord_capture_index + 1} more ignored clicks).")
        else:
            # Calculate the 0-indexed position in the click_data list
            macro_click_list_index = current_coord_capture_index - num_ignored_clicks_setup - 1

            if macro_click_list_index >= 0 and macro_click_list_index < num_macro_clicks_for_setup:
                # Store default click type and delay for now. Will be customizable later.
                settings['macro_click_data'][macro_click_list_index] = {
                    'x': x,
                    'y': y,
                    'click_type': 'left', # Default to left click
                    'delay_after': settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])
                }
                print(f"  Coordinate {macro_click_list_index + 1} (X: {x}, Y: {y}) saved.")
                debug_print(f"Saved coordinate ({x}, {y}) at index {macro_click_list_index}.")

            # Check if all required macro clicks have been captured
            if (macro_click_list_index + 1) == num_macro_clicks_for_setup:
                print("  All required coordinates captured. Exiting setup mode.")
                debug_print("All macro clicks captured, stopping listener.")
                mouse_listener_active = False # Signal to stop the listener
                return False # This explicit return False stops the pynput listener

# --- Setup Phase Function ---
def get_clicks_for_setup():
    """
    Guides the user to define the number of macro clicks, ignored clicks,
    and then capture the coordinates.
    Returns True if setup is successful, False if cancelled or failed.
    """
    global current_coord_capture_index, mouse_listener_active, num_macro_clicks_for_setup, num_ignored_clicks_setup

    print("\n--- Setup Phase: Define Macro Clicks ---")
    debug_print("Starting macro clicks setup.")
    while True:
        try:
            num_str = input("How many macro clicks do you want to perform? (Enter 0 to go back to Main Menu): ").strip()
            if num_str == '0':
                print("[INFO] Returning to Main Menu.")
                debug_print("User cancelled macro setup.")
                return False # Indicate user cancelled
            
            num = int(num_str)
            if num < 0:
                print("[ERROR] Number of clicks must be a non-negative integer.")
                debug_print("Invalid input for num_macro_clicks_for_setup: negative.")
                continue
            num_macro_clicks_for_setup = num
            debug_print(f"num_macro_clicks_for_setup set to {num_macro_clicks_for_setup}.")
            break
        except ValueError:
            print("[ERROR] Please enter a valid number or 0.")
            debug_print("Invalid input for num_macro_clicks_for_setup: not a number.")

    if num_macro_clicks_for_setup == 0:
        print("[INFO] 0 macro clicks selected. Skipping coordinate capture.")
        debug_print("Skipping coordinate capture as num_macro_clicks_for_setup is 0.")
        settings['macro_click_data'] = [] # Clear any existing clicks
        save_settings(settings['settings_file_path'], settings)
        return True # Treat as successful setup, just no clicks to perform

    while True:
        try:
            num = int(input("How many initial clicks should be ignored during coordinate capture? (e.g., 1 for a warm-up click): ").strip())
            if num < 0:
                print("[ERROR] Number of ignored clicks cannot be negative.")
                debug_print("Invalid input for num_ignored_clicks_setup: negative.")
                continue
            num_ignored_clicks_setup = num
            debug_print(f"num_ignored_clicks_setup set to {num_ignored_clicks_setup}.")
            break
        except ValueError:
            print("[ERROR] Please enter a valid number.")
            debug_print("Invalid input for num_ignored_clicks_setup: not a number.")

    # Dynamically size the click_data list based on user input
    settings['macro_click_data'].clear() # Clear any previous clicks
    settings['macro_click_data'].extend([None] * num_macro_clicks_for_setup)
    current_coord_capture_index = 0 # Reset total clicks seen for new setup
    debug_print(f"macro_click_data initialized to {settings['macro_click_data']}.")

    print("\n--- Start Capturing Coordinates ---")
    if num_ignored_clicks_setup > 0:
        print(f"Make your first {num_ignored_clicks_setup} clicks anywhere on screen. These will be ignored.")
    print(f"Then, click on the exact {num_macro_clicks_for_setup} positions where you want the script to click.")
    print(f"Total clicks expected: {num_ignored_clicks_setup + num_macro_clicks_for_setup}")
    
    time.sleep(0.5) 

    mouse_listener_active = True
    debug_print("Starting pynput mouse listener.")
    with mouse.Listener(on_click=on_click_for_setup) as listener:
        listener.join() # Blocks until on_click_for_setup returns False and stops the listener

    # Final check if all clicks were indeed captured
    if None in settings['macro_click_data']:
        print("[WARNING] Not all desired macro coordinates were captured during setup. Macro clicks may be incomplete.")
        debug_print("Not all macro clicks were captured.")
        save_settings(settings['settings_file_path'], settings) # Save partially captured clicks
        return True # Treat as successful setup, just no clicks to perform
    else:
        print("\nSetup complete. All required coordinates captured!")
        debug_print("All macro clicks captured successfully.")
        save_settings(settings['settings_file_path'], settings) # Save captured clicks
        return True

# --- Combination Generator ---
def generate_all_combinations(start_combination=None):
    """
    Generates all string combinations lexicographically, starting from length 1.
    If start_combination is provided, it resumes from that point.
    This generator runs indefinitely, but respects min/max length settings.
    """
    chars_set = settings.get('chars', DEFAULT_SETTINGS['chars']) # Use configured chars
    min_len = settings.get('min_combination_length', DEFAULT_SETTINGS['min_combination_length'])
    max_len = settings.get('max_combination_length', DEFAULT_SETTINGS['max_combination_length'])
    
    debug_print(f"Character set for combination generation: '{chars_set}'. Min Length: {min_len}, Max Length: {max_len if max_len > 0 else 'Infinite'}.")
    
    # Flag to indicate if we have reached or passed the start_combination
    started_yielding = False

    actual_start_length_for_gen = min_len

    if start_combination:
        start_length = len(start_combination)
        actual_start_length_for_gen = max(min_len, start_length) # Start from current length or min_len
        debug_print(f"Attempting to resume from start_combination: '{start_combination}' (length {start_length}). Actual start length for gen: {actual_start_length_for_gen}.")
        
        # Iterate up to the starting length to find the start_combination
        for length_iter in itertools.count(min_len):
            if STOP_SCRIPT: 
                debug_print("STOP_SCRIPT detected during resume search.")
                return
            if max_len > 0 and length_iter > max_len:
                debug_print(f"Max length ({max_len}) reached during resume search. Stopping generator.")
                return # Exceeded max length while searching

            if length_iter < start_length: # Skip lengths shorter than the start_combination's length
                debug_print(f"Skipping length {length_iter} (shorter than start_combination length).")
                continue # Move to the next length

            for combo_tuple in itertools.product(chars_set, repeat=length_iter):
                if STOP_SCRIPT: 
                    debug_print("STOP_SCRIPT detected during resume search inner loop.")
                    return
                current_combo_str = ''.join(combo_tuple)
                debug_print(f"Checking combo '{current_combo_str}' against resume point '{start_combination}'.")

                # If we are at the start_combination, start yielding from here
                if current_combo_str == start_combination:
                    print(f"[INFO] Found resume point: '{start_combination}'. Resuming generation from next combination.")
                    debug_print("Resume point found. Setting started_yielding to True.")
                    started_yielding = True
                    break # Break inner loop (combinations for this length)

            if started_yielding:
                debug_print("Breaking outer loop as resume point was found.")
                break # Break outer loop (lengths)
            
            if length_iter >= start_length and not started_yielding:
                print(f"[WARNING] Resume point '{start_combination}' was not found in generated sequence (it might be invalid or deleted from character set). Starting from 'a'.")
                debug_print("Resume point not found after searching. Resetting start_combination.")
                start_combination = None # Reset to start from the beginning
                started_yielding = True # Force yielding from now on, starting with 'a'
                break # Break here to start main generation loop from length 1

        if not started_yielding and start_combination: # This case is if start_combination was provided but somehow not found (e.g., too long for current chars, or invalid)
             print(f"[WARNING] Resume point '{start_combination}' was not found (invalid or already passed). Starting from 'a'.")
             debug_print("Resume point not found and started_yielding is false. Resetting.")
             start_combination = None
             started_yielding = True # Force yielding from now on, starting with 'a'


    # Main generation loop (either from beginning or after resuming)
    for length in itertools.count(actual_start_length_for_gen):
        if STOP_SCRIPT: 
            debug_print(f"STOP_SCRIPT detected during generation for length {length}.")
            return
        
        if max_len > 0 and length > max_len:
            print(f"\n[INFO] Maximum combination length ({max_len}) reached. Stopping generation.")
            debug_print("Max length reached. Stopping generator.")
            return # Stop if max length is set and reached

        print(f"\n[INFO] Generating combinations for length: {length} (Total possible: {len(chars_set)**length})")
        debug_print(f"Generating combinations for length {length}.")

        for combo_tuple in itertools.product(chars_set, repeat=length):
            if STOP_SCRIPT: 
                debug_print(f"STOP_SCRIPT detected inside combination generation for length {length}.")
                return
            
            current_combo_str = ''.join(combo_tuple)
            
            # If we are resuming, skip until we pass the start_combination
            if start_combination and not started_yielding:
                if current_combo_str == start_combination:
                    started_yielding = True
                    debug_print(f"Passed start_combination '{start_combination}', starting to yield.")
                continue # Keep skipping until we've passed it
            
            yield current_combo_str


# --- Automation Core Functions ---
def perform_macro_clicks():
    """Performs the sequence of macro clicks defined in settings."""
    debug_print(f"Starting macro clicks. Total clicks: {len(settings['macro_click_data'])}.")
    
    # Cache settings for performance within the loop
    default_delay_between_macro_clicks = settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])

    for i, click_data in enumerate(settings['macro_click_data']):
        if STOP_SCRIPT:
            debug_print(f"STOP_SCRIPT detected during macro click {i+1}. Stopping.")
            return False # Indicate interruption
        
        if click_data is None:
            print(f"[WARNING] Macro click {i+1} has no coordinates defined. Skipping this click.")
            debug_print(f"Macro click {i+1} has no data.")
            continue

        # Directly access click_data fields, using .get for defaults
        x, y = click_data['x'], click_data['y']
        click_type = click_data.get('click_type', 'left')
        delay_after = click_data.get('delay_after', default_delay_between_macro_clicks)
        
        try:
            debug_print(f"Performing {click_type} click at ({x}, {y}). Delay after: {delay_after}s.")
            pyautogui.click(x=x, y=y, button=click_type)
            time.sleep(delay_after)
        except pyautogui.FailSafeException:
            print("\n[INFO] PyAutoGUI Fail-Safe triggered during macro clicks. Automation stopped.")
            debug_print("PyAutoGUI Fail-Safe triggered during macro clicks.")
            return False # Indicate Fail-Safe
        except Exception as e:
            print(f"[ERROR] An error occurred during macro click {i+1} at ({x}, {y}): {e}")
            debug_print(f"Error during macro click: {e}.")
            return False # Indicate error

    debug_print("All macro clicks completed.")
    return True # Indicate success

def type_string(text_to_type):
    """
    Types a given string using the configured typing method.
    Returns True on success, False if interrupted by Fail-Safe or STOP_SCRIPT.
    """
    debug_print(f"Attempting to type: '{text_to_type}'. Method: '{settings['typing_method']}'.")
    
    # Cache settings at function entry
    typing_method = settings.get('typing_method', DEFAULT_SETTINGS['typing_method'])
    pyautogui_write_interval = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
    pyautogui_global_pause = settings.get('pyautogui_global_pause', DEFAULT_SETTINGS['pyautogui_global_pause'])

    original_pyautogui_pause = pyautogui.PAUSE # Store original to restore later
    
    try:
        pyautogui.PAUSE = pyautogui_global_pause
        
        if typing_method == 'pyautogui_write':
            pyautogui.write(text_to_type, interval=pyautogui_write_interval)
            debug_print("Used pyautogui.write.")
        elif typing_method == 'pyautogui_typewrite':
            # pyautogui.typewrite is generally slower and handles special chars directly
            pyautogui.typewrite(text_to_type, interval=pyautogui_write_interval)
            debug_print("Used pyautogui.typewrite.")
        elif typing_method == 'pyperclip_safe':
            # Copy to clipboard, paste, then restore original clipboard content
            original_clipboard = pyperclip.paste()
            pyperclip.copy(text_to_type)
            pyautogui.hotkey('ctrl', 'v')
            pyperclip.copy(original_clipboard) # Restore original clipboard
            debug_print("Used pyperclip_safe.")
        elif typing_method == 'pyperclip_all':
            # Copy to clipboard and paste, leaving the text on clipboard
            pyperclip.copy(text_to_type)
            pyautogui.hotkey('ctrl', 'v')
            debug_print("Used pyperclip_all.")
        else:
            print(f"[WARNING] Unknown typing method '{typing_method}'. Defaulting to 'pyautogui_write'.")
            pyautogui.write(text_to_type, interval=pyautogui_write_interval)
            debug_print("Used default pyautogui.write due to unknown method.")
        
        return True # Typing successful
    except pyautogui.FailSafeException:
        print("\n[INFO] PyAutoGUI Fail-Safe triggered during typing. Automation stopped.")
        debug_print("PyAutoGUI Fail-Safe triggered during typing.")
        return False # Indicate Fail-Safe
    except Exception as e:
        print(f"[ERROR] An error occurred during typing: {e}")
        debug_print(f"Error during typing: {e}.")
        return False # Indicate error
    finally:
        pyautogui.PAUSE = original_pyautogui_pause # Restore original pause after action

def run_automation_loop(include_macro_clicks, process_custom_list=False, custom_list_path=None):
    """
    Main automation loop.
    If process_custom_list is True, it reads and types lines from a file.
    Otherwise, it generates combinations.
    """
    global STOP_SCRIPT
    STOP_SCRIPT = False # Reset flag for a new run

    # Cache frequently used settings values at the start of the loop for performance
    initial_delay = settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])
    delay_between_repetitions = settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])
    pyautogui_failsafe_enabled = settings.get('pyautogui_failsafe_enabled', DEFAULT_SETTINGS['pyautogui_failsafe_enabled'])
    pyautogui_global_pause = settings.get('pyautogui_global_pause', DEFAULT_SETTINGS['pyautogui_global_pause'])
    stop_hotkey_display = settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])
    configured_failsafe_corners = settings.get('pyautogui_failsafe_corners', DEFAULT_SETTINGS['pyautogui_failsafe_corners'])
    
    pyautogui.FAILSAFE = pyautogui_failsafe_enabled
    pyautogui.HIGHSPEED = False # The easter egg that was missed! Re-added.

    # Set PyAutoGUI failsafe corners
    corner_map = {
        'top_left': (0, 0),
        'top_right': (pyautogui.size().width - 1, 0),
        'bottom_left': (0, pyautogui.size().height - 1),
        'bottom_right': (pyautogui.size().width - 1, pyautogui.size().height - 1)
    }
    # Clear failsafe points and add only the configured ones
    pyautogui.DEFAULTS['failSafePoints'] = []
    for corner_name in configured_failsafe_corners:
        if corner_name in corner_map:
            pyautogui.DEFAULTS['failSafePoints'].append(corner_map[corner_name])
            debug_print(f"Added failsafe corner: {corner_name} {corner_map[corner_name]}")
        else:
            debug_print(f"[WARNING] Unknown failsafe corner: {corner_name}")

    print(f"\n[INFO] Starting automation in {initial_delay} seconds...")
    print(f"[INFO] Press '{stop_hotkey_display}' to stop the script at any time.")
    if pyautogui.FAILSAFE:
        print("[INFO] PyAutoGUI Fail-Safe is ENABLED. Move your mouse to a corner of the screen to stop.")
    else:
        print("[INFO] PyAutoGUI Fail-Safe is DISABLED. Be cautious!")
    debug_print(f"Initial delay: {initial_delay}s. Repetition delay: {delay_between_repetitions}s.")
    debug_print(f"Fail-Safe enabled: {pyautogui.FAILSAFE}. Failsafe corners: {pyautogui.DEFAULTS['failSafePoints']}.")
    time.sleep(initial_delay)

    if process_custom_list:
        file_path = custom_list_path or settings.get('progress_file_for_custom_list_path', DEFAULT_SETTINGS['progress_file_for_custom_list_path'])
        debug_print(f"Processing custom list from: '{file_path}'.")
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            lines = [line.strip() for line in lines if line.strip()]
            debug_print(f"Loaded {len(lines)} lines from custom list file.")
        except FileNotFoundError:
            print(f"[ERROR] Custom list file not found at '{file_path}'. Returning to main menu.")
            debug_print(f"Custom list file not found: {file_path}.")
            handle_enter_to_continue()
            return
        except Exception as e:
            print(f"[ERROR] Error reading custom list file '{file_path}': {e}. Returning to main menu.")
            debug_print(f"Error reading custom list file: {e}.")
            handle_enter_to_continue()
            return

        if not lines:
            print("[INFO] Custom list file is empty. Nothing to process. Returning to main menu.")
            debug_print("Custom list file is empty.")
            handle_enter_to_continue()
            return

        progress_index_file = file_path + ".index"
        last_processed_index = 0
        if os.path.exists(progress_index_file):
            try:
                with open(progress_index_file, 'r') as f:
                    last_processed_index = int(f.readline().strip())
                if last_processed_index >= len(lines):
                    print(f"[INFO] All lines in '{file_path}' previously processed. Starting from the beginning.")
                    debug_print("All lines in custom list processed. Resetting index.")
                    last_processed_index = 0
                else:
                    print(f"[INFO] Resuming custom list processing from line {last_processed_index + 1}.")
                    debug_print(f"Resuming custom list from index: {last_processed_index}.")
            except (ValueError, IOError) as e:
                print(f"[WARNING] Could not load custom list progress from '{progress_index_file}': {e}. Starting from line 1.")
                debug_print(f"Error loading custom list progress: {e}.")
                last_processed_index = 0
        else:
            print("[INFO] No custom list progress found. Starting from line 1.")
            debug_print("No custom list progress file found.")

        for i in range(last_processed_index, len(lines)):
            if STOP_SCRIPT:
                print("\n[INFO] Script stopped by user hotkey. Saving custom list progress.")
                debug_print("STOP_SCRIPT detected during custom list processing.")
                with open(progress_index_file, 'w') as f:
                    f.write(str(i)) # Save the index of the line *just processed* or about to be processed
                break
            
            current_line = lines[i]
            print(f"Typing custom list line {i+1}/{len(lines)}: '{current_line}'")
            debug_print(f"Processing custom list line: '{current_line}'.")

            if include_macro_clicks:
                if not perform_macro_clicks():
                    print("[INFO] Macro clicks failed or were interrupted during custom list processing. Saving custom list progress.")
                    with open(progress_index_file, 'w') as f:
                        f.write(str(i))
                    break
            
            if not type_string(current_line):
                print("[INFO] Typing failed or was interrupted during custom list processing. Saving custom list progress.")
                with open(progress_index_file, 'w') as f:
                    f.write(str(i))
                break
            
            time.sleep(delay_between_repetitions)

            # Save progress periodically instead of every iteration
            if (i + 1) % PROGRESS_SAVE_INTERVAL == 0:
                debug_print(f"Saving custom list progress at iteration {i + 1}.")
                with open(progress_index_file, 'w') as f:
                    f.write(str(i + 1))
        else: # This block executes if the loop completes without a 'break'
            print("\n[INFO] All lines in the custom list have been processed.")
            debug_print("All lines in custom list processed successfully.")
            with open(progress_index_file, 'w') as f:
                f.write("0") # Reset progress to start from beginning next time
            print("[INFO] Custom list progress has been reset for next run.")
        
        # Ensure progress is saved if the loop finishes or breaks
        if not STOP_SCRIPT: # Only save if not already saved by a break
             with open(progress_index_file, 'w') as f:
                f.write(str(len(lines))) # Mark as fully processed, or the last completed index + 1


    else: # Combination Generator mode
        start_from = load_progress(settings['progress_file_path'])
        
        # Keep track of combinations processed for periodic saving
        combinations_processed_count = 0 
        last_saved_combo = start_from if start_from else ""

        for combo in generate_all_combinations(start_from):
            if STOP_SCRIPT:
                print("\n[INFO] Script stopped by user hotkey. Saving combination progress.")
                debug_print("STOP_SCRIPT detected during combination generation.")
                save_progress(settings['progress_file_path'], combo)
                break
            
            print(f"Typing combination: '{combo}'")
            debug_print(f"Processing combination: '{combo}'.")

            if include_macro_clicks:
                if not perform_macro_clicks():
                    print("[INFO] Macro clicks failed or were interrupted during combination generation. Saving combination progress.")
                    save_progress(settings['progress_file_path'], combo)
                    break
            
            if not type_string(combo):
                print("[INFO] Typing failed or was interrupted during combination generation. Saving combination progress.")
                save_progress(settings['progress_file_path'], combo)
                    # No need to save progress as `type_string` handles FailSafe and sets STOP_SCRIPT
                break
            
            time.sleep(delay_between_repetitions)

            # Save progress periodically instead of every iteration
            combinations_processed_count += 1
            if combinations_processed_count % PROGRESS_SAVE_INTERVAL == 0:
                debug_print(f"Saving combination progress for '{combo}' at iteration {combinations_processed_count}.")
                save_progress(settings['progress_file_path'], combo)
                last_saved_combo = combo
        else:
            print("\n[INFO] Combination generation completed based on max length setting.")
            debug_print("Combination generation loop completed.")
            # Save final progress if loop completes
            if not STOP_SCRIPT and last_saved_combo:
                save_progress(settings['progress_file_path'], last_saved_combo)
                debug_print("Final combination progress saved upon completion.")
            
    print(settings.get('exit_message', DEFAULT_SETTINGS['exit_message']))
    handle_enter_to_continue() # Pause for user to read

# --- Hotkey Handling ---
_stop_hotkey_listener = None # Global variable to hold the keyboard listener

def on_key_press_stop(event):
    """Callback function for the stop hotkey."""
    global STOP_SCRIPT
    debug_print(f"Hotkey '{settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])}' pressed. Signalling script to stop.")
    STOP_SCRIPT = True

def register_stop_hotkey():
    """Registers the global hotkey to stop the script."""
    global _stop_hotkey_listener
    
    # If a listener is already active, stop it before registering a new one
    if _stop_hotkey_listener:
        debug_print("Stopping existing hotkey listener.")
        try:
            _stop_hotkey_listener.stop()
            _stop_hotkey_listener.join(timeout=1) # Give it a moment to stop
        except Exception as e:
            debug_print(f"Error stopping old hotkey listener: {e}")
        _stop_hotkey_listener = None

    hotkey = settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])
    debug_print(f"Attempting to register hotkey: '{hotkey}'")
    try:
        # pynput keyboard.GlobalHotKey is a non-blocking listener
        _stop_hotkey_listener = keyboard.add_hotkey(hotkey, on_key_press_stop, suppress=True)
        print(f"[INFO] Stop hotkey '{hotkey}' registered.")
        debug_print("Hotkey registered successfully.")
    except Exception as e:
        print(f"[ERROR] Could not register hotkey '{hotkey}': {e}. Please ensure it's not already in use by another application.")
        debug_print(f"Error registering hotkey: {e}")
        # If hotkey registration fails, ensure script can still be stopped
        # by advising manual termination or focusing on Fail-Safe.

def unregister_stop_hotkey():
    """Unregisters the global hotkey."""
    global _stop_hotkey_listener
    if _stop_hotkey_listener:
        debug_print("Unregistering stop hotkey.")
        try:
            keyboard.remove_hotkey(on_key_press_stop) # remove_hotkey works on the callback
            _stop_hotkey_listener = None # Clear the global listener reference
            debug_print("Hotkey unregistered.")
        except Exception as e:
            debug_print(f"Error unregistering hotkey: {e}")

# --- Menu Functions ---
def display_menu(menu_name, options_prefix):
    """Displays a generic menu based on settings."""
    clear_terminal()
    print(settings.get('menu_titles', DEFAULT_SETTINGS['menu_titles']).get(menu_name, f"--- {menu_name.replace('_', ' ').title()} ---"))
    for key, value in sorted(settings.get('menu_options', DEFAULT_SETTINGS['menu_options']).items()):
        if key.startswith(options_prefix):
            print(value)
    print("-" * 30)

def get_user_choice(max_option, back_option='B'):
    """Gets validated user input for menu choices."""
    while True:
        choice = input("Enter your choice: ").strip().upper()
        if choice == back_option:
            return choice
        if choice.isdigit():
            num_choice = int(choice)
            if 1 <= num_choice <= max_option:
                return num_choice
        print("[ERROR] Invalid choice. Please enter a valid option.")

def main_menu():
    """Displays the main menu and handles user choices."""
    while True:
        clear_terminal()
        display_menu('main_menu', 'main_menu_')
        choice = get_user_choice(9, back_option='Q') # Q for quit
        
        if choice == 1:
            run_automation_loop(include_macro_clicks=True)
        elif choice == 2:
            run_automation_loop(include_macro_clicks=False)
        elif choice == 3:
            settings_menu()
        elif choice == 4:
            reset_progress(settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path']))
        elif choice == 5:
            # For processing a custom text file, ask for the path
            while True:
                custom_file_path = input("Enter the full path to your text file (e.g., C:\\Users\\User\\list.txt): ").strip()
                if os.path.exists(custom_file_path) and custom_file_path.lower().endswith('.txt'):
                    run_automation_loop(include_macro_clicks=False, process_custom_list=True, custom_list_path=custom_file_path)
                    break
                else:
                    print("[ERROR] Invalid file path or not a .txt file. Please try again.")
        elif choice == 6:
            reset_custom_list_progress()
        elif choice == 7:
            repetitions = settings.get('only_macro_clicks_repetitions', DEFAULT_SETTINGS['only_macro_clicks_repetitions'])
            if not settings['macro_click_data']:
                print("[WARNING] No macro clicks are configured. Please set them up in Macro Click Options (Settings -> Macro Click Options -> Customize Individual Macro Clicks).")
                handle_enter_to_continue()
                continue

            if repetitions == 0:
                print(f"\n[INFO] Running macro clicks indefinitely. Press '{settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])}' to stop.")
                while not STOP_SCRIPT:
                    if not perform_macro_clicks():
                        break # Stop if clicks fail or failsafe is triggered
                    time.sleep(settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions']))
            else:
                print(f"\n[INFO] Running macro clicks {repetitions} times. Press '{settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])}' to stop.")
                for _ in range(repetitions):
                    if STOP_SCRIPT:
                        break
                    if not perform_macro_clicks():
                        break
                    time.sleep(settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions']))
            print(settings.get('exit_message', DEFAULT_SETTINGS['exit_message']))
            handle_enter_to_continue()
            STOP_SCRIPT = False # Reset stop flag after completion/interruption
        elif choice == 8:
            display_credits()
        elif choice == 'Q':
            print(settings.get('exit_message', DEFAULT_SETTINGS['exit_message']))
            handle_enter_to_continue()
            unregister_stop_hotkey()
            sys.exit()

def settings_menu():
    """Displays the settings menu and handles user choices."""
    while True:
        clear_terminal()
        display_menu('settings_menu', 'settings_menu_')
        choice = get_user_choice(10, back_option='B')

        if choice == 1:
            file_paths_menu()
        elif choice == 2:
            intervals_menu()
        elif choice == 3:
            change_character_set()
        elif choice == 4:
            toggle_debug_mode()
        elif choice == 5:
            customization_menu()
        elif choice == 6:
            hotkey_failsafe_menu()
        elif choice == 7:
            typing_options_menu()
        elif choice == 8:
            combo_gen_settings_menu()
        elif choice == 9:
            macro_click_settings_menu()
        elif choice == 10:
            reset_settings_section(None) # Reset all settings
        elif choice == 'B':
            break # Back to main menu

def file_paths_menu():
    """Allows user to change file paths."""
    while True:
        clear_terminal()
        display_menu('file_paths_menu', 'file_paths_menu_')
        print(f"  Current Settings File Path: {settings.get('settings_file_path')}")
        print(f"  Current Combination Progress File Path: {settings.get('progress_file_path')}")
        print(f"  Current Custom List Progress File Path: {settings.get('progress_file_for_custom_list_path')}")
        choice = get_user_choice(3, back_option='B')

        if choice == 1:
            new_path = input("Enter new path for Settings File (e.g., C:\\Users\\User\\new_settings.json): ").strip()
            if new_path:
                settings['settings_file_path'] = new_path
                save_settings(new_path, settings)
                print("[INFO] Please restart the script for the new settings file path to take full effect.")
            else:
                print("[INFO] Path not changed.")
            handle_enter_to_continue()
        elif choice == 2:
            new_path = input("Enter new path for Combination Progress File (e.g., C:\\Users\\User\\new_progress.txt): ").strip()
            if new_path:
                settings['progress_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
            else:
                print("[INFO] Path not changed.")
            handle_enter_to_continue()
        elif choice == 3:
            new_path = input("Enter new path for Custom List Progress File (e.g., C:\\Users\\User\\new_custom_progress.txt): ").strip()
            if new_path:
                settings['progress_file_for_custom_list_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
                initialize_custom_list_progress_file() # Ensure new file is initialized
            else:
                print("[INFO] Path not changed.")
            handle_enter_to_continue()
        elif choice == 'B':
            break

def intervals_menu():
    """Allows user to change interval settings."""
    while True:
        clear_terminal()
        display_menu('intervals_menu', 'intervals_menu_')
        print(f"  1. Delay Between Repetitions: {settings.get('delay_between_repetitions')} seconds")
        print(f"  2. Delay Between Macro Clicks: {settings.get('delay_between_macro_clicks')} seconds")
        print(f"  3. PyAutoGUI Write Interval: {settings.get('pyautogui_write_interval')} seconds")
        print(f"  4. Initial Delay Before Automation: {settings.get('initial_delay_before_automation')} seconds")
        choice = get_user_choice(4, back_option='B')

        try:
            if choice == 1:
                new_value = float(input("Enter new delay between repetitions (seconds): ").strip())
                if new_value >= 0:
                    settings['delay_between_repetitions'] = new_value
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Value must be non-negative.")
            elif choice == 2:
                new_value = float(input("Enter new delay between macro clicks (seconds): ").strip())
                if new_value >= 0:
                    settings['delay_between_macro_clicks'] = new_value
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Value must be non-negative.")
            elif choice == 3:
                new_value = float(input("Enter new PyAutoGUI write interval (seconds, 0 for no interval): ").strip())
                if new_value >= 0:
                    settings['pyautogui_write_interval'] = new_value
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Value must be non-negative.")
            elif choice == 4:
                new_value = float(input("Enter new initial delay before automation starts (seconds): ").strip())
                if new_value >= 0:
                    settings['initial_delay_before_automation'] = new_value
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Value must be non-negative.")
            elif choice == 'B':
                break
            else:
                print("[ERROR] Invalid input. Please enter a number or 'B'.")
        except ValueError:
            print("[ERROR] Invalid input. Please enter a valid number.")
        handle_enter_to_continue()

def change_character_set():
    """Allows user to change the character set for combination generation."""
    while True:
        clear_terminal()
        display_menu('character_set_menu', 'combo_gen_settings_menu_') # Using a similar menu for presets
        print(f"  Current character set: '{settings.get('chars')}'")
        print("\nChoose a preset or enter a custom set:")
        print("1. All (letters, digits, punctuation)")
        print("2. Alphabetic (a-z, A-Z)")
        print("3. Alphanumeric (a-z, A-Z, 0-9)")
        print("4. Digits (0-9)")
        print("5. Custom (enter your own characters)")
        print("B. Back to Settings Menu")

        choice = input("Enter your choice: ").strip().upper()

        new_chars = None
        if choice == '1':
            new_chars = string.ascii_letters + string.digits + string.punctuation
        elif choice == '2':
            new_chars = string.ascii_letters
        elif choice == '3':
            new_chars = string.ascii_letters + string.digits
        elif choice == '4':
            new_chars = string.digits
        elif choice == '5':
            new_chars = input("Enter your custom character set (e.g., 'abc123!@#'): ").strip()
            if not new_chars:
                print("[ERROR] Custom character set cannot be empty.")
                handle_enter_to_continue()
                continue
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice.")
            handle_enter_to_continue()
            continue

        if new_chars is not None:
            settings['chars'] = new_chars
            save_settings(settings['settings_file_path'], settings)
            print(f"[INFO] Character set updated to: '{new_chars}'")
        handle_enter_to_continue()
        break # Exit after successful update or back

def toggle_debug_mode():
    """Toggles debug mode on/off."""
    global DEBUG_MODE
    current_status = settings.get('debug_mode', DEFAULT_SETTINGS['debug_mode'])
    new_status = not current_status
    settings['debug_mode'] = new_status
    DEBUG_MODE = new_status # Update global flag immediately
    save_settings(settings['settings_file_path'], settings)
    print(f"[INFO] Debug mode is now {'ENABLED' if new_status else 'DISABLED'}.")
    handle_enter_to_continue()

def customization_menu():
    """Menu for UI/message customization."""
    while True:
        clear_terminal()
        display_menu('customization_menu', 'customization_menu_')
        print(f"  1. Toggle 'Press Enter to Continue' Prompts: {'Enabled' if settings.get('press_enter_to_exit_enabled') else 'Disabled'}")
        print(f"  2. Edit Launch Message: '{settings.get('launch_message')}'")
        print(f"  3. Edit Exit Message: '{settings.get('exit_message')}'")
        print(f"  4. Edit Menu Titles and Options (resets to default)")
        print(f"  5. Toggle Clear Screen on Menu Display: {'Enabled' if settings.get('clear_screen_on_menu_display') else 'Disabled'}")
        choice = get_user_choice(5, back_option='B')

        if choice == 1:
            settings['press_enter_to_exit_enabled'] = not settings.get('press_enter_to_exit_enabled')
            print(f"[INFO] 'Press Enter to Continue' prompts are now {'ENABLED' if settings.get('press_enter_to_exit_enabled') else 'DISABLED'}.")
        elif choice == 2:
            new_message = input("Enter new launch message: ").strip()
            if new_message:
                settings['launch_message'] = new_message
                print("[INFO] Launch message updated.")
            else:
                print("[INFO] Launch message not changed (cannot be empty).")
        elif choice == 3:
            new_message = input("Enter new exit message: ").strip()
            if new_message:
                settings['exit_message'] = new_message
                print("[INFO] Exit message updated.")
            else:
                print("[INFO] Exit message not changed (cannot be empty).")
        elif choice == 4:
            confirm = input("This will reset all menu titles and options to default. Are you sure? (yes/no): ").strip().lower()
            if confirm == 'yes':
                reset_settings_section('all_menu_text')
            else:
                print("[INFO] Menu titles and options not reset.")
            handle_enter_to_continue()
            continue # Go back to customization menu after reset
        elif choice == 5:
            settings['clear_screen_on_menu_display'] = not settings.get('clear_screen_on_menu_display')
            print(f"[INFO] Clear screen on menu display is now {'ENABLED' if settings.get('clear_screen_on_menu_display') else 'DISABLED'}.")
        elif choice == 'B':
            break
        
        save_settings(settings['settings_file_path'], settings)
        handle_enter_to_continue()

def hotkey_failsafe_menu():
    """Menu for hotkey and PyAutoGUI failsafe settings."""
    while True:
        clear_terminal()
        display_menu('hotkey_failsafe_menu', 'hotkey_failsafe_menu_')
        print(f"  1. Stop Hotkey: '{settings.get('stop_hotkey')}'")
        print(f"  2. PyAutoGUI Fail-Safe: {'Enabled' if settings.get('pyautogui_failsafe_enabled') else 'Disabled'}")
        print(f"  3. Custom Fail-Safe Corners: {', '.join(settings.get('pyautogui_failsafe_corners'))}")
        choice = get_user_choice(3, back_option='B')

        if choice == 1:
            new_hotkey = input("Enter new stop hotkey (e.g., 'ctrl+q' or 'ctrl+alt+delete'): ").strip().lower()
            if new_hotkey:
                settings['stop_hotkey'] = new_hotkey
                save_settings(settings['settings_file_path'], settings)
                register_stop_hotkey() # Re-register the hotkey with the new value
                print(f"[INFO] Stop hotkey updated to '{new_hotkey}'.")
            else:
                print("[INFO] Hotkey not changed.")
        elif choice == 2:
            settings['pyautogui_failsafe_enabled'] = not settings.get('pyautogui_failsafe_enabled')
            save_settings(settings['settings_file_path'], settings)
            print(f"[INFO] PyAutoGUI Fail-Safe is now {'ENABLED' if settings.get('pyautogui_failsafe_enabled') else 'DISABLED'}.")
            print("[INFO] Changes will apply on next automation run.")
        elif choice == 3:
            print("\nEnter corner names separated by commas (e.g., 'top_left, bottom_right').")
            print("Valid corners: 'top_left', 'top_right', 'bottom_left', 'bottom_right'.")
            corners_str = input("New fail-safe corners: ").strip().lower()
            if corners_str:
                new_corners = [c.strip() for c in corners_str.split(',') if c.strip() in ['top_left', 'top_right', 'bottom_left', 'bottom_right']]
                if new_corners:
                    settings['pyautogui_failsafe_corners'] = new_corners
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[INFO] Fail-safe corners updated to: {', '.join(new_corners)}.")
                    print("[INFO] Changes will apply on next automation run.")
                else:
                    print("[ERROR] No valid corners entered. Keeping current settings.")
            else:
                print("[INFO] Fail-safe corners not changed.")
        elif choice == 'B':
            break
        handle_enter_to_continue()

def typing_options_menu():
    """Menu for typing method and global PyAutoGUI pause."""
    while True:
        clear_terminal()
        display_menu('typing_options_menu', 'typing_options_menu_')
        print(f"  1. Current Typing Method: '{settings.get('typing_method')}'")
        print(f"  2. Global PyAutoGUI Pause: {settings.get('pyautogui_global_pause')} seconds")
        choice = get_user_choice(2, back_option='B')

        if choice == 1:
            print("\nSelect a typing method:")
            print("  1. pyautogui_write (Default, good balance)")
            print("  2. pyautogui_typewrite (Slower, handles some special chars directly)")
            print("  3. pyperclip_safe (Fastest, copies to clipboard, pastes, restores original clipboard)")
            print("  4. pyperclip_all (Fastest, copies to clipboard, pastes, leaves text on clipboard)")
            method_choice = input("Enter method choice (1-4): ").strip()
            methods = {
                '1': 'pyautogui_write',
                '2': 'pyautogui_typewrite',
                '3': 'pyperclip_safe',
                '4': 'pyperclip_all'
            }
            if method_choice in methods:
                settings['typing_method'] = methods[method_choice]
                save_settings(settings['settings_file_path'], settings)
                print(f"[INFO] Typing method updated to '{settings['typing_method']}'.")
            else:
                print("[ERROR] Invalid method choice.")
        elif choice == 2:
            try:
                new_value = float(input("Enter new global PyAutoGUI pause (seconds, 0 for no pause): ").strip())
                if new_value >= 0:
                    settings['pyautogui_global_pause'] = new_value
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[INFO] Global PyAutoGUI pause set to {new_value} seconds.")
                else:
                    print("[ERROR] Value must be non-negative.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter a valid number.")
        elif choice == 'B':
            break
        handle_enter_to_continue()

def combo_gen_settings_menu():
    """Menu for combination generator specific settings."""
    while True:
        clear_terminal()
        display_menu('combo_gen_settings_menu', 'combo_gen_settings_menu_')
        print(f"  1. Minimum Combination Length: {settings.get('min_combination_length')}")
        print(f"  2. Maximum Combination Length: {settings.get('max_combination_length')} (0 for infinite)")
        print(f"  3. Current Character Set: '{settings.get('chars')}'")
        choice = get_user_choice(3, back_option='B')

        if choice == 1:
            try:
                new_min_len = int(input("Enter new minimum combination length (e.g., 1): ").strip())
                if new_min_len >= 1:
                    settings['min_combination_length'] = new_min_len
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[INFO] Minimum combination length set to {new_min_len}.")
                else:
                    print("[ERROR] Minimum length must be at least 1.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter a valid integer.")
        elif choice == 2:
            try:
                new_max_len = int(input("Enter new maximum combination length (0 for infinite): ").strip())
                if new_max_len >= 0:
                    settings['max_combination_length'] = new_max_len
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[INFO] Maximum combination length set to {new_max_len} (infinite if 0).")
                else:
                    print("[ERROR] Value must be non-negative.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter a valid integer.")
        elif choice == 3:
            change_character_set() # Link to existing character set function
            continue # Stay in combo_gen_settings_menu after changing chars
        elif choice == 'B':
            break
        handle_enter_to_continue()

def macro_click_settings_menu():
    """Menu for macro click specific settings."""
    global num_macro_clicks_for_setup # Needed if get_clicks_for_setup updates this
    while True:
        clear_terminal()
        display_menu('macro_click_settings_menu', 'macro_click_settings_menu_')
        
        # Display current macro click data
        if settings['macro_click_data']:
            print("\n--- Current Macro Clicks ---")
            for i, click_data in enumerate(settings['macro_click_data']):
                if click_data:
                    print(f"  Click {i+1}: X={click_data['x']}, Y={click_data['y']}, Type='{click_data.get('click_type', 'left')}', Delay={click_data.get('delay_after', DEFAULT_SETTINGS['delay_between_macro_clicks'])}s")
                else:
                    print(f"  Click {i+1}: (Not yet captured or invalid)")
            print("----------------------------")
        else:
            print("\n[INFO] No macro clicks configured. Use option 1 to set them up.")
        
        print(f"  2. Macro Click Repetitions (for 'Only Macro Clicks' mode): {settings.get('only_macro_clicks_repetitions')} (0 for infinite)")

        choice = get_user_choice(2, back_option='B')

        if choice == 1:
            # Re-run setup to re-capture/customize clicks
            if get_clicks_for_setup(): # get_clicks_for_setup handles saving clicks
                print("[INFO] Macro click setup completed.")
            else:
                print("[INFO] Macro click setup cancelled or failed.")
            handle_enter_to_continue()
            
            # Offer customization for each click if there are any
            if settings['macro_click_data']:
                while True:
                    print("\n--- Customize Individual Macro Clicks ---")
                    print("Enter the number of the click to customize (1-{}). Enter 0 to finish.".format(len(settings['macro_click_data'])))
                    print("To change coordinates, you need to re-run '1. Customize Individual Macro Clicks'.")
                    
                    try:
                        click_index_choice = int(input("Enter click number to customize (0 to finish): ").strip())
                        if click_index_choice == 0:
                            break
                        if 1 <= click_index_choice <= len(settings['macro_click_data']):
                            target_index = click_index_choice - 1
                            click_data = settings['macro_click_data'][target_index]
                            if not click_data:
                                print("[WARNING] This click has no data. Cannot customize.")
                                handle_enter_to_continue()
                                continue
                            
                            print(f"\nCustomizing Click {click_index_choice} (X: {click_data['x']}, Y: {click_data['y']}):")
                            
                            # Customize click type
                            current_type = click_data.get('click_type', 'left')
                            print(f"  Current Type: '{current_type}'")
                            new_type = input("Enter new click type ('left', 'right', 'middle', or leave blank for current): ").strip().lower()
                            if new_type in ['left', 'right', 'middle']:
                                click_data['click_type'] = new_type
                                print(f"  Click type updated to '{new_type}'.")
                            elif new_type == '':
                                print("  Click type unchanged.")
                            else:
                                print("[ERROR] Invalid click type. Keeping current.")
                            
                            # Customize delay after click
                            current_delay = click_data.get('delay_after', DEFAULT_SETTINGS['delay_between_macro_clicks'])
                            print(f"  Current Delay After: {current_delay}s")
                            try:
                                new_delay_str = input("Enter new delay after click (seconds, or leave blank for current): ").strip()
                                if new_delay_str:
                                    new_delay = float(new_delay_str)
                                    if new_delay >= 0:
                                        click_data['delay_after'] = new_delay
                                        print(f"  Delay after click updated to {new_delay}s.")
                                    else:
                                        print("[ERROR] Delay must be non-negative. Keeping current.")
                                else:
                                    print("  Delay after click unchanged.")
                            except ValueError:
                                print("[ERROR] Invalid delay. Please enter a valid number. Keeping current.")
                            
                            settings['macro_click_data'][target_index] = click_data # Update in settings
                            save_settings(settings['settings_file_path'], settings)
                            handle_enter_to_continue()

                        else:
                            print("[ERROR] Invalid click number.")
                            handle_enter_to_continue()
                    except ValueError:
                        print("[ERROR] Invalid input. Please enter a number.")
                        handle_enter_to_continue()
            
        elif choice == 2:
            try:
                new_repetitions = int(input("Enter number of repetitions for 'Only Macro Clicks' mode (0 for infinite): ").strip())
                if new_repetitions >= 0:
                    settings['only_macro_clicks_repetitions'] = new_repetitions
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[INFO] Macro click repetitions set to {new_repetitions} (infinite if 0).")
                else:
                    print("[ERROR] Repetitions must be non-negative.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter a valid integer.")
        elif choice == 'B':
            break
        handle_enter_to_continue()

def display_credits():
    """Displays script credits."""
    clear_terminal()
    print(settings.get('menu_titles', DEFAULT_SETTINGS['menu_titles']).get('credits_page', DEFAULT_SETTINGS['menu_titles']['credits_page']))
    print("Google gemini, Requests done by me, MrCookie")
    print("This script utilizes the following libraries:")
    print("- pyautogui: For automation (keyboard and mouse control)")
    print("- pynput: For global mouse listener (for capturing click coordinates)")
    print("- keyboard: For global hotkey detection (to stop the script)")
    print("- pyperclip: For cross-platform clipboard operations (for safer typing methods)")
    print("- itertools: For efficient combination generation")
    print("\nSpecial thanks to the open-source community for these amazing tools!")
    print("\n-----------------------------------------------------------")
    print("Version: 1.0.0 (Customizable)") # Example version, keep updated manually
    print("-----------------------------------------------------------")
    handle_enter_to_continue()

# --- Main Script Execution ---
if __name__ == "__main__":
    # Load settings at startup
    settings = load_settings(DEFAULT_SETTINGS_FILE)
    
    # Initialize the custom list progress file if it doesn't exist
    initialize_custom_list_progress_file()

    # Display initial launch message
    clear_terminal()
    print(settings.get('launch_message', DEFAULT_SETTINGS['launch_message']))
    handle_enter_to_continue()

    # Register the stop hotkey once at the start of the script
    register_stop_hotkey()

    main_menu() # Start the main menu loop