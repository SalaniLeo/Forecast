import requests
from datetime import datetime
from Forecast.accurate_forecast import *
from Forecast.style import app_style
from Forecast.data import *
import gi
import os
import time
import threading
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
from gettext import gettext as _

meteo = None
forecast = None
pollution = None
main_window = None
last_refresh = 0
app = None
lat = None
lon = None

base_infos = elements.conditions_box('base_info')
advanced_infos = elements.adv_conditions_box('advanced_infos')
title_label = Gtk.Label()
subtitle_label = Gtk.Label()
local_tm_label = Gtk.Label()
last_update = Gtk.Label()
situa_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
situa_img = Gtk.Image()
hourly_forecast_box = Gtk.Box(spacing=0, orientation=Gtk.Orientation.HORIZONTAL)
daily_forecast_box  = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

class main_page(Gtk.Box):
    def __init__(self, thread, window, name, package):
        super().__init__()
        global meteo, lat, lon, app, main_window, forecast, pollution
        main_window = window
        app = self

        elements.add_page(self, 'Weather', main_window.weather_stack, main_window.pages_names)

        process_locations(name)
        meteo = get_weather()
        pollution = get_pollution()
        process_forecast(False)
        main_window.icons_list.append(meteo['weather'][0]['icon'])

        # sets properties for current situa
        global title_label
        title_label.set_justify(Gtk.Justification.LEFT)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_valign(Gtk.Align.START)
        title_label.set_css_classes(['text_big'])

        # sets properties for temperature
        global subtitle_label
        subtitle_label.set_justify(Gtk.Justification.LEFT)
        subtitle_label.set_halign(Gtk.Align.START)
        subtitle_label.set_valign(Gtk.Align.START)
        subtitle_label.set_css_classes(['text_medium'])

        # sets properties for local time
        global local_tm_label
        local_tm_label.set_halign(Gtk.Align.START)
        local_tm_label.set_valign(Gtk.Align.START)

        # adds properties for conditions box
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        title_box.append(title_label)
        title_box.append(subtitle_label)
        title_box.append(local_tm_label)
        title_box.set_size_request(200, -1)
        title_box.set_halign(Gtk.Align.END)
        title_box.set_valign(Gtk.Align.CENTER)

        # sets properties for the current situa icon
        global situa_box, situa_img
        situa_img.set_valign(Gtk.Align.CENTER)
        situa_img.set_halign(Gtk.Align.CENTER)
        
        # adds all the elements to current situa box
        situa_box.append(situa_img)
        situa_box.append(title_box)
        situa_box.set_size_request(300, 150)

        # creates the box to switch city
        window.saved_loc_box = Gtk.ComboBoxText.new()
        window.saved_loc_box.set_active(index_=app_data.current_city_n())

        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.info_box.set_vexpand(True)
        self.info_box.set_size_request(100, -1)
        self.info_stack = Gtk.Stack()
        self.info_switcher = Gtk.StackSwitcher()
        self.info_switcher.set_stack(self.info_stack)
        self.info_switcher.add_css_class('info_sw')
        self.info_box.append(self.info_switcher)
        self.info_box.append(self.info_stack)

        conditions_boxes = get_info_box(False)
        
        self.info_stack.add_titled(child=conditions_boxes[0], name='Base', title=_('Base'))
        self.info_stack.add_titled(child=conditions_boxes[1], name='Advanced', title=_('Advanced'))
        self.info_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        global last_update
        last_update.set_halign(Gtk.Align.CENTER)
        last_update.set_valign(Gtk.Align.CENTER)

        load_locations(False, app_data.current_city_n(), window)
        
        window.saved_loc_box.connect('changed', switch_city)

        window.header_bar.pack_start(window.saved_loc_box)
        window.header_bar.pack_end(window.menu_button)
        window.header_bar.pack_end(window.add_button)
        window.header_bar.pack_start(window.refresh_button)        

        self.today_title = Gtk.Label(label=_('Today'))
        self.today_title.set_css_classes(['text_big'])
        self.today_title.set_halign(Gtk.Align.CENTER)
        self.today_title.set_valign(Gtk.Align.CENTER)

        self.today_title_box = Gtk.Box()
        self.today_title_box.append(self.today_title)
        self.today_title_box.set_halign(Gtk.Align.CENTER)
        self.today_title_box.set_margin_bottom(18)

        self.right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.right_box.append(self.today_title_box)
        self.right_box.append(hourly_forecast_box)
        self.right_box.append(self.info_box)
        self.right_box.set_hexpand(True)
        
        self.frcst_title = Gtk.Label(label=_('Forecast'))
        self.frcst_title.set_css_classes(['text_big'])
        self.frcst_title.set_halign(Gtk.Align.START)

        self.left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.left_box.append(fill_title(window, meteo))
        self.left_box.set_hexpand(True)
        self.left_box.append(self.frcst_title)
        self.left_box.append(daily_forecast_box)

        self.append(self.left_box)
        self.append(self.right_box)

        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_end(6)
        self.set_margin_start(12)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_hexpand(True)

        if app_data.use_dark_text() and app_data.use_gradient_bg():
            style.apply_enhanced_text(None, True)
        if app_data.use_glassy_elements():
            style.apply_glassy(None, True)
        if app_data.weather_locs_list() is not None:
            window.loading_stack.set_visible_child(window.weather_stack)

        accurate_forecast(main_window, meteo, forecast)

    # ---- function to refresh weather and change city ---- #
    def refresh(lati=None, longi=None, change_units=None):
        wttr_thrd = threading.Thread(target=reload_weather, args=(lati, longi, change_units))
        wttr_thrd.start()
        main_window.loading_stack.set_visible_child(main_window.spinner_box)

