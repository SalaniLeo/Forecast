desktop_file = i18n.merge_file(
        input: 'dev.salaniLeo.forecast.desktop.in',
       output: 'dev.salaniLeo.forecast.desktop',
         type: 'desktop',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

appstream_file = i18n.merge_file(
        input: 'dev.salaniLeo.forecast.appdata.xml.in',
       output: 'dev.salaniLeo.forecast.appdata.xml',
       po_dir: '../po',
      install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util, args: ['validate', appstream_file])
endif

install_data('dev.salaniLeo.forecast.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file',
       compile_schemas,
       args: ['--strict', '--dry-run', meson.current_source_dir()])
endif

gnome.compile_resources('forecast',
  'forecast.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')
py3 = python.find_installation('python3')
app_install_dir = py3.get_install_dir()
install_data(
  'style.css',
  install_dir: join_paths(app_install_dir, 'Forecast/data')
)
