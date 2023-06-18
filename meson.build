project('forecast',
          version: '0.2',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

APPLICATION_ID = 'dev.salaniLeo.forecast@0@'.format('')
PKGDATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), APPLICATION_ID)
PKGLIB_DIR = join_paths(get_option('prefix'), get_option('libdir'), APPLICATION_ID)

i18n = import('i18n')
gnome = import('gnome')

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'forecast')

subdir('data')
subdir('po')
subdir('share/icons')

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'forecast.in',
  output: 'forecast',
  configuration: conf,
  install: true,
  install_dir: '/app/bin'
)

install_subdir('data/status', install_dir: '/app/share/icons/hicolor/scalable')
install_subdir('Forecast', install_dir: '/app/bin')

gnome.post_install(
     glib_compile_schemas: true,
  update_desktop_database: true,
)