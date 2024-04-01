import gi, cairo, math
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk
from gettext import gettext as _

css_classes = []
night = False

class app_style():
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

    def get_wttr_description(code):
        switcher = {
            230 and 200: (_("Thunderstorm with Light Rain")),
            231 and 201: (_("Thunderstorm with Rain")),
            232 and 202: (_("Thunderstorm with Heavy Rain")),
            210: (_("Light Thunderstorm")),
            211: (_("Thunderstorm")),
            212: (_("Heavy Thunderstorm")),
            221: (_("Ragged Thunderstorm")),
            300: (_("Light Drizzle")),
            301: (_("Drizzle")),
            302: (_("Heavy Drizzle")),
            310: (_("Light Drizzle Rain")),
            311: (_("Drizzle Rain")),
            312: (_("Heavy Drizzle Rain")),
            313: (_("Shower Rain and Drizzle")),
            314: (_("Heavy Rain and Drizzle")),
            321: (_("Shower Drizzle")),
            500: (_("Light Rain")),
            501: (_("Moderate Rain")),
            502: (_("Heavy Rain")),
            503: (_("Very Heavy Rain")),
            504: (_("Extreme Rain")),
            511: (_("Freezing Rain")),
            520: (_("Light Shower Rain")),
            521: (_("Shower Rain")),
            522: (_("Heavy Shower Rain")),
            531: (_("Ragged Shower Rain")),
            600: (_("Light Snow")),
            601: (_("Snow")),
            602: (_("Heavy Snow")),
            611: (_("Sleet")),
            612: (_("Light Shower Sleet")),
            613: (_("Shower Sleet")),
            615: (_("Light Rain and Snow")),
            616: (_("Rain and Snow")),
            620: (_("Light Shower Snow")),
            621: (_("Shower Snow")),
            622: (_("Heavy Shower Snow")),
            701: (_("Mist")),
            711: (_("Smoke")),
            721: (_("Haze")),
            731: (_("Sand/Dust Whirls")),
            741: (_("Fog")),
            751: (_("Sand")),
            761: (_("Dust")),
            762: (_("Volcanic Ash")),
            771: (_("Squalls")),
            781: (_("Tornado")),
            800: (_("Clear Sky")),
            801: (_("Few Clouds")),
            802: (_("Scattered Clouds")),
            803: (_("Broken Clouds")),
            804: (_("Overcast Clouds"))
        }
        return switcher.get(int(code), ('Not available'))
    
    def apply_bg(main_window, icon, forecast):
        global night
        if not forecast:
            night = app_style.get_icon_info(icon)[-1]
        icon = app_style.get_icon_info(icon)[0]
        main_window.set_css_classes([app_style.get_css_bg(icon, night)[0], "main_window"])

    def draw_aqi_index(da: Gtk.DrawingArea, context: cairo.Context, width, height, index):
        width_index = index*10*2
        width_curve_radius = 2.5

        start = width_curve_radius*2
        end = width_index-width_curve_radius*2

        fixed_end = width-width_curve_radius*2

        y_top = height/3+width_curve_radius
        y_middle = height/2
        y_bottom = height-(height/3)-width_curve_radius

        radius_end_pixel = end+width_curve_radius
        radius_start_pixel = start-width_curve_radius

        context.set_source_rgba(255,255,255,0.25)
        context.move_to(start, y_top)
        context.line_to(fixed_end, y_top)
        context.stroke()

        color_code = app_style.get_color_gradient(index)

        context.set_source_rgba(color_code['red'], color_code['green'], color_code['blue'])
        context.set_line_width(10)
        context.move_to(start, y_top)
        context.line_to(end, y_top)
        context.curve_to(end, y_top, radius_end_pixel, y_middle, end, y_bottom)
        context.line_to(start, y_bottom)
        context.curve_to(start, y_bottom, radius_start_pixel, y_middle, start+1, y_top)

        context.stroke()

    def get_color_gradient(number):
        green_value = int((5 - number) * 255 / 4)
        red_value = int((number - 1) * 255 / 4)
        color_dict = {'red': red_value, 'green': green_value, 'blue': 0}
        return color_dict

    def draw_forecast_temps(da: Gtk.DrawingArea, context: cairo.Context, width, height, intervals, start, end):

        gradient = cairo.LinearGradient(0, 0, width, 0)
        gradient.add_color_stop_rgb(0, 66/255, 135/255, 245/255)
        gradient.add_color_stop_rgb(1, 245/255, 209/255, 66/255)

        context.set_source(gradient)

        width=width-(width/25)
        max_val = max(intervals)
        min_val = min(intervals)

        width_curve_radius = 2.5
        start_pixel = app_style.map_to_pixel(round(end), min_val, max_val, width)+width_curve_radius*2
        end_pixel = app_style.map_to_pixel(round(start), min_val, max_val, width)-width_curve_radius

        y_top = height/3+width_curve_radius
        y_middle = height/2
        y_bottom = height-(height/3)-width_curve_radius

        radius_end_pixel = end_pixel+width_curve_radius
        radius_start_pixel = start_pixel-width_curve_radius

        context.set_line_width(7.5)
        context.move_to(start_pixel,y_top)

        if round(start) == round(end):
            context.arc(start_pixel, y_middle, width_curve_radius,  0, 2 * math.pi)
        elif abs(round(start) - round(end)) == 1:
            end_pixel = end_pixel*math.sqrt(2)
            radius_end_pixel = end_pixel+width_curve_radius
            context.line_to(end_pixel,y_top)
            context.curve_to(end_pixel,y_top, radius_end_pixel, y_middle, end_pixel, y_bottom)
            context.line_to(start_pixel,y_bottom)
            context.curve_to(start_pixel, y_bottom, radius_start_pixel, y_middle, start_pixel+1, y_top)
        else:
            context.line_to(end_pixel,y_top)
            context.curve_to(end_pixel,y_top, radius_end_pixel, y_middle, end_pixel, y_bottom)
            context.line_to(start_pixel,y_bottom)
            context.curve_to(start_pixel, y_bottom, radius_start_pixel, y_middle, start_pixel+1, y_top)

        context.stroke()

    def map_to_pixel(value, min_val, max_val, width):
        return (value - min_val) / (max_val - min_val) * width

    def draw_single_temp(da: Gtk.DrawingArea, context: cairo.Context, width, height, temp_to_draw, max_temp, min_temp):
        gradient = cairo.LinearGradient(0, 0, width, 0)
        gradient.add_color_stop_rgb(0, 66/255, 135/255, 245/255)
        gradient.add_color_stop_rgb(1, 245/255, 209/255, 66/255)

        width=width-(width/25)

        width_curve_radius = 2.5

        temp_pixel = app_style.map_to_pixel(temp_to_draw, min_temp, max_temp, width)
        y_middle = height/2

        start = app_style.map_to_pixel(min_temp, min_temp, max_temp, width)
        end = app_style.map_to_pixel(max_temp, min_temp, max_temp, width)

        if temp_pixel < 2 * math.pi + width_curve_radius*2:
            temp_pixel += 2 * math.pi
        elif temp_pixel > 2 * math.pi - width_curve_radius*2:
            temp_pixel -= 2 * math.pi
        temp_pixel = round(temp_pixel)

        context.set_source_rgba(255,255,255,0.2)
        context.set_line_width(3.75)
        context.move_to(start,y_middle)
        context.line_to(end, y_middle)
        context.stroke()

        context.set_source(gradient)
        context.set_line_width(7.5)
        context.move_to(temp_pixel,y_middle)
        context.arc(temp_pixel, y_middle, width_curve_radius,  0, 2 * math.pi)
        context.stroke()

    def draw_astral_position(da: Gtk.DrawingArea, context: cairo.Context, width, height, hour):
        return

class Spinner(Gtk.Stack):
    def __init__(self, child):
        super().__init__()
        spinner = Gtk.Spinner.new()
        spinner.set_size_request(100, 100)
        spinner.start()
        spinner_box = Gtk.Box()
        spinner_box.append(spinner)
        spinner_box.set_halign(Gtk.Align.CENTER)
        spinner_box.set_valign(Gtk.Align.CENTER)
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.add_named(spinner_box, 'spinner')
        self.add_named(child, 'weather')
        self.set_vexpand(True)
        self.set_transition_duration(duration=250)