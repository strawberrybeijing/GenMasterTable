from tkinter import *
from tkinter import ttk, filedialog, messagebox
from pandastable import Table, TableModel
import pandas as pd
import vcf  
import re
import os
import warnings
import numpy as np 
from tqdm import tqdm  

class MasterTableApp(Tk):
    def __init__(self):
        super().__init__()
        self.title('MasterTable App')
        self.geometry('1400x900+200+100')
        self.configure(bg='#f0f0f0')
        
        # Configure ttk style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Arial', 14), padding=5)
        self.style.configure('TLabel', font=('Arial', 14))
        self.style.configure('TEntry', font=('Arial', 14))
        self.style.configure('TFrame', background='#f0f0f0')

        # Create paned window
        self.paned_window = ttk.PanedWindow(self, orient=VERTICAL)
        self.paned_window.pack(fill=BOTH, expand=True)

        # Table Frame
        self.table_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.table_frame, weight=4)

        # Control Frame
        self.control_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.control_frame, weight=8)

        # Initialize Table with an empty DataFrame
        self.table = Table(self.table_frame, dataframe=pd.DataFrame(), 
                         showtoolbar=True, showstatusbar=True)
        self.table.show()

        # Create interface components
        self.create_file_controls()
        self.create_filter_controls()  

    def create_file_controls(self):
        """Create file operation controls"""
        file_frame = ttk.LabelFrame(self.control_frame, text="File Operations", padding=(10, 5))
        file_frame.pack(fill=X, expand=True, padx=10, pady=5)

        self.load_btn = ttk.Button(file_frame, text="Load/Merge CSV/VCF", 
                           command=self.load_merge_files, padding=0)
        self.load_btn.pack(fill=BOTH, expand=True, padx=5, pady=5, ipadx=10, ipady=10)

    def create_filter_controls(self):
        """Create filter controls with three separate filter sections"""
        filter_frame = ttk.LabelFrame(self.control_frame, text="Filters", padding=(10, 5))
        filter_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Configure grid weights for the filter_frame
        filter_frame.columnconfigure(0, weight=1)
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(2, weight=1)
        filter_frame.rowconfigure(1, weight=1)
        filter_frame.rowconfigure(2, weight=1)
        
        # Filter 1: Leftmost
        self.create_filter_section(filter_frame, row=0, column=0, label="Filter 1")
        
        # Filter 2: Middle
        self.create_filter_section(filter_frame, row=0, column=1, label="Filter 2")
        
        # Filter 3: Rightmost
        self.create_filter_section(filter_frame, row=0, column=2, label="Filter 3")
        
        # Button frame
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10, sticky='ew')
        
        self.apply_btn = ttk.Button(btn_frame, text="Apply Filters", 
                                    command=self.apply_filters)
        self.apply_btn.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        self.clear_btn = ttk.Button(btn_frame, text="Clear Filters", 
                                    command=self.clear_filters)
        self.clear_btn.pack(side=LEFT, padx=5, fill=X, expand=True)
        
        # Configure row weights
        filter_frame.rowconfigure(1, weight=1)
        filter_frame.rowconfigure(2, weight=1)
        
        self.control_frame.columnconfigure(0, weight=1)
        self.control_frame.rowconfigure(0, weight=1)
        self.control_frame.rowconfigure(1, weight=1)
    
    def create_filter_section(self, parent, row, column, label):
        """Create a filter section with a dropdown and entry box"""
        section_frame = ttk.Frame(parent)
        section_frame.grid(row=row, column=column, padx=10, pady=5, sticky='nsew')
        
        # Column selection dropdown
        ttk.Label(section_frame, text=f"{label} - Select Column:").grid(row=0, column=0, sticky='w', pady=2)
        combobox = ttk.Combobox(section_frame, font=('Arial', 14), state="readonly")
        combobox.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        # Filter values entry box 
        ttk.Label(section_frame, text="Filter Values (comma/space separated):").grid(row=2, column=0, sticky='w', pady=2)
        entry = ttk.Entry(section_frame, font=('Arial', 14))
        entry.grid(row=3, column=0, sticky='ew', padx=5, pady=5, ipady=10)  
        
        # Store widgets for later use
        if not hasattr(self, 'filter_sections'):
            self.filter_sections = []
        self.filter_sections.append({
            'combobox': combobox,
            'entry': entry
        })

    def populate_column_comboboxes(self):
        """Populate all column comboboxes with column names from the DataFrame"""
        if hasattr(self, 'MasterTable') and not self.MasterTable.empty:
            columns = self.MasterTable.columns.tolist()
            for section in self.filter_sections:
                section['combobox']['values'] = columns
                if columns:  
                    section['combobox'].current(0)

    def apply_filters(self):
        filtered_df = self.original_MasterTable.copy()

        # Apply filters from all sections
        for section in self.filter_sections:
            selected_column = section['combobox'].get()
            filter_values = section['entry'].get().strip()
            
            if selected_column and filter_values:
                filter_list = [value.strip() for value in re.split(r'[,\s]+', filter_values)]

                if selected_column in filtered_df.columns:
                    column_dtype = filtered_df[selected_column].dtype
                    
                    # Handle numeric columns (e.g., 'POS', 'Start')
                    if pd.api.types.is_numeric_dtype(column_dtype):
                        try:
                            filter_list = [float(value) if '.' in value else int(value) for value in filter_list]
                        except ValueError:
                            print(f"Warning: Could not convert filter values to numbers for column '{selected_column}'")
                            continue
                    
                    # Handle string/categorical columns
                    elif pd.api.types.is_string_dtype(column_dtype) or pd.api.types.is_categorical_dtype(column_dtype):
                        filter_list = [str(value) for value in filter_list]
                    
                    # Apply the filter
                    filtered_df = filtered_df[filtered_df[selected_column].isin(filter_list)]

        self.MasterTable = filtered_df
        self.update_table()

    def clear_filters(self):
        self.MasterTable = self.original_MasterTable.copy()
        
        # Clear all input fields
        for section in self.filter_sections:
            section['combobox'].set('')
            section['entry'].delete(0, END)
        self.update_table()

    def load_merge_files(self):
        try:
            filepaths = filedialog.askopenfilenames(
                parent=self,  
                title="Select CSV/VCF Files",
                filetypes=[("CSV files", "*.csv"), ("VCF files", "*.vcf"), ("VCF GZ files", "*.vcf.gz")]
            )
            if not filepaths:
                return

            print("Selected files:", filepaths)  

            file_extension = os.path.splitext(filepaths[0])[1].lower()
            
            if all(os.path.splitext(fp)[1].lower() == file_extension for fp in filepaths):
                if file_extension == ".csv":
                    self.load_merge_csv(filepaths)
                elif file_extension in [".vcf", ".gz"]:
                    self.load_merge_vcf(filepaths)
                else:
                    messagebox.showerror("Error", "Unsupported file type.")
            else:
                messagebox.showerror("Error", "All selected files must have the same extension (CSV or VCF).")
        except Exception as e:
            print("Error in load_merge_files:", e) 
            messagebox.showerror("Error", f"An error occurred: {e}")

    def load_merge_csv(self, filepaths):
        csv_data = []
        for filepath in filepaths:
            try:
                # Load CSV in chunks
                chunks = pd.read_csv(filepath, chunksize=100000, low_memory=False)
                df = pd.concat(chunks, ignore_index=True)
                df["File_Name"] = os.path.basename(filepath)
                csv_data.append(df)
            except Exception as e:
                print(f"Error loading CSV file {filepath}: {e}")
        
        if csv_data:
            self.MasterTable = pd.concat(csv_data, ignore_index=True)
            self.original_MasterTable = self.MasterTable.copy()
            self.populate_column_comboboxes()  
            self.update_table()
            self.title("MasterTable App - Merged CSV")

    def load_merge_vcf(self, filepaths):
        vcf_data = []
        for filepath in filepaths:
            try:
                # Parse VCF in batches and collect all batches into a single DataFrame
                vcf_df = pd.concat(self.parse_vcf(filepath), ignore_index=True)
                if not vcf_df.empty:
                    vcf_df["File_Name"] = os.path.basename(filepath)
                    vcf_data.append(vcf_df)
            except Exception as e:
                print(f"Error processing VCF file {filepath}: {e}")
        
        if vcf_data:
            self.MasterTable = pd.concat(vcf_data, ignore_index=True)
            self.original_MasterTable = self.MasterTable.copy()
            self.populate_column_comboboxes()  
            self.update_table()
            self.title("MasterTable App - Merged VCF")

    def parse_vcf(self, filepath, batch_size=1000):
        try:
            vcf_reader = vcf.Reader(filename=filepath)
            records = []
            for record in tqdm(vcf_reader, desc=f"Parsing {os.path.basename(filepath)}"):
                row = {
                    'Chrom': record.CHROM,
                    'Pos': record.POS,
                    'ID': record.ID if record.ID else '.',
                    'Ref': record.REF,
                    'Alt': ','.join(str(a) for a in record.ALT),
                    'Qual': record.QUAL,
                    'Filter': ';'.join(record.FILTER) if record.FILTER else 'PASS'
                }
                
                # Add INFO fields
                for key, value in record.INFO.items():
                    if isinstance(value, (list, tuple)):
                        row[key] = ', '.join(map(str, value))
                    else:
                        row[key] = str(value)
                
                # Add sample-specific fields (e.g., AD)
                if record.samples:
                    sample = record.samples[0]  # First sample
                    if 'AD' in sample.data:
                        row['AD'] = '|'.join(map(str, sample.data['AD']))
                
                records.append(row)
                
                # Process in batches
                if len(records) >= batch_size:
                    yield pd.DataFrame(records)
                    records = []
        
            if records:
                yield pd.DataFrame(records)
        except Exception as e:
            print("Error parsing VCF:", e)
            yield pd.DataFrame() 

    def update_table(self):
        self.table.updateModel(TableModel(self.MasterTable))
        self.table.redraw()

# good luck and have fun
app = MasterTableApp()
app.mainloop()