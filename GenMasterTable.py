from tkinter import *
from tkinter import ttk, filedialog, messagebox
from pandastable import Table, TableModel
import pandas as pd
import vcf
import re
import os
from tqdm import tqdm
import subprocess
import tempfile
import shutil
from tkinter import messagebox, simpledialog


class AdvancedFilterWindow(Toplevel):
    def __init__(self, parent, dataframe, disable_main_filters_callback=None, enable_main_filters_callback=None):
        super().__init__(parent)
        self.title("Advanced Filters")
        self.geometry("800x600")
        self.dataframe = dataframe
        self.original_dataframe = dataframe.copy()
        self.filtered_dataframe = None
        self.disable_main_filters = disable_main_filters_callback
        self.enable_main_filters = enable_main_filters_callback
        self.loaded_from_vcf = False
        self.style = ttk.Style()
        self.style.theme_use('clam')       
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.create_filter_interface()       
        if self.disable_main_filters:
            self.disable_main_filters()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
          
    def create_filter_interface(self):
        self.rules_frame = ttk.LabelFrame(self.main_frame, text="Filter Rules", padding=10)
        self.rules_frame.pack(fill=BOTH, expand=True)
        self.filter_rows = []
        self.add_filter_row()
        self.add_btn = ttk.Button(self.main_frame, text="Add Another Filter", command=self.add_filter_row)
        self.add_btn.pack(pady=5, fill=X, padx=10)
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=X, pady=10, padx=10)
        self.apply_btn = ttk.Button(self.btn_frame, text="Apply Filters", command=self.apply_filters)
        self.apply_btn.pack(side=LEFT, padx=5, expand=True, fill=X)
        self.cancel_btn = ttk.Button(self.btn_frame, text="Close", command=self.on_close)
        self.cancel_btn.pack(side=LEFT, padx=5, expand=True, fill=X)

    def on_close(self):
        if self.enable_main_filters:
            self.enable_main_filters()
        self.destroy()

    def add_filter_row(self, column="", operator="", value=""):
        row_frame = ttk.Frame(self.rules_frame)
        row_frame.pack(fill=X, pady=5, padx=5)
        columns = self.dataframe.columns.tolist()
        col_combo = ttk.Combobox(row_frame, values=columns, state="readonly")
        col_combo.set(column)
        col_combo.pack(side=LEFT, padx=5, expand=True, fill=X)
        op_combo = ttk.Combobox(row_frame, state="readonly")
        op_combo.set(operator)
        op_combo.pack(side=LEFT, padx=5, expand=True, fill=X)
        vcmd = (self.register(self.validate_input), '%P')
        value_entry = ttk.Entry(row_frame, validate='key', validatecommand=vcmd)
        if value:
            value_entry.insert(0, value)
        value_entry.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        remove_btn = ttk.Button(row_frame, text="×", width=2,
                              command=lambda: self.remove_filter_row(row_frame))
        remove_btn.pack(side=LEFT, padx=5)

        self.filter_rows.append({
            'frame': row_frame,
            'column': col_combo,
            'operator': op_combo,
            'value': value_entry,
            'is_numeric': False  
        })
        col_combo.bind("<<ComboboxSelected>>", lambda e: self.update_operators_for_column(col_combo, op_combo, value_entry))
        if column:
            self.update_operators_for_column(col_combo, op_combo, value_entry)
        self.update_value_visibility(op_combo, value_entry)
        op_combo.bind("<<ComboboxSelected>>", lambda e: self.update_value_visibility(op_combo, value_entry))

    def update_operators_for_column(self, col_combo, op_combo, value_entry):
        col = col_combo.get()
        if not col:
            return
        col_data = self.dataframe[col]
        def is_column_numeric(series):
            if pd.api.types.is_numeric_dtype(series):
                return True
            sample = series.dropna().sample(min(100, len(series))) if len(series) > 0 else series
            numeric_count = 0
            for val in sample:
                try:
                    float(val)
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass
            return numeric_count / len(sample) > 0.9 if len(sample) > 0 else False       
        is_numeric = is_column_numeric(col_data)
        for row in self.filter_rows:
            if row['column'] == col_combo:
                row['is_numeric'] = is_numeric
                break
        if is_numeric:
            operators = ["equals", "not equals", ">", ">=", "<", "<=", "is empty", "is not empty"]
        else:
            operators = ["equals", "not equals", "contains", "does not contain",
                        "starts with", "ends with", "is empty", "is not empty"]
        op_combo['values'] = operators
        if op_combo.get() not in operators:
            op_combo.set(operators[0] if operators else "")

    def validate_input(self, new_value):
        for row in self.filter_rows:
            if row['value'] == self.focus_get():
                if row['is_numeric']:
                    if new_value == "":
                        return True
                    try:
                        float(new_value)
                        return True
                    except ValueError:
                        return False
                break
        return True 

    def remove_filter_row(self, row_frame):
        for i, row in enumerate(self.filter_rows):
            if row['frame'] == row_frame:
                row_frame.destroy()
                self.filter_rows.pop(i)
                break

    def update_value_visibility(self, op_combo, value_entry):
        op = op_combo.get()
        if op in ["is empty", "is not empty"]:
            value_entry.pack_forget()
        else:
            value_entry.pack(side=LEFT, padx=5, expand=True, fill=X)

    def update_column_dropdowns(self, current_columns):
        for row in self.filter_rows:
            current_value = row['column'].get()
            row['column']['values'] = current_columns
            if current_value not in current_columns:
                row['column'].set('')

    def apply_filters(self):
        try:
            current_columns = self.master.MasterTable.columns
            filtered_df = self.original_dataframe[current_columns].copy()
            for row in self.filter_rows:
                col = row['column'].get()
                op = row['operator'].get()
                val = row['value'].get()
                if not col or not op:
                    continue
                series = filtered_df[col]
                is_num = pd.api.types.is_numeric_dtype(series)
                if op in ["is empty", "is not empty"]:
                    filtered_df = filtered_df[series.isna() | (series == "")] if op == "is empty" else filtered_df[~series.isna() & (series != "")]
                    continue
                if val == "":
                    continue
                if is_num:
                    try:
                        val = float(val) if "." in val else int(val)
                    except ValueError:
                        messagebox.showerror("Type Error", f"Column '{col}' is numeric but '{val}' is not.")
                        return
                if op == "equals":
                    filtered_df = filtered_df[series == val]
                elif op == "not equals":
                    filtered_df = filtered_df[series != val]
                elif op == "contains":
                    filtered_df = filtered_df[series.astype(str).str.contains(val, case=False, na=False)]
                elif op == "does not contain":
                    filtered_df = filtered_df[~series.astype(str).str.contains(val, case=False, na=False)]
                elif op == "starts with":
                    filtered_df = filtered_df[series.astype(str).str.startswith(val, na=False)]
                elif op == "ends with":
                    filtered_df = filtered_df[series.astype(str).str.endswith(val, na=False)]
                elif op == ">":
                    filtered_df = filtered_df[series > val]
                elif op == ">=":
                    filtered_df = filtered_df[series >= val]
                elif op == "<":
                    filtered_df = filtered_df[series < val]
                elif op == "<=":
                    filtered_df = filtered_df[series <= val]

            current_df = self.master.table.model.df.copy()
            common_indices = filtered_df.index.intersection(current_df.index)
            for col in current_columns:
                filtered_df.loc[common_indices, col] = current_df.loc[common_indices, col]
        
            self.filtered_dataframe = filtered_df
            self.master.MasterTable = filtered_df
            self.master.update_table()
            messagebox.showinfo("Success", f"Done!\n{len(filtered_df)} rows match the filters.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters:\n{str(e)}")

    def clear_filters(self):
        try:
            for row in self.filter_rows[:]:  
                self.remove_filter_row(row['frame'])
            self.add_filter_row()
            self.filtered_dataframe = None
            self.dataframe = self.original_dataframe.copy()
            current_df = self.master.table.model.df.copy()
            common_indices = self.original_dataframe.index.intersection(current_df.index)
            current_dtypes = current_df.dtypes
            
            for col in self.original_dataframe.columns:
                if col in current_df.columns:
                    current_df.loc[common_indices, col] = self.original_dataframe.loc[common_indices, col]
                    if col in current_dtypes:
                        try:
                            current_df[col] = current_df[col].astype(current_dtypes[col])
                        except (ValueError, TypeError):
                            pass
            
            self.master.MasterTable = current_df
            self.master.update_table()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear advanced filters:\n{str(e)}")

