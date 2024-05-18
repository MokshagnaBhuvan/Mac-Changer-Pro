import tkinter as tk
from tkinter import messagebox
import random
import subprocess
import os
import threading

class MACChangerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("MAC Changer Pro")
        
        self.label_current_mac = tk.Label(master, text="Current MAC Address:")
        self.label_current_mac.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.entry_current_mac = tk.Entry(master, width=20, state="readonly", bg="#f0f0f0")
        self.entry_current_mac.grid(row=0, column=1, padx=10, pady=5)
        
        self.label_new_mac = tk.Label(master, text="New MAC Address:")
        self.label_new_mac.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.entry_new_mac = tk.Entry(master, width=20)
        self.entry_new_mac.grid(row=1, column=1, padx=10, pady=5)
        
        self.button_generate_random = tk.Button(master, text="Generate Random MAC", command=self.generate_random_mac)
        self.button_generate_random.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="we")
        
        self.button_apply = tk.Button(master, text="Apply", command=self.apply_mac)
        self.button_apply.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="we")
        
        self.button_reset_mac = tk.Button(master, text="Reset MAC Address", command=self.reset_mac)
        self.button_reset_mac.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="we")
        
        self.label_info = tk.Label(master, text="Note: This tool requires administrative privileges to change MAC address.")
        self.label_info.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="we")
        
        # Update current MAC address when GUI initializes
        self.update_current_mac()
        
    def update_current_mac(self):
        current_mac = self.get_current_mac()
        print(f"Current MAC: {current_mac}")  # Debug print to check the MAC address
        self.entry_current_mac.config(state="normal")
        self.entry_current_mac.delete(0, tk.END)
        if current_mac:
            self.entry_current_mac.insert(0, current_mac)
        else:
            self.entry_current_mac.insert(0, "N/A")
        self.entry_current_mac.config(state="readonly")
        
    def get_current_mac(self):
        try:
            result = subprocess.run(["ifconfig"], capture_output=True, text=True)
            interface_name = self.get_interface_name()
            if interface_name:
                print(f"Interface name: {interface_name}")
                for line in result.stdout.split('\n'):
                    if interface_name in line:
                        print(f"Line with interface name: {line}")
                        mac_line = next(line for line in result.stdout.split('\n') if 'ether' in line)
                        print(f"Line with MAC address: {mac_line}")
                        return mac_line.split()[1]
            return None
        except Exception as e:
            print("Error:", e)
            return None
    
    def generate_random_mac(self):
        new_mac = "02"
        for _ in range(5):
            new_mac += "".join(random.choice("0123456789ABCDEF") for _ in range(2))
        new_mac = ':'.join(new_mac[i:i+2] for i in range(0, len(new_mac), 2))
        self.entry_new_mac.delete(0, tk.END)
        self.entry_new_mac.insert(0, new_mac)
    
    def apply_mac(self):
        new_mac = self.entry_new_mac.get()
        threading.Thread(target=self.apply_mac_thread, args=(new_mac,)).start()
        
    def apply_mac_thread(self, new_mac):
        interface_name = self.get_interface_name()
        if interface_name:
            print(f"Applying new MAC: {new_mac} to interface: {interface_name}")
            result = subprocess.run(f"sudo ip link set dev {interface_name} down", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error_message(f"Failed to disable the network interface.\n{result.stderr}")
                return
            
            result = subprocess.run(f"sudo ip link set dev {interface_name} address {new_mac}", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error_message(f"Failed to change MAC address.\n{result.stderr}")
                return
            
            result = subprocess.run(f"sudo ip link set dev {interface_name} up", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error_message(f"Failed to enable the network interface.\n{result.stderr}")
                return
            
            self.restart_network_interface(interface_name)
            self.update_current_mac()  # Update current MAC address display
            self.log_change(new_mac)
            self.show_info_message("MAC address changed successfully.")
    
    def reset_mac(self):
        threading.Thread(target=self.reset_mac_thread).start()
    
    def reset_mac_thread(self):
        interface_name = self.get_interface_name()
        if interface_name:
            print(f"Resetting MAC for interface: {interface_name}")
            result = subprocess.run(f"sudo ip link set dev {interface_name} down", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error_message(f"Failed to disable the network interface.\n{result.stderr}")
                return
            
            result = subprocess.run(f"sudo ip link set dev {interface_name} address 00:00:00:00:00:00", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error_message(f"Failed to reset MAC address.\n{result.stderr}")
                return
            
            result = subprocess.run(f"sudo ip link set dev {interface_name} up", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.show_error_message(f"Failed to enable the network interface.\n{result.stderr}")
                return
            
            self.restart_network_interface(interface_name)
            self.update_current_mac()  # Update current MAC address display
            self.show_info_message("MAC address reset successfully.")
    
    def get_interface_name(self):
        try:
            result = subprocess.run(["ip", "link"], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if "state UP" in line:
                    return line.split(':')[1].strip()
            return None
        except Exception as e:
            print("Error:", e)
            return None

    def restart_network_interface(self, interface_name):
        print(f"Restarting network interface: {interface_name}")
        result = subprocess.run(f"sudo systemctl restart networking", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self.show_error_message(f"Failed to restart networking service.\n{result.stderr}")
            return

    def log_change(self, new_mac):
        with open("mac_changer_log.txt", "a") as log_file:
            log_file.write(f"Changed MAC address to: {new_mac}\n")
            
    def show_info_message(self, message):
        messagebox.showinfo("Success", message)
    
    def show_error_message(self, message):
        messagebox.showerror("Error", message)
    
def main():
    root = tk.Tk()
    app = MACChangerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
