import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
import io

class OverloadPayCalculator:
    def __init__(self):
        # Variables with default values
        self.school_name = ""
        self.num_weeks = 4
        self.pay_rate = 1.25
        self.show_only_nonzero = False
        
        # Data storage
        self.data = None
        self.processed_data = None
        self.staff_totals = None
        self.grand_total = {"total_overload": 0, "overload_pay": 0}
    
    def process_data(self, file, school_name, num_weeks, pay_rate, show_only_nonzero):
        try:
            # Update instance variables
            self.school_name = school_name
            self.num_weeks = num_weeks
            self.pay_rate = pay_rate
            self.show_only_nonzero = show_only_nonzero
            
            # Read CSV file
            self.data = pd.read_csv(file)
            
            # Check required columns
            required_cols = ["Course Title", "Staff Name", "Total Students"]
            missing_cols = [col for col in required_cols if col not in self.data.columns]
            
            if missing_cols:
                return False, f"The CSV file is missing required columns: {', '.join(missing_cols)}"
            
            # Filter for required courses and students > 0
            course_mask = (
                self.data["Course Title"].str.contains("MUSIC|PHYS ED|ART|CREATIVE", case=False, na=False) &
                (self.data["Total Students"] > 0)
            )
            relevant_courses = self.data[course_mask].copy()
            
            if relevant_courses.empty:
                return False, "No MUSIC, PHYS ED, ART, or CREATIVE courses with students > 0 found in the file."
            
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
                overload_pay = total_overload * self.pay_rate * self.num_weeks
                
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
            
            return True, "Data processed successfully"
            
        except Exception as e:
            return False, f"An error occurred while processing the file: {str(e)}"
    
    def get_download_link_csv(self):
        """Generates a download link for the CSV export"""
        if not hasattr(self, 'processed_df'):
            return None
            
        # Filter data if nonzero option is selected
        export_data = self.processed_df
        if self.show_only_nonzero:
            export_data = export_data[export_data["Total Overload"] > 0]
        
        # Create a copy of the DataFrame for export
        export_df = export_data.copy()
        
        # Format the Overload Pay column with dollar signs
        export_df["Overload Pay"] = export_df["Overload Pay"].apply(lambda x: f"${x:.2f}")
        
        # Create final DataFrame for export with staff totals
        final_data = []
        current_staff = None
        
        # Create a copy of staff totals for formatting
        staff_totals_df = self.staff_totals.copy()
        staff_totals_df["Overload Pay"] = staff_totals_df["Overload Pay"].apply(lambda x: f"${x:.2f}")
        
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
        
        # Convert to DataFrame
        final_df = pd.DataFrame(final_data)
        
        # Generate CSV
        csv = final_df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        filename = f"{self.school_name or 'School'}_Overload_Pay.csv"
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
        return href
    
    def get_download_link_html(self):
        """Generates a download link for the HTML report"""
        if not hasattr(self, 'processed_df'):
            return None
            
        # Filter data if nonzero option is selected
        display_data = self.processed_df
        if self.show_only_nonzero:
            display_data = display_data[display_data["Total Overload"] > 0]
            
        # Start building HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.school_name or 'School'} Overload Pay Report</title>
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
            <h1>{self.school_name or 'School'} Overload Pay Report</h1>
            <p>Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
            
            <div class="notice">
                <h3>Calculation Parameters:</h3>
                <p>Payment Period: <strong>{self.num_weeks} week{'s' if self.num_weeks != 1 else ''}</strong></p>
                <p>Pay Rate: <strong>${self.pay_rate:.2f}</strong> per overload student per week</p>
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
                    <li>Payment calculation: Overload Students × ${self.pay_rate:.2f} × {self.num_weeks} week{'s' if self.num_weeks != 1 else ''}</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        # Create download link
        b64 = base64.b64encode(html_content.encode()).decode()
        filename = f"{self.school_name or 'School'}_Overload_Pay_Report.html"
        href = f'<a href="data:text/html;base64,{b64}" download="{filename}">Download HTML Report</a>'
        return href


