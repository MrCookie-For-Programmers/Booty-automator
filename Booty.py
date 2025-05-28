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
    'user_name': "goofball", # NEW: User's customizable name
    'first_launch_done': False, # NEW: Flag for first-time setup
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
        # 'macro_click_settings_menu': "--- Macro Click Settings ---", # REMOVED: Macro clicks configured dynamically
    },
    'menu_options': { # New: Customizable menu options
        'main_menu_0': "0. How to Use / Instructions", # NEW: Instructions option
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
        # 'settings_menu_9': "9. Macro Click Options", # REMOVED: Macro clicks configured dynamically
        'settings_menu_9': "9. Reset All Settings to Default", # Moved reset option to here
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
        'customization_menu_6': "6. Set User Name", # NEW: Option for user name
        'customization_menu_7': "7. Toggle Shutdown PC on Completion", # NEW: Shutdown on completion option
        'customization_menu_B': "B. Back to Settings Menu",
        'hotkey_failsafe_menu_1': "1. Change Stop Hotkey",
        'hotkey_failsafe_menu_2': "2. Toggle PyAutoGUI Fail-Safe",
        'hotkey_failsafe_3': "3. Customize Fail-Safe Corners",
        'hotkey_failsafe_menu_B': "B. Back to Settings Menu",
        'typing_options_menu_1': "1. Change Typing Method",
        'typing_options_menu_2': "2. Change Global PyAutoGUI Pause",
        'typing_options_menu_B': "B. Back to Settings Menu",
        'combo_gen_settings_menu_1': "1. Set Minimum Combination Length",
        'combo_gen_settings_menu_2': "2. Set Maximum Combination Length",
        'combo_gen_settings_menu_3': "3. Select Character Set Preset",
        'combo_gen_settings_menu_B': "B. Back to Settings Menu",
        # 'macro_click_settings_menu_1': "1. Customize Individual Macro Clicks (Type & Delay)", # REMOVED
        # 'macro_click_settings_menu_2': "2. Set Macro Click Repetitions (for 'Only Macro Clicks' mode)", # REMOVED
        # 'macro_click_settings_menu_B': "B. Back to Settings Menu", # REMOVED
    },
    # --- New Functional Settings ---
    'stop_hotkey': 'ctrl+shift+c+v', # Customizable stop hotkey
    'pyautogui_failsafe_enabled': True, # Enable/disable pyautogui failsafe
    'pyautogui_failsafe_corners': ['top_left', 'top_right', 'bottom_left', 'bottom_right'], # Which corners trigger failsafe
    'typing_method': 'pyperclip_safe', # 'pyautogui_write', 'pyautogui_typewrite', 'pyperclip_safe', 'pyperclip_all'
    'pyautogui_global_pause': 0.0, # General pause for ALL pyautogui actions
    'min_combination_length': 1, # Minimum length for combination generation
    'max_combination_length': 0, # 0 means no max length (infinite)
    'only_macro_clicks_repetitions': 0, # 0 means infinite repetitions (This will be set dynamically now)
    # Macro click data structure will change from `click_coords` to `macro_click_data`
    # each item in macro_click_data will be {'x': int, 'y': int, 'click_type': str, 'delay_after': float}
    'macro_click_data': [], # Stores detailed click information
    'shutdown_on_completion': False # NEW: Toggle for shutting down PC after successful completion
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
            print(f"[ERROR] Error deleting custom list progress file: {file_path}: {e}")
            debug_print(f"Error deleting custom list progress file: {e}")
    else:
        print(f"[INFO] Custom list file not found at '{file_path}'. No need to reset.")
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
        # No need to save settings here, as dynamic repetitions will handle it later.
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
        # No save_settings here, as the full automation loop will handle it.
        return True # Treat as successful setup, just no clicks to perform
    else:
        print("\nSetup complete. All required coordinates captured!")
        debug_print("All macro clicks captured successfully.")
        # No save_settings here, as the full automation loop will handle it.
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

    if not settings['macro_click_data']:
        print("[WARNING] No macro click coordinates are defined. Skipping macro clicks.")
        return True # Consider it successful if there's nothing to do

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
        
        # ADD THIS LINE TO PRESS ENTER AFTER TYPING
        pyautogui.press('enter') 
        debug_print("Pressed 'enter' after typing.")

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

