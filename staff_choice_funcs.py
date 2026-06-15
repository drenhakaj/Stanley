from datetime import datetime
from config import OPENING_TIME, CLOSING_TIME
from format_helper import get_number_input, get_valid_datetime
from models import Standard, Reservation, Event
from tables import TableManager, Table
from colours import RED, GREEN, RESET, BOLD


# OPTION 1
def floor_plan(manager):
    print(manager.get_floor_plan_data())
    input("\nPress Enter to return to menu...")


# OPTION 2
def area_management_helper(manager):
    """
    Sticky sub-menu for managing restaurant areas.
    Stays active until the user chooses option 4.
    """
    while True:
        print("\n" + "-" * 15 + " AREA MANAGEMENT " + "-" * 15)
        print("1. Add Area | 2. Rename Area | 3. Remove Area | 4. Back")
        sub = get_number_input("\nSelect (1-4): ")

        # --- EXIT OPTION ---
        if sub == 4:
            print("Returning to Main Menu...")
            break  # Breaks the while loop and returns to staff_app.py

        # --- 1. ADD AREA ---
        if sub == 1:
            name = input("New area name: ").strip().title()
            if name in manager.restaurant_areas:
                print(f">> Error: An area named '{name}' already exists.")
            elif input(f"Confirm creation of '{name}'? (y/n): ").lower() == "y":
                success, msg = manager.add_area(name)
                if success:
                    manager.save_data()
                print(f">> {msg}")

        # --- 2. RENAME AREA ---
        elif sub == 2:
            if not manager.restaurant_areas:
                print(">> Error: No areas exist to rename.")
            else:
                print(f"Current Areas: {', '.join(manager.restaurant_areas)}")
                old = input("Rename which area? ").strip().title()
                if old not in manager.restaurant_areas:
                    print(f">> Error: '{old}' not found.")
                else:
                    new = input(f"New name for '{old}': ").strip().title()
                    if new in manager.restaurant_areas:
                        print(
                            f">> Error: Cannot rename to '{new}' because that area already exists."
                        )
                    elif input(f"Change '{old}' to '{new}'? (y/n): ").lower() == "y":
                        success, msg = manager.rename_area(old, new)
                        if success:
                            manager.save_data()
                        print(f">> {msg}")

        # --- 3. REMOVE AREA ---
        elif sub == 3:
            if not manager.restaurant_areas:
                print(">> Error: No areas exist to remove.")
            else:
                print(f"Existing Areas: {', '.join(manager.restaurant_areas)}")
                name = input("Area to remove: ").strip().title()
                if name not in manager.restaurant_areas:
                    print(f">> Error: '{name}' not found.")
                else:
                    success, msg = manager.remove_area(name)
                    if success:
                        manager.save_data()
                    print(f">> {msg}")

        # --- INVALID INPUT ---
        else:
            print(f">> Error: '{sub}' is not valid.")
            input("Press Enter to refresh menu...")


# OPTION 3
def table_management_helper(manager):
    """
    Sticky sub-menu for managing tables.
    Keeps staff in this menu until they choose to go back.
    """
    while True:
        # --- NEW: Get and sort all current table numbers for a quick list ---
        all_table_nos = sorted([t.table_no for t in manager.tables])
        nos_str = ", ".join(map(str, all_table_nos)) if all_table_nos else "None"

        print("\n" + "-" * 15 + " TABLE MANAGEMENT " + "-" * 15)
        print(f"Current Table Numbers: {nos_str}")  # Added this line
        print("-" * 47)
        print("1. Add Table | 2. Remove Table | 3. Back")
        sub = get_number_input("\nSelect (1-3): ")

        # --- EXIT ---
        if sub == 3:
            print("Returning to Main Menu...")
            break

        # --- ADD TABLE ---
        if sub == 1:
            if not manager.restaurant_areas:
                print(">> Error: You must create an Area first.")
            else:
                print(f"Available Areas: {', '.join(manager.restaurant_areas)}")
                area = input("Select Area: ").strip().title()
                if area not in manager.restaurant_areas:
                    print(f">> Error: '{area}' does not exist.")
                else:
                    area_tables = [t for t in manager.tables if t.area == area]
                    print(f"\n--- Current Tables in {area} ---")
                    for t in sorted(area_tables, key=lambda x: x.table_no):
                        print(f"  > Table {t.table_no}")

                    t_no = get_number_input("\nNew Table Number: ")
                    cap = get_number_input("Capacity: ")
                    if t_no is not None and cap is not None:
                        success, msg = manager.add_table(t_no, cap, area)
                        if success:
                            manager.save_data()
                        print(f">> {msg}")

        # --- REMOVE TABLE ---
        elif sub == 2:
            if not manager.tables:
                print(">> Error: No tables exist.")
            else:
                print("\n" + "=" * 45)
                print(manager.get_floor_plan_data())
                t_no = get_number_input("\nEnter Table Number to remove: ")
                if t_no is not None:
                    target = manager.get_table_by_no(t_no)
                    if target:
                        if input(f"Delete Table {t_no}? (y/n): ").lower() == "y":
                            success, msg = manager.remove_table(t_no)
                            if success:
                                manager.save_data()
                            print(f">> {msg}")
                    else:
                        # --- FIX: Error message if table doesn't exist ---
                        print(f">> Error: Table {t_no} does not exist.")

        # --- INVALID INPUT ---
        else:
            print(f">> Error: '{sub}' is not valid.")
            input("Press Enter to refresh menu...")


