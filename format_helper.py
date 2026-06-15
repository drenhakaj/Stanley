from word2number import w2n
from datetime import datetime
from config import OPENING_TIME, CLOSING_TIME


def get_number_input(prompt):
    """
    Converts user input string into an integer.
    Supports both digits ('10') and words ('ten').
    """
    user_input = input(prompt).strip().lower()
    try:
        return int(user_input)
    except ValueError:
        try:
            return w2n.word_to_num(user_input)
        except ValueError:
            return None


def get_valid_datetime():
    """
    Step-by-step date collection to ensure user-friendly input.
    Returns a formatted string 'YYYY-MM-DD HH:MM' for the models.
    """
    while True:
        print("\n--- ENTER BOOKING DATE ---")
        year = get_number_input("Year (e.g., 2026): ")
        month = get_number_input("Month (1-12): ")
        day = get_number_input("Day (1-31): ")

        print("\n--- ENTER BOOKING TIME ---")
        hour = get_number_input(f"Hour ({OPENING_TIME}-{CLOSING_TIME}): ")
        minute = get_number_input("Minute: ")

        # 1. Check for invalid non-numeric input
        if None in [year, month, day, hour, minute]:
            print(
                ">> Error: One or more inputs were not valid numbers. Please try again."
            )
            continue

        try:
            user_dt = datetime(year, month, day, hour, minute)

            # 2. Past Date Check
            if user_dt < datetime.now():
                print(">> Error: We cannot accept bookings for the past.")
                continue

            # 3. Opening Hours Check
            if user_dt.hour < OPENING_TIME or user_dt.hour >= CLOSING_TIME:
                print(
                    f">> Error: We are only open from {OPENING_TIME}:00 to {CLOSING_TIME}:00."
                )
                continue

            # 4. Final Verification
            print(f"\nYou selected: {user_dt.strftime('%A, %B %d %Y at %H:%M')}")
            confirm = input("Is this correct? (y/n): ").lower()
            if confirm == "y":
                return user_dt  # Return the object to the app

        except ValueError as e:
            print(f">> Error: {e}. (Example: April only has 30 days).")
