import requests, threading, gi, time
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, Adw, Gtk
from datetime import datetime
from gettext import gettext as _
from .style import *
from datetime import datetime

class constants():
    meters = _('Metric System')
    miles = _('Imperial System')
    metric_system = f'{meters}, °C - Km/h'
    imperial_system = f'{miles}, °F - mph'

    settings     = Gio.Settings.new("dev.salanileo.forecast")
    units        = settings.get_string('units').split(' ')[0].lower()
    raw_units    = settings.get_string('units')
    degrees_unit = raw_units[raw_units.find(",")+1:raw_units.find("-")]
    speed_unit   = raw_units[raw_units.find("-")+1:]
    poll_unit    = ' μg/m3'
    icon_loc     = None
    today        = datetime.now()
    api_key      = settings.get_string('api-key-s')
    available_units = [metric_system, imperial_system]
    time_formats = ['12', '24']
    time_am_pm   = ['am', 'pm']
    root         = None
    app          = None

    #pollution index
    air_good = _('Good')
    air_fair = _('Fair')
    air_moderate = _('Moderate')
    air_poor = _('Poor')
    air_very_poor = _('Very Poor')

    align_breakpoint = 700
    sidebar_breakpoint = 500
    min_window_size = sidebar_breakpoint/1.475

    def uv_index(uv_index):
        if uv_index >= 0 and uv_index <= 2:
            return "Low"
        elif uv_index >= 3 and uv_index <= 7:
            return "Seek shade during midday hours! Slip on a shirt, slop on sunscreen, and slap on a hat!"
        elif uv_index >= 8:
            return "Avoid being outside during midday hours! Make sure you seek shade! Shirt, sunscreen, and hat are a must!"
        else:
            return "Invalid UV index input. Please provide a number within the valid range."

    def wind_dir(angle):
        directions = [
            _("N"), _("NNE"), _("NE"), _("ENE"), _("E"), _("ESE"), _("SE"), _("SSE"),
            _("S"), _("SSW"), _("SW"), _("WSW"), _("W"), _("WNW"), _("NW"), _("NNW"),
        ]
        index = round(angle / (360.0 / len(directions))) % len(directions)
        return directions[index]

class global_variables():
    def get_saved_cities():
        return constants.settings.get_strv('wthr-locs')

    def get_city_name(city):
        return str(city).split("-")[0]

    def get_default_city():
        return constants.settings.get_int('selected-city')

    def get_temperature_units():
        return constants.settings.get_string('units').split(',')[-1].split('-')[0]

    def get_current_units():
        return constants.settings.get_string('units')

    def set_default_city(n):
        constants.settings.set_int("selected-city", n)

    def set_saved_cities(cities):
        constants.settings.set_strv('wthr-locs', cities)

    def set_default_units(units):
        constants.settings.set_string('units', units)

    def get_timezone_format():
        return constants.settings.get_int('time-format')

    def set_timezone_format(time_format):
        constants.settings.set_int('time-format', int(time_format))

    def get_max_search_cities():
        return 5

    def get_speed_units():
        return constants.settings.get_string('units').split(',')[-1].split('-')[-1]

    def get_distance_units():
        return global_variables.get_speed_units().split('/')[0]

