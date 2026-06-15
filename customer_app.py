from tables import TableManager
from models import Standard, Event, Reservation
from format_helper import get_valid_datetime, get_number_input
from datetime import datetime


def run_customer_app():
    manager = TableManager()
    manager.load_data()

    print("\n" + "=" * 45)
    print("      WELCOME TO THE RESTAURANT PORTAL      ")
    print("=" * 45)
    print("1. Book a Table (Standard Dining)")
    print("2. Enquire for an Event (Special Occasions)")
    print("3. Exit")

    choice = input("\nSelect an option (1-3): ")

    if choice == "3":
        print("Goodbye!")
        return

    # User Details
    first_name = input("\nEnter First Name: ").strip()
    last_name = input("Enter Last Name: ").strip()
    phone = input("Enter Phone Number: ").strip()

    # --- COMBINE VARIABLES HERE ---
    full_name = f"{first_name} {last_name}"

    user_dt = get_valid_datetime()
    date_str = user_dt.strftime("%Y-%m-%d %H:%M")
    party_size = get_number_input("How many guests in total? ")

    if party_size is None or party_size <= 0:
        print(">> Error: Invalid party size. Booking aborted.")
        return

    notes = input("Any special requests or notes? (Press enter to skip): ").strip()

    # --- CASE 1: STANDARD BOOKING ---
    if choice == "1":
        table, status = manager.find_available_table(party_size, user_dt)
        if table:
            # Passing the combined full_name variable
            new_res = Standard(
                full_name, phone, date_str, party_size, "Confirmed", table, notes=notes
            )
            table.add_booking(user_dt)
            manager.save_data()
            print(f"\n>> SUCCESS! Table {table.table_no} reserved for {full_name}.")
            print(f">> Reservation ID: {new_res.get_id()}")
        else:
            print("\n>> Sorry, we are fully booked for that party size at that time.")

    # --- CASE 2: EVENT ENQUIRY ---
    elif choice == "2":
        # Passing the combined full_name variable
        new_event = Event(
            full_name, phone, date_str, party_size, "Enquiry", 0.0, 0.0, notes=notes
        )
        manager.save_data()

        print("\n" + "*" * 45)
        print(f"ENQUIRY SUBMITTED! REFERENCE: {new_event.get_id()}")
        print(f"Thank you, {full_name}. Our team will review your request.")
        print("*" * 45)


if __name__ == "__main__":
    run_customer_app()
