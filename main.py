import sys
import subprocess
import threading
import time
import logging
import psutil
import os  # Add this import for os functions
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from colorama import init

# Initialize Colorama (For Windows Terminal Colors)
init(autoreset=True)

# Configurable Settings
AEGISUM_CLI = "aegisum-cli.exe"  # Path to CLI
MINING_DELAY = 2  # Delay in seconds between mining attempts
LOG_FILE = "miner.log"
running = False  # Mining state

# Setup Logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

class MiningThread(QThread):
    """Thread for mining to avoid UI freezing"""
    mining_result = pyqtSignal(str)
    blocks_mined_signal = pyqtSignal(int)  # Signal to update number of blocks mined
    mining_data_signal = pyqtSignal(str)  # Signal to update mining data
    
    def __init__(self, wallet_address):
        super().__init__()
        self.wallet_address = wallet_address
        self.running = True
        self.blocks_mined = 0  # Tracks the number of blocks mined

    def run(self):
        """Mining process in background thread."""
        try:
            while self.running:
                subprocess.run([AEGISUM_CLI, "generatetoaddress", "1", self.wallet_address], check=True)
                self.blocks_mined += 1
                self.blocks_mined_signal.emit(self.blocks_mined)  # Update mined blocks count
                self.mining_result.emit("Block mined successfully!")
                self.update_mining_data()  # Update mining data every cycle
                time.sleep(MINING_DELAY)
        except subprocess.CalledProcessError as e:
            self.mining_result.emit(f"ERROR: Mining failed: {e}")
            logging.error(f"Mining error: {e}")
            self.mining_result.emit("Retrying in 5 seconds...")
            time.sleep(5)

    def stop(self):
        """Stop the mining process."""
        self.running = False

    def update_mining_data(self):
        """Fetch mining data and update it."""
        try:
            result = subprocess.check_output([AEGISUM_CLI, "getmininginfo"], text=True)
            self.mining_data_signal.emit(result.strip())  # Send the raw result to the UI
        except subprocess.CalledProcessError as e:
            self.mining_result.emit(f"ERROR: Unable to fetch mining data: {e}")
            logging.error(f"Mining data error: {e}")

class AppWindow(QWidget):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegisum MinerUI version1.0")
        self.setGeometry(200, 200, 800, 600)

        # UI elements
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()

        # Display area for mining result, status, and logs
        self.status_label = QLabel("Status: Waiting to start mining...")
        self.balance_label = QLabel("Balance: Not Checked")
        self.mining_data_label = QLabel("Mining Info: Fetching...")
        self.logs_text_edit = QTextEdit()
        self.logs_text_edit.setReadOnly(True)

        # Buttons for actions
        self.start_button = QPushButton("Start Mining")
        self.stop_button = QPushButton("Stop Mining")
        self.check_balance_button = QPushButton("Check Balance")
        self.view_logs_button = QPushButton("View Logs")

        # Layout setup
        layout.addWidget(self.status_label)
        layout.addWidget(self.balance_label)
        layout.addWidget(self.mining_data_label)
        layout.addWidget(self.logs_text_edit)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.check_balance_button)
        layout.addWidget(self.view_logs_button)

        self.setLayout(layout)

        # Connect buttons to their functions
        self.start_button.clicked.connect(self.start_mining)
        self.stop_button.clicked.connect(self.stop_mining)
        self.check_balance_button.clicked.connect(self.check_balance)
        self.view_logs_button.clicked.connect(self.view_logs)

        # Timer for real-time balance check
        self.balance_timer = QTimer(self)
        self.balance_timer.timeout.connect(self.check_balance)
        self.balance_timer.start(1000)  # Update every second

        # Timer for real-time mining data update
        self.mining_data_timer = QTimer(self)
        self.mining_data_timer.timeout.connect(self.fetch_mining_data)
        self.mining_data_timer.start(1000)  # Update every second

    def start_mining(self):
        """Start mining when the button is clicked"""
        wallet_address = self.get_wallet_address()
        if wallet_address:
            self.mining_thread = MiningThread(wallet_address)
            self.mining_thread.mining_result.connect(self.update_mining_result)
            self.mining_thread.blocks_mined_signal.connect(self.update_mining_status)
            self.mining_thread.mining_data_signal.connect(self.update_mining_data)
            self.mining_thread.start()
            self.status_label.setText("Status: Mining started...")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.update_mining_result("Error: Could not get wallet address.")

    def stop_mining(self):
        """Stop mining when the button is clicked"""
        if hasattr(self, 'mining_thread') and self.mining_thread.isRunning():
            self.mining_thread.stop()
            self.status_label.setText("Status: Mining stopped.")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def check_balance(self):
        """Check the wallet balance"""
        try:
            result = subprocess.check_output([AEGISUM_CLI, "getbalance"], text=True).strip()
            self.balance_label.setText(f"Balance: {result} AEG")
            logging.info(f"Checked balance: {result} AEG")
        except subprocess.CalledProcessError as e:
            self.balance_label.setText(f"ERROR: {e}")
            logging.error(f"Error checking balance: {e}")

    def view_logs(self):
        """Display logs in the text edit area"""
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
            with open(LOG_FILE, "r") as log_file:
                self.logs_text_edit.setText(log_file.read())
        else:
            self.logs_text_edit.setText("No logs found or log file is empty.")

    def update_mining_result(self, message):
        """Update the mining result in logs and status"""
        self.logs_text_edit.append(message)
        logging.info(message)

    def update_mining_status(self, blocks_mined):
        """Update the mining status with number of blocks mined"""
        self.status_label.setText(f"Status: Mining... {blocks_mined} blocks mined.")

    def update_mining_data(self, raw_data):
        """Update the UI with mining data"""
        try:
            mining_info = self.format_mining_data(raw_data)
            self.mining_data_label.setText(mining_info)
        except Exception as e:
            logging.error(f"Error formatting mining data: {e}")

    def fetch_mining_data(self):
        """Fetch mining data every second and update UI"""
        try:
            result = subprocess.check_output([AEGISUM_CLI, "getmininginfo"], text=True)
            self.update_mining_data(result.strip())  # Update UI with real-time mining data
        except subprocess.CalledProcessError as e:
            self.mining_result.emit(f"ERROR: Unable to fetch mining data: {e}")
            logging.error(f"Mining data error: {e}")

    def format_mining_data(self, raw_data):
        """Format raw mining data into a readable string"""
        data = eval(raw_data)  # This assumes the mining data is returned as a dictionary-like string
        mining_info = (
            f"Blocks: {data['blocks']}\n"
            f"Current Block Weight: {data['currentblockweight']}\n"
            f"Difficulty: {data['difficulty']}\n"
            f"Network Hashrate (H/s): {data['networkhashps']}\n"
            f"Pooled Transactions: {data['pooledtx']}\n"
            f"Chain: {data['chain']}\n"
            f"Warnings: {data['warnings']}"
        )
        return mining_info

    def get_wallet_address(self):
        """Retrieve a new wallet address for mining"""
        try:
            result = subprocess.check_output([AEGISUM_CLI, "getnewaddress"], text=True).strip()
            return result
        except subprocess.CalledProcessError as e:
            self.logs_text_edit.append(f"ERROR: Failed to retrieve wallet address: {e}")
            logging.error(f"Error getting wallet address: {e}")
            return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())
