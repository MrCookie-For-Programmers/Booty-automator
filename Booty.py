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

# These are global for setup, but their effective values depend on user input in get_clicks_for_setup
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
    'delay_between_macro_clicks': 0.01, # Seconds to wait between individual macro clicks
    'pyautogui_write_interval': 0.0, # Seconds to wait between each character typed by pyautogui.write
    'initial_delay_before_automation': 10.0, # Seconds to wait before the automation loop starts
    'progress_file_path': 'progress.txt', # Default path for the progress file (relative to script execution)
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

# --- Settings File Functions ---
def load_settings(file_path):
    """
    Loads settings from the specified JSON file.
    Merges with DEFAULT_SETTINGS to ensure all keys are present.
    """
    global settings
    loaded_settings = {}
    if os.path.exists(file_path):
        if os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r') as f:
                    loaded_settings = json.load(f)
                print(f"[INFO] Settings loaded from '{file_path}'.")
            except json.JSONDecodeError as e:
                print(f"[WARNING] Settings file '{file_path}' is corrupted or invalid JSON ({e}). Using default settings.")
            except Exception as e:
                print(f"[WARNING] Could not read settings file '{file_path}': {e}. Using default settings.")
        else:
            print(f"[INFO] Settings file '{file_path}' is empty. Using default settings.")
    else:
        print(f"[INFO] Settings file '{file_path}' not found. Using default settings.")

    # Merge loaded settings with defaults to ensure all keys are present
    current_settings = DEFAULT_SETTINGS.copy()
    current_settings.update(loaded_settings)
    
    # Ensure chars is string, as JSON might mess with it if not handled properly
    if not isinstance(current_settings.get('chars'), str):
        print("[WARNING] 'chars' setting invalid. Resetting to default character set.")
        current_settings['chars'] = DEFAULT_SETTINGS['chars']

    settings = current_settings
    return settings

def save_settings(file_path, settings_data):
    """Saves the current settings to the specified JSON file."""
    try:
        # Ensure the directory for the settings file exists
        settings_dir = os.path.dirname(file_path)
        if settings_dir and not os.path.exists(settings_dir):
            os.makedirs(settings_dir, exist_ok=True)
            print(f"[INFO] Created directory for settings: '{settings_dir}'")

        with open(file_path, 'w') as f:
            json.dump(settings_data, f, indent=4)
        print(f"[INFO] Settings saved to '{file_path}'.")
    except Exception as e:
        print(f"[ERROR] Could not save settings to '{file_path}': {e}")


# --- Progress File Functions ---
def load_progress(file_path):
    """
    Loads the last saved combination from the progress file.
    Returns None if file doesn't exist, is empty, or has invalid content.
    """
    if not os.path.exists(file_path):
        print(f"[INFO] Progress file '{file_path}' not found. Starting from 'a'.")
        return None # No previous progress
    
    if os.path.getsize(file_path) == 0:
        print(f"[INFO] Progress file '{file_path}' is empty. Starting from 'a'.")
        return None

    try:
        with open(file_path, 'r') as f:
            last_progress = f.readline().strip()
            if not last_progress:
                print(f"[INFO] Progress file '{file_path}' is empty after read. Starting from 'a'.")
                return None
            
            # Basic validation: ensure all chars in last_progress are in CHARS set
            configured_chars = settings.get('chars', DEFAULT_SETTINGS['chars'])
            if not all(char in configured_chars for char in last_progress):
                print(f"[ERROR] Invalid characters found in progress file: '{last_progress}'. Starting from 'a'.")
                return None

            print(f"[INFO] Resuming from last saved progress: '{last_progress}'")
            return last_progress
    except Exception as e:
        print(f"[ERROR] Could not read progress file '{file_path}': {e}. Starting from 'a'.")
        return None

