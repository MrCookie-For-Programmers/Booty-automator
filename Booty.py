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
CHARS = string.ascii_letters + string.digits + string.punctuation 
DELAY_BETWEEN_REPETITIONS = 1 # Seconds to wait between each full cycle (after a string has been processed)

# --- Hotkey Callback ---
def on_stop_hotkey_pressed():
    """Callback function executed when the Ctrl+Shift+C+V hotkey is pressed."""
    global STOP_SCRIPT
    STOP_SCRIPT = True
    print("\n[INFO] Stop hotkey (Ctrl+Shift+C+V) detected. Script will terminate gracefully after current action.")

# --- Mouse Listener Callback for Setup ---
def on_click_for_setup(x, y, button, pressed):
    """
    Callback function for pynput mouse listener during the setup phase.
    Captures 3 coordinates after an initial ignored click.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords

    if pressed: # Only act on mouse down event
        current_coord_capture_index += 1
        
        if current_coord_capture_index == 1:
            print(f"  First click (X: {x}, Y: {y}) received. This one is ignored. Now click for Coordinate 1...")
        elif current_coord_capture_index <= 4: # Capture coordinates 1, 2, 3 (indices 0, 1, 2 in click_coords list)
            click_coords[current_coord_capture_index - 2] = (x, y) 
            print(f"  Coordinate {current_coord_capture_index - 1} (X: {x}, Y: {y}) saved.")
            if current_coord_capture_index == 4:
                print("  All coordinates captured. Exiting setup mode.")
                mouse_listener_active = False # Signal to stop the listener
                return False # This explicit return False stops the pynput listener

# --- Setup Phase Function ---
def get_clicks_for_setup():
    """
    Guides the user to provide 4 mouse clicks to define the three action coordinates.
    The first click is ignored as a 'warm-up' or to clear any accidental initial clicks.
    """
    global current_coord_capture_index, mouse_listener_active, click_coords
    current_coord_capture_index = 0 # Reset for a new setup
    click_coords = [None, None, None] # Ensure coords are empty for new setup

    print("\n--- Setup Phase: Define Click Coordinates ---")
    print("Move your mouse to the desired position and click. Follow the prompts:")
    print("1. Make the first click anywhere. (This click will be ignored.)")
    print("2. Click for the FIRST macro coordinate (Coordinate 1).")
    print("3. Click for the SECOND macro coordinate (Coordinate 2).")
    print("4. Click for the THIRD macro coordinate (Coordinate 3).")
    
    # Give a brief moment for the user to read the prompts before listening
    time.sleep(0.5) 

    mouse_listener_active = True
    with mouse.Listener(on_click=on_click_for_setup) as listener:
        listener.join() # Blocks until on_click_for_setup returns False and stops the listener

    print("\nSetup complete. All coordinates captured!")

# --- Combination Generator ---
def generate_all_combinations(chars=CHARS):
    """
    Generates all string combinations lexicographically, starting from length 1.
    This generator runs indefinitely.
    """
    for length in itertools.count(1): # Always start from length 1
        print(f"\n[INFO] Generating combinations for length: {length} (Total possible: {len(chars)**length})")
        for combo_tuple in itertools.product(chars, repeat=length):
            if STOP_SCRIPT:
                return # Stop the generator if hotkey pressed
            yield ''.join(combo_tuple)

# --- Core Action Functions ---
def type_the_string(current_string):
    """Types the given string into the active text field and presses Enter."""
    print(f"[ACTION] Typing: '{current_string}' (Length: {len(current_string)})")
    pyautogui.write(current_string)
    pyautogui.press('enter')
    print("[ACTION] Enter pressed.")

def perform_macro_clicks():
    """Performs the specific click combination using the globally captured coordinates."""
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


# --- Main Execution Block ---
if __name__ == "__main__":
    print("--- Python Combination Generator & Automation Script ---")
    print("This script will systematically generate string combinations,")
    print("type them once, and perform actions based on your menu selection.") # Updated description
    print(f"Character set for combinations: '{CHARS}' (Total {len(CHARS)} characters)")

    # 1. Register the stop hotkey
    try:
        keyboard.add_hotkey('ctrl+shift+c+v', on_stop_hotkey_pressed)
        print(f"\n[INFO] Stop hotkey 'Ctrl+Shift+C+V' registered.")
    except Exception as e:
        print(f"[ERROR] Could not register hotkey. This might be due to permissions or conflicts: {e}")
        print("         You can still stop the script by moving your mouse to a corner or pressing Ctrl+C in the terminal.")

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
    time.sleep(10)

    # 4. Get click coordinates from user, if 'with macro' was selected
    if run_with_macro:
        get_clicks_for_setup()
    else:
        print("\n[INFO] Running WITHOUT macro clicks. Click setup skipped.")

    print("\n--- Starting Automation Loop ---")
    print("[INFO] Starting to generate combinations from length 1 (no progress is saved).")
    
    generator = generate_all_combinations(chars=CHARS)

    try:
        # Loop through each generated string combination
        for current_string in generator:
            if STOP_SCRIPT: # Check global stop flag
                print("[INFO] Stop flag set. Exiting loop.")
                break 

            # Perform actions for the current string ONCE
            print(f"\n[ACTION] Processing string: '{current_string}'") # Updated print
            try:
                type_the_string(current_string)
                if run_with_macro: # ONLY perform clicks if chosen
                    perform_macro_clicks()
            except pyautogui.FailSafeException:
                print("\n[CRITICAL ERROR] pyautogui Fail-safe triggered during action. Exiting script.")
                STOP_SCRIPT = True # Set flag to ensure full script exit
                break # Break the main loop
            except Exception as e:
                print(f"[ERROR] An unexpected error occurred during action for string '{current_string}': {e}.") # Updated print
                print("        Attempting to continue to the next combination.")
            
            if STOP_SCRIPT: # Check again in case fail-safe or error broke before sleep
                break

            print(f"[INFO] Waiting {DELAY_BETWEEN_REPETITIONS} second before next combination...")
            time.sleep(DELAY_BETWEEN_REPETITIONS)

    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C detected. Script terminated by user.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] A critical error occurred in the main loop: {e}")
    finally:
        print("\n--- Script Finished ---")
        keyboard.unhook_all()
        input("Press Enter to exit...") # This will pause the script before closing the window
        sys.exit(0)