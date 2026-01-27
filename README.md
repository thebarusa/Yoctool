# Yoctool

A comprehensive GUI tool for managing Yocto Project builds, specifically designed for Raspberry Pi targets and other embedded systems.

## Overview

Yocto Tool is a Python-based graphical application that simplifies the process of building custom Linux images using the Yocto Project. It provides an intuitive interface for configuring builds, managing settings, and flashing images to SD cards.

## Features

### 🚀 Core Functionality
- **Visual Build Management**: Start, monitor, and clean Yocto builds through an easy-to-use GUI
- **Live Progress Tracking**: Real-time progress bar with percentage display for both builds and flashing operations
- **Configuration Management**: Load and save build configurations with automatic persistence
- **Poky Download**: Built-in downloader for Yocto Poky repository with branch selection
- **SD Card Flashing**: Direct image flashing to SD cards with progress tracking

### 🔧 Configuration Options
- **Machine Selection**: Support for multiple targets (Raspberry Pi 0/3/4, QEMU x86-64)
- **Image Types**: Choose from minimal, base, or full-featured images
- **Package Management**: Select package format (RPM, DEB, IPK)
- **Init System**: Choose between SysVinit and systemd
- **Features**: Toggle debug tweaks, SSH server, and debug tools

### 🍓 Raspberry Pi Specific
- **WiFi Configuration**: Pre-configure WiFi credentials in the image
- **USB Gadget Mode**: Enable USB Ethernet gadget mode
- **UART Console**: Enable/disable UART for debugging
- **Auto-loading**: Device-specific settings appear only for Raspberry Pi targets

### 💾 Smart Path Management
- **Auto-save**: Automatically saves Poky path for next session
- **Auto-load**: Loads configuration automatically when path is selected
- **Persistent Settings**: Remembers your workspace across app restarts

## Requirements

### System Requirements
- **Operating System**: Linux (tested on Ubuntu/Debian)
- **Python**: 3.6 or higher
- **Privileges**: Root access (sudo) required for SD card flashing

### Dependencies
- `tkinter` - GUI framework (usually pre-installed)
- `python3-tk` - Tkinter package for Python 3
- Standard Python libraries: `os`, `re`, `subprocess`, `threading`, `glob`, `sys`, `shlex`

