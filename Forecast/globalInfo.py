import requests
from datetime import datetime
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, Gio, WebKit, GLib
from gettext import gettext as _
from threading import Thread

settings = Gio.Settings.new("dev.salaniLeo.forecast")
saved_locations = settings.get_strv('wthr-locs')
use_glassy = settings.get_boolean('use-glassy')

today = datetime.now()

degrees_unit = None
speed_unit = None
units = settings.get_string('units').split(' ')[0].lower()
raw_units = settings.get_string('units')
degrees_unit = raw_units[raw_units.find(",")+1:raw_units.find("-")]
speed_unit   = raw_units[raw_units.find("-")+1:]

last_refresh = 0

class global_weather(Gtk.Box):
    def __init__(self, thread, window):
        super().__init__()
        
        main_box = Gtk.Box()

        scrolled_window = Gtk.ScrolledWindow.new()
        scrolled_window.set_child(child=main_box)
        scrolled_window.set_vexpand(True)
        self.append(child=scrolled_window)

        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_end(6)
        self.set_margin_start(6)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_hexpand(True)
        
        main_box.append(self.get_widgets())

        window.stack.add_titled(self, 'Satellites', 'Satellites')
            
    def get_widgets(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label='Satellites - Meteosat')
        label.set_margin_top(12)
        label.set_margin_start(12)
        label.set_css_classes(['text_medium'])
        box.append(label)
        box.set_halign(Gtk.Align.START)
        
        browser = WebKit.WebView()
        browser.load_uri('https://google.com')
        # box.append(browser)
        
        return box

    def get_meteosat(self):
        response = requests.get("https://api.sat24.com/animated/EU/visual/1/Central%20European%20Standard%20Time/2648745")
        return response.raw()
    
