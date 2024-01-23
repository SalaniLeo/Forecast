import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk
from gettext import gettext as _

css_classes = []
night = False

class app_style():
    def create_icon(icon_id, icon_size, loc):

        img = Gtk.Image()
        img.set_pixel_size(icon_size)

        if icon_id == "01d":
            img.set_from_file(loc + 'weather-clear-large.svg')
        elif icon_id == "02d" or icon_id == "03d":
            img.set_from_file(loc + 'weather-few-clouds-large.svg')
        elif icon_id == "04d":
            img.set_from_file(loc + 'weather-overcast-large.svg')
        elif icon_id == "09d":
            img.set_from_file(loc + 'weather-showers-scattered-large.svg')
        elif icon_id == "10d":
            img.set_from_file(loc + 'weather-showers-large.svg')
        elif icon_id == "11d":
            img.set_from_file(loc + 'weather-storm-large.svg')
        elif icon_id == "13d":
            img.set_from_file(loc + 'weather-snow-large.svg')
        elif icon_id == "50d":
            img.set_from_file(loc + 'weather-fog-large.svg')

        # -------- night icon_ids --------- #
        elif icon_id == "01n":
            img.set_from_file(loc + 'weather-clear-night-large.svg')
        elif icon_id == "02n" or icon_id == "03n":
            img.set_from_file(loc + 'weather-few-clouds-night-large.svg')
        elif icon_id == "04n":
            img.set_from_file(loc + 'weather-overcast-large.svg')
        elif icon_id == "09n":
            img.set_from_file(loc + 'weather-showers-scattered-large.svg')
        elif icon_id == "10n":
            img.set_from_file(loc + 'weather-showers-large.svg')
        elif icon_id == "11n":
            img.set_from_file(loc + 'weather-storm-large.svg')
        elif icon_id == "13n":
            img.set_from_file(loc + 'weather-snow-large.svg')
        elif icon_id == "50n":
            img.set_from_file(loc + 'weather-fog-large.svg')
            
        return img

    # ---- sets icon for current weather ---- #
    def forecast_icon(icon, size, img, loc):
            img.set_pixel_size(size)
            
            if icon == "01d":
                img.set_from_file(loc + 'weather-clear-large.svg')
            elif icon == "02d" or icon == "03d":
                img.set_from_file(loc + 'weather-few-clouds-large.svg')
            elif icon == "04d":
                img.set_from_file(loc + 'weather-overcast-large.svg')
            elif icon == "09d":
                img.set_from_file(loc + 'weather-showers-scattered-large.svg')
            elif icon == "10d":
                img.set_from_file(loc + 'weather-showers-large.svg')
            elif icon == "11d":
                img.set_from_file(loc + 'weather-storm-large.svg')
            elif icon == "13d":
                img.set_from_file(loc + 'weather-snow-large.svg')
            elif icon == "50d":
                img.set_from_file(loc + 'weather-fog-large.svg')

            # -------- night icons --------- # 
            elif icon == "01n":
                img.set_from_file(loc + 'weather-clear-night-large.svg')
            elif icon == "02n" or icon == "03n":
                img.set_from_file(loc + 'weather-few-clouds-night-large.svg')
            elif icon == "04n":
                img.set_from_file(loc + 'weather-overcast-large.svg')
            elif icon == "09n":
                img.set_from_file(loc + 'weather-showers-scattered-large.svg')
            elif icon == "10n":
                img.set_from_file(loc + 'weather-showers-large.svg')
            elif icon == "11n":
                img.set_from_file(loc + 'weather-storm-large.svg')
            elif icon == "13n":
                img.set_from_file(loc + 'weather-snow-large.svg')
            elif icon == "50n":
                img.set_from_file(loc + 'weather-fog-large.svg')

    def get_icon_info(icon):
        info = []
        if 'd' in icon:
            base = icon.split('d')[0]
            icon = f'{base}d'
            night = False
        elif 'n' in icon:
            base = icon.split('n')[0]
            night = True
            icon = f'{base}n'
        info = [base, night]
        return info

    def get_css_bg(icon, night):
        if not night:
            if icon == "01":
                css_classes = ["clear_sky", night]
            elif icon == "02" or icon == "03":
                css_classes = ['few_clouds', night]
            elif icon == "04":
                css_classes = ['overcast', night]
            elif icon == "09":
                css_classes = ['showers_scattered', night]
            elif icon == "10":
                css_classes = ['showers_large', night]
            elif icon == "11":
                css_classes = ['storm', night]
            elif icon == "13":
                css_classes = ['snow', night]
            elif icon == "50":
                css_classes = ['fog', night]
        else:
            if icon == "01":
                css_classes = ['clear_sky_night', night]
            elif icon == "02" or icon == "03":
                css_classes = ['few_clouds_night', night]
            elif icon == "04":
                css_classes = ['overcast_night', night]
            elif icon == "09":
                css_classes = ['showers_scattered_night', night]
            elif icon == "10":
                css_classes = ['showers_large_night', night]
            elif icon == "11":
                css_classes = ['storm_night', night]
            elif icon == "13":
                css_classes = ['snow_night', night]
            elif icon == "50":
                css_classes = ['fog_night', night]
        return css_classes

    # ---- function to translate id to weather description ---- #
    def get_wttr_description(code):
        switcher = {
            230 and 200: (_('Thunderstorm with Light Rain')),
            231 and 201: (_('Thunderstorm with Rain')),
            232 and 202: (_('Thunderstorm with Heavy Rain')),
            210: (_('Light Thunderstorm')),
            211: (_('Thunderstorm')),
            212: (_('Heavy Thunderstorm')),
            221: (_('Ragged Thunderstorm')),
            300: (_('Light Drizzle')),
            301: (_('Drizzle')),
            302: (_('Heavy Drizzle')),
            310: (_('Light Drizzle Rain')),
            311: (_('Drizzle Rain')),
            312: (_('Heavy Drizzle Rain')),
            313: (_('Shower Rain and Drizzle')),
            314: (_('Heavy Rain and Drizzle')),
            321: (_('Shower Drizzle')),
            500: (_('Light Rain')),
            501: (_('Moderate Rain')),
            502: (_('Heavy Rain')),
            503: (_('Very Heavy Rain')),
            504: (_('Extreme Rain')),
            511: (_('Freezing Rain')),
            520: (_('Light Shower Rain')),
            521: (_('Shower Rain')),
            522: (_('Heavy Shower Rain')),
            531: (_('Ragged Shower Rain')),
            600: (_('Light Snow')),
            601: (_('Snow')),
            602: (_('Heavy Snow')),
            611: (_('Sleet')),
            612: (_('Light Shower Sleet')),
            613: (_('Shower Sleet')),
            615: (_('Light Rain and Snow')),
            616: (_('Rain and Snow')),
            620: (_('Light Shower Snow')),
            621: (_('Shower Snow')),
            622: (_('Heavy Shower Snow')),
            701: (_('Mist')),
            711: (_('Smoke')),
            721: (_('Haze')),
            731: (_('Sand/Dust Whirls')),
            741: (_('Fog')),
            751: (_('Sand')),
            761: (_('Dust')),
            762: (_('Volcanic Ash')),
            771: (_('Squalls')),
            781: (_('Tornado')),
            800: (_('Clear Sky')),
            801: (_('Few Clouds')),
            802: (_('Scattered Clouds')),
            803: (_('Broken Clouds')),
            804: (_('Overcast Clouds'))
        }
        return switcher.get(int(code), ('Not available'))
    
        # ---- applies gradient background ---- #
    def apply_bg(main_window, icon, forecast):
        global night
        if not forecast:
            night = app_style.get_icon_info(icon)[-1]
        icon = app_style.get_icon_info(icon)[0]
        main_window.set_css_classes([app_style.get_css_bg(icon, night)[0], "main_window"])