import pyautogui
import string
import time
import os
import sys
import json
from pynput import mouse
import keyboard
import itertools

# --- Global Flags and Data ---
STOP_SCRIPT = False # Flag to signal the main loop to stop
click_coords = [] # Stores (x, y) tuples for the macro clicks, dynamically sized
current_coord_capture_index = 0 # Helper for the setup phase
mouse_listener_active = False # Flag to control pynput listener

# These are global for setup, but their effective values depends on user input in get_clicks_for_setup
num_macro_clicks = 0
num_ignored_clicks_setup = 0

# --- Settings and Configuration ---
# Define the default settings file path within the user's home directory
USER_HOME_DIR = os.path.expanduser('~')
DEFAULT_SETTINGS_FILE = os.path.join(USER_HOME_DIR, 'script_settings.json')

# Default settings values
DEFAULT_SETTINGS = {
    'chars': string.ascii_letters + string.digits + string.punctuation,
    'delay_between_repetitions': 0.1, # Seconds to wait after a string has been processed
    'delay_between_macro_clicks': 0.01, # New: Seconds to wait between individual macro clicks
    'pyautogui_write_interval': 0.0, # New: Seconds to wait between each character typed by pyautogui.write
    'initial_delay_before_automation': 10.0, # NEW: Seconds to wait before the automation loop starts
    'progress_file_path': os.path.join(USER_HOME_DIR, 'progress.txt'), # DEFAULT path for the progress file in user's home directory
    'settings_file_path': DEFAULT_SETTINGS_FILE # Path where settings are saved (this will be updated if user changes it)
}

# Global dictionary to hold current settings
settings = {}

# --- Hotkey Callback ---
def on_stop_hotkey_pressed():
    """Callback function executed when the Ctrl+Shift+C+V hotkey is pressed."""
    global STOP_SCRIPT
    STOP_SCRIPT = True
    print("\n[INFO] Stop hotkey (Ctrl+Shift+C+V) detected. Script will terminate gracefully after current action.")
    print("[DEBUG] STOP_SCRIPT flag set to True by hotkey 'Ctrl+Shift+C+V'.")

# --- Settings File Functions ---
def load_settings(file_path):
    """
    Loads settings from the specified JSON file.
    Merges with DEFAULT_SETTINGS to ensure all keys are present.
    """
    global settings
    print(f"[DEBUG] Attempting to load settings from: '{file_path}'")
    loaded_settings = {}
    if os.path.exists(file_path):
        print(f"[DEBUG] Settings file '{file_path}' exists. Checking size.")
        if os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r') as f:
                    loaded_settings = json.load(f)
                print(f"[INFO] Settings loaded from '{file_path}'.")
                print(f"[DEBUG] Raw loaded settings: {loaded_settings}")
            except json.JSONDecodeError as e:
                print(f"[WARNING] Settings file '{file_path}' is corrupted or invalid JSON ({e}). Using default settings.")
                print(f"[DEBUG] JSONDecodeError: {e}")
            except Exception as e:
                print(f"[WARNING] Could not read settings file '{file_path}': {e}. Using default settings.")
                print(f"[DEBUG] General exception during load: {e}")
        else:
            print(f"[INFO] Settings file '{file_path}' is empty. Using default settings.")
            print(f"[DEBUG] File '{file_path}' is empty.")
    else:
        print(f"[INFO] Settings file '{file_path}' not found. Using default settings.")
        print(f"[DEBUG] File '{file_path}' does not exist.")

    # Merge loaded settings with defaults to ensure all keys are present
    current_settings = DEFAULT_SETTINGS.copy()
    print(f"[DEBUG] DEFAULT_SETTINGS copied: {current_settings}")
    current_settings.update(loaded_settings)
    print(f"[DEBUG] Settings after update with loaded_settings: {current_settings}")
    
    # Ensure chars is string, as JSON might mess with it if not handled properly
    if not isinstance(current_settings.get('chars'), str):
        print("[WARNING] 'chars' setting invalid. Resetting to default character set.")
        current_settings['chars'] = DEFAULT_SETTINGS['chars']
        print(f"[DEBUG] 'chars' reset to default: '{current_settings['chars']}'")

    settings = current_settings
    print(f"[DEBUG] Final settings dictionary after load and merge: {settings}")
    return settings

def save_settings(file_path, settings_data):
    """Saves the current settings to the specified JSON file."""
    print(f"[DEBUG] Attempting to save settings to: '{file_path}'. Data: {settings_data}")
    try:
        # Ensure the directory for the settings file exists
        settings_dir = os.path.dirname(file_path)
        if settings_dir and not os.path.exists(settings_dir):
            os.makedirs(settings_dir, exist_ok=True) # Create directory if it doesn't exist
            print(f"[INFO] Created directory for settings: '{settings_dir}'")
            print(f"[DEBUG] Directory '{settings_dir}' created.")

        with open(file_path, 'w') as f:
            json.dump(settings_data, f, indent=4)
        print(f"[INFO] Settings saved to '{file_path}'.")
        print(f"[DEBUG] Settings successfully written to '{file_path}'.")
    except Exception as e:
        print(f"[ERROR] Could not save settings to '{file_path}': {e}")
        print(f"[DEBUG] Exception during save_settings: {e}")


