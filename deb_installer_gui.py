#!/usr/bin/env python3
import sys
import os
import re
import shutil
import hashlib
import tempfile
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTextEdit, QProgressBar,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QProcess, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont

class DragDropWidget(QFrame):
    fileDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("DragDropWidget")
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumHeight(160)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        self.iconLabel = QLabel("📦", self)
        self.iconLabel.setStyleSheet("font-size: 54px; margin-bottom: 5px;")
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.iconLabel)
        
        self.textLabel = QLabel("Drag & Drop your .deb file here", self)
        self.textLabel.setStyleSheet("font-size: 15px; font-weight: bold; color: #f1f2f6;")
        self.textLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.textLabel)
        
        self.subTextLabel = QLabel("or click anywhere in this card to browse", self)
        self.subTextLabel.setStyleSheet("font-size: 12px; color: #747d8c;")
        self.subTextLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subTextLabel)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].toLocalFile().endswith(".deb"):
                self.setStyleSheet("border: 2px dashed #05c46b; background-color: #132019;")
                event.acceptProposedAction()
                
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.endswith(".deb"):
                self.fileDropped.emit(file_path)
                
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Debian Package", "", "Debian Packages (*.deb)"
            )
            if file_path:
                self.fileDropped.emit(file_path)


class DebArchMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DebArch Installer")
        self.setMinimumSize(700, 680)
        self.init_variables()
        self.setup_ui()
        self.apply_styles()
        
    def init_variables(self):
        self.selected_deb_path = None
        self.build_directory = None
        self.generated_pkg_path = None
        self.metadata = {}
        self.process = None
        self.sha256 = ""
        
    def setup_ui(self):
        # Main Widget and Scroll Area to ensure scrollability
        main_scroll = QScrollArea(self)
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(main_scroll)
        
        central_widget = QWidget()
        main_scroll.setWidget(central_widget)
        
        # Root Layout
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(30, 25, 30, 30)
        root_layout.setSpacing(20)
        
        # 1. Header Area
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        self.titleLabel = QLabel("DebArch Installer")
        self.titleLabel.setObjectName("AppTitle")
        
        self.subtitleLabel = QLabel("Convert and install Debian packages natively on Arch")
        self.subtitleLabel.setObjectName("AppSubtitle")
        
        header_layout.addWidget(self.titleLabel)
        header_layout.addWidget(self.subtitleLabel)
        root_layout.addLayout(header_layout)
        
        # 2. Drag & Drop Card
        self.dragDropCard = DragDropWidget(self)
        self.dragDropCard.fileDropped.connect(self.on_file_selected)
        root_layout.addWidget(self.dragDropCard)
        
        # 3. Details Card (collapsible / initially hidden)
        self.detailsCard = QFrame()
        self.detailsCard.setObjectName("DetailsCard")
        self.detailsCard.setFrameStyle(QFrame.Shape.StyledPanel)
        self.detailsCard.setVisible(False)
        
        details_layout = QVBoxLayout(self.detailsCard)
        details_layout.setContentsMargins(20, 20, 20, 20)
        details_layout.setSpacing(15)
        
        # Title of details section
        section_title = QLabel("Package Information")
        section_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #05c46b;")
        details_layout.addWidget(section_title)
        
        # Grid/Form style metadata columns
        meta_grid = QHBoxLayout()
        meta_grid.setSpacing(30)
        
        # Left meta column
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        self.nameLabel = QLabel("<b>Name:</b> Loading...")
        self.versionLabel = QLabel("<b>Version:</b> Loading...")
        self.archLabel = QLabel("<b>Architecture:</b> Loading...")
        self.sizeLabel = QLabel("<b>Installed Size:</b> Loading...")
        left_col.addWidget(self.nameLabel)
        left_col.addWidget(self.versionLabel)
        left_col.addWidget(self.archLabel)
        left_col.addWidget(self.sizeLabel)
        meta_grid.addLayout(left_col)
        
        # Right meta column
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        self.maintainerLabel = QLabel("<b>Maintainer:</b> Loading...")
        right_col.addWidget(self.maintainerLabel)
        
        self.descLabel = QLabel("<b>Description:</b> Loading...")
        self.descLabel.setWordWrap(True)
        self.descLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        right_col.addWidget(self.descLabel)
        meta_grid.addLayout(right_col, 1) # Expand right column
        
        details_layout.addLayout(meta_grid)
        
        # Action Buttons for compilation
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.buildBtn = QPushButton("🔧 Convert to Arch Package")
        self.buildBtn.setObjectName("BuildButton")
        self.buildBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.buildBtn.clicked.connect(self.start_package_build)
        
        self.clearBtn = QPushButton("Clear")
        self.clearBtn.setObjectName("ClearButton")
        self.clearBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clearBtn.clicked.connect(self.reset_ui)
        
        btn_layout.addWidget(self.buildBtn, 2)
        btn_layout.addWidget(self.clearBtn, 1)
        details_layout.addLayout(btn_layout)
        
        root_layout.addWidget(self.detailsCard)
        
        # 4. Console Logs / Progress card (initially hidden)
        self.consoleCard = QFrame()
        self.consoleCard.setObjectName("ConsoleCard")
        self.consoleCard.setFrameStyle(QFrame.Shape.StyledPanel)
        self.consoleCard.setVisible(False)
        
        console_layout = QVBoxLayout(self.consoleCard)
        console_layout.setContentsMargins(20, 20, 20, 20)
        console_layout.setSpacing(15)
        
        self.progressLabel = QLabel("Status: Idle")
        self.progressLabel.setStyleSheet("font-weight: bold; font-size: 13px; color: #f1f2f6;")
        console_layout.addWidget(self.progressLabel)
        
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        console_layout.addWidget(self.progressBar)
        
        self.consoleText = QTextEdit()
        self.consoleText.setObjectName("ConsoleLog")
        self.consoleText.setReadOnly(True)
        self.consoleText.setMinimumHeight(180)
        console_layout.addWidget(self.consoleText)
        
        # Install buttons shown after success
        self.installBtn = QPushButton("⚡ Install with Pacman")
        self.installBtn.setObjectName("InstallButton")
        self.installBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.installBtn.setVisible(False)
        self.installBtn.clicked.connect(self.install_arch_package)
        console_layout.addWidget(self.installBtn)
        
        root_layout.addWidget(self.consoleCard)
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0c0d12;
            }
            QWidget {
                color: #f1f2f6;
                font-family: 'Segoe UI', 'Ubuntu', 'Helvetica Neue', sans-serif;
            }
            QFrame#DragDropWidget {
                border: 2px dashed #2f3542;
                border-radius: 12px;
                background-color: #141722;
            }
            QFrame#DragDropWidget:hover {
                border-color: #05c46b;
                background-color: #181d2a;
            }
            QFrame#DetailsCard, QFrame#ConsoleCard {
                background-color: #141722;
                border: 1px solid #1e2230;
                border-radius: 12px;
            }
            QLabel#AppTitle {
                font-size: 26px;
                font-weight: bold;
                color: #05c46b;
            }
            QLabel#AppSubtitle {
                font-size: 13px;
                color: #747d8c;
            }
            QPushButton#BuildButton {
                background-color: #05c46b;
                color: #0c0d12;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#BuildButton:hover {
                background-color: #26de81;
            }
            QPushButton#BuildButton:disabled {
                background-color: #2f3542;
                color: #747d8c;
            }
            QPushButton#ClearButton {
                background-color: #1c1f2b;
                color: #f1f2f6;
                font-size: 14px;
                border: 1px solid #2f3542;
                border-radius: 8px;
                padding: 12px 20px;
            }
            QPushButton#ClearButton:hover {
                background-color: #2f3542;
            }
            QPushButton#InstallButton {
                background-color: #00e676;
                color: #0c0d12;
                font-weight: bold;
                font-size: 15px;
                padding: 14px 20px;
                border: none;
                border-radius: 8px;
                margin-top: 10px;
            }
            QPushButton#InstallButton:hover {
                background-color: #2dfd82;
            }
            QTextEdit#ConsoleLog {
                background-color: #07080c;
                color: #a4b0be;
                border: 1px solid #1c1f2b;
                border-radius: 8px;
                font-family: 'Fira Code', 'Courier New', monospace;
                font-size: 12px;
                padding: 8px;
            }
            QProgressBar {
                border: 1px solid #1c1f2b;
                border-radius: 6px;
                background-color: #0c0d12;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: #05c46b;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #0c0d12;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #2f3542;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #05c46b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

    def on_file_selected(self, file_path):
        self.selected_deb_path = file_path
        self.consoleCard.setVisible(False)
        self.installBtn.setVisible(False)
        self.progressBar.setValue(0)
        self.consoleText.clear()
        
        # Load package metadata
        self.show_progress_status("Reading package metadata...")
        self.detailsCard.setVisible(True)
        self.buildBtn.setEnabled(False)
        
        try:
            self.metadata = self.extract_deb_metadata(file_path)
            self.sha256 = self.calculate_file_sha256(file_path)
            self.populate_metadata_fields()
            self.buildBtn.setEnabled(True)
        except Exception as e:
            self.nameLabel.setText("<b>Error reading package!</b>")
            self.descLabel.setText(f"Details: {str(e)}")
            self.buildBtn.setEnabled(False)
            
    def calculate_file_sha256(self, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def extract_deb_metadata(self, deb_path):
        # Create temp folder to extract control
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Find control tar file inside deb
            result = subprocess.run(["bsdtar", "-tf", deb_path], capture_output=True, text=True, check=True)
            files = result.stdout.splitlines()
            control_tar = None
            for f in files:
                if "control.tar" in f:
                    control_tar = f
                    break
            
            if not control_tar:
                raise Exception("Missing control.tar inside Debian package")
                
            # Extract control archive
            subprocess.run(["bsdtar", "-xf", deb_path, "-C", tmp_dir, control_tar], check=True)
            
            # Extract control file from control.tar
            control_tar_path = os.path.join(tmp_dir, control_tar)
            subprocess.run(["bsdtar", "-xf", control_tar_path, "-C", tmp_dir, "control"], check=True)
            
            control_path = os.path.join(tmp_dir, "control")
            if os.path.exists(control_path):
                with open(control_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                return self.parse_control_content(content)
            else:
                raise Exception("Failed to locate control file in control.tar")

    def parse_control_content(self, text):
        metadata = {}
        current_key = None
        for line in text.splitlines():
            if line.startswith(" ") or line.startswith("\t"):
                if current_key:
                    metadata[current_key] += "\n" + line.strip()
            else:
                if ":" in line:
                    key, val = line.split(":", 1)
                    current_key = key.strip()
                    metadata[current_key] = val.strip()
        return metadata

    def populate_metadata_fields(self):
        pkg_name = self.metadata.get("Package", "Unknown")
        version = self.metadata.get("Version", "Unknown")
        arch = self.metadata.get("Architecture", "Unknown")
        maintainer = self.metadata.get("Maintainer", "Unknown")
        
        # Calculate human-readable size
        size_str = self.metadata.get("Installed-Size", "0")
        try:
            size_kb = int(size_str)
            if size_kb > 1024:
                size = f"{size_kb / 1024:.2f} MB"
            else:
                size = f"{size_kb} KB"
        except ValueError:
            size = size_str
            
        desc = self.metadata.get("Description", "No description provided.")
        
        self.nameLabel.setText(f"<b>Name:</b> {pkg_name}")
        self.versionLabel.setText(f"<b>Version:</b> {version}")
        self.archLabel.setText(f"<b>Architecture:</b> {arch}")
        self.sizeLabel.setText(f"<b>Installed Size:</b> {size}")
        self.maintainerLabel.setText(f"<b>Maintainer:</b> {maintainer}")
        
        # Format description beautifully
        formatted_desc = desc.replace("\n", "<br>")
        self.descLabel.setText(f"<b>Description:</b><br>{formatted_desc}")
        
    def start_package_build(self):
        if not self.selected_deb_path:
            return
            
        self.consoleCard.setVisible(True)
        self.consoleText.clear()
        self.progressBar.setValue(10)
        self.show_progress_status("Setting up build directory...")
        
        # Create persistent build directory under ~/.cache/deb-installer
        self.build_directory = os.path.expanduser(f"~/.cache/deb-installer/{self.metadata.get('Package', 'build')}")
        if os.path.exists(self.build_directory):
            shutil.rmtree(self.build_directory)
        os.makedirs(self.build_directory, exist_ok=True)
        
        # Generate custom PKGBUILD file
        try:
            self.write_pkgbuild()
        except Exception as e:
            self.append_log(f"Error generating PKGBUILD: {str(e)}\n")
            self.progressBar.setValue(0)
            self.show_progress_status("Failed to create build environment.")
            return
            
        self.progressBar.setValue(25)
        self.show_progress_status("Compiling with makepkg...")
        self.append_log(f"Build environment initialized at {self.build_directory}\n")
        self.append_log("Starting makepkg execution...\n\n")
        
        # Asynchronously run makepkg using QProcess
        self.process = QProcess(self)
        self.process.setWorkingDirectory(self.build_directory)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_process_stdout)
        self.process.finished.connect(self.on_build_finished)
        
        # Execute makepkg (using -f to overwrite, -c to clean after build)
        self.process.start("makepkg", ["-f"])
        self.buildBtn.setEnabled(False)

    def write_pkgbuild(self):
        orig_name = self.metadata.get("Package", "vsclient-linux")
        # Sanitize package name for Arch standard (lowercase, no spaces/underscores)
        pkgname = orig_name.lower()
        pkgname = re.sub(r'[^a-z0-9@._+-]', '', pkgname)
        
        pkgver = self.metadata.get("Version", "1.0").replace("-", "_")
        pkgdesc = self.metadata.get("Description", "Repackaged Debian package").split("\n")[0]
        maintainer = self.metadata.get("Maintainer", "Repackaged")
        
        pkgbuild_content = f"""# Maintainer: {maintainer}
pkgname={pkgname}
pkgver={pkgver}
pkgrel=1
pkgdesc="{pkgdesc}"
arch=('x86_64')
license=('custom')
depends=('glibc' 'gcc-libs' 'hicolor-icon-theme')
options=('!strip')
source=("{pkgname}-${{pkgver}}-amd64.deb::file://{self.selected_deb_path}")
sha256sums=('{self.sha256}')

prepare() {{
	cd "${{srcdir}}"
	if [ -f data.tar.gz ]; then
		bsdtar -xf data.tar.gz
	elif [ -f data.tar.xz ]; then
		bsdtar -xf data.tar.xz
	elif [ -f data.tar.zst ]; then
		bsdtar -xf data.tar.zst
	elif [ -f data.tar.bz2 ]; then
		bsdtar -xf data.tar.bz2
	fi
}}

package() {{
	cd "${{srcdir}}"
	if [ -d opt ]; then
		cp -rp opt "${{pkgdir}}/"
	fi
	if [ -d usr ]; then
		cp -rp usr "${{pkgdir}}/"
	fi
}}
"""
        with open(os.path.join(self.build_directory, "PKGBUILD"), "w", encoding="utf-8") as f:
            f.write(pkgbuild_content)

    def on_process_stdout(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.append_log(data)
        
        # Basic progress increment based on key output lines
        if "Validating source files" in data:
            self.progressBar.setValue(40)
        elif "Extracting sources" in data:
            self.progressBar.setValue(60)
        elif "Entering fakeroot environment" in data:
            self.progressBar.setValue(75)
        elif "Creating package" in data:
            self.progressBar.setValue(90)

    def on_build_finished(self, exit_code, exit_status):
        self.buildBtn.setEnabled(True)
        if exit_code == 0:
            self.progressBar.setValue(100)
            self.show_progress_status("Success: Package built successfully!")
            
            # Find the output package path
            files = os.listdir(self.build_directory)
            pkg_file = None
            for f in files:
                if f.endswith(".pkg.tar.zst"):
                    pkg_file = f
                    break
            
            if pkg_file:
                self.generated_pkg_path = os.path.join(self.build_directory, pkg_file)
                self.append_log(f"\n[SUCCESS] Native Arch package created: {pkg_file}\n")
                self.installBtn.setVisible(True)
            else:
                self.append_log("\n[ERROR] Built package could not be found in build directory.\n")
                self.show_progress_status("Failed to locate built package.")
        else:
            self.progressBar.setValue(0)
            self.show_progress_status("Error: Build failed.")
            self.append_log(f"\n[FAIL] makepkg process exited with error code {exit_code}\n")

    def install_arch_package(self):
        if not self.generated_pkg_path:
            return
            
        self.installBtn.setEnabled(False)
        self.show_progress_status("Installing package... Check Polkit authentication dialog.")
        self.append_log("\nRunning security prompt for password (pkexec pacman -U)...\n")
        
        # Run pacman installation via pkexec asynchronously
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_process_stdout)
        self.process.finished.connect(self.on_install_finished)
        
        self.process.start("pkexec", ["pacman", "-U", "--noconfirm", self.generated_pkg_path])

    def on_install_finished(self, exit_code, exit_status):
        self.installBtn.setEnabled(True)
        if exit_code == 0:
            self.show_progress_status("Success: Package installed successfully!")
            self.append_log("\n[SUCCESS] Package was successfully registered and installed on your system!\n")
        else:
            self.show_progress_status("Error: Installation aborted or failed.")
            self.append_log(f"\n[FAIL] Installation process exited with code {exit_code}. Authentication might have been cancelled or failed.\n")

    def show_progress_status(self, text):
        self.progressLabel.setText(f"Status: {text}")
        
    def append_log(self, text):
        # Auto-scroll console output to the bottom
        self.consoleText.insertPlainText(text)
        cursor = self.consoleText.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.consoleText.setTextCursor(cursor)
        
    def reset_ui(self):
        self.init_variables()
        self.nameLabel.setText("<b>Name:</b> Loading...")
        self.versionLabel.setText("<b>Version:</b> Loading...")
        self.archLabel.setText("<b>Architecture:</b> Loading...")
        self.sizeLabel.setText("<b>Installed Size:</b> Loading...")
        self.maintainerLabel.setText("<b>Maintainer:</b> Loading...")
        self.descLabel.setText("<b>Description:</b> Loading...")
        self.detailsCard.setVisible(False)
        self.consoleCard.setVisible(False)
        self.installBtn.setVisible(False)
        self.progressBar.setValue(0)
        self.consoleText.clear()
        self.show_progress_status("Status: Idle")


def main():
    app = QApplication(sys.argv)
    window = DebArchMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