class request():
    def weather(lat, lon):
        response = requests.get(f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units={constants.units}&appid={constants.api_key}')
        return response.json()

    def pollution(lat, lon):
        response = requests.get(f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&units={constants.units}&appid={constants.api_key}')
        return response.json()

row_list = []
class actions():
    def show_hide_sidebar(button, application):
        application.side_pane.set_show_sidebar(not application.side_pane.get_show_sidebar())

    def refresh_weather(button, app, stack):
        for city in global_variables.get_saved_cities():
            stack.remove(stack.get_child_by_name(city))

    def add_city(row, city, self=None):
        cities = global_variables.get_saved_cities()
        if city not in cities:
            cities.append(city)
            global_variables.set_saved_cities(cities)
            actions.refresh_weather(None, constants.app, constants.root)
        else:
            return
        if self != None:
            actions.switch_search(None, self.locations_stack)
            actions.load_preferences_saved_cities(self, True)

    def switch_search(button, stack, names=['locations','search']):
        name = names[names.index(stack.get_visible_child_name())]
        child = not bool(names.index(name))
        stack.set_visible_child(stack.get_child_by_name(names[child]))

    def load_preferences_saved_cities(self, reload):
        
        i = -1
        if reload:
            for row in row_list:
                self.locations.remove(row)

        default = Gtk.Button.new_from_icon_name("emblem-ok-symbolic")
        default.set_valign(Gtk.Align.CENTER)
        default.set_sensitive(False)
        default.set_css_classes(['flat'])

        for loc in global_variables.get_saved_cities(): 
            coords_raw = loc[loc.find("(")+1:loc.find(")")]

            place_name = loc.split('-')

            country_it = place_name[1][:3][1:]

            b = Gtk.Button()
            b.set_size_request(30,30)
            b.set_valign(Gtk.Align.CENTER)
            b.set_icon_name(icon_name='user-trash-symbolic')
            b.get_style_context().add_class(class_name='error')

            location = Adw.ActionRow.new()
            location.set_title(title=f'{place_name[0]}- {country_it}')
            location.set_subtitle(coords_raw)
            location.set_activatable(True)

            if i == global_variables.get_default_city()-1:
                location.add_suffix(default)
            location.add_prefix(b)
            self.locations.add(location)
            i += 1
            row_list.append(location)
            b.connect('clicked', self.remove_city, i, location, row_list)

        i = 0
        for row in row_list:
            row.connect("activated", self.set_default_city, i, row_list, default)
            i += 1
        
class converters():
    def convert_timezone(hours):
        if hours < 0:
            lbl = f'UTC {int(hours)}'
        else:
            lbl = f'UTC + {int(hours)}'
        return lbl

    def convert_timestamp(time):
        converted_time = datetime.fromtimestamp(time)
        formatted_time = converted_time.strftime("%H:%M")
        return formatted_time

    def convert_day(time):
        converted_time = datetime.fromtimestamp(time)
        formatted_time = converted_time.strftime("%A")
        return formatted_time

    # ---- converts the timezone of the selected city into real time ---- #
    def convert_time(timezone):
        local_time = timezone//3600
        converted_datetime = local_time + int(datetime.utcnow().strftime("%H"))
        if converted_datetime > 24:
            converted_datetime = "0" + str(converted_datetime - 24)
        elif(converted_datetime < 10) and local_time > 0:
            converted_datetime = "0" + str(converted_datetime)
        elif(converted_datetime < 10) and local_time < 0:
            converted_datetime = '0' + str(converted_datetime).split('-')[-1]
        local_full_time = str(converted_datetime) + ":" + datetime.now().strftime("%M")
        return local_full_time

    def convert_time_format(time_raw, timezone):
        o = 0
        time = int(converters.convert_timestamp(time_raw).split(':')[0])+int(timezone.split('.')[0])
        if(time > global_variables.get_timezone_format()):
            o = 1
        if time == 24: o = not o
        if time == 12: o = not o

        if time > global_variables.get_timezone_format():
            time = time - global_variables.get_timezone_format()
        if global_variables.get_timezone_format() == 12:
            return f'{str(time)}:{converters.convert_timestamp(time_raw).split(":")[-1]} {constants.time_am_pm[o]}'
        else:
            time = f'{str(time)}:{converters.convert_timestamp(time_raw).split(":")[-1]}'
            if time == '24:00':
                time = '00:00'
            return time


cities = []
        
class search_city():
    def init_thread(searchbar, preferenesgroup, self, reverse_query):
        global last_keydown, load

        search_thread = threading.Thread(target=search_city.get_search_result, args=(searchbar, preferenesgroup, self, reverse_query))
        search_thread.start()
        search_thread.join()

    def get_search_result(searchbar, preferenesgroup, self, reverse_query):
        global cities

        place_to_search = ""

        if type(reverse_query) == list:
            lat = reverse_query[0].get_text()
            lon = reverse_query[1].get_text()

            geocoding = requests.get(f'http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit={global_variables.get_max_search_cities()}&appid=72d251b81d30ef572ae667dfe6c4ee1a')
            data = geocoding.json() 
            #TODO API KEI
        elif type(reverse_query) == bool:
            place_to_search = searchbar.get_text()
            geocoding = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={place_to_search}&limit={global_variables.get_max_search_cities()}&appid=72d251b81d30ef572ae667dfe6c4ee1a')
            data = geocoding.json()
            if place_to_search == "":
                return
        elif type(reverse_query) == str:
            place_to_search = self
            geocoding = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={place_to_search}&limit=1&appid=72d251b81d30ef572ae667dfe6c4ee1a')
            city = geocoding.json()
            location = f'{city[0]["name"]} - {city[0]["country"]} ({city[0]["lat"]}; {city[0]["lon"]})'
            return location

        if len(cities) != 0:
            for every in cities:
                preferenesgroup.remove(every)
            cities = []

        for city in data:
            name = city['name']
            coords = f'{city["lat"]} {city["lon"]}'
            country = city['country']
            try:
                state = city['state']
            except:
                None

            city_format = f'{name} - {country} ({city["lat"]}; {city["lon"]})'

            new_city = Adw.ActionRow()
            new_city.set_title(name)
            new_city.set_subtitle(coords)
            new_city.set_hexpand(True)
            new_city.set_vexpand(True)
            new_city.set_activatable(True)

            try:
                state_widget = Gtk.Label.new(f'{state}, {country}')
                state_widget.set_css_classes(['font_light', 'font_small'])
                new_city.add_suffix(Gtk.Label.new(f'{state}, {country}'))
            except:
                new_city.add_suffix(Gtk.Label.new(f'{country}'))

            # try:
            #     response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?lat={city["lat"]}&lon={city["lon"]}&units={constants.units}&limit={global_variables.get_max_search_cities()}&appid=72d251b81d30ef572ae667dfe6c4ee1a')
            #     weather = response.json()
            #     icon = weather['weather'][0]['icon']
            #     icon_widget = Gtk.Image()
            #     app_style.forecast_icon(icon, 20, icon_widget, constants.icon_loc)
            #     new_city.add_suffix(icon_widget)
            #     temp = f'{round(weather["main"]["temp"])} {global_variables.get_temperature_units()}'
            #     temp_widget = Gtk.Label.new(str(temp))
            #     temp_widget.set_css_classes(['font_bold'])
            #     new_city.add_suffix(temp_widget)
            # except:
            #     None

            new_city.connect('activated', actions.add_city, city_format, self)

            cities.append(new_city)
            preferenesgroup.add(new_city)