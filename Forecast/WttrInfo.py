import requests
import pytz
from datetime import datetime, timedelta
import gi
from threading import Thread
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GObject

meteo = None
forecast = None
settings = Gio.Settings.new("dev.salaniLeo.forecast")
main_window = None
css_class = None
saved_locations = settings.get_strv('wthr-locs')

title = None

both_update = True #TODO

lat = None
lon = None

info_label = Gtk.Label()
situa_label = Gtk.Label()
situa_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
situa_img = Gtk.Image()

forecast_box = Gtk.Box(spacing=24, orientation=Gtk.Orientation.HORIZONTAL)

icon_loc = None

class main_page(Gtk.Box):
    def __init__(self, thread, window, name, flatpak):
        super().__init__()
        
        global icon_loc
        global meteo
        global lat
        global lon
        
        if name is not None:
            text_raw = name.split(" - ")[1]
        else:
            text_raw = saved_locations[0]
            
        if flatpak:
            icon_loc = '/app/share/icons/hicolor/scalable/status/'
        # elif appimage:
        #     icon_loc.load_from_path('style.css')
        else:
            icon_loc = 'data/status/'
            
        coords_raw = text_raw[text_raw.find("(")+1:text_raw.find(")")]
            
        lat = coords_raw.split("; ")[0]
        lon = coords_raw.split("; ")[1]
        
        # -- gets weather from api -- #  
        meteo = get_wttr(lat, lon)
        
        # -- sets main_window to windo -- #
        global main_window
        main_window = window
        
        # -- adds properties for conditions label -- #
        global situa_label
        situa_label.set_justify(Gtk.Justification.CENTER)
        situa_label.set_halign(Gtk.Align.CENTER)
        situa_label.set_css_classes(['text_big'])
        
        # -- adds properties for conditions box -- #
        global situa_box
        situa_box.set_hexpand(True)
        situa_box.append(situa_img)
        situa_box.append(situa_label)
        situa_box.set_margin_top(12)
        situa_box.set_margin_bottom(12)
        
        window.saved_loc_box = Gtk.ComboBoxText.new()
        
        load_locations(False, 0, window)

        
        # adds everything to headerbar
        window.header_bar.pack_start(window.saved_loc_box)
        window.header_bar.pack_start(window.refresh_button)
        window.header_bar.pack_end(window.menu_button)
        window.header_bar.pack_end(window.add_button)
        
        window.saved_loc_box.set_active(index_=0)


        # ------ top grid ------ #

        self.icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.icon_box.append(set_icon(window, meteo, False))
        self.icon_box.append(set_info(meteo))
        self.icon_box.set_margin_start(12)
        self.icon_box.set_halign(Gtk.Align.FILL)

        
        # ------ forecast ------ #

        get_forecast(False)

        forecast_window = Gtk.ScrolledWindow()

        forecast_window.set_min_content_height(100)
        forecast_window.set_child(forecast_box)
        forecast_window.set_halign(Gtk.Align.FILL)
        forecast_window.set_hexpand(True)
        forecast_window.set_margin_top(44)

        # ------ main page ------ #
        
        self.set_margin_top(6)
        self.set_margin_bottom(6)
        self.set_margin_end(6)
        self.set_margin_start(6)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        
        
        self.append(self.icon_box)
        self.append(forecast_window)
                
        # -- adds itself to stack -- #
        
        window.stack.add_child(self)
        if saved_locations is not None:
            window.stack.set_visible_child(self)
    
        window.saved_loc_box.connect('changed', switch_city)

    
    # ---- function to refresh weather and change city ---- #
    def refresh(lati, longi, box_pos):
        global meteo
        global lat
        global lon
        
        # -- checks if new city coords are being added to list -- #
        if lati == None:
            
            meteo = get_wttr(lat, lon) # requests newer data to apis
                
        # -- if new city is being added -- #
        else: 
            
            lat = lati  # updates global variables to new ones
            lon = longi #

            meteo = get_wttr(lati, longi) # requests new city weather
            
            # main_window.header_bar.set_css_classes(['title'])
            global title 
            title = Gtk.Label(label=meteo["name"] +" - "+meteo["weather"][0]['description']).set_css_classes(['title'])
            
            main_window.header_bar.set_title_widget()                         


        set_info(meteo) # updates labels to new city weather
        set_icon(main_window, meteo, False) # updates icon to new city weather
        if both_update:
            get_forecast(True)
        

    # ---- box used to fill blanc spaces ---- #
    def wttr_fill(self):
        wttr_fill = Gtk.Box()
        wttr_fill.set_hexpand(True)
        wttr_fill.set_vexpand(False)
        return wttr_fill

