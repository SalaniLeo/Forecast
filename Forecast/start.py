import os
from .App import start

AppId="dev.salanileo.forecast"
app_type = None

if 'FLATPAK_SANDBOX_DIR' in os.environ:
    app_type = 'flatpak'

if 'IS_APP_APPIMAGE' in os.environ:
    app_type = 'appimage'

if 'SNAP' in os.environ:
    app_type = 'snap'

if 'IS_DEBIAN' in os.environ:
    app_type = 'debian'

class main():
    app = start(AppId, app_type)