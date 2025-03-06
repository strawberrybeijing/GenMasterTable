# MasterTableApp


**MasterTableApp** is a user-friendly, secure, and locally operated desktop application designed to handle large-scale genetic variant datasets. It features an intuitive graphical user interface (GUI) that simplifies filtering, merging, summarizing, and visualizing annotated variants from DNA and RNA sequencing data. The application supports both **VCF** and **CSV** file formats and is accessible to clinicians, geneticists, and researchers without requiring programming expertise.

## Features

- **Standalone Desktop Application**: No need for command-line execution or database setup.
- **Supports Large Datasets**: Handles millions of variants across hundreds of annotations.
- **Multiple Input Formats**: Accepts **VCF** and **CSV** files from DNA and RNA sequencing.
- **Advanced Filtering System**: Enables multi-tier list-based (str) filtering and threshold-based quantitative filtering.
- **Merging Capability**: Combines multiple annotated files for **cohort-level analysis**.
- **Interactive Data Visualization**: Provides sorting, indexing, and data transformation functions.
- **Secure & Local**: No cloud upload, ensuring patient data privacy.
- **Cross-Platform Compatibility**: Available for **Windows x64** and **macOS**.
- **Completely Free**: Open-source and available for research use.

## Installation

### Download the Latest Release

Visit the **[GitHub Releases](https://github.com/strawberrybeijing/MasterTableAPP/releases)** page and download the latest version for your operating system:

- **Windows**: Download `MasterTableApp.exe`
- **macOS**: Download `MasterTableApp.app`

### System Requirements
- **Operating System**: Windows (64-bit) or macOS

## Usage

### Launching MasterTableApp
1. **Windows**: Double-click `MasterTableApp.exe`.
2. **macOS**: Open `MasterTableApp.app`.
If you encounter a security warning, navigate to **System Preferences > Security & Privacy** and allow the app to run.

### Loading Data
- **VCF Files**: Directly import individual or multiple **annotated VCF** files.
- **CSV Files**: Load and merge CSV files for large-scale analysis.

### Filtering and Summarization
- Apply advanced column-based filtering using the main control frame, e.g. a list of genes, patient IDs, pedigree IDs (seperate by comma/space).
- Set thresholds for pathogenicity scores (e.g., CADD, REVEL, AlphaMissense) by using the toolbar on the right side of the GUI. Click the button with a small yellow key icon, which displays 'Filter Table' when hovered over.
- Sort, index, and transform genomic data for cohort-level analysis by right-clicking on the column header.

### Data Export
- Copy and paste filtered datasets into Excel. (click on the left above coner of the datasheet is select all, then go the toolbar on the right side of the GUI, click the button with 2 sheets together (the 5th) icon, which displays 'copy table to clipboard' when hovered over.
- Paste the copied data into a blank Excel sheet for further analysis.

## Application in Genomic Research
MasterTableApp has been successfully applied to a whole-genome sequencing dataset of **935 subjects**, analyzing **2.1 million variants** across **181 annotations**. It enables efficient variant filtering for disease-associated genes, including **ANOS1, CHD7, DMXL2, FGFR1, PCSK1, POLR3A, SEMA3A, SOX10, TAC3**, and many others.

## Citation
If you use MasterTableApp in your research, please cite:

> **MasterTableApp: A user-friendly desktop solution for filtering, summarizing, and visualizing large-scale annotated genetic variants**

(Paper link will be added once published)

## License
MasterTableApp is released under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## Contributions
We welcome contributions! Feel free to **submit issues, feature requests, or pull requests** to improve MasterTableApp.

## Contact
For support or questions, please open an **[issue on GitHub](https://github.com/strawberrybeijing/MasterTableAPP/issues)**.

---
**GitHub Repository:** [MasterTableApp](https://github.com/strawberrybeijing/MasterTableAPP)
