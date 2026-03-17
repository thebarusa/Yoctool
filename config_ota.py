import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import glob
import threading

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

    def get_config_lines(self):
        if not self.enable_rauc.get(): return []
        
        self.create_bundle_recipe()
        
        project_root = os.getcwd()
        key_dir = os.path.join(project_root, "rauc-keys")
        cert_path = os.path.join(key_dir, "development-1.cert.pem")
        key_path = os.path.join(key_dir, "development-1.key.pem")

        if not os.path.exists(key_path):
             self.root_app.log("Warning: RAUC Keys not found. Please click 'Generate Keys'.")

        lines = []
        lines.append('\n')
        lines.append('PACKAGECONFIG:append:pn-rauc = " uboot"\n')
        lines.append('DISTRO_FEATURES:append = " rauc"\n')
        lines.append('IMAGE_INSTALL:append = " rauc"\n')
        lines.append(f'RAUC_KEY_FILE_REAL = "{key_path}"\n')
        lines.append(f'RAUC_CERT_FILE_REAL = "{cert_path}"\n')
        lines.append(f'RAUC_KEYRING_FILE = "{cert_path}"\n')
        
        current_image = self.root_app.tab_general.image_var.get()
        lines.append(f'RAUC_TARGET_IMAGE = "{current_image}"\n')
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