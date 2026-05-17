import tkinter as tk
from tkinter import ttk
import sqlite3
import os

class CRMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple CRM")
        self.root.geometry("600x450")
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

        # Left Frame: Search and Listbox
        ttk.Label(left_frame, text="Search Contacts:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.on_search)
        self.search_entry = ttk.Entry(left_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(pady=(5, 5), fill="x")

        self.listbox = tk.Listbox(left_frame, width=25, font=("Helvetica", 10))
        self.listbox.pack(fill="y", expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_contact)
        
        ttk.Button(left_frame, text="Add New Contact", command=self.add_new_contact).pack(pady=(5, 0), fill="x")
        ttk.Button(left_frame, text="Delete Contact", command=self.delete_contact).pack(pady=(5, 0), fill="x")
        ttk.Button(left_frame, text="Export to CSV", command=self.export_to_csv).pack(pady=(5, 0), fill="x")
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

        self.load_contacts()

    def create_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                name TEXT PRIMARY KEY,
                number TEXT,
                notes TEXT
            )
        ''')
        self.db_conn.commit()

    def load_contacts(self, search_query=""):
        self.listbox.delete(0, tk.END)
        cursor = self.db_conn.cursor()
        
        if search_query:
            cursor.execute("SELECT name FROM contacts WHERE name LIKE ? ORDER BY name", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT name FROM contacts ORDER BY name")
            
        for row in cursor.fetchall():
            self.listbox.insert(tk.END, row[0])

    def on_search(self, *args):
        self.load_contacts(self.search_var.get().strip())

    def add_new_contact(self):
        self.is_loading = True
        self.current_contact_id = None
        self.listbox.selection_clear(0, tk.END)
        
        self.name_var.set("")
        self.number_var.set("")
        self.notes_text.delete("1.0", tk.END)
        self.status_var.set("Creating new contact...")
        self.name_entry.focus()
        self.is_loading = False

    def on_select_contact(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        name = self.listbox.get(selection[0])
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, number, notes FROM contacts WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            self.is_loading = True
            self.current_contact_id = row[0]
            self.name_var.set(row[0])
            self.number_var.set(row[1] if row[1] else "")
            self.notes_text.delete("1.0", tk.END)
            if row[2]:
                self.notes_text.insert("1.0", row[2])
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
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        cursor = self.db_conn.cursor()
        
        try:
            if self.current_contact_id and self.current_contact_id != new_name:
                # Update existing record and change name
                cursor.execute('''
                    UPDATE contacts 
                    SET name = ?, number = ?, notes = ?
                    WHERE name = ?
                ''', (new_name, number, notes, self.current_contact_id))
                self.current_contact_id = new_name
            else:
                # Insert or update
                cursor.execute('''
                    INSERT INTO contacts (name, number, notes) 
                    VALUES (?, ?, ?) 
                    ON CONFLICT(name) DO UPDATE SET 
                    number=excluded.number, 
                    notes=excluded.notes
                ''', (new_name, number, notes))
                self.current_contact_id = new_name
                
            self.db_conn.commit()
            self.status_var.set("Saved.")
            
            # Refresh listbox silently without losing selection
            current_search = self.search_var.get().strip()
            self.load_contacts(current_search)
            
            # Reselect the item
            for i in range(self.listbox.size()):
                if self.listbox.get(i) == new_name:
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
            
        name = self.listbox.get(selection[0])
        
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
                self.notes_text.delete("1.0", tk.END)
                self.current_contact_id = None
                self.status_var.set(f"Deleted '{name}'")
                self.is_loading = False
                
            # Reload listbox
            self.load_contacts(self.search_var.get().strip())

    def export_to_csv(self):
        import csv
        from tkinter import messagebox
        
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name, number, notes FROM contacts ORDER BY name")
        rows = cursor.fetchall()
        
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contacts_export.csv")
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Number", "Notes"])
                writer.writerows(rows)
            
            # Automatically open the CSV if on Windows
            if os.name == 'nt':
                os.startfile(csv_path)
            messagebox.showinfo("Export Successful", f"Exported {len(rows)} contacts to:\n{csv_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = CRMApp(root)
    root.mainloop()
