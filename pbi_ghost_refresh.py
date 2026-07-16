import pyautogui
import pygetwindow as gw
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def refresh_power_bi():
    try:
        # Find Power BI Desktop windows
        pbi_windows = [w for w in gw.getWindowsWithTitle('') if 'Power BI Desktop' in w.title]
        
        if not pbi_windows:
            logging.warning("Power BI Desktop is not open.")
            return

        window = pbi_windows[0]
        
        # Save the currently active window to restore it later
        active_window = gw.getActiveWindow()
        
        # Focus Power BI
        if not window.isActive:
            try:
                window.activate()
                time.sleep(0.5) # Give it a moment to gain focus
            except Exception as e:
                logging.error(f"Could not activate window: {e}")
                
        # Send Alt, then H, then R sequentially to avoid global hotkeys like NVIDIA's Alt+R
        pyautogui.press('alt')
        time.sleep(0.1)
        pyautogui.press('h')
        time.sleep(0.1)
        pyautogui.press('r')
        
        logging.info("Sent refresh command to Power BI.")
        
        # Try to restore the original window focus
        if active_window and active_window != window:
            try:
                active_window.activate()
            except:
                pass

    except Exception as e:
        logging.error(f"Error during refresh: {e}")

if __name__ == "__main__":
    logging.info("Starting UI Ghost Script for Power BI Auto-Refresh...")
    logging.info("Press Ctrl+C to stop.")
    try:
        while True:
            refresh_power_bi()
            time.sleep(5)  # Wait 5 seconds before the next refresh
    except KeyboardInterrupt:
        logging.info("Ghost script stopped.")
