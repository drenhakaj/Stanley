from datetime import timedelta, datetime
import json
import os
from models import Reservation, Standard, Event
from config import STANDARD_DURATION, EVENT_DURATION


class Table:
    """Represents a physical table in the restaurant."""

    def __init__(self, table_no: int, capacity: int, area: str):
        self.table_no = table_no
        self.capacity = capacity
        self.area = area
        self.bookings = {}  

    def is_available(self, start_time, duration_hrs=STANDARD_DURATION):
        """Checks if a time slot overlaps, isolated to a specific date bucket."""
        end_time = start_time + timedelta(hours=duration_hrs)
        date_key = start_time.strftime("%Y-%m-%d")
        
        # O(1) Check: If there are absolutely zero bookings on this date, it's instantly FREE
        if date_key not in self.bookings:
            return True
            
        # If the date has bookings, only loop through that specific day's records
        for b_start, b_end in self.bookings[date_key]:
            if start_time < b_end and end_time > b_start:
                return False
        return True

    def add_booking(self, start_time, duration_hrs=STANDARD_DURATION):
        """Adds a time block directly into the appropriate date bucket."""
        end_time = start_time + timedelta(hours=duration_hrs)
        date_key = start_time.strftime("%Y-%m-%d")
        
        if date_key not in self.bookings:
            self.bookings[date_key] = []
            
        self.bookings[date_key].append((start_time, end_time))
        return True

    def remove_booking(self, start_time, duration_hrs=STANDARD_DURATION):
        """Finds and removes a specific time slot inside its date bucket."""
        end_time = start_time + timedelta(hours=duration_hrs)
        date_key = start_time.strftime("%Y-%m-%d")
        
        if date_key not in self.bookings:
            return False
            
        initial_count = len(self.bookings[date_key])
        self.bookings[date_key] = [
            b for b in self.bookings[date_key] 
            if not (b[0] == start_time and b[1] == end_time)
        ]
        return len(self.bookings[date_key]) < initial_count

    def __repr__(self):
        # This tells Python: "When someone prints me, show my table number instead of my memory ID"
        return f"Table {self.table_no}"


