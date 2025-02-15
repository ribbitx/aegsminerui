# Aegisum MinerUI version 1.0

## Overview
This Python application provides a user interface for managing the Aegisum Miner. It allows you to mine Aegisum coins, check your balance, view mining data, and review logs in a graphical interface.

## Features
- Start and stop the mining process.
- Display mining status and the number of blocks mined.
- Fetch and display mining information (e.g., network hashrate, difficulty).
- View logs of mining activity.
- Check wallet balance.

## Requirements
- Python 3.x
- `PyQt5` for the GUI
- `psutil` for system monitoring
- `colorama` for colored terminal output

## Installation

1. Clone the repository or download the script.
2. Install the required Python dependencies:

    ```bash
    pip install PyQt5 psutil colorama
    ```

3. Ensure you have Aegisum CLI (`aegisum-cli.exe`) available in the same directory as the script or set the correct path.

4. Run the script:

    ```bash
    python main.py
    ```

## Usage
- **Start Mining**: Click "Start Mining" to begin the mining process. The mining process will continue until you click "Stop Mining."
- **Stop Mining**: Click "Stop Mining" to stop the mining process.
- **Check Balance**: Click "Check Balance" to view your current wallet balance.
- **View Logs**: Click "View Logs" to view mining logs.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
