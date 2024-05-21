project('forecast',
          version: '1.0.0',
    meson_version: '>= 0.59.0',
  default_options: [ 'warning_level=2', 'werror=false', 'prefix=/app'],
)

APPLICATION_ID = 'dev.salanileo.forecast@0@'.format('')
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
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

bindir = join_paths(get_option('prefix'), 'bin')

py3 = python.find_installation('python3')
app_install_dir = py3.get_install_dir()

configure_file(
  input: 'forecast.in',
  output: 'forecast',
  configuration: conf,
  install: true,
  install_dir: bindir
)

install_subdir('data/status', install_dir: join_paths(get_option('prefix'), 'share/icons/hicolor/scalable'))
install_subdir('Forecast', install_dir: app_install_dir)
install_subdir('data/status', install_dir: join_paths(app_install_dir, 'Forecast/data'))

gnome.post_install(
  glib_compile_schemas: true,
  update_desktop_database: true,
)
