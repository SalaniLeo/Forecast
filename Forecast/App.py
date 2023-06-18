import sys
from Forecast.WttrInfo import *
from threading import Thread
import gi
import os
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, Gdk

toast_overlay = Adw.ToastOverlay.new()
meteo = None
application = None
settings = Gio.Settings.new("dev.salaniLeo.forecast")
style_manager = None
saved_locations = settings.get_strv('wthr-locs')
# saved_locations = []

flatpak = None

css_provider = Gtk.CssProvider()

units = None
available_units = ['Metric System, °C - Km/h', 'Imperial System, °F - mph']


class Application(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # settings.set_strv('wthr-locs', [])

        global application
        global style_manager
        global units
        global units_list
        application = self

        # creates headerbar #
        self.header_bar = Gtk.HeaderBar()

        self.application = kwargs.get('application')
        self.style_manager = self.application.get_style_manager()


        # sets properties to main page #
        self.set_title('Forecast - loading')
        self.set_default_size(850, 390)        

        # creates stack containing the pages #
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        if len(saved_locations) == 0:
            self.first_page = search_page(None, self, True)

        # menu button #
        self.menu_button_model = Gio.Menu()
        self.menu_button_model.append('Preferences', 'app.preferences')
        self.menu_button_model.append('About', 'app.about')
        self.menu_button = Gtk.MenuButton.new()
        self.menu_button.set_margin_end(4)
        self.menu_button.set_icon_name(icon_name='open-menu-symbolic')
        self.menu_button.set_menu_model(menu_model=self.menu_button_model)

        self.add_button = Gtk.Button.new_from_icon_name('list-add-symbolic')
        self.add_button.connect('clicked', search_page, self, False)

        # refresh button
        self.refresh_button = Gtk.Button.new_from_icon_name('view-refresh-symbolic')
        self.refresh_button.connect("clicked", Forecast.refresh, self)


        # header bar
        self.header_bar.add_css_class(css_class='flat')

        self.set_titlebar(self.header_bar)

        # window handle
        window_handle = Gtk.WindowHandle()
        self.set_child(child=window_handle)

        # adds toast_overlay to self #
        window_handle.set_child(toast_overlay)
        toast_overlay.set_child(child=self.stack)

        # starts the weather app
        if len(saved_locations) > 0:
            self.start_application()

    # ---- if everything is ok the application gets started correctly via this def ---- #
    def start_application(main_window):
        # starts main thread
        wttr_thrd = Thread(target=main_page, args=(None, main_window, None, flatpak))
        wttr_thrd.start()

    def add_city(button, active, main_window, name):
        if name is None:
            main_page(None, main_window, name, flatpak, units)



class Forecast(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect('activate', self.on_activate)
        self.create_action('refresh', self.refresh)
        self.create_action('preferences', self.show_preferences)
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
    def refresh(button, self):
        main_page.refresh(None, None, None)

    # ----- shows about window ------ #
    def show_about(self, action, param):
        dialog = Adw.AboutWindow()
        dialog.set_transient_for(application)
        dialog.set_application_name('Forecast')
        dialog.set_version("0.1.1")
        dialog.set_license_type(Gtk.License(Gtk.License.GPL_3_0))
        dialog.set_comments("Meteo app made with GTK")
        dialog.set_website("https://github.com/SalaniLeo/Forecast")
        dialog.set_developers(["Leonardo Salani"])
        dialog.set_application_icon("dev.salaniLeo.Forecast")
        dialog.present()

   # ----- shows preferences window ----- #
    def show_preferences(self, action, param):
        adw_preferences_window = ForecastPreferences(application)
        adw_preferences_window.show()

    def exit_app(self, action, param):
        self.quit()


# ------- first page that shows when app is opened for the first time ------- #
class search_page(Gtk.Box):
    def __init__(self, button, window, first, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.completion_model = Gtk.ListStore.new([])

        self.completion = Gtk.EntryCompletion.new()
        self.completion.set_model(model=self.completion_model)
        self.completion.set_text_column(column=1)

        # city search bar
        self.search_bar = Gtk.Entry()
        # self.search_bar.set_halign(Gtk.Align.CENTER)
        self.search_bar.set_valign(Gtk.Align.START)
        self.search_bar.set_hexpand(True)
        self.search_bar.set_completion(completion=self.completion)
        self.search_bar.connect('changed', get_cities, self, self.search_bar)

        if first:
            # welcome title 
            self.title = Gtk.Label(label='Welcome to Forecast!\nsearch a city')
            self.title.set_justify(Gtk.Justification.CENTER)
            self.title.set_valign(Gtk.Align.START)
            self.title.set_vexpand(True)
            self.title.set_hexpand(True)
            self.title.set_css_classes(['text_big'])

            # sets main grid properties and childs
            self.set_orientation(Gtk.Orientation.VERTICAL)
            self.append(self.search_bar)
            self.append(self.title)
            self.set_margin_start(50)
            self.set_margin_end(50)
            self.set_margin_top(24)
            self.set_margin_bottom(24)
            self.set_spacing(48)

            # sets title and adds self as app child
            window.set_title('Forecast')
            window.stack.add_child(self)
            if saved_locations is not None:
                window.stack.set_visible_child(self)
            self.search_bar.connect('activate', self.add_loc, window)

        else:
            if window.add_button.get_icon_name() == 'edit-undo-symbolic':
                window.header_bar.remove(window.header_bar.get_title_widget())
                window.add_button.set_icon_name('list-add-symbolic')
            else:
                window.header_bar.set_title_widget(self.search_bar)
                self.search_bar.set_placeholder_text('Search a city')
                self.search_bar.connect('activate', self.add_loc, window)
                window.add_button.set_icon_name('edit-undo-symbolic')

    def add_loc(key, entry, self):
        first_time = False

        if len(saved_locations) == 0:
            first_time = True
            saved_locations.append(entry.get_text())

        city = entry.get_text()

        add_city(city, self, first_time)
        self.add_city(None, self, entry.get_text())
        self.add_button.set_icon_name('list-add-symbolic')


# -------- preferences class ---------- #
class ForecastPreferences(Adw.PreferencesWindow):
    def __init__(self, parent,  **kwargs):
        super().__init__(**kwargs)   

        self.set_title(title='Preferences')
        self.set_transient_for(parent)
        self.connect('close-request', self.do_shutdown)

        forecast_opt_page = Adw.PreferencesPage.new()
        self.add(page=forecast_opt_page)

        # -- background radient -- #
        application_preferences = Adw.PreferencesGroup.new()
        application_preferences.set_title('App preferences')

        use_gradient_bg_switch = self.opt_switch(None, "gradient-bg")

        use_gradient_bg_row = Adw.ActionRow.new()
        use_gradient_bg_row.set_title(title='Use gradient as background')
        use_gradient_bg_row.set_subtitle("Applies a gradient based on current weather and time. Requires restart to disable")
        use_gradient_bg_row.add_suffix(widget=use_gradient_bg_switch)

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
        units_row.set_title(title='Units')
        units_row.set_subtitle("Select which unit of measurement to use")
        units_row.add_suffix(widget=units_choice)

        # -- api key -- #
        api_preferences = Adw.PreferencesGroup.new()
        api_preferences.set_title('Api preferences')

        # creates option for changing api key
        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_valign(Gtk.Align.CENTER)
        self.api_key_entry.set_text(settings.get_string("api-key-s"))
        api_key_switch = self.opt_switch(self.api_key_entry, "api-key-b")

        api_key_row = Adw.ActionRow.new()
        api_key_row.set_title(title='Use personal api key')
        api_key_row.set_subtitle("Choose wether to use default api key or personal key")
        api_key_row.add_suffix(widget=self.api_key_entry)
        api_key_row.add_suffix(widget=api_key_switch)


        # adds option rows to option page
        application_preferences.add(child=use_gradient_bg_row)
        application_preferences.add(child=units_row)
        api_preferences.add(child=api_key_row)

        forecast_opt_page.add(group=application_preferences)
        forecast_opt_page.add(group=api_preferences)

    def change_unit(self, combobox):
        global units 
        units = combobox.get_active_text()
        self.saveString(None, units, 'units')
        main_page.refresh(None, None, 'True')


    # ---- creates a switch for an option ---- #
    def opt_switch(self, entry, option):
        switch = Gtk.Switch()                                   #
        switch.set_valign(align=Gtk.Align.CENTER)               # creates switch
        switch.set_active(settings.get_boolean(option))         #
        switch.connect('notify::active', self.saveOpt, option)  # connects to save option when clicked

        # -- if option is gradient bg connects switch to apply a gradient -- #
        if option == "gradient-bg":
            switch.connect('state-set', apply_bg)

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



def start(AppId, Flatpak, appimage):
    global flatpak
    flatpak = Flatpak

    global css_provider
    if flatpak:
        css_provider.load_from_resource('/dev/salaniLeo/forecast/style.css')
    elif appimage:
        css_provider.load_from_path('style.css')
    else:
        css_provider.load_from_path('data/style.css')

    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    app = Forecast(application_id=AppId)
    app.run(sys.argv)
