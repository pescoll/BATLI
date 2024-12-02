# BATLI: Backtracking Analysis of Time-Lapse Images

BATLI stands for **Backtracking Analysis of Time-Lapse Images**. It is a bioinformatics tool designed for the retrospective analysis of dynamic cellular activities using time-lapse microscopy. BATLI specializes in quantitative measurements within high-content assays and can backtrack properties such as fluorescence and morphology in individual cells, including various subcellular structures like nuclei, mitochondria, lysosomes, or intracellular bacteria.

Using BATLI, you can classify cellular fates based on a single dynamic parameter and examine all other parameters through retrospective analysis for each identified category of cellular fate. This tool enables you to link certain dynamic parameters observed at the start of the time-lapse with specific cellular outcomes observed at the conclusion of the time-lapse. While these correlations can be revealing, they do not necessarily establish a cause-and-effect relationship. However, the insights gained from BATLI can indicate which parameters might be directly associated with particular cellular fates, valuable for developing predictive models for specific cellular outcomes.

For more details, please refer to the [BATLI paper](https://www.biorxiv.org/content/10.1101/2024.10.28.620606v1.full.pdf+html).

BATLI has been developed by Mariatou Dramé, Dmitry Ershov, Jean-Yves Tinevez and Pedro Escoll (Institut Pasteur, Paris)

---

## Table of Contents

- [BATLI Modules](#batli-modules)
  - [Cleaner](#cleaner)
  - [Loader](#loader)
  - [Viewer](#viewer)
  - [Backtracking](#backtracking)
- [Preparing Datasets for BATLI Analysis](#preparing-datasets-for-batli-analysis)
- [Dependencies](#dependencies)
- [Installation Instructions](#installation-instructions)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Additional Information](#additional-information)
- [License](#license)
- [Citation](#citation)
- [Contributing](#contributing)

---

## BATLI Modules

BATLI is composed of four modules that are typically used sequentially:

1. **Cleaner**
2. **Loader**
3. **Viewer**
4. **Backtracking**

### Cleaner

The **Cleaner** module imports the CSV dataset from your image analysis and automatically adjusts it for subsequent use. In this module, you can rename specific parameters (columns in your CSV file) to make them shorter or more descriptive. These revised names will then be displayed in the subsequent modules. The Cleaner module is designed to standardize datasets acquired from various equipment and analyzed through different image analysis pipelines, such as those combining automated time-lapse microscopy with image analysis tools like [CellProfiler](https://cellprofiler.org/) or [TrackMate](https://imagej.net/plugins/trackmate/).

### Loader

Use the **Loader** module to import cleaned CSV datasets. This module displays the metadata of the dataset, offering a summary of your experiment. It reveals the number of wells analyzed, the count of timepoints, and the number of single-cell trajectories examined in each well. Additionally, the module presents a table showcasing all the columns along with the first 20 rows of your dataset for review. If you need to rename any parameter (column), you can return to the Cleaner module to make those changes.

### Viewer

In the **Viewer** module, you can select various parameters from the dataset, such as bacterial vacuole size or cell death markers, and visualize single-cell trajectories from your tracked time-lapse imaging experiments. The Viewer offers multiple normalization methods for data analysis:

- **Normalization to the first timepoint**
- **Custom normalization to a chosen range of timepoints**
- **Delta normalization** (calculates the increment of each timepoint relative to the previous one)
- **Curve fitting** (smooths the data curve using polynomial regression)

### Backtracking

The **Backtracking** module classifies the trajectories according to a defined cellular fate (e.g., bacterial replication, cell death, differentiation) and a threshold that triggers the classification of trajectories into two classes. Once the classification criteria are set, this module performs backtracking (retrospective) analyses of each parameter measured in each class.

Outputs include:

- **Single-cell datasets** organized according to cell fate classes and selected measured parameters
- **Graphs** showing the progression of single-cell parameters over time, color-grouped by their class:
  - **Bold lines** represent the median value of the selected parameter at each timepoint for each class.
  - **Shaded areas** represent the 95% confidence interval around the median, calculated using bootstrapping.
  - **Light red and blue lines** are the individual single-cell trajectories for class_1 (red) and class_0 (blue) cells.
- All results are downloadable as **figures (PNG files)** and **tables (CSV files)** by clicking "Download Results".

---

## Preparing Datasets for BATLI Analysis

To use BATLI effectively, prepare your datasets as follows:

1. **Collect time-lapse images** using automated confocal microscopy.
2. **Identify cellular compartments** through image segmentation.
3. **Track single cells over time**.
4. **Export single-cell data** as a CSV file, including all measured parameters and single-cell IDs of tracked cells.
5. BATLI is designed to work seamlessly with datasets generated by [Harmony 4.9](https://www.perkinelmer.com/fr/product/harmony-4-9-office-license-hh17000010) (PerkinElmer) for image analysis and cell tracking.
6. Alternatively, you can use open-source software like [CellProfiler](https://cellprofiler.org/) or [TrackMate](https://imagej.net/plugins/trackmate/) for image analysis and cell tracking tasks. Ensure that you modify the BATLI code appropriately to accurately interpret the CSV files exported from these tools.
7. Once your dataset is prepared, you're ready to unlock the full potential of backtracking your time-lapse experiments with BATLI.

---

## Dependencies

Ensure that the following dependencies are installed on your system:

- **Python 3.7 or higher**
- **Git**
- **Python Packages** (these will be installed by the launcher script):
  - `flask`
  - `pandas`
  - `seaborn`
  - `matplotlib`
  - `numpy`
  - `werkzeug`

Additional dependencies for the launcher script:

- **Windows**:
  - None beyond the above.
- **macOS**:
  - **Homebrew** (for package management)
- **Linux**:
  - `lsof` (for checking open ports)
  - `netcat` (`nc`, for checking if the Flask app has started)
  - `xdg-utils` or `GNOME` utilities (for opening the web browser)

---

## Installation Instructions

### Windows

Download the file `Launch_BATLI.bat` and move it to a convenient location on your computer. 
Then, double-click on the icon to install and run it. 
You can click this icon everytime you want to run BATLI, it will check that the software is updated and will open BATLI in your browser to start your analyses.

Alternatively, or if you find installation problems, you can install BATLI step by step:

1. **Install Python 3.7 or Higher**

   - Download and install Python from the [official website](https://www.python.org/downloads/windows/).
   - During installation, check the option to **Add Python to PATH**.

2. **Install Git**

   - Download and install Git for Windows from [git-scm.com](https://git-scm.com/download/win).

3. **Download the BATLI Launcher Script**

   - Save the `Launch_BATLI.bat` script to a convenient location on your computer.

4. **Run the Launcher Script**

   - Double-click on `Launch_BATLI.bat` to run it.
   - The script will:
     - Check for dependencies.
     - Clone or update the BATLI repository in your user directory.
     - Set up a Python virtual environment.
     - Install the required Python packages.
     - Start the Flask application.
     - Open your default web browser to [http://localhost:5001](http://localhost:5001).

5. **Using BATLI**

   - Use BATLI through your web browser.
   - Leave the command window open while BATLI is running.
   - To stop the application, return to the command window and press any key.

### macOS

If [Homebrew](https://brew.sh/) is already installed in your computer: 
Download the file `Launch_BATLI.app.zip` and unzip it. 
Then, move `Launch_BATLI.app` to the Applications folder on your computer. 
Double-click on the app icon to install BATLi and run it. 
You can click the app everytime you want to run BATLI, it will check that the software is updated and will open BATLI in your browser to start your analyses.

Alternatively, or if you find installation problems, you can install BATLI step by step:

1. **Install Homebrew (if not already installed)**

   - Open the **Terminal** app.
   - Run the following command:

     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```

2. **Install Python 3 and Git**

   - Run:

     ```bash
     brew install python3 git
     ```

3. **Download the BATLI Launcher Script**

   - Save the `launch_BATLI.sh` script to a convenient location.

4. **Make the Script Executable**

   - In Terminal, navigate to the script's directory:

     ```bash
     cd /path/to/script
     ```

   - Make it executable:

     ```bash
     chmod +x launch_BATLI.sh
     ```

5. **Run the Launcher Script**

   - Run the script:

     ```bash
     ./launch_BATLI.sh
     ```

   - The script will:
     - Check for dependencies.
     - Clone or update the BATLI repository in your home directory.
     - Set up a Python virtual environment.
     - Install the required Python packages.
     - Start the Flask application.
     - Open your default web browser to [http://localhost:5001](http://localhost:5001).

6. **Using BATLI**

   - Use BATLI through your web browser.
   - Leave the Terminal window open while BATLI is running.
   - To stop the application, press `Ctrl+C` in the Terminal.

### Linux

1. **Install Python 3, Git, and Other Dependencies**

   - Open your terminal.
   - Update package lists:

     ```bash
     sudo apt update
     ```

   - Install dependencies:

     ```bash
     sudo apt install python3 python3-pip python3-venv git lsof netcat xdg-utils
     ```

2. **Download the BATLI Launcher Script**

   - Save the `launch_BATLI.sh` script to a convenient location.

3. **Make the Script Executable**

   - In Terminal, navigate to the script's directory:

     ```bash
     cd /path/to/script
     ```

   - Make it executable:

     ```bash
     chmod +x launch_BATLI.sh
     ```

4. **Run the Launcher Script**

   - Run the script:

     ```bash
     ./launch_BATLI.sh
     ```

   - The script will:
     - Check for dependencies.
     - Clone or update the BATLI repository in your home directory.
     - Set up a Python virtual environment.
     - Install the required Python packages.
     - Start the Flask application.
     - Open your default web browser to [http://localhost:5001](http://localhost:5001).

5. **Using BATLI**

   - Use BATLI through your web browser.
   - Leave the Terminal window open while BATLI is running.
   - To stop the application, press `Ctrl+C` in the Terminal.

---

## Additional Information

- **Typical install time on a "normal" desktop computer**: 10-15 minutes.
- **Customization**: BATLI can be customized to work with datasets from various image analysis tools. Modify the code as necessary to interpret your specific CSV file format.
- **Support**: For questions or support, please open an issue on the [GitHub repository](https://github.com/pescoll/BATLI).
- **Contributors**: BATLI software has been developed by Mariatou Dramé, Dmitry Ershov, Jean-Yves Tinevez and Pedro Escoll (Institut Pasteur, Paris)
- **Contribution**: Contributions are welcome! Feel free to fork the repository and submit pull requests with improvements or new features.

---

## License

This project is licensed under the terms of the MIT license.

Copyright (c) 2024 INSTITUT PASTEUR

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Citation

If you use BATLI in your research, please cite:

>  Dramé et al., “Backtracking Metabolic Dynamics in Single Cells Predicts Bacterial Replication in Human Macrophages” bioRxiv 2024.10.28.620606; doi: https://doi.org/10.1101/2024.10.28.620606. [Download](https://www.biorxiv.org/content/10.1101/2024.10.28.620606v1.full.pdf)

---

## Contributing

We welcome contributions from the community! To contribute:

1. **Fork** the repository on GitHub.
2. **Create a new branch** for your feature or bugfix.
3. **Commit** your changes with clear messages.
4. **Push** your branch to your forked repository.
5. **Submit a pull request** to the main repository.

Please ensure your code adheres to the existing style and includes appropriate tests.

---

Thank you for using BATLI! We hope it accelerates your research in analyzing time-lapse images.