def reload_weather(lati, longi, change_units):
        global meteo, lat, lon, last_refresh, app, forecast, pollution
        current_time = time.time()

        if change_units == 'True':
            app_data.update_units()

        # -- checks if new city coords are being added to list -- #
        if lati == None:
            if change_units:
                meteo = get_weather() # requests newer data to apis
                pollution = get_pollution()
                process_forecast(True)
            else:
                if current_time - last_refresh >= 60:
                    last_refresh = current_time
                    meteo = get_weather() # requests newer data to apis
                    pollution = get_pollution()
                    process_forecast(True)
                else:
                    wait_toast = Adw.Toast.new(_('You must wait at least one minute to refresh'))
                    main_window.toast_overlay.add_toast(wait_toast)
        # -- if new city is being added -- #
        else:
            lat = lati  # updates global variables to new ones
            lon = longi #

            meteo = get_weather() # requests new city weather
            pollution = get_pollution()
            process_forecast(True)

        if app_data.use_glassy_elements() and app_data.use_gradient_bg():
            hours = int(convert_time(meteo["timezone"])[:2])
            if hours >= 19 or hours < 6:
                style.apply_enhanced_text(None, False)
            else:
                style.apply_enhanced_text(None, True)

        get_info_box(True) # updates labels to new city weather
        fill_title(main_window, meteo) # updates icon to new city weather

        main_window.loading_stack.set_visible_child(main_window.weather_stack)
        main_window.weather_stack.connect("notify::visible-child", change_bg, main_window, main_window.icons_list, main_window.pages_names)

# ---- updates cities inside combo box ---- #
def load_locations(remove, active, window):
    if remove:
        main_window.saved_loc_box.remove_all()
    for text in app_data.weather_locs_list():
        main_window.saved_loc_box.append_text(text=str(text.rsplit(" - ",1)[0]))
    main_window.saved_loc_box.set_active(index_=active)


# ---- sorts icons based on if it's the forecast or now ---- #
def fill_title(window, meteo):

        local_time  = str(convert_time(meteo['timezone']))        #
        name        = meteo['name']                               #
        icon        = meteo['weather'][0]['icon']                 # gets weather conditions
        situa       = meteo['weather'][0]['id']                   #
        temp        = int(meteo['main']['temp'])                  #

        window.set_title(name + ' - ' + app_style.get_wttr_description(situa)) # updates window title to current weather conditions

        # --- adds image for current weather ---- #
        app_style.forecast_icon(icon, 100, situa_img, constants.icon_loc)

        # ---- label for current weather info ---- #
        global title_label
        title_label.set_label(app_style.get_wttr_description(situa))

        global subtitle_label
        subtitle_label.set_label(str(temp) + constants.degrees_unit + '\n')

        global local_tm_label
        local_tm_label.set_label(_('Local time: ') + local_time)

        # --- applies gradient background if wanted --- #
        if app_data.use_gradient_bg():
            app_style.apply_bg(main_window, icon, False)

        return situa_box


