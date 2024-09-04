import gi, threading
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk
from gettext import gettext as _, pgettext as C_
from .data import *
from .page import *
from .style import *

class city_page(Gtk.Stack):
    def __init__(self, app, city):
        super().__init__()

        self.city         = city
        self.root         = Gtk.Box()
        self.day_selector = Gtk.ComboBoxText.new()
        self.css_classes  = []

        coords_raw = city[city.find("(")+1:city.find(")")]
        lat        = coords_raw.split("; ")[0]
        lon        = coords_raw.split("; ")[1]

        meteo      = request.weather(lat, lon)
        pollution  = request.pollution(lat, lon)

        try:
            now    = meteo['current']
            daily  = meteo['daily']
            hourly = meteo['hourly']
        except:
            if 'exceeding' in meteo:
                constants.toast_overlay.add_toast(Adw.Toast(title=_('Exceeded limit of api calls :(')))
            else:
                constants.toast_overlay.add_toast(Adw.Toast(title=_('Could not retrieve weather data')))
            return

        icon   = now['weather'][0]['icon']

        alerts = None
        try:
            alerts = meteo["alerts"]
        except:
            None

        if global_variables.get_use_dyn_bg():
            classes = app_style.get_css_bg(icon[:-1], icon[-1])
            constants.css_classes[global_variables.get_saved_cities().index(city)] = classes
            constants.app.set_css_classes(constants.css_classes[global_variables.get_saved_cities().index(city)])

        title_box = components.title_box(meteo)
        now_conditions = components.now_conditions(now, pollution, alerts)
        daily_forecast_box = components.daily_forecast(daily, self, app)
        hourly_forecast_box = components.hourly_forecast(meteo, hourly)
        # current_pollution_box = components.current_pollution(pollution)

        accurate_daily_forecast_stack = components.accurate_daily_forecast(daily, self, app)

        self.day_selector.set_active(index_=0)
        self.day_selector.connect('changed', actions.switch_day, accurate_daily_forecast_stack, self)

        app.day_selector_stack.add_titled(self.day_selector, city, city)

        # -- adds wather and forecast pages -- 
        self.add_named(self.root, _("Weather"))
        self.add_named(accurate_daily_forecast_stack, _("Forecast"))

        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

        # -- root container for page --
        base_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        base_box.set_hexpand(True)

        # -- left container --
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        right_box.append(hourly_forecast_box)
        right_box.set_spacing(6)
        right_box.append(now_conditions)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_box.append(title_box)
        left_box.set_hexpand(True)
        left_box.set_halign(Gtk.Align.START)
        # left_box.append(current_pollution_box)
        left_box.append(daily_forecast_box)

        base_box.append(left_box)
        base_box.append(right_box)

        self.root.append(base_box)
        self.root.set_orientation(Gtk.Orientation.VERTICAL)

        if(global_variables.get_use_dyn_bg()):
            self.connect("notify::visible-child", self.change_bg, self.css_classes)

        mobile_layout = Adw.Breakpoint() # TODO
        mobile_layout.add_setter(left_box, "halign", Gtk.Align.CENTER)
        mobile_layout.add_setter(base_box, "orientation", Gtk.Orientation.VERTICAL)
        mobile_layout.set_condition(Adw.BreakpointCondition.new_length(Adw.BreakpointConditionLengthType.MAX_WIDTH, constants.align_breakpoint, Adw.LengthUnit.SP))
        app.add_breakpoint(mobile_layout)

    def new(app, city, load):
        root = Gtk.ScrolledWindow()
        box = Gtk.Box()

        spinner = Spinner(box)
        root.set_child(spinner)
        if load:
            weather_thread = threading.Thread(target=city_page.fill_weather, args=(box, app, city, spinner))
            weather_thread.start()
            box.set_margin_top(12)
            box.set_margin_bottom(12)
            box.set_margin_start(12)
            box.set_margin_end(12)
        return root

    def fill_weather(box, app, city, spinner):
        box.append(city_page(app, city))
        spinner.set_visible_child(spinner.get_child_by_name('weather'))

    def change_bg(self, child, stack, css_classes):
        if self.get_visible_child_name() == "Weather":
            constants.app.set_css_classes(constants.css_classes[global_variables.get_saved_cities().index(self.city)])
        else:
            constants.app.set_css_classes(constants.days_css_classes[global_variables.get_saved_cities().index(self.city)][0][constants.day_names.index(self.day_selector.get_active_text())])