# --- Progress File Functions ---
def load_progress(file_path):
    """
    Loads the last saved combination from the progress file.
    Returns None if file doesn't exist, is empty, or has invalid content.
    """
    print(f"[DEBUG] Attempting to load progress from: '{file_path}'")
    if not os.path.exists(file_path):
        print(f"[INFO] Progress file '{file_path}' not found. Starting from 'a'.")
        print(f"[DEBUG] File '{file_path}' does not exist. Returning None.")
        return None # No previous progress
    
    if os.path.getsize(file_path) == 0:
        print(f"[INFO] Progress file '{file_path}' is empty. Starting from 'a'.")
        print(f"[DEBUG] File '{file_path}' is empty. Returning None.")
        return None

    try:
        with open(file_path, 'r') as f:
            last_progress = f.readline().strip()
            print(f"[DEBUG] Read '{last_progress}' from progress file.")
            if not last_progress:
                print(f"[INFO] Progress file '{file_path}' is empty after read. Starting from 'a'.")
                print(f"[DEBUG] Progress file content is empty string. Returning None.")
                return None
            
            # Basic validation: ensure all chars in last_progress are in CHARS set
            configured_chars = settings.get('chars', DEFAULT_SETTINGS['chars'])
            print(f"[DEBUG] Configured chars for validation: '{configured_chars}'")
            if not all(char in configured_chars for char in last_progress):
                print(f"[ERROR] Invalid characters found in progress file: '{last_progress}'. Starting from 'a'.")
                print(f"[DEBUG] Validation failed for '{last_progress}' against '{configured_chars}'. Returning None.")
                return None

            print(f"[INFO] Resuming from last saved progress: '{last_progress}'")
            print(f"[DEBUG] Successfully loaded progress: '{last_progress}'.")
            return last_progress
    except Exception as e:
        print(f"[ERROR] Could not read progress file '{file_path}': {e}. Starting from 'a'.")
        print(f"[DEBUG] Exception during load_progress: {e}. Returning None.")
        return None

def save_progress(file_path, current_string):
    """Saves the current combination to the progress file, overwriting previous content."""
    print(f"[DEBUG] Attempting to save progress: '{current_string}' to '{file_path}'")
    try:
        # Ensure the directory for the progress file exists
        progress_dir = os.path.dirname(file_path)
        if progress_dir and not os.path.exists(progress_dir):
            os.makedirs(progress_dir, exist_ok=True)
            print(f"[INFO] Created directory for progress file: '{progress_dir}'")
            print(f"[DEBUG] Directory '{progress_dir}' created for progress.")

        with open(file_path, 'w') as f: # Overwrite mode 'w'
            f.write(current_string + '\n')
        print(f"[DEBUG] Progress successfully written to '{file_path}'.")
    except Exception as e:
        print(f"[ERROR] Could not save progress to '{file_path}': {e}")
        print(f"[DEBUG] Exception during save_progress: {e}")

def reset_progress(file_path):
    """Resets the progress by deleting the progress file and immediately creating an empty one."""
    print(f"[DEBUG] Attempting to reset progress file: '{file_path}'")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] Progress file '{file_path}' deleted.")
            print(f"[DEBUG] File '{file_path}' removed.")
        except OSError as e:
            print(f"[ERROR] Could not delete progress file '{file_path}': {e}. Please delete it manually if needed.")
            print(f"[DEBUG] OSError during reset_progress (deletion): {e}.")
    else:
        print(f"[INFO] Progress file '{file_path}' does not exist. No deletion needed.")
        print(f"[DEBUG] File '{file_path}' did not exist, no action needed for deletion.")
    
    # Always create a new empty file after deletion or if it didn't exist
    try:
        # Ensure the directory exists before creating the file
        progress_dir = os.path.dirname(file_path)
        if progress_dir and not os.path.exists(progress_dir):
            os.makedirs(progress_dir, exist_ok=True)
            print(f"[INFO] Created directory for new progress file: '{progress_dir}'")
            print(f"[DEBUG] Directory '{progress_dir}' created for new progress file.")
        with open(file_path, 'w') as f:
            f.write('') # Create an empty file
        print(f"[INFO] New empty progress file created at '{file_path}'. Progress reset.")
        print(f"[DEBUG] Empty file '{file_path}' created after reset.")
    except Exception as e:
        print(f"[ERROR] Could not create new empty progress file at '{file_path}': {e}")
        print(f"[DEBUG] Exception during reset_progress (creation): {e}.")

    input("Press Enter to continue...") # Pause for user to read

