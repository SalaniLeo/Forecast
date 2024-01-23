import shutil
import os
from pathlib import Path

gschema_loc = str(Path.home()) + "/.local/glib-2.0/schemas"
current_loc = str(Path.cwd())

if(not os.path.exists(gschema_loc)):
    os.makedirs(gschema_loc)
shutil.copyfile(current_loc+"/data/dev.salaniLeo.forecast.gschema.xml", gschema_loc+"/dev.salaniLeo.forecast.gschema.xml")
os.system("glib-compile-schemas "+gschema_loc)
os.environ["GSETTINGS_SCHEMA_DIR"] = gschema_loc

if __name__ == '__main__':
    from gi.repository import Gio
    from Forecast import start
