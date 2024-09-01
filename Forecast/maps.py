import gi, time
from .data import *
from gettext import gettext as _
gi.require_version('Gtk', '4.0')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk, WebKit

class maps_page(Gtk.Box):
    def __init__(self, app, city):
        super().__init__()

        layer = 'clouds_new'

        browser = WebKit.WebView()
        # browser.load_uri(f'https://tile.openweathermap.org/map/{layer}/{0}/{0}/{0}.png?appid=')
        # browser.load_uri(f'https://weather.salanileo.dev')

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_child(browser)
        scrolled_window.set_vexpand(True)
        self.append(scrolled_window)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_hexpand(True)