# OPTION 4
def view_reservations_helper(manager):
    """
    Handles the sub-menu for viewing active and archived reservations.
    Moved from staff_app.py to keep the main file clean.
    """
    print("\n--- VIEW RESERVATIONS ---")
    print("1. All Active | 2. Day | 3. Table | 4. Area | 5. History/Archive")

    # get_number_input is assumed to be in the same file
    sub_choice = get_number_input("Select: ")

    # --- SUB-OPTION 1: ALL ACTIVE ---
    if sub_choice == 1:
        now = datetime.now()
        unassigned = []

        for r in Reservation._all_reservations:
            status = r.get_status()

            # 1. Ignore Cancelled, Past, or raw Enquiries
            # Enquiries don't trigger alerts yet because we haven't sent a quote.
            if status in ["Cancelled", "Enquiry"] or r.get_date() < now:
                continue

            # 2. Check for missing table assignments
            # This catches Standard (Confirmed) and Events (Awaiting Deposit/Confirmed)
            is_unassigned_standard = isinstance(r, Standard) and r.get_table() is None
            is_unassigned_event = isinstance(r, Event) and not r.get_tables()

            if is_unassigned_standard or is_unassigned_event:
                unassigned.append(r)

        # Display the Attention Box if unassigned bookings are found
        if unassigned:
            print("\n" + "!" * 65)
            print(f"{RED}{BOLD}  ATTENTION: UNASSIGNED SEATS FOUND".center(65))
            print(
                f"  These bookings are confirmed/quoted but have no tables! {RESET}".center(
                    65
                )
            )
            print("-" * 65)
            # Table header for the alert box
            print(f"    {'ID':<8} | {'Status':<18} | {'Name':<15} | {'Date'}")
            print("  " + "-" * 61)

            for u in unassigned:
                date_str = u.get_date().strftime("%d %b %H:%M")
                print(
                    f"  > {u.get_id():<8} | {u.get_status():<18} | {u.get_name():<15} | {date_str}"
                )
            print("!" * 65 + f"{RESET}\n")

        print(Reservation.list_all_bookings())

    # --- SUB-OPTION 2: FILTER BY DAY ---
    elif sub_choice == 2:
        print("\nEnter Date to Filter:")
        try:
            y = get_number_input("Year (YYYY): ")
            m = get_number_input("Month (1-12): ")
            d = get_number_input("Day (1-31): ")

            if all([y, m, d]):
                target_date = datetime(y, m, d).strftime("%Y-%m-%d")
                print(Reservation.list_all_bookings(day=target_date))
            else:
                print(">> Error: Incomplete date provided.")
        except ValueError:
            print(">> Error: Invalid date values entered.")

    # --- SUB-OPTION 3: FILTER BY TABLE ---
    elif sub_choice == 3:
        all_nos = [t.table_no for t in manager.get_all_tables()]
        print(f"Current Tables: {', '.join(map(str, all_nos))}")

        table_no = get_number_input("Table: ")

        if table_no not in all_nos:
            print(
                f">> Error: Table {table_no} doesn't exist. Please select from the list above."
            )
        else:
            print(Reservation.list_all_bookings(table_no=table_no))

    # --- SUB-OPTION 4: FILTER BY AREA ---
    elif sub_choice == 4:
        existing_areas = manager.get_all_areas()
        print(f"Current Areas: {', '.join(existing_areas)}")

        area_query = input("Area: ").strip()

        # Check if the area exists (case-insensitive check)
        if area_query.title() not in existing_areas:
            print(f">> Error: '{area_query}' is not a valid area.")
        else:
            print(Reservation.list_all_bookings(area=area_query))

    # --- SUB-OPTION 5: VIEW ARCHIVE ---
    elif sub_choice == 5:
        print(Reservation.list_archive())

    input("\nPress Enter to return to menu...")


