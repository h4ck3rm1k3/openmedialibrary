import os
import ox

root_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
os.chdir(root_dir)

path = '../js/'
files = sorted([
    file for file in os.listdir(path)
    if not file.startswith('.')
    and not file.startswith('oml.')
])
ox.file.write_json('../json/js.json', files, indent=4)
ox.file.write_file(
    '%soml.min.js' % path,
    '\n'.join([
        ox.js.minify(ox.file.read_file('%s%s' % (path, file)))
        for file in files
    ])
)
