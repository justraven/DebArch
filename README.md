<p align="center">
  <img src="debarch.svg" alt="DebArch Logo" width="140" height="140" />
</p>

<h1 align="center">DebArch Installer</h1>

<p align="center">
  <strong>just a GUI to convert and install Debian (.deb) packages natively on Arch Linux systems.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Arch%20Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white" alt="Arch Linux" />
  <img src="https://img.shields.io/badge/GUI-PyQt6-05c46b?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6" />
  <img src="https://img.shields.io/badge/Language-Python%203-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3" />
  <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License" />
</p>


## 📦 What is DebArch?

**DebArch** bridges the gap between Debian-based distributions and Arch Linux (including derivatives like CachyOS, EndeavourOS, and Manjaro). Many proprietary or niche utilities are distributed solely as `.deb` binaries. Rather than manually unpacking these files and cluttering your system, **DebArch** parses Debian metadata, auto-generates a clean Arch Linux standard `PKGBUILD`, builds a native `.pkg.tar.zst` package via `makepkg`, and registers it cleanly with the Pacman package database.

This ensures that Debian-only software can be tracked, updated, and cleanly uninstalled by Pacman without manual file tracing!

---

## 🛠️ Installation Guide

### Method 1: Clean System Install (Recommended)

You can build and install DebArch natively using the included `PKGBUILD` script. This integrates the app directly into your system desktop menu with custom shortcuts and icons:

1. Clone this repository:
   ```bash
   git clone https://github.com/USERNAME/DebArch.git
   cd DebArch
   ```
2. Build and install with `makepkg`:
   ```bash
   makepkg -si
   ```
3. Run it via your application launcher (search **"DebArch Installer"**) or from the command line:
   ```bash
   debarch
   ```

### Method 2: Download Pre-built Release Packages

If you don't want to build it yourself, you can download pre-compiled packages directly from GitHub Releases:
1. Navigate to the **Releases** page of this repository.
2. Download the `.pkg.tar.zst` asset for the latest release.
3. Install it using pacman:
   ```bash
   sudo pacman -U debarch-v*.pkg.tar.zst
   ```

### Method 3: Standalone/Portable Execution

If you prefer to run it without installing it to your system paths:
1. Install dependencies:
   ```bash
   sudo pacman -S python python-pyqt6 libarchive polkit
   ```
2. Run the script directly:
   ```bash
   python deb_installer_gui.py
   ```
   
---

## ⚙️ System Requirements

To run DebArch, ensure you have the following system components installed:
*   **Operating System:** Arch Linux or any Arch-based distribution (CachyOS, EndeavourOS, Manjaro).
*   **Python 3** (and standard libraries)
*   **PyQt6** (`python-pyqt6` package)
*   **bsdtar** (`libarchive` package, used to safely unpack Deb contents on Arch)
*   **polkit** (used for authorization during Pacman installation)

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.