# --- Mouse Listener Callback for Setup ---
def on_click_for_setup(x, y, button, pressed):
    """
    Callback function for pynput mouse listener during the setup phase.
    Captures the specified number of coordinates after ignoring initial clicks.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords, num_macro_clicks, num_ignored_clicks_setup

    if pressed: # Only act on mouse down event
        print(f"[DEBUG] Mouse click detected at ({x}, {y}) - Button: {button}, Pressed: {pressed}.")
        current_coord_capture_index += 1 # Total clicks seen so far
        print(f"[DEBUG] current_coord_capture_index incremented to {current_coord_capture_index}.")

        # If we are still in the 'ignored clicks' phase
        if current_coord_capture_index <= num_ignored_clicks_setup:
            print(f"  Click {current_coord_capture_index} received. This click is ignored ({num_ignored_clicks_setup - current_coord_capture_index + 1} more ignored clicks).")
        else:
            # Calculate the 0-indexed position in the click_coords list
            macro_click_list_index = current_coord_capture_index - num_ignored_clicks_setup - 1
            print(f"[DEBUG] Calculating macro_click_list_index: {current_coord_capture_index} - {num_ignored_clicks_setup} - 1 = {macro_click_list_index}")

            if macro_click_list_index >= 0 and macro_click_list_index < num_macro_clicks:
                click_coords[macro_click_list_index] = (x, y)
                print(f"  Coordinate {macro_click_list_index + 1} (X: {x}, Y: {y}) saved. click_coords now: {click_coords}")
            else:
                print(f"[DEBUG] Click out of bounds for macro clicks. Index: {macro_click_list_index}, num_macro_clicks: {num_macro_clicks}")

            # Check if all required macro clicks have been captured
            if (macro_click_list_index + 1) == num_macro_clicks:
                print("  All required coordinates captured. Exiting setup mode.")
                mouse_listener_active = False # Signal to stop the listener
                print("[DEBUG] mouse_listener_active set to False. Returning False to stop pynput listener.")
                return False # This explicit return False stops the pynput listener

# --- Setup Phase Function ---
def get_clicks_for_setup():
    """
    Guides the user to define the number of macro clicks, ignored clicks,
    and then capture the coordinates.
    Returns True if setup is successful, False if cancelled or failed.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords, num_macro_clicks, num_ignored_clicks_setup
    print("[DEBUG] Entering get_clicks_for_setup().")

    print("\n--- Setup Phase: Define Macro Clicks ---")
    while True:
        try:
            num_str = input("How many macro clicks do you want to perform? (Enter 0 to go back to Main Menu): ").strip()
            print(f"[DEBUG] User input for macro clicks: '{num_str}'")
            if num_str == '0':
                print("[INFO] Returning to Main Menu.")
                print("[DEBUG] User cancelled macro setup. Returning False.")
                return False # Indicate user cancelled
            
            num = int(num_str)
            if num < 0:
                print("[ERROR] Number of clicks must be a non-negative integer.")
                print(f"[DEBUG] Invalid input for macro clicks: {num}. Must be non-negative.")
                continue
            num_macro_clicks = num
            print(f"[DEBUG] num_macro_clicks set to: {num_macro_clicks}.")
            break
        except ValueError:
            print("[ERROR] Please enter a valid number or 0.")
            print("[DEBUG] ValueError for macro clicks input.")

    if num_macro_clicks == 0: # If user entered 0 clicks, it's also a form of "skip"
        print("[INFO] 0 macro clicks selected. Skipping coordinate capture.")
        print("[DEBUG] num_macro_clicks is 0. Setup considered successful with no clicks.")
        return True # Treat as successful setup, just no clicks to perform

    while True:
        try:
            num = int(input("How many initial clicks should be ignored during coordinate capture? (e.g., 1 for a warm-up click): ").strip())
            print(f"[DEBUG] User input for ignored clicks: '{num}'")
            if num < 0:
                print("[ERROR] Number of ignored clicks cannot be negative.")
                print(f"[DEBUG] Invalid input for ignored clicks: {num}. Cannot be negative.")
                continue
            num_ignored_clicks_setup = num
            print(f"[DEBUG] num_ignored_clicks_setup set to: {num_ignored_clicks_setup}.")
            break
        except ValueError:
            print("[ERROR] Please enter a valid number.")
            print("[DEBUG] ValueError for ignored clicks input.")

    # Dynamically size the click_coords list based on user input
    click_coords.clear() # Clear any previous clicks
    click_coords.extend([None] * num_macro_clicks)
    current_coord_capture_index = 0 # Reset total clicks seen for new setup
    print(f"[DEBUG] click_coords re-initialized to size {num_macro_clicks}: {click_coords}")
    print(f"[DEBUG] current_coord_capture_index reset to {current_coord_capture_index}.")

    print("\n--- Start Capturing Coordinates ---")
    if num_ignored_clicks_setup > 0:
        print(f"Make your first {num_ignored_clicks_setup} clicks anywhere on screen. These will be ignored.")
    print(f"Then, click on the exact {num_macro_clicks} positions where you want the script to click.")
    print(f"Total clicks expected: {num_ignored_clicks_setup + num_macro_clicks}")
    
    # Give a brief moment for the user to read the prompts before listening
    time.sleep(0.5) 
    print("[DEBUG] Paused for 0.5 seconds before starting mouse listener for setup.")

    mouse_listener_active = True
    print("[DEBUG] Starting pynput mouse listener for coordinate capture.")
    with mouse.Listener(on_click=on_click_for_setup) as listener:
        listener.join() # Blocks until on_click_for_setup returns False and stops the listener
    print("[DEBUG] pynput mouse listener for setup has stopped.")

    # Final check if all clicks were indeed captured
    if None in click_coords:
        print("[WARNING] Not all desired macro coordinates were captured during setup. Macro clicks may be incomplete.")
        print(f"[DEBUG] Incomplete click_coords: {click_coords}. Returning True (with warning).")
        return True # Still return True, so the script runs but with incomplete clicks
    else:
        print("\nSetup complete. All required coordinates captured!")
        print(f"[DEBUG] All macro clicks captured: {click_coords}. Returning True.")
        return True