# ---- updates cities inside combo box ---- #
def load_locations(remove, active, window):
    if window is not None:
        global main_window
        main_window = window
        
    if remove:
        main_window.saved_loc_box.remove_all()
    for text in saved_locations:
        main_window.saved_loc_box.append_text(text=str(text.rsplit(" - ",1)[0]))
    main_window.saved_loc_box.set_active(index_=active)

# ---- sorts icons based on if it's the forecast or now ---- #
def set_icon(window, meteo, forecast):
        
        # checks if forecast is being requested 
        if not forecast:
            
            name = meteo['name']                               #
            sky_value = meteo['weather'][0]['description']     #
            icon = meteo['weather'][0]['icon']                 # gets weather conditions
            situa = meteo['weather'][0]['id']                  #
            temp = round(meteo['main']['temp'], 1)             #
            
            window.set_title(name + ' - ' + sky_value) # updates window title to current weather conditions
            
            # --- adds image for current weather ---- #
            global situa_box
            forecast_icon(icon, 100, False)
            
            # ---- label for current weather info ---- #
            global situa_label
            situa_label.set_markup(get_wttr_description(situa) + "\n" + str(temp) + " °C")

            # --- applies gradient background if wanted --- #
            if settings.get_boolean('gradient-bg'):
                apply_bg(None, True)

        return situa_box        


# ---- weather api call ---- #
def get_wttr(lat, lon):
    response = requests.get("http://api.openweathermap.org/data/2.5/weather?lat="+ lat +"&lon="+ lon +"&units="+ "metric" +"&appid=" + settings.get_string('api-key-s'))
    return response.json()

    
# ---- forecast api call ---- # 
def get_frcst():
    response = requests.get("http://api.openweathermap.org/data/2.5/forecast?lat="+ lat +"&lon="+ lon +"&units="+ "metric" +"&appid=" + settings.get_string('api-key-s'))
    return response.json()


# --- converts wind degrees to direction --- #
def wind_dir(angle):
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
        ]
        index = round(angle / (360.0 / len(directions))) % len(directions)
        return directions[index]


# ----- gets all the info for the bottom label ----- #
def set_info(meteo):
    
    global info_label
    
    # --- gets info from api response --- #
    local_time  = str(convert_time(meteo['timezone']))
    feels_like  = str(round(meteo['main']['feels_like'], 1)) + " °C  "
    humidity    = str(meteo["main"]["humidity"])   + "%    "
    wind_speed  = str(meteo['wind']['speed'])      + "Km/h " + wind_dir(meteo['wind']['deg'])
    pressure    = str(meteo['main']['pressure'])   + " hPa "
    last_update = str(datetime.now().strftime("%H:%M"))

    info_label.set_margin_end(24)
    info_label.set_margin_top(24)
    info_label.set_halign(Gtk.Align.END)
    info_label.set_valign(Gtk.Align.CENTER)
    info_label.set_markup(       
            "Local time:  " +  local_time  + "\n" +
            "  Feels like:  " +  feels_like  + "\n" +
            "          Wind:  "       +  wind_speed  + "\n" +
            "  Humidity:  "   +  humidity    + "\n\n" +
            "  Last updated:  " + datetime.now().strftime("%H:%M")

    )        
            
    return info_label

# --- sets up forecast --- #
def get_forecast(refresh):
    global forecast
    global forecast_box
    
    forecast_box.set_hexpand(True)
    forecast_box.set_halign(Gtk.Align.CENTER)
    forecast = get_frcst() # calls api to get forecast

    i = 0
    hours = 0

    # adds forecast per 3 hours intervals
    for weather in forecast["list"]:
        i = i+1
        if i<10:

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)    #
            
            local_time = int(convert_time(forecast["city"]["timezone"])[:2]) + hours  # gets local city time
            
            if local_time > 24: # checks if local_time is more than 24
                local_time = local_time - 24
                if local_time < 10: # checks if local_time is less than 10
                    local_time = '0' + str(local_time) # adds a zero to time es. 1 -> 01
            local_time = str(local_time) + ':00' # adds minutes to time es. 01 -> 01:00
                         
                                
            box.append(Gtk.Label(label=local_time))    # Creates box for every 3 hours prevision
            box.append(set_frcst_icon(weather))                               # 
            box.append(Gtk.Label(label=str(round(weather['main']['temp'], 1)) + " °C")) #
            
            hours = hours + 3
            
            if refresh:
                forecast_box.remove(forecast_box.get_first_child())
            forecast_box.append(box) # adds 3 hour interval to slider
    
    
def switch_city(combobox):
    city = saved_locations[combobox.get_active()]
    
    if city is not None:
        coords_raw = city[city.find("(")+1:city.find(")")] # gets coords of new city
        lati = coords_raw.split("; ")[0]  # gets latitude of new city  
        longi = coords_raw.split("; ")[1] # gets longitude of new city
        
        main_page.refresh(lati, longi, len(saved_locations))
    
