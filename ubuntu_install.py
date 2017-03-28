import os
os.system("sudo apt-get install python-gi")
os.system("sudo apt-get install gir1.2-webkit-3.0")

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from gi.repository import Gdk
    gi.require_version('WebKit', '3.0')
    from gi.repository import WebKit
except ImportError:
    print "Dependency unfulfilled, please install gi library"
    exit(1)


def install_and_import(package):
    """@brief     Imports modules and installs them if they are not."""
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        try:
            import pip
        except ImportError:
            print "no pip"
            os.system('sudo python get_pip.py')
        finally:
            import pip
        pip.main(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)


# these other ones I a am not so sure of. Thus the install function.
install_and_import("subprocess")
install_and_import("json")
install_and_import("sys")
install_and_import("time")
install_and_import("shutil")
install_and_import("urlparse")
install_and_import("itertools")
install_and_import("webbrowser")