def save_progress(file_path, current_string):
    """Saves the current combination to the progress file, overwriting previous content."""
    try:
        # Ensure the directory for the progress file exists
        progress_dir = os.path.dirname(file_path)
        if progress_dir and not os.path.exists(progress_dir):
            os.makedirs(progress_dir, exist_ok=True)
            print(f"[INFO] Created directory for progress file: '{progress_dir}'")

        with open(file_path, 'w') as f: # Overwrite mode 'w'
            f.write(current_string + '\n')
    except Exception as e:
        print(f"[ERROR] Could not save progress to '{file_path}': {e}")

def reset_progress(file_path):
    """Resets the progress by deleting the progress file or clearing its content."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] Progress file '{file_path}' deleted. Progress reset.")
        except OSError as e:
            print(f"[ERROR] Could not delete progress file '{file_path}': {e}. Please delete it manually if needed.")
    else:
        print(f"[INFO] Progress file '{file_path}' does not exist. No reset needed.")
    input("Press Enter to continue...") # Pause for user to read

# --- Mouse Listener Callback for Setup ---
def on_click_for_setup(x, y, button, pressed):
    """
    Callback function for pynput mouse listener during the setup phase.
    Captures the specified number of coordinates after ignoring initial clicks.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords, num_macro_clicks, num_ignored_clicks_setup

    if pressed: # Only act on mouse down event
        current_coord_capture_index += 1

        # If we are still in the 'ignored clicks' phase
        if current_coord_capture_index <= num_ignored_clicks_setup:
            print(f"  Click {current_coord_capture_index} received. This click is ignored ({num_ignored_clicks_setup - current_coord_capture_index + 1} more ignored clicks).")
        else:
            # Calculate the 0-indexed position in the click_coords list
            macro_click_list_index = current_coord_capture_index - num_ignored_clicks_setup - 1

            if macro_click_list_index >= 0 and macro_click_list_index < num_macro_clicks:
                click_coords[macro_click_list_index] = (x, y)
                print(f"  Coordinate {macro_click_list_index + 1} (X: {x}, Y: {y}) saved.")

            # Check if all required macro clicks have been captured
            if (macro_click_list_index + 1) == num_macro_clicks:
                print("  All required coordinates captured. Exiting setup mode.")
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
    while True:
        try:
            num_str = input("How many macro clicks do you want to perform? (Enter 0 to go back to Main Menu): ").strip()
            if num_str == '0':
                print("[INFO] Returning to Main Menu.")
                return False # Indicate user cancelled
            
            num = int(num_str)
            if num < 0:
                print("[ERROR] Number of clicks must be a non-negative integer.")
                continue
            num_macro_clicks = num
            break
        except ValueError:
            print("[ERROR] Please enter a valid number or 0.")

    if num_macro_clicks == 0:
        print("[INFO] 0 macro clicks selected. Skipping coordinate capture.")
        return True # Treat as successful setup, just no clicks to perform

    while True:
        try:
            num = int(input("How many initial clicks should be ignored during coordinate capture? (e.g., 1 for a warm-up click): ").strip())
            if num < 0:
                print("[ERROR] Number of ignored clicks cannot be negative.")
                continue
            num_ignored_clicks_setup = num
            break
        except ValueError:
            print("[ERROR] Please enter a valid number.")

    # Dynamically size the click_coords list based on user input
    click_coords.clear() # Clear any previous clicks
    click_coords.extend([None] * num_macro_clicks)
    current_coord_capture_index = 0 # Reset total clicks seen for new setup

    print("\n--- Start Capturing Coordinates ---")
    if num_ignored_clicks_setup > 0:
        print(f"Make your first {num_ignored_clicks_setup} clicks anywhere on screen. These will be ignored.")
    print(f"Then, click on the exact {num_macro_clicks} positions where you want the script to click.")
    print(f"Total clicks expected: {num_ignored_clicks_setup + num_macro_clicks}")
    
    time.sleep(0.5) 

    mouse_listener_active = True
    with mouse.Listener(on_click=on_click_for_setup) as listener:
        listener.join() # Blocks until on_click_for_setup returns False and stops the listener

    # Final check if all clicks were indeed captured
    if None in click_coords:
        print("[WARNING] Not all desired macro coordinates were captured during setup. Macro clicks may be incomplete.")
        return True # Still return True, so the script runs but with incomplete clicks
    else:
        print("\nSetup complete. All required coordinates captured!")
        return True

