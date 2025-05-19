from tkinter import *
from tkinter import ttk, filedialog, messagebox
from pandastable import Table, TableModel
import pandas as pd
import vcf
import re
import os
from tqdm import tqdm



class AdvancedFilterWindow(Toplevel):
    def __init__(self, parent, dataframe):
        super().__init__(parent)
        self.title("Advanced Filters")
        self.geometry("800x600")
        self.dataframe = dataframe
        self.original_dataframe = dataframe.copy()
        self.filtered_dataframe = None

        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

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

        self.cancel_btn = ttk.Button(self.btn_frame, text="Close", command=self.destroy)
        self.cancel_btn.pack(side=LEFT, padx=5, expand=True, fill=X)

    def add_filter_row(self, column="", operator="", value=""):
        row_frame = ttk.Frame(self.rules_frame)
        row_frame.pack(fill=X, pady=5, padx=5)

        columns = self.dataframe.columns.tolist()
        col_combo = ttk.Combobox(row_frame, values=columns, state="readonly")
        col_combo.set(column)
        col_combo.pack(side=LEFT, padx=5, expand=True, fill=X)

        operators = ["equals", "not equals", "contains", "does not contain",
                    "starts with", "ends with", ">", ">=", "<", "<=",
                    "is empty", "is not empty"]
        op_combo = ttk.Combobox(row_frame, values=operators, state="readonly")
        op_combo.set(operator)
        op_combo.pack(side=LEFT, padx=5, expand=True, fill=X)

        value_entry = ttk.Entry(row_frame)
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
            'value': value_entry
        })

        self.update_value_visibility(op_combo, value_entry)
        op_combo.bind("<<ComboboxSelected>>", lambda e: self.update_value_visibility(op_combo, value_entry))

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
            self.filtered_dataframe = filtered_df
            self.master.MasterTable = filtered_df
            self.master.update_table()
            messagebox.showinfo("Success", f"Filters applied successfully!\n{len(filtered_df)} rows match the filters.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters:\n{str(e)}")

    def clear_filters(self):
        try:
            current_columns = self.master.MasterTable.columns
            common_cols = [col for col in current_columns if col in self.original_dataframe.columns]
            if not common_cols:
                self.master.MasterTable = self.original_dataframe.copy()
            else:
                self.master.MasterTable = self.original_dataframe[common_cols].copy()
            

            for row in self.filter_rows[:]:
                try:
                    row['frame'].destroy()
                except Exception as e:
                    print(f"Frame destroy error: {e}")
            self.filter_rows.clear()
            self.add_filter_row()
            

            if self.master.winfo_exists():
                self.after(10, self.master.update_table)
            messagebox.showinfo("Success", "All filters cleared and data reset!")
        except Exception as e:
            import traceback
            print("Exception in clear_filters:", e)
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to clear filters:\n{str(e)}")




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

        def new_deleteColumn(*args, **kwargs):
            result = self._original_deleteColumn(*args, **kwargs)
            self._sync_columns_immediately()
            return result

        self.table.deleteColumn = new_deleteColumn

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

    def handle_table_change(self, event=None):
        self.after(100, self._sync_columns_immediately)

    def handle_column_deletion(self, event=None):
        self._sync_columns_immediately()

    def _sync_columns_immediately(self, event=None):
        try:
            current_columns = self.MasterTable.columns.tolist()
            if current_columns != self.previous_columns:
                self.previous_columns = current_columns
                self._update_filter_dropdowns()
                for child in self.winfo_children():
                    if isinstance(child, AdvancedFilterWindow):
                        child.update_column_dropdowns(current_columns)
        except Exception as e:
            print(f"Error syncing columns: {e}")

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
            self.filter_sections.append({'combobox': combo, 'entry': entry})


        btn_frame = ttk.Frame(center_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky='ew')
        for i in range(4):
            btn_frame.columnconfigure(i, weight=1)

        self.advanced_btn = ttk.Button(btn_frame, text="Advanced Filters", command=self.open_advanced_filters)
        self.advanced_btn.grid(row=0, column=0, padx=5, pady=4, sticky='ew')
        self.apply_btn = ttk.Button(btn_frame, text="Apply Filters", command=self.apply_filters)
        self.apply_btn.grid(row=0, column=1, padx=5, pady=4, sticky='ew')
        self.clear_btn = ttk.Button(btn_frame, text="Clear Filters", command=self.clear_filters)
        self.clear_btn.grid(row=0, column=2, padx=5, pady=4, sticky='ew')

        self.export_menu = Menu(self, tearoff=0)
        self.export_menu.add_command(label="Export as CSV", command=self.export_csv)
        self.export_menu.add_command(label="Export as TSV", command=self.export_tsv)
        self.export_menu.add_command(label="Export as VCF", command=self.export_to_vcf)

        def show_export_menu(event):
            self.export_menu.post(event.x_root, event.y_root)

        self.export_btn = ttk.Button(btn_frame, text="Export as CSV/TSV/VCF")
        self.export_btn.grid(row=0, column=3, padx=5, pady=4, sticky='ew')
        self.export_btn.bind("<Button-1>", show_export_menu)



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
                items = [v.strip() for v in re.split(r'[,\s]+', vals)]
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        items = [float(x) if '.' in x else int(x) for x in items]
                    except ValueError:
                        continue
                df = df[df[col].isin(items)]
            self.MasterTable = df
            self.update_table()
            messagebox.showinfo("Success", f"Filters applied successfully!\n{len(df)} rows match the filters.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply filters:\n{str(e)}")

    def clear_filters(self):
        if not self.has_data_loaded():
            self.show_no_data_message("clear filters")
            return
        try:
            current_columns = self.MasterTable.columns
            common_cols = [col for col in current_columns if col in self.original_MasterTable.columns]
            self.MasterTable = self.original_MasterTable[common_cols].copy()
            for sec in self.filter_sections:
                sec['combobox'].set('')
                sec['entry'].delete(0, END)
            self._sync_columns_immediately()
            self.update_table()
            messagebox.showinfo("Success", "All filters cleared and data reset!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear filters:\n{str(e)}")

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
                    messagebox.showinfo("Success", "CSV files loaded successfully!")
                elif ext == ".tsv": 
                    self._load_tsv(filepaths)
                    messagebox.showinfo("Success", "TSV files loaded successfully!")
                elif ext in [".vcf", ".gz"]: 
                    self._load_vcf(filepaths)
                    messagebox.showinfo("Success", "VCF files loaded successfully!")
                else: 
                    messagebox.showerror("Error","Unsupported file type.")
            else:
                messagebox.showerror("Error","Cannot mix different file types.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load files:\n{str(e)}")

    def _load_csv(self, fps):
        data = []
        for f in fps:
            try:
                df = pd.concat(pd.read_csv(f, chunksize=100000, low_memory=False), ignore_index=True)
                df["File_Name"] = os.path.basename(f)
                data.append(df)
            except Exception as e:
                print(e)
        self._finalize_load(data, "CSV")

    def _load_tsv(self, fps):
        data = []
        for f in fps:
            try:
                df = pd.concat(pd.read_csv(f, sep='\t', chunksize=100000, low_memory=False), ignore_index=True)
                df["File_Name"] = os.path.basename(f)
                data.append(df)
            except Exception as e:
                print(e)
        self._finalize_load(data, "TSV")

    def _load_vcf(self, fps):
        data = []
        for f in fps:
            try:
                reader = vcf.Reader(filename=f)
                self.vcf_headers[os.path.basename(f)] = reader
                vdfs = list(self.parse_vcf(reader, os.path.basename(f)))
                if vdfs:
                    df = pd.concat(vdfs, ignore_index=True)
                    df["File_Name"] = os.path.basename(f)
                    data.append(df)
            except Exception as e:
                print(e)
        self._finalize_load(data, "VCF")

    def parse_vcf(self, reader, filename, batch_size=1000):
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
                        sample = rec.samples[0]
                        row['GT'] = getattr(sample.data, 'GT', None)
                batch.append(row)
                
                if len(batch) >= batch_size:
                    yield pd.DataFrame(batch)
                    batch = []
            if batch:
                yield pd.DataFrame(batch)
        except Exception as e:
            print(e)
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
        AdvancedFilterWindow(self, self.MasterTable)

    def export_csv(self):
        if not self.has_data_loaded():
            self.show_no_data_message("export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.MasterTable.to_csv(path, index=False)
            messagebox.showinfo("Success", "CSV file exported successfully.")

    def export_tsv(self):
        if not self.has_data_loaded():
            self.show_no_data_message("export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".tsv", filetypes=[("TSV files", "*.tsv")])
        if path:
            self.MasterTable.to_csv(path, index=False, sep='\t')
            messagebox.showinfo("Success", "TSV file exported successfully.")

    def export_to_vcf(self):
        if not self.has_data_loaded():
            self.show_no_data_message("export to VCF")
            return

        required_columns = {'Chrom', 'Pos', 'Ref', 'Alt'}
        if not required_columns.issubset(self.MasterTable.columns):
            messagebox.showerror(
                "Missing Columns",
                "VCF export requires these essential columns: Chrom, Pos, Ref, Alt."
                "Please restore or avoid deleting them before exporting."
            )
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".vcf", filetypes=[("VCF files", "*.vcf")])
        if not filepath:
            return
        try:
            grouped = self.MasterTable.groupby("File_Name")
            with open(filepath, 'w') as vcf_out:
                for fname, df in grouped:
                    if fname not in self.vcf_headers:
                        raise ValueError("VCF header for file '{}' is missing. Cannot export non-VCF input.".format(fname))
                    reader = self.vcf_headers[fname]
                    writer = vcf.Writer(vcf_out, reader)
                    for _, row in df.iterrows():
                        record = vcf.model._Record(
                            CHROM=row.get('Chrom', '.'),
                            POS=int(row.get('Pos', 1)),
                            ID=row.get('ID', '.'),
                            REF=row.get('Ref', 'N'),
                            ALT=[vcf.model._Substitution(alt) for alt in str(row.get('Alt', '.')).split(',') if alt != '.'],
                            QUAL=float(row['Qual']) if 'Qual' in row and not pd.isna(row['Qual']) else None,
                            FILTER=str(row.get('Filter', 'PASS')).split(';') if row.get('Filter', 'PASS') != 'PASS' else [],
                            INFO={k: self._parse_info_value(row[k]) for k in reader.infos if k in row and pd.notna(row[k])},
                            FORMAT=None,
                            sample_indexes=None,
                            samples=[]
                        )
                        writer.write_record(record)
                writer.close()
            messagebox.showinfo("Success", "Filtered VCF exported successfully!")
        except Exception as e:
            messagebox.showerror("Error", "VCF export cannot be done with a CSV/TSV input or if VCF headers are missing.")

    def _parse_info_value(self, val):
        if pd.isna(val):
            return None
        if isinstance(val, str) and ',' in val:
            return val.split(',')
        return val

if __name__ == "__main__":
    app = MasterTableApp()
    app.mainloop()