def run_automation_loop(include_macro_clicks, process_custom_list=False, custom_list_path=None, repetitions=0):
    """
    Main automation loop. If process_custom_list is True, it reads and types lines from a file.
    Otherwise, it generates combinations. 'repetitions' defines how many times the whole loop should repeat (0 for infinite).
    """
    global STOP_SCRIPT
    STOP_SCRIPT = False # Reset flag for a new run
    automation_completed_naturally = False # Flag to track natural completion

    # Cache frequently used settings values at the start of the loop for performance
    initial_delay = settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])
    delay_between_repetitions = settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])
    pyautogui_failsafe_enabled = settings.get('pyautogui_failsafe_enabled', DEFAULT_SETTINGS['pyautogui_failsafe_enabled'])
    pyautogui_global_pause = settings.get('pyautogui_global_pause', DEFAULT_SETTINGS['pyautogui_global_pause'])
    stop_hotkey_display = settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])
    configured_failsafe_corners = settings.get('pyautogui_failsafe_corners', DEFAULT_SETTINGS['pyautogui_failsafe_corners'])
    shutdown_on_completion_enabled = settings.get('shutdown_on_completion', DEFAULT_SETTINGS['shutdown_on_completion']) # NEW: Get shutdown setting

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
    """
    pyautogui.DEFAULTS['failSafePoints'] = []
    for corner_name in configured_failsafe_corners:
        if corner_name in corner_map:
            pyautogui.DEFAULTS['failSafePoints'].append(corner_map[corner_name])
            debug_print(f"Added failsafe corner: {corner_name} {corner_map[corner_name]}")
        else:
            debug_print(f"[WARNING] Unknown failsafe corner: {corner_name}")
    """
    print(f"\n[INFO] Starting automation in {initial_delay} seconds...")
    print(f"[INFO] Press '{stop_hotkey_display}' to stop the script at any time.")
    if pyautogui.FAILSAFE:
        print("[INFO] PyAutoGUI Fail-Safe is ENABLED. Move your mouse to a corner of the screen to stop.")
    else:
        print("[INFO] PyAutoGUI Fail-Safe is DISABLED. Be cautious!")
    debug_print(f"Initial delay: {initial_delay}s. Repetition delay: {delay_between_repetitions}s.")
    time.sleep(initial_delay)

    iteration_count = 0
    while repetitions == 0 or iteration_count < repetitions:
        if STOP_SCRIPT:
            print("\n[INFO] Script stopped by user hotkey.")
            debug_print("STOP_SCRIPT detected, breaking repetition loop.")
            break # Exit the loop if STOP_SCRIPT is True

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
                break # Exit if file not found

            # Find the starting line based on progress file
            custom_list_progress_file = settings.get('progress_file_for_custom_list_path', DEFAULT_SETTINGS['progress_file_for_custom_list_path'])
            last_typed_line = None
            if os.path.exists(custom_list_progress_file) and os.path.getsize(custom_list_progress_file) > 0:
                try:
                    with open(custom_list_progress_file, 'r') as f:
                        last_typed_line = f.readline().strip()
                    print(f"[INFO] Resuming custom list from after: '{last_typed_line}'.")
                    debug_print(f"Loaded last typed line: '{last_typed_line}'.")
                except Exception as e:
                    print(f"[WARNING] Could not read custom list progress file: {e}. Starting from beginning of list.")
                    debug_print(f"Error reading custom list progress: {e}.")
                    last_typed_line = None
            else:
                print("[INFO] No custom list progress found. Starting from beginning of list.")

            start_index = 0
            if last_typed_line:
                try:
                    start_index = lines.index(last_typed_line) + 1
                    print(f"[INFO] Starting custom list processing from line {start_index + 1}.")
                except ValueError:
                    print(f"[WARNING] Last typed line '{last_typed_line}' not found in the custom list. Starting from beginning.")
                    debug_print(f"Last typed line '{last_typed_line}' not found in current custom list. Starting from 0.")
                    start_index = 0
            
            if start_index >= len(lines):
                print("[INFO] All lines in the custom list have already been processed. Returning to main menu.")
                debug_print("All lines in custom list processed.")
                handle_enter_to_continue()
                automation_completed_naturally = True # Consider natural completion for this mode
                break # All lines processed, exit loop

            for i in range(start_index, len(lines)):
                if STOP_SCRIPT:
                    print("\n[INFO] Script stopped by user hotkey during custom list processing.")
                    debug_print("STOP_SCRIPT detected during custom list processing.")
                    break # Exit inner loop if STOP_SCRIPT is True
                
                line_to_type = lines[i]
                print(f"[{i+1}/{len(lines)}] Typing custom list entry: {line_to_type}")
                debug_print(f"Typing custom list entry: '{line_to_type}'.")
                
                if not type_string(line_to_type):
                    # type_string returns False if Fail-Safe or other error occurred
                    STOP_SCRIPT = True # Ensure STOP_SCRIPT is set for the outer loop to break
                    print("[INFO] Typing interrupted. Returning to main menu.")
                    break # Break the inner loop

                # Save progress after each line typed
                try:
                    with open(custom_list_progress_file, 'w') as f:
                        f.write(line_to_type + '\n')
                    debug_print(f"Saved custom list progress: '{line_to_type}'.")
                except Exception as e:
                    print(f"[ERROR] Could not save custom list progress: {e}")
                    debug_print(f"Error saving custom list progress: {e}.")

                if STOP_SCRIPT:
                    break # If typing was interrupted, break outer loop too

            if not STOP_SCRIPT and (start_index + (len(lines) - start_index)) == len(lines):
                print("\n[INFO] Finished processing all entries in the custom list.")
                debug_print("Finished processing all custom list entries.")
                automation_completed_naturally = True # This mode completed naturally
                handle_enter_to_continue()
                break # All lines processed, exit loop

            if STOP_SCRIPT: # Check again after inner loop
                break

        else: # Combination Generator or Only Macro Clicks
            if include_macro_clicks:
                if not perform_macro_clicks(): # Perform clicks first
                    STOP_SCRIPT = True # Set flag if clicks were interrupted
                    print("[INFO] Macro clicks interrupted. Returning to main menu.")
                    break # Exit the main loop if clicks failed

            if not STOP_SCRIPT: # Only proceed with typing if not stopped by clicks
                current_progress = load_progress(settings['progress_file_path'])
                combination_generator = generate_all_combinations(start_combination=current_progress)

                # Iterate through combinations and type them
                try:
                    for combo in combination_generator:
                        if STOP_SCRIPT:
                            print("\n[INFO] Script stopped by user hotkey during combination generation.")
                            debug_print("STOP_SCRIPT detected during combination generation.")
                            break # Exit inner loop
                        
                        print(f"Typing: {combo} (Iteration: {iteration_count + 1})")
                        debug_print(f"Typing combo: '{combo}'.")

                        if not type_string(combo):
                            # type_string returns False if Fail-Safe or other error occurred
                            STOP_SCRIPT = True # Ensure STOP_SCRIPT is set for the outer loop to break
                            print("[INFO] Typing interrupted. Returning to main menu.")
                            break # Break the inner loop
                        
                        # Save progress periodically to reduce disk I/O
                        if (iteration_count + 1) % PROGRESS_SAVE_INTERVAL == 0:
                            save_progress(settings['progress_file_path'], combo)

                        # Pause between repetitions
                        time.sleep(delay_between_repetitions)

                        iteration_count += 1
                        if repetitions > 0 and iteration_count >= repetitions:
                            print(f"\n[INFO] Reached desired number of repetitions: {repetitions}.")
                            debug_print(f"Reached {repetitions} repetitions.")
                            automation_completed_naturally = True # Natural completion if repetitions are met
                            break # Exit the combination loop
                except pyautogui.FailSafeException:
                    print("\n[INFO] PyAutoGUI Fail-Safe triggered during combination generation. Automation stopped.")
                    debug_print("PyAutoGUI Fail-Safe triggered during combination generation.")
                    STOP_SCRIPT = True # Set flag to break outer loop
                except Exception as e:
                    print(f"[ERROR] An unexpected error occurred during automation: {e}")
                    debug_print(f"Unexpected error during automation: {e}.")
                    STOP_SCRIPT = True # Set flag to break outer loop

            if STOP_SCRIPT: # Check after combination generator loop
                break # Exit the main while loop

        # If repetitions are set and reached, or if custom list finished, break the overall loop
        if repetitions > 0 and iteration_count >= repetitions:
            debug_print("Outer loop condition: repetitions met.")
            automation_completed_naturally = True
            break
        elif process_custom_list and automation_completed_naturally: # If custom list finished, automation_completed_naturally already set
            debug_print("Outer loop condition: custom list completed naturally.")
            break
        elif process_custom_list and STOP_SCRIPT: # If custom list was stopped prematurely
            debug_print("Outer loop condition: custom list stopped by user.")
            break

    # --- Post-Automation Actions ---
    if automation_completed_naturally and shutdown_on_completion_enabled:
        print("\n[INFO] Automation completed successfully and 'Shutdown PC on Completion' is enabled.")
        print("[INFO] Shutting down your PC in 5 seconds...")
        time.sleep(5) # Give user a moment to see the message
        try:
            # Use appropriate shutdown command for the OS
            if os.name == 'nt': # For Windows
                os.system('shutdown /s /t 1') 
            elif os.name == 'posix': # For Linux/macOS
                # NOTE: This might require root privileges (sudo).
                # User might need to run the script with sudo or configure sudoers.
                os.system('sudo shutdown -h now')
            else:
                print("[WARNING] Automatic shutdown not supported on this operating system.")
                debug_print("Automatic shutdown not supported on current OS.")
        except Exception as e:
            print(f"[ERROR] Failed to execute shutdown command: {e}")
            debug_print(f"Error executing shutdown command: {e}.")
    elif STOP_SCRIPT:
        print("[INFO] Script was manually stopped. Returning to main menu.")
    else:
        print("[INFO] Automation finished. Returning to main menu.")

    handle_enter_to_continue()


