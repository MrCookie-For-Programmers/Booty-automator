import pyautogui
import string
import time
import os
import sys
from pynput import mouse
import keyboard
import itertools

# --- Global Flags and Data ---
STOP_SCRIPT = False # Flag to signal the main loop to stop
click_coords = [None, None, None] # Stores (x, y) tuples for the 3 macro clicks
current_coord_capture_index = 0 # Helper for the setup phase
mouse_listener_active = False # Flag to control pynput listener

# --- Configuration ---
# UPDATED: CHARS now includes punctuation
CHARS = string.ascii_letters + string.digits + string.punctuation
DELAY_BETWEEN_REPETITIONS = 1 # Seconds to wait between each full cycle (after a string has been processed twice)

# --- Hotkey Callback ---
def on_stop_hotkey_pressed():
    """Callback function executed when the Ctrl+Shift+C+V hotkey is pressed."""
    global STOP_SCRIPT
    STOP_SCRIPT = True
    print("\n[INFO] Stop hotkey (Ctrl+Shift+C+V) detected. Script will terminate gracefully after current action.")
    print("[DEBUG] STOP_SCRIPT flag set to True by hotkey.")

# --- Mouse Listener Callback for Setup ---
def on_click_for_setup(x, y, button, pressed):
    """
    Callback function for pynput mouse listener during the setup phase.
    Captures 3 coordinates after an initial ignored click.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords

    if pressed: # Only act on mouse down event
        print(f"[DEBUG] Mouse click detected at ({x}, {y}) - Button: {button}, Pressed: {pressed}.")
        current_coord_capture_index += 1
        
        if current_coord_capture_index == 1:
            print(f"  First click (X: {x}, Y: {y}) received. This one is ignored. Now click for Coordinate 1...")
        elif current_coord_capture_index <= 4: # Capture coordinates 1, 2, 3 (indices 0, 1, 2 in click_coords list)
            click_coords[current_coord_capture_index - 2] = (x, y) 
            print(f"  Coordinate {current_coord_capture_index - 1} (X: {x}, Y: {y}) saved. click_coords: {click_coords}")
            if current_coord_capture_index == 4:
                print("  All coordinates captured. Exiting setup mode.")
                mouse_listener_active = False # Signal to stop the listener
                print("[DEBUG] Mouse listener set to inactive. Returning False to stop listener.")
                return False # This explicit return False stops the pynput listener

# --- Setup Phase Function ---
def get_clicks_for_setup():
    """
    Guides the user to provide 4 mouse clicks to define the three action coordinates.
    The first click is ignored as a 'warm-up' or to clear any accidental initial clicks.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords
    print("[DEBUG] Entering get_clicks_for_setup().")
    current_coord_capture_index = 0 # Reset for a new setup
    click_coords = [None, None, None] # Ensure coords are empty for new setup
    print(f"[DEBUG] Reset current_coord_capture_index to {current_coord_capture_index} and click_coords to {click_coords}.")

    print("\n--- Setup Phase: Define Click Coordinates ---")
    print("Move your mouse to the desired position and click. Follow the prompts:")
    print("1. Make the first click anywhere. (This click will be ignored.)")
    print("2. Click for the FIRST macro coordinate (Coordinate 1).")
    print("3. Click for the SECOND macro coordinate (Coordinate 2).")
    print("4. Click for the THIRD macro coordinate (Coordinate 3).")
    
    time.sleep(0.5) 
    print("[DEBUG] Paused for 0.5 seconds before starting mouse listener.")

    mouse_listener_active = True
    print("[DEBUG] Starting mouse listener.")
    with mouse.Listener(on_click=on_click_for_setup) as listener:
        listener.join() # Blocks until on_click_for_setup returns False and stops the listener

    print("\nSetup complete. All coordinates captured!")
    print("[DEBUG] Exiting get_clicks_for_setup().")