def main():
    st.set_page_config(
        page_title="Elementary School Overload Pay Calculator",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("Elementary School Overload Pay Calculator")
    st.markdown("Upload a class roster CSV file to calculate teacher overload pay based on class sizes.")
    
    # Create calculator instance
    calculator = OverloadPayCalculator()
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Settings")
        
        uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
        
        # Extract school name from filename
        school_name = ""
        if uploaded_file is not None:
            filename = uploaded_file.name
            name_without_ext = os.path.splitext(filename)[0]
            # Clean up common suffixes
            for suffix in ["_roster", "_classes", "_data", "_overload"]:
                name_without_ext = name_without_ext.replace(suffix, "")
            school_name = name_without_ext.replace("_", " ").title()
        
        school_name = st.text_input("School Name", value=school_name)
        num_weeks = st.number_input("Number of Weeks", min_value=1, max_value=52, value=4)
        pay_rate = st.number_input("Pay Rate ($)", min_value=0.01, value=1.25, format="%.2f")
        show_only_nonzero = st.checkbox("Show only courses with overload", value=False)
        
        # Add a description about file format
        st.markdown("---")
        st.caption("File must include columns for Course Title, Staff Name, and Total Students.")
    
    # Main content
    if uploaded_file is not None:
        # Process button
        if st.button("Calculate Overload Pay", type="primary"):
            success, message = calculator.process_data(
                uploaded_file, 
                school_name, 
                num_weeks, 
                pay_rate, 
                show_only_nonzero
            )
            
            if success:
                st.success(message)
                
                # Display information about calculation
                st.markdown("### Calculation Details")
                st.markdown(f"""
                - Calculation Method: Overload Pay = Overload Students × ${pay_rate:.2f} × {num_weeks} week{'s' if num_weeks != 1 else ''}
                - Base Student thresholds: MIXED/1/2/3 = 23 students, 4/5 = 26 students, KINDER/K = 22 students
                - Total Overload Students: {int(calculator.grand_total['total_overload'])}, Total Overload Pay: ${calculator.grand_total['overload_pay']:.2f}
                """)
                
                # Create tabs for different views
                tab1, tab2 = st.tabs(["Detailed Results", "Summary by Teacher"])
                
                # Tab 1: Detailed Results
                with tab1:
                    # Display data
                    display_data = calculator.processed_df
                    
                    # Filter for non-zero overload if the option is selected
                    if show_only_nonzero:
                        display_data = display_data[display_data["Total Overload"] > 0]
                    
                    # Highlight rows with overload
                    def highlight_overload(row):
                        if row["Total Overload"] > 0:
                            return ['background-color: #ffeded'] * len(row)
                        return [''] * len(row)
                    
                    # Format the Overload Pay column with dollar signs
                    display_data_formatted = display_data.copy()
                    display_data_formatted["Overload Pay"] = display_data_formatted["Overload Pay"].apply(lambda x: f"${x:.2f}")
                    
                    # Display the table with highlighting
                    st.dataframe(
                        display_data_formatted.style.apply(highlight_overload, axis=1),
                        use_container_width=True
                    )
                
                # Tab 2: Summary by Teacher
                with tab2:
                    # Create a formatted copy of staff totals
                    staff_totals_formatted = calculator.staff_totals.copy()
                    staff_totals_formatted["Overload Pay"] = staff_totals_formatted["Overload Pay"].apply(lambda x: f"${x:.2f}")
                    
                    # Display the table
                    st.dataframe(
                        staff_totals_formatted,
                        use_container_width=True
                    )
                    
                    # Display grand total
                    st.markdown(f"""
                    **GRAND TOTAL:**  
                    Total Overload Students: **{int(calculator.grand_total['total_overload'])}**  
                    Total Overload Pay: **${calculator.grand_total['overload_pay']:.2f}**
                    """)
                
                # Download links
                st.markdown("### Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_link = calculator.get_download_link_csv()
                    if csv_link:
                        st.markdown(csv_link, unsafe_allow_html=True)
                
                with col2:
                    html_link = calculator.get_download_link_html()
                    if html_link:
                        st.markdown(html_link, unsafe_allow_html=True)
            
            else:
                st.error(message)
    else:
        # Show placeholder when no file is uploaded
        st.info("Please upload a CSV file to begin.")
        
        # Add demo image or instructions
        st.markdown("""
        ### CSV File Format
        Your CSV file should contain at least these columns:
        - **Course Title**: The name of the course (must include MUSIC, PHYS ED, ART, or CREATIVE to be counted)
        - **Staff Name**: The teacher's name
        - **Total Students**: The number of students in the class
        
        The calculator will automatically determine the base student threshold based on course titles:
        - MIXED/1/2/3: 23 students
        - 4/5: 26 students
        - KINDER/K: 22 students
        """)

if __name__ == "__main__":
    main()