# --- Menu Functions ---
def show_how_to_use():
    """Displays instructions on how to use the script."""
    clear_terminal()
    print(settings['menu_options']['main_menu_0'].replace("0. ", "\n--- ") + " ---")
    print("\nThis script automates typing of character combinations or lines from a text file,")
    print("and can optionally perform mouse clicks at predefined locations.")
    print("\nKey features:")
    print("  - **Combination Generator**: Types all possible combinations of characters (e.g., a, b, ..., aa, ab, ...)")
    print("  - **Custom List Processor**: Reads lines from a specified text file and types each line.")
    print("  - **Macro Clicks**: Perform mouse clicks at recorded coordinates.")
    print("  - **Persistent Settings & Progress**: Saves your configurations and automation progress.")
    print("  - **Customizable**: Adjust character sets, delays, hotkeys, UI messages, and more.")
    print("\nHow to get started:")
    print("1. **Initial Setup**: The first time you run the script, it will guide you through a quick setup.")
    print("   This includes setting your name and other basic preferences.")
    print("2. **Define Macro Clicks (Optional)**: If you want to use mouse clicks, select option 7 in the main menu ('Run Only Macro Clicks')")
    print("   or option 1 ('Run Combination Generator WITH Macro Clicks') to enter the setup phase for clicks.")
    print("   Follow the on-screen instructions to record your click positions.")
    print("3. **Configure Settings**: Access the 'Settings' menu (Option 3) to customize:")
    print("   - **File Paths**: Where progress and settings files are stored.")
    print("   - **Intervals**: Delays between typing actions and clicks.")
    print("   - **Character Set**: What characters are used for combination generation.")
    print("   - **Debug Mode**: Toggle detailed logging for troubleshooting.")
    print("   - **Customization Options**: Change UI messages, clear screen behavior, and prompts.")
    print("   - **Hotkey & Fail-Safe**: Set your emergency stop hotkey and configure PyAutoGUI's fail-safe corners.")
    print("   - **Typing Options**: Choose between different typing methods (pyautogui.write, pyperclip, etc.).")
    print("   - **Combination Generator Options**: Set min/max length for combinations, select character set presets.")
    print("4. **Run Automation**:")
    print("   - **Combination Generator**: Select option 1 or 2 from the main menu.")
    print("   - **Custom List Processor**: Select option 5 and provide the path to your .txt file.")
    print("   - **Only Macro Clicks**: Select option 7 to run only the recorded mouse clicks.")
    print("5. **Stop Script**: Use your configured stop hotkey (default: ctrl+shift+c+v) or move your mouse to a screen corner if fail-safe is enabled.")
    print("\nRemember to explore the 'Settings' menu for more advanced customization!")
    handle_enter_to_continue()


def show_settings_menu():
    """Displays the settings menu and handles user input."""
    while True:
        clear_terminal()
        print(settings['menu_titles']['settings_menu'])
        print(settings['menu_options']['settings_menu_1'])
        print(settings['menu_options']['settings_menu_2'])
        print(settings['menu_options']['settings_menu_3'])
        print(settings['menu_options']['settings_menu_4'])
        print(settings['menu_options']['settings_menu_5']) # Customization Options
        print(settings['menu_options']['settings_menu_6']) # Hotkey & Fail-Safe Options
        print(settings['menu_options']['settings_menu_7']) # Typing Options
        print(settings['menu_options']['settings_menu_8']) # Combination Generator Options
        # print(settings['menu_options']['settings_menu_9']) # Macro Click Options - REMOVED
        print(settings['menu_options']['settings_menu_9']) # Reset All Settings to Default
        print(settings['menu_options']['settings_menu_B'])

        choice = input("Enter your choice: ").strip().upper()

        if choice == '1':
            show_file_paths_menu()
        elif choice == '2':
            show_intervals_menu()
        elif choice == '3':
            change_character_set()
        elif choice == '4':
            toggle_debug_mode()
        elif choice == '5':
            show_customization_menu() # New menu for customization
        elif choice == '6':
            show_hotkey_failsafe_menu() # New menu for hotkey/failsafe
        elif choice == '7':
            show_typing_options_menu() # New menu for typing options
        elif choice == '8':
            show_combo_gen_settings_menu() # New menu for combo gen options
        # elif choice == '9': # REMOVED: Macro clicks configured dynamically now
        #     show_macro_click_settings_menu()
        elif choice == '9': # Reset All Settings to Default (re-used '9')
            confirm = input("Are you sure you want to reset ALL settings to default? (yes/no): ").strip().lower()
            if confirm == 'yes':
                reset_settings_section(None) # Pass None to reset all
            else:
                print("[INFO] Settings reset cancelled.")
                debug_print("Settings reset cancelled by user.")
                handle_enter_to_continue()
        elif choice == 'B':
            break # Go back to main menu
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in settings menu: {choice}.")
            handle_enter_to_continue()