# OPTION 5
def manage_reservation_helper(manager):
    """
    Handles assigning, moving, and removing tables for existing bookings.
    Differentiates between Standard (single table) and Event (multi-table) logic.
    Uses functional references instead of menu numbers for future-proofing.
    """
    res_id = input("Enter Reservation ID to manage: ").strip().upper()

    # Locate the reservation in the master list
    res = next((r for r in Reservation._all_reservations if r.get_id() == res_id), None)

    if not res:
        print(">> Error: Reservation ID not found.")
        return

    # --- GATEKEEPER CHECK ---
    # Prevents table assignment for raw enquiries that haven't been quoted yet.
    status = res.get_status()
    if status == "Enquiry":
        print(f"\n{RED}>> BLOCK: This booking is currently a raw ENQUIRY.{RESET}")
        print(
            ">> Please process the enquiry and send a quote before assigning physical tables."
        )
        return

    managing_res = True
    while managing_res:
        current_val = res.get_table()  # Returns list for Events, object for Standard
        party = res.get_party_size()
        status = res.get_status()  # Refresh status for display

        print(f"\n{'-' * 120}")
        # Clean header showing current lifecycle status
        print(
            f"ID: {res_id} | Name: {res.get_name()} | STATUS: {status} | Party: {party}"
        )
        print(
            f"Details: {res.get_date().strftime('%a %d %b %H:%M')} for {res.get_duration()} mins"
        )
        print("-" * 120)

        # --- EVENT-SPECIFIC INTERFACE ---
        if isinstance(res, Event):
            current_cap = res.get_current_capacity()
            # Sorting objects by table number for easy reading
            t_str = (
                ", ".join(
                    [
                        str(t.table_no)
                        for t in sorted(current_val, key=lambda x: x.table_no)
                    ]
                )
                if current_val
                else "NONE"
            )

            print(f"Current Tables: {t_str}")
            print(f"Capacity Status: {current_cap} / {party} seats assigned.")

            if current_cap < party:
                print(f">> NOTICE: You still need {party - current_cap} more seats!")
            else:
                print(f"{BOLD}>> SUCCESS: This event is fully accommodated.{RESET}")

            print("\n1. Add Table | 2. Edit Info | 3. Remove Specific Table | 4. Clear All | 5. Back")

        # --- STANDARD-SPECIFIC INTERFACE ---
        else:
            if current_val:
                print(f"Current: Table {current_val.table_no} ({current_val.area})")
            else:
                print(f"{RED}Current: !!! UNASSIGNED (Table was deleted) !!!{RESET}")

            print("\n1. Move/Assign to Table | 2. Edit Info | 5. Back")

        sub_choice = get_number_input("\nSelect action: ")

        # --- ACTION 1: ADD / MOVE ---
        if sub_choice == 1:
            if (
                isinstance(res, Event)
                and res.get_current_capacity() >= res.get_party_size()
            ):
                print(
                    f"\n>> BLOCK: Event capacity ({res.get_party_size()}) already reached."
                )
                print(">> Remove a table first if you wish to swap assignments.")
                input("\nPress Enter to return...")

            elif not manager.restaurant_areas:
                print(">> Error: No restaurant areas exist yet.")
            else:
                print("\n--- TABLE AVAILABILITY ---")
                for area in manager.restaurant_areas:
                    print(f"[{area}]")
                    area_tables = [t for t in manager.tables if t.area == area]
                    for t in sorted(area_tables, key=lambda x: x.table_no):
                        # check physical availability for this specific time slot
                        status_text = (
                            "FREE"
                            if t.is_available(res.get_date(), res.get_duration())
                            else "OCCUPIED"
                        )
                        print(
                            f"  > Table {t.table_no} | {status_text} | Cap: {t.capacity}"
                        )

                new_t_no = get_number_input("\nEnter Table Number to assign/add: ")
                if new_t_no:
                    success, msg = manager.move_reservation(res_id, new_t_no)
                    if success:
                        manager.save_data()
                    print(f">> {msg}")

                    # Standard bookings auto-exit after assignment; Events stay for multiple tables
                    if not isinstance(res, Event):
                        managing_res = False

        # --- ACTION 2: EDIT RESERVATION DETAILS ---
        elif sub_choice == 2:
            edit_reservation_details_helper(res, manager)

        # --- ACTION 3: REMOVE SPECIFIC (Events Only) ---
        elif sub_choice == 3 and isinstance(res, Event):
            current_tables = res.get_tables()
            if not current_tables:
                print(">> Error: No tables assigned.")
            else:
                print("\n--- TABLES CURRENTLY ASSIGNED ---")
                for t in sorted(current_tables, key=lambda x: x.table_no):
                    print(f"  > Table {t.table_no} ({t.area}) | Cap: {t.capacity}")

                t_no = get_number_input("\nEnter Table Number to remove: ")
                target_t = next((t for t in current_tables if t.table_no == t_no), None)

                if target_t:
                    target_t.remove_booking(res.get_date(), res.get_duration())
                    current_tables.remove(target_t)
                    manager.save_data()
                    print(f">> SUCCESS: Table {t_no} removed.")
                else:
                    print(f">> Error: Table {t_no} not found in this event.")

        # --- ACTION 4: CLEAR ALL (Events Only) ---
        elif sub_choice == 4 and isinstance(res, Event):
            if (
                input("Clear all assigned tables for this event? (y/n): ").lower()
                == "y"
            ):
                msg = res.release_table_slot()
                manager.save_data()
                print(f">> {msg}")

        # --- ACTION 5: EXIT ---
        elif sub_choice == 5:
            managing_res = False

        # --- INVALID INPUT ---
        else:
            print(
                f">> Error: '{sub_choice}' is not valid. Please select a valid action."
            )