# --- Combination Generator ---
def generate_all_combinations(start_combination=None):
    """
    Generates all string combinations lexicographically, starting from length 1.
    If start_combination is provided, it resumes from that point.
    This generator runs indefinitely.
    """
    print(f"[DEBUG] Entering generate_all_combinations() with start_combination='{start_combination}'.")
    chars_set = settings.get('chars', DEFAULT_SETTINGS['chars']) # Use configured chars
    print(f"[DEBUG] Character set for generator: '{chars_set}'.")
    
    # Flag to indicate if we have reached or passed the start_combination
    started_yielding = False

    if start_combination:
        start_length = len(start_combination)
        print(f"[INFO] Attempting to resume from length {start_length} to find '{start_combination}'...")
        print(f"[DEBUG] Initializing search for resume point starting from length 1.")
        
        # Iterate up to the starting length to find the start_combination
        for length_iter in itertools.count(1):
            if STOP_SCRIPT: 
                print("[DEBUG] STOP_SCRIPT is True during resume point search. Generator returning.")
                return
            
            if length_iter < start_length: # Skip lengths shorter than the start_combination's length
                print(f"[DEBUG] Skipping combinations for length {length_iter} (less than start_combination length {start_length}).")
                continue # Move to the next length

            print(f"[DEBUG] Searching for '{start_combination}' within combinations of length {length_iter}.")
            for combo_tuple in itertools.product(chars_set, repeat=length_iter):
                if STOP_SCRIPT: 
                    print("[DEBUG] STOP_SCRIPT is True during resume point search (inner loop). Generator returning.")
                    return
                current_combo_str = ''.join(combo_tuple)

                # If we are at the start_combination, start yielding from here
                if current_combo_str == start_combination:
                    print(f"[INFO] Found resume point: '{start_combination}'. Resuming generation from next combination.")
                    started_yielding = True
                    print(f"[DEBUG] start_combination '{start_combination}' found. started_yielding set to True. Breaking inner loop.")
                    break # Break inner loop (combinations for this length)

            if started_yielding:
                print(f"[DEBUG] started_yielding is True. Breaking outer loop (lengths).")
                break # Break outer loop (lengths)
            
            if length_iter >= start_length and not started_yielding:
                print(f"[WARNING] Resume point '{start_combination}' was not found in generated sequence (it might be invalid or deleted from character set). Starting from 'a'.")
                start_combination = None # Reset to start from the beginning
                started_yielding = True # Force yielding from now on, starting with 'a'
                print("[DEBUG] Resume point not found, forcing start from 'a'.")
                break # Break here to start main generation loop from length 1

        if not started_yielding: # This case is if start_combination was provided but somehow not found (e.g., too long)
             print(f"[WARNING] Resume point '{start_combination}' was not found (too long or invalid). Starting from 'a'.")
             start_combination = None
             started_yielding = True # Force yielding from now on, starting with 'a'
             print("[DEBUG] Final check: Resume point not found, forcing start from 'a'.")


    # Main generation loop (either from beginning or after resuming)
    actual_start_length_for_gen = 1
    if start_combination and started_yielding and len(start_combination) > 0:
        actual_start_length_for_gen = len(start_combination)
        print(f"[DEBUG] Setting actual_start_length_for_gen to {actual_start_length_for_gen} (from start_combination).")
    else:
        print(f"[DEBUG] Starting generation from length 1 (no resume point or reset).")


    for length in itertools.count(actual_start_length_for_gen):
        if STOP_SCRIPT: 
            print("[DEBUG] STOP_SCRIPT is True in main generator loop. Generator returning.")
            return
        print(f"\n[INFO] Generating combinations for length: {length} (Total possible: {len(chars_set)**length})")
        print(f"[DEBUG] Entering itertools.product for length {length}.")
        
        skip_to_start_combo = False
        # If we just finished searching for a resume point and it was *not* found, and length matches, we are now at the start of the next combo
        if start_combination and length == len(start_combination) and not started_yielding:
            skip_to_start_combo = True
            print(f"[DEBUG] Setting skip_to_start_combo to True for length {length} (to bypass already processed start_combination).")
            
        for combo_tuple in itertools.product(chars_set, repeat=length):
            if STOP_SCRIPT: 
                print("[DEBUG] STOP_SCRIPT is True in main generator loop (inner loop). Generator returning.")
                return
            current_combo_str = ''.join(combo_tuple)
            
            if skip_to_start_combo:
                if current_combo_str == start_combination:
                    skip_to_start_combo = False # Found it, stop skipping
                    started_yielding = True # Ensure this flag is set for subsequent iterations
                    print(f"[DEBUG] Found start_combination '{start_combination}' for skipping. Now yielding from next. started_yielding=True.")
                continue # Keep skipping until we find the start_combination
            
            if started_yielding or start_combination is None: # Only yield if we've passed the resume point or no resume point was set
                print(f"[DEBUG] Yielding combination: '{current_combo_str}'.")
                yield current_combo_str
    print("[DEBUG] Generator has exhausted its possibilities (THIS SHOULD NEVER PRINT).")

# --- Core Action Functions ---
def type_the_string(current_string):
    """Types the given string into the active text field and presses Enter."""
    write_interval = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
    print(f"[DEBUG] Entering type_the_string() for '{current_string}' with interval {write_interval}s.")
    print(f"[ACTION] Typing: '{current_string}' (Length: {len(current_string)})")
    pyautogui.write(current_string, interval=write_interval)
    print(f"[DEBUG] pyautogui.write('{current_string}', interval={write_interval}) executed.")
    pyautogui.press('enter')
    print("[ACTION] Enter pressed.")
    print(f"[DEBUG] Exiting type_the_string().")

def perform_macro_clicks():
    """Performs the specific click combination using the globally captured coordinates."""
    macro_delay = settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])
    print(f"[DEBUG] Entering perform_macro_clicks() with delay {macro_delay}s.")
    print("[ACTION] Performing macro clicks...")
    
    if not click_coords or all(c is None for c in click_coords):
        print("[WARNING] No macro click coordinates defined or captured. Skipping clicks.")
        print(f"[DEBUG] click_coords is empty or all None: {click_coords}. Skipping perform_macro_clicks().")
        return

    # Iterate through the captured click coordinates and perform clicks
    for i, coords in enumerate(click_coords):
        if coords: # Ensure coordinates were actually captured for this slot
            print(f"  Clicking at Coordinate {i+1}: {coords}")
            pyautogui.click(x=coords[0], y=coords[1])
            print(f"[DEBUG] pyautogui.click(x={coords[0]}, y={coords[1]}) executed for click {i+1}.")
            time.sleep(macro_delay) # Use the configured delay
            print(f"[DEBUG] Paused for {macro_delay}s after click {i+1}.")
        else:
            print(f"[WARNING] Macro click {i+1} coordinates not defined during setup. Skipping this click.")
            print(f"[DEBUG] Coordinate {i+1} was None. Skipping this click.")

    print("[ACTION] Macro clicks finished.")
    print(f"[DEBUG] Exiting perform_macro_clicks().")