def show_file_paths_menu():
    """Displays and allows changing file paths."""
    while True:
        clear_terminal()
        print(settings['menu_titles']['file_paths_menu'])
        print(f"{settings['menu_options']['file_paths_menu_1']}: {settings['settings_file_path']}")
        print(f"{settings['menu_options']['file_paths_menu_2']}: {settings['progress_file_path']}")
        print(f"{settings['menu_options']['file_paths_menu_3']}: {settings['progress_file_for_custom_list_path']}")
        print(settings['menu_options']['file_paths_menu_B'])

        choice = input("Enter your choice (1-3 to change, B to go back): ").strip().upper()

        if choice == '1':
            new_path = input("Enter new settings file path: ").strip()
            if new_path:
                settings['settings_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
                print("[INFO] Settings file path updated. Please restart the script for full effect.")
            else:
                print("[INFO] Path cannot be empty. Using current path.")
        elif choice == '2':
            new_path = input("Enter new combination progress file path: ").strip()
            if new_path:
                settings['progress_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings) # Save updated settings
                print("[INFO] Combination progress file path updated.")
            else:
                print("[INFO] Path cannot be empty. Using current path.")
        elif choice == '3':
            new_path = input("Enter new custom list progress file path: ").strip()
            if new_path:
                settings['progress_file_for_custom_list_path'] = new_path
                save_settings(settings['settings_file_path'], settings) # Save updated settings
                print("[INFO] Custom list progress file path updated.")
                initialize_custom_list_progress_file() # Ensure the new file exists
            else:
                print("[INFO] Path cannot be empty. Using current path.")
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in file paths menu: {choice}.")
        handle_enter_to_continue()

def show_intervals_menu():
    """Displays and allows changing interval settings."""
    while True:
        clear_terminal()
        print(settings['menu_titles']['intervals_menu'])
        print(f"{settings['menu_options']['intervals_menu_1']}: {settings['delay_between_repetitions']} seconds")
        print(f"{settings['menu_options']['intervals_menu_2']}: {settings['delay_between_macro_clicks']} seconds")
        print(f"{settings['menu_options']['intervals_menu_3']}: {settings['pyautogui_write_interval']} seconds per character")
        print(f"{settings['menu_options']['intervals_menu_4']}: {settings['initial_delay_before_automation']} seconds")
        print(settings['menu_options']['intervals_menu_B'])

        choice = input("Enter your choice (1-4 to change, B to go back): ").strip().upper()
        
        if choice in ['1', '2', '3', '4']:
            try:
                new_delay = float(input("Enter new delay (seconds): ").strip())
                if new_delay < 0:
                    print("[ERROR] Delay cannot be negative.")
                    debug_print("Negative delay entered.")
                    handle_enter_to_continue()
                    continue
                if choice == '1':
                    settings['delay_between_repetitions'] = new_delay
                    print(f"[INFO] Delay between repetitions set to {new_delay} seconds.")
                elif choice == '2':
                    settings['delay_between_macro_clicks'] = new_delay
                    print(f"[INFO] Delay between macro clicks set to {new_delay} seconds.")
                elif choice == '3':
                    settings['pyautogui_write_interval'] = new_delay
                    print(f"[INFO] PyAutoGUI write interval set to {new_delay} seconds.")
                elif choice == '4':
                    settings['initial_delay_before_automation'] = new_delay
                    print(f"[INFO] Initial delay before automation set to {new_delay} seconds.")
                save_settings(settings['settings_file_path'], settings)
            except ValueError:
                print("[ERROR] Invalid input. Please enter a number.")
                debug_print("Non-numeric input for delay.")
            handle_enter_to_continue()
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in intervals menu: {choice}.")
            handle_enter_to_continue()

def change_character_set():
    """Allows user to customize the character set for combination generation."""
    clear_terminal()
    print(settings['menu_titles']['character_set_menu'])
    print(f"Current character set: '{settings['chars']}' (Length: {len(settings['chars'])})")
    print("1. Use default (all letters, digits, punctuation)")
    print("2. Use only letters (a-z, A-Z)")
    print("3. Use only digits (0-9)")
    print("4. Use only custom characters")
    print("B. Back to Settings Menu")

    choice = input("Enter your choice: ").strip().upper()

    if choice == '1':
        settings['chars'] = string.ascii_letters + string.digits + string.punctuation
        print("[INFO] Character set set to default (letters, digits, punctuation).")
    elif choice == '2':
        settings['chars'] = string.ascii_letters
        print("[INFO] Character set set to only letters.")
    elif choice == '3':
        settings['chars'] = string.digits
        print("[INFO] Character set set to only digits.")
    elif choice == '4':
        new_chars = input("Enter your custom character set (e.g., abcde123): ").strip()
        if new_chars:
            settings['chars'] = new_chars
            print(f"[INFO] Character set set to: '{new_chars}'.")
        else:
            print("[WARNING] Custom character set cannot be empty. Using current set.")
            debug_print("Empty custom character set entered.")
    elif choice == 'B':
        pass # Go back
    else:
        print("[ERROR] Invalid choice. Please try again.")
        debug_print(f"Invalid choice in character set menu: {choice}.")
    
    save_settings(settings['settings_file_path'], settings)
    handle_enter_to_continue()

def toggle_debug_mode():
    """Toggles the DEBUG_MODE setting."""
    global DEBUG_MODE
    clear_terminal()
    print("--- Toggle Debug Mode ---")
    current_status = settings.get('debug_mode', DEFAULT_SETTINGS['debug_mode'])
    print(f"Current Debug Mode status: {'ENABLED' if current_status else 'DISABLED'}")
    
    confirm = input("Do you want to TOGGLE Debug Mode? (yes/no): ").strip().lower()
    if confirm == 'yes':
        settings['debug_mode'] = not current_status
        DEBUG_MODE = settings['debug_mode'] # Update global flag immediately
        save_settings(settings['settings_file_path'], settings)
        print(f"[INFO] Debug Mode is now {'ENABLED' if DEBUG_MODE else 'DISABLED'}.")
        debug_print(f"Debug Mode toggled to {DEBUG_MODE}.")
    else:
        print("[INFO] Debug Mode toggle cancelled.")
        debug_print("Debug Mode toggle cancelled by user.")
    handle_enter_to_continue()

def show_customization_menu():
    """Displays and handles customization options."""
    while True:
        clear_terminal()
        print(settings['menu_titles']['customization_menu'])
        print(f"{settings['menu_options']['customization_menu_1']} ({'ENABLED' if settings['press_enter_to_exit_enabled'] else 'DISABLED'})")
        print(f"{settings['menu_options']['customization_menu_2']} (Current: '{settings['launch_message']}')")
        print(f"{settings['menu_options']['customization_menu_3']} (Current: '{settings['exit_message']}')")
        print(f"{settings['menu_options']['customization_menu_4']}")
        print(f"{settings['menu_options']['customization_menu_5']} ({'ENABLED' if settings['clear_screen_on_menu_display'] else 'DISABLED'})")
        print(f"{settings['menu_options']['customization_menu_6']} (Current: '{settings['user_name']}')")
        print(f"{settings['menu_options']['customization_menu_7']} ({'ENABLED' if settings['shutdown_on_completion'] else 'DISABLED'})") # NEW: Shutdown option
        print(settings['menu_options']['customization_menu_B'])

        choice = input("Enter your choice: ").strip().upper()

        if choice == '1':
            toggle_setting_boolean('press_enter_to_exit_enabled', "Press Enter to Continue prompts")
        elif choice == '2':
            new_message = input("Enter new launch message: ").strip()
            if new_message:
                settings['launch_message'] = new_message
                print("[INFO] Launch message updated.")
                save_settings(settings['settings_file_path'], settings)
            else:
                print("[WARNING] Message cannot be empty. Using current message.")
            handle_enter_to_continue()
        elif choice == '3':
            new_message = input("Enter new exit message: ").strip()
            if new_message:
                settings['exit_message'] = new_message
                print("[INFO] Exit message updated.")
                save_settings(settings['settings_file_path'], settings)
            else:
                print("[WARNING] Message cannot be empty. Using current message.")
            handle_enter_to_continue()
        elif choice == '4':
            customize_menu_text()
        elif choice == '5':
            toggle_setting_boolean('clear_screen_on_menu_display', "Clear screen on menu display")
        elif choice == '6':
            set_user_name()
        elif choice == '7': # NEW: Handle shutdown toggle
            toggle_setting_boolean('shutdown_on_completion', "Shutdown PC on Completion")
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in customization menu: {choice}.")
            handle_enter_to_continue()

def toggle_setting_boolean(setting_key, display_name):
    """Generic function to toggle a boolean setting."""
    current_status = settings.get(setting_key, DEFAULT_SETTINGS[setting_key])
    settings[setting_key] = not current_status
    save_settings(settings['settings_file_path'], settings)
    print(f"[INFO] {display_name} is now {'ENABLED' if settings[setting_key] else 'DISABLED'}.")
    debug_print(f"Setting '{setting_key}' toggled to {settings[setting_key]}.")
    handle_enter_to_continue()

def set_user_name():
    """Allows the user to set their custom name."""
    clear_terminal()
    print("--- Set User Name ---")
    current_name = settings.get('user_name', DEFAULT_SETTINGS['user_name'])
    print(f"Current user name: '{current_name}'")
    new_name = input("Enter your desired name (leave empty to keep current): ").strip()
    if new_name:
        settings['user_name'] = new_name
        save_settings(settings['settings_file_path'], settings)
        print(f"[INFO] User name updated to '{new_name}'.")
        debug_print(f"User name set to '{new_name}'.")
    else:
        print("[INFO] User name not changed.")
        debug_print("User name not changed (empty input).")
    handle_enter_to_continue()

def customize_menu_text():
    """Allows user to customize menu titles and options."""
    while True:
        clear_terminal()
        print("--- Customize Menu Text ---")
        print("1. Customize Menu Titles")
        print("2. Customize Menu Options")
        print("3. Reset All Menu Text to Default")
        print("B. Back to Customization Options")

        choice = input("Enter your choice: ").strip().upper()

        if choice == '1':
            _customize_nested_dict_setting('menu_titles', "Menu Title")
        elif choice == '2':
            _customize_nested_dict_setting('menu_options', "Menu Option Text")
        elif choice == '3':
            confirm = input("Are you sure you want to reset ALL menu titles and options to default? (yes/no): ").strip().lower()
            if confirm == 'yes':
                reset_settings_section('all_menu_text')
            else:
                print("[INFO] Reset cancelled.")
                debug_print("Menu text reset cancelled.")
                handle_enter_to_continue()
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in customize menu text: {choice}.")
            handle_enter_to_continue()

def _customize_nested_dict_setting(setting_key, display_name):
    """Helper to customize nested dictionary settings like menu_titles or menu_options."""
    while True:
        clear_terminal()
        print(f"--- Customize {display_name}s ---")
        current_dict = settings[setting_key]
        sorted_keys = sorted(current_dict.keys())
        
        for i, key in enumerate(sorted_keys):
            print(f"{i+1}. {key}: '{current_dict[key]}'")
        print("B. Back")

        choice = input("Enter the number of the item to edit, or 'B' to go back: ").strip().upper()

        if choice == 'B':
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(sorted_keys):
                selected_key = sorted_keys[index]
                current_value = current_dict[selected_key]
                print(f"Currently '{selected_key}': '{current_value}'")
                new_value = input(f"Enter new text for '{selected_key}' (leave empty to keep current): ").strip()
                if new_value:
                    settings[setting_key][selected_key] = new_value
                    print(f"[INFO] '{selected_key}' updated.")
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[INFO] Text not changed.")
                    debug_print("Text not changed (empty input).")
            else:
                print("[ERROR] Invalid number. Please try again.")
                debug_print(f"Invalid number for nested dict customization: {choice}.")
        except ValueError:
            print("[ERROR] Invalid input. Please enter a number or 'B'.")
            debug_print(f"Non-numeric input for nested dict customization: {choice}.")
        handle_enter_to_continue()


def show_hotkey_failsafe_menu():
    """Displays and handles hotkey and failsafe settings."""
    while True:
        clear_terminal()
        print(settings['menu_titles']['hotkey_failsafe_menu'])
        print(f"{settings['menu_options']['hotkey_failsafe_menu_1']} (Current: '{settings['stop_hotkey']}')")
        print(f"{settings['menu_options']['hotkey_failsafe_menu_2']} ({'ENABLED' if settings['pyautogui_failsafe_enabled'] else 'DISABLED'})")
        print(f"{settings['menu_options']['hotkey_failsafe_3']} (Current: {', '.join(settings['pyautogui_failsafe_corners'])})")
        print(settings['menu_options']['hotkey_failsafe_menu_B'])

        choice = input("Enter your choice: ").strip().upper()

        if choice == '1':
            new_hotkey = input("Enter new stop hotkey (e.g., ctrl+shift+q, escape): ").strip().lower()
            if new_hotkey:
                settings['stop_hotkey'] = new_hotkey
                save_settings(settings['settings_file_path'], settings)
                register_stop_hotkey() # Re-register the hotkey immediately
                print(f"[INFO] Stop hotkey updated to: '{new_hotkey}'.")
                debug_print(f"Stop hotkey set to '{new_hotkey}'.")
            else:
                print("[WARNING] Hotkey cannot be empty. Using current hotkey.")
                debug_print("Empty hotkey entered.")
            handle_enter_to_continue()
        elif choice == '2':
            toggle_setting_boolean('pyautogui_failsafe_enabled', "PyAutoGUI Fail-Safe")
            pyautogui.FAILSAFE = settings['pyautogui_failsafe_enabled'] # Update live setting
            if settings['pyautogui_failsafe_enabled']:
                print("[INFO] PyAutoGUI Fail-Safe is now ENABLED. Remember to move your mouse to a corner to stop.")
            else:
                print("[INFO] PyAutoGUI Fail-Safe is now DISABLED. Be cautious!")
            handle_enter_to_continue()
        elif choice == '3':
            customize_failsafe_corners()
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in hotkey/failsafe menu: {choice}.")
            handle_enter_to_continue()

def customize_failsafe_corners():
    """Allows customization of PyAutoGUI failsafe corners."""
    available_corners = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
    while True:
        clear_terminal()
        print("--- Customize Fail-Safe Corners ---")
        print("Select corners to enable/disable (enter numbers, separated by space, or 'R' to reset, 'B' to back):")
        
        current_corners = set(settings['pyautogui_failsafe_corners'])
        for i, corner in enumerate(available_corners):
            status = "ENABLED" if corner in current_corners else "DISABLED"
            print(f"{i+1}. {corner.replace('_', ' ').title()} ({status})")
        print("R. Reset to Default Corners (All Enabled)")
        print("B. Back")

        choice_str = input("Enter your choice: ").strip().lower()

        if choice_str == 'b':
            break
        elif choice_str == 'r':
            settings['pyautogui_failsafe_corners'] = DEFAULT_SETTINGS['pyautogui_failsafe_corners'].copy()
            print("[INFO] Fail-safe corners reset to default (all enabled).")
            # Update PyAutoGUI's internal failsafe points immediately
            update_pyautogui_failsafe_points()
            save_settings(settings['settings_file_path'], settings)
            handle_enter_to_continue()
        else:
            try:
                selected_indices = [int(x.strip()) - 1 for x in choice_str.split()]
                new_corners = set(settings['pyautogui_failsafe_corners'])
                
                for index in selected_indices:
                    if 0 <= index < len(available_corners):
                        corner_name = available_corners[index]
                        if corner_name in new_corners:
                            new_corners.remove(corner_name) # Disable
                            print(f"[INFO] {corner_name.replace('_', ' ').title()} DISABLED.")
                        else:
                            new_corners.add(corner_name) # Enable
                            print(f"[INFO] {corner_name.replace('_', ' ').title()} ENABLED.")
                    else:
                        print(f"[ERROR] Invalid number: {index + 1}. Please try again.")
                        debug_print(f"Invalid corner index: {index + 1}.")
                
                settings['pyautogui_failsafe_corners'] = list(new_corners)
                # Update PyAutoGUI's internal failsafe points immediately
                update_pyautogui_failsafe_points()
                save_settings(settings['settings_file_path'], settings)
                handle_enter_to_continue()

            except ValueError:
                print("[ERROR] Invalid input. Please enter numbers separated by spaces, 'R', or 'B'.")
                debug_print(f"Invalid input for failsafe corners: {choice_str}.")
                handle_enter_to_continue()

def update_pyautogui_failsafe_points():
    """Updates PyAutoGUI's internal failsafe points based on settings."""
    corner_map = {
        'top_left': (0, 0),
        'top_right': (pyautogui.size().width - 1, 0),
        'bottom_left': (0, pyautogui.size().height - 1),
        'bottom_right': (pyautogui.size().width - 1, pyautogui.size().height - 1)
    }
    # Clear failsafe points and add only the configured ones
    pyautogui.DEFAULTS['failSafePoints'] = []
    for corner_name in settings['pyautogui_failsafe_corners']:
        if corner_name in corner_map:
            pyautogui.DEFAULTS['failSafePoints'].append(corner_map[corner_name])
            debug_print(f"Added failsafe corner: {corner_name} {corner_map[corner_name]}")
        else:
            debug_print(f"[WARNING] Unknown failsafe corner in settings: {corner_name}")


def show_typing_options_menu():
    """Displays and handles typing method and global pause settings."""
    typing_methods = {
        'pyautogui_write': "PyAutoGUI .write() (general purpose, respects interval)",
        'pyautogui_typewrite': "PyAutoGUI .typewrite() (slower, better for special chars, respects interval)",
        'pyperclip_safe': "Pyperclip Safe (fastest, uses clipboard, restores original clipboard content)",
        'pyperclip_all': "Pyperclip All (fastest, uses clipboard, leaves typed text on clipboard)"
    }
    while True:
        clear_terminal()
        print(settings['menu_titles']['typing_options_menu'])
        print(f"{settings['menu_options']['typing_options_menu_1']} (Current: {typing_methods.get(settings['typing_method'], 'Unknown')})")
        print(f"{settings['menu_options']['typing_options_menu_2']} (Current: {settings['pyautogui_global_pause']} seconds)")
        print(settings['menu_options']['typing_options_menu_B'])

        choice = input("Enter your choice: ").strip().upper()

        if choice == '1':
            print("\n--- Change Typing Method ---")
            print("Select a typing method:")
            sorted_methods = sorted(typing_methods.items())
            for i, (key, desc) in enumerate(sorted_methods):
                print(f"{i+1}. {desc}")
            print("B. Back")
            method_choice = input("Enter your choice: ").strip().upper()

            if method_choice == 'B':
                continue
            try:
                index = int(method_choice) - 1
                if 0 <= index < len(sorted_methods):
                    selected_key = sorted_methods[index][0]
                    settings['typing_method'] = selected_key
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[INFO] Typing method set to: {typing_methods[selected_key]}.")
                    debug_print(f"Typing method set to '{selected_key}'.")
                else:
                    print("[ERROR] Invalid number. Please try again.")
                    debug_print(f"Invalid number for typing method: {method_choice}.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter a number or 'B'.")
                debug_print(f"Non-numeric input for typing method: {method_choice}.")
            handle_enter_to_continue()
        elif choice == '2':
            try:
                new_pause = float(input("Enter new global pause (seconds, applies to ALL PyAutoGUI actions): ").strip())
                if new_pause < 0:
                    print("[ERROR] Pause cannot be negative.")
                    debug_print("Negative global pause entered.")
                    handle_enter_to_continue()
                    continue
                settings['pyautogui_global_pause'] = new_pause
                save_settings(settings['settings_file_path'], settings)
                pyautogui.PAUSE = new_pause # Apply live
                print(f"[INFO] Global PyAutoGUI pause set to {new_pause} seconds.")
                debug_print(f"Global PyAutoGUI pause set to {new_pause}.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter a number.")
                debug_print("Non-numeric input for global pause.")
            handle_enter_to_continue()
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in typing options menu: {choice}.")
            handle_enter_to_continue()

def show_combo_gen_settings_menu():
    """Displays and handles combination generator settings."""
    while True:
        clear_terminal()
        print(settings['menu_titles']['combo_gen_settings_menu'])
        print(f"{settings['menu_options']['combo_gen_settings_menu_1']} (Current: {settings['min_combination_length']})")
        max_len_display = f"{settings['max_combination_length']} (0 for infinite)" if settings['max_combination_length'] >= 0 else "N/A (Infinite)"
        print(f"{settings['menu_options']['combo_gen_settings_menu_2']} (Current: {max_len_display})")
        print(settings['menu_options']['combo_gen_settings_menu_3'])
        print(settings['menu_options']['combo_gen_settings_menu_B'])

        choice = input("Enter your choice: ").strip().upper()

        if choice == '1':
            try:
                new_min_len = int(input("Enter new minimum combination length (integer >= 1): ").strip())
                if new_min_len < 1:
                    print("[ERROR] Minimum length must be at least 1.")
                    debug_print("Invalid min combination length (<1).")
                    handle_enter_to_continue()
                    continue
                settings['min_combination_length'] = new_min_len
                save_settings(settings['settings_file_path'], settings)
                print(f"[INFO] Minimum combination length set to {new_min_len}.")
                debug_print(f"Min combination length set to {new_min_len}.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter an integer.")
                debug_print("Non-integer input for min combo length.")
            handle_enter_to_continue()
        elif choice == '2':
            try:
                new_max_len = int(input("Enter new maximum combination length (integer, enter 0 for infinite): ").strip())
                if new_max_len < 0:
                    print("[ERROR] Maximum length cannot be negative. Enter 0 for infinite.")
                    debug_print("Negative max combination length.")
                    handle_enter_to_continue()
                    continue
                if new_max_len > 0 and new_max_len < settings['min_combination_length']:
                    print("[ERROR] Maximum length cannot be less than minimum length.")
                    debug_print("Max length less than min length.")
                    handle_enter_to_continue()
                    continue
                settings['max_combination_length'] = new_max_len
                save_settings(settings['settings_file_path'], settings)
                print(f"[INFO] Maximum combination length set to {new_max_len} ({'Infinite' if new_max_len == 0 else ''}).")
                debug_print(f"Max combination length set to {new_max_len}.")
            except ValueError:
                print("[ERROR] Invalid input. Please enter an integer.")
                debug_print("Non-integer input for max combo length.")
            handle_enter_to_continue()
        elif choice == '3':
            change_character_set() # Reuse existing function
        elif choice == 'B':
            break
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in combo gen settings menu: {choice}.")
            handle_enter_to_continue()

def register_stop_hotkey():
    """Registers the global hotkey to stop the script."""
    global STOP_SCRIPT
    # Unhook any existing hotkeys first to avoid conflicts
    try:
        keyboard.unhook_all()
        debug_print("Unhooked all previous hotkeys.")
    except Exception as e:
        debug_print(f"Error unhooking hotkeys (might be none registered): {e}")

    hotkey = settings.get('stop_hotkey', DEFAULT_SETTINGS['stop_hotkey'])
    try:
        # Use a lambda to ensure STOP_SCRIPT is accessed correctly within the handler
        keyboard.add_hotkey(hotkey, lambda: globals().update(STOP_SCRIPT=True))
        debug_print(f"Registered stop hotkey: '{hotkey}'.")
    except Exception as e:
        print(f"[ERROR] Could not register stop hotkey '{hotkey}': {e}. Please choose a different hotkey in settings or ensure it's not in use.")
        debug_print(f"Failed to register hotkey '{hotkey}': {e}.")


# --- Main Application Loop ---
def main_menu():
    """Displays the main menu and handles overall script flow."""
    # Run initial setup if it's the first launch
    if not settings.get('first_launch_done', False):
        initial_setup()

    # Re-register hotkey in case the settings file was just loaded or changed
    register_stop_hotkey() 
    
    while True:
        clear_terminal()
        print(settings['launch_message']) # Use customizable launch message
        print(settings['menu_titles']['main_menu'])
        # Dynamically display menu options
        menu_options = {k: v for k, v in settings['menu_options'].items() if k.startswith('main_menu_')}
        sorted_keys = sorted(menu_options.keys(), key=lambda x: (x.replace('main_menu_', '').isdigit(), x))
        for key in sorted_keys:
            print(menu_options[key])
        
        choice = input("Enter your choice: ").strip().upper()

        if choice == '0':
            show_how_to_use()
        elif choice == '1':
            # Ask for repetitions for combination generator with clicks
            repetitions = get_repetitions_input()
            if repetitions is not None: # If user didn't cancel
                run_automation_loop(include_macro_clicks=True, repetitions=repetitions)
        elif choice == '2':
            # Ask for repetitions for combination generator without clicks
            repetitions = get_repetitions_input()
            if repetitions is not None: # If user didn't cancel
                run_automation_loop(include_macro_clicks=False, repetitions=repetitions)
        elif choice == '3':
            show_settings_menu()
        elif choice == '4':
            reset_progress(settings['progress_file_path'])
        elif choice == '5':
            custom_list_path = input("Enter the full path to your text file (e.g., C:\\Users\\User\\list.txt): ").strip()
            if os.path.exists(custom_list_path) and os.path.isfile(custom_list_path):
                # Ask for repetitions for custom list processor (0 for infinite if it were relevant, but typically 1 for full list)
                # For custom list, repetitions mean how many times to process the *entire* list.
                repetitions = get_repetitions_input(prompt="How many times do you want to process the entire custom list? (Enter 0 for infinite, but usually 1 for this mode): ")
                if repetitions is not None:
                    run_automation_loop(include_macro_clicks=False, process_custom_list=True, custom_list_path=custom_list_path, repetitions=repetitions)
            else:
                print(f"[ERROR] File not found at '{custom_list_path}'. Please check the path and try again.")
                debug_print(f"Custom list file not found: {custom_list_path}.")
                handle_enter_to_continue()
        elif choice == '6':
            reset_custom_list_progress()
        elif choice == '7':
            # Determine repetitions for 'Only Macro Clicks' mode
            repetitions = get_repetitions_input(prompt="How many times do you want to repeat the macro clicks? (Enter 0 for infinite): ")
            if repetitions is not None:
                # Need to ensure macro clicks are defined first
                if not settings['macro_click_data']:
                    print("[INFO] No macro clicks defined. Entering setup mode to define them first.")
                    debug_print("No macro clicks defined, initiating setup.")
                    if get_clicks_for_setup(): # If setup is successful (even if no clicks were defined)
                        # Now, re-run 'only macro clicks' with repetitions
                        print("\n[INFO] Macro click setup complete. Starting macro click automation.")
                        run_automation_loop(include_macro_clicks=True, repetitions=repetitions)
                    else:
                        print("[INFO] Macro click setup cancelled. Returning to main menu.")
                        debug_print("Macro click setup cancelled.")
                        handle_enter_to_continue()
                else:
                    run_automation_loop(include_macro_clicks=True, repetitions=repetitions)
        elif choice == '8':
            show_credits_page()
        elif choice == '9':
            print(settings['exit_message']) # Use customizable exit message
            debug_print("Exiting script.")
            sys.exit() # Exit the application
        else:
            print("[ERROR] Invalid choice. Please try again.")
            debug_print(f"Invalid choice in main menu: {choice}.")
            handle_enter_to_continue()

def get_repetitions_input(prompt="Enter number of repetitions (0 for infinite): "):
    """Helper function to get repetitions input from user."""
    while True:
        try:
            reps_str = input(prompt).strip()
            if reps_str.lower() == 'c': # Allow 'c' to cancel
                print("[INFO] Operation cancelled.")
                return None
            repetitions = int(reps_str)
            if repetitions < 0:
                print("[ERROR] Repetitions cannot be negative. Enter 0 for infinite, or a positive number.")
                debug_print("Negative repetitions entered.")
                continue
            return repetitions
        except ValueError:
            print("[ERROR] Invalid input. Please enter a number or 'c' to cancel.")
            debug_print("Non-numeric input for repetitions.")

def show_credits_page():
    """Displays the credits page."""
    clear_terminal()
    print(settings['menu_titles']['credits_page'])
    print("\n--- Development Team ---")
    print("Main Coder: Google Gemini (that's me!)")
    print("Project Idea & Guidance: MrCookie")
    print("\n--- Libraries Used ---")
    print(" - pyautogui: For controlling mouse and keyboard.")
    print(" - pynput: For global hotkey listening (used for STOP_SCRIPT).")
    print(" - pyperclip: For clipboard operations (used in typing methods).")
    print(" - itertools: For efficient combination generation.")
    print("\n--- Special Thanks ---")
    print("To the open-source community for providing these amazing tools and resources.")
    print("\nThis script is licensed under the MIT License.")
    print("Feel free to inspect, modify, and distribute (but please credit the original authors!).")
    handle_enter_to_continue()

def initial_setup():
    """Guides the user through a first-time setup."""
    clear_terminal()
    print("--- Welcome to MrCookie's Macro and Automation Tool! ---")
    print("It looks like this is your first time running the script or your settings have been reset.")
    print("Let's do a quick initial setup.")
    handle_enter_to_continue()

    # Set user name
    set_user_name()

    # Toggle clear screen
    toggle_setting_boolean('clear_screen_on_menu_display', "Clear screen on menu display (clears terminal before menus)")

    # Toggle press enter to continue
    toggle_setting_boolean('press_enter_to_exit_enabled', "Press Enter to Continue prompts")

    # Set initial delay
    while True:
        try:
            initial_delay = float(input(f"Enter initial delay before automation (seconds, default: {DEFAULT_SETTINGS['initial_delay_before_automation']}): ").strip() or DEFAULT_SETTINGS['initial_delay_before_automation'])
            if initial_delay >= 0:
                settings['initial_delay_before_automation'] = initial_delay
                print(f"[INFO] Initial delay set to {initial_delay} seconds.")
                debug_print(f"Initial delay set to {initial_delay}.")
                break
            else:
                print("[WARNING] Invalid input for initial delay. Must be non-negative.")
                debug_print("Negative initial delay during setup.")
        except ValueError:
            print("[WARNING] Invalid input for initial delay. Please enter a number. Using default.")
            debug_print("Non-numeric initial delay during setup.")
    
    # Get stop hotkey
    stop_key = input(f"\nSet your stop hotkey (e.g., ctrl+shift+q, escape, default: {DEFAULT_SETTINGS['stop_hotkey']}): ").strip()
    if stop_key:
        settings['stop_hotkey'] = stop_key
        print(f"[INFO] Stop hotkey set to: {settings['stop_hotkey']}.")
        debug_print(f"Stop hotkey set to '{settings['stop_hotkey']}'.")
    else:
        print(f"[INFO] No hotkey entered. Using default: {DEFAULT_SETTINGS['stop_hotkey']}.")
        debug_print("No hotkey entered, using default.")

    settings['first_launch_done'] = True
    save_settings(DEFAULT_SETTINGS_FILE, settings)
    print("\n[INFO] Initial setup complete!")
    handle_enter_to_continue()
    
    # Display personalized launch message for subsequent launches
    username_display = settings.get('user_name', 'goofball')
    print("\n[INFO] This tool is fully open source and free, IF YOU PAID FOR THIS DEMAND YOUR MONEY BACK IMMEDIATELY!")
    print(f"Hello {username_display}, welcome to MrCookie's macro and automation tool (with main coding done by gemini), press enter to continue")
    handle_enter_to_continue()

    # Register the stop hotkey once at the end of setup
    register_stop_hotkey()

# --- Entry Point ---
if __name__ == "__main__":
    # Load settings at the very beginning
    settings = load_settings(DEFAULT_SETTINGS_FILE)
    # Ensure progress files are initialized on startup if they don't exist
    initialize_custom_list_progress_file()
    # Call the main menu function to start the application
    main_menu() # Start the main application loop