# --- Combination Generator ---
def generate_all_combinations(chars=CHARS):
    """
    Generates all string combinations lexicographically, starting from length 1.
    This generator runs indefinitely.
    """
    print(f"[DEBUG] Entering generate_all_combinations() with CHARS: '{chars}'.")
    for length in itertools.count(1): # Always start from length 1
        print(f"\n[INFO] Generating combinations for length: {length} (Total possible: {len(chars)**length})")
        print(f"[DEBUG] Starting itertools.product for length {length}.")
        for combo_tuple in itertools.product(chars, repeat=length):
            if STOP_SCRIPT:
                print("[DEBUG] STOP_SCRIPT is True. Generator returning.")
                return # Stop the generator if hotkey pressed
            current_string = ''.join(combo_tuple)
            print(f"[DEBUG] Yielding combination: '{current_string}'.")
            yield current_string
    print("[DEBUG] Generator has exhausted its possibilities (THIS SHOULD NEVER PRINT).") # This line should logically never be reached.

# --- Core Action Functions ---
def type_the_string(current_string):
    """Types the given string into the active text field and presses Enter."""
    print(f"[DEBUG] Entering type_the_string() for '{current_string}'.")
    print(f"[ACTION] Typing: '{current_string}' (Length: {len(current_string)})")
    pyautogui.write(current_string)
    pyautogui.press('enter')
    print("[ACTION] Enter pressed.")
    print(f"[DEBUG] Exiting type_the_string() for '{current_string}'.")

def perform_macro_clicks():
    """Performs the specific click combination using the globally captured coordinates."""
    print("[DEBUG] Entering perform_macro_clicks().")
    print("[ACTION] Performing macro clicks...")
    
    # Iterate through the captured click coordinates and perform clicks
    for i, coords in enumerate(click_coords):
        if coords: # Ensure coordinates were actually captured
            print(f"  Clicking at Coordinate {i+1}: {coords}")
            pyautogui.click(x=coords[0], y=coords[1])
            time.sleep(0.1) # Small delay to allow the system to register the click
        else:
            print(f"[WARNING] Macro click {i+1} coordinates not defined. Skipping.") # Should not happen if setup is done.

    print("[ACTION] Macro clicks finished.")
    print("[DEBUG] Exiting perform_macro_clicks().")


