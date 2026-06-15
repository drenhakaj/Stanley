from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from config import BUSINESS_NAME
from colours import RED, RESET, BOLD


class Reservation(ABC):
    """
    Abstract Base Class for all reservations.
    Handles core data (Combined Name, Phone, Time, ID, and Notes).
    """

    _next_id = 1000
    _all_reservations = []

    def __init__(
        self,
        guest_name,
        phone_no,
        date_time_str,
        party_size,
        duration_hrs=2,
        status="Pending",
        notes="",
    ):
        self.__date_time_str = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")

        is_new = status in ["Pending", "Confirmed", "Enquiry"]
        if is_new and self.__date_time_str < datetime.now():
            if self.__date_time_str.date() < datetime.now().date():
                raise ValueError("Cannot create a booking for a past date.")

        self.__guest_name = guest_name.strip().title()
        self.__phone_no = phone_no.strip()
        self.__notes = notes.strip()
        self._status = status
        self.__party_size = party_size
        self.__duration_hrs = duration_hrs
        self._is_paid = False

        self.__reservation_id = f"RES{Reservation._next_id}"
        Reservation._next_id += 1
        Reservation._all_reservations.append(self)
        self._history = [f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    # --- GETTERS ---
    def get_id(self):
        return self.__reservation_id

    def get_name(self):
        return self.__guest_name

    def get_phone(self):
        return self.__phone_no

    def get_notes(self):
        return self.__notes

    def get_date(self):
        return self.__date_time_str

    def get_status(self):
        return self._status

    def get_party_size(self):
        return self.__party_size

    def get_duration(self):
        return self.__duration_hrs

    def get_table(self):
        if isinstance(self, Standard):
            return getattr(self, f"_{self.__class__.__name__}__table", None)
        elif isinstance(self, Event):
            return self.get_tables()
        return None

    def is_paid(self):
        return getattr(self, "_is_paid", False)

    # --- ACTIONS ---
    def confirm_booking(self):
        self._status = "Confirmed"
        self._history.append(f"Confirmed: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return f"SUCCESS: {self.get_id()} ({self.get_name()}) is now Confirmed."

    def cancel_booking(self):
        """
        Logic to free assigned table(s) and update the reservation status.
        Works for both Standard (single table) and Event (multiple tables).
        """
        # 1. Use the existing release_table_slot logic you already wrote
        # for each subclass to clean up the table objects.
        msg = self.release_table_slot()

        # 2. Update the status
        self._status = "Cancelled"

        # 3. Add to history
        self._history.append(f"Cancelled: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        return f"SUCCESS: Booking {self.get_id()} has been cancelled. ({msg})"

    def notify_customer(self, message_type="Update"):
        name = self.get_name()
        res_id = self.get_id()
        date_str = self.get_date().strftime("%B %d at %H:%M")

        print(f"\n>>> [NOTIFICATION SENT TO {name.upper()}] <<<")
        print(f"From: {BUSINESS_NAME}")

        if message_type == "Confirmed":
            print(f"Subject: Booking Confirmed - {res_id}")
            print(
                f"Message: Great news {name}! Your booking at {BUSINESS_NAME} for {date_str} is now confirmed."
            )

        elif message_type == "DepositRequired":
            owed = self.get_price() - self.get_deposit()
            print(f"Subject: Action Required: Deposit for {res_id}")
            print(
                f"Message: Hello {name}, we have allocated space at {BUSINESS_NAME} for your event on {date_str}!"
            )
            print(f"To finalize, please pay a deposit of ${self.get_deposit():.2f}.")
            print(f"Total Quote: ${self.get_price():.2f} | Remaining: ${owed:.2f}")

    def reactivate_booking(self):
        """Restores a cancelled booking to Pending status."""
        if self._status != "Cancelled":
            return f"Error: Only cancelled bookings can be reactivated. (Current: {self._status})"

        self._status = "Pending"
        self._history.append(
            f"Reactivated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return f"SUCCESS: Reservation {self.get_id()} is now Pending. Please re-assign tables."

    def update_info(self, manager, name=None, phone=None, notes=None, party_size=None):
        from tables import TableManager as manager

        """Updates core reservation details."""
        if name:
            self.__guest_name = name.strip().title()
        if phone:
            self.__phone_no = phone.strip()
        if notes is not None:  # Allows empty string to clear notes
            self.__notes = notes.strip()
        if party_size:
            # Check capacity if the size is increasing
            if party_size > self.get_party_size():
                increase = party_size - self.get_party_size()
                if not manager.can_fit_party(
                    self.get_date(), self.get_duration(), increase
                ):
                    return (
                        False,
                        f"Error: Cannot increase to {party_size}. Restaurant is at capacity.",
                    )

            self._Reservation__party_size = party_size  # Accessing private attr
        self._history.append(
            f"Updated Info: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return True, f"SUCCESS: Details updated for {self.get_id()}."

    @abstractmethod
    def release_table_slot(self):
        pass

    @abstractmethod
    def get_info(self):
        pass

    @classmethod
    def list_all_bookings(cls, day=None, table_no=None, area=None):
        if not cls._all_reservations:
            return "No reservations found."

        now = datetime.now()

        # 1. Filter: ONLY show bookings that are NOT Cancelled AND are NOT in the past
        filtered = [
            r
            for r in cls._all_reservations
            if r.get_status() != "Cancelled" and r.get_date() >= now
        ]

        # 2. Apply existing filters
        if day:
            filtered = [r for r in filtered if r.get_date().strftime("%Y-%m-%d") == day]
        if table_no:
            filtered = [
                r
                for r in filtered
                if (
                    isinstance(r, Standard)
                    and r.get_table()
                    and r.get_table().table_no == table_no
                )
                or (
                    isinstance(r, Event)
                    and any(t.table_no == table_no for t in r.get_tables())
                )
            ]
        if area:
            # We standardize the search term to match your .title() storage format
            search_area = area.strip().title()
            filtered = [
                r
                for r in filtered
                if (
                    isinstance(r, Standard)
                    and r.get_table()
                    and r.get_table().area == search_area
                )
                or (
                    isinstance(r, Event)
                    and any(t.area == search_area for t in r.get_tables())
                )
            ]

        if not filtered:
            return "\n>> No active upcoming reservations match your criteria."

        # 3. Sort and Build Output
        sorted_bookings = sorted(
            filtered, key=lambda res: (res.get_date(), res.get_name().lower())
        )
        output = ["\n=== CURRENT ACTIVE RESERVATIONS ==="]
        for res in sorted_bookings:
            output.append("-" * 130)
            output.append(res.get_info())
        return "\n".join(output)

    @classmethod
    def list_archive(cls):
        """Returns bookings that are either cancelled or from the past."""
        now = datetime.now()

        # Filter: Status is Cancelled OR the date is earlier than right now
        archive = [
            r
            for r in cls._all_reservations
            if r.get_status() == "Cancelled" or r.get_date() < now
        ]

        if not archive:
            return "\n>> The archive is currently empty."

        # Sort by date (most recent at the top)
        sorted_archive = sorted(archive, key=lambda x: x.get_date(), reverse=True)

        output = ["\n=== RESERVATION HISTORY & ARCHIVE ==="]
        for res in sorted_archive:
            # Add a visual tag so you know WHY it's in the archive
            tag = "[CANCELLED]" if res.get_status() == "Cancelled" else "[PAST]"
            output.append("-" * 130)
            output.append(f"{tag}\n{res.get_info()}")

        return "\n".join(output)


class Standard(Reservation):
    def __init__(self, name, phone, date_str, size, status, table_obj, notes=""):
        super().__init__(name, phone, date_str, size, status=status, notes=notes)
        self.__table = table_obj

    def release_table_slot(self):
        """Clears the table's schedule only if a table is currently assigned."""
        # 1. Safety check: If the table was deleted or never assigned
        if self.__table is None:
            return "No table was assigned; skipping release."

        # 2. Communicate with the Table object to remove the time slot
        success = self.__table.remove_booking(self.get_date(), self.get_duration())

        if success:
            temp_no = self.__table.table_no
            self.__table = None  # Clear the reference after successful removal
            return f"Table {temp_no} slot released."

        return "Booking slot not found on table schedule."

    def get_info(self):
        dt = self.get_date().strftime("%m-%d %H:%M")
        # Check if table exists before trying to access its number
        table_obj = self.get_table()
        if table_obj:
            t_info = f"{table_obj.table_no} ({table_obj.area})"
        else:
            t_info = f"{RED}{BOLD}UNASSIGNED{RESET}"

        header = f"{'ID:':^10}| {'Who:':^25}| {'Phone:':^15}| {'When (MM-DD):':^18}| {'Size:':^8}| {'Table:':^18}"
        data = f"{self.get_id():<10}| {self.get_name():<25}| {self.get_phone():<15}| {dt:<18}| {self.get_party_size():<8}| {t_info:<18}"

        notes = f"\n   >> NOTES: {self.get_notes()}" if self.get_notes() else ""
        return f"{header}\n{data}\n{notes}"


class Event(Reservation):
    def __init__(
        self,
        name,
        phone,
        date_str,
        size,
        status,
        price,
        deposit,
        tables=None,
        duration_hrs=4,
        notes="",
    ):
        super().__init__(
            name,
            phone,
            date_str,
            size,
            duration_hrs=duration_hrs,
            status=status,
            notes=notes,
        )
        self._is_paid = False
        self.__price = 0.0
        self.__deposit = 0.0
        self.__tables = tables if tables else []
        if price or deposit:
            self.set_financials(price, deposit)

    # --- GETTERS ---
    def get_tables(self):
        return self.__tables

    def is_paid(self):
        return self._is_paid

    def get_price(self):
        return self.__price

    def get_deposit(self):
        return self.__deposit

    def get_current_capacity(self):
        return sum(t.capacity for t in self.__tables)

    # --- ACTIONS ---
    def add_table_to_event(self, table_obj):
        if table_obj not in self.__tables:
            self.__tables.append(table_obj)

    def release_table_slot(self):
        """Loops through all assigned tables and frees them up in the system."""
        # 1. Safety check: Handle empty lists
        if not self.__tables:
            return "No tables were assigned to this event."

        count = 0
        for t in self.__tables:
            # 2. Check if the individual table object exists
            if t is not None:
                success = t.remove_booking(self.get_date(), self.get_duration())
                if success:
                    count += 1

        # 3. Wipe the list clean
        self.__tables = []
        return f"SUCCESS: {count} tables have been released and cleared from the event."

    def set_financials(self, price, deposit):
        """Sets the official quote and deposit requirements."""
        if price < 0 or deposit < 0:
            raise ValueError("Pricing cannot be negative.")

        self.__price = float(price)
        self.__deposit = float(deposit)

    def mark_as_paid(self):
        """Records payment and promotes the booking to Confirmed."""
        self._is_paid = True
        self._status = "Confirmed"  # <--- THIS IS THE KEY LINE
        return (
            f"SUCCESS: Payment recorded. Reservation {self.get_id()} is now CONFIRMED."
        )

    def get_info(self):
        dt = self.get_date().strftime("%m-%d %H:%M")
        t_info = (
            ", ".join(
                [
                    str(t.table_no)
                    for t in sorted(self.__tables, key=lambda x: x.table_no)
                ]
            )
            if self.__tables
            else "PENDING"
        )

        # --- DYNAMIC OWED CALCULATION ---
        if self.is_paid():
            # If the event is marked as paid, they owe nothing
            owed = 0.0
        elif self.get_status() == "Awaiting Deposit":
            # If they haven't paid anything yet, they owe the full price
            # (Or you can set this to the deposit amount if you prefer
            # to only show what is currently due)
            owed = self.__price
        else:
            # If the deposit is paid but the full balance isn't
            # (Assuming your mark_as_paid only covers the deposit)
            owed = self.__price - self.__deposit

        size = self.get_party_size()
        header = f"{'[EVENT]\n'}{'ID:':^10}| {'Who:':^18}| {'Phone:':^15}| {'When (MM-DD):':^18}| {'Size:':^8}| {'Owed:':^10}| {'Tables:':^15}"
        data = f"{self.get_id():<10}| {self.get_name():<18}| {self.get_phone():<15}| {dt:<18}| {size:<8}| {owed:<10.2f}| {t_info:<15}"

        # Add notes on a new line if they exist
        notes = f"\n   >> EVENT NOTES: {self.get_notes()}" if self.get_notes() else ""
        return f"{header}\n{data}\n{notes}"
