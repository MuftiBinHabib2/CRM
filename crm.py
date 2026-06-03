import tkinter as tk
from tkinter import ttk
import sqlite3
import os
import calendar
import datetime

class CalendarDialog(tk.Toplevel):
    def __init__(self, parent, title="Select Date", initial_date=None, callback=None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        
        # Center the window relative to parent
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        self.resizable(False, False)
        
        self.callback = callback
        try:
            self.current_date = datetime.datetime.strptime(initial_date, "%Y-%m-%d").date()
        except (ValueError, TypeError, AttributeError):
            self.current_date = datetime.date.today()
            
        self.year = self.current_date.year
        self.month = self.current_date.month
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self, pady=5)
        header_frame.pack(fill="x")
        
        self.prev_btn = ttk.Button(header_frame, text="<", width=3, command=self.prev_month)
        self.prev_btn.pack(side="left", padx=10)
        
        self.header_label = ttk.Label(header_frame, font=("Helvetica", 10, "bold"))
        self.header_label.pack(side="left", expand=True)
        
        self.next_btn = ttk.Button(header_frame, text=">", width=3, command=self.next_month)
        self.next_btn.pack(side="right", padx=10)
        
        # Weekdays header
        weeks_frame = tk.Frame(self)
        weeks_frame.pack(fill="x", padx=10)
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for day in days:
            lbl = ttk.Label(weeks_frame, text=day, width=4, anchor="center", font=("Helvetica", 9, "bold"))
            lbl.pack(side="left", expand=True)
            
        # Grid frame
        self.grid_frame = tk.Frame(self)
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bottom controls
        bottom_frame = tk.Frame(self, pady=5)
        bottom_frame.pack(fill="x")
        
        today_btn = ttk.Button(bottom_frame, text="Today", command=self.select_today)
        today_btn.pack(side="left", padx=10)
        
        clear_btn = ttk.Button(bottom_frame, text="Clear", command=self.clear_date)
        clear_btn.pack(side="right", padx=10)
        
        self.draw_calendar()

    def draw_calendar(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        self.header_label.config(text=f"{calendar.month_name[self.month]} {self.year}")
        
        cal = calendar.monthcalendar(self.year, self.month)
        today = datetime.date.today()
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    lbl = ttk.Label(self.grid_frame, text="")
                    lbl.grid(row=r, column=c, sticky="nsew", ipady=2)
                else:
                    btn_date = datetime.date(self.year, self.month, day)
                    bg = "#e0e0e0"
                    fg = "black"
                    
                    if btn_date == today:
                        fg = "#0056b3"
                    if btn_date == self.current_date:
                        bg = "#a0c0e0"
                        
                    btn = tk.Button(self.grid_frame, text=str(day), bg=bg, fg=fg, bd=1, relief="flat",
                                    font=("Helvetica", 9),
                                    command=lambda d=btn_date: self.select_date(d))
                    btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                    
        for i in range(7):
            self.grid_frame.columnconfigure(i, weight=1)
        for i in range(6):
            self.grid_frame.rowconfigure(i, weight=1)

    def select_date(self, date):
        if self.callback:
            self.callback(date.strftime("%Y-%m-%d"))
        self.destroy()
        
    def select_today(self):
        self.select_date(datetime.date.today())
        
    def clear_date(self):
        if self.callback:
            self.callback("")
        self.destroy()
        
    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.draw_calendar()
        
    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.draw_calendar()


class CalendarViewWindow(tk.Toplevel):
    def __init__(self, parent, db_conn, on_select_contact_callback):
        super().__init__(parent)
        self.title("Follow-up Calendar")
        self.geometry("620x420")
        self.transient(parent)
        
        # Center the window relative to parent
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 30, parent.winfo_rooty() + 30))
        
        self.db_conn = db_conn
        self.on_select_contact_callback = on_select_contact_callback
        
        self.today = datetime.date.today()
        self.year = self.today.year
        self.month = self.today.month
        
        self.selected_date = self.today
        self.contacts_in_listbox = []
        
        self.setup_ui()

    def setup_ui(self):
        # Left pane: Calendar
        left_pane = tk.Frame(self, padx=10, pady=10)
        left_pane.pack(side="left", fill="both", expand=True)
        
        # Right pane: Details
        right_pane = tk.Frame(self, padx=10, pady=10, bg="#f5f6f8")
        right_pane.pack(side="right", fill="both", width=240)
        
        # Header in Left Pane
        header_frame = tk.Frame(left_pane)
        header_frame.pack(fill="x", pady=(0, 10))
        
        self.prev_btn = ttk.Button(header_frame, text="<", width=3, command=self.prev_month)
        self.prev_btn.pack(side="left")
        
        self.header_label = ttk.Label(header_frame, font=("Helvetica", 11, "bold"))
        self.header_label.pack(side="left", expand=True)
        
        self.next_btn = ttk.Button(header_frame, text=">", width=3, command=self.next_month)
        self.next_btn.pack(side="right")
        
        # Weekdays in Left Pane
        weeks_frame = tk.Frame(left_pane)
        weeks_frame.pack(fill="x")
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for day in days:
            lbl = ttk.Label(weeks_frame, text=day, width=4, anchor="center", font=("Helvetica", 9, "bold"))
            lbl.pack(side="left", expand=True)
            
        # Grid frame in Left Pane
        self.grid_frame = tk.Frame(left_pane)
        self.grid_frame.pack(fill="both", expand=True, pady=5)
        
        # Right pane components
        self.date_details_label = ttk.Label(right_pane, text="Contacts to Follow up", font=("Helvetica", 10, "bold"), background="#f5f6f8")
        self.date_details_label.pack(anchor="w", pady=(0, 5))
        
        self.contacts_listbox = tk.Listbox(right_pane, font=("Helvetica", 10))
        self.contacts_listbox.pack(fill="both", expand=True, pady=(0, 5))
        self.contacts_listbox.bind("<Double-Button-1>", self.on_double_click_contact)
        
        help_label = ttk.Label(right_pane, text="Double-click a contact\nto view in main window.", font=("Helvetica", 8, "italic"), foreground="gray", background="#f5f6f8")
        help_label.pack(anchor="w")
        
        self.draw_calendar()
        self.load_contacts_for_date(self.today)

    def get_followup_dates_for_month(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT latest_followup_date, COUNT(*) FROM contacts WHERE latest_followup_date LIKE ? GROUP BY latest_followup_date", (f"{self.year:04d}-{self.month:02d}-%",))
        
        dates_with_followups = {}
        for row in cursor.fetchall():
            if row[0]:
                dates_with_followups[row[0]] = row[1]
        return dates_with_followups

    def draw_calendar(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        self.header_label.config(text=f"{calendar.month_name[self.month]} {self.year}")
        
        cal = calendar.monthcalendar(self.year, self.month)
        dates_with_followups = self.get_followup_dates_for_month()
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    lbl = ttk.Label(self.grid_frame, text="")
                    lbl.grid(row=r, column=c, sticky="nsew", ipady=2)
                else:
                    btn_date = datetime.date(self.year, self.month, day)
                    date_str = btn_date.strftime("%Y-%m-%d")
                    
                    count = dates_with_followups.get(date_str, 0)
                    bg = "#ffffff"
                    fg = "black"
                    
                    if btn_date == self.today:
                        bg = "#f0f4f8"
                        fg = "#0056b3"
                        
                    if btn_date == self.selected_date:
                        bg = "#d1e7dd"
                        
                    text = f"{day}"
                    if count > 0:
                        text = f"{day}\n({count})"
                        if btn_date != self.selected_date:
                            bg = "#f8d7da"
                            fg = "#842029"
                            
                    btn = tk.Button(self.grid_frame, text=text, bg=bg, fg=fg, bd=1, relief="groove",
                                    font=("Helvetica", 9),
                                    command=lambda d=btn_date: self.select_day(d))
                    btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                    
        for i in range(7):
            self.grid_frame.columnconfigure(i, weight=1)
        for i in range(6):
            self.grid_frame.rowconfigure(i, weight=1)

    def select_day(self, date):
        self.selected_date = date
        self.draw_calendar()
        self.load_contacts_for_date(date)
        
    def load_contacts_for_date(self, date):
        self.contacts_listbox.delete(0, tk.END)
        self.date_details_label.config(text=f"Follow-ups for {date.strftime('%b %d, %Y')}:")
        
        date_str = date.strftime("%Y-%m-%d")
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name FROM contacts WHERE latest_followup_date = ? ORDER BY name", (date_str,))
        
        self.contacts_in_listbox = []
        for row in cursor.fetchall():
            self.contacts_listbox.insert(tk.END, row[0])
            self.contacts_in_listbox.append(row[0])
            
    def on_double_click_contact(self, event):
        selection = self.contacts_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx < len(self.contacts_in_listbox):
            contact_name = self.contacts_in_listbox[idx]
            self.on_select_contact_callback(contact_name)

    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.draw_calendar()
        
    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.draw_calendar()


class CRMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple CRM")
        self.root.geometry("650x500")
        self.root.configure(padx=10, pady=10)

        # Connect to local SQLite database using absolute path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crm_database.db")
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

        # Layout Setup
        left_frame = tk.Frame(root)
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        right_frame = tk.Frame(root)
        right_frame.pack(side="left", fill="both", expand=True)

        # Left Frame: Search, Summary, and Listbox
        ttk.Label(left_frame, text="Search Contacts:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search)
        self.search_entry = ttk.Entry(left_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(pady=(5, 5), fill="x")

        self.total_followups_var = tk.StringVar()
        self.total_followups_var.set("Total Follow-ups: 0")
        self.total_lbl = ttk.Label(left_frame, textvariable=self.total_followups_var, font=("Helvetica", 9, "bold"), foreground="#2c3e50")
        self.total_lbl.pack(pady=(2, 5), anchor="w")

        self.listbox = tk.Listbox(left_frame, width=25, font=("Helvetica", 10))
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_contact)
        
        ttk.Button(left_frame, text="Add New Contact", command=self.add_new_contact).pack(pady=(5, 0), fill="x")
        ttk.Button(left_frame, text="Delete Contact", command=self.delete_contact).pack(pady=(5, 0), fill="x")
        ttk.Button(left_frame, text="Export to CSV", command=self.export_to_csv).pack(pady=(5, 0), fill="x")
        ttk.Button(left_frame, text="📅 View Calendar", command=self.open_calendar_view).pack(pady=(5, 0), fill="x")

        # Right Frame: Edit Contact
        ttk.Label(right_frame, text="Name:", font=("Helvetica", 10, "bold")).pack(pady=(0, 5), anchor="w")
        self.name_var = tk.StringVar()
        self.name_var.trace_add('write', self.on_data_change)
        self.name_entry = ttk.Entry(right_frame, textvariable=self.name_var, font=("Helvetica", 10))
        self.name_entry.pack(pady=(0, 15), fill="x")

        ttk.Label(right_frame, text="Number:", font=("Helvetica", 10, "bold")).pack(pady=(0, 5), anchor="w")
        self.number_var = tk.StringVar()
        self.number_var.trace_add('write', self.on_data_change)
        self.number_entry = ttk.Entry(right_frame, textvariable=self.number_var, font=("Helvetica", 10))
        self.number_entry.pack(pady=(0, 15), fill="x")

        ttk.Label(right_frame, text="Passport Number:", font=("Helvetica", 10, "bold")).pack(pady=(0, 5), anchor="w")
        self.passport_var = tk.StringVar()
        self.passport_var.trace_add('write', self.on_data_change)
        self.passport_entry = ttk.Entry(right_frame, textvariable=self.passport_var, font=("Helvetica", 10))
        self.passport_entry.pack(pady=(0, 15), fill="x")

        # Follow-up Counter Frame
        followup_frame = tk.Frame(right_frame)
        followup_frame.pack(pady=(0, 15), fill="x")
        
        ttk.Label(followup_frame, text="Follow-ups:", font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 10))
        
        self.followup_var = tk.StringVar()
        self.followup_var.set("0")
        
        self.followup_label = ttk.Label(followup_frame, textvariable=self.followup_var, font=("Helvetica", 10, "bold"), width=5, anchor="center")
        self.followup_label.pack(side="left", padx=(0, 10))
        
        self.btn_inc = ttk.Button(followup_frame, text="+ Log Follow-up", width=15, command=self.increment_followup)
        self.btn_inc.pack(side="left", padx=(0, 5))
        
        self.btn_dec = ttk.Button(followup_frame, text="-", width=3, command=self.decrement_followup)
        self.btn_dec.pack(side="left", padx=(0, 5))
        
        self.btn_reset = ttk.Button(followup_frame, text="Reset", width=6, command=self.reset_followup)
        self.btn_reset.pack(side="left")

        # Latest Follow-up Date Frame
        date_frame = tk.Frame(right_frame)
        date_frame.pack(pady=(0, 15), fill="x")
        
        ttk.Label(date_frame, text="Latest Follow-up Date:", font=("Helvetica", 10, "bold")).pack(side="left", padx=(0, 10))
        
        self.latest_followup_var = tk.StringVar()
        self.latest_followup_var.trace_add('write', self.on_data_change)
        
        self.latest_followup_entry = ttk.Entry(date_frame, textvariable=self.latest_followup_var, width=15, font=("Helvetica", 10))
        self.latest_followup_entry.pack(side="left", padx=(0, 5))
        
        self.btn_calendar = ttk.Button(date_frame, text="📅 Select", width=10, command=self.open_calendar_picker)
        self.btn_calendar.pack(side="left")

        ttk.Label(right_frame, text="Notes:", font=("Helvetica", 10, "bold")).pack(pady=(0, 5), anchor="w")
        self.notes_text = tk.Text(right_frame, height=10, font=("Helvetica", 10))
        self.notes_text.pack(pady=(0, 15), fill="both", expand=True)
        self.notes_text.bind('<KeyRelease>', self.on_notes_change)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        ttk.Label(right_frame, textvariable=self.status_var, font=("Helvetica", 8, "italic"), foreground="gray").pack(anchor="w")

        # State Variables
        self.save_timer = None
        self.is_loading = False
        self.current_contact_id = None # Using the original name as ID if editing
        self.contact_names = [] # In-sync list of raw database names

        self.load_contacts()

    def create_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                name TEXT PRIMARY KEY,
                number TEXT,
                notes TEXT,
                follow_up_count INTEGER DEFAULT 0,
                passport_number TEXT,
                latest_followup_date TEXT
            )
        ''')
        # Backward compatibility checks
        cursor.execute("PRAGMA table_info(contacts)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'follow_up_count' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN follow_up_count INTEGER DEFAULT 0")
        if 'passport_number' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN passport_number TEXT")
        if 'latest_followup_date' not in columns:
            cursor.execute("ALTER TABLE contacts ADD COLUMN latest_followup_date TEXT")
        self.db_conn.commit()

    def load_contacts(self, search_query=""):
        self.listbox.delete(0, tk.END)
        self.contact_names = []
        cursor = self.db_conn.cursor()
        
        if search_query:
            cursor.execute("SELECT name, follow_up_count FROM contacts WHERE name LIKE ? ORDER BY name", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT name, follow_up_count FROM contacts ORDER BY name")
            
        for row in cursor.fetchall():
            name = row[0]
            count = row[1] if row[1] is not None else 0
            self.listbox.insert(tk.END, f"{name} ({count})")
            self.contact_names.append(name)
            
        self.update_total_followups()

    def on_search(self, *args):
        self.load_contacts(self.search_var.get().strip())

    def add_new_contact(self):
        self.is_loading = True
        self.current_contact_id = None
        self.listbox.selection_clear(0, tk.END)
        
        self.name_var.set("")
        self.number_var.set("")
        self.passport_var.set("")
        self.latest_followup_var.set("")
        self.notes_text.delete("1.0", tk.END)
        self.followup_var.set("0")
        self.status_var.set("Creating new contact...")
        self.name_entry.focus()
        self.is_loading = False

    def on_select_contact(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        idx = selection[0]
        if idx >= len(self.contact_names):
            return
        name = self.contact_names[idx]
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, number, notes, follow_up_count, passport_number, latest_followup_date FROM contacts WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            self.is_loading = True
            self.current_contact_id = row[0]
            self.name_var.set(row[0])
            self.number_var.set(row[1] if row[1] else "")
            self.passport_var.set(row[4] if row[4] else "")
            self.latest_followup_var.set(row[5] if row[5] else "")
            self.notes_text.delete("1.0", tk.END)
            if row[2]:
                self.notes_text.insert("1.0", row[2])
            self.followup_var.set(str(row[3] if row[3] is not None else 0))
            self.status_var.set(f"Loaded '{name}'")
            self.is_loading = False

    def on_data_change(self, *args):
        if not self.is_loading:
            self.schedule_save()

    def on_notes_change(self, event):
        if not self.is_loading:
            self.schedule_save()

    def schedule_save(self):
        if self.save_timer is not None:
            self.root.after_cancel(self.save_timer)
        self.status_var.set("Typing...")
        self.save_timer = self.root.after(800, self.save_data)

    def save_data(self):
        new_name = self.name_var.get().strip()
        if not new_name:
            self.status_var.set("Name cannot be empty.")
            return
            
        number = self.number_var.get().strip()
        passport = self.passport_var.get().strip()
        notes = self.notes_text.get("1.0", tk.END).strip()
        latest_followup = self.latest_followup_var.get().strip()
        try:
            followup = int(self.followup_var.get())
        except ValueError:
            followup = 0
        
        cursor = self.db_conn.cursor()
        
        try:
            if self.current_contact_id and self.current_contact_id != new_name:
                # Update existing record and change name
                cursor.execute('''
                    UPDATE contacts 
                    SET name = ?, number = ?, notes = ?, follow_up_count = ?, passport_number = ?, latest_followup_date = ?
                    WHERE name = ?
                ''', (new_name, number, notes, followup, passport, latest_followup, self.current_contact_id))
                self.current_contact_id = new_name
            else:
                # Insert or update
                cursor.execute('''
                    INSERT INTO contacts (name, number, notes, follow_up_count, passport_number, latest_followup_date) 
                    VALUES (?, ?, ?, ?, ?, ?) 
                    ON CONFLICT(name) DO UPDATE SET 
                    number=excluded.number, 
                    notes=excluded.notes,
                    follow_up_count=excluded.follow_up_count,
                    passport_number=excluded.passport_number,
                    latest_followup_date=excluded.latest_followup_date
                ''', (new_name, number, notes, followup, passport, latest_followup))
                self.current_contact_id = new_name
                
            self.db_conn.commit()
            self.status_var.set("Saved.")
            
            # Refresh listbox silently without losing selection
            current_search = self.search_var.get().strip()
            self.load_contacts(current_search)
            
            # Reselect the item
            for i in range(len(self.contact_names)):
                if self.contact_names[i] == new_name:
                    self.listbox.selection_set(i)
                    break
                    
        except sqlite3.IntegrityError:
            self.status_var.set("Error: Contact name already exists.")

    def delete_contact(self):
        from tkinter import messagebox
        
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a contact from the list to delete.")
            return
            
        idx = selection[0]
        if idx >= len(self.contact_names):
            return
        name = self.contact_names[idx]
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name}'?")
        if confirm:
            cursor = self.db_conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE name = ?", (name,))
            self.db_conn.commit()
            
            # Clear UI if the deleted contact was currently loaded
            if self.current_contact_id == name:
                self.is_loading = True
                self.name_var.set("")
                self.number_var.set("")
                self.passport_var.set("")
                self.latest_followup_var.set("")
                self.notes_text.delete("1.0", tk.END)
                self.followup_var.set("0")
                self.current_contact_id = None
                self.status_var.set(f"Deleted '{name}'")
                self.is_loading = False
                
            # Reload listbox
            self.load_contacts(self.search_var.get().strip())

    def export_to_csv(self):
        import csv
        from tkinter import messagebox
        
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, number, notes, follow_up_count, passport_number, latest_followup_date FROM contacts ORDER BY name")
        rows = cursor.fetchall()
        
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts_export.csv")
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Number", "Notes", "Follow-up Count", "Passport Number", "Latest Follow-up Date"])
                writer.writerows(rows)
            
            # Automatically open the CSV if on Windows
            if os.name == 'nt':
                os.startfile(csv_path)
            messagebox.showinfo("Export Successful", f"Exported {len(rows)} contacts to:\n{csv_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
 
    def increment_followup(self):
        if self.is_loading:
            return
        try:
            val = int(self.followup_var.get())
        except ValueError:
            val = 0
        self.followup_var.set(str(val + 1))
        
        # Set latest follow-up date to today
        self.latest_followup_var.set(datetime.date.today().strftime("%Y-%m-%d"))
        
        self.save_data()

    def open_calendar_picker(self):
        if self.is_loading:
            return
        initial = self.latest_followup_var.get().strip()
        CalendarDialog(self.root, initial_date=initial, callback=self.set_followup_date)

    def set_followup_date(self, date_str):
        self.latest_followup_var.set(date_str)
        self.save_data()

    def open_calendar_view(self):
        CalendarViewWindow(self.root, self.db_conn, self.select_contact_by_name)

    def select_contact_by_name(self, name):
        # Clear search filter to ensure the contact is loaded
        self.search_var.set("")
        self.load_contacts()
        
        # Find index in listbox
        for i, contact_name in enumerate(self.contact_names):
            if contact_name == name:
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(i)
                self.listbox.see(i)
                self.on_select_contact(None)
                break
        
    def decrement_followup(self):
        if self.is_loading:
            return
        try:
            val = int(self.followup_var.get())
        except ValueError:
            val = 0
        if val > 0:
            self.followup_var.set(str(val - 1))
            self.save_data()
            
    def reset_followup(self):
        if self.is_loading:
            return
        self.followup_var.set("0")
        self.save_data()

    def update_total_followups(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT SUM(coalesce(follow_up_count, 0)) FROM contacts")
        result = cursor.fetchone()
        total = result[0] if result[0] is not None else 0
        self.total_followups_var.set(f"Total Follow-ups: {total}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CRMApp(root)
    root.mainloop()