class MasterTableApp(Tk):
    def __init__(self):
        super().__init__()
        self.title('GenMasterTable')
        self.geometry('1400x900+200+100')
        self.configure(bg='#f0f0f0')
        self.vcf_headers = {}
        self.MasterTable = pd.DataFrame()
        self.original_MasterTable = pd.DataFrame()
        self.previous_columns = []
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', font=('Arial', 14), padding=5)
        self.style.configure('TLabel', font=('Arial', 14))
        self.style.configure('TEntry', font=('Arial', 14))
        self.style.configure('TFrame', background='#f0f0f0')
        self.paned_window = ttk.PanedWindow(self, orient=VERTICAL)
        self.paned_window.pack(fill=BOTH, expand=True)
        self.table_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.table_frame, weight=4)
        self.control_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.control_frame, weight=1)
        self.update_idletasks()
        window_height = self.winfo_height()
        if window_height < 100:
            window_height = 900
        self.paned_window.sashpos(0, int(window_height * 0.55))

        self.table = Table(self.table_frame, dataframe=pd.DataFrame(), showtoolbar=False, showstatusbar=True)
        self.table.show()
        self._original_deleteColumn = self.table.deleteColumn
        self._original_deleteRow = self.table.deleteRow
        
        def new_deleteColumn(*args, **kwargs):
            result = self._original_deleteColumn(*args, **kwargs)
            self._sync_columns_immediately()
            return result
        
        def new_deleteRow(*args, **kwargs):
            result = self._original_deleteRow(*args, **kwargs)
            self._sync_rows_immediately()
            return result
        
        self.table.deleteColumn = new_deleteColumn
        self.table.deleteRow = new_deleteRow 
        self.table.unbind("<Button-3>")
        self.table.unbind("<Button-2>")
        self.table.popupMenu = None 
        self.table.bind("<ButtonRelease-1>", self.handle_table_change)
        self.table.bind("<KeyRelease>", self.handle_table_change)
        self.table.bind("<Delete>", self.handle_column_deletion)
        if hasattr(self.table, 'columnheader'):
            self.table.columnheader.bind("<ButtonRelease-1>", self.handle_table_change)

        self.create_file_controls()
        self.create_filter_controls()

    def is_column_numeric(self, series):
        if pd.api.types.is_numeric_dtype(series):
            return True
        sample = series.dropna().sample(min(100, len(series))) if len(series) > 0 else series
        numeric_count = 0       
        for val in sample:
            try:
                float(val)
                numeric_count += 1
            except (ValueError, TypeError):
                pass
        return numeric_count / len(sample) > 0.9 if len(sample) > 0 else False

    def disable_simple_filters(self):
        disabled_bg = '#e0e0e0'  
        disabled_fg = '#a0a0a0'  
        for sec in self.filter_sections:
            sec['combobox'].config(state='disabled', 
                                background=disabled_bg,
                                foreground=disabled_fg)
            sec['entry'].config(state='disabled', 
                            background=disabled_bg,
                            foreground=disabled_fg)
        self.apply_btn.config(state='disabled')
        self.clear_btn.config(state='disabled')
        self.style.map('TCombobox',
                    fieldbackground=[('disabled', disabled_bg)],
                    foreground=[('disabled', disabled_fg)])
        self.style.map('TEntry',
                    fieldbackground=[('disabled', disabled_bg)],
                    foreground=[('disabled', disabled_fg)])
        
        self.update()  

    def enable_simple_filters(self):
        """Enable all simple filter controls and restore their appearance"""
        normal_bg = 'white'  
        normal_fg = 'black'  
        
        for sec in self.filter_sections:
            sec['combobox'].config(state='readonly', 
                                background=normal_bg,
                                foreground=normal_fg)
            sec['entry'].config(state='normal', 
                            background=normal_bg,
                            foreground=normal_fg)
        self.apply_btn.config(state='normal')
        self.clear_btn.config(state='normal')
        self.style.map('TCombobox',
                    fieldbackground=[],
                    foreground=[])
        self.style.map('TEntry',
                    fieldbackground=[],
                    foreground=[])
        
        self.update()
    
    def handle_table_change(self, event=None):
        self.after(100, self._sync_columns_immediately)

    def handle_column_deletion(self, event=None):
        try:
            current_columns = self.table.model.df.columns.tolist()
            self.MasterTable = self.MasterTable[current_columns]
            self.deleted_columns = set(self.original_MasterTable.columns) - set(current_columns)
            self._update_filter_dropdowns()
            for child in self.winfo_children():
                if isinstance(child, AdvancedFilterWindow):
                    child.update_column_dropdowns(current_columns)
                    
        except Exception as e:
            print(f"Error handling column deletion: {e}")

    def _sync_columns_immediately(self, event=None):
        try:
            current_columns = self.table.model.df.columns.tolist()
            self.MasterTable = self.MasterTable[current_columns]
            
            if current_columns != self.previous_columns:
                self.previous_columns = current_columns
                self._update_filter_dropdowns()
                for child in self.winfo_children():
                    if isinstance(child, AdvancedFilterWindow):
                        child.update_column_dropdowns(current_columns)
        except Exception as e:
            print(f"Error syncing columns: {e}")

    def _sync_rows_immediately(self, event=None):
        try:
            model_data = self.table.model.df
            self.MasterTable = model_data.copy()
            deleted_indices = set(self.original_MasterTable.index) - set(self.MasterTable.index)
            self.deleted_indices = deleted_indices         
        except Exception as e:
            print(f"Error syncing rows: {e}")

    def _update_filter_dropdowns(self):
        if not hasattr(self, 'filter_sections'):
            return
        try:
            current_columns = self.MasterTable.columns.tolist()
            for sec in self.filter_sections:
                current_value = sec['combobox'].get()
                sec['combobox']['values'] = current_columns
                if current_value not in current_columns:
                    sec['combobox'].set('')
                    sec['entry'].delete(0, END)
                if not sec['combobox'].get() and current_columns:
                    sec['combobox'].current(0)
        except Exception as e:
            print(f"Error updating filter dropdowns: {e}")

    def has_data_loaded(self):
        return not self.MasterTable.empty

    def show_no_data_message(self, action="perform this action"):
        messagebox.showwarning("No Data", f"Load data before you {action}.")

    def create_file_controls(self):
        file_frame = ttk.LabelFrame(self.control_frame, text="Choose your file", padding=(10,5))
        file_frame.pack(fill=X, expand=True, padx=10, pady=5)

        self.load_btn = ttk.Button(file_frame, text="Load or Merge CSV/TSV/VCF", command=self.load_merge_files)
        self.load_btn.pack(fill=BOTH, expand=True, padx=5, pady=5, ipady=10)

    def create_filter_controls(self):
        filter_frame = ttk.LabelFrame(self.control_frame, text="Filters", padding=(10,5))
        filter_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        center_frame = ttk.Frame(filter_frame)
        center_frame.pack(fill='x', expand=True, pady=10)
        self.filter_sections = []
        for i, label in enumerate(["Filter 1", "Filter 2", "Filter 3"]):
            section = ttk.Frame(center_frame)
            section.grid(row=0, column=i, padx=18, pady=5, sticky='nsew')
            center_frame.columnconfigure(i, weight=1)  
            section.columnconfigure(0, weight=1)       
            ttk.Label(section, text=f"{label} - Select Column:").grid(row=0, column=0, sticky='ew')
            combo = ttk.Combobox(section, font=('Arial',14), state='readonly', width=16)
            combo.grid(row=1, column=0, pady=5, sticky='ew')
            ttk.Label(section, text="Filter Values (comma/space):").grid(row=2, column=0, sticky='ew')
            entry = ttk.Entry(section, font=('Arial',14), width=18)
            entry.grid(row=3, column=0, pady=5, ipady=10, sticky='ew')
            section_data = {'combobox': combo, 'entry': entry}
            self.filter_sections.append(section_data)
            combo.bind("<<ComboboxSelected>>", 
                    lambda e, entry=entry, combo=combo: self.update_entry_validation(entry, combo))
            ttk.Label(section, text="Filter Values (comma/space):").grid(row=2, column=0, sticky='ew')
            entry = ttk.Entry(section, font=('Arial',14), width=18)
            entry.grid(row=3, column=0, pady=5, ipady=10, sticky='ew')
            self.filter_sections.append({'combobox': combo, 'entry': entry})
        btn_frame = ttk.Frame(center_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky='ew')
        for i in range(5):
            btn_frame.columnconfigure(i, weight=1)
        self.advanced_btn = ttk.Button(btn_frame, text="Advanced Filters", command=self.open_advanced_filters)
        self.advanced_btn.grid(row=0, column=0, padx=5, pady=4, sticky='ew')
        self.apply_btn = ttk.Button(btn_frame, text="Apply Filters", command=self.apply_filters)
        self.apply_btn.grid(row=0, column=1, padx=5, pady=4, sticky='ew')
        self.clear_btn = ttk.Button(btn_frame, text="Clear Filters", command=self.clear_filters)
        self.clear_btn.grid(row=0, column=2, padx=5, pady=4, sticky='ew')
        self.clear_table_btn = ttk.Button(btn_frame, text="Clear Table", command=self.clear_table)
        self.clear_table_btn.grid(row=0, column=3, padx=5, pady=4, sticky='ew')

        self.export_menu = Menu(self, tearoff=0)
        self.export_menu.add_command(label="Export as CSV", command=self.export_csv)
        self.export_menu.add_command(label="Export as TSV", command=self.export_tsv)
        self.export_menu.add_command(label="Export as VCF", command=self.export_to_vcf)

        def check_vcf_export(self):
            if not self.loaded_from_vcf:
                messagebox.showerror(
                    "Export Error",
                    "VCF export can only be performed when the input data was loaded from VCF files.\n"
                    "Please load VCF files first before attempting VCF export."
                )
            else:
                self.export_to_vcf()

        def show_export_menu(event):
            self.export_menu.post(event.x_root, event.y_root)

        self.export_btn = ttk.Button(btn_frame, text="Export as CSV/TSV/VCF")
        self.export_btn.grid(row=0, column=4, padx=5, pady=4, sticky='ew')
        self.export_btn.bind("<Button-1>", show_export_menu)


    def update_entry_validation(self, entry, combo):
        col = combo.get()
        if col:
            is_numeric = self.is_column_numeric(self.MasterTable[col])
            if is_numeric:
                vcmd = (self.register(self.validate_numeric_input), '%P')
                entry.config(validate='key', validatecommand=vcmd)
            else:
                entry.config(validate='none')

    def validate_numeric_input(self, new_value):
        if new_value == "":
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            return False
    

    def populate_column_comboboxes(self):
        cols = self.MasterTable.columns.tolist()
        for sec in self.filter_sections:
            current_value = sec['combobox'].get()
            sec['combobox']['values'] = cols
            if current_value in cols:
                sec['combobox'].set(current_value)
            elif cols:
                sec['combobox'].current(0)
            else:
                sec['combobox'].set('')


    def apply_filters(self):
        if not self.has_data_loaded():
            self.show_no_data_message("apply filters")
            return
        try:
            current_columns = self.MasterTable.columns
            df = self.original_MasterTable[current_columns].copy()
            
            for sec in self.filter_sections:
                col = sec['combobox'].get()
                vals = sec['entry'].get().strip()
                if not col or not vals:
                    continue
                col_data = df[col]
                def is_numeric_column(series):
                    if pd.api.types.is_numeric_dtype(series):
                        return True
                    sample = series.dropna().sample(min(100, len(series))) if len(series) > 0 else series
                    numeric_count = 0
                    for val in sample:
                        try:
                            float(val)
                            numeric_count += 1
                        except (ValueError, TypeError):
                            pass
                    return numeric_count / len(sample) > 0.9 if len(sample) > 0 else False                   
                is_numeric = is_numeric_column(col_data)
                items = [v.strip() for v in re.split(r'[,\s]+', vals) if v.strip()]
                    
                if is_numeric:
                    try:
                        numeric_items = []
                        for x in items:
                            try:
                                num_val = float(x)
                                if '.' not in x and pd.api.types.is_integer_dtype(col_data):
                                    num_val = int(num_val)
                                numeric_items.append(num_val)
                            except ValueError:
                                messagebox.showerror(
                                    "Type Error", 
                                    f"Column '{col}' contains numeric data but filter value '{x}' is not numeric.\n"
                                    f"Please enter numbers only for this column."
                                )
                                return
                        items = numeric_items
                        if not pd.api.types.is_numeric_dtype(df[col]):
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    except ValueError as e:
                        messagebox.showerror("Error", f"Invalid numeric input: {str(e)}")
                        return
                try:
                    if is_numeric:
                        mask = False
                        for val in items:
                            mask = mask | (df[col] == val)
                        df = df[mask]
                    else:
                        df = df[df[col].astype(str).str.lower().isin([str(x).lower() for x in items])]
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to apply filters:\n{str(e)}")
                    return     
            self.MasterTable = df
            self.update_table()
            messagebox.showinfo("Success", f"Done!\n{len(df)} rows match the filters.")            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters:\n{str(e)}")

    def clear_filters(self):
        if not hasattr(self, 'original_MasterTable') or self.original_MasterTable.empty:
            self.show_no_data_message("clear filters")
            return           
        try:
            for sec in self.filter_sections:
                sec['combobox'].set('')
                sec['entry'].delete(0, END)

            for child in self.winfo_children():
                if isinstance(child, AdvancedFilterWindow):
                    child.clear_filters()
            current_columns = set(self.MasterTable.columns)
            restored_df = self.original_MasterTable.copy()
            restored_df = restored_df[list(current_columns.intersection(restored_df.columns))]
            if hasattr(self, 'deleted_indices'):
                restored_df = restored_df.drop(index=self.deleted_indices, errors='ignore')
            current_df = self.table.model.df.copy()
            common_indices = restored_df.index.intersection(current_df.index)
            for col in restored_df.columns:
                if col in current_df.columns:
                    restored_df.loc[common_indices, col] = current_df.loc[common_indices, col]
            self.MasterTable = restored_df
            self.update_table()
            messagebox.showinfo("Success", "Done")   
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear filters:\n{str(e)}")

    def add_filter_row(self, column="", operator="", value=""):
        row_frame = ttk.Frame(self.rules_frame)
        row_frame.pack(fill=X, pady=5, padx=5)

        columns = self.dataframe.columns.tolist()
        col_combo = ttk.Combobox(row_frame, values=columns, state="readonly")
        col_combo.set(column)
        col_combo.pack(side=LEFT, padx=5, expand=True, fill=X)
        type_combo = ttk.Combobox(row_frame, values=["auto", "numeric", "text"], 
                                state="readonly", width=8)
        type_combo.set("auto")
        type_combo.pack(side=LEFT, padx=5)
        op_combo = ttk.Combobox(row_frame, state="readonly")
        op_combo.set(operator)
        op_combo.pack(side=LEFT, padx=5, expand=True, fill=X)
        vcmd = (self.register(self.validate_input), '%P')
        value_entry = ttk.Entry(row_frame, validate='key', validatecommand=vcmd)
        if value:
            value_entry.insert(0, value)
        value_entry.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        remove_btn = ttk.Button(row_frame, text="×", width=2,
                            command=lambda: self.remove_filter_row(row_frame))
        remove_btn.pack(side=LEFT, padx=5)

        self.filter_rows.append({
            'frame': row_frame,
            'column': col_combo,
            'type': type_combo,  
            'operator': op_combo,
            'value': value_entry,
            'is_numeric': False
        })

        col_combo.bind("<<ComboboxSelected>>", 
                    lambda e: self.update_operators_for_column(col_combo, op_combo, value_entry))
        type_combo.bind("<<ComboboxSelected>>",
                    lambda e: self.force_column_type(col_combo, type_combo, op_combo, value_entry))
        
        if column:
            self.update_operators_for_column(col_combo, op_combo, value_entry)
        
        self.update_value_visibility(op_combo, value_entry)
        op_combo.bind("<<ComboboxSelected>>", lambda e: self.update_value_visibility(op_combo, value_entry))

    def force_column_type(self, col_combo, type_combo, op_combo, value_entry):
        type_choice = type_combo.get()
        for row in self.filter_rows:
            if row['column'] == col_combo:
                if type_choice == "numeric":
                    row['is_numeric'] = True
                    operators = ["equals", "not equals", ">", ">=", "<", "<=", "is empty", "is not empty"]
                elif type_choice == "text":
                    row['is_numeric'] = False
                    operators = ["equals", "not equals", "contains", "does not contain",
                            "starts with", "ends with", "is empty", "is not empty"]
                else:  
                    self.update_operators_for_column(col_combo, op_combo, value_entry)
                    return
                    
                op_combo['values'] = operators
                if op_combo.get() not in operators:
                    op_combo.set(operators[0])
                break

    def update_operators_for_column(self, col_combo, op_combo, value_entry):
        col = col_combo.get()
        if not col:
            return
        is_numeric = pd.api.types.is_numeric_dtype(self.dataframe[col])
        for row in self.filter_rows:
            if row['column'] == col_combo:
                row['is_numeric'] = is_numeric
                break
        if is_numeric:
            operators = ["equals", "not equals", ">", ">=", "<", "<=", "is empty", "is not empty"]
        else:
            operators = ["equals", "not equals", "contains", "does not contain",
                        "starts with", "ends with", "is empty", "is not empty"]      
        op_combo['values'] = operators
        if op_combo.get() not in operators:
            op_combo.set(operators[0] if operators else "")

    def validate_input(self, new_value):
        for row in self.filter_rows:
            if row['value'].widget == self.focus_get():
                if row['is_numeric']:
                    if new_value == "":
                        return True
                    try:
                        float(new_value)
                        return True
                    except ValueError:
                        return False
                break
        return True

    def load_merge_files(self):
        try:
            filepaths = filedialog.askopenfilenames(parent=self, title="Select CSV/TSV/VCF Files",
                filetypes=[("CSV files","*.csv"),("TSV files","*.tsv"),("VCF files","*.vcf"),("VCF GZ files","*.vcf.gz")])
            if not filepaths:
                return
                
            ext = os.path.splitext(filepaths[0])[1].lower()
            if all(os.path.splitext(fp)[1].lower() == ext for fp in filepaths):
                if ext == ".csv": 
                    self._load_csv(filepaths)
                    if not self.MasterTable.empty:  
                        messagebox.showinfo("Success", "CSV files loaded successfully!")
                elif ext == ".tsv": 
                    self._load_tsv(filepaths)
                    if not self.MasterTable.empty:
                        messagebox.showinfo("Success", "TSV files loaded successfully!")
                elif ext in [".vcf", ".gz"]: 
                    self._load_vcf(filepaths)
                    if not self.MasterTable.empty:
                        messagebox.showinfo("Success", "VCF files loaded successfully!")
                else: 
                    messagebox.showerror("Error","Unsupported file type.")
            else:
                messagebox.showerror("Error","Cannot mix different file types.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load files:\n{str(e)}")

    def _load_csv(self, fps):
        self.loaded_from_vcf = False
        data = []
        for f in fps:
            try:
                df = pd.concat(pd.read_csv(f, chunksize=10**12, low_memory=False), ignore_index=True)
                df["File_Name"] = os.path.basename(f)
                data.append(df)
            except Exception as e:
                print(e)
        self._finalize_load(data, "CSV")

    def _load_tsv(self, fps):
        self.loaded_from_vcf = False
        data = []
        for f in fps:
            try:
                df = pd.concat(pd.read_csv(f, sep='\t', chunksize=10**12, low_memory=False), ignore_index=True)
                df["File_Name"] = os.path.basename(f)
                data.append(df)
            except Exception as e:
                print(e)
        self._finalize_load(data, "TSV")
    
    def _load_vcf(self, fps):
        self.loaded_from_vcf = True 
        data = []
        files_loaded = 0       
        for f in fps:
            try:
                reader = vcf.Reader(filename=f)
                if len(reader.samples) > 1:
                    proceed = messagebox.askyesno(
                        "Multi-sample VCF Detected",
                        f"'{os.path.basename(f)}' contains {len(reader.samples)} samples.\n"
                        "Would you like to split it into individual sample files?",
                        parent=self
                    )
                    if not proceed:  
                        continue  
                    split_files = self._split_multi_sample_vcf_python(f)
                    for split_file in split_files:
                        try:
                            reader = vcf.Reader(filename=split_file)
                            self.vcf_headers[os.path.basename(split_file)] = reader
                            vdfs = list(self.parse_vcf(reader, os.path.basename(split_file)))
                            if vdfs:
                                df = pd.concat(vdfs, ignore_index=True)
                                df["File_Name"] = os.path.basename(split_file)
                                data.append(df)
                                files_loaded += 1
                        finally:
                            if os.path.exists(split_file):
                                os.remove(split_file)
                    continue  
                self.vcf_headers[os.path.basename(f)] = reader
                vdfs = list(self.parse_vcf(reader, os.path.basename(f)))
                if vdfs:
                    df = pd.concat(vdfs, ignore_index=True)
                    df["File_Name"] = os.path.basename(f)
                    data.append(df)
                    files_loaded += 1
                    
            except Exception as e:
                print(f"Error processing {f}: {e}")
        if files_loaded > 0:
            self._finalize_load(data, "VCF")
        else:
            self.MasterTable = pd.DataFrame()
            self.original_MasterTable = pd.DataFrame()
            self.update_table()


    def _split_multi_sample_vcf_python(self, vcf_path):
        temp_dir = tempfile.mkdtemp()
        base_name = os.path.splitext(os.path.basename(vcf_path))[0]
        split_files = []
        
        try:
            reader = vcf.Reader(filename=vcf_path)
            original_header = {
                'fileformat': reader.metadata.get('fileformat', 'VCFv4.2'),
                'infos': {k: v for k, v in reader.infos.items()},
                'formats': {k: v for k, v in reader.formats.items()},
                'filters': {k: v for k, v in reader.filters.items()},
                'contigs': {k: v for k, v in reader.contigs.items()},
                'samples': reader.samples
            }
            
            for sample in reader.samples:
                output_file = os.path.join(temp_dir, f"{base_name}_{sample}.vcf")
                split_files.append(output_file)
                
                with open(output_file, 'w') as f_out:
                    sample_reader = vcf.Reader(filename=vcf_path)
                    writer = vcf.Writer(f_out, sample_reader)
                    
                    for record in sample_reader:
                        new_samples = [s for s in record.samples if s.sample == sample]
                        if not new_samples:
                            continue
                        new_record = vcf.model._Record(
                            CHROM=record.CHROM,
                            POS=record.POS,
                            ID=record.ID,
                            REF=record.REF,
                            ALT=record.ALT,
                            QUAL=record.QUAL,
                            FILTER=record.FILTER,
                            INFO=record.INFO,
                            FORMAT=record.FORMAT,
                            sample_indexes=[0],  
                            samples=new_samples
                        )
                        writer.write_record(new_record)
                    
                    writer.close()
                self.vcf_headers[os.path.basename(output_file)] = {
                    'reader': vcf.Reader(filename=output_file),
                    'original_header': original_header
                }
            
            messagebox.showinfo(
                "Split Complete",
                f"Split {len(split_files)} samples from {os.path.basename(vcf_path)}",
                parent=self
            )
            return split_files
            
        except Exception as e:
            messagebox.showerror("Split Error", str(e), parent=self)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return []

    def handle_row_deletion(self, event=None):
        try:
            selected = self.table.getSelectedRows()
            
            if selected:
                self.table.model.df.drop(self.table.model.df.index[selected], inplace=True)
                self.table.redraw()
                self._sync_rows_immediately()
                
        except Exception as e:
            print(f"Error handling row deletion: {e}")

    def parse_vcf(self, reader, filename, batch_size=10**12):
        try:
            batch = []
            for rec in tqdm(reader, desc=filename):
                row = {
                    'Chrom': rec.CHROM,
                    'Pos': rec.POS,
                    'ID': rec.ID or '.',
                    'Ref': rec.REF,
                    'Alt': ','.join(map(str, rec.ALT)),
                    'Qual': rec.QUAL,
                    'Filter': ';'.join(rec.FILTER) if rec.FILTER else 'PASS',
                }
                
                for k, v in rec.INFO.items():
                    row[k] = ','.join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
                if rec.samples:
                    format_fields = rec.FORMAT.split(':')
                    for field in format_fields:
                        values = []
                        for sample in rec.samples:
                            if hasattr(sample.data, field):
                                val = getattr(sample.data, field)
                                if isinstance(val, (list, tuple)):
                                    values.append(','.join(map(str, val)))
                                else:
                                    values.append(str(val))
                            else:
                                values.append('.')
                        row[field] = '|'.join(values)
                
                batch.append(row)
                
                if len(batch) >= batch_size:
                    yield pd.DataFrame(batch)
                    batch = []
            if batch:
                yield pd.DataFrame(batch)
        except Exception as e:
            print(f"Error parsing VCF: {e}")
            yield pd.DataFrame()

    def _finalize_load(self, data, label):
        if data:
            self.MasterTable = pd.concat(data, ignore_index=True)
            self.original_MasterTable = self.MasterTable.copy()
            self.previous_columns = self.MasterTable.columns.tolist()
            self.populate_column_comboboxes()
            self.update_table()
            self.title(f"GenMasterTable - Merged {label}")

    def update_table(self):
        self.table.updateModel(TableModel(self.MasterTable))
        self.table.redraw()
        self._sync_columns_immediately()

    def open_advanced_filters(self):
        if not self.has_data_loaded():
            self.show_no_data_message("open advanced filters")
            return
        for child in self.winfo_children():
            if isinstance(child, AdvancedFilterWindow):
                child.lift()  
                return
        adv_window = AdvancedFilterWindow(
            self, 
            self.MasterTable,
            disable_main_filters_callback=self.disable_simple_filters,
            enable_main_filters_callback=self.enable_simple_filters
        )
        
        adv_window.lift()
        adv_window.focus_force()

    def clear_table(self):
        if not self.has_data_loaded():
            self.show_no_data_message("clear the table")
            return
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all data from the table?"):
            self.MasterTable = pd.DataFrame()
            self.original_MasterTable = pd.DataFrame()
            self.previous_columns = []
            self.vcf_headers = {}
            self.loaded_from_vcf = False
            if hasattr(self, 'deleted_indices'):
                del self.deleted_indices
            self.update_table()
            for sec in self.filter_sections:
                sec['combobox'].set('')
                sec['entry'].delete(0, END)
            
            messagebox.showinfo("Success", "Table cleared successfully!")    
       
    def export_csv(self):
        if not self.has_data_loaded():
            self.show_no_data_message("export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.table.model.df.to_csv(path, index=False)
            messagebox.showinfo("Success", "CSV file exported successfully.")

    def export_tsv(self):
        if not self.has_data_loaded():
            self.show_no_data_message("export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".tsv", filetypes=[("TSV files", "*.tsv")])
        if path:
            self.table.model.df.to_csv(path, index=False, sep='\t')
            messagebox.showinfo("Success", "TSV file exported successfully.")

    def _write_vcf_header(self, file_obj, header_source, available_fields=None):
        if isinstance(header_source, dict):
            file_obj.write(f"##fileformat={header_source['fileformat']}\n")
            for info_id, info in header_source['infos'].items():
                if available_fields is None or info_id in available_fields:
                    file_obj.write(f"##INFO=<ID={info_id},Number={info.num},Type={info.type},Description=\"{info.desc}\">\n")
            for fmt_id, fmt in header_source['formats'].items():
                if available_fields is None or fmt_id in available_fields:
                    file_obj.write(f"##FORMAT=<ID={fmt_id},Number={fmt.num},Type={fmt.type},Description=\"{fmt.desc}\">\n")
            file_obj.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
            if 'FORMAT' in (available_fields or []):
                file_obj.write("\tFORMAT")
                for sample in header_source['samples']:
                    file_obj.write(f"\t{sample}")
            file_obj.write("\n")
        else:
            file_obj.write(f"##fileformat={header_source.metadata.get('fileformat', 'VCFv4.2')}\n")
            for info_id, info in header_source.infos.items():
                if available_fields is None or info_id in available_fields:
                    file_obj.write(f"##INFO=<ID={info_id},Number={info.num},Type={info.type},Description=\"{info.desc}\">\n")
            for fmt_id, fmt in header_source.formats.items():
                if available_fields is None or fmt_id in available_fields:
                    file_obj.write(f"##FORMAT=<ID={fmt_id},Number={fmt.num},Type={fmt.type},Description=\"{fmt.desc}\">\n")
            file_obj.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
            if hasattr(header_source, 'samples') and len(header_source.samples) > 0 and ('FORMAT' in (available_fields or [])):
                file_obj.write("\tFORMAT\tSAMPLE")
            file_obj.write("\n")

    def _get_vcf_value(self, row, field):
        val = row.get(field, '.')
        if pd.isna(val):
            return '.'
        return str(val)




    def export_to_vcf(self):
        if not self.has_data_loaded():
            self.show_no_data_message("export to VCF")
            return

        required_columns = {'Chrom', 'Pos', 'Ref', 'Alt'}
        if not required_columns.issubset(self.MasterTable.columns):
            messagebox.showerror(
                "Missing Columns",
                "VCF export requires these essential columns: Chrom, Pos, Ref, Alt."
            )
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".vcf", filetypes=[("VCF files", "*.vcf")])
        if not filepath:
            return
        
        try:
            current_columns = set(self.table.model.df.columns)
            
            samples = {}
            sample_names = []
            format_fields = set()  
            
            for fname, df in self.MasterTable.groupby("File_Name"):
                sample_name = os.path.splitext(fname)[0].split('_')[-1]
                sample_names.append(sample_name)
                
                visible_cols = [col for col in df.columns if col in current_columns]
                samples[sample_name] = df[visible_cols]
                
                for col in visible_cols:
                    if col in ['Chrom', 'Pos', 'ID', 'Ref', 'Alt', 'Qual', 'Filter', 'File_Name']:
                        continue
                    if fname in self.vcf_headers:
                        reader = self.vcf_headers[fname]
                        if hasattr(reader, 'formats') and col in reader.formats:
                            format_fields.add(col)
                        elif hasattr(reader, 'infos') and col in reader.infos:
                            continue  
                        else:
                            if any('|' in str(val) for val in df[col].dropna().head(5)):
                                format_fields.add(col)

            if len(samples) > 1:
                with open(filepath, 'w') as vcf_out:
                    vcf_out.write("##fileformat=VCF\n")
                    
                    for fname, reader in self.vcf_headers.items():
                        if hasattr(reader, 'infos'):
                            for info_id, info in reader.infos.items():
                                if info_id in current_columns:
                                    vcf_out.write(f"##INFO=<ID={info_id},Number={info.num},Type={info.type},Description=\"{info.desc}\">\n")
                            break
                    
                    format_field_order = sorted([f for f in format_fields if f in current_columns])
                    for field in format_field_order:
                        field_spec = None
                        for fname, reader in self.vcf_headers.items():
                            if hasattr(reader, 'formats') and field in reader.formats:
                                field_spec = reader.formats[field]
                                break
                        
                        if field_spec:
                            vcf_out.write(f"##FORMAT=<ID={field},Number={field_spec.num},Type={field_spec.type},Description=\"{field_spec.desc}\">\n")
                        else:
                            vcf_out.write(f"##FORMAT=<ID={field},Number=1,Type=String,Description=\"Unknown field {field}\">\n")
                    
                    vcf_out.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO")
                    if format_field_order:  
                        vcf_out.write("\tFORMAT")
                        for sample in sample_names:
                            vcf_out.write(f"\t{sample}")
                    vcf_out.write("\n")
                    
                    all_positions = set()
                    for sample_data in samples.values():
                        for _, row in sample_data.iterrows():
                            all_positions.add((row['Chrom'], row['Pos']))
                    
                    for chrom, pos in sorted(all_positions):
                        variant_info = {}
                        for sample in sample_names:
                            sample_data = samples[sample]
                            variant = sample_data[
                                (sample_data['Chrom'] == chrom) & 
                                (sample_data['Pos'] == pos)
                            ]
                            if not variant.empty:
                                variant_info[sample] = variant.iloc[0]
                        
                        if not variant_info:
                            continue
                        
                        first_var = next(iter(variant_info.values()))
                        
                        vid = first_var.get('ID', '.')
                        ref = first_var.get('Ref', 'N')
                        alt = first_var.get('Alt', '.')
                        qual = first_var.get('Qual', '.')
                        filt = first_var.get('Filter', 'PASS')
                        
                        info_fields = []
                        for info_field in first_var.index:
                            if info_field in ['Chrom', 'Pos', 'ID', 'Ref', 'Alt', 'Qual', 'Filter', 'File_Name']:
                                continue
                            if info_field not in format_fields and not pd.isna(first_var[info_field]):
                                info_fields.append(f"{info_field}={first_var[info_field]}")
                        info = ';'.join(info_fields) if info_fields else '.'
                        
                        if format_field_order:
                            sample_data_lines = []
                            for sample in sample_names:
                                if sample in variant_info:
                                    var = variant_info[sample]
                                    sample_data = []
                                    for field in format_field_order:
                                        val = var.get(field, '.')
                                        if pd.isna(val):
                                            sample_data.append('.')
                                        else:
                                            if '|' in str(val):
                                                sample_data.append(str(val).split('|')[0])
                                            else:
                                                sample_data.append(str(val))
                                    sample_data_lines.append(':'.join(sample_data))
                                else:
                                    sample_data_lines.append(':'.join(['.'] * len(format_field_order)))
                        
                        vcf_out.write(f"{chrom}\t{pos}\t{vid}\t{ref}\t{alt}\t{qual}\t{filt}\t{info}")
                        if format_field_order:  
                            vcf_out.write(f"\t{':'.join(format_field_order)}")
                            for data in sample_data_lines:
                                vcf_out.write(f"\t{data}")
                        vcf_out.write("\n")
            else:
                self._export_single_sample_vcf(filepath, format_fields)
            
            messagebox.showinfo("Success", "VCF exported successfully!")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export VCF:\n{str(e)}")

    def _export_single_sample_vcf(self, filepath, format_fields=None):
        with open(filepath, 'w') as vcf_out:
            for fname, df in self.MasterTable.groupby("File_Name"):
                if fname not in self.vcf_headers:
                    continue
                
                current_columns = set(self.table.model.df.columns)
                visible_cols = [col for col in df.columns if col in current_columns]
                df = df[visible_cols]
                
                reader = self.vcf_headers[fname]
                available_fields = set(df.columns)
                
                if format_fields is None:
                    format_fields = set()
                    if hasattr(reader, 'formats'):
                        format_fields.update([f for f in reader.formats.keys() if f in available_fields])
                    for col in available_fields:
                        if col in ['Chrom', 'Pos', 'ID', 'Ref', 'Alt', 'Qual', 'Filter', 'File_Name']:
                            continue
                        if col not in format_fields and any('|' in str(val) for val in df[col].dropna().head(5)):
                            format_fields.add(col)
                
                format_fields = {f for f in format_fields if f in current_columns}
                format_field_order = sorted(format_fields)
                
                self._write_vcf_header(vcf_out, reader, available_fields)
                
                for _, row in df.iterrows():
                    chrom = self._get_vcf_value(row, 'Chrom')
                    pos = self._get_vcf_value(row, 'Pos')
                    vid = self._get_vcf_value(row, 'ID')
                    ref = self._get_vcf_value(row, 'Ref')
                    alt = self._get_vcf_value(row, 'Alt')
                    qual = self._get_vcf_value(row, 'Qual')
                    filt = self._get_vcf_value(row, 'Filter')
                    
                    info_fields = []
                    for info_field in row.index:
                        if info_field in ['Chrom', 'Pos', 'ID', 'Ref', 'Alt', 'Qual', 'Filter', 'File_Name']:
                            continue
                        if info_field not in format_fields and not pd.isna(row[info_field]):
                            info_fields.append(f"{info_field}={row[info_field]}")
                    info = ';'.join(info_fields) if info_fields else '.'
                    
                    if format_field_order:
                        sample_data = []
                        for field in format_field_order:
                            val = row.get(field, '.')
                            if pd.isna(val):
                                sample_data.append('.')
                            else:
                                if '|' in str(val):
                                    sample_data.append(str(val).split('|')[0])
                                else:
                                    sample_data.append(str(val))
                    
                    vcf_out.write(f"{chrom}\t{pos}\t{vid}\t{ref}\t{alt}\t{qual}\t{filt}\t{info}")
                    if format_field_order:  
                        vcf_out.write(f"\t{':'.join(format_field_order)}\t{':'.join(sample_data)}")
                    vcf_out.write("\n")



    def _parse_info_value(self, val):
        if pd.isna(val):
            return None
        if isinstance(val, str) and ',' in val:
            return val.split(',')
        return val

if __name__ == "__main__":
    app = MasterTableApp()
    app.mainloop()