# ---- adds new city to cities list and calls each function to update weather and forecast based on new city ---- #
def add_city(city, window, first_time): 
    global saved_locations

    coords_raw = city[city.find("(")+1:city.find(")")] # gets coords of new city
    
    if len(coords_raw.split("; ")) == 2:
        
        if city in saved_locations: # skips city if already added
            # TODO
            None
        else:

            saved_locations.append(str(city))   # adds new city to cities list
            settings.set_strv('wthr-locs', saved_locations)  # updates gschema setting to contain new city
            
            if first_time:
                window.start_application()
            else:
                load_locations(True, len(saved_locations)-1, window)

 # --- starts thread to get location with openweatherapi --- #
def get_loc(button, self, entry, window, complete):
        wttr_thrd = Thread(target=get_cities, args=(self, entry))
        wttr_thrd.start()
        

# ---- funtction to get city based on user input ---- #
def get_cities(any, self, entry):

    # gets user input
    name = entry.get_text()
    
    # calls api to get cities
    response = requests.get("http://api.openweathermap.org/data/2.5/find?q="+ name +"&units=metric&appid=72d251b81d30ef572ae667dfe6c4ee1a")
    data = response.json()    
    cod = data['cod']
    
    i = 0
    cities = []

    # checks if response if OK
    if int(cod) == 200:
        self.completion_model.clear()

        # gets info about each element given in the api response
        for element in data["list"]:
            text = element['name'] + " - " + element["sys"]['country'] + " (" + str(element["coord"]["lat"]) + "; " + str(element["coord"]["lon"]) + ")"

            cities.append(text) # adds info to cities list

            for city in cities:
                i = i + 1 
                self.completion_model.insert_with_values(  #
                    position=i,                            # adds city to dropdown menu
                    columns=(1,),                          #
                    values=[str(city)],                    #
                )
    
# ---- applies gradient background ---- #
def apply_bg(switch, active):
    if active is True:
        main_window.set_css_classes([css_class, "main_window"])
        # print(css_class)


# ---- sets icon for forecast ---- #
def set_frcst_icon(forecast):
        
        icon_id = forecast["weather"][0]['icon']
                
        img = Gtk.Image()
        img.set_pixel_size(35)
                        
        if icon_id == "01d":
            img.set_from_file(icon_loc + 'weather-clear-large.svg')
        elif icon_id == "02d" or icon_id == "03d":
            img.set_from_file(icon_loc + 'weather-few-clouds-large.svg')
        elif icon_id == "04d":
            img.set_from_file(icon_loc + 'weather-overcast-large.svg')
        elif icon_id == "09d":
            img.set_from_file(icon_loc + 'weather-showers-scattered-large.svg')
        elif icon_id == "10d":
            img.set_from_file(icon_loc + 'weather-showers-large.svg')
        elif icon_id == "11d":
            img.set_from_file(icon_loc + 'weather-storm-large.svg')
        elif icon_id == "13d":
            img.set_from_file(icon_loc + 'weather-snow-large.svg')
        elif icon_id == "50d":
            img.set_from_file(icon_loc + 'weather-fog-large.svg')

        # -------- night icon_ids --------- # 
        elif icon_id == "01n":
            img.set_from_file(icon_loc + 'weather-clear-night-large.svg')
        elif icon_id == "02n" or icon_id == "03n":
            img.set_from_file(icon_loc + 'weather-few-clouds-night-large.svg')
        elif icon_id == "04n":
            img.set_from_file(icon_loc + 'weather-overcast-large.svg')
        elif icon_id == "09n":
            img.set_from_file(icon_loc + 'weather-showers-scattered-large.svg')
        elif icon_id == "10n":
            img.set_from_file(icon_loc + 'weather-showers-large.svg')
        elif icon_id == "11n":
            img.set_from_file(icon_loc + 'weather-storm-large.svg')
        elif icon_id == "13n":
            img.set_from_file(icon_loc + 'weather-snow-large.svg')
        elif icon_id == "50n":
            img.set_from_file(icon_loc + 'weather-fog-large.svg')

        return img
    