# --- Menu Functions ---
def display_main_menu():
    """Displays the main menu and handles user selection.
    Returns (should_run_automation: bool, run_with_macro: bool).
    """
    print("[DEBUG] Entering display_main_menu().")
    while True:
        print("\n--- Main Menu ---")
        print("1. Run WITH Macro Clicks (types string + performs user-defined clicks)")
        print("2. Run WITHOUT Macro Clicks (types string ONLY)")
        print("3. Access Settings")
        print("4. Reset Progress (starts from 'a')")
        print("Q. Quit Script")

        choice = input("Enter your choice: ").strip().lower()
        print(f"[DEBUG] User choice in main menu: '{choice}'.")

        if choice == '1':
            print("[DEBUG] User chose '1'. Returning (True, True).")
            return True, True # Run with macro clicks
        elif choice == '2':
            print("[DEBUG] User chose '2'. Returning (True, False).")
            return True, False # Run without macro clicks
        elif choice == '3':
            print("[DEBUG] User chose '3'. Calling display_settings_menu().")
            display_settings_menu() # Go to settings
        elif choice == '4':
            print("[DEBUG] User chose '4'. Prompting for progress reset confirmation.")
            confirm = input("Are you sure you want to reset progress? This cannot be undone. (y/n): ").strip().lower()
            print(f"[DEBUG] User confirmation for reset: '{confirm}'.")
            if confirm == 'y':
                reset_progress(settings['progress_file_path'])
            else:
                print("[INFO] Progress reset cancelled.")
                print("[DEBUG] User cancelled progress reset.")
        elif choice == 'q':
            print("[DEBUG] User chose 'Q'. Returning (False, False) to quit script.")
            return False, False # Quit script
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4, or Q.")
            print(f"[DEBUG] Invalid choice '{choice}'. Re-displaying main menu.")

def display_settings_menu():
    """Displays the settings menu and handles user selection."""
    global settings
    print("[DEBUG] Entering display_settings_menu().")
    while True:
        print("\n--- Settings Menu ---")
        print(f"Current Settings File: {settings.get('settings_file_path', DEFAULT_SETTINGS_FILE)}")
        print(f"Current Progress File: {settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])}")
        print(f"Delay Between Repetitions: {settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])}s")
        print(f"Delay Between Macro Clicks: {settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])}s")
        print(f"PyAutoGUI Write Interval: {settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])}s")
        print(f"Initial Delay Before Automation: {settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])}s") # NEW
        print(f"Character Set: '{settings.get('chars', DEFAULT_SETTINGS['chars'])}'")
        print("\n1. Change File Paths")
        print("2. Change Intervals")
        print("3. Change Character Set") # New option for character set customization
        print("B. Back to Main Menu")

        choice = input("Enter your choice: ").strip().lower()
        print(f"[DEBUG] User choice in settings menu: '{choice}'.")

        if choice == '1':
            print("[DEBUG] User chose '1'. Calling display_file_paths_menu().")
            display_file_paths_menu()
        elif choice == '2':
            print("[DEBUG] User chose '2'. Calling display_intervals_menu().")
            display_intervals_menu()
        elif choice == '3':
            print("[DEBUG] User chose '3'. Calling change_character_set().")
            change_character_set()
        elif choice == 'b':
            print("[DEBUG] User chose 'B'. Exiting settings menu.")
            break # Exit settings menu
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, or B.")
            print(f"[DEBUG] Invalid choice '{choice}'. Re-displaying settings menu.")

