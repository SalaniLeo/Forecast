import sys
import os

from .App import start

AppId="dev.salaniLeo.forecast"
flatpak = False
appimage = False

if 'FLATPAK_SANDBOX_DIR' in os.environ:
    flatpak = True

if 'IS_APP_APPIMAGE' in os.environ:
    appimage = True


class main():
    app = start(AppId,flatpak, appimage)