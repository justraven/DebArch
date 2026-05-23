# Maintainer: alim <your email>
pkgname=debarch
pkgver=1.0.0
pkgrel=1
pkgdesc="A PyQt6 GUI to easily convert and install Debian packages (.deb) on Arch Linux"
arch=('any')
url="https://github.com/alim/DebArch"
license=('MIT')
depends=('python' 'python-pyqt6' 'libarchive' 'polkit')
source=("deb_installer_gui.py"
        "debarch.desktop"
        "debarch.svg")
sha256sums=('SKIP'
            'SKIP'
            'SKIP')

package() {
    # Install the main Python script
    install -Dm755 "${srcdir}/deb_installer_gui.py" "${pkgdir}/usr/share/debarch/deb_installer_gui.py"
    
    # Create the launcher in /usr/bin
    mkdir -p "${pkgdir}/usr/bin"
    echo -e '#!/bin/sh\nexec python /usr/share/debarch/deb_installer_gui.py "$@"' > "${pkgdir}/usr/bin/debarch"
    chmod +x "${pkgdir}/usr/bin/debarch"

    # Install the desktop entry
    install -Dm644 "${srcdir}/debarch.desktop" "${pkgdir}/usr/share/applications/debarch.desktop"
    
    # Install the icon
    install -Dm644 "${srcdir}/debarch.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/debarch.svg"
}
