import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import glob
import threading
import shutil

class OTATab:
    def __init__(self, root_app):
        self.root_app = root_app
        
        self.enable_rauc = tk.BooleanVar(value=False)
        self.rauc_slot_size = tk.StringVar(value="1024")
        
        self.target_ip = tk.StringVar(value="192.168.1.x")
        self.target_user = tk.StringVar(value="root")
        self.target_pass = tk.StringVar(value="root")

    def create_tab(self, notebook):
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="OTA Update (RAUC)")
        
        frame_cfg = ttk.LabelFrame(tab, text=" 1. RAUC Configuration ")
        frame_cfg.pack(fill="x", padx=10, pady=5)
        
        ttk.Checkbutton(frame_cfg, text="Enable RAUC (A/B Partitioning)", variable=self.enable_rauc).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        ttk.Label(frame_cfg, text="Rootfs Slot Size (MB):").grid(row=1, column=0, sticky="w", padx=10)
        ttk.Entry(frame_cfg, textvariable=self.rauc_slot_size, width=10).grid(row=1, column=1, sticky="w")
        ttk.Label(frame_cfg, text="(Must be > Image Size)").grid(row=1, column=2, sticky="w", padx=5)

        frame_act = ttk.LabelFrame(tab, text=" 2. Build Actions ")
        frame_act.pack(fill="x", padx=10, pady=5)
        
        btn_keys = ttk.Button(frame_act, text="1. Generate Keys", command=self.generate_keys)
        btn_keys.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        btn_bundle = ttk.Button(frame_act, text="2. BUILD UPDATE BUNDLE (.raucb)", command=self.build_bundle)
        btn_bundle.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(frame_act, text="(Note: Build standard Image first, then Build Bundle)").grid(row=0, column=2, padx=10)

        frame_dep = ttk.LabelFrame(tab, text=" 3. Deployment (SCP Transfer) ")
        frame_dep.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_dep, text="Target IP:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame_dep, textvariable=self.target_ip, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(frame_dep, text="User:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        ttk.Entry(frame_dep, textvariable=self.target_user, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(frame_dep, text="Pass:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        ttk.Entry(frame_dep, textvariable=self.target_pass, width=10, show="*").grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        btn_send = ttk.Button(frame_dep, text="SEND BUNDLE & INSTALL", command=self.send_bundle_to_device)
        btn_send.grid(row=1, column=0, columnspan=6, pady=10, sticky="ew", padx=20)

    def build_bundle(self):
        if not self.enable_rauc.get():
            messagebox.showwarning("Warning", "Please enable RAUC first.")
            return
        if self.root_app.poky_path.get():
            self.root_app.start_specific_build("update-bundle")
        else:
            messagebox.showerror("Error", "Poky path not set")

    def send_bundle_to_device(self):
        if not self.check_sshpass(): return
        
        poky_dir = self.root_app.poky_path.get()
        build_dir = self.root_app.build_dir_name.get()
        machine = self.root_app.tab_general.machine_var.get()
        deploy_dir = os.path.join(poky_dir, build_dir, "tmp/deploy/images", machine)
        
        if not os.path.exists(deploy_dir):
            messagebox.showerror("Error", "Deploy directory not found. Build first.")
            return
            
        files = glob.glob(os.path.join(deploy_dir, "*.raucb"))
        if not files:
            messagebox.showerror("Error", "No .raucb file found. Please click 'BUILD UPDATE BUNDLE' first.")
            return
            
        bundle_file = max(files, key=os.path.getctime)
        file_name = os.path.basename(bundle_file)
        
        ip = self.target_ip.get()
        user = self.target_user.get()
        pwd = self.target_pass.get()
        target_path = f"/tmp/{file_name}"
        
        self.root_app.log(f"Starting SCP transfer: {file_name} -> {ip}...")
        
        cmd_scp = ["sshpass", "-p", pwd, "scp", "-v", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", bundle_file, f"{user}@{ip}:{target_path}"]
        cmd_install = ["sshpass", "-p", pwd, "ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", f"{user}@{ip}", f"rauc install {target_path} && reboot"]
        
        threading.Thread(target=self.run_scp_thread, args=(cmd_scp, cmd_install, file_name)).start()

    def run_scp_thread(self, cmd_scp, cmd_install, filename):
        try:
            self.root_app.set_busy_state(True)
            
            process = subprocess.Popen(
                cmd_scp, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, 
                bufsize=1, 
                universal_newlines=True
            )
            
            for line in process.stdout:
                line_str = line.strip()
                if line_str:
                    if "Sending file modes" in line_str or "Transferred" in line_str or "Bytes per second" in line_str or "Sink" in line_str:
                         self.root_app.log(f"[SCP] {line_str}")
            
            process.wait()
            
            if process.returncode == 0:
                self.root_app.log(f"SUCCESS: {filename} uploaded.")
                
                self.root_app.log("Installing update & Rebooting. Please wait...")
                install_process = subprocess.run(cmd_install, capture_output=True, text=True)
                
                if install_process.returncode == 0 or install_process.returncode == 255:
                    self.root_app.log(f"[INSTALL] {install_process.stdout.strip()}")
                    self.root_app.root.after(0, messagebox.showinfo, "Success", f"Update installed successfully!\nDevice is rebooting into the new partition.")
                else:
                    self.root_app.log(f"INSTALL ERROR: {install_process.stderr}")
                    self.root_app.root.after(0, messagebox.showerror, "Install Failed", f"Update failed during rauc install.\nError: {install_process.stderr}")
            else:
                 self.root_app.log(f"SCP ERROR: Transfer failed with code {process.returncode}")
                 self.root_app.root.after(0, messagebox.showerror, "Transfer Failed", "Failed to upload the update bundle.")

        except Exception as e:
            self.root_app.log(f"DEPLOY ERROR: {str(e)}")
            self.root_app.root.after(0, messagebox.showerror, "Deploy Failed", f"Check IP/User/Pass.\nError: {str(e)}")
        finally:
            self.root_app.set_busy_state(False)

    def check_sshpass(self):
        from shutil import which
        if which("sshpass") is None:
            if messagebox.askyesno("Missing Component", "Install 'sshpass' to deploy?"):
                subprocess.run("sudo apt-get install -y sshpass", shell=True)
                return True
            return False
        return True

    def generate_keys(self):
        project_root = os.getcwd()
        key_dir = os.path.join(project_root, "rauc-keys")
        if not os.path.exists(key_dir): os.makedirs(key_dir)
        
        cert_path = os.path.join(key_dir, "development-1.cert.pem")
        key_path = os.path.join(key_dir, "development-1.key.pem")
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            messagebox.showinfo("Info", f"Keys already exist in {key_dir}")
            return
            
        cmd = f"""openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 -keyout {key_path} -out {cert_path} -subj "/C=VN/ST=HCM/L=Saigon/O=Yoctool/CN=rpi-update" """
        try:
            subprocess.run(cmd, shell=True, check=True)
            real_user = self.root_app.sudo_user
            if real_user and real_user != "root":
                subprocess.run(f"chown -R {real_user}:{real_user} {key_dir}", shell=True)
            messagebox.showinfo("Success", f"Keys generated at:\n{key_dir}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_wks_file(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir or not os.path.exists(poky_dir): return None
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        wic_dir = os.path.join(layer_path, "wic")
        os.makedirs(wic_dir, exist_ok=True)
        
        wks_filename = "sdimage-dual-raspberrypi.wks"
        wks_path = os.path.join(wic_dir, wks_filename)
        size = self.rauc_slot_size.get()
        
        content = f"""part /boot --source bootimg-partition --ondisk mmcblk0 --fstype=vfat --label boot --active --align 4096 --size 100
part / --source rootfs --ondisk mmcblk0 --fstype=ext4 --label rootfs_A --align 4096 --size {size}
part / --source rootfs --ondisk mmcblk0 --fstype=ext4 --label rootfs_B --align 4096 --size {size}
part /data --ondisk mmcblk0 --fstype=ext4 --label data --align 4096 --size 128
"""
        with open(wks_path, "w") as f: f.write(content)
        return wks_filename

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

    def create_kernel_bbappend(self):
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

    def create_bundle_recipe(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        recipes_dir = os.path.join(layer_path, "recipes-core", "bundles")
        os.makedirs(recipes_dir, exist_ok=True)
        
        bundle_bb = os.path.join(recipes_dir, "update-bundle.bb")
        content = """DESCRIPTION = "RAUC Update Bundle"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit bundle

RAUC_BUNDLE_COMPATIBLE = "${MACHINE}"
RAUC_BUNDLE_VERSION = "v1"
RAUC_BUNDLE_DESCRIPTION = "RAUC Bundle generated by Yoctool"
RAUC_BUNDLE_FORMAT = "plain"

RAUC_BUNDLE_SLOTS = "rootfs" 
RAUC_SLOT_rootfs = "${RAUC_TARGET_IMAGE}"
RAUC_SLOT_rootfs[fstype] = "ext4"

RAUC_KEY_FILE = "${RAUC_KEY_FILE_REAL}"
RAUC_CERT_FILE = "${RAUC_CERT_FILE_REAL}"
"""
        with open(bundle_bb, "w") as f: f.write(content.strip() + "\n")

    def create_base_files_bbappend(self):
        poky_dir = self.root_app.poky_path.get()
        if not poky_dir: return
        
        layer_path = os.path.join(poky_dir, "meta-yoctool")
        recipe_dir = os.path.join(layer_path, "recipes-core", "base-files")
        os.makedirs(recipe_dir, exist_ok=True)
        
        content = """do_install:append() {
    if ! grep -q "/boot" ${D}${sysconfdir}/fstab; then
        echo "/dev/mmcblk0p1 /boot vfat defaults,rw,sync 0 0" >> ${D}${sysconfdir}/fstab
    fi
}
"""
        with open(os.path.join(recipe_dir, "base-files_%.bbappend"), "w") as f:
            f.write(content)

    def get_config_lines(self):
        if not self.enable_rauc.get(): return []
        
        wks_file = self.create_wks_file()
        self.create_rauc_config()
        self.create_bundle_recipe()
        self.create_uboot_bbappend()
        self.create_rpi_uboot_scr_bbappend()
        self.create_kernel_bbappend()
        self.create_base_files_bbappend()
        
        project_root = os.getcwd()
        key_dir = os.path.join(project_root, "rauc-keys")
        cert_path = os.path.join(key_dir, "development-1.cert.pem")
        key_path = os.path.join(key_dir, "development-1.key.pem")

        if not os.path.exists(key_path):
             self.root_app.log("Warning: RAUC Keys not found. Please click 'Generate Keys'.")

        lines = []
        lines.append('\n')
        
        lines.append('RPI_USE_U_BOOT = "1"\n')
        lines.append('PREFERRED_PROVIDER_virtual/bootloader = "u-boot"\n')
        lines.append('DEPENDS:append:pn-rauc = " libubootenv"\n')
        
        lines.append('PREFERRED_PROVIDER_rauc-conf = "rpi-rauc-conf"\n')
        lines.append('PREFERRED_PROVIDER_virtual/rauc-conf = "rpi-rauc-conf"\n')
        lines.append('BBMASK += "meta-rauc/recipes-core/rauc/rauc-conf.bb"\n')
        
        lines.append('PACKAGECONFIG:append:pn-rauc = " uboot"\n')
        
        lines.append('DISTRO_FEATURES:append = " rauc"\n')
        lines.append('IMAGE_INSTALL:append = " rauc rpi-rauc-conf libubootenv-bin e2fsprogs-mke2fs dosfstools"\n')
        
        if wks_file: lines.append(f'WKS_FILE = "{wks_file}"\n')
        
        lines.append(f'RAUC_KEY_FILE_REAL = "{key_path}"\n')
        lines.append(f'RAUC_CERT_FILE_REAL = "{cert_path}"\n')
        lines.append(f'RAUC_KEYRING_FILE = "{cert_path}"\n')
        
        current_image = self.root_app.tab_general.image_var.get()
        lines.append(f'RAUC_TARGET_IMAGE = "{current_image}"\n')
        
        lines.append('IMAGE_BOOT_FILES:append = " uboot.env"\n')
        
        lines.append('IMAGE_FSTYPES:append = " wic.bz2 ext4"\n')
        
        lines.append('SYSTEMD_AUTO_ENABLE:pn-systemd-growfs = "disable"\n')
        lines.append('IMAGE_FEATURES:remove = "read-only-rootfs"\n')
        
        return lines

    def get_bblayers_lines(self):
        return ['BBLAYERS += "${TOPDIR}/../meta-rauc"\n']
    
    def get_required_layers(self):
        return [("meta-rauc", "https://github.com/rauc/meta-rauc -b scarthgap")]
    
    def get_state(self):
         return {
             "enable_rauc": self.enable_rauc.get(),
             "rauc_slot_size": self.rauc_slot_size.get(),
             "target_ip": self.target_ip.get(),
             "target_user": self.target_user.get()
         }
    
    def set_state(self, state):
        if not state: return
        self.enable_rauc.set(state.get("enable_rauc", False))
        self.rauc_slot_size.set(state.get("rauc_slot_size", "1024"))
        self.target_ip.set(state.get("target_ip", "192.168.1.x"))
        self.target_user.set(state.get("target_user", "root"))