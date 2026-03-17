import tkinter as tk
from tkinter import ttk
import os
import shutil

class RpiTab:
    def __init__(self, root_app):
        self.root_app = root_app
        self.poky_path_var = root_app.poky_path
        self.machines = ["raspberrypi0-wifi", "raspberrypi3", "raspberrypi4", "raspberrypi5"]

        self.rpi_hostname = tk.StringVar(value="raspberrypi-yocto")
        self.rpi_username = tk.StringVar(value="root")
        self.rpi_password = tk.StringVar(value="root")

        self.rpi_usb_gadget = tk.BooleanVar(value=False)
        self.rpi_enable_uart = tk.BooleanVar(value=True)
        self.license_commercial = tk.BooleanVar(value=True)
        self.rpi_enable_wifi = tk.BooleanVar(value=False)
        self.persistent_logs = tk.BooleanVar(value=True)
        self.wifi_ssid = tk.StringVar()
        self.wifi_password = tk.StringVar()

        self.frame_wifi_auth = None
        self.tab = None
        self.notebook = None

    def is_current_machine_supported(self):
        return self.root_app.tab_general.machine_var.get() in self.machines

    def get_required_layers(self):
        return [
            ("meta-openembedded", "https://git.openembedded.org/meta-openembedded"),
            ("meta-raspberrypi", "https://git.yoctoproject.org/meta-raspberrypi")
        ]

    def get_bblayers_lines(self):
        layers = [
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-oe"\n',
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-python"\n',
            'BBLAYERS += "${TOPDIR}/../meta-openembedded/meta-networking"\n',
            'BBLAYERS += "${TOPDIR}/../meta-raspberrypi"\n'
        ]
        
        if self.rpi_enable_wifi.get():
            layers.append('BBLAYERS += "${TOPDIR}/../meta-yoctool"\n')
            
        return layers

    def create_tab(self, notebook):
        self.notebook = notebook
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Raspberry Pi Options")

        tab_rpi = self.tab
        
        tab_rpi.columnconfigure(0, weight=1)
        tab_rpi.columnconfigure(1, weight=1)

        frame_sys = ttk.LabelFrame(tab_rpi, text=" 1. System Identity & User ")
        frame_sys.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        ttk.Label(frame_sys, text="Hostname:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame_sys, textvariable=self.rpi_hostname, width=25).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_sys, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame_sys, textvariable=self.rpi_username, width=25).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_sys, text="Password:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame_sys, textvariable=self.rpi_password, width=25).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        lbl_note = ttk.Label(frame_sys, text="(User 'root' skips creation)", font=("Arial", 8, "italic"), foreground="gray")
        lbl_note.grid(row=3, column=1, sticky="w", padx=5, pady=(0, 5))

        frame_hw = ttk.LabelFrame(tab_rpi, text=" 2. Hardware & Drivers ")
        frame_hw.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        ttk.Checkbutton(frame_hw, text="Enable UART Console (Serial)", variable=self.rpi_enable_uart).grid(row=0, column=0, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(frame_hw, text="Enable USB Gadget Mode (SSH via USB)", variable=self.rpi_usb_gadget).grid(row=1, column=0, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(frame_hw, text="Enable Persistent Logs (Save to SD)", variable=self.persistent_logs).grid(row=2, column=0, sticky="w", padx=10, pady=2)
        ttk.Separator(frame_hw, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=5)
        ttk.Checkbutton(frame_hw, text="Accept Commercial Licenses (Codecs/Firmware)", variable=self.license_commercial).grid(row=4, column=0, sticky="w", padx=10, pady=2)

        frame_net = ttk.LabelFrame(tab_rpi, text=" 3. Wireless Connectivity ")
        frame_net.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        chk_wifi = ttk.Checkbutton(frame_net, text="Enable Wi-Fi Configuration", variable=self.rpi_enable_wifi, command=self.toggle_wifi_fields)
        chk_wifi.pack(anchor="w", padx=10, pady=5)

        self.frame_wifi_auth = ttk.Frame(frame_net)
        self.frame_wifi_auth.pack(fill="x", padx=20, pady=(0, 10))

        ttk.Label(self.frame_wifi_auth, text="SSID (Network Name):").pack(side="left")
        ttk.Entry(self.frame_wifi_auth, textvariable=self.wifi_ssid, width=25).pack(side="left", padx=5)
        
        ttk.Label(self.frame_wifi_auth, text="Password:").pack(side="left", padx=(15, 0))
        ttk.Entry(self.frame_wifi_auth, textvariable=self.wifi_password, width=25, show="*").pack(side="left", padx=5)

        self.toggle_wifi_fields()

    def toggle_wifi_fields(self):
        if self.frame_wifi_auth:
            if self.rpi_enable_wifi.get():
                self.frame_wifi_auth.pack(fill="x", padx=20, pady=(0, 10))
            else:
                self.frame_wifi_auth.pack_forget()

    def set_visible(self, visible):
        if not self.tab or not self.notebook:
            return
        try:
            state = self.notebook.tab(self.tab, "state")
            hidden = (state == "hidden")
            if visible and hidden:
                self.notebook.tab(self.tab, state="normal")
            elif not visible and not hidden:
                self.notebook.hide(self.tab)
        except:
            pass

    def get_state(self):
        return {
            "rpi_hostname": self.rpi_hostname.get(),
            "rpi_username": self.rpi_username.get(),
            "rpi_password": self.rpi_password.get(),
            "rpi_usb_gadget": self.rpi_usb_gadget.get(),
            "rpi_enable_uart": self.rpi_enable_uart.get(),
            "license_commercial": self.license_commercial.get(),
            "persistent_logs": self.persistent_logs.get(),
            "rpi_enable_wifi": self.rpi_enable_wifi.get(),
            "wifi_ssid": self.wifi_ssid.get(),
            "wifi_password": self.wifi_password.get()
        }

    def set_state(self, state):
        if not state:
            return
        self.rpi_hostname.set(state.get("rpi_hostname", "raspberrypi-yocto"))
        self.rpi_username.set(state.get("rpi_username", "root"))
        self.rpi_password.set(state.get("rpi_password", "root"))
        self.rpi_usb_gadget.set(state.get("rpi_usb_gadget", False))
        self.rpi_enable_uart.set(state.get("rpi_enable_uart", True))
        self.license_commercial.set(state.get("license_commercial", True))
        self.persistent_logs.set(state.get("persistent_logs", True))
        self.rpi_enable_wifi.set(state.get("rpi_enable_wifi", False))
        self.wifi_ssid.set(state.get("wifi_ssid", ""))
        self.wifi_password.set(state.get("wifi_password", ""))
        self.toggle_wifi_fields()

    def generate_wpa_config(self):
        poky_dir = self.poky_path_var.get()
        if not poky_dir or not os.path.exists(poky_dir):
            return

        layer_path = os.path.join(poky_dir, "meta-yoctool")
        recipe_dir = os.path.join(layer_path, "recipes-connectivity", "wpa-config")
        files_dir = os.path.join(recipe_dir, "files")

        os.makedirs(files_dir, exist_ok=True)
        os.makedirs(os.path.join(layer_path, "conf"), exist_ok=True)

        with open(os.path.join(layer_path, "conf", "layer.conf"), "w") as f:
            f.write('BBPATH .= ":${LAYERDIR}"\n')
            f.write('BBFILES += "${LAYERDIR}/recipes-*/*/*.bb"\n')
            f.write('BBFILES += "${LAYERDIR}/recipes-*/*/*.bbappend"\n')
            f.write('BBFILE_COLLECTIONS += "wifisetup"\n')
            f.write('BBFILE_PATTERN_wifisetup = "^${LAYERDIR}/"\n')
            f.write('BBFILE_PRIORITY_wifisetup = "10"\n')
            f.write('LAYERSERIES_COMPAT_wifisetup = "scarthgap"\n')

        wpa_conf = f"""ctrl_interface=/run/wpa_supplicant
update_config=1
country=VN

network={{
    ssid="{self.wifi_ssid.get()}"
    psk="{self.wifi_password.get()}"
}}
"""
        with open(os.path.join(files_dir, "wpa_supplicant.conf"), "w") as f:
            f.write(wpa_conf.strip() + "\n")

        network_conf = """[Match]
Name=wlan0

[Network]
DHCP=yes

[DHCPv4]
SendHostname=yes
"""
        with open(os.path.join(files_dir, "80-wifi.network"), "w") as f:
            f.write(network_conf.strip() + "\n")

        wpa_service = """[Unit]
Description=WPA Supplicant for wlan0
Before=network.target
After=dbus.service
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/wpa_supplicant -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        with open(os.path.join(files_dir, "wpa-wlan0.service"), "w") as f:
            f.write(wpa_service.strip() + "\n")

        with open(os.path.join(recipe_dir, "wpa-config_1.0.bb"), "w") as f:
            f.write("""SUMMARY = "WPA Supplicant and Networkd configuration"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://wpa_supplicant.conf \\
           file://80-wifi.network \\
           file://wpa-wlan0.service"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "wpa-wlan0.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install() {
    install -d ${D}${sysconfdir}/wpa_supplicant
    install -m 600 ${WORKDIR}/wpa_supplicant.conf ${D}${sysconfdir}/wpa_supplicant/wpa_supplicant.conf

    install -d ${D}${sysconfdir}/systemd/network
    install -m 644 ${WORKDIR}/80-wifi.network ${D}${sysconfdir}/systemd/network/80-wifi.network

    install -d ${D}${systemd_system_unitdir}
    install -m 644 ${WORKDIR}/wpa-wlan0.service ${D}${systemd_system_unitdir}/wpa-wlan0.service
}

FILES:${PN} += "${sysconfdir}/wpa_supplicant/wpa_supplicant.conf \\
                ${sysconfdir}/systemd/network/80-wifi.network \\
                ${systemd_system_unitdir}/wpa-wlan0.service"
""")

    def create_base_files_bbappend(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        recipe_dir = os.path.join(layer_path, "recipes-core", "base-files")
        os.makedirs(recipe_dir, exist_ok=True)
        
        hostname = self.rpi_hostname.get().strip()
        content = ""
        
        if hostname:
            content += f'hostname = "{hostname}"\n\n'
            
        if hasattr(self.root_app, 'tab_ota') and self.root_app.tab_ota.enable_rauc.get():
            content += """do_install:append() {
    if ! grep -q "/boot" ${D}${sysconfdir}/fstab; then
        echo "/dev/mmcblk0p1 /boot vfat defaults,rw,sync 0 0" >> ${D}${sysconfdir}/fstab
    fi
}
"""
        bbappend_file = os.path.join(recipe_dir, "base-files_%.bbappend")
        if content:
            with open(bbappend_file, "w") as f:
                f.write(content)
        else:
            if os.path.exists(bbappend_file):
                os.remove(bbappend_file)

    def create_rauc_wks_file(self, size):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir or not os.path.exists(poky_dir): return None
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        wic_dir = os.path.join(layer_path, "wic")
        os.makedirs(wic_dir, exist_ok=True)
        
        wks_filename = "sdimage-dual-raspberrypi.wks"
        wks_path = os.path.join(wic_dir, wks_filename)
        
        content = f"""part /boot --source bootimg-partition --ondisk mmcblk0 --fstype=vfat --label boot --active --align 4096 --size 100
part / --source rootfs --ondisk mmcblk0 --fstype=ext4 --label rootfs_A --align 4096 --size {size}
part / --source rootfs --ondisk mmcblk0 --fstype=ext4 --label rootfs_B --align 4096 --size {size}
part /data --ondisk mmcblk0 --fstype=ext4 --label data --align 4096 --size 128
"""
        with open(wks_path, "w") as f: f.write(content)

    def create_rauc_config(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        rauc_recipe_dir = os.path.join(layer_path, "recipes-core", "rauc")
        rauc_files_dir = os.path.join(rauc_recipe_dir, "files")
        os.makedirs(rauc_files_dir, exist_ok=True)

        project_root = os.getcwd()
        cert_src = os.path.join(project_root, "rauc-keys", "development-1.cert.pem")
        cert_dest = os.path.join(rauc_files_dir, "development-1.cert.pem")
        if os.path.exists(cert_src):
            shutil.copy(cert_src, cert_dest)

        machine = self.root_app.tab_general.machine_var.get()
        sys_conf_content = f"""[system]
compatible={machine}
bootloader=uboot
data-directory=/var/lib/rauc

[keyring]
path=development-1.cert.pem

[slot.rootfs.0]
device=/dev/mmcblk0p2
type=ext4
bootname=A

[slot.rootfs.1]
device=/dev/mmcblk0p3
type=ext4
bootname=B
"""
        with open(os.path.join(rauc_files_dir, "system.conf"), "w") as f: f.write(sys_conf_content.strip())
        
        fw_env_content = "/boot/uboot.env 0x0000 0x4000\n"
        with open(os.path.join(rauc_files_dir, "fw_env.config"), "w") as f: f.write(fw_env_content)

        for old_file in ["rauc-conf_1.0.bb", "rauc-conf_%.bbappend", "rauc-conf.bbappend"]:
            old_path = os.path.join(rauc_recipe_dir, old_file)
            if os.path.exists(old_path):
                try: os.remove(old_path)
                except: pass

        recipe_content = """SUMMARY = "RPI Specific RAUC configuration"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://system.conf file://fw_env.config file://development-1.cert.pem"

PROVIDES += "rauc-conf virtual/rauc-conf"
RPROVIDES:${PN} += "rauc-conf virtual-rauc-conf"

RCONFLICTS:${PN} += "rauc-conf"
RREPLACES:${PN} += "rauc-conf"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${sysconfdir}/rauc
    install -m 644 ${WORKDIR}/system.conf ${D}${sysconfdir}/rauc/system.conf
    
    if [ -f ${WORKDIR}/development-1.cert.pem ]; then
        install -m 644 ${WORKDIR}/development-1.cert.pem ${D}${sysconfdir}/rauc/development-1.cert.pem
    fi
    
    install -d ${D}${sysconfdir}
    install -m 644 ${WORKDIR}/fw_env.config ${D}${sysconfdir}/fw_env.config
}

