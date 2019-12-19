# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# REGIOPROJEKTCHECK
# install_packages.py
#
# Description:
# PROJECT URL: http://www.regioprojektcheck.de
#
# Author:
# ILS gGmbH
#
# LICENSE: The MIT License (MIT) Copyright (c) 2014 RPC Consortium
# ---------------------------------------------------------------------------

try:
    from nsis import log, messagebox
except:
    def log(x): print(x)
    messagebox = log

import os, sys
import subprocess
from collections import OrderedDict
import _winreg

min_requirement = 10.2

def get_python_path():
    try:
        esri_reg_path = r'SOFTWARE\WOW6432Node\ESRI'
        arcgis_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                     os.path.join(esri_reg_path, 'ArcGIS'),
                                     0)
        version = _winreg.QueryValueEx(arcgis_key, 'RealVersion')[0][:4]
        if float(version) < min_requirement:
            raise Exception('AddIn unterstützt ArcGIS ab Version {}'
                            .format(min_requirement))

        desktop_reg_path = os.path.join(esri_reg_path,
                                        'Desktop{v}'.format(v=version))
        desktop_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                      desktop_reg_path,
                                     0)
        desktop_dir = _winreg.QueryValueEx(desktop_key, 'InstallDir')[0]

        python_reg_path = os.path.join(esri_reg_path,
                                       'Python{v}'.format(v=version))
        python_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,
                                     python_reg_path,
                                     0)
        python_dir = _winreg.QueryValueEx(python_key, 'PythonDir')[0]

        # is desktop installation 64-Bit?
        is_64b = os.path.exists(os.path.join(desktop_dir, "bin64"))
        bitstr = 'x64' if is_64b else ''

        possible_pathes = []
        possible_pathes.append(os.path.join(python_dir, 'ArcGIS{v}'.format(v=version)))
        possible_pathes.append(os.path.join(python_dir, 'ArcGISx64{v}'.format(v=version)))

        python_pathes = []
        for path in possible_pathes:
            if os.path.exists(path):
                python_pathes.append(path)

        return python_pathes

    except WindowsError:
        log('Keine ArcGIS-Pythoninstallation gefunden.')
        return None
    except Exception as e:
        log(e)

