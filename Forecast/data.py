import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gio, Gtk
from datetime import datetime
from gettext import gettext as _
from Forecast.style import *

class constants():
    meters = _('Metric System')
    miles = _('Imperial System')
    metric_system = f'{meters}, °C - Km/h'
    imperial_system = f'{miles}, °F - mph'

    settings     = Gio.Settings.new("dev.salaniLeo.forecast")
    units        = settings.get_string('units').split(' ')[0].lower()
    raw_units    = settings.get_string('units')
    degrees_unit = raw_units[raw_units.find(",")+1:raw_units.find("-")]
    speed_unit   = raw_units[raw_units.find("-")+1:]
    poll_unit    = ' μg/m3'
    icon_loc     = None
    today        = datetime.now()
    api_key      = settings.get_string('api-key-s')
    available_units = [metric_system, imperial_system]

    def wind_dir(angle):
        directions = [
            _("N"), _("NNE"), _("NE"), _("ENE"), _("E"), _("ESE"), _("SE"), _("SSE"),
            _("S"), _("SSW"), _("SW"), _("WSW"), _("W"), _("WNW"), _("NW"), _("NNW"),
        ]
        index = round(angle / (360.0 / len(directions))) % len(directions)
        return directions[index]


class app_data():
    def current_city_n():
        return constants.settings.get_int('selected-city')
    
    def use_dark_text():
        return constants.settings.get_boolean("enhance-contrast")
    
    def use_gradient_bg():
        return constants.settings.get_boolean("gradient-bg")
    
    def use_glassy_elements():
        return constants.settings.get_boolean('use-glassy')
    
    def weather_locs_list():
        return constants.settings.get_strv('wthr-locs')
    
    def current_units():
        return constants.settings.get_string('units')
    
    def update_units():
        raw_units = constants.current_units()
        constants.degrees_unit = raw_units[raw_units.find(",")+1:raw_units.find("-")]
        constants.speed_unit   = raw_units[raw_units.find("-")+1:]
        constants.units = raw_units.split(' ')[0].lower()
        
class elements():
    def dynamic_stack():
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        return stack

    def info_box(data, icon):
        box = Gtk.Box(spacing=3)
        label = Gtk.Label()
        icon = Gtk.Image.new_from_icon_name(icon)
        box.append(icon)
        label.set_label(data)
        box.append(label)
        box.set_halign(Gtk.Align.CENTER)
        return box

    def add_page(self, name, stack, lista):
        lista.append(name)
        stack.add_titled(child=self, name=name, title=name)

    def conditions_box(name):
        name = []
        text_label = Gtk.Label()
        text_label.add_css_class(css_class='dim-label')
        info_label = Gtk.Label()
        text_label.set_valign(Gtk.Align.START)
        info_label.set_valign(Gtk.Align.START)
        name.append(text_label)
        name.append(info_label)
        return name
    
    def adv_conditions_box(name):
        name = []
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        top_bar = Gtk.Box()
        stack = elements.dynamic_stack()
        second_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        second_box.set_name(_('Weather'))
        first_box = Gtk.Box()
        first_box.set_name(_('Pollution'))
        title_label = Gtk.Label()
        title_label.set_hexpand(True)
        title_label.add_css_class('text_medium')

        cndts_info_label = Gtk.Label()
        cndts_txt_label = Gtk.Label()
        cndts_box = elements.create_info_box(_('Conditions:'), cndts_txt_label, cndts_info_label)

        base_pllt_txt_lbl = Gtk.Label()
        base_pllt_info_lbl = Gtk.Label()
        pllt_box = elements.create_info_box(_('Pollution:'), base_pllt_txt_lbl, base_pllt_info_lbl)

        pllt_info_lbl = Gtk.Label()
        pllt_txt_lbl = Gtk.Label()
        pllt_box = elements.create_info_box(_('Pollution:'), pllt_txt_lbl, pllt_info_lbl)

        sys_info_lbl = Gtk.Label()
        sys_txt_lbl = Gtk.Label()
        sys_box = elements.create_info_box(_('System:'), sys_txt_lbl, sys_info_lbl)

        pages = [stack, second_box, first_box]

        top_bar.prepend(elements.next_page_btn(1, pages, title_label))
        top_bar.append(title_label)
        top_bar.append(elements.next_page_btn(2, pages, title_label))
        top_bar.set_hexpand(True)

        stack.add_child(second_box)
        stack.add_child(first_box)
        stack.set_halign(Gtk.Align.START)

        second_box.append(cndts_box)
        second_box.append(sys_box)
        second_box.set_valign(Gtk.Align.CENTER)
        first_box.append(pllt_box)

        main_box.append(top_bar)
        main_box.append(stack)

        title_label.set_label(stack.get_visible_child().get_name())

        name.append(main_box)
        name.append(cndts_txt_label)
        name.append(cndts_info_label)
        name.append(pllt_info_lbl)
        name.append(pllt_txt_lbl)
        name.append(sys_txt_lbl)
        name.append(sys_info_lbl)
        name.append(base_pllt_info_lbl)
        name.append(base_pllt_txt_lbl)
        return name
    
    def create_info_box(title, txt_lbl, info_lbl):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_name(title)
        title = Gtk.Label(label=title)
        title.add_css_class('text_medium')
        title.set_halign(Gtk.Align.START)
        txt_lbl.set_valign(Gtk.Align.CENTER)
        txt_lbl.set_halign(Gtk.Align.CENTER)
        txt_lbl.add_css_class(css_class='dim-label')
        inn_box = Gtk.Box(spacing=30)
        box.append(title)
        box.append(inn_box)
        inn_box.append(txt_lbl)
        inn_box.append(info_lbl)
        return box


    def next_page_btn(n, stacks, title_label):
        btn = Gtk.Button()
        if n == 1:
            btn.set_icon_name('pan-start-symbolic')
        elif n == 2:
            btn.set_icon_name('pan-end-symbolic')
            btn.set_halign(Gtk.Align.END)
        btn.connect('clicked', elements.next_page, stacks, title_label)
        
        return btn

    def next_page(btn, stacks, title_label):
        stack  = stacks[0]
        pages  = [stacks[1], stacks[2]]
        active = pages.index(stack.get_visible_child())
        if len(pages) <= active + 1:
            stack.set_visible_child(pages[active-1])
        else:
            stack.set_visible_child(pages[active+1])
        title_label.set_label(stack.get_visible_child().get_name())

def change_bg(stack, gparamstring, main_window, icons, names):
    if app_data.use_gradient_bg():
        day = names.index(stack.get_visible_child_name())
        icon = icons[day]
        app_style.apply_bg(main_window, icon, True)

def sw_set_bg(switch, state, main_window, icons, names):
    app_style.apply_bg(main_window, icons[0], False)