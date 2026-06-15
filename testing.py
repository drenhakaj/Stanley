from tables import TableManager
from models import Standard, Event, Reservation
from datetime import datetime, timedelta
import random


def create_test_environment():
    manager = TableManager()

    # 1. Setup the Restaurant Floor
    manager.add_area("Main Hall")
    manager.add_area("Garden Terrace")

    manager.add_table(1, 2, "Main Hall")
    manager.add_table(2, 4, "Main Hall")
    manager.add_table(3, 4, "Main Hall")
    manager.add_table(4, 2, "Garden Terrace")
    manager.add_table(5, 6, "Garden Terrace")
    manager.add_table(10, 12, "Main Hall")  # Big table for events

    # 2. Clear any old data
    Reservation._all_reservations = []

    now = datetime.now()

    # 3. Generate Mock Reservations
    test_data = [
        # Standard Bookings
        {
            "f": "Alice",
            "l": "Smith",
            "p": "0412 345 678",
            "size": 2,
            "type": "std",
            "notes": "Allergy: Shellfish",
        },
        {
            "f": "Bob",
            "l": "Jones",
            "p": "0422 111 222",
            "size": 4,
            "type": "std",
            "notes": "Window seat preferred",
        },
        {
            "f": "Charlie",
            "l": "Brown",
            "p": "0433 999 888",
            "size": 2,
            "type": "std",
            "notes": "",
        },
        # Event Enquiries
        {
            "f": "David",
            "l": "Miller",
            "p": "0455 000 111",
            "size": 15,
            "type": "evt",
            "notes": "50th Birthday - Bringing a large cake",
        },
        {
            "f": "Eve",
            "l": "Wilson",
            "p": "0466 777 888",
            "size": 10,
            "type": "evt",
            "notes": "Corporate lunch - Need a quiet corner",
        },
    ]

    for i, person in enumerate(test_data):
        # Stagger times by hours
        res_time = (now + timedelta(days=1, hours=i)).strftime("%Y-%m-%d %H:%M")
        full_name = f"{person['f']} {person['l']}"

        if person["type"] == "std":
            # Auto-assign a table
            table, _ = manager.find_available_table(
                person["size"], datetime.strptime(res_time, "%Y-%m-%d %H:%M")
            )
            if table:
                Standard(
                    full_name,
                    person["p"],
                    res_time,
                    person["size"],
                    "Confirmed",
                    table,
                    notes=person["notes"],
                )
                table.add_booking(datetime.strptime(res_time, "%Y-%m-%d %H:%M"))
        else:
            # Create as enquiry (No tables assigned yet)
            Event(
                full_name,
                person["p"],
                res_time,
                person["size"],
                "Enquiry",
                0.0,
                0.0,
                notes=person["notes"],
            )

    # 4. Save to JSON
    manager.save_data()
    print(f">> SUCCESS: Created {len(test_data)} test reservations.")
    print(">> Open your Staff App and select Option 7 to see the new layout!")


if __name__ == "__main__":
    create_test_environment()