class TableManager:
    """The 'Brain' of the system. Handles data persistence and assignment logic."""

    def __init__(self):
        self.tables = []
        self.restaurant_areas = []

    # --- AREA & TABLE MANAGEMENT ---
    def add_area(self, area_name: str):
        area = area_name.strip().title()
        if area not in self.restaurant_areas:
            self.restaurant_areas.append(area)
            return True, f"Area {area} added."
        return False, "Area already exists."

    def add_table(self, table_no: int, capacity: int, area_name: str):
        area = area_name.strip().title()
        if area not in self.restaurant_areas:
            return False, f"Error: Area {area} does not exist."
        if any(t.table_no == table_no for t in self.tables):
            return False, f"Error: Table {table_no} already exists."
        self.tables.append(Table(table_no, capacity, area))
        return True, f"Table {table_no} added."

    def remove_table(self, table_no: int):
        """Removes a table and flags any impacted bookings within the next 7 real-life days."""
        target = self.get_table_by_no(table_no)
        if not target:
            return False, f"Error: Table {table_no} not found."

        urgent_orphans = []
        # --- REAL WORLD TIME LOGIC ---
        now = datetime.now()
        one_week_later = now + timedelta(days=7)

        # 1. Detach affected reservations
        for res in Reservation._all_reservations:
            is_affected = False

            if isinstance(res, Standard) and res.get_table() == target:
                res._Standard__table = None
                is_affected = True
            elif isinstance(res, Event) and target in res.get_tables():
                res.get_tables().remove(target)
                is_affected = True

            # 2. Check if the booking is 'Urgent' (within next 7 days from TODAY)
            if is_affected:
                # We only care about bookings today or in the future week
                if now <= res.get_date() <= one_week_later:
                    urgent_orphans.append(
                        f"{res.get_id()} | {res.get_name()} | {res.get_date().strftime('%a %d %b')}"
                    )

        # 3. Physically remove the table
        self.tables.remove(target)

        msg = f"SUCCESS: Table {table_no} removed from floor plan."

        if urgent_orphans:
            msg += f"\n\n!!! URGENT ACTION REQUIRED: {len(urgent_orphans)} BOOKING(S) IN NEXT 7 DAYS !!!"
            for alert in urgent_orphans:
                msg += f"\n  [!] {alert}"
            msg += (
                "\n\nPlease use Option 8 to re-assign these to new tables immediately."
            )

        return True, msg

    def get_table_by_no(self, table_no: int):
        return next((t for t in self.tables if t.table_no == table_no), None)

    def get_all_tables(self, sorted_by_no=True):
        """
        Returns all table objects.
        If sorted_by_no is True, they are returned in numerical order.
        """
        if sorted_by_no:
            return sorted(self.tables, key=lambda t: t.table_no)
        return self.tables

    def get_floor_plan_data(self):
        """Generates a visual summary of all areas and tables for Staff Option 1."""
        if not self.restaurant_areas:
            return "\n>> Floor plan is empty. Please add an area first (Option 2)."

        output = ["\n" + "=" * 45, f"{'RESTAURANT FLOOR PLAN':^45}", "=" * 45]

        # Sort areas alphabetically
        for area in sorted(self.restaurant_areas):
            output.append(f"\n[{area.upper()}]")

            # Filter and sort tables in this area numerically
            area_tables = [t for t in self.tables if t.area == area]

            if not area_tables:
                output.append("  (No tables assigned)")
            else:
                for t in sorted(area_tables, key=lambda x: x.table_no):
                    output.append(f"  > Table {t.table_no:<3} | Capacity: {t.capacity}")

        return "\n".join(output)

    def get_all_areas(self):
        """
        Scans all current tables and returns a sorted list of unique area names.
        Useful if areas and tables were loaded from a file.
        """
        # 1. Collect area names from every table object
        # 2. Use set() to remove duplicates
        areas = {t.area for t in self.tables if hasattr(t, "area") and t.area}

        # 3. Return as a sorted list for a consistent UI
        return sorted(list(areas))

    def rename_area(self, old_name: str, new_name: str):
        """Updates an area name and migrates all existing tables to the new name."""
        old = old_name.strip().title()
        new = new_name.strip().title()

        if old not in self.restaurant_areas:
            return False, f"Error: Area '{old}' does not exist."

        if new in self.restaurant_areas:
            return False, f"Error: Area '{new}' already exists. Use a unique name."

        # 1. Update the master area list
        index = self.restaurant_areas.index(old)
        self.restaurant_areas[index] = new

        # 2. Update all tables currently assigned to the old area
        count = 0
        for t in self.tables:
            if t.area == old:
                t.area = new
                count += 1

        return (
            True,
            f"SUCCESS: Area '{old}' renamed to '{new}'. {count} table(s) updated.",
        )

    def remove_area(self, area_name: str):
        """
        Removes an area from the system only if it contains no tables.
        """
        area = area_name.strip().title()

        if area not in self.restaurant_areas:
            return False, f"Error: Area '{area}' not found."

        # Safety Check: Check if any tables are still linked to this area
        tables_in_area = [t for t in self.tables if t.area == area]

        if tables_in_area:
            return (
                False,
                f"Cannot remove: '{area}' still contains {len(tables_in_area)} tables. Delete the tables first.",
            )

        self.restaurant_areas.remove(area)
        return True, f"Area '{area}' successfully removed."

    # --- RESERVATION ASSIGNMENT ---
    def move_reservation(self, res_id, new_table_no):
        res = next(
            (r for r in Reservation._all_reservations if r.get_id() == res_id), None
        )
        if not res:
            return False, "Reservation not found."

        new_table = self.get_table_by_no(new_table_no)
        if not new_table:
            return False, f"Table {new_table_no} doesn't exist."

        if not new_table.is_available(res.get_date(), res.get_duration()):
            return False, f"Table {new_table_no} is occupied."

        if isinstance(res, Standard):
            if new_table.capacity < res.get_party_size():
                return False, "Table too small."
            res.release_table_slot()
            # Update the private attribute in the Standard instance
            res._Standard__table = new_table
            new_table.add_booking(res.get_date(), res.get_duration())
            return True, f"Moved to Table {new_table_no}."

        elif isinstance(res, Event):
            # Event behavior: Adds to the list rather than replacing
            res.add_table_to_event(new_table)
            new_table.add_booking(res.get_date(), res.get_duration())
            return True, f"Table {new_table_no} added to Event {res_id}."

    def find_available_table(
        self, party_size, date_time, duration_hrs=STANDARD_DURATION
    ):
        """Finds the smallest available table that fits the party."""
        available = [
            t
            for t in self.tables
            if t.capacity >= party_size and t.is_available(date_time, duration_hrs)
        ]
        if not available:
            return None, None
        best_fit = min(available, key=lambda x: x.capacity)
        return best_fit, "Found"

    def get_total_restaurant_capacity(self):
        """Returns the sum of all table capacities."""
        return sum(t.capacity for t in self.tables)

    def get_seats_occupied_at(self, target_date, duration):
        from models import Reservation
        from datetime import datetime

        # Ensure target_date is a datetime object
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d %H:%M")

        occupied_seats = 0
        for res in Reservation._all_reservations:
            if res.get_status() in ["Confirmed", "Awaiting Deposit"]:
                # The overlap math is the most critical part:
                if self._check_time_overlap(
                    res.get_date(), res.get_duration(), target_date, duration
                ):
                    occupied_seats += res.get_party_size()
        return occupied_seats

    def _check_time_overlap(self, start1, dur1, start2, dur2):
        """Helper to see if two time slots crash into each other."""
        from datetime import timedelta

        end1 = start1 + timedelta(minutes=dur1)
        end2 = start2 + timedelta(minutes=dur2)
        return start1 < end2 and start2 < end1

    def can_fit_party(self, date, duration, party_size):
        """The ultimate check: Total Capacity - Occupied >= New Party?"""
        total = self.get_total_restaurant_capacity()
        occupied = self.get_seats_occupied_at(date, duration)
        return (total - occupied) >= party_size

    # --- DATA PERSISTENCE (Crucial Updates) ---
    # Update the save_data and load_data methods within TableManager in tables.py

    def save_data(self, filename="restaurant_data.json"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, filename)
        res_data = []

        for res in Reservation._all_reservations:
            res_type = "Standard" if isinstance(res, Standard) else "Event"
            t_val = (
                res.get_table().table_no
                if res_type == "Standard" and res.get_table()
                else (
                    [t.table_no for t in res.get_tables()]
                    if res_type == "Event"
                    else None
                )
            )

            data = {
                "type": res_type,
                "name": res.get_name(),
                "phone": res.get_phone(),
                "date": res.get_date().strftime("%Y-%m-%d %H:%M"),
                "size": res.get_party_size(),
                "status": res.get_status(),
                "notes": res.get_notes(),  # Saving the notes
                "table_no": t_val,
                "paid": res.is_paid(),
            }
            if isinstance(res, Event):
                data.update(
                    {
                        "price": res.get_price(),
                        "deposit": res.get_deposit(),
                        "duration": res.get_duration(),
                    }
                )
            res_data.append(data)

        full_dump = {
            "areas": self.restaurant_areas,
            "tables": [
                {
                    "no": t.table_no,
                    "cap": t.capacity,
                    "area": t.area,
                    # Iterate over the dictionary items instead of a flat list
                    "bookings": {
                        date: [[b[0].isoformat(), b[1].isoformat()] for b in blocks]
                        for date, blocks in t.bookings.items()
                    },
                }
                for t in self.tables
            ],
            "reservations": res_data,
        }
        with open(full_path, "w") as f:
            json.dump(full_dump, f, indent=4)
        return "Data saved successfully."

    def load_data(self, filename="restaurant_data.json"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, filename)
        if not os.path.exists(full_path):
            return False, "No save file found."

        try:
            with open(full_path, "r") as f:
                data = json.load(f)
                self.restaurant_areas = data.get("areas", [])
                Reservation._all_reservations = []
                self.tables = []

                for t_data in data.get("tables", []):
                    t = Table(t_data["no"], t_data["cap"], t_data["area"])
                    bookings_json = t_data.get("bookings", {})
                    
                    # Safe validation check to handle your new dictionary structure
                    if isinstance(bookings_json, dict):
                        for date_key, blocks in bookings_json.items():
                            t.bookings[date_key] = [
                                (datetime.fromisoformat(b[0]), datetime.fromisoformat(b[1]))
                                for b in blocks
                            ]
                    else: 
                        # Fallback parsing system to support reading older, flat-list JSON files
                        for b in bookings_json:
                            start_dt = datetime.fromisoformat(b[0])
                            t.add_booking(start_dt)
                            
                    self.tables.append(t)

                for r in data.get("reservations", []):
                    # Passing notes back into constructors
                    if r["type"] == "Standard":
                        table_obj = self.get_table_by_no(r["table_no"])
                        res = Standard(
                            r["name"],
                            r["phone"],
                            r["date"],
                            r["size"],
                            r["status"],
                            table_obj,
                            notes=r.get("notes", ""),
                        )
                    else:
                        table_list = (
                            [self.get_table_by_no(tn) for tn in r["table_no"]]
                            if r["table_no"]
                            else []
                        )
                        res = Event(
                            r["name"],
                            r["phone"],
                            r["date"],
                            r["size"],
                            r["status"],
                            r.get("price", 0),
                            r.get("deposit", 0),
                            tables=table_list,
                            duration_hrs=r.get("duration", 4),
                            notes=r.get("notes", ""),
                        )

                    res._paid = r.get("paid", False)
            return True, "System loaded successfully."
        except Exception as e:
            return False, f"Load Error: {e}"
