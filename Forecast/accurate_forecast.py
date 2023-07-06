import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')
from gi.repository import Gtk
from gettext import gettext as _
from datetime import datetime
from Forecast.style import *
from Forecast.data import *

max_tmp_labels = []
min_tmp_labels = []
days_icons = []
days_names = []
main_window = None

class accurate_forecast(Gtk.Box):
    def __init__(self, window, meteo, forecast):
        super().__init__()
        global main_window
        main_window = window

        self.main_window = main_window

        self.days_stack = elements.dynamic_stack()

        self.days_switcher = Gtk.StackSidebar.new()
        self.days_switcher.set_stack(self.days_stack)

        self.append(self.days_switcher)
        self.append(self.days_stack)
        self.get_forecast_days(meteo, forecast)
        elements.add_page(self, 'Forecast', self.main_window.weather_stack, main_window.pages_names)
        main_window.icons_list.append(days_icons[0])

    def get_forecast_days(self, meteo, forecast):
        self.hours = 3
        self.day = 0
        self.day_weather = []

        min_temp = forecast["list"][0]['main']['temp']
        max_temp = forecast["list"][0]['main']['temp']
        self.min_temps = []
        self.max_temps = []
        date = str(datetime.today()).split('-')[2]
        today = str(date).split(' ')[0]

        for weather in forecast["list"]:
                temperature = weather['main']['temp']
                self.day_weather.append(weather)

                if temperature < min_temp:
                    min_temp = temperature
                if temperature > max_temp:
                    max_temp = temperature

                if self.hours % 24 == 0:

                    self.min_temps.append(min_temp)
                    self.max_temps.append(max_temp)

                    day_forecast(self, weather)

                    min_temp = temperature
                    max_temp = temperature
                    self.day_weather = []
                    self.day = self.day + 1

                self.hours = self.hours + 3
        self.days_stack.connect("notify::visible-child", change_bg, main_window, days_icons, days_names)

class day_forecast(Gtk.Box):
    def __init__(self, accurate_forecast, weather):
        super().__init__()
        global days_icons, days_names
        date_string = weather['dt_txt'][0:10]
        day_name = datetime.strptime(date_string, "%Y-%m-%d").strftime("%A")
        days_names.append(day_name)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_hexpand(True)

        max_temp = accurate_forecast.max_temps[accurate_forecast.day]
        min_temp = accurate_forecast.min_temps[accurate_forecast.day]
        day_icon = weather["weather"][0]['icon']
        day_id = weather["weather"][0]['id']
        day_img = app_style.create_icon(day_icon, 100, constants.icon_loc)
        day_img.set_valign(Gtk.Align.CENTER)

        days_icons.append(day_icon)

        self.top_left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        inner_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        inner_top.append(Gtk.Image.new_from_icon_name('go-up-symbolic'))
        inner_top.set_css_classes(['text_small'])
        inner_top.append(Gtk.Label(label=str(round(max_temp, 1)) + constants.degrees_unit))
        inner_bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        inner_bottom.append(Gtk.Image.new_from_icon_name('go-down-symbolic'))
        inner_bottom.append(Gtk.Label(label=str(round(min_temp, 1)) + constants.degrees_unit))
        inner_bottom.set_css_classes(['text_small'])
        inner_max_min = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        inner_max_min.append(inner_top)
        inner_max_min.append(inner_bottom)
        inner_max_min.set_valign(Gtk.Align.END)
        inner_max_min.set_margin_top(6)
        
        title_label = Gtk.Label()
        title_label.set_css_classes(['text_big'])
        title_label.set_label(app_style.get_wttr_description(day_id))
        title_label.set_valign(Gtk.Align.CENTER)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.append(title_label)
        title_box.append(inner_max_min)
        title_box.set_valign(Gtk.Align.CENTER)

        self.top_left_box.append(day_img)
        self.top_left_box.append(title_box)
        self.top_left_box.set_valign(Gtk.Align.START)

        self.top_right_box = Gtk.Box()

        self.main_box.append(self.top_left_box)
        self.main_box.append(self.get_hourly_info(accurate_forecast.day_weather))
        self.main_box.set_halign(Gtk.Align.CENTER)

        self.append(self.main_box)

        accurate_forecast.days_stack.add_titled(child=self, name=day_name, title=day_name)

    def get_hourly_info(self, day_weather):
        hourly_box = Gtk.Box(spacing=0)
        hourly_box.set_valign(Gtk.Align.END)

        for weather in day_weather:
            
            temp_lbl = Gtk.Label(label=str(round(weather['main']['temp'], 1)) + constants.degrees_unit)
            rain_prb = elements.info_box(str(int(weather['pop']*100)) + '%', 'weather-showers-scattered-symbolic')
            wind_spd = elements.info_box(str(weather['wind']['speed']) + constants.speed_unit, 'weather-windy-small')
            cndt_img = app_style.create_icon(weather["weather"][0]['icon'], 35, constants.icon_loc)
            date_lbl = Gtk.Label(label=weather['dt_txt'][10:16])
            
            hourly_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            hourly_info.set_size_request(80, 160)
            hourly_info.append(date_lbl)
            hourly_info.append(cndt_img)
            hourly_info.append(rain_prb)
            hourly_info.append(temp_lbl)
            hourly_info.set_margin_top(20)

            hourly_box.append(hourly_info)
            
        return hourly_box