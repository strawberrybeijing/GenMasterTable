# GenMasterTable


**GenMasterTable** is a user-friendly, secure, and locally operated desktop application designed to handle large-scale genetic variant datasets. It features an intuitive graphical user interface (GUI) that simplifies filtering, merging(concatenation), summarizing, and visualizing annotated variants from DNA and RNA sequencing data. The application supports **VCF**,**CSV** and **TSV** file formats and is accessible to clinicians, geneticists, and researchers without requiring programming expertise.

## Citation
If you use GenMasterTable in your research, please cite:

> **GenMasterTable: A user-friendly desktop solution for filtering, summarizing, and visualizing large-scale annotated genetic variants**

(https://doi.org/10.1186/s12859-025-06238-6)

## Features

- **Standalone Desktop Application**: No need for command-line execution or database setup.
- **Supports Large Datasets**: Handles millions of variants across hundreds of annotations.
- **Multiple Input Formats**: Accepts **VCF**,**CSV** and **TSV**  files from DNA and RNA sequencing.
- **Advanced Filtering System**: Enables multi-tier list-based (str) filtering and threshold-based quantitative filtering.
- **Merging Capability**: Combines multiple annotated files for **cohort-level analysis**.
- **Interactive Data Visualization**: Provides sorting, summerizing data transformation functions.
- **Secure & Local**: No cloud upload, ensuring patient data privacy.
- **Cross-Platform Compatibility**: Available for **Windows x64** , **macOS** and **Linux** .
- **Completely Free**: Open-source and available for research use.

## Installation

### Download the Latest Release

Visit the **[GitHub Releases](https://github.com/strawberrybeijing/GenMasterTable/releases)** page and download the latest version for your operating system:

- **Windows**: Download `GenMasterTable_windows.exe`
- **macOS**: Download `GenMasterTable_macOS.zip`
- **Linux**: Download `GenMasterTable_linux`
- **Handbook**: A comprehensive user guide `GenMasterTable_UserGuide_v1.pdf` is also available in the Release section to help you navigate the application.

### System Requirements
- **Operating System**: Windows (64-bit) /macOS /Linux

## Usage

### Launching GenMasterTable
If you encounter a security warning, navigate to **System Preferences > Security & Privacy** and allow the app to run.
1. **Windows**: Double-click `GenMasterTable_windows.exe`.
2. **macOS**: Open `GenMasterTable_macOS.app`.
3. **Linux**: command ./`GenMasterTable_linux`.


### Loading Data
- **VCF Files**: Directly import individual or multiple **annotated VCF** files.
- **CSV/TSV Files**: Load and merge CSV/TSV files for large-scale analysis.

### Filtering and Summarization
- Apply advanced column-based filtering using the main control frame, e.g. a list of genes, patient IDs, pedigree IDs (seperate by comma/space).
- Set thresholds for pathogenicity scores (e.g., CADD, REVEL, AlphaMissense) by using the 'Advanced Filters' function of.
- Sort and transform genomic data for cohort-level analysis by right-clicking on the column header.

### Data Export
- Processed data can be exported to VCF/CSV/TSV

## Application in Genomic Research
GenMasterTable has been successfully applied to a whole-genome sequencing dataset of **935 subjects**, analyzing **2.1 million variants** across **181 annotations**. It enables efficient variant filtering for disease-associated genes, including **ANOS1, CHD7, DMXL2, FGFR1, PCSK1, POLR3A, SEMA3A, SOX10, TAC3**, and many others.

## License
GenMasterTable is released under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## Contributions
We welcome contributions! Feel free to **submit issues, feature requests, or pull requests** to improve GenMasterTable.

## Contact
For support or questions, please open an **[issue on GitHub](https://github.com/strawberrybeijing/GenMasterTable/issues)**.

---
**GitHub Repository:** [GenMasterTable](https://github.com/strawberrybeijing/GenMasterTable)
