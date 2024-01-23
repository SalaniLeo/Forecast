import os

from .App import start

AppId="dev.salaniLeo.forecast"
app_type = None
appimage = False

if 'FLATPAK_SANDBOX_DIR' in os.environ:
    flatpak = True
    app_type = 'flatpak'
    
if 'SNAP' in os.environ:
    snap = True
    app_type = 'snap'

if 'IS_APP_APPIMAGE' in os.environ:
    appimage = True
    app_type = 'appimage'

if 'IS_DEBIAN' in os.environ:
    appimage = True
    app_type = 'debian'


class main():
    app = start(AppId, app_type)
