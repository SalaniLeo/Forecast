import sys
from Forecast.WttrInfo import *
from threading import Thread
import gi
import socket
from gettext import gettext as _
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Gdk, GObject

toast_overlay = Adw.ToastOverlay.new()
meteo = None
application = None
settings = Gio.Settings.new("dev.salaniLeo.forecast")
style_manager = None
saved_locations = settings.get_strv('wthr-locs')

package = None

units = None
available_units = ['Metric System, °C - Km/h', 'Imperial System, °F - mph']


class Application(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        global application, style_manager, units, units_list
        application = self

        # settings.set_strv('wthr-locs', [])

        # city search bar
        self.search_bar = Forecast.search_entry()
        
        # creates headerbar #
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.add_css_class(css_class='flat')
        
        # refresh button
        self.refresh_button = Gtk.Button.new_from_icon_name('view-refresh-symbolic')
        self.refresh_button.set_tooltip_text(_("Refresh"))
        self.refresh_button.connect("clicked", Forecast.refresh)


        self.application = kwargs.get('application')
        self.style_manager = self.application.get_style_manager()

        # creates stack containing the pages #
        self.weather_stack = Gtk.Stack()
        self.weather_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # window handle
        window_handle = Gtk.WindowHandle()

        # sets properties to main page #
        self.set_title(_('Forecast - loading'))
        self.set_default_size(780, 420)
        self.set_titlebar(self.header_bar)
        self.set_child(child=window_handle)

        spinner = Gtk.Spinner.new()
        spinner.set_size_request(100, 100)
        spinner.start()
        self.spinner_box = Gtk.Box()
        self.spinner_box.append(spinner)
        self.spinner_box.set_halign(Gtk.Align.CENTER)
        self.spinner_box.set_valign(Gtk.Align.CENTER)
        self.loading_stack = Gtk.Stack()
        self.loading_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.loading_stack.add_child(self.spinner_box)
        self.loading_stack.add_child(self.weather_stack)
        self.stack_switcher = Gtk.StackSwitcher.new()
        self.stack_switcher.set_stack(stack=self.weather_stack)
        
        
        # self.header_bar.set_title_widget(title_widget=self.stack_switcher)

        window_handle.set_child(toast_overlay)
        toast_overlay.set_child(child=self.loading_stack)

        # menu button #
        self.menu_button_model = Gio.Menu()
        self.menu_button_model.append(_('Refresh'), 'app.refresh')
        self.menu_button_model.append(_('Preferences'), 'app.preferences')
        self.menu_button_model.append(_('About Forecast'), 'app.about')
        self.menu_button = Gtk.MenuButton.new()
        self.menu_button.set_margin_end(4)
        self.menu_button.set_icon_name(icon_name='open-menu-symbolic')
        self.menu_button.set_menu_model(menu_model=self.menu_button_model)

        self.add_button = Gtk.Button.new_from_icon_name('list-add-symbolic')
        self.add_button.connect('clicked', search_page, self, False)

        self.toast_overlay = toast_overlay

        internet = self.check_connection()

        # starts the weather app
        if len(saved_locations) > 0 and internet:
            self.start_application()
        elif len(saved_locations) == 0:
            self.gotoFirstPage()
        elif internet == False:
            self.no_network_page()

    def gotoFirstPage(self, first=True):
        search_page(None, self, first)

    def create_toast(self, text):
        toast = Adw.Toast()
        toast.set_title(text)
        toast_overlay.add_toast(toast)

    # ---- if everything is ok the application gets started correctly via this def ---- #
    def start_application(self):
        wttr_thrd = Thread(target=main_page, args=(None, self, None, package))
        wttr_thrd.start()

        # global_info_thrd = Thread(target=global_weather, args=(None, main_window))
        # global_info_thrd.start()

    def add_city(button, active, main_window, name):
        if name is None:
            main_page(None, main_window, name, package)
            
    def no_network_page(self):
        no_ntwrk_box = Gtk.Box()
        
        no_ntwrk_status = Adw.StatusPage.new()
        no_ntwrk_status.set_hexpand(True)
        no_ntwrk_status.set_title(_("No internet connection"))
        # no_ntwrk_status.set_description(description='No AppImage files are inside the library' +    str(error))
        no_ntwrk_status.set_icon_name('network-no-route-symbolic')
        application.set_title(_('Forecast - No Internet Connection'))

        no_ntwrk_box.append(no_ntwrk_status)
        no_ntwrk_box.set_hexpand(True)

        self.loading_stack.add_child(no_ntwrk_box)
        self.loading_stack.set_visible_child(no_ntwrk_box)

    def check_connection(self):
        try:
            socket.create_connection(("1.1.1.1", 53))
            return True
        except OSError:
            pass
        return False


class Forecast(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect('activate', self.on_activate)
        self.create_action('refresh', self.refresh, ['<Control>r'])
        self.create_action('preferences', self.show_preferences, ['<Control>comma'])
        self.create_action('about', self.show_about)
        self.create_action('quit', self.exit_app, ['<Control>w', '<Control>q'])

    # ---- action to perform on startup ---- #
    def on_activate(self, app):  
        self.win = Application(application=app)
        self.win.present()

    # ---- creates an action for the application --- #
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)

    # ----- refreshes meteo ----- #
    def refresh(button=None, self=None, args=None):
        internet = application.check_connection()
        
        if internet == True:
            main_page.refresh()
        else:
            application.create_toast(_('No internet connection'))
            application.no_network_page()

    def rm_loc(button, row, location, self):
        global saved_locations
        active = settings.get_int('selected-city')-1
        settings.set_int('selected-city', active)
        saved_locations.remove(location)
        settings.set_strv('wthr-locs', saved_locations)
        load_locations(True, active, application)
        self.locations.remove(row)

    # ----- shows about window ------ #
    def show_about(self, action, param):
        dialog = Adw.AboutWindow()
        dialog.set_transient_for(application)
        dialog.set_application_name(_("Forecast"))
        dialog.set_version("0.2.2")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments(_("Weather app for Linux"))
        dialog.set_website("https://github.com/SalaniLeo/Forecast")
        dialog.set_developers(["Leonardo Salani"])
        dialog.set_application_icon("dev.salaniLeo.Forecast")
        # TRANSLATORS: eg. 'Translator Name <your.email@domain.com>' or 'Translator Name https://website.example'
        dialog.set_translator_credits(_("translator-credits"))
        dialog.present()

   # ----- shows preferences window ----- #
    def show_preferences(self, action, param):
        adw_preferences_window = ForecastPreferences(application)
        adw_preferences_window.show()

    def search_entry():
        completion_model = Gtk.ListStore.new([GObject.TYPE_INT, GObject.TYPE_STRING])
        completion = Gtk.EntryCompletion.new()
        completion.set_model(model=completion_model)
        completion.set_text_column(column=1)

        # city search bar
        search_bar = Gtk.Entry()
        search_bar.set_valign(Gtk.Align.START)
        search_bar.set_hexpand(True)
        search_bar.set_completion(completion=completion)
        search_bar.set_placeholder_text(_('Search a city'))
        search_bar.connect('changed', get_cities, completion_model, search_bar)
        search_bar.connect('activate', search_page.add_loc, search_bar)
            
        return search_bar

    def exit_app(self, action, param):
        self.quit()


# ------- first page that shows when app is opened for the first time ------- #
class search_page(Gtk.Box):
    def __init__(self, button, window, first, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if first:

            # welcome title 
            self.title = Gtk.Label(label=_('Welcome to Forecast!\n'))
            self.title.set_justify(Gtk.Justification.CENTER)
            self.title.set_valign(Gtk.Align.START)
            self.title.set_css_classes(['bold'])
            
            self.subtitle = Gtk.Label(label=_('Search a city'))
            self.subtitle.set_justify(Gtk.Justification.CENTER)
            self.subtitle.set_valign(Gtk.Align.START)
            self.subtitle.set_css_classes(['text_medium'])

            if package == 'flatpak':
                self.title_image = Gtk.Image.new_from_resource('/app/share/icons/hicolor/symbolic/apps/dev.salaniLeo.forecast-symbolic.svg')
            elif package == None:
                self.title_image = Gtk.Image.new_from_file('share/icons/hicolor/scalable/apps/dev.salaniLeo.forecast.svg')

            self.title_image.set_pixel_size(175)
            self.title_image.set_vexpand(True)
            self.title_image.set_valign(Gtk.Align.CENTER)

            self.title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.title_box.append(self.title)
            self.title_box.append(self.subtitle)
            self.title_box.append(self.title_image)
            self.title_box.set_vexpand(True)

            # sets main grid properties and childs
            self.set_orientation(Gtk.Orientation.VERTICAL)
            self.append(Forecast.search_entry())
            self.append(self.title_box)
            self.set_margin_start(50)
            self.set_margin_end(50)
            self.set_margin_top(24)
            self.set_margin_bottom(24)
            self.set_spacing(48)

            # sets title and adds self as app child
            window.set_title(_('Forecast'))
            window.loading_stack.add_child(self)
            if saved_locations is not None:
                window.loading_stack.set_visible_child(self)
                
        else:
            if window.add_button.get_icon_name() == 'edit-undo-symbolic':
                self.close_search()
            else:
                self.open_search()

    def close_search(self):
        application.header_bar.remove(application.header_bar.get_title_widget())
        application.add_button.set_icon_name('list-add-symbolic')  
        application.header_bar.set_title_widget(application.stack_switcher)

    def open_search(self):
        application.header_bar.set_title_widget(application.search_bar)
        application.add_button.set_icon_name('edit-undo-symbolic')

    def add_loc(self, entry):
        global saved_locations
        first_time = False
        if len(saved_locations) == 0:
            first_time = True
        add_city(entry.get_text(), application, first_time, search_page)
        saved_locations.append(entry.get_text())
        # application.add_city(self, application, entry.get_text())

# -------- preferences class ---------- #
class ForecastPreferences(Adw.PreferencesWindow):
    def __init__(self, parent,  **kwargs):
        super().__init__(**kwargs)   

        self.set_title(title=_('Preferences'))
        self.set_transient_for(parent)
        self.connect('close-request', self.do_shutdown)
        self.locations_changed = False

        location_page = Adw.PreferencesPage()
        location_page.set_title(_("Locations"))
        location_page.set_icon_name('mark-location-symbolic')
        self.add(location_page)

        forecast_opt_page = Adw.PreferencesPage.new()
        forecast_opt_page.set_title(_("Preferences"))
        forecast_opt_page.set_icon_name('org.gnome.Settings-symbolic')
        self.add(page=forecast_opt_page)

        self.locations = Adw.PreferencesGroup()
        self.locations.set_title(_("Locations"))
        location_page.add(self.locations)

        for loc in settings.get_strv('wthr-locs'):
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
            location.add_suffix(b)
            location.connect("activated", self.set_default_location)
            self.locations.add(location)

            b.connect('clicked', Forecast.rm_loc, location, loc, self)


        # -- background radient -- #
        application_preferences = Adw.PreferencesGroup.new()
        application_preferences.set_title(_('App Preferences'))
        appearance_preferences = Adw.PreferencesGroup.new()
        appearance_preferences.set_title(_('Appearance Preferences'))
        
        use_gradient_bg_switch = self.opt_switch(None, "gradient-bg")
        use_gradient_bg_row = Adw.ActionRow.new()
        use_gradient_bg_row.set_title(title=_('Use Gradient as Background'))
        use_gradient_bg_row.set_subtitle(_("Applies a gradient based on current weather and time. Requires restart to disable"))
        use_gradient_bg_row.add_suffix(widget=use_gradient_bg_switch)


        use_glassy_sw = self.opt_switch(None, "use-glassy")
        use_glassy_look = Adw.ActionRow.new()
        use_glassy_look.set_title(title=_('Use glassy background look'))
        use_glassy_look.set_subtitle(_("Applies a glass-like background to all elements"))
        use_glassy_look.add_suffix(widget=use_glassy_sw)
        use_glassy_sw = self.opt_switch(None, "enhance-contrast")

        enhance_contrast = Adw.ActionRow.new()
        enhance_contrast.set_title(title=_('Use dark text on dark background'))
        enhance_contrast.set_subtitle(_("Chenges the text color from light to dark on light backgrounds"))
        enhance_contrast.add_suffix(widget=use_glassy_sw)

        # -- units -- #
        units = settings.get_string('units')
        if units == available_units[0]:
            units_list = 0
        elif units == available_units[1]:
            units_list = 1

        units_choice = Gtk.ComboBoxText()
        for text in available_units:
            units_choice.append_text(text=text)
        units_choice.set_active(index_=units_list)
        units_choice.connect('changed', self.change_unit)
        units_choice.set_valign(Gtk.Align.CENTER)

        units_row = Adw.ActionRow.new()
        units_row.set_title(title=_('Units'))
        units_row.set_subtitle(_("Select which unit of measurement to use"))
        units_row.add_suffix(widget=units_choice)

        # -- api key -- #
        api_preferences = Adw.PreferencesGroup.new()
        api_preferences.set_title(_('API Preferences'))

        # creates option for changing api key
        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_editable(True)
        self.api_key_entry.set_valign(Gtk.Align.CENTER)
        self.api_key_entry.set_size_request(175, -1)
        self.api_key_entry.set_width_chars(35)
        self.api_key_entry.set_text(settings.get_string("api-key-s"))
        api_key_switch = self.opt_switch(self.api_key_entry, "api-key-b")

        api_key_row = Adw.ActionRow.new()
        api_key_row.set_title(title=_("Use Personal API Key"))
        api_key_row.set_subtitle(_("Choose whether to use default API key or personal key"))
        api_key_row.add_suffix(widget=api_key_switch)

        personal_api_key_row = Adw.ActionRow.new()
        personal_api_key_row.set_title(title=_("Personal API Key"))
        personal_api_key_row.add_suffix(widget=self.api_key_entry)

        # adds option rows to option page
        application_preferences.add(child=units_row)
        api_preferences.add(child=api_key_row)
        api_preferences.add(child=personal_api_key_row)

        appearance_preferences.add(child=use_gradient_bg_row)
        appearance_preferences.add(child=use_glassy_look)
        appearance_preferences.add(child=enhance_contrast)


        forecast_opt_page.add(group=application_preferences)
        forecast_opt_page.add(group=appearance_preferences)
        forecast_opt_page.add(group=api_preferences)
        
    def set_default_location(self, row):
            active = f'{row.get_title()} ({row.get_subtitle()})'
            locs = settings.get_strv('wthr-locs')
            activeNum = locs.index(active)
            settings.set_int('selected-city', activeNum)
            switch_city(activeNum)
            application.saved_loc_box.set_active(index_=activeNum)

    def change_unit(self, combobox):
        global units 
        units = combobox.get_active_text()
        self.saveString(None, units, 'units')
        main_page.refresh(change_units='True')

    # ---- creates a switch for an option ---- #
    def opt_switch(self, entry, option):
        switch = Gtk.Switch()                                   #
        switch.set_valign(align=Gtk.Align.CENTER)               # creates switch
        switch.set_active(settings.get_boolean(option))         #
        switch.connect('notify::active', self.saveOpt, option)  # connects to save option when clicked

        # -- if option is gradient bg connects switch to apply a gradient -- #
        if option == "gradient-bg":
            switch.connect('state-set', style.apply_bg)

        if option == 'use-glassy':
            switch.connect('state-set', style.apply_glassy)

        if option == 'enhance-contrast':
            switch.connect('state-set', style.apply_enhanced_text)

        # -- if option is api key switch state sets colors based on state -- #
        if option == "api-key-b":
            if not switch.get_state():
                entry.add_css_class(css_class='error') # adds red color to entry
                entry.set_editable(False)              # sets entry to uneditable
            switch.connect('state-set', self.change_state, entry) # connects to changing state of entry based on switch state

        return switch

    # ---- saves whatever boolean is asked to be saved in gschema settings ---- #
    def saveOpt(self, switch, GParamBoolean, option):
        global settings
        settings.set_boolean(option, switch.get_state())

    # ---- saves whatever string is asked to be saved in gschema settings ---- #
    def saveString(self, entry, string, option):
        global settings
        settings.set_string(option, string)

    # ---- sets given entry to red if a switch is turned off ---- #
    def change_state(opt, switch, active, entry):
        global api_key
        if not active:
            entry.set_editable(False)                   # sets entry to off
            entry.add_css_class(css_class='error')      #
        else:
            api_key = entry.get_text()                  #
            entry.remove_css_class(css_class='error')   # sets entry to on

    # ---- actions to perform before closing preferences window ---- #
    def do_shutdown(self, quit):
        if self.api_key_entry.get_text() is not None:       # saves api key to gsettings
            self.saveString(self.api_key_entry, self.api_key_entry.get_text(), "api-key-s")
        if self.locations_changed:
            Forecast.refresh()

def start(AppId, type):
    global package
    package = type

    css_provider = Gtk.CssProvider()

    if package == 'flatpak':
        css_provider.load_from_resource('/dev/salaniLeo/forecast/style.css')
    elif package == 'appimage':
        css_provider.load_from_path('data/style.css')
    elif package == None:
        css_provider.load_from_path('data/style.css')
        
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    app = Forecast(application_id=AppId)
    app.run(sys.argv)
