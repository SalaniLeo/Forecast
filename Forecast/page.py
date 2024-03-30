import gi, cairo, threading
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gsk, GLib
from gettext import gettext as _
from .data import *
from .page import *
from .style import *

timezone = 0
days_container_stack = Gtk.Stack()

class city_page(Gtk.Stack):
    def __init__(self, app, city):
        super().__init__()
        global timezone
        
        self.root = Gtk.Box()

        coords_raw = city[city.find("(")+1:city.find(")")] # gets coords of new city
        lat = coords_raw.split("; ")[0]  # gets latitude of new city  
        lon = coords_raw.split("; ")[1] # gets longitude of new city

        meteo = request.weather(lat, lon)
        pollution = request.pollution(lat, lon)

        self.city_name   = str(city.split('-')[0])

        timezone    = str(meteo['timezone_offset']/3600)
        time_raw  = meteo['current']['dt']
        day_name    = str(converters.convert_day(meteo['current']['dt']))
        icon        = meteo['current']['weather'][0]['icon']
        conditions  = str(meteo['current']['weather'][0]['description'])
        temperature = str(round(meteo['current']['temp'], 1))
        feels_like  = str(round(meteo['current']['feels_like']))

        now = meteo['current']
        daily = meteo['daily']
        hourly = meteo['hourly']

        alerts = None
        try:
            alerts = meteo["alerts"]
        except:
            None

        local_time = converters.convert_time_format(time_raw, timezone)

        title_box = components.title_box(icon,conditions,temperature,local_time,day_name, feels_like)
        now_conditions = components.now_conditions(now, self, app)
        daily_forecast_box = components.daily_forecast(daily, self, app)
        hourly_forecast_box = components.hourly_forecast(hourly)
        current_pollution_box = components.current_pollution(pollution)

        accurate_daily_forecast_stack = components.accurate_daily_forecast(daily, self, app)

        days_stack_root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        days_stack_title_widget = Gtk.Label.new(_("Days"))
        days_stack_title_widget.set_margin_top(12)
        days_stack_title_widget.set_margin_bottom(12)
        days_stack_title_widget.set_css_classes(['font_app_title'])

        days_stack_sidebar = Gtk.StackSidebar()
        days_stack_sidebar.set_stack(accurate_daily_forecast_stack)
        days_stack_sidebar.set_vexpand(True)

        days_stack_root_box.append(days_stack_title_widget)
        days_stack_root_box.append(days_stack_sidebar)

        app.forecast_stacks_container.add_named(days_stack_root_box, self.city_name)

        # -- adds wather and forecast pages -- 
        self.add_named(self.root, _("Weather"))
        self.add_named(accurate_daily_forecast_stack, _("Forecast"))

        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)

        # -- root container for page --
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        base_box.set_hexpand(True)

        # -- left container --
        top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        top_box.append(title_box)
        top_box.set_vexpand(False)
        top_box.set_hexpand(True)
        top_box.set_spacing(6)
        # top_box.set_margin_bottom(12)
        top_box.set_size_request(-1, 125)

        alert_box = Gtk.Box()
        if(alerts is not None):
            alert_box = components.alarm_box(alerts, app)
            alert_box.set_halign(Gtk.Align.CENTER)

            top_box.append(alert_box)

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        center_box.append(hourly_forecast_box)
        center_box.append(daily_forecast_box)
        center_box.append(current_pollution_box)
        center_box.append(now_conditions)

        base_box.append(top_box)
        base_box.append(center_box)

        self.root.append(base_box)
        self.root.set_vexpand(True)
        self.root.set_hexpand(True)
        self.root.set_orientation(Gtk.Orientation.VERTICAL)

        align_alerts = Adw.Breakpoint() # TODO
        align_alerts.add_setter(alert_box, "halign", Gtk.Align.START);
        align_alerts.add_setter(top_box, "orientation", Gtk.Orientation.VERTICAL)
        align_alerts.set_condition(Adw.BreakpointCondition.new_length(Adw.BreakpointConditionLengthType.MAX_WIDTH, constants.align_breakpoint, Adw.LengthUnit.SP))
        app.add_breakpoint(align_alerts)

        repeat_align = Adw.Breakpoint() # TODO
        repeat_align.add_setter(alert_box, "halign", Gtk.Align.START);
        repeat_align.add_setter(top_box, "orientation", Gtk.Orientation.VERTICAL)
        repeat_align.add_setter(app.side_pane, "collapsed", True);
        repeat_align.set_condition(Adw.BreakpointCondition.new_length(Adw.BreakpointConditionLengthType.MAX_WIDTH, constants.sidebar_breakpoint, Adw.LengthUnit.SP))
        app.add_breakpoint(repeat_align)

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
            box.set_visible(True)
        return root

    def fill_weather(box, app, city, spinner):
        box.append(city_page(app, city))
        spinner.set_visible_child(spinner.get_child_by_name('weather'))