class components(city_page):
    def title_box(meteo):

        day_name    = str(converters.convert_day(meteo['current']['dt']))
        icon        = meteo['current']['weather'][0]['icon']
        conditions  = str(meteo['current']['weather'][0]['description'])
        temperature = str(round(meteo['current']['temp'], 1))
        feels_like  = str(round(meteo['current']['feels_like']))
        time_full   = str(converters.convert_time(meteo['timezone_offset']))

        if global_variables.get_timezone_format() == 12:
            d = datetime.strptime(str(time_full), "%H:%M")
            time_full = d.strftime("%I:%M %p")

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # -- icon --
        icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_widget = Gtk.Image()
        app_style.forecast_icon(icon, 100, icon_widget, constants.icon_loc)
        
        # -- title container -- #
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # -- title --
        title_widget = Gtk.Label.new(f'{conditions[0].upper()}{conditions[1:]}')
        title_widget.set_halign(Gtk.Align.START)
        title_widget.set_css_classes(['font_big'])
        title_widget.set_wrap(True)
        subtitle_box = Gtk.Box()
        subtitle_widget = Gtk.Label.new(f'{temperature}{global_variables.get_temperature_units()}')
        subtitle_widget.set_halign(Gtk.Align.START)
        subtitle_widget.set_css_classes(['font_medium'])
        feels_like_subtitle_widget = Gtk.Label.new(_("- Feels like {0}{1}").format(feels_like, global_variables.get_temperature_units()))
        feels_like_subtitle_widget.set_css_classes(['font_light', 'font_bold'])
        feels_like_subtitle_widget.set_valign(Gtk.Align.CENTER)
        subtitle_box.append(subtitle_widget)
        subtitle_box.append(feels_like_subtitle_widget)
        # -- container for icon and title container --
        icon_box.append(icon_widget)
        icon_box.append(title_box)
        icon_box.set_vexpand(False)

        # -- local time label --
        city_time = Gtk.Label.new(f'{day_name}, {time_full}')
        city_time.set_halign(Gtk.Align.START)
        city_time.set_valign(Gtk.Align.END)
        # -- top container for title and subtitle --
        top_title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        top_title_box.append(title_widget)
        top_title_box.append(subtitle_box)
        # -- bottom container for local time --
        bottom_title_box = Gtk.Box()
        bottom_title_box.append(city_time)
        bottom_title_box.set_valign(Gtk.Align.END)
        bottom_title_box.set_vexpand(False)
        # -- container for top and bottom containers --
        title_box.append(top_title_box)
        title_box.append(bottom_title_box)
        title_box.set_vexpand(False)
        title_box.set_css_classes(['title_box'])

        # icon_box.set_css_classes(['glass'])
        icon_widget.set_margin_top(6)
        icon_widget.set_margin_start(6)
        title_box.set_margin_end(6)
        icon_widget.set_margin_bottom(6)

        root.append(icon_box)
        root.set_vexpand(False)
        return root

    def alarm_box(alerts):
        label_box = Gtk.Box(spacing=3)
        data_box = Gtk.Box(spacing=3)

        label_box.append(components.label_label(_("Alerts")))
        label_box.set_valign(Gtk.Align.CENTER)
        label_box.set_halign(Gtk.Align.START)
        label_box.set_margin_top(6)
        label_box.set_size_request(60, -1)
        label_box.set_css_classes(['font_light'])

        alert_button = Gtk.Button.new_from_icon_name('dialog-warning-symbolic')
        alert_button.set_css_classes(['warning'])
        alert_button.connect('clicked', alarm_description, alerts, constants.app)

        data_box.append(alert_button)
        data_box.set_size_request(60, -1)

        return label_box, data_box

    def now_conditions(now, pollution, alerts):
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        base_box.set_halign(Gtk.Align.CENTER)

        top_bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title = Gtk.Label.new(_("Conditions"))
        title.set_css_classes(['font_medium'])
        top_bar.append(title)
        top_bar.set_hexpand(top_bar)

        base_box.append(top_bar)
        base_box.append(components.base_conditions(now, pollution, alerts))

        return base_box

    def base_conditions(now, pollution, alerts):
        base_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=32)
        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        label_box.set_hexpand(True)
        label_box.set_margin_start(32)
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        data_box.set_hexpand(True)

        label_box.add_css_class('font_light')
        label_box.append(components.label_label(_("Wind")))
        label_box.append(components.label_label(_("Pressure")))
        label_box.append(components.label_label(_("Humidity")))
        label_box.append(components.label_label(_("Visibility")))
        label_box.append(components.label_label(_("Sunrise")))
        label_box.append(components.label_label(_("Sunset")))
        label_box.append(components.label_label(_("AQI")))

        data_box.append(components.data_label(f'{now["wind_speed"]}{constants.speed_unit} {constants.wind_dir(now["wind_deg"])}'))
        data_box.append(components.data_label(f'{now["pressure"]}hPa'))
        data_box.append(components.data_label(f'{now["humidity"]}%'))
        data_box.append(components.data_label(f'{now["visibility"]/1000} {constants.speed_unit.split("/")[0]}'))
        data_box.append(components.data_label(f'{converters.convert_timestamp(now["sunrise"])}'))
        data_box.append(components.data_label(f'{converters.convert_timestamp(now["sunset"])}'))
        data_box.append(components.data_label(pollution['list'][0]['main']['aqi']))

        if(alerts is not None):
            pollution_label, pollution_data_label = components.alarm_box(alerts)
            label_box.append(pollution_label)
            data_box.append(pollution_data_label)

        base_box.append(label_box)
        base_box.append(data_box)

        return base_box

    def label_label(name):
        label = Gtk.Label.new(name)
        label.set_css_classes(['font_light'])
        label.set_halign(Gtk.Align.START)
        return label

    def data_label(name):
        label = Gtk.Label.new(str(name))
        label.set_halign(Gtk.Align.START)
        return label

    def adv_conditions(now, pollution):
        root = Gtk.Stack()

        root.add_titled(components.weather_conditions(now), "Weather", "Weather")
        root.add_titled(components.pollution_conditions(now), "Pollution", "Pollution")

        return root

    def weather_conditions(now):
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        top_box = Gtk.Box(spacing=6)

        back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        title_label = Gtk.Label(label=_("Weather"))
        title_label.set_hexpand(True)
        title_label.set_css_classes(['font_medium'])
        next_button = Gtk.Button.new_from_icon_name("go-next-symbolic")

        top_box.append(back_button)
        top_box.append(title_label)
        top_box.append(next_button)
        top_box.set_hexpand(True)

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        top_left_center_box = Gtk.Label(label=_("Conditions"))
        top_left_center_box.set_halign(Gtk.Align.START)
        top_left_center_box.set_css_classes(['font_bold'])
        bottom_left_center_box = Gtk.Box(spacing=6)

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        data_box.append(components.data_label(f'{now["feels_like"]}{constants.degrees_unit}'))
        data_box.append(components.data_label(f'{now["wind_speed"]}{constants.speed_unit} {constants.wind_dir(now["wind_deg"])}'))
        data_box.append(components.data_label(f'{now["pressure"]}hPa'))
        data_box.append(components.data_label(f'{now["humidity"]}%'))
        data_box.append(components.data_label(f'{now["visibility"]/1000}{constants.speed_unit.split("/")[0]}'))

        label_box.append(components.label_label(_("Feels Like")))
        label_box.append(components.label_label(_("Wind")))
        label_box.append(components.label_label(_("Pressure")))
        label_box.append(components.label_label(_("Pressure")))
        label_box.append(components.label_label(_("Visibility")))

        bottom_left_center_box.append(label_box)
        bottom_left_center_box.append(data_box)

        left_center_box.append(top_left_center_box)
        left_center_box.append(bottom_left_center_box)
        center_box.append(left_center_box)

        # base_box.append(top_box)
        base_box.append(center_box)

        return base_box

    def pollution_conditions(now):
        base_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_box = Gtk.Box(spacing=6)

        back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        weather_title_label = Gtk.Label(label=_("Weather"))
        next_button = Gtk.Button.new_from_icon_name("go-next-symbolic")

        top_box.append(back_button)
        top_box.append(weather_title_label)
        top_box.append(next_button)
        base_box.append(top_box)

        return base_box

    def hourly_forecast(meteo, hourly):
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title_widget = Gtk.Box()
        title_widget.append(Gtk.Label.new(_("Today")))
        title_widget.set_halign(Gtk.Align.CENTER)
        title_widget.set_margin_bottom(12)
        title_widget.set_css_classes(['font_medium'])
        hourly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        hourly_box.set_halign(Gtk.Align.CENTER)
        hourly_box.set_hexpand(True)
        # scrolled_window = Gtk.ScrolledWindow()
        # scrolled_window.set_hexpand(True)
        # scrolled_window.set_child(hourly_box)
        # scrolled_window.set_min_content_height(100)

        base_box.append(title_widget)
        base_box.append(hourly_box)

        i = 0
        for hour in hourly:
            if i <= 15 and i % 3 == 0:
                hour_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

                temp = hour['temp']
                icon = hour['weather'][0]['icon']

                time = int(converters.convert_time(meteo["timezone_offset"])[:2]) + i
                if time >= 24:
                    time = time - 24

                if global_variables.get_timezone_format() == 12:
                    d = datetime.strptime(str(time), "%H")
                    time = d.strftime("%I %p")
                else:
                    time = f'{time}:00'

                time_widget = Gtk.Label.new(str(time))
                hour_box.append(time_widget)

                temp_widget = Gtk.Label.new(f'{str(round(temp))} {global_variables.get_temperature_units()}')
                temp_widget.set_css_classes(['font_bold', 'font_light'])

                icon_widget = Gtk.Image()
                app_style.forecast_icon(icon, 35, icon_widget, constants.icon_loc)

                hour_box.append(icon_widget)
                hour_box.append(temp_widget)
                hourly_box.append(hour_box)
            i += 1

        return base_box

    def daily_forecast(daily, self, app):
        title_widget = Gtk.Label.new(_("Weekly forecast"))
        title_widget.set_css_classes(['font_medium'])
        title_widget.set_halign(Gtk.Align.START)

        title_button = Gtk.Button.new_from_icon_name('go-next-symbolic')
        title_button.set_css_classes(['flat'])
        title_button.set_size_request(-1, 25)
        title_button.connect('clicked', components.go_to_weather, self, app, ['Weather', 'Forecast'])

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title_box.append(title_widget)
        title_box.append(title_button)

        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        base_box.append(title_box)
        # base_box.set_halign(Gtk.Align.START)

        max_min = []
        overall_max = daily[0]['temp']['max']
        overall_min = daily[0]['temp']['min']

        i = 0
        for day in daily:
            if i < 7:
                day_name = converters.convert_day(day['dt'])
                max_temp = day['temp']['max']
                min_temp = day['temp']['min']
                icon     = day['weather'][0]['icon']

                if len(constants.day_names) < 7:
                    constants.day_names.append(day_name)

                max_min.append(max_temp)
                max_min.append(min_temp)
                if max_temp > overall_max: overall_max = max_temp
                if min_temp < overall_min: overall_min = min_temp

                day_box = components.temp_graph_box(day_name, icon, max_temp, min_temp, max_min)

                base_box.append(day_box)

            i += 1
        return base_box

    def temp_graph_box(day_name, icon, max_temp, min_temp, max_min):

        day_box = Gtk.Box(spacing=12)

        day_widget = Gtk.Label.new(day_name)
        day_widget.set_css_classes(['font_light', 'font_bold'])
        day_widget.set_size_request(80,-1)
        day_widget.set_xalign(0)

        icon_widget = Gtk.Image()
        app_style.forecast_icon(icon, 25, icon_widget, constants.icon_loc)

        max_min_box = Gtk.Box()
        max_widget = Gtk.Label.new(f'{round(max_temp)} {global_variables.get_temperature_units()}')
        min_widget = Gtk.Label.new(f'{round(min_temp)} {global_variables.get_temperature_units()}')

        temp_graph = Gtk.DrawingArea()
        temp_graph.set_draw_func(app_style.draw_forecast_temps, max_min, min_temp, max_temp)
        temp_graph.set_size_request(80,10)

        temp_box = Gtk.Box()
        temp_box.append(temp_graph)
        temp_box.set_size_request(80, -1)
        temp_box.set_margin_start(10)
        temp_box.set_margin_end(10)

        max_min_box.append(min_widget)
        max_min_box.append(temp_box)
        max_min_box.append(max_widget)

        day_box.append(icon_widget)
        day_box.append(day_widget)
        day_box.append(max_min_box)
        return day_box

    def current_pollution(pollution):
        right_expand_fill = Gtk.Box()
        right_expand_fill.set_hexpand(True)

        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        base_box.set_margin_top(12)
        base_box.set_hexpand(False)

        title_widget = Gtk.Label.new(_("Pollution"))
        title_widget.set_css_classes(['font_medium'])
        title_widget.set_halign(Gtk.Align.START)

        pollution_details = Gtk.Expander()
        subtitle_widget = Gtk.Label.new(_("Details"))
        subtitle_widget.set_css_classes(['font_medium', 'font_light'])
        subtitle_widget.set_halign(Gtk.Align.START)
        pollution_details.set_label_widget(subtitle_widget)

        center_box = Gtk.Box(spacing=12)
        aqi_center_box = Gtk.Box(spacing=12)
        aqi_line_box = Gtk.Box()
        main_box = Gtk.Box(spacing=12)

        for index in pollution['list']:
            aqi_data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            aqi_text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            aqi_text_box.set_css_classes(['font_light'])
            text_box.set_css_classes(['font_light'])

            overall_widget = Gtk.Label.new(str(index['main']['aqi']))
            overall_widget.set_halign(Gtk.Align.START)
            overall_widget.set_hexpand(True)

            # AQI: Air Quality Index
            overall_text_widget = Gtk.Label.new(C_("pollution", "AQI"))
            overall_text_widget.set_tooltip_text(C_("pollution", "AQI: Air Quality Index"))
            overall_text_widget.set_halign(Gtk.Align.END)
            overall_text_widget.set_hexpand(True)

            aqi_data_box.append(overall_widget)
            aqi_text_box.append(overall_text_widget)

            aqi_draw_line = Gtk.DrawingArea()
            aqi_draw_line.set_size_request(100, 20)
            aqi_draw_line.set_draw_func(app_style.draw_aqi_index, index['main']['aqi'])

            aqi_line_box.append(aqi_draw_line)

            co_widget = Gtk.Label.new(str(index['components']['co']))
            co_widget.set_halign(Gtk.Align.START)
            # CO: Carbon monoxide emissions, from sources like vehicles pose health risks
            co_text_widget = Gtk.Label.new(C_("pollution", "CO"))
            co_text_widget.set_tooltip_text(C_("pollution", "CO: Carbon monoxide emissions, from sources like vehicles pose health risks"))
            co_text_widget.set_halign(Gtk.Align.START)
            data_box.append(co_widget)
            text_box.append(co_text_widget)

            no_widget = Gtk.Label.new(str(index['components']['no']))
            no_widget.set_halign(Gtk.Align.START)
            # NO: Nitric oxide, a colorless gas, poses health risks, including respiratory issues
            no_text_widget = Gtk.Label.new(C_("pollution", "NO"))
            no_text_widget.set_tooltip_text(C_("pollution", "NO: Nitric oxide, a colorless gas, poses health risks, including respiratory issues"))
            no_text_widget.set_halign(Gtk.Align.START)
            data_box.append(no_widget)
            text_box.append(no_text_widget)

            # NO2: Nitrogen dioxide, a poisonous gas that can be fatal if inhaled in large quantities
            no2_widget = Gtk.Label.new(str(index['components']['no2']))
            no2_widget.set_halign(Gtk.Align.START)
            no2_text_widget = Gtk.Label.new(C_("pollution", "NO2"))
            no2_text_widget.set_tooltip_text(C_("pollution", "NO2: Nitrogen dioxide, a poisonous gas that can be fatal if inhaled in large quantities"))
            no2_text_widget.set_halign(Gtk.Align.START)
            data_box.append(no2_widget)
            text_box.append(no2_text_widget)

            o3_widget = Gtk.Label.new(str(index['components']['o3']))
            o3_widget.set_halign(Gtk.Align.START)
            # O3: Ozone (or trioxygen) is a strong oxidant, but at high concentrations, it poses respiratory hazards
            o3_text_widget = Gtk.Label.new(C_("pollution", "O3"))
            o3_text_widget.set_tooltip_text(C_("pollution", "O3: Ozone (or trioxygen) is a strong oxidant, but at high concentrations, it poses respiratory hazards"))
            o3_text_widget.set_halign(Gtk.Align.START)
            data_box.append(o3_widget)
            text_box.append(o3_text_widget)

            so2_widget = Gtk.Label.new(str(index['components']['so2']))
            so2_widget.set_halign(Gtk.Align.START)
            # SO2: Sulfur dioxide emissions from industry and fossil fuels can harm respiratory health
            so2_text_widget = Gtk.Label.new(C_("pollution", "SO2"))
            so2_text_widget.set_tooltip_text(C_("pollution", "SO2: Sulfur dioxide emissions from industry and fossil fuels can harm respiratory health"))
            so2_text_widget.set_halign(Gtk.Align.START)
            data_box.append(so2_widget)
            text_box.append(so2_text_widget)

            pm25_widget = Gtk.Label.new(str(index['components']['pm2_5']))
            pm25_widget.set_halign(Gtk.Align.START)
            # PM 2.5: Tiny airborne particles, deeply penetrate lungs, causing respiratory and cardiovascular issues
            pm25_text_widget = Gtk.Label.new(C_("pollution", "PM 2.5"))
            pm25_text_widget.set_tooltip_text(C_("pollution", "PM 2.5: Tiny airborne particles, deeply penetrate lungs, causing respiratory and cardiovascular issues"))
            pm25_text_widget.set_halign(Gtk.Align.START)
            data_box.append(pm25_widget)
            text_box.append(pm25_text_widget)

            pm10widget = Gtk.Label.new(str(index['components']['pm10']))
            pm10widget.set_halign(Gtk.Align.START)
            # PM 10: larger particles, pose health risks, especially to the respiratory system
            pm10_text_widget = Gtk.Label.new(C_("pollution", "PM 10"))
            pm10_text_widget.set_tooltip_text(C_("pollution", "PM 10: Larger particles, pose health risks, especially to the respiratory system"))
            pm10_text_widget.set_halign(Gtk.Align.START)
            data_box.append(pm10widget)
            text_box.append(pm10_text_widget)

            nh3_widget = Gtk.Label.new(str(index['components']['nh3']))
            nh3_widget.set_halign(Gtk.Align.START)
            # H3: Ammonia, emissions, primarily from agriculture and industry, harm respiratory health
            nh3_text_widget = Gtk.Label.new(C_("pollution", "NH3"))
            nh3_text_widget.set_tooltip_text(C_("pollution", "H3: Ammonia, emissions, primarily from agriculture and industry, harm respiratory health"))
            nh3_text_widget.set_halign(Gtk.Align.START)
            data_box.append(nh3_widget)
            text_box.append(nh3_text_widget)


        aqi_center_box.append(aqi_text_box)
        aqi_center_box.append(aqi_data_box)

        center_box.append(text_box)
        center_box.append(data_box)

        pollution_details.set_child(center_box)

        base_box.append(title_widget)
        base_box.append(aqi_center_box)
        base_box.append(aqi_line_box)

        base_box.append(pollution_details)

        main_box.append(base_box)
        main_box.append(right_expand_fill)

        return main_box

    def accurate_daily_forecast(daily, self, app):
        root = Gtk.Stack()
        root.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        i = 0
        boxes = []
        css_classes = []
        for day in daily:
            if i < 7:
                base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                base_box.set_margin_start(12)
                base_box.set_margin_end(12)
                base_box.set_margin_bottom(12)

                back_button = Gtk.Button.new_from_icon_name('window-close-symbolic')
                back_button.connect('clicked', components.back_to_wather, self, app, ['Weather', 'Forecast'])
                back_button.set_css_classes(['flat'])
                back_button.set_vexpand(False)
                back_button.set_valign(Gtk.Align.START)

                center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
                center_box.set_hexpand(True)

                top_box = Gtk.Box()

                # box = Gtk.Box()
                day_name = converters.convert_day(day['dt'])
                max_temp = day['temp']['max']
                min_temp = day['temp']['min']
                icon     = day['weather'][0]['icon']
                conditions = day['summary']

                icon_widget = Gtk.Image()
                app_style.forecast_icon(icon, 100, icon_widget, constants.icon_loc)
                self.day_selector.append_text(text=str(day_name))

                conditions_widget = Gtk.Label.new(conditions)
                conditions_widget.set_css_classes(['font_medium'])
                conditions_widget.set_halign(Gtk.Align.START)
                conditions_widget.set_wrap(True)
                conditions_widget.set_size_request(10, -1)

                icon_box = Gtk.Box()
                icon_box.append(icon_widget)

                max_box = Gtk.Box(spacing=6)
                max_widget = Gtk.Label.new(f'{str(round(max_temp))} {global_variables.get_temperature_units()}')
                max_widget.set_css_classes(['font_bold'])
                max_box.append(Gtk.Image.new_from_icon_name('go-up-symbolic'))
                max_box.append(max_widget)

                min_box = Gtk.Box(spacing=6)
                min_widget = Gtk.Label.new(f'{str(round(min_temp))} {global_variables.get_temperature_units()}')
                min_widget.set_css_classes(['font_bold'])
                min_box.append(Gtk.Image.new_from_icon_name('go-down-symbolic'))
                min_box.append(min_widget)

                max_min_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                max_min_box.append(max_box)
                max_min_box.append(min_box)
                max_min_box.set_margin_start(12)

                important_info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                important_info_box.append(conditions_widget)
                important_info_box.append(max_min_box)
                important_info_box.set_margin_top(6)
                important_info_box.set_margin_start(6)
                important_info_box.set_margin_end(6)
                important_info_box.set_margin_bottom(6)
                important_info_box.set_hexpand(True)

                top_box.append(icon_box)
                top_box.append(important_info_box)
                top_box.append(back_button)

                root.add_titled(base_box, day_name, day_name)

                day_temps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                day_temps_box.set_hexpand(True)
                day_temps_box.set_vexpand(False)

                night_temp = day['temp']['night']
                evening_temp = day['temp']['eve']
                morning_temp = day['temp']['morn']
                afternoon_temp = day['temp']['day']

                night_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                night_temp_label = Gtk.Label.new(_("Night"))
                night_temp_label.set_css_classes(['font_light'])
                night_temp_label.set_size_request(75, 20)
                night_temp_label.set_xalign(0)
                night_temp_label_data = Gtk.Label.new(f'{str(round(night_temp))} {global_variables.get_temperature_units()}')
                night_temp_graph = Gtk.DrawingArea()
                night_temp_graph.set_size_request(60, 20)
                night_temp_graph.set_draw_func(app_style.draw_single_temp, night_temp, max_temp, min_temp)
                night_temp_graph.set_hexpand(False)
                night_temp_box.append(night_temp_label)
                night_temp_box.append(night_temp_graph)
                night_temp_box.append(night_temp_label_data)

                evening_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                evening_temp_label = Gtk.Label.new(_("Evening"))
                evening_temp_label.set_css_classes(['font_light'])
                evening_temp_label.set_size_request(75, 20)
                evening_temp_label.set_xalign(0)
                evening_temp_label_data = Gtk.Label.new(f'{str(round(evening_temp))} {global_variables.get_temperature_units()}')
                evening_temp_graph = Gtk.DrawingArea()
                evening_temp_graph.set_size_request(60, 20)
                evening_temp_graph.set_draw_func(app_style.draw_single_temp, evening_temp, max_temp, min_temp)
                evening_temp_graph.set_hexpand(False)
                evening_temp_box.append(evening_temp_label)
                evening_temp_box.append(evening_temp_graph)
                evening_temp_box.append(evening_temp_label_data)

                morning_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                morning_temp_label = Gtk.Label.new(_("Morning"))
                morning_temp_label.set_css_classes(['font_light'])
                morning_temp_label.set_size_request(75, 20)
                morning_temp_label.set_xalign(0)
                morning_temp_label_data = Gtk.Label.new(f'{str(round(morning_temp))} {global_variables.get_temperature_units()}')
                morning_temp_graph = Gtk.DrawingArea()
                morning_temp_graph.set_size_request(60, 20)
                morning_temp_graph.set_draw_func(app_style.draw_single_temp, morning_temp, max_temp, min_temp)
                morning_temp_graph.set_hexpand(False)
                morning_temp_box.append(morning_temp_label)
                morning_temp_box.append(morning_temp_graph)
                morning_temp_box.append(morning_temp_label_data)

                afternoon_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                afternoon_temp_label = Gtk.Label.new(_("Afternoon"))
                afternoon_temp_label.set_css_classes(['font_light'])
                afternoon_temp_label.set_size_request(75, 20)
                afternoon_temp_label.set_xalign(0)
                afternoon_temp_label_data = Gtk.Label.new(f'{str(round(afternoon_temp))} {global_variables.get_temperature_units()}')
                afternoon_temp_graph = Gtk.DrawingArea()
                afternoon_temp_graph.set_size_request(60, 20)
                afternoon_temp_graph.set_draw_func(app_style.draw_single_temp, afternoon_temp, max_temp, min_temp)
                afternoon_temp_graph.set_hexpand(False)
                afternoon_temp_box.append(afternoon_temp_label)
                afternoon_temp_box.append(afternoon_temp_graph)
                afternoon_temp_box.append(afternoon_temp_label_data)

                temps_title_widget = Gtk.Label.new(_("Temperatures"))
                temps_title_widget.set_css_classes(['font_medium'])
                temps_title_widget.set_margin_bottom(6)
                temps_title_widget.set_halign(Gtk.Align.START)

                day_temps_box.append(temps_title_widget)
                day_temps_box.append(morning_temp_box)
                day_temps_box.append(afternoon_temp_box)
                day_temps_box.append(evening_temp_box)
                day_temps_box.append(night_temp_box)

                current_conditions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

                day_temp = components.info_label(_("Temperature"), f'{str(round(day["temp"]["day"]))}{global_variables.get_temperature_units()}')
                wind_speed = components.info_label(_("Wind speed"), f'{str(round(day["wind_speed"]))}{global_variables.get_speed_units()} {constants.wind_dir(day["wind_deg"])}')
                humidity = components.info_label(_("Humidity"), _("{0}%").format(str(round(day["humidity"]))))
                cloudiness = components.info_label(_("Cloudiness"), _("{0}%").format(str(round(day["clouds"]))))
                pop = components.info_label(_("Probability of rain"), _("{0}%").format(str(round(day["pop"]*100))))
                uv_index = components.info_label(_("UV Index"), f'{constants.uv_index(round(day["uvi"]))}  ({str(round(day["uvi"],1))})')

                conditions_title_widget = Gtk.Label.new(_("Conditions"))
                conditions_title_widget.set_css_classes(['font_medium'])
                conditions_title_widget.set_margin_bottom(6)
                conditions_title_widget.set_halign(Gtk.Align.START)

                current_conditions_box.append(conditions_title_widget)
                current_conditions_box.append(day_temp)
                current_conditions_box.append(wind_speed)
                current_conditions_box.append(humidity)
                current_conditions_box.append(cloudiness)
                current_conditions_box.append(pop)
                current_conditions_box.append(uv_index)
                current_conditions_box.set_size_request(200, -1)
                current_conditions_box.set_hexpand(True)

                center_top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
                center_top_box.set_vexpand(False)

                boxes.append(center_top_box)

                if(global_variables.get_use_dyn_bg()):
                    if 'night' in constants.css_classes[global_variables.get_saved_cities().index(self.city)][0]:
                        classes = app_style.get_css_bg(icon[:-1], 'n')
                    else:
                        classes = app_style.get_css_bg(icon[:-1], 'd')
                    self.css_classes.append(classes)
                    css_classes.append(classes)

                sunset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
                sunset_value = converters.convert_timestamp(day['sunset'])
                sunset_widget = Gtk.Label.new(_("Sunset"))
                sunset_widget.set_css_classes(['font_light'])
                sunset_value_widget = Gtk.Label.new(f'{str(sunset_value)}')
                sunset_box.append(sunset_widget)
                sunset_box.append(sunset_value_widget)

                sunrise_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
                sunrise_value = converters.convert_timestamp(day['sunrise'])
                sunrise_widget = Gtk.Label.new(_("Sunrise"))
                sunrise_widget.set_css_classes(['font_light'])
                sunrise_value_widget = Gtk.Label.new(f'{str(sunrise_value)}')
                sunrise_box.append(sunrise_widget)
                sunrise_box.append(sunrise_value_widget)

                sun_title = Gtk.Label.new(_("Sun"))
                sun_title.set_css_classes(['font_medium'])
                sun_title.set_halign(Gtk.Align.START)
                sun_title.set_margin_bottom(6)
                sunrise_sunset_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                sunrise_sunset_box.append(sun_title)
                sunrise_sunset_box.append(sunrise_box)
                sunrise_sunset_box.append(sunset_box)

                center_center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                center_center_box.append(current_conditions_box)

                center_top_box.append(day_temps_box)
                center_top_box.append(sunrise_sunset_box)

                center_box.append(center_top_box)
                center_box.append(center_center_box)

                base_box.append(top_box)
                base_box.append(center_box)
            i += 1
        constants.days_css_classes[global_variables.get_saved_cities().index(self.city)].append(css_classes)

        return root

    def go_to_weather(button, self, app, names):
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        actions.switch_search(button, self, names)

        names = ['Cities', "Days"]

        app.header_bar.remove(app.city_selector)
        app.header_bar.pack_start(app.day_selector_stack)

        app.day_selector_stack.set_visible_child(app.day_selector_stack.get_child_by_name(self.city))

        #name = names[names.index(app.sidebar_stack.get_visible_child_name())]
        #child = not bool(names.index(name))
        #app.sidebar_stack.set_visible_child(app.sidebar_stack.get_child_by_name(names[child]))
        #stack_sidebar_root = app.sidebar_stack.get_child_by_name(names[child])
        #stack_sidebar_root.set_visible_child(stack_sidebar_root.get_child_by_name(self.city_name))


    def back_to_wather(button, stack, app, names):
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        actions.switch_search(button, stack, names)

        names = ['Cities', "Days"]

        app.header_bar.remove(app.day_selector_stack)
        app.header_bar.pack_start(app.city_selector)

        #name = names[names.index(app.sidebar_stack.get_visible_child_name())]
        #child = not bool(names.index(name))
        #app.sidebar_stack.set_visible_child(app.sidebar_stack.get_child_by_name(names[child]))

    def info_label(title, value):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        title_box = Gtk.Box()
        title_widget = Gtk.Label()
        title_widget.set_halign(Gtk.Align.START)
        title_widget.set_css_classes(['font_light'])
        title_widget.set_text(title)
        data_widget = Gtk.Label.new(value)
        data_widget.set_wrap(True)
        title_box.append(title_widget)
        title_box.set_size_request(130, -1)
        box.append(title_box)
        box.append(data_widget)
        box.set_halign(Gtk.Align.START)
        return box