# --- Combination Generator ---
def generate_all_combinations(start_combination=None):
    """
    Generates all string combinations lexicographically, starting from length 1.
    If start_combination is provided, it resumes from that point.
    This generator runs indefinitely.
    """
    chars_set = settings.get('chars', DEFAULT_SETTINGS['chars']) # Use configured chars
    
    # Flag to indicate if we have reached or passed the start_combination
    started_yielding = False

    if start_combination:
        start_length = len(start_combination)
        print(f"[INFO] Attempting to resume from '{start_combination}'...")
        
        # Iterate up to the starting length to find the start_combination
        for length_iter in itertools.count(1):
            if STOP_SCRIPT: 
                return
            
            if length_iter < start_length: # Skip lengths shorter than the start_combination's length
                continue # Move to the next length

            for combo_tuple in itertools.product(chars_set, repeat=length_iter):
                if STOP_SCRIPT: 
                    return
                current_combo_str = ''.join(combo_tuple)

                # If we are at the start_combination, start yielding from here
                if current_combo_str == start_combination:
                    print(f"[INFO] Found resume point: '{start_combination}'. Resuming generation from next combination.")
                    started_yielding = True
                    break # Break inner loop (combinations for this length)

            if started_yielding:
                break # Break outer loop (lengths)
            
            if length_iter >= start_length and not started_yielding:
                print(f"[WARNING] Resume point '{start_combination}' was not found in generated sequence (it might be invalid or deleted from character set). Starting from 'a'.")
                start_combination = None # Reset to start from the beginning
                started_yielding = True # Force yielding from now on, starting with 'a'
                break # Break here to start main generation loop from length 1

        if not started_yielding: # This case is if start_combination was provided but somehow not found (e.g., too long)
             print(f"[WARNING] Resume point '{start_combination}' was not found (too long or invalid). Starting from 'a'.")
             start_combination = None
             started_yielding = True # Force yielding from now on, starting with 'a'


    # Main generation loop (either from beginning or after resuming)
    actual_start_length_for_gen = 1
    if start_combination and started_yielding and len(start_combination) > 0:
        actual_start_length_for_gen = len(start_combination)


    for length in itertools.count(actual_start_length_for_gen):
        if STOP_SCRIPT: 
            return
        print(f"\n[INFO] Generating combinations for length: {length} (Total possible: {len(chars_set)**length})")
        
        skip_to_start_combo = False
        # If we just finished searching for a resume point and it was *not* found, and length matches, we are now at the start of the next combo
        if start_combination and length == len(start_combination) and not started_yielding:
            skip_to_start_combo = True
            
        for combo_tuple in itertools.product(chars_set, repeat=length):
            if STOP_SCRIPT: 
                return
            current_combo_str = ''.join(combo_tuple)
            
            if skip_to_start_combo:
                if current_combo_str == start_combination:
                    skip_to_start_combo = False # Found it, stop skipping
                    started_yielding = True # Ensure this flag is set for subsequent iterations
                continue # Keep skipping until we find the start_combination
            
            if started_yielding or start_combination is None: # Only yield if we've passed the resume point or no resume point was set
                yield current_combo_str

# --- Core Action Functions ---
def type_the_string(current_string):
    """Types the given string into the active text field and presses Enter."""
    write_interval = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
    print(f"[ACTION] Typing: '{current_string}' (Length: {len(current_string)})")
    pyautogui.write(current_string, interval=write_interval)
    pyautogui.press('enter')
    print(f"[ACTION] Enter pressed.")

