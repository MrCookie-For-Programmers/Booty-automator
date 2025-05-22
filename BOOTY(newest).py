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
click_coords = [] # Stores (x, y) tuples for the macro clicks, dynamically sized
current_coord_capture_index = 0 # Helper for the setup phase
mouse_listener_active = False # Flag to control pynput listener

# These are global for setup, but their effective values depends on user input in get_clicks_for_setup
num_macro_clicks = 0
num_ignored_clicks_setup = 0

# --- DEBUG MODE (Controlled by settings) ---
DEBUG_MODE = False # This will be updated by load_settings based on user's saved preference

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
    'delay_between_repetitions': 0.1, # Seconds to wait after a string has been processed
    'delay_between_macro_clicks': 0.01, # Seconds to wait between individual macro clicks
    'pyautogui_write_interval': 0.0, # Seconds to wait between each character typed by pyautogui.write
    'initial_delay_before_automation': 10.0, # Seconds to wait before the automation loop starts
    'progress_file_path': os.path.join(USER_HOME_DIR, 'progress.txt'), # DEFAULT path for the combination progress file
    'progress_file_for_custom_list_path': os.path.join(USER_HOME_DIR, 'progressforcustomlist.txt'), # DEFAULT path for the custom list progress file
    'settings_file_path': DEFAULT_SETTINGS_FILE, # Path where settings are saved (this will be updated if user changes it)
    'debug_mode': False # New default setting for debug mode
}

# Global dictionary to hold current settings
settings = {}

# --- Hotkey Callback ---
def on_stop_hotkey_pressed():
    """Callback function executed when the Ctrl+Shift+C+V hotkey is pressed."""
    global STOP_SCRIPT
    STOP_SCRIPT = True
    print("\n[INFO] Stop hotkey (Ctrl+Shift+C+V) detected. Script will terminate gracefully after current action.")
    debug_print("Stop hotkey pressed, setting STOP_SCRIPT to True.")

# --- Settings File Functions ---
def load_settings(file_path):
    """
    Loads settings from the specified JSON file.
    Merges with DEFAULT_SETTINGS to ensure all keys are present.
    """
    global settings, DEBUG_MODE # Need to modify global DEBUG_MODE here
    loaded_settings = {}
    debug_print(f"Attempting to load settings from '{file_path}'.") # This will only show if DEBUG_MODE is already True from a previous run or default
    
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

    # Merge loaded settings with defaults to ensure all keys are present
    current_settings = DEFAULT_SETTINGS.copy()
    current_settings.update(loaded_settings)
    
    # Ensure chars is string, as JSON might mess with it if not handled properly
    if not isinstance(current_settings.get('chars'), str):
        print("[WARNING] 'chars' setting invalid. Resetting to default character set.")
        debug_print("Invalid 'chars' setting, resetting to default.")
        current_settings['chars'] = DEFAULT_SETTINGS['chars']

    # Update global DEBUG_MODE based on loaded settings BEFORE assigning to 'settings'
    DEBUG_MODE = current_settings.get('debug_mode', DEFAULT_SETTINGS['debug_mode'])
    debug_print(f"DEBUG_MODE set to {DEBUG_MODE} based on loaded settings.")

    settings = current_settings
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

    input("Press Enter to continue...") # Pause for user to read

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
    input("Press Enter to continue...") # Pause for user to read

