import argparse
import os
import sys
from search_tracker.tracker import SearchTracker

def show_menu():
    while True:
        print("\n" + "="*50)
        print("Search Tracker - Research Tool")
        print("="*50)
        print("1. Start Tracking")
        print("2. Exit")
        print("="*50)
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            print("\nInvalid choice. Please enter 1 or 2.")
            input("Press Enter to continue...")

def main():
    parser = argparse.ArgumentParser(description='Track and analyze web search behavior')
    parser.add_argument('--data-dir', type=str, help='Directory to save tracking data (default: ./data)')
    args = parser.parse_args()

    while True:
        if not show_menu():
            print("\nThank you for using Search Tracker!")
            return 0

        print("\nStarting Search Tracker...")
        print("This tool will track your web search behavior and save the data for analysis.")
        print("Press Ctrl+C to stop tracking and save data.")
        print("\nThe following data will be collected:")
        print("- Search queries from Google")
        print("- Navigation between pages")
        print("- New tabs opened/closed")
        print("- Scroll events")
        print("- Time spent on each URL")
        print("\nData will be saved in CSV format in the specified directory.")
        
        try:
            tracker = SearchTracker(data_dir=args.data_dir)
            tracker.run()
        except KeyboardInterrupt:
            print("\nStopping tracking...")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            input("\nPress Enter to return to main menu...")
            continue
        
        print("\nTracking session completed.")
        input("Press Enter to return to main menu...")

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to exit...") 