# ---- weather api call ---- #
def get_weather():
    global last_update
    upd = str(' - '+_('Last update:') + datetime.now().strftime("%H:%M"))
    last_update.set_label(upd)
    response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={constants.units}&appid={constants.api_key}')
    return response.json()

def get_forecast():
    response = requests.get(f'http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units={constants.units}&appid={constants.api_key}')
    return response.json()

def get_pollution():
    response = requests.get(f'http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&units={constants.units}&appid={constants.api_key}')
    return response.json()

# ----- gets all the info for the bottom label ----- #
def get_info_box(refresh):

    base_text_label = base_infos[0]
    base_info_label = base_infos[1]

    adv_info_box = advanced_infos[0]
    adv_text_label = advanced_infos[1]
    adv_info_label = advanced_infos[2]
    pollution_label = advanced_infos[3]
    pollution_text_lbl = advanced_infos[4]
    sys_txt_lbl = advanced_infos[5]
    sys_info_lbl = advanced_infos[6]
    base_pllt_txt_lbl = advanced_infos[7]
    base_pllt_info_lbl = advanced_infos[8]


    base_box = Gtk.Box(spacing=38)
    base_box.set_halign(Gtk.Align.CENTER)

    conditions_boxes = []

    if not refresh:    
        base_box.append(base_text_label)
        base_box.append(base_info_label)
        conditions_boxes.append(base_box)
        conditions_boxes.append(adv_info_box)

    feels_like  = str(round(meteo['main']['feels_like'], 1)) + constants.degrees_unit
    humidity    = str(meteo["main"]["humidity"])   + "%    "
    wind_speed  = str(meteo['wind']['speed'])      + constants.speed_unit +' '+ constants.wind_dir(meteo['wind']['deg'])
    pressure    = str(meteo['main']['pressure'])   + ' hPa    '
    Visibility  = '>' + str(meteo['visibility']/1000) + constants.speed_unit.split('/')[0]
    Sunrise     = str(convert_timestamp(meteo['sys']['sunrise']))
    Sunset      = str(convert_timestamp(meteo['sys']['sunset']))
    Timezone    = str(convert_timezone(meteo['timezone']/3600))
    Last_update = last_update.get_text()[15:]

    pollution_level = str(pollution['list'][0]['main']['aqi'])
    pollution_co    = str(pollution['list'][0]['components']['co'])
    pollution_no    = str(pollution['list'][0]['components']['no'])
    pollution_no2   = str(pollution['list'][0]['components']['no2'])
    pollution_o3    = str(pollution['list'][0]['components']['o3'])
    pollution_so2   = str(pollution['list'][0]['components']['so2'])
    pollution_pm2_5 = str(pollution['list'][0]['components']['pm2_5'])
    pollution_pm10    = str(pollution['list'][0]['components']['pm10'])
    pollution_nh3   = str(pollution['list'][0]['components']['nh3'])

    try:
        wind_gusts  = str(meteo['wind']['gust']) + constants.speed_unit
        if wind_gusts == '0' + constants.speed_unit:
            wind_gusts = '...'
    except:
        wind_gusts  = '...'

    base_text_label.set_markup(
        _("Feels like") + '\n' +
        _("Wind") + '\n' +
        _("Pressure") + '\n' +
        _("Humidity") + '\n\n' +
        _("Last update")
    )

    base_info_label.set_markup(
        feels_like + '\n' +
        wind_speed + '\n' +
        pressure + '\n' +
        humidity + '\n\n' +
        Last_update
    )

    adv_text_label.set_markup(
        _("Feels like") + '\n' +
        _("Wind") + '\n' +
        _("Gusts") + '\n' +
        _("Pressure") + '\n' +
        _("Humidity") + '\n' + 
        _("Visibility")
    )

    adv_info_label.set_markup(
        feels_like + '\n' +
        wind_speed + '\n' +
        wind_gusts + '\n' +
        pressure + '\n' +
        humidity + '\n' + 
        Visibility
    )
    
    sys_txt_lbl.set_markup(
        _("Sunrise") + '\n' +
        _("Sunset") + '\n' +
        _("Timezone")
    )
    
    sys_info_lbl.set_markup(
        Sunrise + '\n' +
        Sunset + '\n' +
        Timezone
    )

    pollution_label.set_markup(
        _("co") + '\n' +
        _("no") + '\n' +
        _("no2") + '\n' +
        _("o3") + '\n' +
        _("so2") + '\n' +
        _("pm 2.5") + '\n' +
        _("pm 10") + '\n' +
        _("nh3") + '\n'
    )

    pollution_text_lbl.set_markup(
        pollution_co + '\n' +
        pollution_no + '\n' +
        pollution_no2 + '\n' +
        pollution_o3 + '\n' +
        pollution_so2 + '\n' +
        pollution_pm2_5 + '\n' +
        pollution_pm10 + '\n' +
        pollution_nh3 + '\n'
    )

    return conditions_boxes

