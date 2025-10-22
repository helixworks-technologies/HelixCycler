# HelixCycler
<<<<<<< Updated upstream

An easy-to-use Python application to run an Opentrons Thermocycler independently from an Opentrons Robot.

<img src="https://github.com/helixworks-technologies/HelixCycler/blob/main/HelixCycler.png" width=90% height=85%>

<img src="HelixCycler.png" width="90%" alt="HelixCycler App Screenshot">

## Prerequisites

* **Python:** Version 3.7 or higher recommended.
* **Libraries:** The application relies on several Python libraries.

=======
An easy to use python application to run the OT thermocycler independently from an Opentrons Robot.

<img src="https://github.com/helixworks-technologies/HelixCycler/blob/main/HelixCycler.png" width=90% height=85%>

## Prerequisites

* **Python:** Version 3.13 recommended.
* **Libraries:** The application relies on several Python libraries.

---

>>>>>>> Stashed changes
## Installation

1.  **Clone the Repository:**
    ```bash
<<<<<<< Updated upstream
    git clone <your-repository-url>
    cd HelixCycler
    ```
2.  **Install Dependencies:**
    Make sure you have `pip` installed. Then, run the following command in your terminal within the `HelixCycler` directory:
=======
    git clone https://github.com/helixworks-technologies/HelixCycler.git
    cd HelixCycler-main
    ```
2.  **Install Dependencies:**
    Make sure you have `pip` installed. Then, run the following command in your terminal within the `HelixCycler-main` directory:
>>>>>>> Stashed changes
    ```bash
    pip install -r requirements.txt
    ```
    This will install `customtkinter`, `pyserial`, and `matplotlib`.

<<<<<<< Updated upstream
=======
---

>>>>>>> Stashed changes
## Running the Application

1.  **Navigate to the Directory:**
    Open your terminal or command prompt and navigate to the directory containing the `helixcycler.py` file.
2.  **Run the Script:**
    ```bash
    python helixcycler.py
    ```
<<<<<<< Updated upstream
=======
This should open a GUI that looks like this:

<img src="https://github.com/helixworks-technologies/HelixCycler/blob/main/HelixCycler_GUI.png" width=90% height=85%>

---
>>>>>>> Stashed changes

## Connecting to the Thermocycler

1.  **Refresh Ports:** When the app launches, click the **"Refresh"** button to scan for connected devices.
2.  **Select Port:** Choose the correct serial port for your Opentrons Thermocycler from the dropdown menu.
    * On **Windows**, this typically looks like `COM<number>`.
    * On **Linux** or **Mac**, this looks like `/dev/ttyACM<number>` or `/dev/cu.usbmodem<number>`.
3.  **Connect:** Click the **"Connect"** button. The status label should turn green and read "Connected". All device controls will become active.
4.  **Disconnect:** To disconnect, click the **"Disconnect"** button (the same button, its text changes).

<<<<<<< Updated upstream
=======
---

>>>>>>> Stashed changes
## User Interface Overview

The application window is divided into several sections:

<<<<<<< Updated upstream
### 1. Title Bar & Connection

* **Title:** Displays the application name.
* **Lid Controls:**
    * **Open Lid:** Opens the thermocycler lid. (Enabled when connected).
    * **Close Lid:** Closes the thermocycler lid. (Enabled when connected).
=======
### 1. Lid Controls & Connection

* **Lid Controls:**
    * **Open Lid:** Opens the thermocycler lid (Enabled when connected).
    * **Close Lid:** Closes the thermocycler lid (Enabled when connected).
>>>>>>> Stashed changes
* **Connection Controls:**
    * **Serial Port Dropdown:** Lists available serial ports.
    * **Refresh:** Rescans for available serial ports.
    * **Connect/Disconnect:** Connects to or disconnects from the selected port.
    * **Status Label:** Shows the connection status ("Disconnected", "Connected", "Failed", etc.).

### 2. Presets & Actual Temperatures

This section allows manual control and provides live temperature feedback when connected and idle.

* **Preset Temperatures (Left Side):**
<<<<<<< Updated upstream
    * **Set Lid Temperature °C:** Enter a target temperature (37°C - 110°C) and click **"Set Lid Temp"**. The lid heats passively and cools ambiently (no active cooling).
=======
    * **Set Lid Temperature °C:** Enter a target temperature (37°C - 105°C) and click **"Set Lid Temp"**. The lid heats passively and cools ambiently (no active cooling).
>>>>>>> Stashed changes
    * **Set Plate Temperature °C:** Enter a target temperature (4°C - 99°C) and click **"Set Plate Temp"**.
    * **Deactivate all:** Stops heating/cooling for both the lid and the plate.
* **Actual Temperatures (Right Side):**
    * Displays the current, real-time temperature reported by the thermocycler's lid and plate sensors. This is updated automatically every few seconds when the device is connected and *not* running a protocol.

### 3. Protocol Control

This section manages loading and running automated protocols from CSV files.

* **Protocol Setup (Displayed when Idle):**
    * **Import Protocol CSV file:**
        * **Experiment Name:** Enter a descriptive name for your run (must be > 5 characters).
        * **Import:** Click to open a file dialog and select your protocol `.csv` file. The file path will be displayed.
        * **Run Protocol:** Becomes active (red) when connected, a valid CSV is loaded, and an experiment name is entered. Click to start the protocol.
* **Protocol Running (Displayed during a Run):**
    * **Status Display:** Shows the current stage, cycle, and step number.
    * **Current Lid Temperature:** Displays the live lid temperature during the run.
    * **Current Plate Temperature:** Displays the live plate temperature during the run.
    * **Step Time Remaining:** Shows the countdown timer (in seconds) for the current timed step.
    * **Skip Current Step:** Prompts for confirmation. If confirmed, sends a command to immediately end the current heating/cooling/holding step and proceed to the next one in the protocol.
    * **Emergency Stop:** Prompts for confirmation. If confirmed, immediately halts all thermocycler activity, stops the protocol entirely, and resets the UI to the setup screen.
* **Protocol Info (Right Side):**
    * Displays a formatted summary of the steps loaded from the imported CSV file.

<<<<<<< Updated upstream
=======
---

>>>>>>> Stashed changes
## CSV Protocol Format

Protocols are defined in `.csv` (Comma Separated Values) files. You can create these using spreadsheet software (like Google Sheets, Excel, LibreOffice Calc) and exporting as `.csv`.

**See this Google Sheet for an example:**
[https://docs.google.com/spreadsheets/d/1APvXpImfQ8JtOwSfbmaLQZdP6SYDe2T5pF8ugUPLfnM/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1APvXpImfQ8JtOwSfbmaLQZdP6SYDe2T5pF8ugUPLfnM/edit?usp=sharing)
*(Make a copy for yourself to edit)*

**Key Commands (Must be in the first column):**

* **`CYCLES`**
    * **Purpose:** Defines the start of a new stage and how many times the subsequent `STEP` commands should repeat.
    * **Format:**
        * Column A: `CYCLES`
        * Column B: Number of repetitions (e.g., `1`, `30`). If you don't want to cycle, use `1`.
* **`STEP`**
    * **Purpose:** Sets target temperatures and hold times. Multiple `STEP` commands can follow a `CYCLES` command and will execute sequentially within each cycle.
    * **Format:**
        * Column A: `STEP`
        * Column B: *(Leave Blank)*
        * Column C: Plate Target Temperature (°C) (e.g., `95`, `60`, `4`). **Required.**
        * Column D: Hold Time (seconds) (e.g., `30`, `60`, `180`). Leave blank for infinite hold (until the next step or end of protocol).
<<<<<<< Updated upstream
        * Column E: Lid Target Temperature (°C) (e.g., `105`). Leave blank to keep the lid at its current target temperature. *Note: It's generally recommended to set the lid temperature once at the beginning or via presets, as it heats/cools slowly.*
=======
        * Column E: Lid Target Temperature (°C) (e.g., `105`). Leave blank to keep the lid at its current target temperature. *Note: It's generally recommended to set the lid temperature once at the beginning or via presets, as it heats/cools slowly*.
>>>>>>> Stashed changes
* **`DEACTIVATE_ALL`**
    * **Purpose:** Turns off heating/cooling for both the plate and the lid. Usually placed near the end of the protocol.
    * **Format:**
        * Column A: `DEACTIVATE_ALL`
        * Columns B-E: *(Leave Blank)*
* **`END&GRAPH`**
    * **Purpose:** Marks the official end of the protocol and generates a plot showing the temperature profile (Lid and Plate vs. Time) throughout the run. The plot may appear behind the main application window.
    * **Format:**
        * Column A: `END&GRAPH`
        * Columns B-E: *(Leave Blank)*

**Important Notes:**

* Every protocol stage **must** start with a `CYCLES` command.
* Save your spreadsheet as a `.csv` file before importing.
* The order is important: `CYCLES` -> one or more `STEP`s -> (optional `DEACTIVATE_ALL`) -> (optional `END&GRAPH`). You can have multiple `CYCLES` stages.
<<<<<<< Updated upstream


=======
>>>>>>> Stashed changes