class alarm_description(Gtk.MessageDialog):
    def __init__(self, button, alerts, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.box.set_margin_start(12)
        self.box.set_margin_end(12)
        self.box.set_margin_top(12)
        self.box.set_margin_bottom(12)

        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_margin_bottom(12)
        self.scrolled.set_margin_end(12)
        self.scrolled.set_margin_start(12)
        self.scrolled.set_vexpand(True)

        self.closeButton = Gtk.Button(label=_("Close"))
        self.closeButton.set_hexpand(False)
        self.closeButton.set_halign(Gtk.Align.END)
        self.closeButton.connect('clicked', self.exit)
        self.closeButton.set_css_classes(['suggested-action'])

        self.box.append(self.scrolled)
        self.box.append(self.closeButton)

        self.set_child(self.box)

        self.inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scrolled.set_child(self.inner_box)

        alert_num = 0

        for alert in alerts:
            tags = ""
            for tag in alert['tags']:
                tags = tags + " " + tag
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            title = Gtk.Label.new(f'{alert["event"]} -{tags}')
            title.set_css_classes(['title-4'])
            title.set_halign(Gtk.Align.START)
            subtitle = Gtk.Label.new(f'{str(converters.convert_timestamp_full(alert["start"]))} - {str(converters.convert_timestamp_full(alert["end"]))}')
            subtitle.set_halign(Gtk.Align.START)

            description = alert['description']
            description_box = Gtk.Label()
            description_box.set_wrap(True)
            description_box.set_margin_top(6)
            description_box.set_markup(description)

            box.append(title)
            box.append(subtitle)
            box.append(description_box)
            box.set_margin_bottom(6)
            box.set_margin_top(6)

            self.inner_box.append(box)
            alert_num = alert_num + 1

        self.show()
        self.set_title(title=f'{_("Alerts")} ({alert_num})')
        self.set_transient_for(app)
        self.set_modal(True)
        self.set_default_size(600, 400)

    def exit(self, button):
        self.close()