# --- sets up forecast --- #
def process_forecast(refresh):
    global forecast
    global hourly_forecast_box
    global daily_forecast_box

    forecast = get_forecast() # calls api to get forecast

    daily_forecast_box.set_halign(Gtk.Align.START)

    hourly_forecast_box.set_halign(Gtk.Align.CENTER)
    hourly_forecast_box.set_valign(Gtk.Align.CENTER)

    hours = 3
    day = 0

    min_temp = forecast["list"][0]['main']['temp']
    max_temp = forecast["list"][0]['main']['temp']
    min_temps = []
    max_temps = []

    # adds everything related to the api response to the app
    for weather in forecast["list"]:

        # declares the temperature for every 3 hour interval
        temperature = weather['main']['temp']

        # adds 24h forecast per 3 hours intervals
        if hours <= 15:

            hourly_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            time_icon = weather['weather'][0]['icon']
            local_time = int(convert_time(forecast["city"]["timezone"])[:2]) + hours  # gets local city time

            if local_time >= 24: # checks if local_time is more than 24
                local_time = local_time - 24
                if local_time < 10: # checks if local_time is less than 10
                    local_time = '0' + str(local_time) # adds a zero to time es. 1 -> 01
            local_time = str(local_time) + ':00' # adds minutes to time es. 01 -> 01:00

            hourly_box.append(Gtk.Label(label=local_time))    # Creates box for every 3 hours prevision
            hourly_box.append(app_style.create_icon(time_icon, 45, constants.icon_loc))
            hourly_box.append(Gtk.Label(label=str(int(weather['main']['temp']))+constants.degrees_unit))
            hourly_box.set_margin_start(12)
            hourly_box.set_margin_end(12)

            if refresh:
                hourly_forecast_box.remove(hourly_forecast_box.get_first_child())

            hourly_forecast_box.append(hourly_box) # adds 3 hour interval to slider

        # checks the minimum temperature of the day
        if temperature < min_temp:
            min_temp = temperature

        # checks the maximum temperature of the day
        if temperature > max_temp:
            max_temp = temperature

        # saves both max and min temperatures of one day
        if hours % 24 == 0:
            min_temps.append(min_temp)
            max_temps.append(max_temp)

            if refresh:
                daily_forecast_box.remove(daily_forecast_box.get_first_child())

            # adds 5 days forecast
            daily_forecast_box.append(get_day_situa(weather, hours, int(min_temp), int(max_temp)))

            # resets min and max temperatures for the next day
            min_temp = temperature
            max_temp = temperature

            # counts the days
            day = day + 1

        hours = hours + 3

def get_day_situa(weather, hours, min_temp, max_temp):
    box = Gtk.Box(spacing=28)

    date_string = weather['dt_txt'][0:10]
    date = Gtk.Label()
    date.set_xalign(0)
    date.set_markup(datetime.strptime(date_string, "%Y-%m-%d").strftime("%A"))
    date.set_size_request(80, -1)

    time_icon = weather['weather'][0]['icon']

    box.append(date)
    box.append(app_style.create_icon(time_icon, 25, constants.icon_loc))
    box.append(Gtk.Label(label=str(min_temp) + constants.degrees_unit + '- ' + str(max_temp) + constants.degrees_unit))

    return box
    