def perform_macro_clicks():
    """Performs the specific click combination using the globally captured coordinates."""
    macro_delay = settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])
    print("[ACTION] Performing macro clicks...")
    
    if not click_coords or all(c is None for c in click_coords):
        print("[WARNING] No macro click coordinates defined or captured. Skipping clicks.")
        return

    # Iterate through the captured click coordinates and perform clicks
    for i, coords in enumerate(click_coords):
        if coords: # Ensure coordinates were actually captured for this slot
            print(f"  Clicking at Coordinate {i+1}: {coords}")
            pyautogui.click(x=coords[0], y=coords[1])
            time.sleep(macro_delay) # Use the configured delay
        else:
            print(f"[WARNING] Macro click {i+1} coordinates not defined during setup. Skipping this click.")

    print("[ACTION] Macro clicks finished.")

# --- Menu Functions ---
def display_main_menu():
    """Displays the main menu and handles user selection.
    Returns (should_run_automation: bool, run_with_macro: bool).
    """
    while True:
        print("\n--- Main Menu ---")
        print("1. Run WITH Macro Clicks (types string + performs user-defined clicks)")
        print("2. Run WITHOUT Macro Clicks (types string ONLY)")
        print("3. Access Settings")
        print("4. Reset Progress (starts from 'a')")
        print("Q. Quit Script")

        choice = input("Enter your choice: ").strip().lower()

        if choice == '1':
            return True, True # Run with macro clicks
        elif choice == '2':
            return True, False # Run without macro clicks
        elif choice == '3':
            display_settings_menu() # Go to settings
        elif choice == '4':
            confirm = input("Are you sure you want to reset progress? This cannot be undone. (y/n): ").strip().lower()
            if confirm == 'y':
                reset_progress(settings['progress_file_path'])
            else:
                print("[INFO] Progress reset cancelled.")
        elif choice == 'q':
            return False, False # Quit script
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4, or Q.")

def display_settings_menu():
    """Displays the settings menu and handles user selection."""
    global settings
    while True:
        print("\n--- Settings Menu ---")
        print(f"Current Settings File: {settings.get('settings_file_path', DEFAULT_SETTINGS_FILE)}")
        print(f"Current Progress File: {settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])}")
        print(f"Delay Between Repetitions: {settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])}s")
        print(f"Delay Between Macro Clicks: {settings.get('delay_between_macro_clicks', DEFAULT_SETTINGS['delay_between_macro_clicks'])}s")
        print(f"PyAutoGUI Write Interval: {settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])}s")
        print(f"Initial Delay Before Automation: {settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])}s")
        print(f"Character Set: '{settings.get('chars', DEFAULT_SETTINGS['chars'])}'")
        print("\n1. Change File Paths")
        print("2. Change Intervals")
        print("3. Change Character Set")
        print("B. Back to Main Menu")

        choice = input("Enter your choice: ").strip().lower()

        if choice == '1':
            display_file_paths_menu()
        elif choice == '2':
            display_intervals_menu()
        elif choice == '3':
            change_character_set()
        elif choice == 'b':
            break # Exit settings menu
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, 3, or B.")