FILES:${PN} += "${sysconfdir}/rauc/system.conf ${sysconfdir}/fw_env.config ${sysconfdir}/rauc/development-1.cert.pem"
"""
        with open(os.path.join(rauc_recipe_dir, "rpi-rauc-conf_1.0.bb"), "w") as f: f.write(recipe_content.strip())

    def create_uboot_bbappend(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        uboot_dir = os.path.join(layer_path, "recipes-bsp", "u-boot")
        os.makedirs(uboot_dir, exist_ok=True)
        
        old_boot_cmd = os.path.join(uboot_dir, "files", "boot.cmd")
        if os.path.exists(old_boot_cmd):
            try: os.remove(old_boot_cmd)
            except: pass

        content = """DEPENDS += "u-boot-tools-native"

do_compile:append() {
    echo "bootlimit=3" >> ${B}/u-boot-initial-env
    echo "bootcount=0" >> ${B}/u-boot-initial-env
    echo "upgrade_available=0" >> ${B}/u-boot-initial-env
    echo "BOOT_ORDER=A B" >> ${B}/u-boot-initial-env
    echo "BOOT_A_LEFT=3" >> ${B}/u-boot-initial-env
    echo "BOOT_B_LEFT=0" >> ${B}/u-boot-initial-env
    
    mkenvimage -s 16384 -o ${WORKDIR}/uboot.env ${B}/u-boot-initial-env
}