def install_packages(python_path):

    log("\n"+ "Verwendeter Python-Pfad: " + python_path + "\n")
    log(sys.version)
    log(sys.platform)
    platform = 'win32'
    if "ArcGISx64" in python_path:
        platform = 'win_amd64'


    #Creating list with missing packages
    used_packages = OrderedDict()
    used_packages['appdirs']='appdirs-1.4.3-py2.py3-none-any.whl'
    used_packages['six']='six-1.10.0-py2.py3-none-any.whl'
    used_packages['pyparsing']='pyparsing-2.2.0-py2.py3-none-any.whl'
    used_packages['packaging']='packaging-16.8-py2.py3-none-any.whl'
    used_packages['setuptools']='setuptools-34.3.3-py2.py3-none-any.whl'

    used_packages['functools32']='functools32-3.2.3.post2-py27-none-any.whl'

    used_packages['numpy'] = 'numpy-1.12.1+mkl-cp27-cp27m-{}.whl'.format(platform)
    used_packages['cycler'] = 'cycler-0.10.0-py2.py3-none-any.whl'
    used_packages['dateutil']='python_dateutil-2.6.0-py2.py3-none-any.whl'
    used_packages['pytz']='pytz-2017.2-py2.py3-none-any.whl'

    used_packages['matplotlib']='matplotlib-2.0.0-cp27-cp27m-{}.whl'.format(platform)

    used_packages['pyodbc']='pyodbc-4.0.16-cp27-cp27m-{}.whl'.format(platform)

    used_packages['jdcal'] = 'jdcal-1.3-py2.py3-none-any.whl'
    used_packages['et-xmlfile'] = 'et_xmlfile-1.0.1-py2.py3-none-any.whl'
    used_packages['openpyxl'] = 'openpyxl-2.4.5-py2.py3-none-any.whl'

    used_packages['polyline'] = 'polyline-1.3.2-py2.py3-none-any.whl'


    used_packages['xlrd'] = 'xlrd-1.0.0-py2-none-any.whl'
    used_packages['xlsxwriter'] = 'XlsxWriter-0.9.6-py2.py3-none-any.whl'

    used_packages['py']='py-1.4.33-py2.py3-none-any.whl'
    used_packages['colorama']='colorama-0.3.7-py2.py3-none-any.whl'

    used_packages['pytest']='pytest-3.0.7-py2.py3-none-any.whl'

    used_packages['imagesize']='imagesize-0.7.1-py2.py3-none-any.whl'
    used_packages['pygments']='Pygments-2.2.0-py2.py3-none-any.whl'
    used_packages['snowballstemmer']='snowballstemmer-1.2.1-py2.py3-none-any.whl'
    used_packages['alabaster']='alabaster-0.7.10-py2.py3-none-any.whl'
    used_packages['docutils']='docutils-0.13.1-py2-none-any.whl'
    used_packages['requests']='requests-2.13.0-py2.py3-none-any.whl'

    used_packages['babel']='Babel-2.4.0-py2-none-any.whl'
    used_packages['markupsafe']='MarkupSafe-1.0-cp27-cp27m-{}.whl'.format(platform)
    used_packages['jinja2']='Jinja2-2.9.6-py2.py3-none-any.whl'

    used_packages['sphinx']='Sphinx-1.5.5-py2.py3-none-any.whl'
    used_packages['numpydoc']='numpydoc-0.6.0-py2-none-any.whl'
    used_packages['enum']='enum-0.4.6-py2-none-any.whl'
    used_packages['beautifulsoup4']='beautifulsoup4-4.6.0-py2-none-any.whl'

    used_packages['pypiwin32-219'] = 'pypiwin32-219-cp27-none-{}.whl'.format(platform)
    used_packages['pyproj'] = 'pyproj-1.9.5.1-cp27-cp27m-{}.whl'.format(platform)

    used_packages['scipy'] = 'scipy-0.19.1-cp27-cp27m-{}.whl'.format(platform)
    used_packages['pandas'] = 'pandas-0.19.1-cp27-cp27m-{}.whl'.format(platform)


    missing = OrderedDict()

    #Installing pip
    base_path = os.path.dirname(__file__)
    wheel_path = os.path.join(base_path, 'installer', 'wheels')
    log('Install or upgrade pip')
    process = subprocess.Popen([os.path.join(python_path, 'python'),
                                os.path.join(wheel_path, "pip-9.0.1-py2.py3-none-any.whl", "pip"),
                     'install',
                     '--upgrade',
                     os.path.join(wheel_path, "pip-9.0.1-py2.py3-none-any.whl")],
                               shell=True)
    ret = process.wait()
    if ret:
        log('pip nicht richtig installiert')
    else:
        log('pip installiert')

    ##Installing packages
    log('wheel_path; {}'.format(wheel_path))

    for package, filename in used_packages.iteritems():
        log('{p}: {f}'.format(p=package, f=filename))
        process = subprocess.Popen([os.path.join(python_path, 'Scripts', 'pip.exe'),
                                    'install',
                                    '-f', wheel_path,
                                    os.path.join(wheel_path, filename)],
                                   shell=True)
        ret = process.wait()
        if ret:
            log("Paket " + package + " konnte ggf. nicht installiert werden." + "\n")

    # install rpctools package
    # ToDo: Finally change from --editable to wheel
    log("installiere RPCTools")

    process = subprocess.Popen([os.path.join(python_path, 'Scripts', 'pip.exe'),
                                'install',
                                '--editable',
                                base_path],
                               shell=True)

    ret = process.wait()

    if ret:
        log('rpctools konnte nicht installiert werden')
    else:
        log("RPCTools installiert")

    log('Installation abgeschlossen.')

if __name__ == '__main__':
    python_pathes = get_python_path()
    if python_pathes:
        for path in python_pathes:
            install_packages(path)
    #install_packages('C:\\Python27-ArcGIS\\ArcGISx6410.4')
