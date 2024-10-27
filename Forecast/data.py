import requests, threading, gi, time, locale
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, Adw, Gtk
from datetime import datetime
from gettext import gettext as _
from .style import *
from datetime import datetime, timezone
import subprocess, os, json

class constants():
    meters = _("Metric System")
    miles = _("Imperial System")
    metric_system = f'{meters}, °C - Km/h'
    imperial_system = f'{miles}, °F - mi/h'
    system_locale = locale.getdefaultlocale()[0].split("_")[0]
    binary_path = f'{os.path.dirname(os.path.realpath(__file__))}/weatherInfo'

    settings     = Gio.Settings.new("dev.salaniLeo.forecast")
    units        = settings.get_string('units').split(' ')[0].lower()
    raw_units    = settings.get_string('units')
    degrees_unit = raw_units[raw_units.find(",")+1:raw_units.find("-")]
    speed_unit   = raw_units[raw_units.find("-")+1:]
    poll_unit    = ' μg/m3'
    icon_loc     = None
    today        = datetime.now()
    available_units = [metric_system, imperial_system]
    time_formats = ['12', '24']
    time_am_pm   = ['AM', 'PM']
    css_classes  = []
    days_css_classes = []
    day_names    = []
    root         = None
    app          = None
    toast_overlay= None
    city_page    = None
    last_refresh = 0

    #pollution index
    air_good = _("Good")
    air_fair = _("Fair")
    air_moderate = _("Moderate")
    air_poor = _("Poor")
    air_very_poor = _("Very Poor")

    align_breakpoint = 700
    sidebar_breakpoint = 500

    def uv_index(uv_index):
        if uv_index >= 0 and uv_index <= 2:
            return _("Low")
        elif uv_index >= 3 and uv_index <= 7:
            return _("Seek shade during midday hours!")
        elif uv_index >= 8:
            return _("Avoid being outside during midday hours!")
        else:
            return _("Invalid UV index input.")

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

    def set_use_dyn_bg(use):
        constants.settings.set_boolean('gradient-bg', use)

    def get_max_search_cities():
        return 5

    def get_speed_units():
        return constants.settings.get_string('units').split(',')[-1].split('-')[-1]

    def get_distance_units():
        return global_variables.get_speed_units().split('/')[0]

    def get_use_dyn_bg():
        return constants.settings.get_boolean('gradient-bg')

    def get_last_refresh():
        return constants.last_refresh

    def set_last_refresh(time):
        constants.last_refresh = time

    def get_api_key():
        if constants.settings.get_boolean("api-key-b"):
            return constants.settings.get_string('custom-api-key')
        else:
            return constants.settings.get_string('api-key-s')

    def set_api_key(key):
        return constants.settings.get_string('custom-api-key', key)

class request():
    def weather(lat, lon):
        command = f'exec {constants.binary_path} --request=weather --lat={lat} --lon={lon} --units={constants.units} --locale={constants.system_locale}'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def pollution(lat, lon):
        command = f'exec {constants.binary_path} --request=pollution --lat={lat} --lon={lon} --units={constants.units} --locale={constants.system_locale}'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return json.loads(result.stdout)