do_deploy:append() {
    install -d ${DEPLOYDIR}
    install -m 644 ${WORKDIR}/uboot.env ${DEPLOYDIR}/uboot.env
}
"""
        with open(os.path.join(uboot_dir, "u-boot_%.bbappend"), "w") as f: 
            f.write(content.strip())

    def create_rpi_uboot_scr_bbappend(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        scr_dir = os.path.join(layer_path, "recipes-bsp", "rpi-u-boot-scr")
        files_dir = os.path.join(scr_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        bad_bbappend = os.path.join(scr_dir, "rpi-u-boot-scr_%.bbappend")
        if os.path.exists(bad_bbappend):
            try: os.remove(bad_bbappend)
            except: pass
            
        boot_cmd_content = """test -n "${BOOT_ORDER}" || setenv BOOT_ORDER "A B"
test -n "${BOOT_A_LEFT}" || setenv BOOT_A_LEFT 3
test -n "${BOOT_B_LEFT}" || setenv BOOT_B_LEFT 3

setenv boot_part ""
for target in ${BOOT_ORDER}; do
    if test "${boot_part}" = ""; then
        if test "${target}" = "A"; then
            if test ${BOOT_A_LEFT} -gt 0; then
                setenv boot_part "2"
                setenv rauc_slot "A"
                setexpr BOOT_A_LEFT ${BOOT_A_LEFT} - 1
            fi
        elif test "${target}" = "B"; then
            if test ${BOOT_B_LEFT} -gt 0; then
                setenv boot_part "3"
                setenv rauc_slot "B"
                setexpr BOOT_B_LEFT ${BOOT_B_LEFT} - 1
            fi
        fi
    fi