def switch_city(combobox):
    global last_refresh
    current_time = time.time()
    if current_time - last_refresh >= 0.5:
        last_refresh = current_time
        if isinstance(combobox, int):
            city = app_data.weather_locs_list()[combobox]
        else:
                city = app_data.weather_locs_list()[combobox.get_active()]
        if city is not None:
            coords_raw = city[city.find("(")+1:city.find(")")] # gets coords of new city
            lati = coords_raw.split("; ")[0]  # gets latitude of new city  
            longi = coords_raw.split("; ")[1] # gets longitude of new city
            main_page.refresh(lati, longi, len(app_data.weather_locs_list()))
    
# ---- adds new city to cities list and calls each function to update weather and forecast based on new city ---- #
def add_city(city, window, first_time, search): 
    saved_locations = app_data.weather_locs_list()
    coords_raw = city[city.find("(")+1:city.find(")")] # gets coords of new city
    
    if len(coords_raw.split("; ")) == 2:
        if city in app_data.weather_locs_list(): # skips city if already added
            window.create_toast(_('The selected city has already been added'))
        else:
            saved_locations.append(str(city))   # adds new city to cities list
            constants.settings.set_strv('wthr-locs', saved_locations)  # updates gschema setting to contain new city
            if first_time:
                window.start_application()
            else:
                load_locations(True, len(saved_locations)-1, window)
                search.close_search(window)

# ---- funtction to get city based on user input ---- #
def get_cities(button, completion_model, search_entry):
    # gets user input
    name = search_entry.get_text()
    
    # calls api to get cities
    response = requests.get("http://api.openweathermap.org/data/2.5/find?q="+ name +"&units=metric&appid=72d251b81d30ef572ae667dfe6c4ee1a")
    data = response.json()    
    cod = data['cod']
    
    i = 0
    cities = []

    # checks if response if OK
    if int(cod) == 200:
        completion_model.clear()

        # gets info about each element given in the api response
        for element in data["list"]:
            text = element['name'] + " - " + element["sys"]['country'] + " (" + str(element["coord"]["lat"]) + "; " + str(element["coord"]["lon"]) + ")"

            cities.append(text) # adds info to cities list

        for city in cities:
            i = i + 1
            completion_model.insert_with_values(  #
                position=i,                            # adds city to dropdown menu
                columns=(1,),                          #
                values=[str(city)],                    #
            )

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

def process_locations(name):
    global lat, lon
    if name is not None:
        text_raw = name.split(" - ")[1]
    else:
        if app_data.current_city_n() < 0:
            constants.settings.set_int('selected-city', 0)
        if len(app_data.weather_locs_list()) <= app_data.current_city_n():
            constants.settings.set_int('selected-city', 0)
            text_raw = app_data.weather_locs_list()[0]
        else:
            text_raw = app_data.weather_locs_list()[app_data.current_city_n()]

        # extracts the coordinates from saved locations
        coords_raw = text_raw[text_raw.find("(")+1:text_raw.find(")")]
        lat = coords_raw.split("; ")[0]
        lon = coords_raw.split("; ")[1]

# ----- class to manage all the custom styling of the app ----- #
class style:
    def apply_enhanced_text(switch, state):
        time = int(convert_time(meteo["timezone"])[:2])
        if state:
            if time >= 19 or time < 6:
                app.set_css_classes(['light'])
                main_window.saved_loc_box.set_css_classes(['light'])
            else:
                app.set_css_classes(['dark'])
                main_window.saved_loc_box.set_css_classes(['dark'])
        else:
            if time >= 19 or time < 6:
                app.remove_css_class('dark')
                main_window.saved_loc_box.remove_css_class('dark')
            else:
                app.set_css_classes(['light'])
                main_window.saved_loc_box.set_css_classes(['light'])

    def apply_glassy(switch, state):
        if state:
            situa_box.set_css_classes(['glassy'])
            conditions_box.set_css_classes(['glassy'])
            daily_forecast_box.set_css_classes(['glassy'])
            hourly_forecast_box.set_css_classes(['glassy'])
        else:
            situa_box.remove_css_class('glassy')
            conditions_box.remove_css_class('glassy')
            daily_forecast_box.remove_css_class('glassy')
            hourly_forecast_box.remove_css_class('glassy')