class components(city_page):
    def title_box(icon, conditions, temperature, local_time, day_name, feels_like):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # -- icon --
        icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_widget = Gtk.Image()
        app_style.forecast_icon(icon, 100, icon_widget, constants.icon_loc)
        
        # -- title container -- #
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # -- title --
        title_widget = Gtk.Label.new(conditions)
        title_widget.set_halign(Gtk.Align.START)
        title_widget.set_css_classes(['font_big'])
        # -- subtitle --
        subtitle_box = Gtk.Box()
        subtitle_widget = Gtk.Label.new(f'{temperature}{global_variables.get_temperature_units()}')
        subtitle_widget.set_halign(Gtk.Align.START)
        subtitle_widget.set_css_classes(['font_medium'])
        feels_like_subtitle_widget = Gtk.Label.new(f'- {_("Feels like")} {feels_like}{global_variables.get_temperature_units()}')
        feels_like_subtitle_widget.set_css_classes(['font_light', 'font_bold'])
        feels_like_subtitle_widget.set_valign(Gtk.Align.CENTER)
        subtitle_box.append(subtitle_widget)
        subtitle_box.append(feels_like_subtitle_widget)
        # -- container for icon and title container --
        icon_box.append(icon_widget)
        icon_box.append(title_box)
        icon_box.set_vexpand(False)

        # -- local time label --
        city_time = Gtk.Label.new(f'{day_name}, {local_time}')
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

    def alarm_box(alerts, app):
        base_box = Gtk.Box()

        for alert in alerts:
            title = Gtk.Label(label=_("Alerts"))
            title.set_halign(Gtk.Align.START)
            title.set_margin_bottom(6)
            title.set_css_classes(['font_medium'])
            event = str(alert['event'])
            start = str(converters.convert_timestamp(alert['start']))
            end   = str(converters.convert_timestamp(alert['end']))
            description = str(alert['description'])
            sender = str(alert['sender_name'])

            event_icon = Gtk.Image.new_from_icon_name('dialog-warning-symbolic')

            event_widget = Gtk.Label()
            event_widget.set_text(event)
            event_widget.set_css_classes(['font_bold'])

            event_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            event_box.append(event_icon)
            event_box.append(event_widget)
            event_box.set_spacing(6)

            start_widget = Gtk.Label(label=f'{_("Start:")} {start}')
            start_widget.set_halign(Gtk.Align.START)
            end_widget = Gtk.Label(label=f'{_("End:")} {end}')
            end_widget.set_halign(Gtk.Align.START)

            duration_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            duration_box.append(start_widget)
            duration_box.append(end_widget)
            duration_box.set_margin_top(4)
            duration_box.set_margin_start(4)

            button = Gtk.Button()
            button.set_label(_("See description"))
            button.set_css_classes(['flat'])
            button.connect('clicked', alarm_description, description, sender, app)

            top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            top_box.append(title)
            top_box.append(event_box)
            top_box.append(duration_box)
            top_box.append(button)

        base_box.append(top_box)
        base_box.set_vexpand(True)
        base_box.set_hexpand(True)

        return base_box

    def now_conditions(now, self, app):
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        title_widget = Gtk.Label.new(_("Current conditions"))
        title_widget.set_css_classes(['font_medium'])
        title_widget.set_halign(Gtk.Align.START)
        base_box.append(title_widget)
        base_box.set_margin_bottom(6)
        base_box.set_margin_top(20)

        temp  = str(round(now['temp'], 1)) + constants.degrees_unit
        feels_like  = str(round(now['feels_like'], 1)) + constants.degrees_unit
        humidity    = str(now["humidity"])   + "%    "
        wind_speed  = str(now['wind_speed'])      + constants.speed_unit +' '+ constants.wind_dir(now['wind_deg'])
        pressure    = str(now['pressure'])   + ' hPa    '
        Visibility  = '>' + str(now['visibility']/1000) + constants.speed_unit.split('/')[0]
        Sunrise     = str(converters.convert_timestamp(now['sunrise']))
        Sunset      = str(converters.convert_timestamp(now['sunset']))
        cloudiness  = f'{str(round(now["clouds"]))}%'
        # rain_prob   = f'{str(round(now["pop"]*100))}%'
        uv_index    = constants.uv_index(round(now["uvi"]))

        day_temp_widget = components.info_label(_("Temperature"), f'{temp}')
        wind_speed_widget = components.info_label(_("Wind speed"), f'{wind_speed}')
        humidity_widget = components.info_label(_("Humidity"), f'{humidity}')
        cloudiness_widget = components.info_label(_("Cloudiness"), f'{cloudiness}')
        # pop_widget = components.info_label(_("Probability of rain"), f'{rain_prob}')
        uv_index_widget = components.info_label(_("UV Index"), f'{uv_index}  ({str(round(now["uvi"],1))})')

        widgets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        widgets_box.append(day_temp_widget)
        widgets_box.append(wind_speed_widget)
        widgets_box.append(humidity_widget)
        widgets_box.append(cloudiness_widget)
        widgets_box.append(uv_index_widget)

        base_box.append(widgets_box)
        return base_box

    def hourly_forecast(hourly):
        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title_widget = Gtk.Box()
        title_widget.append(Gtk.Label.new(_("24 Hours forecast")))
        title_widget.set_css_classes(['font_medium'])
        hourly_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_margin_bottom(12)
        scrolled_window.set_child(hourly_box)
        # scrolled_window.set_hexpand(True)
        scrolled_window.set_min_content_height(100)

        base_box.append(title_widget)
        base_box.append(scrolled_window)

        i = 0
        for hour in hourly:
            if i <= 24:
                hour_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

                time_raw = hour['dt']
                temp = hour['temp']
                icon = hour['weather'][0]['icon']

                time = converters.convert_time_format(time_raw, timezone)

                time_widget = Gtk.Label.new(time)
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

        base_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        base_box.append(title_box)
        base_box.set_spacing(12)
        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        base_box.append(top_box)
        base_box.append(center_box)
        base_box.set_valign(Gtk.Align.START)

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

                max_min.append(max_temp)
                max_min.append(min_temp)
                if max_temp > overall_max: overall_max = max_temp
                if min_temp < overall_min: overall_min = min_temp

                day_box = components.temp_graph_box(day_name, icon, max_temp, min_temp, max_min)

                top_box.append(day_box)

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
        temp_graph.set_draw_func(app_style.draw_forecast_temps, max_min, max_temp, min_temp)
        temp_graph.set_hexpand(True)

        temp_box = Gtk.Box()
        temp_box.append(temp_graph)
        temp_box.set_size_request(80, -1)
        temp_box.set_margin_start(10)
        temp_box.set_margin_end(10)

        max_min_box.append(min_widget)
        max_min_box.append(temp_box)
        max_min_box.append(max_widget)
        max_min_box.set_hexpand(False)
        max_min_box.set_size_request(100,10)

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

            overall_text_widget = Gtk.Label.new(_("AQI"))
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
            co_text_widget = Gtk.Label.new(_("CO"))
            co_text_widget.set_halign(Gtk.Align.START)
            data_box.append(co_widget)
            text_box.append(co_text_widget)

            no_widget = Gtk.Label.new(str(index['components']['no']))
            no_widget.set_halign(Gtk.Align.START)
            no_text_widget = Gtk.Label.new(_("NO"))
            no_text_widget.set_halign(Gtk.Align.START)
            data_box.append(no_widget)
            text_box.append(no_text_widget)

            no2_widget = Gtk.Label.new(str(index['components']['no2']))
            no2_widget.set_halign(Gtk.Align.START)
            no2_text_widget = Gtk.Label.new(_("NO2"))
            no2_text_widget.set_halign(Gtk.Align.START)
            data_box.append(no2_widget)
            text_box.append(no2_text_widget)

            o3_widget = Gtk.Label.new(str(index['components']['o3']))
            o3_widget.set_halign(Gtk.Align.START)
            o3_text_widget = Gtk.Label.new(_("O3"))
            o3_text_widget.set_halign(Gtk.Align.START)
            data_box.append(o3_widget)
            text_box.append(o3_text_widget)

            so2_widget = Gtk.Label.new(str(index['components']['so2']))
            so2_widget.set_halign(Gtk.Align.START)
            so2_text_widget = Gtk.Label.new(_("SO2"))
            so2_text_widget.set_halign(Gtk.Align.START)
            data_box.append(so2_widget)
            text_box.append(so2_text_widget)

            pm25_widget = Gtk.Label.new(str(index['components']['pm2_5']))
            pm25_widget.set_halign(Gtk.Align.START)
            pm25_text_widget = Gtk.Label.new(_("pm 2.5"))
            pm25_text_widget.set_halign(Gtk.Align.START)
            data_box.append(pm25_widget)
            text_box.append(pm25_text_widget)

            pm10widget = Gtk.Label.new(str(index['components']['pm10']))
            pm10widget.set_halign(Gtk.Align.START)
            pm10_text_widget = Gtk.Label.new(_("pm 10"))
            pm10_text_widget.set_halign(Gtk.Align.START)
            data_box.append(pm10widget)
            text_box.append(pm10_text_widget)

            nh3_widget = Gtk.Label.new(str(index['components']['nh3']))
            nh3_widget.set_halign(Gtk.Align.START)
            nh3_text_widget = Gtk.Label.new(_("NH3"))
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
        i = 0
        boxes = []
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

                center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
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
                root.add_titled(base_box, str(i), day_name)


                day_temps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                day_temps_box.set_hexpand(True)
                day_temps_box.set_vexpand(False)

                night_temp = day['temp']['night']
                evening_temp = day['temp']['eve']
                morning_temp = day['temp']['morn']
                afternoon_temp = day['temp']['day']

                night_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                night_temp_label = Gtk.Label.new(f'{_("Night")}')
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
                evening_temp_label = Gtk.Label.new(f'{_("Evening")}')
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
                morning_temp_label = Gtk.Label.new(f'{_("Morning")}')
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
                afternoon_temp_label = Gtk.Label.new(f'{_("Afternoon")}')
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
                humidity = components.info_label(_("Humidity"), f'{str(round(day["humidity"]))}%')
                cloudiness = components.info_label(_("Cloudiness"), f'{str(round(day["clouds"]))}%')
                pop = components.info_label(_("Probability of rain"), f'{str(round(day["pop"]*100))}%')
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
                sunrise_sunset_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                sunrise_sunset_box.append(sunrise_box)
                sunrise_sunset_box.append(sunset_box)

                center_center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                center_center_box.append(sun_title)
                center_center_box.append(sunrise_sunset_box)

                center_top_box.append(current_conditions_box)
                center_top_box.append(day_temps_box)

                center_box.append(center_top_box)
                center_box.append(center_center_box)

                base_box.append(top_box)
                base_box.append(center_box)
            i += 1

        awd_breakpoint = Adw.Breakpoint() # TODO
        for each in boxes:
            awd_breakpoint.add_setter(each, 'orientation', Gtk.Orientation.HORIZONTAL)
        awd_breakpoint.set_condition(Adw.BreakpointCondition.new_length(Adw.BreakpointConditionLengthType.MIN_WIDTH, constants.sidebar_breakpoint, Adw.LengthUnit.SP))
        app.add_breakpoint(awd_breakpoint)

        return root

    def go_to_weather(button, self, app, names):
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        actions.switch_search(button, self, names)

        names = ['Cities', "Days"]

        name = names[names.index(app.sidebar_stack.get_visible_child_name())]
        child = not bool(names.index(name))
        app.sidebar_stack.set_visible_child(app.sidebar_stack.get_child_by_name(names[child]))
        stack_sidebar_root = app.sidebar_stack.get_child_by_name(names[child])
        stack_sidebar_root.set_visible_child(stack_sidebar_root.get_child_by_name(self.city_name))

    def back_to_wather(button, stack, app, names):
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        actions.switch_search(button, stack, names)

        names = ['Cities', "Days"]

        name = names[names.index(app.sidebar_stack.get_visible_child_name())]
        child = not bool(names.index(name))
        app.sidebar_stack.set_visible_child(app.sidebar_stack.get_child_by_name(names[child]))

    def info_label(title, value):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        title_widget = Gtk.Label.new(title)
        title_widget.set_css_classes(['font_light'])
        data_widget = Gtk.Label.new(value)
        data_widget.set_wrap(True)
        box.append(title_widget)
        box.append(data_widget)
        return box

class alarm_description(Gtk.MessageDialog):
    def __init__(self, button, description, sender, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(500,225)
        self.set_title(title=sender)
        self.set_transient_for(app)
        self.set_modal(True)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_margin_bottom(12)
        self.scrolled.set_margin_end(12)
        self.scrolled.set_margin_start(12)
        self.scrolled.set_vexpand(True)

        self.closeButton = Gtk.Button(label=_("Close"))
        self.closeButton.set_hexpand(True)
        self.closeButton.set_size_request(-1, 50)
        self.closeButton.connect('clicked', self.exit)

        self.box.append(self.scrolled)
        self.box.append(self.closeButton)

        self.set_child(self.box)

        self.alert = Gtk.Label.new(description)
        self.alert.set_wrap(True)
        self.scrolled.set_child(self.alert)
        self.show()

    def exit(self, button):
        self.close()