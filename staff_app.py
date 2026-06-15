from models import Reservation, Event, Standard
from tables import Table, TableManager
from datetime import datetime
from staff_choice_funcs import (
    floor_plan,
    area_management_helper,
    table_management_helper,
    view_reservations_helper,
    manage_reservation_helper,
    process_enquiry_helper,
)
from format_helper import get_valid_datetime, get_number_input
from colours import RED, RESET, BOLD


"""
New stuff to work on:
- Can't uncancel a booking. can also assign a table to cancelled booking
- seperate reservatoings from events
- reshuffle interface and seperate functions from inputs to make it easier to develop to front end
"""


def run_staff_system():
    """
    Main loop for the Staff Administration Panel.
    Handles restaurant configuration and reservation management.
    """
    manager = TableManager()
    success, msg = manager.load_data()
    print(f">> System Message: {msg}")

    while True:
        print("\n" + "=" * 30)
        print(" STAFF ADMINISTRATION PANEL ")
        print("=" * 30)
        print("1. View Floor Plan")
        print("2. Area Management")
        print("3. Table Management")
        print("4. View Reservations")
        print("5. Manage Reservation")
        print("6. Process Event Enquiry")
        print("7. Cancel Reservation")
        print("8. Exit & Save")

        choice = get_number_input("\nSelect (1-8): ")

        # --- VIEWING LOGIC ---
        if choice == 1:
            floor_plan(manager)

        # --- AREA MANAGEMENT ---
        elif choice == 2:
            area_management_helper(manager)

        # --- TABLE MANAGEMENT ---
        elif choice == 3:
            table_management_helper(manager)

        # --- 4. VIEW RESERVATIONS ---
        elif choice == 4:
            view_reservations_helper(manager)

        # --- 5. MANAGE RESERVATIONS ---
        elif choice == 5:
            manage_reservation_helper(manager)

        # --- 6. PROCESS EVENTS ---
        elif choice == 6:
            process_enquiry_helper(manager)

        # --- 7. CANCEL RESERVATIONS ---
        elif choice == 7:
            print("\n--- CANCEL STANDARD RESERVATION ---")
            res_id = input("Enter Reservation ID: ").strip().upper()
            res = next(
                (r for r in Reservation._all_reservations if r.get_id() == res_id), None
            )

            if res and isinstance(res, Standard):
                if (
                    input(f"Cancel booking for {res.get_name()}? (y/n): ").lower()
                    == "y"
                ):
                    print(res.cancel_booking())  # This frees the table in models.py
                    manager.save_data()
                else:
                    print(">> Cancellation aborted.")
            elif res and isinstance(res, Event):
                print(">> Error: Events must be managed through Option 6.")
            else:
                print(">> Error: ID not found.")
            input("\nPress Enter to return to menu...")

        # --- SYSTEM EXIT ---
        elif choice == 8:
            print("\n" + "." * 30)
            print("Shutting down system...")
            try:
                msg = manager.save_data()
                print(f">> {msg}")
                print("All changes are saved!")
            except Exception as e:
                print(f">> CRITICAL ERROR: Could not save data. {e}")
            print("." * 30)
            break


if __name__ == "__main__":
    run_staff_system()