# ---- sets icon for current weather ---- #
def forecast_icon(icon, size, frcst):
    
        global css_class
        global situa_img
        
        situa_img.set_pixel_size(size)

        if icon == "01d":
            situa_img.set_from_file(icon_loc + 'weather-clear-large.svg')
            css_class = "clear_sky"
        elif icon == "02d" or icon == "03d":
            situa_img.set_from_file(icon_loc + 'weather-few-clouds-large.svg')
            css_class = 'few_clouds'
        elif icon == "04d":
            situa_img.set_from_file(icon_loc + 'weather-overcast-large.svg')
            css_class = 'overcast'
        elif icon == "09d":
            situa_img.set_from_file(icon_loc + 'weather-showers-scattered-large.svg')
            css_class = 'showers_scattered'
        elif icon == "10d":
            situa_img.set_from_icon_name(icon_loc + 'weather-showers-large.svg')
            css_class = 'showers_large'
        elif icon == "11d":
            situa_img.set_from_icon_name(icon_loc + 'weather-storm-large.svg')
            css_class = 'storm'
        elif icon == "13d":
            situa_img.set_from_icon_name(icon_loc + 'weather-snow-large.svg')
            css_class = 'snow'
        elif icon == "50d":
            situa_img.set_from_icon_name(icon_loc + 'weather-fog-large.svg')
            css_class = 'fog'

        # -------- night icons --------- # 
        elif icon == "01n":
            situa_img.set_from_icon_name(icon_loc + 'weather-clear-night-large.svg')
            css_class = 'clear_sky_night'
        elif icon == "02n" or icon == "03n":
            situa_img.set_from_icon_name(icon_loc + 'weather-few-clouds-night-large.svg')
            css_class = 'few_clouds_night'
        elif icon == "04n":
            situa_img.set_from_icon_name(icon_loc + 'weather-overcast-large.svg')
            css_class = 'overcast_night'
        elif icon == "09n":
            situa_img.set_from_icon_name(icon_loc + 'weather-showers-scattered-large.svg')
            css_class = 'showers_scattered_night'
        elif icon == "10n":
            situa_img.set_from_icon_name(icon_loc + 'weather-showers-large.svg')
            css_class = 'showers_large_night'
        elif icon == "11n":
            situa_img.set_from_icon_name(icon_loc + 'weather-storm-large.svg')
            css_class = 'storm_night'
        elif icon == "13n":
            situa_img.set_from_icon_name(icon_loc + 'weather-snow-large.svg')
            css_class = 'snow_night'
        elif icon == "50n":
            situa_img.set_from_icon_name(icon_loc + 'weather-fog-large.svg')
            css_class = 'fog_night'   


# ---- function to translate id to weather description ---- #
def get_wttr_description(code):
    switcher = {
        200: ('Thunderstorm with Light Rain'),
        201: ('Thunderstorm with Rain'),
        202: ('Thunderstorm with Heavy Rain'),
        210: ('Light Thunderstorm'),
        211: ('Thunderstorm'),
        212: ('Heavy Thunderstorm'),
        221: ('Ragged Thunderstorm'),
        230: ('Thunderstorm with Light Drizzle'),
        231: ('Thunderstorm with Drizzle'),
        232: ('Thunderstorm with Heavy Drizzle'),
        300: ('Light Drizzle'),
        301: ('Drizzle'),
        302: ('Heavy Drizzle'),
        310: ('Light Drizzle Rain'),
        311: ('Drizzle Rain'),
        312: ('Heavy Drizzle Rain'),
        313: ('Shower Rain and Drizzle'),
        314: ('Heavy Rain and Drizzle'),
        321: ('Shower Drizzle'),
        500: ('Light Rain'),
        501: ('Moderate Rain'),
        502: ('Heavy Rain'),
        503: ('Very Heavy Rain'),
        504: ('Extreme Rain'),
        511: ('Freezing Rain'),
        520: ('Light Shower Rain'),
        521: ('Shower Rain'),
        522: ('Heavy Shower Rain'),
        531: ('Ragged Shower Rain'),
        600: ('Light Snow'),
        601: ('Snow'),
        602: ('Heavy Snow'),
        611: ('Sleet'),
        612: ('Light Shower Sleet'),
        613: ('Shower Sleet'),
        615: ('Light Rain and Snow'),
        616: ('Rain and Snow'),
        620: ('Light Shower Snow'),
        621: ('Shower Snow'),
        622: ('Heavy Shower Snow'),
        701: ('Mist'),
        711: ('Smoke'),
        721: ('Haze'),
        731: ('Sand/Dust Whirls'),
        741: ('Fog'),
        751: ('Sand'),
        761: ('Dust'),
        762: ('Volcanic Ash'),
        771: ('Squalls'),
        781: ('Tornado'),
        800: ('Clear Sky'),
        801: ('Few Clouds'),
        802: ('Scattered Clouds'),
        803: ('Broken Clouds'),
        804: ('Overcast Clouds')
    }
    return switcher.get(int(code), ('Not available'))

def convert_time(timezone):
    
    local_time = timezone//3600
        
    global_time = pytz.timezone('Europe/London')  
    
    converted_datetime = local_time + int(datetime.utcnow().strftime("%H"))
        
    if converted_datetime > 24:
        converted_datetime = "0" + str(converted_datetime - 24)
    elif(converted_datetime<10):
        converted_datetime = "0" + str(converted_datetime)
        
    local_full_time = str(converted_datetime) + ":" + datetime.now().strftime("%M")
                
    return local_full_time