def display_file_paths_menu():
    """Allows changing settings and progress file paths."""
    global settings
    while True:
        print("\n--- File Paths Settings ---")
        print(f"1. Current Settings File Path: {settings.get('settings_file_path', DEFAULT_SETTINGS_FILE)}")
        print(f"2. Current Progress File Path: {settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])}")
        print("B. Back to Settings Menu")

        choice = input("Enter your choice (1, 2, or B): ").strip().lower()

        if choice == '1':
            new_path = input(f"Enter new settings file path (current: {settings['settings_file_path']}): ").strip()
            if new_path:
                settings['settings_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings)
                print(f"[INFO] Settings file path updated to '{new_path}'. (Changes effective next script run)")
            else:
                print("[INFO] Path not changed.")
        elif choice == '2':
            new_path = input(f"Enter new progress file path (current: {settings['progress_file_path']}): ").strip()
            if new_path:
                settings['progress_file_path'] = new_path
                save_settings(settings['settings_file_path'], settings) # Save updated progress path to settings file
                print(f"[INFO] Progress file path updated to '{new_path}'.")
            else:
                print("[INFO] Path not changed.")
        elif choice == 'b':
            break
        else:
            print("[ERROR] Invalid choice. Please enter 1, 2, or B.")

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

        try:
            if choice == '1':
                new_delay = float(input("Enter new delay between repetitions (seconds): ").strip())
                if new_delay >= 0:
                    settings['delay_between_repetitions'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Delay cannot be negative.")
            elif choice == '2':
                new_delay = float(input("Enter new delay between macro clicks (seconds): ").strip())
                if new_delay >= 0:
                    settings['delay_between_macro_clicks'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Delay cannot be negative.")
            elif choice == '3':
                new_delay = float(input("Enter new PyAutoGUI write interval (seconds): ").strip())
                if new_delay >= 0:
                    settings['pyautogui_write_interval'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Interval cannot be negative.")
            elif choice == '4':
                new_delay = float(input("Enter new initial delay before automation starts (seconds): ").strip())
                if new_delay >= 0:
                    settings['initial_delay_before_automation'] = new_delay
                    save_settings(settings['settings_file_path'], settings)
                else:
                    print("[ERROR] Delay cannot be negative.")
            elif choice == 'b':
                break
            else:
                print("[ERROR] Invalid choice. Please enter 1, 2, 3, 4, or B.")
        except ValueError:
            print("[ERROR] Invalid input. Please enter a number.")

def change_character_set():
    """Allows changing the character set for combination generation."""
    global settings
    print("\n--- Change Character Set ---")
    print(f"Current Character Set: '{settings.get('chars', DEFAULT_SETTINGS['chars'])}'")
    print("Default Characters: " + string.ascii_letters + string.digits + string.punctuation)
    print("You can enter any string of characters you want to use.")
    print("Example: 'abc' for only lowercase a, b, c.")
    new_chars = input("Enter new character set (or leave empty to keep current): ").strip()
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
    load_settings(settings_file_chosen) # Load settings (or defaults if file invalid/missing)
    # Ensure the settings file path itself is correctly stored in settings for future saves
    settings['settings_file_path'] = settings_file_chosen
    save_settings(settings['settings_file_path'], settings) # Save defaults if new file was created or existing updated

    # 2. Register the stop hotkey
    try:
        keyboard.add_hotkey('ctrl+shift+c+v', on_stop_hotkey_pressed)
        print(f"\n[INFO] Stop hotkey 'Ctrl+Shift+C+V' registered.")
    except Exception as e:
        print(f"[ERROR] Could not register hotkey. This might be due to permissions or conflicts: {e}")
        print("         You can still stop the script by moving your mouse to a corner or pressing Ctrl+C in the terminal.")
    
    # --- Main Application Loop (keeps the script running until explicitly quit) ---
    while True:
        # Reset STOP_SCRIPT flag before entering automation if it was set by a previous run's interruption
        if STOP_SCRIPT:
            STOP_SCRIPT = False 

        run_automation_chosen, with_macro_clicks_chosen = display_main_menu()

        if not run_automation_chosen: # User chose to quit ('Q')
            break # Exit the main application loop, leading to final cleanup

        # User chose to run automation (either with or without macro clicks)
        pyautogui.PAUSE = settings.get('pyautogui_write_interval', DEFAULT_SETTINGS['pyautogui_write_interval'])
        pyautogui.FAILSAFE = True
        
        # Determine the initial delay from settings
        initial_delay = settings.get('initial_delay_before_automation', DEFAULT_SETTINGS['initial_delay_before_automation'])

        # Handle macro clicks setup if chosen
        if with_macro_clicks_chosen:
            print("\n[INFO] Please read the instructions below carefully before proceeding.")
            print("       You will define the number of macro clicks and then capture their coordinates.")
            print("       Then, the main automation loop will begin.")
            print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
            print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
            print("       Or, press Ctrl+C in the terminal to force quit.")
            print(f"\n[INFO] Waiting {initial_delay} seconds. Use this time to prepare your target application and read the instructions.")
            time.sleep(initial_delay)

            setup_successful = get_clicks_for_setup()
            if not setup_successful:
                # User chose to go back during setup, or setup failed
                print("[INFO] Macro click setup was not completed. Returning to Main Menu.")
                pyautogui.PAUSE = 0 # Reset pause for menu interaction
                continue # Go back to the beginning of the while True loop (main menu)
        else: # User chose to run WITHOUT macro clicks
            print("\n[INFO] Running WITHOUT macro clicks. Click setup skipped.")
            print("\n[INFO] Please read the instructions below carefully before proceeding.")
            print("       The main automation loop will begin shortly.")
            print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
            print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
            print("       Or, press Ctrl+C in the terminal to force quit.")
            print(f"\n[INFO] Waiting {initial_delay} seconds. Use this time to prepare your target application and read the instructions.")
            time.sleep(initial_delay)


        # --- Automation Loop (this block only executes if setup was successful or no macro clicks chosen) ---
        print("\n--- Starting Automation Loop ---")
        progress_file_path = settings.get('progress_file_path', DEFAULT_SETTINGS['progress_file_path'])
        print(f"[INFO] Starting to generate combinations. Progress will be saved to and resumed from: '{progress_file_path}'.")
        
        start_combination = load_progress(progress_file_path)
        generator = generate_all_combinations(start_combination=start_combination)

        try:
            for current_string in generator:
                if STOP_SCRIPT: # Hotkey detected
                    print("[INFO] Stop flag set (hotkey triggered). Exiting automation loop to Main Menu.")
                    break # Break the for loop, control goes to finally then back to main while loop

                print(f"\n[ACTION] Processing string: '{current_string}'")
                try:
                    type_the_string(current_string)
                    if with_macro_clicks_chosen: # Only perform clicks if chosen
                        perform_macro_clicks()
                except pyautogui.FailSafeException:
                    print("\n[CRITICAL ERROR] pyautogui Fail-safe triggered during action. Returning to Main Menu.")
                    STOP_SCRIPT = True  # Set STOP_SCRIPT to ensure clean break
                    break # Break the for loop
                except Exception as e:
                    print(f"[ERROR] An unexpected error occurred during action for string '{current_string}': {e}.")
                    print("         Attempting to continue to the next combination.")
                
                if STOP_SCRIPT: # Check again in case an error occurred right before sleep or another hotkey press
                    break

                save_progress(progress_file_path, current_string)
                print(f"[INFO] Progress saved: '{current_string}'")

                delay = settings.get('delay_between_repetitions', DEFAULT_SETTINGS['delay_between_repetitions'])
                print(f"[INFO] Waiting {delay} second before next combination...")
                time.sleep(delay)

            else: # This 'else' block executes if the 'for current_string in generator' loop finishes WITHOUT a 'break'
                print("[INFO] Automation loop finished unexpectedly (generator exhausted). This shouldn't happen.")

        except KeyboardInterrupt:
            print("\n[INFO] Ctrl+C detected. Returning to Main Menu.")
            STOP_SCRIPT = True  
            pass # The outer loop will handle returning to main menu.
        except Exception as e:
            print(f"\n[CRITICAL ERROR] A critical error occurred in the main automation loop: {e}. Returning to Main Menu.")
            STOP_SCRIPT = True
            pass
        finally:
            print("\n--- Automation Loop Ended ---")
            pyautogui.PAUSE = 0 # Reset pause for menu interaction
            # Control naturally goes back to the outer `while True` loop after this `try...except...finally` block
            # which will then display the main menu again.

# --- Final cleanup and actual script exit (only happens if user chose 'Q' from main menu) ---
print("\n--- Script Exiting ---")
keyboard.unhook_all()
input("Press Enter to exit...")
sys.exit(0)
