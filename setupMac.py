from setuptools import setup

APP = ['app.py']
DATA_FILES = []
OPTIONS = {
    'includes': [
        'readline',
    ],
    'iconfile': 'layout/resources/logo.icns',
    # Prevents an issue involving setuptools' vendored
    # packages causing conflicts with our own versions.
    #
    # For further information:
    # https://github.com/ronaldoussoren/py2app/issues/531
    'excludes': [
        'setuptools',
    ]
}

import os

def loopThrough(directory):
    files = []
    for file in os.listdir(directory):
        cur = os.path.join(directory, file)
        if os.path.isfile(cur):
            files.append(cur)
        elif os.path.isdir(cur):
            loopThrough(cur)
    DATA_FILES.append((directory, files))

loopThrough('layout')

print('\n'.join(list(map(str, DATA_FILES))))

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='3DS-RPC',
)