### Yocto Project Requirements
- Git (for cloning Poky)
- Yocto Project build dependencies (see [Yocto Project Quick Build](https://docs.yoctoproject.org/brief-yoctoprojectqs/index.html))

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd YoctoTool
```

### 2. Install Python Dependencies
```bash
# Install tkinter if not present
sudo apt-get install python3-tk

# Verify Python version
python3 --version  # Should be 3.6+
```

### 3. Ensure Required Tools
```bash
# Install git for Poky download
sudo apt-get install git

# Install Yocto build dependencies
sudo apt-get install gawk wget git diffstat unzip texinfo gcc build-essential \
    chrpath socat cpio python3 python3-pip python3-pexpect xz-utils \
    debianutils iputils-ping python3-git python3-jinja2 libegl1-mesa \
    libsdl1.2-dev pylint xterm python3-subunit mesa-common-dev zstd liblz4-tool
```

## Usage

### Starting the Application
```bash
# Run with sudo for full functionality (especially for flashing)
sudo python3 yocto_tool.py
```

### First-Time Setup

1. **Set Poky Path**:
   - Click "Browse" to select existing Poky directory, OR
   - Click "Download Poky" to clone from Yocto Project repository

2. **Configure Build**:
   - Select your target machine (e.g., `raspberrypi0-wifi`)
   - Choose image type (e.g., `core-image-full-cmdline`)
   - Configure distro features and packages
   - For Raspberry Pi: Configure WiFi, USB gadget, etc. in the "Raspberry Pi Options" tab

3. **Save Configuration**:
   - Click "SAVE CONFIG" to write settings to `local.conf`

### Building an Image

1. **Start Build**:
   - Click "START BUILD"
   - Monitor progress in the terminal log
   - Progress bar shows build completion percentage

2. **Monitor Progress**:
   - Real-time output appears in the terminal log area
   - Progress bar updates as tasks complete
   - Green bar with percentage indicates build progress

3. **Wait for Completion**:
   - Build time varies (30 minutes to several hours for first build)
   - Subsequent builds are faster due to caching

### Flashing to SD Card

1. **Insert SD Card**:
   - Insert SD card into your computer
   - Click refresh (↻) button to scan for drives

2. **Select Drive**:
   - Choose your SD card from the dropdown
   - **WARNING**: Double-check the device to avoid data loss!

3. **Flash Image**:
   - Click "FLASH"
   - Confirm the operation
   - Progress bar shows flashing progress
   - Wait for completion

## Project Structure

```
YoctoTool/
├── yocto_tool.py          # Main application
├── manager_rpi.py         # Raspberry Pi configuration manager
├── README.md              # This file
├── .gitignore             # Git ignore rules
└── poky/                  # Yocto Poky repository (downloaded)
    └── build/             # Build directory
        └── conf/          # Configuration files
            └── local.conf # Main configuration
```

## Configuration Files

### User Config File
- **Location**: `~/.yocto_tool_config`
- **Purpose**: Stores last used Poky path
- **Format**: Plain text, single line

### Build Config
- **Location**: `<poky>/build/conf/local.conf`
- **Purpose**: Yocto build configuration
- **Managed by**: Auto-generated from GUI settings

## Troubleshooting

### Permission Errors
- **Issue**: Cannot flash to SD card
- **Solution**: Run with `sudo python3 yocto_tool.py`

### Build Failures
- **Issue**: Build fails with dependency errors
- **Solution**: Ensure all Yocto dependencies are installed
- **Reference**: [Yocto System Requirements](https://docs.yoctoproject.org/ref-manual/system-requirements.html)

### GUI Not Displaying
- **Issue**: Tkinter errors or blank window
- **Solution**: Install `python3-tk`: `sudo apt-get install python3-tk`

### Progress Bar Stuck at 0%
- **Issue**: Progress not updating during build
- **Solution**: This is normal for the first few minutes; Bitbake progress appears after initial parsing

### Config Not Auto-Loading
- **Issue**: Config doesn't load when selecting path
- **Solution**: Ensure `local.conf` exists in `<poky>/build/conf/`

## Advanced Usage

### Custom Build Directory
- Default: `build`
- Modify `self.build_dir_name` in code if needed

### Multiple Machines
- Configure different machines by selecting from dropdown
- Config automatically updates for Raspberry Pi-specific options

### Clean Builds
- Click "CLEAN BUILD" to remove build artifacts
- This forces a complete rebuild (useful for troubleshooting)

## Development

### Adding New Features
1. Edit `yocto_tool.py` for core functionality
2. Edit `manager_rpi.py` for Raspberry Pi-specific features
3. Test with `python3 -m py_compile yocto_tool.py`

### Code Structure
- **YoctoBuilderApp**: Main application class
- **RpiManager**: Raspberry Pi configuration handler (in `manager_rpi.py`)
- **Progress Tracking**: Canvas-based custom progress bar with automatic updates

## Version History

- **v14**: Fixed extra space issue in configuration files
- Recent updates:
  - Progress bar with percentage inside
  - Auto-load configuration on path selection
  - Path persistence across sessions
  - Flashing progress tracking

## Credits

Developed for simplifying Yocto Project builds, especially for Raspberry Pi embedded systems.

## License

[Add your license information here]

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review [Yocto Project Documentation](https://docs.yoctoproject.org/)
3. Check build logs in terminal output

## Contributing

Contributions are welcome! Please ensure:
- Code is tested before submitting
- Follow existing code style
- Update README for new features