def display_file_paths_menu():
    """Allows changing settings and progress file paths."""
    global settings
    print("[DEBUG] Entering display_file_paths_menu().")
    while True:
        print("\n--- File Paths Settings ---")
        print(f"1. Current Settings File Path: {settings.get('settings_file_path', DEFAULT_SETTINGS_FILE)}")
        print(f"2. Current Progress File Path: {settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])}")
        print("B. Back to Settings Menu")

        choice = input("Enter your choice (1, 2, or B): ").strip().lower()

        if choice == '1':
            new_path = input(f"Enter new settings file path (current: {settings['settings_file_path']}): ").strip()
            print(f"[DEBUG] User entered new settings file path: '{new_path}'.")
            if new_path:
                settings['settings_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
                print(f"[INFO] Settings file path updated to '{new_path}'. (Changes effective next script run)")
                print(f"[DEBUG] settings['settings_file_path'] updated to '{new_path}'.")
            else:
                print("[INFO] Path not changed.")
                print("[DEBUG] User left path empty. No change to settings file path.")
        elif choice == '2':
            new_path = input(f"Enter new progress file path (current: {settings['progress_file_path']}): ").strip()
            print(f"[DEBUG] User entered new progress file path: '{new_path}'.")
            if new_path:
                # Ensure the new path points to a directory within USER_HOME_DIR if it's just a filename
                if os.path.basename(new_path) == new_path: # If it's just a filename, assume it's in USER_HOME_DIR
                    new_path = os.path.join(USER_HOME_DIR, new_path)
                    print(f"[DEBUG] New progress path was just a filename, assumed in USER_HOME_DIR: '{new_path}'")

                settings['progress_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings) # Save updated progress path to settings file
                print(f"[INFO] Progress file path updated to '{new_path}'.")
                print(f"[DEBUG] settings['progress_file_path'] updated to '{new_path}'. Settings saved to reflect change.")
                
                # Also, ensure the directory for the new path exists and create the file
                progress_dir = os.path.dirname(new_path)
                if progress_dir and not os.path.exists(progress_dir):
                    os.makedirs(progress_dir, exist_ok=True)
                    print(f"[INFO] Created directory for new progress file: '{progress_dir}'")
                    print(f"[DEBUG] Directory '{progress_dir}' created for new progress file path.")
                if not os.path.exists(new_path):
                    try:
                        with open(new_path, 'w') as f:
                            f.write('')
                        print(f"[INFO] Created empty progress file at new path: '{new_path}'")
                        print(f"[DEBUG] Empty file '{new_path}' created after path change.")
                    except Exception as e:
                        print(f"[ERROR] Could not create empty progress file at '{new_path}': {e}")
                        print(f"[DEBUG] Exception during creating empty progress file after path change: {e}")

            else:
                print("[INFO] Path not changed.")
                print("[DEBUG] User left path empty. No change to progress file path.")
        elif choice == 'b':
            print("[DEBUG] User chose 'B'. Exiting file paths menu.")
            break
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, or B.")
            print(f"[DEBUG] Invalid choice '{choice}'. Re-displaying file paths menu.")
    print("[DEBUG] Exiting display_file_paths_menu().")

def display_intervals_menu():
    """Allows changing time interval settings."""
    global settings
    print("[DEBUG] Entering display_intervals_menu().")
    while True:
        print("\n--- Interval Settings ---")
        print(f"1. Delay Between Repetitions (Current: {settings['delay_between_repetitions']}s)")
        print(f"2. Delay Between Macro Clicks (Current: {settings['delay_between_macro_clicks']}s)")
        print(f"3. PyAutoGUI Write Interval (Current: {settings['pyautogui_write_interval']}s)")
        print(f"4. Initial Delay Before Automation (Current: {settings['initial_delay_before_automation']}s)") # NEW
        print("B. Back to Settings Menu")

        choice = input("Enter your choice (1, 2, 3, 4, or B): ").strip().lower() # Updated choices
        print(f"[DEBUG] User choice in intervals menu: '{choice}'.")

        try:
            if choice == '1':
                new_delay = float(input("Enter new delay between repetitions (seconds): ").strip())
                print(f"[DEBUG] User entered new delay_between_repetitions: {new_delay}.")
                if new_delay >= 0:
                    settings['delay_between_repetitions'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[DEBUG] delay_between_repetitions updated to {new_delay}s and settings saved.")
                else:
                    print("[ERROR] Delay cannot be negative.")
                    print("[DEBUG] Negative delay input for repetitions.")
            elif choice == '2':
                new_delay = float(input("Enter new delay between macro clicks (seconds): ").strip())
                print(f"[DEBUG] User entered new delay_between_macro_clicks: {new_delay}.")
                if new_delay >= 0:
                    settings['delay_between_macro_clicks'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[DEBUG] delay_between_macro_clicks updated to {new_delay}s and settings saved.")
                else:
                    print("[ERROR] Delay cannot be negative.")
                    print("[DEBUG] Negative delay input for macro clicks.")
            elif choice == '3':
                new_delay = float(input("Enter new PyAutoGUI write interval (seconds): ").strip())
                print(f"[DEBUG] User entered new pyautogui_write_interval: {new_delay}.")
                if new_delay >= 0:
                    settings['pyautogui_write_interval'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[DEBUG] pyautogui_write_interval updated to {new_delay}s and settings saved.")
                else:
                    print("[ERROR] Interval cannot be negative.")
                    print("[DEBUG] Negative interval input for pyautogui write.")
            elif choice == '4': # NEW OPTION FOR INITIAL DELAY
                new_delay = float(input("Enter new initial delay before automation starts (seconds): ").strip())
                print(f"[DEBUG] User entered new initial_delay_before_automation: {new_delay}.")
                if new_delay >= 0:
                    settings['initial_delay_before_automation'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                    print(f"[DEBUG] initial_delay_before_automation updated to {new_delay}s and settings saved.")
                else:
                    print("[ERROR] Delay cannot be negative.")
                    print("[DEBUG] Negative delay input for initial automation delay.")
            elif choice == 'b':
                print("[DEBUG] User chose 'B'. Exiting intervals menu.")
                break
            else:
                print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4, or B.") # Updated message
                print(f"[DEBUG] Invalid choice '{choice}'. Re-displaying intervals menu.")
        except ValueError:
            print("[ERROR] Invalid input. Please enter a number.")
            print("[DEBUG] ValueError for interval input.")
    print("[DEBUG] Exiting display_intervals_menu().")

def change_character_set():
    """Allows changing the character set for combination generation."""
    global settings
    print("[DEBUG] Entering change_character_set().")
    print("\n--- Change Character Set ---")
    print(f"Current Character Set: '{settings.get('chars', DEFAULT_SETTINGS['chars'])}'")
    print("Default Characters: " + string.ascii_letters + string.digits + string.punctuation)
    print("You can enter any string of characters you want to use.")
    print("Example: 'abc' for only lowercase a, b, c.")
    new_chars = input("Enter new character set (or leave empty to keep current): ").strip()
    print(f"[DEBUG] User entered new character set: '{new_chars}'.")
    if new_chars:
        settings['chars'] = new_chars
        save_settings(settings['settings_file_path'], settings)
        print(f"[INFO] Character set updated to: '{new_chars}'")
        print(f"[DEBUG] Character set updated to '{new_chars}' and settings saved.")
    else:
        print("[INFO] Character set not changed.")
        print("[DEBUG] User left character set empty. No change.")
    input("Press Enter to continue...")
    print("[DEBUG] Exiting change_character_set().")


# --- Main Execution Block ---
if __name__ == "__main__":
    print("[DEBUG] Script started (main execution block).")
    # Ensure pyautogui fail-safe is enabled and interval is 0 for initial operations
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0 # Set to 0 initially for menu interactions
    print(f"[DEBUG] pyautogui.FAILSAFE set to True. pyautogui.PAUSE set to {pyautogui.PAUSE}s.")

    print("--- Python Combination Generator & Automation Script (DEBUG VERSION) ---")
    print("This script systematically generates string combinations, types them,")
    print("and performs actions based on your configuration.")

    # 1. Determine and load settings
    settings_file_chosen = DEFAULT_SETTINGS_FILE # Use the auto-created path
    print(f"[DEBUG] Settings file path resolved to: '{settings_file_chosen}'.")
    load_settings(settings_file_chosen) # Load settings (or defaults if file invalid/missing)
    # Ensure the settings file path itself is correctly stored in settings for future saves
    settings['settings_file_path'] = settings_file_chosen
    print(f"[DEBUG] settings['settings_file_path'] confirmed as '{settings['settings_file_path']}'.")
    save_settings(settings['settings_file_path'], settings) # Save defaults if new file was created or existing updated
    print(f"[DEBUG] Initial settings state after load/save: {settings}")

    # Ensure the progress file exists at script start
    progress_file_path = settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])
    print(f"[DEBUG] Checking existence of progress file at: '{progress_file_path}'.")
    progress_dir = os.path.dirname(progress_file_path)
    if progress_dir and not os.path.exists(progress_dir):
        os.makedirs(progress_dir, exist_ok=True)
        print(f"[INFO] Created directory for progress file: '{progress_dir}'")
        print(f"[DEBUG] Directory '{progress_dir}' created for progress file at start.")
    if not os.path.exists(progress_file_path):
        try:
            with open(progress_file_path, 'w') as f:
                f.write('') # Create an empty file
            print(f"[INFO] Created empty progress file at: '{progress_file_path}'")
            print(f"[DEBUG] Empty progress file '{progress_file_path}' created at script start.")
        except Exception as e:
            print(f"[ERROR] Could not create empty progress file at '{progress_file_path}': {e}")
            print(f"[DEBUG] Exception during initial progress file creation: {e}")


    # 2. Register the stop hotkey
    print("[DEBUG] Attempting to register hotkey 'ctrl+shift+c+v'.")
    try:
        keyboard.add_hotkey('ctrl+shift+c+v', on_stop_hotkey_pressed)
        print(f"\n[INFO] Stop hotkey 'Ctrl+Shift+C+V' registered.")
        print("[DEBUG] Hotkey registration successful.")
    except Exception as e:
        print(f"[ERROR] Could not register hotkey. This might be due to permissions or conflicts: {e}")
        print("         You can still stop the script by moving your mouse to a corner or pressing Ctrl+C in the terminal.")
        print(f"[DEBUG] Hotkey registration failed: {e}")
    
    # --- Main Application Loop (keeps the script running until explicitly quit) ---
    print("\n[DEBUG] Entering main application loop.")
    while True:
        # Reset STOP_SCRIPT flag before entering automation if it was set by a previous run's interruption
        if STOP_SCRIPT:
            print("[DEBUG] STOP_SCRIPT was True from previous automation run. Resetting to False for new menu cycle.")
            STOP_SCRIPT = False 

        run_automation_chosen, with_macro_clicks_chosen = display_main_menu()
        print(f"[DEBUG] Returned from display_main_menu: run_automation_chosen={run_automation_chosen}, with_macro_clicks_chosen={with_macro_clicks_chosen}.")

        if not run_automation_chosen: # User chose to quit ('Q')
            print("[DEBUG] User chose to quit. Breaking main application loop.")
            break # Exit the main application loop, leading to final cleanup

        # User chose to run automation (either with or without macro clicks)
        pyautogui.PAUSE = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
        print(f"[DEBUG] pyautogui.PAUSE set to {pyautogui.PAUSE}s for automation based on settings.")
        
        # Determine the initial delay from settings
        initial_delay = settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])

        # Handle macro clicks setup if chosen
        if with_macro_clicks_chosen:
            print("[DEBUG] User chose to run WITH macro clicks. Starting setup process.")
            print("\n[INFO] Please read the instructions below carefully before proceeding.")
            print("       You will define the number of macro clicks and then capture their coordinates.")
            print("       Then, the main automation loop will begin.")
            print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
            print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
            print("       Or, press Ctrl+C in the terminal to force quit.")
            print(f"\n[INFO] Waiting {initial_delay} seconds. Use this time to prepare your target application and read the instructions.") # Used new setting
            print(f"[DEBUG] Starting {initial_delay}-second initial delay for macro setup.")
            time.sleep(initial_delay) # Used new setting
            print("[DEBUG] Initial delay for macro setup finished.")

            setup_successful = get_clicks_for_setup()
            print(f"[DEBUG] get_clicks_for_setup() returned: {setup_successful}.")
            if not setup_successful:
                # User chose to go back during setup, or setup failed
                print("[INFO] Macro click setup was not completed. Returning to Main Menu.")
                print("[DEBUG] Macro setup unsuccessful. Resetting pyautogui.PAUSE to 0 and continuing to next main loop iteration.")
                pyautogui.PAUSE = 0 # Reset pause for menu interaction
                continue # Go back to the beginning of the while True loop (main menu)
        else: # User chose to run WITHOUT macro clicks
            print("[DEBUG] User chose to run WITHOUT macro clicks. Skipping click setup.")
            print("\n[INFO] Running WITHOUT macro clicks. Click setup skipped.")
            print("\n[INFO] Please read the instructions below carefully before proceeding.")
            print("       The main automation loop will begin shortly.")
            print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
            print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
            print("       Or, press Ctrl+C in the terminal to force quit.")
            print(f"\n[INFO] Waiting {initial_delay} seconds. Use this time to prepare your target application and read the instructions.") # Used new setting
            print(f"[DEBUG] Starting {initial_delay}-second initial delay for automation without macros.")
            time.sleep(initial_delay) # Used new setting
            print("[DEBUG] Initial delay finished.")


        # --- Automation Loop (this block only executes if setup was successful or no macro clicks chosen) ---
        print("\n--- Starting Automation Loop ---")
        progress_file_path = settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])
        print(f"[INFO] Starting to generate combinations. Progress will be saved to and resumed from: '{progress_file_path}'.")
        print(f"[DEBUG] Attempting to load previous progress from '{progress_file_path}'.")
        
        start_combination = load_progress(progress_file_path)
        print(f"[DEBUG] Progress loaded: '{start_combination}'. Initializing generator.")
        generator = generate_all_combinations(start_combination=start_combination)
        print("[DEBUG] Generator object created.")

        try:
            print("[DEBUG] Entering main iteration loop for generator.")
            for current_string in generator:
                print(f"[DEBUG] Processing string from generator: '{current_string}'.")
                if STOP_SCRIPT: # Hotkey detected
                    print("[INFO] Stop flag set (hotkey triggered). Exiting automation loop to Main Menu.")
                    print("[DEBUG] STOP_SCRIPT is True. Breaking inner automation loop.")
                    break # Break the for loop, control goes to finally then back to main while loop

                print(f"\n[ACTION] Processing string: '{current_string}'")
                try:
                    type_the_string(current_string)
                    if with_macro_clicks_chosen: # Only perform clicks if chosen
                        print("[DEBUG] with_macro_clicks_chosen is True. Calling perform_macro_clicks().")
                        perform_macro_clicks()
                    else:
                        print("[DEBUG] with_macro_clicks_chosen is False. Skipping macro clicks.")
                except pyautogui.FailSafeException:
                    print("\n[CRITICAL ERROR] pyautogui Fail-safe triggered during action. Returning to Main Menu.")
                    print("[DEBUG] pyautogui.FailSafeException caught. Setting STOP_SCRIPT to True and breaking loop.")
                    STOP_SCRIPT = True  # Set STOP_SCRIPT to ensure clean break
                    break # Break the for loop
                except Exception as e:
                    print(f"[ERROR] An unexpected error occurred during action for string '{current_string}': {e}.")
                    print("         Attempting to continue to the next combination.")
                    print(f"[DEBUG] General exception caught during action: {e}. Attempting to continue loop.")
                
                if STOP_SCRIPT: # Check again in case an error occurred right before sleep or another hotkey press
                    print("[INFO] Stop flag set (hotkey triggered). Exiting automation loop to Main Menu.")
                    print("[DEBUG] STOP_SCRIPT is True after action. Breaking inner automation loop.")
                    break

                save_progress(progress_file_path, current_string)
                print(f"[INFO] Progress saved: '{current_string}'")
                print(f"[DEBUG] Progress '{current_string}' saved to '{progress_file_path}'.")

                delay = settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])
                print(f"[INFO] Waiting {delay} second before next combination...")
                print(f"[DEBUG] Pausing for {delay}s (delay_between_repetitions).")
                time.sleep(delay)
                print("[DEBUG] Pause finished. Proceeding to next combination.")

            else: # This 'else' block executes if the 'for current_string in generator' loop finishes WITHOUT a 'break'
                print("[DEBUG] Generator loop finished without break. This indicates generator exhaustion, which should not happen in this infinite script.")
                print("[INFO] Automation loop finished unexpectedly (generator exhausted). This shouldn't happen.")

        except KeyboardInterrupt:
            print("\n[INFO] Ctrl+C detected. Returning to Main Menu.")
            print("[DEBUG] KeyboardInterrupt caught. Setting STOP_SCRIPT to True and passing to finally.")
            STOP_SCRIPT = True  
            pass # The outer loop will handle returning to main menu.
        except Exception as e:
            print(f"\n[CRITICAL ERROR] A critical error occurred in the main automation loop: {e}. Returning to Main Menu.")
            print(f"[DEBUG] Critical error caught in main automation loop: {e}. Setting STOP_SCRIPT to True and passing to finally.")
            STOP_SCRIPT = True
            pass
        finally:
            print("\n--- Automation Loop Ended ---")
            print("[DEBUG] Finally block of automation loop executed.")
            pyautogui.PAUSE = 0 # Reset pause for menu interaction
            print(f"[DEBUG] pyautogui.PAUSE reset to {pyautogui.PAUSE}s.")
            # Control naturally goes back to the outer `while True` loop after this `try...except...finally` block
            # which will then display the main menu again.
            print("[DEBUG] Returning to main application loop for menu display.")

# --- Final cleanup and actual script exit (only happens if user chose 'Q' from main menu) ---
print("\n--- Script Exiting ---")
print("[DEBUG] Script is preparing to exit gracefully.")
keyboard.unhook_all()
print("[DEBUG] Keyboard hotkeys unhooked.")
input("Press Enter to exit...") # This will only show if 'Q' was pressed in main menu
print("[DEBUG] User pressed Enter. Performing sys.exit(0).")
sys.exit(0)
