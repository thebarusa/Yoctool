import tkinter as tk
from tkinter import ttk
import re
import os

class RpiManager:
    def __init__(self, root_app):
        self.root_app = root_app
        self.root = root_app.root if hasattr(root_app, 'root') else root_app
        
        # --- 1. Supported Machines ---
        self.machines = ["raspberrypi0-wifi", "raspberrypi3", "raspberrypi4", "raspberrypi5"]

        # --- UI Variables ---
        self.rpi_usb_gadget = tk.BooleanVar(value=False)
        self.rpi_enable_uart = tk.BooleanVar(value=True)
        self.license_commercial = tk.BooleanVar(value=True)
        self.rpi_enable_wifi = tk.BooleanVar(value=False)
        self.wifi_ssid = tk.StringVar()
        self.wifi_password = tk.StringVar()
        
        self.frame_wifi = None
        self.tab = None
        self.notebook = None

    # --- Interface for YoctoTool ---

    def is_current_machine_supported(self):
        """Check if the currently selected machine belongs to this manager"""
        return self.root_app.machine_var.get() in self.machines

    def get_required_layers(self):
        """
        Return list of layers needed for this board.
        Format: list of tuples (folder_name, git_url)
        """
        return [
            ("meta-openembedded", "https://git.openembedded.org/meta-openembedded"),
            ("meta-raspberrypi", "https://git.yoctoproject.org/meta-raspberrypi")
        ]

    def get_bblayers_lines(self):
        """
        Return list of lines to append to bblayers.conf
        """
        # Note: We use relative paths assuming layers are inside poky/
        return [
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-oe"\n',
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-python"\n',
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-networking"\n',
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-multimedia"\n',
            'BBLAYERS += "${TOPDIR}/../meta-raspberrypi"\n'
        ]

    # --- UI & Config Logic ---

    def create_tab(self, notebook):
        self.notebook = notebook
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Raspberry Pi Options")
        
        tab_rpi = self.tab
        
        ttk.Checkbutton(tab_rpi, text="Enable USB Gadget Mode (SSH over USB)", variable=self.rpi_usb_gadget).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(tab_rpi, text="(Adds 'dtoverlay=dwc2' & 'modules-load=dwc2,g_ether')").grid(row=0, column=1, sticky="w")
        
        ttk.Checkbutton(tab_rpi, text="Enable UART Console", variable=self.rpi_enable_uart).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(tab_rpi, text="Accept Commercial Licenses", variable=self.license_commercial).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        # Wi-Fi
        ttk.Checkbutton(tab_rpi, text="Enable Wi-Fi Configuration", variable=self.rpi_enable_wifi, command=self.toggle_wifi_fields).grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        self.frame_wifi = ttk.Frame(tab_rpi)
        self.frame_wifi.grid(row=4, column=0, columnspan=2, padx=20, pady=0, sticky="w")
        ttk.Label(self.frame_wifi, text="SSID:").pack(side="left")
        ttk.Entry(self.frame_wifi, textvariable=self.wifi_ssid, width=20).pack(side="left", padx=5)
        ttk.Label(self.frame_wifi, text="Password:").pack(side="left", padx=5)
        ttk.Entry(self.frame_wifi, textvariable=self.wifi_password, width=20, show="*").pack(side="left", padx=5)
        
        self.toggle_wifi_fields()

    def toggle_wifi_fields(self):
        if self.frame_wifi:
            if self.rpi_enable_wifi.get(): self.frame_wifi.grid()
            else: self.frame_wifi.grid_remove()

    def set_visible(self, visible):
        if not self.tab or not self.notebook: return
        try:
             # Logic to hide/show tab based on machine selection
             current_state = self.notebook.tab(self.tab, "state")
             is_hidden = (current_state == "hidden")
             if visible and is_hidden:
                self.notebook.tab(self.tab, state="normal")
             elif not visible and not is_hidden:
                self.notebook.hide(self.tab)
        except: pass

    def parse_config(self, content):
        self.rpi_usb_gadget.set("dtoverlay=dwc2" in content)
        self.rpi_enable_uart.set('ENABLE_UART = "1"' in content)
        self.license_commercial.set("commercial" in content)
        
        wssid = re.search(r'^\s*WIFI_SSID\s*=\s*"(.*?)"', content, re.MULTILINE)
        if wssid:
            self.rpi_enable_wifi.set(True)
            self.wifi_ssid.set(wssid.group(1))
            wpass = re.search(r'^\s*WIFI_PASSWORD\s*=\s*"(.*?)"', content, re.MULTILINE)
            if wpass: self.wifi_password.set(wpass.group(1))
        else:
            self.rpi_enable_wifi.set(False)
        self.toggle_wifi_fields()

    def get_config_lines(self):
        lines = []
        val = "1" if self.rpi_enable_uart.get() else "0"
        lines.append(f'ENABLE_UART = "{val}"\n')

        if self.license_commercial.get():
            lines.append('LICENSE_FLAGS_ACCEPTED:append = " commercial synaptics-killswitch"\n')

        if self.rpi_usb_gadget.get():
            lines.append('# Enable USB OTG/Gadget Mode\n')
            lines.append('RPI_EXTRA_CONFIG:append = "dtoverlay=dwc2"\n')
            lines.append('KERNEL_MODULE_AUTOLOAD += "dwc2 g_ether"\n')
            lines.append('IMAGE_INSTALL:append = " kernel-module-dwc2 kernel-module-g-ether"\n')

        if self.rpi_enable_wifi.get():
            lines.append('# Wi-Fi Config\n')
            lines.append('IMAGE_INSTALL:append = " wpa-supplicant linux-firmware-rpidistro-bcm43430"\n')
            lines.append(f'WIFI_SSID = "{self.wifi_ssid.get()}"\n')
            lines.append(f'WIFI_PASSWORD = "{self.wifi_password.get()}"\n')
        return lines