# SUB-CHOICE
def edit_reservation_details_helper(res, manager):
    """Sub-menu for adjusting specific text-based booking details."""
    while True:
        print(f"\n--- EDIT DETAILS: {res.get_id()} ---")
        print(f"1. Name: {res.get_name()}")
        print(f"2. Phone: {res.get_phone()}")
        print(f"3. Notes: {res.get_notes() or '(Empty)'}")
        print(f"4. Party Size: {res.get_party_size()}")
        print("5. Save & Back")

        choice = get_number_input("\nSelect field (1-5): ")
        if choice == 1:
            _, msg = res.update_info(manager, name=input("New Name: "))
            print(f">> {msg}")
        elif choice == 2:
            _, msg = res.update_info(manager, phone=input("New Phone: "))
            print(f">> {msg}")
        elif choice == 3:
            _, msg = res.update_info(manager, notes=input("New Notes: "))
            print(f">> {msg}")
        elif choice == 4:
            new_size = get_number_input("New Party Size: ")
            if new_size:
                success, msg = res.update_info(manager, party_size=new_size)
                print(f">> {msg}")
        elif choice == 5:
            manager.save_data()
            break

# OPTION 6
def process_enquiry_helper(manager):
    """
    Handles reviewing enquiries, setting quotes, and recording payments.
    Features a 'Sticky Menu' to allow quoting and paying in one session.
    """
    print("\n" + "-" * 15 + " PROCESS EVENT ENQUIRIES & PAYMENTS " + "-" * 15)

    # 1. Filter: Show events that require action (Enquiry, Awaiting Deposit, or Unpaid)
    to_process = [
        r for r in Reservation._all_reservations
        if isinstance(r, Event) and (r.get_status() in ["Enquiry", "Awaiting Deposit"] or not r.is_paid())
    ]

    if not to_process:
        print(">> System: No events currently require processing or payment.")
        return

    # Display summary table for initial selection
    header = f"{'ID':<10} | {'Name':<15} | {'Status':<18} | {'Payment':<10}"
    print(header)
    print("-" * len(header))
    for e in to_process:
        paid_status = "PAID" if e.is_paid() else "UNPAID"
        print(f"{e.get_id():<10} | {e.get_name():<15} | {e.get_status():<18} | {paid_status:<10}")

    res_id = input("\nEnter ID to Process (or 'c' to cancel): ").strip().upper()
    if res_id == 'C':
        return

    target = next((r for r in to_process if r.get_id() == res_id), None)

    if not target:
        print(f">> Error: ID {res_id} not found in the actionable list.")
        return

    # --- START OF STICKY ACTION MENU ---
    # This loop keeps the staff member focused on the selected reservation
    processing_target = True
    while processing_target:
        # Refresh current data from the object for display
        status = target.get_status()
        price = target.get_price() if hasattr(target, 'get_price') else 0.0
        deposit = target.get_deposit() if hasattr(target, 'get_deposit') else 0.0
        is_paid = target.is_paid()

        # Detailed Enquiry Info Card
        print("\n" + "=" * 60)
        print(f"{BOLD}[ ENQUIRY DETAILS ]{RESET}".center(60))
        print("=" * 60)
        print(f"{'Reservation ID:':<20} {target.get_id()}")
        print(f"{'Current Status:':<20} {status}")
        print(f"{'Customer Name:':<20} {target.get_name()}")
        print(f"{'Party Size:':<20} {target.get_party_size()} guests")
        print(f"{'Date & Time:':<20} {target.get_date().strftime('%A, %d %b %Y at %H:%M')}")
        print(f"{'Duration:':<20} {target.get_duration()} minutes")
        print(f"{'Contact Info:':<20} {target.get_phone()}")
        if target.get_notes():
            print(f"{'Event Notes:':<20} {target.get_notes()}")
        
        # --- DYNAMIC FINANCIAL SECTION ---
        # Only appears once a Quote has been set (i.e., status is no longer 'Enquiry')
        if status != "Enquiry":
            print("-" * 60)
            print(f"{'Total Quote:':<20} ${price:,.2f}")
            print(f"{'Deposit Req:':<20} ${deposit:,.2f}")
            
            # Calculate what is owed based on payment status
            if is_paid:
                balance = price - deposit
                label = "REMAINING BALANCE:"
                pay_text = f"{GREEN}PAID{RESET}"
            else:
                balance = price
                label = "TOTAL OWED:"
                pay_text = f"{RED}UNPAID{RESET}"

            print(f"{'Deposit Status:':<20} {pay_text}")
            print(f"{BOLD}{label:<20} ${balance:,.2f}{RESET}")
        
        print("=" * 60)

        # Action Selection
        print(f"\nSelect action for {target.get_name()}:")
        print("1. Set Quote & Send to Customer")
        print("2. Reject / Cancel Enquiry")
        print("3. Record Deposit Payment (Confirm Booking)")
        print("4. Back to Home")

        action = get_number_input("\nSelect action (1-4): ")

        # --- ACTION 1: SET QUOTE ---
        if action == 1:
            if status != "Enquiry":
                print(f">> Error: Already quoted (Current Status: {status}).")
            else:
                # Capacity Check (Shadow Booking Logic)
                if not manager.can_fit_party(target.get_date(), target.get_duration(), target.get_party_size()):
                    print(f"\n{RED}{BOLD}>> WARNING: Restaurant capacity is FULL for this time slot!{RESET}")
                    if input("Send quote anyway? (y/n): ").lower() != "y":
                        continue # Return to sticky menu

                print(f"\nSetting Quote for {target.get_name()}...")
                new_price = get_number_input("Enter Total Quote Price: ")
                new_deposit = get_number_input("Enter Deposit Required: ")

                if new_price is not None and new_deposit is not None:
                    try:
                        target.set_financials(new_price, new_deposit)
                        target._status = "Awaiting Deposit" 
                        manager.save_data()
                        print(f"\n>> SUCCESS: Quote saved. Status: Awaiting Deposit.")
                    except ValueError as e:
                        print(f">> Error: {e}")
                else:
                    print(">> Error: Invalid pricing inputs.")

        # --- ACTION 2: REJECT / CANCEL ---
        elif action == 2:
            if input(f"Confirm REJECTION of enquiry {target.get_id()}? (y/n): ").lower() == "y":
                print(target.cancel_booking())
                manager.save_data()
                processing_target = False # Break loop as reservation no longer exists

        # --- ACTION 3: RECORD PAYMENT ---
        elif action == 3:
            if status == "Enquiry":
                print(f"\n{RED}>> BLOCK: You must set a quote (Action 1) before recording payment!{RESET}")
                # We do NOT use 'return' here, so the user stays in the sticky menu to pick Action 1
            elif is_paid:
                print(">> Error: This event is already marked as PAID.")
            else:
                if input(f"Confirm PAID status for {target.get_id()}? (y/n): ").lower() == "y":
                    result_msg = target.mark_as_paid()
                    manager.save_data()
                    print(f"\n{result_msg}")
                    print(f"{RED}{BOLD}>> ACTION REQUIRED: Booking is now CONFIRMED.{RESET}")
                    print(">> Physical tables should now be assigned in the Manage Tables menu.")

        # --- ACTION 4: EXIT STICKY MENU ---
        elif action == 4:
            processing_target = False

        else:
            print(">> Invalid choice. Please select 1-4.")