done

saveenv

if test "${boot_part}" = ""; then
    setenv BOOT_ORDER "A B"
    setenv BOOT_A_LEFT 3
    setenv BOOT_B_LEFT 3
    saveenv
    reset
fi

setenv bootargs "console=ttyS0,115200 root=/dev/mmcblk0p${boot_part} rootfstype=ext4 rootwait rauc.slot=${rauc_slot}"
fatload mmc 0:1 ${kernel_addr_r} @@KERNEL_IMAGETYPE@@
@@KERNEL_BOOTCMD@@ ${kernel_addr_r} - ${fdt_addr}
"""
        with open(os.path.join(files_dir, "boot.cmd.in"), "w") as f: 
            f.write(boot_cmd_content.strip())

        content = """FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
"""
        with open(os.path.join(scr_dir, "rpi-u-boot-scr.bbappend"), "w") as f: 
            f.write(content.strip())

    def create_kernel_rauc_bbappend(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        kernel_dir = os.path.join(layer_path, "recipes-kernel", "linux")
        files_dir = os.path.join(kernel_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        cfg_content = """CONFIG_BLK_DEV_LOOP=y
CONFIG_SQUASHFS=y
CONFIG_SQUASHFS_FILE_CACHE=y
CONFIG_SQUASHFS_FILE_DIRECT=y
CONFIG_SQUASHFS_DECOMP_SINGLE=y
CONFIG_SQUASHFS_XATTR=y
CONFIG_SQUASHFS_ZLIB=y
CONFIG_SQUASHFS_XZ=y
"""
        with open(os.path.join(files_dir, "rauc.cfg"), "w") as f:
            f.write(cfg_content.strip())
            
        bbappend_content = """FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://rauc.cfg"
