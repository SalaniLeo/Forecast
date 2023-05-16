import sys
import os

from .App import start

AppId="dev.salaniLeo.forecast"
flatpak = False

if 'FLATPAK_SANDBOX_DIR' in os.environ:
    flatpak = True


class main():
    app = start(AppId,flatpak)