# --- Main Execution Block ---
if __name__ == "__main__":
    print("--- Python Combination Generator & Automation Script (DEBUG VERSION) ---")
    print("This script will systematically generate string combinations,")
    print("type them TWICE, and perform actions based on your menu selection.")
    print(f"Character set for combinations: '{CHARS}' (Total {len(CHARS)} characters)")
    print(f"[DEBUG] Initial STOP_SCRIPT: {STOP_SCRIPT}")
    print(f"[DEBUG] DELAY_BETWEEN_REPETITIONS: {DELAY_BETWEEN_REPETITIONS} seconds.")

    # 1. Register the stop hotkey
    print("[DEBUG] Attempting to register hotkey 'ctrl+shift+c+v'.")
    try:
        keyboard.add_hotkey('ctrl+shift+c+v', on_stop_hotkey_pressed)
        print(f"\n[INFO] Stop hotkey 'Ctrl+Shift+C+V' registered.")
    except Exception as e:
        print(f"[ERROR] Could not register hotkey. This might be due to permissions or conflicts: {e}")
        print("         You can still stop the script by moving your mouse to a corner or pressing Ctrl+C in the terminal.")
        print(f"[DEBUG] Hotkey registration failed: {e}")

    # 2. Display Main Menu and get user choice
    print("\n--- Main Menu ---")
    print("Select how you want to run the script:")
    print("1. Run WITH Macro Clicks (types string + performs 3 clicks)")
    print("2. Run WITHOUT Macro Clicks (types string ONLY)")

    choice = None
    while choice not in ['1', '2']:
        choice = input("Enter your choice (1 or 2): ").strip()
        if choice not in ['1', '2']:
            print("[ERROR] Invalid choice. Please enter '1' or '2'.")
    
    run_with_macro = (choice == '1')
    print(f"[DEBUG] User choice: '{choice}'. run_with_macro set to: {run_with_macro}.")

    # 3. Provide initial info and delay for user to read
    print("\n[INFO] Please read the instructions below carefully before proceeding.")
    if run_with_macro:
        print("       You will first define the three click coordinates by clicking on your screen.")
    else:
        print("       You have chosen to run WITHOUT macro clicks. Click setup will be skipped.")
    print("       Then, the main automation loop will begin.")
    print("\n[INFO] To STOP THE SCRIPT GRACEFULLY during the loop: Press 'Ctrl+Shift+C+V'.")
    print("       Alternatively, move your mouse to any of the four corners of your screen (pyautogui fail-safe).")
    print("       Or, press Ctrl+C in the terminal to force quit.")
    
    print("\n[INFO] Waiting 10 seconds. Use this time to prepare your target application and read the instructions.")
    print("[DEBUG] Starting 10-second initial delay.")
    time.sleep(10)
    print("[DEBUG] 10-second initial delay finished.")

    # 4. Get click coordinates from user, if 'with macro' was selected
    if run_with_macro:
        get_clicks_for_setup()
        print(f"[DEBUG] Final click_coords after setup: {click_coords}")
    else:
        print("\n[INFO] Running WITHOUT macro clicks. Click setup skipped.")
        print("[DEBUG] run_with_macro is False. get_clicks_for_setup() was skipped.")

    print("\n--- Starting Automation Loop ---")
    print("[INFO] Starting to generate combinations from length 1 (no progress is saved).")
    
    print("[DEBUG] Creating generator object.")
    generator = generate_all_combinations(chars=CHARS)
    print("[DEBUG] Generator object created.")

    try:
        # Loop through each generated string combination
        print("[DEBUG] Entering main generator loop.")
        for current_string in generator:
            print(f"\n[DEBUG] Starting processing for new string: '{current_string}'. Current STOP_SCRIPT state: {STOP_SCRIPT}")
            if STOP_SCRIPT: # Check global stop flag
                print("[INFO] Stop flag set. Exiting loop.")
                print("[DEBUG] Breaking main loop due to STOP_SCRIPT being True.")
                break 

            # Perform actions for the current string TWICE
            print(f"[DEBUG] Starting inner loop for 2 repetitions.")
            for i in range(2): # Loop twice for each string
                print(f"[DEBUG] Repetition {i+1} of 2 for string: '{current_string}'.")
                print(f"\n[ACTION] Processing string '{current_string}' - Repetition {i+1} of 2.")
                try:
                    type_the_string(current_string)
                    if run_with_macro: # ONLY perform clicks if chosen
                        perform_macro_clicks()
                    else:
                        print("[DEBUG] Macro clicks skipped as 'run_with_macro' is False.")
                except pyautogui.FailSafeException:
                    print("\n[CRITICAL ERROR] pyautogui Fail-safe triggered during action. Exiting script.")
                    STOP_SCRIPT = True # Set flag to ensure full script exit
                    print("[DEBUG] FailSafeException caught. STOP_SCRIPT set to True. Breaking inner loop.")
                    break # Break the inner loop (for 2 repetitions)
                except Exception as e:
                    print(f"[ERROR] An unexpected error occurred during action for string '{current_string}' (repetition {i+1}): {e}.")
                    print("        Skipping this repetition and attempting to continue to the next.")
                    print(f"[DEBUG] General exception caught: {e}. Attempting to continue.")
            
            if STOP_SCRIPT: # Check again after inner loop, in case fail-safe or error broke inner loop
                print("[DEBUG] STOP_SCRIPT is True after inner loop. Breaking main loop.")
                break # Break the outer loop (generator loop)

            print(f"[INFO] Waiting {DELAY_BETWEEN_REPETITIONS} second before next combination...")
            print(f"[DEBUG] Pausing for {DELAY_BETWEEN_REPETITIONS} second.")
            time.sleep(DELAY_BETWEEN_REPETITIONS)
            print(f"[DEBUG] Pause finished. Continuing to next combination.")

        else: # This 'else' block executes if the 'for current_string in generator' loop finishes WITHOUT a 'break'
            print("[DEBUG] Main loop finished because generator exhausted. THIS SHOULD NOT HAPPEN IN THIS SCRIPT.")
            print("        This indicates a problem with the generator not producing an infinite sequence.")

    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C detected. Script terminated by user.")
        print("[DEBUG] KeyboardInterrupt exception caught.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] A critical error occurred in the main loop: {e}")
        print(f"[DEBUG] Critical error caught in main loop: {e}.")
    finally:
        print("\n--- Script Finished ---")
        print("[DEBUG] Finally block executed.")
        keyboard.unhook_all()
        print("[DEBUG] Keyboard hotkeys unhooked.")
        input("Press Enter to exit...") # This will pause the script before closing the window
        print("[DEBUG] User pressed Enter. Exiting script.")
        sys.exit(0)