from gettext import gettext as _
import gi, os, sys, re, json
from .data import *
from .maps import *
from .page import *
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from urllib.request import urlopen

cities_stack = Gtk.Stack()
toast_overlay = Adw.ToastOverlay.new()

class root(Adw.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        global cities_stack

        # global_variables.set_saved_cities([])

        constants.app = self
        constants.root = cities_stack
        constants.city_page = city_page
        constants.toast_overlay = toast_overlay

        if len(global_variables.get_saved_cities()) == 0:
            url = 'http://ipinfo.io/json'
            response = urlopen(url)
            data = json.load(response)
            response = data['city']
            city = search_city.get_search_result(None, None, response, 'first_opening')
            global_variables.set_saved_cities([city])

        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # self.maps_page = maps_page(self, global_variables.get_saved_cities()[global_variables.get_default_city()])

        self.root_stack = Gtk.Stack()
        self.root_stack.add_titled(cities_stack, _('Weather'), _('Weather'))
        # self.root_stack.add_titled(self.maps_page, _('Maps'), _('Maps'))
        self.root_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.title = ('')
        self.side_title = _("Locations")
        self.title_wiget = Gtk.Label()
        # self.title_wiget.set_stack(self.root_stack)

        self.side_title_widget = Gtk.Label(label=self.side_title)
        self.side_title_widget.set_css_classes(['font_app_title'])

        # USE SIDEBAR WHEN CRASH BUG IS FIXED
        #self.sidebar_button = Gtk.Button.new_from_icon_name('sidebar-show-symbolic')
        #self.sidebar_button.connect('clicked', actions.show_hide_sidebar, self)

        # COMMENT THIS TO USE SIDEBAR
        self.city_selector = Gtk.ComboBoxText.new()

        self.day_selector_stack = Gtk.Stack()
        self.day_selector_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.refresh_button = Gtk.Button.new_from_icon_name('view-refresh-symbolic')
        self.refresh_button.connect('clicked', actions.refresh_weather, self, cities_stack)

        self.menu_button = elements.menu_button()

        # --- headerbar ---
        self.header_bar = Adw.HeaderBar()
        self.header_bar.set_css_classes(['flat'])
        self.header_bar.set_title_widget(self.title_wiget)
        
        # INVERT THESE TWO TO USE SIDEBAR
        #self.header_bar.pack_start(self.sidebar_button)
        self.header_bar.pack_start(self.city_selector)

        self.header_bar.pack_end(self.menu_button)
        self.header_bar.pack_end(self.refresh_button)

        self.root.append(self.header_bar)

        # --- cities stack ---
        cities_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        cities_stack.add_css_class(css_class='flat')

        # UNCOMMENT TO USE SIDEBAR
        # --- sidebar ---
        # headerbar
        #self.side_header_bar = Adw.HeaderBar()
        #self.side_header_bar.set_css_classes(['flatitle_wigett'])
        #self.side_header_bar.set_title_widget(self.side_title_widget)
        # scrolled window
        #self.sidebar = Gtk.ScrolledWindow()
        # root box
        #self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        #self.sidebar_stack = Gtk.Stack()
        #self.forecast_stacks_container = Gtk.Stack()
        #self.sidebar_stack.add_named(self.sidebar_box, 'Cities')
        #self.sidebar_stack.add_named(self.forecast_stacks_container, 'Days')
        #self.sidebar_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        #self.sidebar.set_child(self.sidebar_stack)
        #self.side_pane = Adw.OverlaySplitView()
        #self.side_pane.set_collapsed(False)
        #self.side_pane.set_max_sidebar_width(250)
        #self.page_switcher = Gtk.StackSidebar.new()
        #self.page_switcher.set_stack(stack=cities_stack)
        #self.page_switcher.set_vexpand(True)

        #self.sidebar_box.append(self.side_header_bar)
        #self.sidebar_box.append(self.page_switcher)

        self.root.append(self.root_stack)

        toast_overlay.set_child(child=self.root)

        #window handle for moving window
        self.window_handle = Gtk.WindowHandle()
        self.window_handle.set_child(toast_overlay)

        # UNCOMMENT FOR SIDEBAR
        #self.side_pane.set_content(self.window_handle)
        #self.side_pane.set_sidebar(self.sidebar)

        # --- window size --- 
        self.set_default_size(800, 500)
        self.set_size_request(400, 400)
        
        # REPLACE WITH SIDE_PANE FOR SIDEBAR
        self.set_content(self.window_handle)

        # STRUCTURE EXPLAINED
        # self>side_pane>window_handle>toast_overlay>cities_stack

        self.default_loader()
        Forecast.change_city()
        cities_stack.connect("notify::visible-child", self.page_loader)
        self.signal = self.city_selector.connect('changed', actions.switch_city)

    def default_loader(self):
        self.loaded_list = []

        for city in global_variables.get_saved_cities():
            load = False
            if len(global_variables.get_saved_cities())<=global_variables.get_default_city():
                global_variables.set_default_city(0)

            if(city == global_variables.get_saved_cities()[global_variables.get_default_city()]):
                load = True

            self.add_city(load, city)
        self.city_selector.set_active(index_=global_variables.get_default_city())

    def page_loader(self, stack, add):
        city = stack.get_visible_child_name()
        n = global_variables.get_saved_cities().index(city)
        if not self.loaded_list[n]:
            cities_stack.get_visible_child().set_child(city_page.new(self, global_variables.get_saved_cities()[n], True))
            self.loaded_list[n] = True
        else:
            if(global_variables.get_use_dyn_bg()):
                constants.app.set_css_classes(constants.css_classes[global_variables.get_saved_cities().index(city)])

    def add_city(self, load, city):
        name = global_variables.get_city_name(city)
        constants.css_classes.append([])
        constants.days_css_classes.append([])

        self.city_selector.append_text(text=name)
        self.loaded_list.append(load)
        stack_page = city_page.new(self, city, load)

        constants.root.add_titled(child=stack_page, title=name, name=city)

    def delete_city(self, city):
        self.city_selector.remove(global_variables.get_saved_cities().index(city))

class Forecast(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
        self.create_action('refresh', self.refresh_weather, ['<Control>r'])
        self.create_action('preferences', self.show_settings, ['<Control>comma'])
        self.create_action('about', self.show_about)
        self.create_action('quit', self.exit_app, ['<Control>w', '<Control>q'])

    def on_activate(self, app):
        self.win = root(application=app)
        self.win.present()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)
            
   # ----- shows preferences window ----- #
    def show_settings(self, action, param):
        ForecastPreferences()

   # ----- refreshes weather ----- #
    def refresh_weather(self, action, param):
        actions.refresh_weather(None, constants.app, cities_stack)

    # ----- shows about window ------ #
    def show_about(self, action, param):
        dialog = Adw.AboutWindow()
        dialog.set_application_name(_("Forecast"))
        dialog.set_version("1.0.0")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments(_("⛅ Check the weather!.\nUses openweathermap api"))
        dialog.set_website("https://forecast.salanileo.dev")
        dialog.set_developers(["Leonardo Salani"])
        dialog.set_application_icon("dev.salaniLeo.forecast")
        dialog.set_issue_url("https://github.com/SalaniLeo/Forecast/issues")
        dialog.add_acknowledgement_section("Used APIs", ["OpenWeatherMap APIs https://openweathermap.org/api"])
        dialog.present()

    def change_city():
        cities_stack.set_visible_child(cities_stack.get_child_by_name(global_variables.get_saved_cities()[global_variables.get_default_city()]))

    def remove_city(name):
        constants.app.delete_city(name)
        cities_stack.remove(cities_stack.get_child_by_name(name))

    def exit_app(self, action, param):
        self.quit()

class elements():
    def menu_button():
        menu_button_model = Gio.Menu()
        menu_button_model.append(_("Refresh"), "app.refresh")
        menu_button_model.append(_("Preferences"), "app.preferences")
        menu_button_model.append(_("About Forecast"), "app.about")
        menu_button = Gtk.MenuButton.new()
        menu_button.set_margin_end(4)
        menu_button.set_icon_name(icon_name='open-menu-symbolic')
        menu_button.set_menu_model(menu_model=menu_button_model)
        return menu_button

class ForecastPreferences(Adw.PreferencesWindow):
    def __init__(self):
        super().__init__()

        self.set_title(title=_("Preferences"))
        self.connect('close-request', self.do_shutdown)
        self.set_transient_for(constants.app)
        self.show()
        self.valid_api_key = False

        self.add_city_button = Gtk.Button.new_from_icon_name('list-add-symbolic')
        self.add_city_button.set_css_classes(['flat'])

        location_page = Adw.PreferencesPage()
        location_page.set_title(_("Locations"))
        location_page.set_icon_name('mark-location-symbolic')

        forecast_opt_page = Adw.PreferencesPage.new()
        forecast_opt_page.set_title(_("Preferences"))
        forecast_opt_page.set_icon_name('org.gnome.Settings-symbolic')

        self.add(location_page)
        self.add(forecast_opt_page)

        names = ['locations', 'search']
        self.locations_root = Adw.PreferencesGroup()
        self.locations = Adw.PreferencesGroup()

        actions.load_preferences_saved_cities(self, False, 0)

        self.locations_stack = Gtk.Stack()

        self.search_locations = self.search_locations(names)

        self.locations_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.locations_stack.set_parent(self.locations_root)
        self.locations_stack.add_named(self.locations, names[0])
        self.locations_stack.add_named(self.search_locations, names[1])
        self.locations.set_title(_("Locations"))
        self.locations.set_header_suffix(self.add_city_button)

        self.add_city_button.connect('clicked', actions.switch_search, self.locations_stack, names)
        location_page.add(self.locations_root)

        units_group = Adw.PreferencesGroup.new()
        units_group.set_title(_('Units preferences'))
        appearance_group = Adw.PreferencesGroup.new()
        appearance_group.set_title(_('Appearance Preferences'))

        current_units = constants.available_units.index(global_variables.get_current_units())

        units_choice = Gtk.ComboBoxText()
        for text in constants.available_units:
            units_choice.append_text(text=text)
        units_choice.set_active(index_=current_units)
        units_choice.connect('changed', self.change_units)
        units_choice.set_valign(Gtk.Align.CENTER)

        use_temp_units = Adw.ActionRow.new()
        use_temp_units.set_title(_("Temperature units"))
        use_temp_units.set_subtitle(_("Select which units to use"))
        use_temp_units.add_suffix(widget=units_choice)

        units_group.add(use_temp_units)


        current_time_format = constants.time_formats.index(str(global_variables.get_timezone_format()))

        time_format = Gtk.ComboBoxText()
        for text in constants.time_formats:
            time_format.append_text(text=text)
        time_format.set_active(index_=current_time_format)
        time_format.connect('changed', self.change_time_format)
        time_format.set_valign(Gtk.Align.CENTER)

        use_time_format = Adw.ActionRow.new()
        use_time_format.set_title(_("Time format"))
        use_time_format.set_subtitle(_("Select whether to use the 12h or 24h formats"))
        use_time_format.add_suffix(widget=time_format)

        units_group.add(use_time_format)

        use_dyn_bg = Adw.SwitchRow.new()
        use_dyn_bg.set_title(_('Use dynamic background'))
        use_dyn_bg.set_subtitle(_('When on, the background changes based on the weather. Restart needed to apply'))
        use_dyn_bg.set_active(global_variables.get_use_dyn_bg())
        use_dyn_bg.connect('notify::active', self.change_dyn_bg)

        appearance_group.add(use_dyn_bg)

        # -- api key -- #
        api_preferences = Adw.PreferencesGroup.new()
        api_preferences.set_title(_('API Preferences'))

        # creates option for changing api key
        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_editable(True)
        self.api_key_entry.set_valign(Gtk.Align.CENTER)
        self.api_key_entry.set_size_request(175, -1)
        self.api_key_entry.set_width_chars(35)
        self.api_key_entry.set_text(constants.settings.get_string('custom-api-key'))
        self.api_key_entry.connect('changed', self.check_api_key)

        api_key_row = Adw.SwitchRow.new()
        api_key_row.set_title(title=_("Use Personal API Key"))
        api_key_row.set_active(constants.settings.get_boolean('api-key-b'))
        api_key_row.set_subtitle(_("Choose whether to use default API key or personal key"))
        api_key_row.connect('notify::active', self.change_api_key, self.api_key_entry)

        personal_api_key_row = Adw.ActionRow.new()
        personal_api_key_row.set_title(title=_("Personal API Key"))
        personal_api_key_row.add_suffix(widget=self.api_key_entry)
        if not constants.settings.get_boolean('api-key-b'):
            self.api_key_entry.set_css_classes(['error'])

        # adds option rows to option page
        api_preferences.add(child=api_key_row)
        api_preferences.add(child=personal_api_key_row)

        forecast_opt_page.add(group=units_group)
        forecast_opt_page.add(group=appearance_group)
        forecast_opt_page.add(group=api_preferences)

    def check_api_key(self, row):
        if(len(row.get_text()) == 32):
            self.valid_api_key = True

    def change_dyn_bg(self, switch, GBool):
        self.add_toast(Adw.Toast(title=_('Restart needed to apply changes')))
        global_variables.set_use_dyn_bg(switch.get_active())

    def change_units(self, combobox):
        global_variables.set_default_units(combobox.get_active_text())
        self.add_toast(Adw.Toast(title=_('Restart needed to apply changes')))

    def change_time_format(self, combobox):
        global_variables.set_timezone_format(combobox.get_active_text())
        self.add_toast(Adw.Toast(title=_('Restart needed to apply changes')))

    def change_api_key(self, switch, GParamBoolean, api_key_entry):
        if(not switch.get_active()):
            api_key_entry.set_css_classes(['error'])
            api_key_entry.set_text('')
            constants.settings.set_boolean('api-key-b', False)
            constants.settings.set_string('custom-api-key', '')
        else:
            api_key_entry.remove_css_class('error')
            if(self.valid_api_key):
                constants.settings.set_boolean('api-key-b', True)
                self.add_toast(Adw.Toast(title=_('Restart needed to apply changes')))
            else:
                self.add_toast(Adw.Toast(title=_('Api key not valid')))

    def search_locations(self, names):
        self.search_locations = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.search_locations.set_hexpand(True)
        
        back_button = Gtk.Button.new_from_icon_name('process-stop-symbolic')
        back_button.set_hexpand(False)
        back_button.set_css_classes(['flat'])
        back_button.set_halign(Gtk.Align.END)
        back_button.connect('clicked', actions.switch_search, self.locations_stack, names)

        search_city_bar = Gtk.SearchEntry.new()
        search_city_bar.set_hexpand(True)

        name_top_box = Gtk.Box(spacing=12)
        name_top_box.set_vexpand(False)
        name_top_box.set_hexpand(True)
        name_top_box.append(search_city_bar)
        name_top_box.append(back_button)

        name_center_box = Gtk.Box()
        name_center_box.set_vexpand(True)

        name_result_list = Adw.PreferencesGroup()
        name_center_box.append(name_result_list)

        self.query_stack = Gtk.Stack()
        self.query_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.name_query_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.name_query_box.append(name_top_box)
        self.name_query_box.append(name_center_box)

        coords_top_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        lat_input = Gtk.Entry.new()
        lat_input.set_placeholder_text(_("Latitude"))
        lat_input.set_hexpand(True)

        lon_input = Gtk.Entry.new()
        lon_input.set_placeholder_text(_("Longitude"))
        lon_input.set_hexpand(True)

        search_coords_button = Gtk.Button.new_from_icon_name('folder-saved-search-symbolic')
        search_coords_button.set_css_classes(['flat'])

        coords_back_button = Gtk.Button.new_from_icon_name('process-stop-symbolic')
        coords_back_button.set_hexpand(False)
        coords_back_button.set_css_classes(['flat'])
        coords_back_button.set_halign(Gtk.Align.END)
        coords_back_button.connect('clicked', actions.switch_search, self.locations_stack, names)

        coords_top_box.append(lat_input)
        coords_top_box.append(lon_input)
        coords_top_box.append(search_coords_button)
        coords_top_box.append(coords_back_button)

        coords_center_box = Gtk.Box()
        coords_result_list = Adw.PreferencesGroup()
        coords_center_box.append(coords_result_list)

        self.coords_query_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.coords_query_box.append(coords_top_box)
        self.coords_query_box.append(coords_center_box)

        self.query_stack.add_named(self.name_query_box, 'name_query')
        self.query_stack.add_named(self.coords_query_box, 'coord_query')

        bottom_box = Gtk.Box()
        use_coords_button = Gtk.ToggleButton(label=_("Use coordinates"))
        use_coords_button.connect('toggled', actions.switch_search, self.query_stack, ['name_query', 'coord_query'])

        bottom_box.append(use_coords_button)

        self.search_locations.append(self.query_stack)
        self.search_locations.append(bottom_box)
        self.search_locations.set_spacing(12)
        self.search_locations.set_margin_end(12)
        self.search_locations.set_margin_start(12)

        search_coords_button.connect('clicked', search_city.init_thread, coords_result_list, self, [lat_input, lon_input])
        search_city_bar.connect('changed', search_city.init_thread, name_result_list, self, False)

        return self.search_locations

    def remove_city(self, button, n, row, row_list):
        n = row_list.index(row)
        if len(row_list) > 1: 
            loc = (f'{row.get_title()} ({row.get_subtitle()})')
            Forecast.remove_city(loc)
            self.locations.remove(row)
            cities = global_variables.get_saved_cities()
            cities.remove(loc)
            global_variables.set_saved_cities(cities)

    def set_default_city(self, button, n, row_list, default):
        row_list[global_variables.get_default_city()].remove(default)
        global_variables.set_default_city(n)
        row_list[global_variables.get_default_city()].add_suffix(default)
        constants.app.city_selector.set_active(index_=n)
        Forecast.change_city()

    def do_shutdown(self, window):
        if self.valid_api_key:
            constants.settings.set_string('custom-api-key', self.api_key_entry.get_text())

def start(AppID, package):

    css_provider = Gtk.CssProvider()
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    if package == 'flatpak':
        css_provider.load_from_resource('/dev/salaniLeo/forecast/style.css')
    elif package == 'snap':
        css_provider.load_from_resource('/dev/salaniLeo/forecast/style.css')
    elif package == 'debian':
        css_provider.load_from_path(os.path.abspath(os.path.dirname(__file__))+'/data/style.css')
    elif package == None:
        css_provider.load_from_path('data/style.css')

    if package == 'flatpak':
        constants.icon_loc = '/app/share/icons/hicolor/scalable/status/'
    elif package == 'snap':
        constants.icon_loc = os.path.join(os.environ.get('SNAP', ''), 'usr/share/icons/hicolor/scalable/status/')
    elif package == 'debian':
        constants.icon_loc = os.path.abspath(os.path.dirname(__file__))+'/data/status/'
    elif package == None:
        constants.icon_loc = 'data/status/'

    app = Forecast(application_id=AppID)
    app.run(sys.argv)