row_list = []
class actions():
    def show_hide_sidebar(button, application):
        application.side_pane.set_show_sidebar(not application.side_pane.get_show_sidebar())

    def refresh_weather(button, app, cities_stack):
        i = 0

        now = time.time()

        if(now - global_variables.get_last_refresh() >= 120):
            global_variables.set_last_refresh(time.time())
            for city in global_variables.get_saved_cities():
                if app.loaded_list[i] == True:
                    if i == global_variables.get_default_city() or city == cities_stack.get_visible_child_name():
                        load = True
                    else:
                        load = False
                    cities_stack.remove(cities_stack.get_child_by_name(city))
                    app.day_selector_stack.remove(app.day_selector_stack.get_child_by_name(city))

                    stack_page = constants.city_page.new(app, city, load)
                    constants.root.add_titled(child=stack_page, title=global_variables.get_city_name(city), name=city)
                    if app.day_selector_stack.get_parent() != None:
                        app.header_bar.remove(app.day_selector_stack)
                        app.header_bar.pack_start(app.city_selector)
                    if global_variables.get_use_dyn_bg():
                        constants.app.set_css_classes(constants.css_classes[global_variables.get_saved_cities().index(city)])
                i = i + 1
        else:
            constants.toast_overlay.add_toast(Adw.Toast(title=_('Wait at least 2 minutes between refreshes!')))


    def add_city(row, city, self=None):
        cities = global_variables.get_saved_cities()
        if city not in cities:
            cities.append(city)
            global_variables.set_saved_cities(cities)
            constants.app.add_city(False, city)
        else:
            return
        if self != None:
            city_num = 0
            actions.switch_search(None, self.locations_stack)
            actions.load_preferences_saved_cities(self, True, city_num)

    def switch_search(button, stack, names=['locations','search']):
        name = names[names.index(stack.get_visible_child_name())]
        child = not bool(names.index(name))
        stack.set_visible_child(stack.get_child_by_name(names[int(child)]))

    def switch_day(combobox, stack, self):
        stack.set_visible_child(stack.get_child_by_name(combobox.get_active_text()))
        if(global_variables.get_use_dyn_bg()):
            constants.app.set_css_classes(constants.days_css_classes[global_variables.get_saved_cities().index(self.city)][0][constants.day_names.index(combobox.get_active_text())])

    def switch_city(combobox):
        i = 0
        for city in global_variables.get_saved_cities():
            if combobox.get_active_text() == global_variables.get_city_name(city):
                constants.root.set_visible_child(constants.root.get_child_by_name(city))

    def load_preferences_saved_cities(self, reload, city_num):
        i = -1
        if reload:
            for row in row_list:
                self.locations.remove(row)

        default = Gtk.Button.new_from_icon_name("emblem-ok-symbolic")
        default.set_valign(Gtk.Align.CENTER)
        default.set_sensitive(False)
        default.set_css_classes(['flat'])

        row_list.clear()
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

        city_num = 0
        for row in row_list:
            row.connect("activated", self.set_default_city, city_num, row_list, default)
            city_num = city_num + 1

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

    def convert_timestamp_full(time):
        converted_time = datetime.fromtimestamp(time)
        formatted_time = converted_time.strftime("%D - %H:%M")
        return formatted_time

    def convert_day(time):
        converted_time = datetime.fromtimestamp(time)
        formatted_time = converted_time.strftime("%A")
        return formatted_time

    # ---- converts the timezone of the selected city into real time ---- #
    def convert_time(offset):
        local_offset = offset//3600
        now_utc = datetime.now(timezone.utc)
        utc_hour = now_utc.hour
        local_time = int(utc_hour + local_offset)

        if int(local_time) >= 24:
            local_time = "0" + str(int(local_time) - 24)
        if(int(local_time) < 10) and int(local_time) > 0:
            local_time = "0" + str(int(local_time))
        if(int(local_time) < 10) and int(local_time) < 0:
            local_time = '0' + str(local_time).split('-')[-1]
        local_full_time = str(local_time) + ":" + datetime.now().strftime("%M")

        return local_full_time

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

            command = f'exec {constants.binary_path} --request=reverse_geocoding --lat={lat} --lon={lon} --locale={constants.system_locale}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            data = json.loads(result.stdout)

        elif type(reverse_query) == bool:
            place_to_search = searchbar.get_text()
            command = f'exec {constants.binary_path} --request=geocoding --place_to_search={place_to_search}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            data = json.loads(result.stdout)
            if place_to_search == "":
                return

        elif type(reverse_query) == str:
            place_to_search = self
            command = f'exec {constants.binary_path} --request=geocoding --place_to_search={place_to_search}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            city = json.loads(result.stdout)

            if len(city) == 0:
                location = f'Ferrara - IT (44.8372737; 11.6186451)'
            else:
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