"""
        with open(os.path.join(kernel_dir, "linux-raspberrypi_%.bbappend"), "w") as f:
            f.write(bbappend_content.strip())

    def setup_rauc_recipes(self):
        if hasattr(self.root_app, 'tab_ota'):
            size = self.root_app.tab_ota.rauc_slot_size.get()
            self.create_rauc_wks_file(size)
        self.create_rauc_config()
        self.create_uboot_bbappend()
        self.create_rpi_uboot_scr_bbappend()
        self.create_kernel_rauc_bbappend()

    def get_config_lines(self):
        lines = []
        
        user = self.rpi_username.get().strip()
        pwd = self.rpi_password.get().strip()
        
        if user and user != "root":
            lines.append('INHERIT += "extrausers"\n')
            pass_flag = f"-P '{pwd}'" if pwd else "-P 'root'" 
            lines.append(f'EXTRA_USERS_PARAMS += "useradd {pass_flag} -G sudo,video,render,input,shutdown,disk {user};"\n')

        lines.append(f'ENABLE_UART = "{"1" if self.rpi_enable_uart.get() else "0"}"\n')

        if self.license_commercial.get():
            lines.append('LICENSE_FLAGS_ACCEPTED:append = " commercial synaptics-killswitch"\n')

        if self.rpi_usb_gadget.get():
            lines.append('RPI_EXTRA_CONFIG:append = "dtoverlay=dwc2"\n')
            lines.append('KERNEL_MODULE_AUTOLOAD += "dwc2 g_ether"\n')
            lines.append('IMAGE_INSTALL:append = " kernel-module-dwc2 kernel-module-g-ether"\n')

        if self.persistent_logs.get():
            lines.append('VOLATILE_LOG_DIR = "no"\n')

        if self.rpi_enable_wifi.get():
            self.generate_wpa_config()
            lines.append('DISTRO_FEATURES:append = " systemd wifi usrmerge"\n')
            lines.append('VIRTUAL-RUNTIME_init_manager = "systemd"\n')
            lines.append('DISTRO_FEATURES_BACKFILL_CONSIDERED = "sysvinit"\n')
            lines.append('VIRTUAL-RUNTIME_initscripts = "systemd-compat-units"\n')
            
            lines.append('IMAGE_INSTALL:append = " wpa-supplicant iw linux-firmware-rpidistro-bcm43430 kernel-module-brcmfmac kernel-module-brcmfmac-wcc wpa-config wireless-regdb-static avahi-daemon libnss-mdns"\n')
            
            lines.append('KERNEL_MODULE_AUTOLOAD:append = " brcmfmac-wcc"\n')
            lines.append('CMDLINE:append = " brcmfmac.feature_disable=0x200000"\n')
            
        self.create_base_files_bbappend()

        if hasattr(self.root_app, 'tab_ota') and self.root_app.tab_ota.enable_rauc.get():
            self.setup_rauc_recipes()
            
            lines.append('\n')
            lines.append('RPI_USE_U_BOOT = "1"\n')
            lines.append('PREFERRED_PROVIDER_virtual/bootloader = "u-boot"\n')
            lines.append('DEPENDS:append:pn-rauc = " libubootenv"\n')
            lines.append('PREFERRED_PROVIDER_rauc-conf = "rpi-rauc-conf"\n')
            lines.append('PREFERRED_PROVIDER_virtual/rauc-conf = "rpi-rauc-conf"\n')
            lines.append('BBMASK += "meta-rauc/recipes-core/rauc/rauc-conf.bb"\n')
            lines.append('IMAGE_INSTALL:append = " rpi-rauc-conf libubootenv-bin e2fsprogs-mke2fs dosfstools"\n')
            lines.append('WKS_FILE = "sdimage-dual-raspberrypi.wks"\n')
            lines.append('EXTRA_IMAGEDEPENDS:remove = "rpi-u-boot-scr"\n')
            lines.append('IMAGE_BOOT_FILES:append = " uboot.env"\n')

        return lines