# --- Mouse Listener Callback for Setup ---
def on_click_for_setup(x, y, button, pressed):
    """
    Callback function for pynput mouse listener during the setup phase.
    Captures the specified number of coordinates after ignoring initial clicks.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords, num_macro_clicks, num_ignored_clicks_setup

    if pressed: # Only act on mouse down event
        debug_print(f"Mouse click detected at ({x}, {y}). Button: {button}. Pressed: {pressed}")
        current_coord_capture_index += 1

        # If we are still in the 'ignored clicks' phase
        if current_coord_capture_index <= num_ignored_clicks_setup:
            print(f"  Click {current_coord_capture_index} received. This click is ignored ({num_ignored_clicks_setup - current_coord_capture_index + 1} more ignored clicks).")
        else:
            # Calculate the 0-indexed position in the click_coords list
            macro_click_list_index = current_coord_capture_index - num_ignored_clicks_setup - 1

            if macro_click_list_index >= 0 and macro_click_list_index < num_macro_clicks:
                click_coords[macro_click_list_index] = (x, y)
                print(f"  Coordinate {macro_click_list_index + 1} (X: {x}, Y: {y}) saved.")
                debug_print(f"Saved coordinate ({x}, {y}) at index {macro_click_list_index}.")

            # Check if all required macro clicks have been captured
            if (macro_click_list_index + 1) == num_macro_clicks:
                print("  All required coordinates captured. Exiting setup mode.")
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
    global current_coord_capture_index, mouse_listener_active, click_coords, num_macro_clicks, num_ignored_clicks_setup

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
                debug_print("Invalid input for num_macro_clicks: negative.")
                continue
            num_macro_clicks = num
            debug_print(f"num_macro_clicks set to {num_macro_clicks}.")
            break
        except ValueError:
            print("[ERROR] Please enter a valid number or 0.")
            debug_print("Invalid input for num_macro_clicks: not a number.")

    if num_macro_clicks == 0:
        print("[INFO] 0 macro clicks selected. Skipping coordinate capture.")
        debug_print("Skipping coordinate capture as num_macro_clicks is 0.")
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

    # Dynamically size the click_coords list based on user input
    click_coords.clear() # Clear any previous clicks
    click_coords.extend([None] * num_macro_clicks)
    current_coord_capture_index = 0 # Reset total clicks seen for new setup
    debug_print(f"click_coords initialized to {click_coords}.")

    print("\n--- Start Capturing Coordinates ---")
    if num_ignored_clicks_setup > 0:
        print(f"Make your first {num_ignored_clicks_setup} clicks anywhere on screen. These will be ignored.")
    print(f"Then, click on the exact {num_macro_clicks} positions where you want the script to click.")
    print(f"Total clicks expected: {num_ignored_clicks_setup + num_macro_clicks}")
    
    time.sleep(0.5) 

    mouse_listener_active = True
    debug_print("Starting pynput mouse listener.")
    with mouse.Listener(on_click=on_click_for_setup) as listener:
        listener.join() # Blocks until on_click_for_setup returns False and stops the listener

    # Final check if all clicks were indeed captured
    if None in click_coords:
        print("[WARNING] Not all desired macro coordinates were captured during setup. Macro clicks may be incomplete.")
        debug_print("Not all macro clicks were captured.")
        return True # Still return True, so the script runs but with incomplete clicks
    else:
        print("\nSetup complete. All required coordinates captured!")
        debug_print("All macro clicks captured successfully.")
        return True

# --- Combination Generator ---
def generate_all_combinations(start_combination=None):
    """
    Generates all string combinations lexicographically, starting from length 1.
    If start_combination is provided, it resumes from that point.
    This generator runs indefinitely.
    """
    chars_set = settings.get('chars', DEFAULT_SETTINGS['chars']) # Use configured chars
    debug_print(f"Character set for combination generation: '{chars_set}'.")
    
    # Flag to indicate if we have reached or passed the start_combination
    started_yielding = False

    if start_combination:
        start_length = len(start_combination)
        debug_print(f"Attempting to resume from start_combination: '{start_combination}' (length {start_length}).")
        
        # Iterate up to the starting length to find the start_combination
        for length_iter in itertools.count(1):
            if STOP_SCRIPT: 
                debug_print("STOP_SCRIPT detected during resume search.")
                return
            
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

        if not started_yielding: # This case is if start_combination was provided but somehow not found (e.g., too long)
             print(f"[WARNING] Resume point '{start_combination}' was not found (too long or invalid). Starting from 'a'.")
             debug_print("Resume point not found and started_yielding is false. Resetting.")
             start_combination = None
             started_yielding = True # Force yielding from now on, starting with 'a'


    # Main generation loop (either from beginning or after resuming)
    actual_start_length_for_gen = 1
    if start_combination and started_yielding and len(start_combination) > 0:
        actual_start_length_for_gen = len(start_combination)
    debug_print(f"Actual starting length for generation: {actual_start_length_for_gen}.")


    for length in itertools.count(actual_start_length_for_gen):
        if STOP_SCRIPT: 
            debug_print(f"STOP_SCRIPT detected during generation for length {length}.")
            return
        print(f"\n[INFO] Generating combinations for length: {length} (Total possible: {len(chars_set)**length})")
        debug_print(f"Starting combinations for length {length}.")
        
        skip_to_start_combo = False
        # If we just finished searching for a resume point and it was *not* found, and length matches, we are now at the start of the next combo
        if start_combination and length == len(start_combination) and not started_yielding:
            skip_to_start_combo = True
            debug_print(f"Setting skip_to_start_combo to True for length {length} matching start_combination length.")
            
        for combo_tuple in itertools.product(chars_set, repeat=length):
            if STOP_SCRIPT: 
                debug_print(f"STOP_SCRIPT detected during inner loop for length {length}.")
                return
            current_combo_str = ''.join(combo_tuple)
            
            if skip_to_start_combo:
                if current_combo_str == start_combination:
                    skip_to_start_combo = False # Found it, stop skipping
                    started_yielding = True # Ensure this flag is set for subsequent iterations
                    debug_print(f"Found {start_combination}, stopping skipping and starting yielding.")
                continue # Keep skipping until we find the start_combination
            
            if started_yielding or start_combination is None: # Only yield if we've passed the resume point or no resume point was set
                debug_print(f"Yielding combination: '{current_combo_str}'")
                yield current_combo_str

# --- Core Action Functions ---
def type_character_safely(char):
    """
    Types a single character, handling potential keyboard layout issues for special characters.
    Uses pyperclip for characters known to be problematic with direct pyautogui.write,
    otherwise falls back to pyautogui.write.
    """
    # Define characters that might cause issues on non-US layouts and are better pasted.
    # This list can be expanded based on user's specific keyboard layout issues.
    # For QWERTZ, '#' is a common issue.
    # We include string.punctuation as a general category for potential issues.
    # Note: string.digits are usually fine with pyautogui.write, but included for extreme caution.
    problematic_chars = string.punctuation 
    
    # Specific problematic chars for QWERTZ from your description:
    # # (hash) - often AltGr+3 or Shift+´
    # ' (apostrophe) - often a direct key
    
    # Try using pyperclip for characters that might cause issues, or are not ASCII.
    # This is generally safer for international keyboards and special symbols.
    if len(char) == 1 and char in problematic_chars: # Check if it's a single problematic punctuation
        try:
            # Preserve current clipboard content
            current_clipboard = None
            try:
                current_clipboard = pyperclip.paste()
            except pyperclip.PyperclipException as e:
                debug_print(f"Warning: Could not get current clipboard content: {e}")
                # If paste fails, current_clipboard remains None, so we don't try to restore it.

            pyperclip.copy(char) # Copy the character
            pyautogui.hotkey('ctrl', 'v') # Paste it
            debug_print(f"Typed '{char}' using clipboard paste.")
        except pyperclip.PyperclipException as e:
            print(f"[WARNING] Could not use pyperclip for character '{char}': {e}. Falling back to direct type. This might cause issues.")
            debug_print(f"Pyperclip error for '{char}': {e}. Falling back to pyautogui.write.")
            pyautogui.write(char) # Fallback to direct write if pyperclip fails
        finally:
            # Restore original clipboard content if there was any
            if current_clipboard is not None:
                try:
                    pyperclip.copy(current_clipboard)
                    debug_print("Restored original clipboard content.")
                except pyperclip.PyperclipException as e:
                    debug_print(f"Warning: Could not restore clipboard content: {e}")
    else:
        # For alphanumeric characters and other simple characters, direct pyautogui.write is generally fine.
        # This is more efficient than copy-pasting for every single character.
        pyautogui.write(char) 
        debug_print(f"Typed '{char}' using direct pyautogui.write.")

def type_the_string(current_string):
    """Types the given string character by character, handling special characters safely, and presses Enter."""
    write_interval = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
    print(f"[ACTION] Typing: '{current_string}' (Length: {len(current_string)})")
    debug_print(f"Starting to type string '{current_string}' with interval {write_interval}.")

    for char in current_string:
        if STOP_SCRIPT:
            debug_print("STOP_SCRIPT detected during character typing.")
            break # Stop typing if script is stopping
        type_character_safely(char)
        time.sleep(write_interval) # Apply interval between characters

    pyautogui.press('enter')
    print(f"[ACTION] Enter pressed.")
    debug_print("pyautogui.press('enter') called.")

def perform_macro_clicks():
    """Performs the specific click combination using the globally captured coordinates."""
    macro_delay = settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])
    print("[ACTION] Performing macro clicks...")
    debug_print(f"Starting macro clicks with delay {macro_delay}s. Clicks defined: {click_coords}.")
    
    if not click_coords or all(c is None for c in click_coords):
        print("[WARNING] No macro click coordinates defined or captured. Skipping clicks.")
        debug_print("click_coords is empty or all None, skipping macro clicks.")
        return

    # Iterate through the captured click coordinates and perform clicks
    for i, coords in enumerate(click_coords):
        if coords: # Ensure coordinates were actually captured for this slot
            print(f"  Clicking at Coordinate {i+1}: {coords}")
            debug_print(f"Calling pyautogui.click(x={coords[0]}, y={coords[1]}).")
            pyautogui.click(x=coords[0], y=coords[1])
            time.sleep(macro_delay) # Use the configured delay
            debug_print(f"Sleeping for {macro_delay} seconds after click.")
        else:
            print(f"[WARNING] Macro click {i+1} coordinates not defined during setup. Skipping this click.")
            debug_print(f"Coordinates for click {i+1} were None, skipping.")

    print("[ACTION] Macro clicks finished.")
    debug_print("Finished performing all macro clicks.")

def process_text_file_automation():
    """
    Prompts the user for a .txt file path, reads its content line by line,
    types each line, and presses Enter after each.
    """
    print("\n--- Process Text File Automation ---")
    file_path = input("Enter the full path to the .txt file you want to process: ").strip()
    debug_print(f"User entered text file path: '{file_path}'.")

    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'. Please check the path and try again.")
        debug_print(f"File '{file_path}' does not exist.")
        input("Press Enter to continue...")
        return

    initial_delay = settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])
    print(f"Switch to the application where you want to type. Typing will begin in {initial_delay} seconds...")
    debug_print(f"Initial delay before text file processing: {initial_delay}s.")
    time.sleep(initial_delay) # Give the user time to switch windows

    write_interval = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
    delay_between_repetitions = settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])
    debug_print(f"PyAutoGUI write interval: {write_interval}s, Delay between repetitions: {delay_between_repetitions}s.")

    try:
        with open(file_path, 'r', encoding='utf-8') as f: # Using utf-8 for broader compatibility
            debug_print(f"Opening file '{file_path}' for reading.")
            for line_num, line in enumerate(f, 1):
                if STOP_SCRIPT:
                    print("\n[INFO] Script stopped by hotkey during text file processing.")
                    debug_print("STOP_SCRIPT detected during text file processing.")
                    break

                content_to_type = line.rstrip('\n\r') # Remove only newline characters, keep other whitespace
                debug_print(f"Processing line {line_num}: raw='{line.strip()}', cleaned='{content_to_type}'.")

                print(f"Typing line {line_num}: '{content_to_type}'")
                
                # Use the new safe typing logic for the entire line
                for char in content_to_type:
                    if STOP_SCRIPT: break
                    type_character_safely(char)
                    time.sleep(write_interval) # Apply interval between characters
                
                if STOP_SCRIPT: break # Check again after typing the line

                pyautogui.press('enter')
                pyautogui.sleep(delay_between_repetitions) # Use repetition delay
                debug_print(f"Line {line_num} typed and enter pressed. Sleeping for {delay_between_repetitions}s.")

        print(f"\nFinished processing '{file_path}'.")
        debug_print(f"Successfully processed all lines in '{file_path}'.")

    except FileNotFoundError: # Redundant due to earlier check, but good practice
        print(f"Error: File not found at '{file_path}'.")
        debug_print(f"FileNotFoundError during text file processing: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred while processing the file: {e}")
        debug_print(f"General error during text file processing: {e}")
    finally:
        input("Press Enter to continue...") # Pause for user to read


# --- Menu Functions ---
def display_main_menu():
    """Displays the main menu and handles user selection.
    Returns (should_run_automation: bool, run_with_macro: bool, mode: str).
    Mode can be 'combinations', 'text_file', or 'quit'.
    """
    while True:
        print("\n--- Main Menu ---")
        print("1. Run Combination Generator WITH Macro Clicks")
        print("2. Run Combination Generator WITHOUT Macro Clicks")
        print("3. Access Settings")
        print("4. Reset Combination Progress (starts from 'a')")
        print("5. Process Text File (types content from a .txt file)")
        print("6. Reset Custom List Progress (resets the 'progressforcustomlist.txt' file)")
        print("7. Quit Script")

        choice = input("Enter your choice: ").strip().lower()
        debug_print(f"Main menu choice: '{choice}'.")

        if choice == '1':
            return True, True, 'combinations'
        elif choice == '2':
            return True, False, 'combinations'
        elif choice == '3':
            display_settings_menu() # Go to settings
        elif choice == '4':
            confirm = input("Are you sure you want to reset combination progress? This cannot be undone. (y/n): ").strip().lower()
            debug_print(f"Confirm reset combination progress: '{confirm}'.")
            if confirm == 'y':
                reset_progress(settings['progress_file_path'])
            else:
                print("[INFO] Combination progress reset cancelled.")
        elif choice == '5':
            return True, False, 'text_file' # Text file processing doesn't use macro clicks currently
        elif choice == '6':
            confirm = input("Are you sure you want to reset the custom list progress file? This will delete the file and create a new empty one. (y/n): ").strip().lower()
            debug_print(f"Confirm reset custom list progress: '{confirm}'.")
            if confirm == 'y':
                reset_custom_list_progress()
            else:
                print("[INFO] Custom list progress reset cancelled.")
        elif choice == '7':
            return False, False, 'quit'
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4, 5, 6 or 7.")
            debug_print("Invalid main menu choice.")

def display_settings_menu():
    """Displays the settings menu and handles user selection."""
    global settings, DEBUG_MODE
    while True:
        print("\n--- Settings Menu ---")
        print(f"Current Settings File: {settings.get('settings_file_path', DEFAULT_SETTINGS_FILE)}")
        print(f"Current Combination Progress File: {settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])}")
        print(f"Current Custom List Progress File: {settings.get('progress_file_for_custom_list_path', DEFAULT_SETTINGS['progress_file_for_custom_list_path'])}")
        print(f"Delay Between Repetitions: {settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])}s")
        print(f"Delay Between Macro Clicks: {settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])}s")
        print(f"PyAutoGUI Write Interval: {settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])}s")
        print(f"Initial Delay Before Automation: {settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])}s")
        print(f"Character Set: '{settings.get('chars', DEFAULT_SETTINGS['chars'])}'")
        print(f"Debug Mode: {'Enabled' if DEBUG_MODE else 'Disabled'}") # Display current debug status
        print("\n1. Change File Paths")
        print("2. Change Intervals")
        print("3. Change Character Set")
        print("4. Toggle Debug Mode") # New option for debug mode
        print("B. Back to Main Menu")

        choice = input("Enter your choice: ").strip().lower()
        debug_print(f"Settings menu choice: '{choice}'.")

        if choice == '1':
            display_file_paths_menu()
        elif choice == '2':
            display_intervals_menu()
        elif choice == '3':
            change_character_set()
        elif choice == '4': # Handle toggling debug mode
            settings['debug_mode'] = not settings.get('debug_mode', False)
            DEBUG_MODE = settings['debug_mode'] # Update the global flag immediately
            save_settings(settings['settings_file_path'], settings)
            print(f"[INFO] Debug Mode is now {'Enabled' if DEBUG_MODE else 'Disabled'}.")
            input("Press Enter to continue...")
        elif choice == 'b':
            break # Exit settings menu
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4 or B.")
            debug_print("Invalid settings menu choice.")

def display_file_paths_menu():
    """Allows changing settings and progress file paths."""
    global settings
    while True:
        print("\n--- File Paths Settings ---")
        print(f"1. Current Settings File Path: {settings.get('settings_file_path', DEFAULT_SETTINGS_FILE)}")
        print(f"2. Current Combination Progress File Path: {settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])}")
        print(f"3. Current Custom List Progress File Path: {settings.get('progress_file_for_custom_list_path', DEFAULT_SETTINGS['progress_file_for_custom_list_path'])}")
        print("B. Back to Settings Menu")

        choice = input("Enter your choice (1, 2, 3, or B): ").strip().lower()
        debug_print(f"File paths menu choice: '{choice}'.")

        if choice == '1':
            new_path = input(f"Enter new settings file path (current: {settings['settings_file_path']}): ").strip()
            debug_print(f"New settings file path input: '{new_path}'.")
            if new_path:
                settings['settings_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
                print(f"[INFO] Settings file path updated to '{new_path}'. (Changes effective next script run)")
            else:
                print("[INFO] Path not changed.")
        elif choice == '2':
            new_path = input(f"Enter new combination progress file path (current: {settings['progress_file_path']}): ").strip()
            debug_print(f"New combination progress file path input: '{new_path}'.")
            if new_path:
                # If it's just a filename, assume it's in USER_HOME_DIR
                if os.path.basename(new_path) == new_path:
                    new_path = os.path.join(USER_HOME_DIR, new_path)
                
                settings['progress_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings) # Save updated progress path to settings file
                # Also, ensure the directory for the new path exists and create the file
                progress_dir = os.path.dirname(new_path)
                if progress_dir and not os.path.exists(progress_dir):
                    os.makedirs(progress_dir, exist_ok=True)
                    debug_print(f"Created directory for new combination progress file: '{progress_dir}'")
                if not os.path.exists(new_path):
                    try:
                        with open(new_path, 'w') as f:
                            f.write('')
                        print(f"[INFO] Created empty combination progress file at new path: '{new_path}'")
                    except Exception as e:
                        print(f"[ERROR] Could not create empty combination progress file at '{new_path}': {e}")
                        debug_print(f"Error creating empty combination progress file: {e}")

                print(f"[INFO] Combination progress file path updated to '{new_path}'.")
            else:
                print("[INFO] Path not changed.")
        elif choice == '3':
            new_path = input(f"Enter new custom list progress file path (current: {settings['progress_file_for_custom_list_path']}): ").strip()
            debug_print(f"New custom list progress file path input: '{new_path}'.")
            if new_path:
                if os.path.basename(new_path) == new_path:
                    new_path = os.path.join(USER_HOME_DIR, new_path)
                
                settings['progress_file_for_custom_list_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
                # Ensure the directory exists and create the file if it doesn't
                initialize_custom_list_progress_file() # This function will handle creating the file if needed
                print(f"[INFO] Custom list progress file path updated to '{new_path}'.")
            else:
                print("[INFO] Path not changed.")
        elif choice == 'b':
            break
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, or B.")
            debug_print("Invalid file paths menu choice.")

def display_intervals_menu():
    """Allows changing time interval settings."""
    global settings
    while True:
        print("\n--- Interval Settings ---")
        print(f"1. Delay Between Repetitions (Current: {settings['delay_between_repetitions']}s)")
        print(f"2. Delay Between Macro Clicks (Current: {settings['delay_between_macro_clicks']}s)")
        print(f"3. PyAutoGUI Write Interval (Current: {settings['pyautogui_write_interval']}s)")
        print(f"4. Initial Delay Before Automation (Current: {settings['initial_delay_before_automation']}s)")
        print("B. Back to Settings Menu")

        choice = input("Enter your choice (1, 2, 3, 4, or B): ").strip().lower()
        debug_print(f"Intervals menu choice: '{choice}'.")

        try:
            if choice == '1':
                new_delay = float(input("Enter new delay between repetitions (seconds): ").strip())
                debug_print(f"New delay between repetitions input: {new_delay}.")
                if new_delay >= 0:
                    settings['delay_between_repetitions'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Delay cannot be negative.")
            elif choice == '2':
                new_delay = float(input("Enter new delay between macro clicks (seconds): ").strip())
                debug_print(f"New delay between macro clicks input: {new_delay}.")
                if new_delay >= 0:
                    settings['delay_between_macro_clicks'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Delay cannot be negative.")
            elif choice == '3':
                new_delay = float(input("Enter new PyAutoGUI write interval (seconds): ").strip())
                debug_print(f"New PyAutoGUI write interval input: {new_delay}.")
                if new_delay >= 0:
                    settings['pyautogui_write_interval'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Interval cannot be negative.")
            elif choice == '4':
                new_delay = float(input("Enter new initial delay before automation starts (seconds): ").strip())
                debug_print(f"New initial delay input: {new_delay}.")
                if new_delay >= 0:
                    settings['initial_delay_before_automation'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Delay cannot be negative.")
            elif choice == 'b':
                break
            else:
                print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4 or B.")
                debug_print("Invalid intervals menu choice.")
        except ValueError:
            print("[ERROR] Invalid input. Please enter a number.")
            debug_print("ValueError in intervals menu input.")

def change_character_set():
    """Allows changing the character set for combination generation."""
    global settings
    print("\n--- Change Character Set ---")
    print(f"Current Character Set: '{settings.get('chars', DEFAULT_SETTINGS['chars'])}'")
    print("Default Characters: " + string.ascii_letters + string.digits + string.punctuation)
    print("You can enter any string of characters you want to use.")
    print("Example: 'abc' for only lowercase a, b, c.")
    new_chars = input("Enter new character set (or leave empty to keep current): ").strip()
    debug_print(f"New character set input: '{new_chars}'.")
    if new_chars:
        settings['chars'] = new_chars
        save_settings(settings['settings_file_path'], settings)
        print(f"[INFO] Character set updated to: '{new_chars}'")
    else:
        print("[INFO] Character set not changed.")
    input("Press Enter to continue...")


# --- Main Execution Block ---
if __name__ == "__main__":
    print("--- Python Combination Generator & Automation Script ---")
    print("This script systematically generates string combinations, types them,")
    print("and performs actions based on your configuration.")

    # 1. Determine and load settings
    settings_file_chosen = DEFAULT_SETTINGS_FILE
    load_settings(settings_file_chosen) # Load settings (or defaults if file invalid/missing). This also sets global DEBUG_MODE.
    
    # Ensure the settings file path itself is correctly stored in settings for future saves
    settings['settings_file_path'] = settings_file_chosen
    save_settings(settings['settings_file_path'], settings) # Save defaults if new file was created or existing updated

    # Ensure the progress files exist at script start
    progress_file_path_combinations = settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])
    progress_dir_combinations = os.path.dirname(progress_file_path_combinations)
    debug_print(f"Checking combination progress file directory: '{progress_dir_combinations}'.")
    if progress_dir_combinations and not os.path.exists(progress_dir_combinations):
        os.makedirs(progress_dir_combinations, exist_ok=True)
        print(f"[INFO] Created directory for combination progress file: '{progress_dir_combinations}'")
        debug_print(f"Directory '{progress_dir_combinations}' created.")
    if not os.path.exists(progress_file_path_combinations):
        try:
            with open(progress_file_path_combinations, 'w') as f:
                f.write('') # Create an empty file
            print(f"[INFO] Created empty combination progress file at: '{progress_file_path_combinations}'")
            debug_print(f"Empty combination progress file created at '{progress_file_path_combinations}'.")
        except Exception as e:
            print(f"[ERROR] Could not create empty combination progress file at '{progress_file_path_combinations}': {e}")
            debug_print(f"Error creating empty combination progress file: {e}")

    # Initialize the custom list progress file
    initialize_custom_list_progress_file()

    # 2. Register the stop hotkey
    try:
        keyboard.add_hotkey('ctrl+shift+c+v', on_stop_hotkey_pressed)
        print(f"\n[INFO] Stop hotkey 'Ctrl+Shift+C+V' registered.")
        debug_print("Hotkey registered successfully.")
    except Exception as e:
        print(f"[ERROR] Could not register hotkey. This might be due to permissions or conflicts: {e}")
        print("         You can still stop the script by moving your mouse to a corner or pressing Ctrl+C in the terminal.")
        debug_print(f"Error registering hotkey: {e}")
    
    # --- Main Application Loop (keeps the script running until explicitly quit) ---
    while True:
        # Reset STOP_SCRIPT flag before entering automation if it was set by a previous run's interruption
        if STOP_SCRIPT:
            STOP_SCRIPT = False 
            debug_print("STOP_SCRIPT flag reset to False for new main loop iteration.")

        run_automation_chosen, with_macro_clicks_chosen, mode_chosen = display_main_menu()
        debug_print(f"Main menu selection: run_automation_chosen={run_automation_chosen}, with_macro_clicks_chosen={with_macro_clicks_chosen}, mode_chosen='{mode_chosen}'.")

        if mode_chosen == 'quit': # User chose to quit ('7')
            debug_print("User chose to quit. Exiting main application loop.")
            break # Exit the main application loop, leading to final cleanup

        # Handle the different automation modes
        if mode_chosen == 'text_file':
            debug_print("Starting text file processing mode.")
            process_text_file_automation()
            continue # Go back to the main menu after processing the text file
        
        # If we reach here, it's a 'combinations' mode run
        debug_print("Starting combination generation mode.")
        pyautogui.PAUSE = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
        pyautogui.FAILSAFE = True
        debug_print(f"PyAutoGUI PAUSE set to {pyautogui.PAUSE}, FAILSAFE enabled.")
        
        # Determine the initial delay from settings
        initial_delay = settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])

        # Handle macro clicks setup if chosen for combination mode
        if with_macro_clicks_chosen:
            print("\n[INFO] Please read the instructions below carefully before proceeding.")
            print("       You will define the number of macro clicks and then capture their coordinates.")
            print("       Then, the main automation loop will begin.")
            print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
            print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
            print("       Or, press Ctrl+C in the terminal to force quit.")
            print(f"\n[INFO] Waiting {initial_delay} seconds. Use this time to prepare your target application and read the instructions.")
            debug_print(f"Waiting {initial_delay} seconds for user preparation (with macro clicks chosen).")
            time.sleep(initial_delay)

            setup_successful = get_clicks_for_setup()
            if not setup_successful:
                # User chose to go back during setup, or setup failed
                print("[INFO] Macro click setup was not completed. Returning to Main Menu.")
                debug_print("Macro click setup not successful. Returning to main menu.")
                pyautogui.PAUSE = 0 # Reset pause for menu interaction
                continue # Go back to the beginning of the while True loop (main menu)
        else: # User chose to run Combination Generator WITHOUT macro clicks
            print("\n[INFO] Running Combination Generator WITHOUT macro clicks. Click setup skipped.")
            print("\n[INFO] Please read the instructions below carefully before proceeding.")
            print("       The main automation loop will begin shortly.")
            print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
            print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
            print("       Or, press Ctrl+C in the terminal to force quit.")
            print(f"\n[INFO] Waiting {initial_delay} seconds. Use this time to prepare your target application and read the instructions.")
            debug_print(f"Waiting {initial_delay} seconds for user preparation (without macro clicks chosen).")
            time.sleep(initial_delay)


        # --- Automation Loop (for combination generation mode) ---
        print("\n--- Starting Combination Generation Automation Loop ---")
        progress_file_path_combinations = settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])
        print(f"[INFO] Starting to generate combinations. Progress will be saved to and resumed from: '{progress_file_path_combinations}'.")
        debug_print(f"Loading combination progress from '{progress_file_path_combinations}'.")
        
        start_combination = load_progress(progress_file_path_combinations)
        generator = generate_all_combinations(start_combination=start_combination)
        debug_print("Combination generator initialized.")

        delay_between_repetitions = settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])
        debug_print(f"Delay between repetitions set to {delay_between_repetitions}s.")

        try:
            for current_string in generator:
                if STOP_SCRIPT:
                    print(f"\n[INFO] Script stopped by hotkey. Saving current progress: '{current_string}'")
                    debug_print(f"STOP_SCRIPT detected. Saving progress: '{current_string}'.")
                    save_progress(progress_file_path_combinations, current_string)
                    break # Exit the automation loop
                
                type_the_string(current_string)
                
                if with_macro_clicks_chosen:
                    perform_macro_clicks()
                
                time.sleep(delay_between_repetitions) # Wait for the configured delay
                debug_print(f"Completed actions for '{current_string}'. Sleeping for {delay_between_repetitions}s.")

        except pyautogui.FailSafeException:
            print("\n[CRITICAL] PyAutoGUI Fail-Safe triggered (mouse moved to screen corner). Script aborted.")
            debug_print("PyAutoGUI Fail-Safe triggered.")
            # If the script was running combinations, save the last known string
            if 'current_string' in locals() and current_string:
                save_progress(progress_file_path_combinations, current_string)
                debug_print(f"Progress '{current_string}' saved due to Fail-Safe.")
            STOP_SCRIPT = False # Reset for next run
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred during automation: {e}")
            debug_print(f"Unexpected error during automation: {e}")
            if 'current_string' in locals() and current_string:
                save_progress(progress_file_path_combinations, current_string)
                debug_print(f"Progress '{current_string}' saved due to error.")
            STOP_SCRIPT = False # Reset for next run
        
        if not STOP_SCRIPT: # If it was a normal completion (e.g. generator exhausted, though it's infinite here) or manual break
            print("\n[INFO] Automation loop finished or manually stopped. Returning to main menu.")
            debug_print("Automation loop finished or manually stopped.")
        
        STOP_SCRIPT = False # Reset the flag for the next iteration of the main app loop
        pyautogui.PAUSE = 0 # Reset for menu interaction
        pyautogui.FAILSAFE = False # Disable failsafe while in menu
        debug_print("PyAutoGUI PAUSE reset to 0, FAILSAFE disabled (back to menu).")
    
    # Final cleanup before exiting
    print("\n[INFO] Script has quit. Goodbye!") # Removed name here
    debug_print("Script exiting.")
    sys.exit(0) # Clean exit