import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import webbrowser
from datetime import datetime
import tempfile

class OverloadPayCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Elementary School Overload Pay Calculator")
        self.root.geometry("800x650")
        self.root.minsize(800, 650)
       
        # Variables
        self.file_path = tk.StringVar()
        self.school_name = tk.StringVar()
        self.num_weeks = tk.IntVar(value=4)
        self.pay_rate = tk.DoubleVar(value=1.25)
        self.show_only_nonzero = tk.BooleanVar(value=False)
       
        # Data storage
        self.data = None
        self.processed_data = None
        self.staff_totals = None
        self.grand_total = {"total_overload": 0, "overload_pay": 0}
       
        # Create UI
        self.create_ui()
   
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
       
        # Title
        title_label = ttk.Label(main_frame,
                               text="Elementary School Overload Pay Calculator",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10), anchor="w")
       
        # Description
        desc_label = ttk.Label(main_frame,
                              text="Upload a class roster CSV file to calculate teacher overload pay based on class sizes.",
                              wraplength=760)
        desc_label.pack(pady=(0, 20), anchor="w")
       
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Input Settings", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 20))
       
        # School name
        school_label = ttk.Label(input_frame, text="School Name:")
        school_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        school_entry = ttk.Entry(input_frame, textvariable=self.school_name, width=30)
        school_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
       
        # Number of weeks
        weeks_label = ttk.Label(input_frame, text="Number of Weeks:")
        weeks_label.grid(row=0, column=2, sticky="w", padx=(20, 5), pady=5)
        weeks_entry = ttk.Spinbox(input_frame, from_=1, to=5, textvariable=self.num_weeks, width=5)
        weeks_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
       
        # Pay rate
        rate_label = ttk.Label(input_frame, text="Pay Rate ($):")
        rate_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        rate_entry = ttk.Entry(input_frame, textvariable=self.pay_rate, width=10)
        rate_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
       
        # Show only nonzero checkbox
        nonzero_check = ttk.Checkbutton(input_frame,
                                       text="Show only courses with overload",
                                       variable=self.show_only_nonzero)
        nonzero_check.grid(row=1, column=2, columnspan=2, sticky="w", padx=(20, 5), pady=5)
       
        # File selection
        file_frame = ttk.Frame(input_frame)
        file_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
       
        file_label = ttk.Label(file_frame, text="CSV File:")
        file_label.pack(side=tk.LEFT, padx=(0, 5))
       
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
       
        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side=tk.LEFT)
       
        # Instruction note
        note_label = ttk.Label(input_frame,
                             text="File must include columns for Course Title, Staff Name, and Total Students.",
                             font=("Arial", 9, "italic"), foreground="gray")
        note_label.grid(row=3, column=0, columnspan=4, sticky="w", padx=5, pady=(0, 5))
       
        # Process button
        process_frame = ttk.Frame(main_frame)
        process_frame.pack(fill=tk.X, pady=(0, 10))
       
        process_button = ttk.Button(process_frame,
                                   text="Calculate Overload Pay",
                                   command=self.process_data,
                                   style="Accent.TButton")
        process_button.pack(side=tk.LEFT)
       
        # Output frame (initially hidden, will be shown after processing)
        self.output_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
       
        # Results frame for preview table
        self.results_frame = ttk.Frame(self.output_frame)
       
        # Buttons frame
        buttons_frame = ttk.Frame(self.output_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
       
        export_button = ttk.Button(buttons_frame,
                                  text="Export to CSV",
                                  command=self.export_to_csv)
        export_button.pack(side=tk.LEFT, padx=(0, 10))
       
        html_button = ttk.Button(buttons_frame,
                                text="Generate HTML Report",
                                command=self.generate_html_report)
        html_button.pack(side=tk.LEFT)
       
        # Create custom style for the accent button
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
   
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
           
            # Try to extract school name from filename if not already set
            if not self.school_name.get():
                base_name = os.path.basename(filename)
                name_without_ext = os.path.splitext(base_name)[0]
                # Clean up common suffixes
                for suffix in ["_roster", "_classes", "_data", "_overload"]:
                    name_without_ext = name_without_ext.replace(suffix, "")
                self.school_name.set(name_without_ext.replace("_", " ").title())
   
    def process_data(self):
        # Validate inputs
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a CSV file.")
            return
       
        try:
            # Read CSV file
            self.data = pd.read_csv(self.file_path.get())
           
            # Check required columns
            required_cols = ["Course Title", "Staff Name", "Total Students"]
            missing_cols = [col for col in required_cols if col not in self.data.columns]
           
            if missing_cols:
                messagebox.showerror(
                    "Missing Columns",
                    f"The CSV file is missing required columns: {', '.join(missing_cols)}"
                )
                return
           
            # Filter for required courses and students > 0
            course_mask = (
                self.data["Course Title"].str.contains("MUSIC|PHYS ED|ART|CREATIVE", case=False, na=False) &
                (self.data["Total Students"] > 0)
            )
            relevant_courses = self.data[course_mask].copy()
           
            if relevant_courses.empty:
                messagebox.showinfo(
                    "No Relevant Data",
                    "No MUSIC, PHYS ED, ART, or CREATIVE courses with students > 0 found in the file."
                )
                return
           
            # Process the data
            self.processed_data = []
           
            for _, row in relevant_courses.iterrows():
                # Determine base students based on course title
                course_title = str(row["Course Title"]).upper()
               
                if ("MIXED" in course_title or
                    " 1" in course_title or
                    " 2" in course_title or
                    " 3" in course_title):
                    base_students = 23
                elif " 4" in course_title or " 5" in course_title:
                    base_students = 26
                elif "KINDER" in course_title or " K" in course_title:
                    base_students = 22
                else:
                    base_students = 23  # Default
               
                # Calculate overload
                total_overload = max(0, row["Total Students"] - base_students)
               
                # Calculate overload pay
                overload_pay = total_overload * self.pay_rate.get() * self.num_weeks.get()
               
                # Add to processed data
                processed_row = {
                    "Year": row.get("Year", ""),
                    "Organization": row.get("Organization", ""),
                    "Course Title": row["Course Title"],
                    "Staff Name": row["Staff Name"],
                    "Total Students": row["Total Students"],
                    "Base Students": base_students,
                    "Total Overload": total_overload,
                    "Overload Pay": round(overload_pay, 2)
                }
                self.processed_data.append(processed_row)
           
            # Convert to DataFrame and sort by Staff Name
            self.processed_df = pd.DataFrame(self.processed_data)
            self.processed_df = self.processed_df.sort_values("Staff Name")
           
            # Calculate staff totals
            self.staff_totals = self.processed_df.groupby("Staff Name").agg({
                "Total Overload": "sum",
                "Overload Pay": "sum"
            }).reset_index()
           
            # Calculate grand total
            self.grand_total = {
                "total_overload": self.staff_totals["Total Overload"].sum(),
                "overload_pay": self.staff_totals["Overload Pay"].sum()
            }
           
            # Display results
            self.display_results()
           
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while processing the file: {str(e)}")
   
    def display_results(self):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
       
        # Show the output frame if it's not already visible
        if not self.output_frame.winfo_ismapped():
            self.output_frame.pack(fill=tk.BOTH, expand=True)
            self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
       
        # Create a notebook for tabs
        notebook = ttk.Notebook(self.results_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
       
        # Display data
        display_data = self.processed_df
       
        # Filter for non-zero overload if the option is selected
        if self.show_only_nonzero.get():
            display_data = display_data[display_data["Total Overload"] > 0]
       
        # Create Detailed Results tab
        detailed_frame = ttk.Frame(notebook)
        notebook.add(detailed_frame, text="Detailed Results")
       
        # Create treeview for detailed data
        detailed_tree = ttk.Treeview(
            detailed_frame,
            columns=("Year", "Organization", "Course Title", "Staff Name",
                    "Total Students", "Base Students", "Total Overload", "Overload Pay"),
            show="headings"
        )
       
        # Set column headings
        detailed_tree.heading("Year", text="Year")
        detailed_tree.heading("Organization", text="Organization")
        detailed_tree.heading("Course Title", text="Course Title")
        detailed_tree.heading("Staff Name", text="Staff Name")
        detailed_tree.heading("Total Students", text="Total Students")
        detailed_tree.heading("Base Students", text="Base Students")
        detailed_tree.heading("Total Overload", text="Total Overload")
        detailed_tree.heading("Overload Pay", text="Overload Pay")
       
        # Set column widths
        detailed_tree.column("Year", width=60)
        detailed_tree.column("Organization", width=150)
        detailed_tree.column("Course Title", width=150)
        detailed_tree.column("Staff Name", width=150)
        detailed_tree.column("Total Students", width=100)
        detailed_tree.column("Base Students", width=100)
        detailed_tree.column("Total Overload", width=100)
        detailed_tree.column("Overload Pay", width=100)
       
        # Add data to treeview
        current_staff = None
        for _, row in display_data.iterrows():
            # If we have a new staff member, add a separator
            if current_staff is not None and current_staff != row["Staff Name"]:
                detailed_tree.insert("", tk.END, values=["", "", "", "", "", "", "", ""])
           
            # Insert the row data
            values = [
                row["Year"],
                row["Organization"],
                row["Course Title"],
                row["Staff Name"],
                row["Total Students"],
                row["Base Students"],
                row["Total Overload"],
                f"${row['Overload Pay']:.2f}"
            ]
            item_id = detailed_tree.insert("", tk.END, values=values)
           
            # Highlight rows with overload
            if row["Total Overload"] > 0:
                detailed_tree.item(item_id, tags=("overload",))
           
            current_staff = row["Staff Name"]
       
        # Configure tag for highlighting
        detailed_tree.tag_configure("overload", background="#ffeded")
       
        # Add scrollbar
        detailed_scroll = ttk.Scrollbar(detailed_frame, orient="vertical", command=detailed_tree.yview)
        detailed_tree.configure(yscrollcommand=detailed_scroll.set)
       
        # Pack treeview and scrollbar
        detailed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detailed_scroll.pack(side=tk.RIGHT, fill=tk.Y)
       
        # Create Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary by Teacher")
       
        # Create treeview for summary
        summary_tree = ttk.Treeview(
            summary_frame,
            columns=("Staff Name", "Total Overload", "Overload Pay"),
            show="headings"
        )
       
        # Set column headings
        summary_tree.heading("Staff Name", text="Staff Name")
        summary_tree.heading("Total Overload", text="Total Overload")
        summary_tree.heading("Overload Pay", text="Overload Pay")
       
        # Set column widths
        summary_tree.column("Staff Name", width=200)
        summary_tree.column("Total Overload", width=150)
        summary_tree.column("Overload Pay", width=150)
       
        # Add data to treeview
        for _, row in self.staff_totals.iterrows():
            values = [
                row["Staff Name"],
                int(row["Total Overload"]),
                f"${row['Overload Pay']:.2f}"
            ]
            item_id = summary_tree.insert("", tk.END, values=values)
           
            # Highlight rows with overload
            if row["Total Overload"] > 0:
                summary_tree.item(item_id, tags=("overload",))
       
        # Add grand total row
        grand_total_id = summary_tree.insert(
            "", tk.END,
            values=["TOTAL",
                   int(self.grand_total["total_overload"]),
                   f"${self.grand_total['overload_pay']:.2f}"]
        )
        summary_tree.item(grand_total_id, tags=("grand_total",))
       
        # Configure tags for highlighting
        summary_tree.tag_configure("overload", background="#ffeded")
        summary_tree.tag_configure("grand_total", font=("Arial", 10, "bold"), background="#e6f2ff")
       
        # Add scrollbar
        summary_scroll = ttk.Scrollbar(summary_frame, orient="vertical", command=summary_tree.yview)
        summary_tree.configure(yscrollcommand=summary_scroll.set)
       
        # Pack treeview and scrollbar
        summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
       
        # Show calculation details
        info_frame = ttk.Frame(self.output_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
       
        info_text = (
            f"Calculation Method: Overload Pay = Overload Students × ${self.pay_rate.get():.2f} × "
            f"{self.num_weeks.get()} week{'s' if self.num_weeks.get() != 1 else ''}\n"
            f"Base Student thresholds: MIXED/1/2/3 = 23 students, 4/5 = 26 students, KINDER/K = 22 students\n"
            f"Total Overload Students: {int(self.grand_total['total_overload'])}, "
            f"Total Overload Pay: ${self.grand_total['overload_pay']:.2f}"
        )
       
        info_label = ttk.Label(info_frame, text=info_text, wraplength=760)
        info_label.pack(anchor="w")
   
    def export_to_csv(self):
        if self.processed_df is None:
            messagebox.showerror("Error", "No data to export. Please process a file first.")
            return
       
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"{self.school_name.get() or 'School'}_Overload_Pay.csv"
        )
       
        if not filename:
            return
       
        try:
            # Filter data if nonzero option is selected
            export_data = self.processed_df
            if self.show_only_nonzero.get():
                export_data = export_data[export_data["Total Overload"] > 0]
           
            # Create a copy of the DataFrame for export
            export_df = export_data.copy()
           
            # Format the Overload Pay column with dollar signs
            export_df["Overload Pay"] = export_df["Overload Pay"].apply(lambda x: f"${x:.2f}")
           
            # Create a DataFrame for staff totals
            staff_totals_df = self.staff_totals.copy()
            staff_totals_df["Overload Pay"] = staff_totals_df["Overload Pay"].apply(lambda x: f"${x:.2f}")
           
            # Add blank rows and total rows
            final_data = []
            current_staff = None
           
            # Iterate through the sorted rows
            for _, row in export_df.iterrows():
                if current_staff is not None and current_staff != row["Staff Name"]:
                    # Add total row for previous staff
                    total_row = {col: "" for col in export_df.columns}
                    total_row["Course Title"] = "TOTAL"
                    total_row["Staff Name"] = current_staff
                    staff_total = staff_totals_df[staff_totals_df["Staff Name"] == current_staff].iloc[0]
                    total_row["Total Overload"] = staff_total["Total Overload"]
                    total_row["Overload Pay"] = staff_total["Overload Pay"]
                    final_data.append(total_row)
                   
                    # Add blank row
                    blank_row = {col: "" for col in export_df.columns}
                    final_data.append(blank_row)
               
                # Add the current data row
                final_data.append(row.to_dict())
                current_staff = row["Staff Name"]
           
            # Add total for the last staff member
            if current_staff is not None:
                total_row = {col: "" for col in export_df.columns}
                total_row["Course Title"] = "TOTAL"
                total_row["Staff Name"] = current_staff
                staff_total = staff_totals_df[staff_totals_df["Staff Name"] == current_staff].iloc[0]
                total_row["Total Overload"] = staff_total["Total Overload"]
                total_row["Overload Pay"] = staff_total["Overload Pay"]
                final_data.append(total_row)
           
            # Convert to DataFrame and export
            final_df = pd.DataFrame(final_data)
            final_df.to_csv(filename, index=False)
           
            messagebox.showinfo("Export Successful", f"Data exported successfully to {filename}")
           
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred while exporting: {str(e)}")
   
    def generate_html_report(self):
        if self.processed_df is None:
            messagebox.showerror("Error", "No data to export. Please process a file first.")
            return
       
        try:
            # Filter data if nonzero option is selected
            display_data = self.processed_df
            if self.show_only_nonzero.get():
                display_data = display_data[display_data["Total Overload"] > 0]
           
            # Start building HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{self.school_name.get() or 'School'} Overload Pay Report</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.4;
                    }}
                    h1, h2, h3 {{
                        color: #333;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin-bottom: 30px;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                    }}
                    th {{
                        background-color: #2c5f9b;
                        color: white;
                        font-weight: bold;
                        text-align: left;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f2f2f2;
                    }}
                    tr:hover {{
                        background-color: #ddd;
                    }}
                    .total-row {{
                        font-weight: bold;
                        background-color: #e6eeff !important;
                    }}
                    .money {{
                        text-align: right;
                    }}
                    .staff-section {{
                        margin-bottom: 30px;
                    }}
                    .summary-table {{
                        width: 50%;
                        margin: 20px 0;
                    }}
                    .overload-highlight {{
                        background-color: #ffe6e6;
                    }}
                    .notice {{
                        background-color: #e6f2ff;
                        border: 1px solid #b3d9ff;
                        padding: 10px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <h1>{self.school_name.get() or 'School'} Overload Pay Report</h1>
                <p>Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
               
                <div class="notice">
                    <h3>Calculation Parameters:</h3>
                    <p>Payment Period: <strong>{self.num_weeks.get()} week{'s' if self.num_weeks.get() != 1 else ''}</strong></p>
                    <p>Pay Rate: <strong>${self.pay_rate.get():.2f}</strong> per overload student per week</p>
                    <p>Base Student thresholds: MIXED/1/2/3 = 23 students, 4/5 = 26 students, KINDER/K = 22 students</p>
                </div>
            """
           
            # Group data by staff name
            staff_groups = {}
            for _, row in display_data.iterrows():
                staff_name = row["Staff Name"]
                if staff_name not in staff_groups:
                    staff_groups[staff_name] = []
                staff_groups[staff_name].append(row)
           
            # Add staff sections
            for staff_name, rows in staff_groups.items():
                html_content += f"""
                <div class="staff-section">
                    <h3>{staff_name}</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Year</th>
                                <th>Organization</th>
                                <th>Course Title</th>
                                <th>Total Students</th>
                                <th>Base Students</th>
                                <th>Total Overload</th>
                                <th>Overload Pay</th>
                            </tr>
                        </thead>
                        <tbody>
                """
               
                # Add rows for this staff
                staff_total_overload = 0
                staff_total_pay = 0
               
                for row in rows:
                    overload = row["Total Overload"]
                    pay = row["Overload Pay"]
                    staff_total_overload += overload
                    staff_total_pay += pay
                   
                    highlight = ' class="overload-highlight"' if overload > 0 else ''
                   
                    html_content += f"""
                        <tr{highlight}>
                            <td>{row["Year"]}</td>
                            <td>{row["Organization"]}</td>
                            <td>{row["Course Title"]}</td>
                            <td>{row["Total Students"]}</td>
                            <td>{row["Base Students"]}</td>
                            <td>{overload}</td>
                            <td class="money">${pay:.2f}</td>
                        </tr>
                    """
               
                # Add total row for this staff
                html_content += f"""
                        <tr class="total-row">
                            <td colspan="4">TOTAL</td>
                            <td></td>
                            <td>{staff_total_overload}</td>
                            <td class="money">${staff_total_pay:.2f}</td>
                        </tr>
                        </tbody>
                    </table>
                </div>
                """
           
            # Add summary table
            html_content += """
                <h2>Summary of Teacher Overload Pay</h2>
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th>Staff Name</th>
                            <th>Total Overload</th>
                            <th>Overload Pay</th>
                        </tr>
                    </thead>
                    <tbody>
            """
           
            for _, row in self.staff_totals.iterrows():
                highlight = ' class="overload-highlight"' if row["Total Overload"] > 0 else ''
                html_content += f"""
                    <tr{highlight}>
                        <td>{row["Staff Name"]}</td>
                        <td>{int(row["Total Overload"])}</td>
                        <td class="money">${row["Overload Pay"]:.2f}</td>
                    </tr>
                """
           
            # Add grand total
            html_content += f"""
                    <tr class="total-row">
                        <td><strong>DISTRICT TOTAL</strong></td>
                        <td><strong>{int(self.grand_total["total_overload"])}</strong></td>
                        <td class="money"><strong>${self.grand_total["overload_pay"]:.2f}</strong></td>
                    </tr>
                    </tbody>
                </table>
               
                <div class="notice">
                    <p><strong>Notes:</strong></p>
                    <ul>
                        <li>This report only includes MUSIC, PHYS ED, ART, and CREATIVE courses with students > 0</li>
                        <li>Rows highlighted in pink indicate courses with overload students</li>
                        <li>Payment calculation: Overload Students × ${self.pay_rate.get():.2f} × {self.num_weeks.get()} week{'s' if self.num_weeks.get() != 1 else ''}</li>
                    </ul>
                </div>
            </body>
            </html>
            """
           
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as f:
                f.write(html_content)
                temp_file_path = f.name
           
            # Open the HTML file in the default browser
            webbrowser.open('file://' + os.path.abspath(temp_file_path))
           
            # Ask if user wants to save the HTML file
            if messagebox.askyesno("Save HTML Report", "Would you like to save this HTML report to a file?"):
                # Ask for save location
                filename = filedialog.asksaveasfilename(
                    title="Save HTML Report",
                    defaultextension=".html",
                    filetypes=[("HTML Files", "*.html"), ("All Files", "*.*")],
                    initialfile=f"{self.school_name.get() or 'School'}_Overload_Pay_Report.html"
                )
               
                if filename:
                    with open(filename, 'w') as f:
                        f.write(html_content)
                    messagebox.showinfo("Save Successful", f"Report saved to {filename}")
           
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred generating the HTML report: {str(e)}")
           
if __name__ == "__main__":
    root = tk.Tk()
    app = OverloadPayCalculator(root)
    root.mainloop()