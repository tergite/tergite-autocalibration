import os

from PyQt5 import QtGui

__base_dir__ = os.path.split(os.path.abspath(__file__))[0]
__res_dir__ = os.path.join(__base_dir__, "resources")


def load_icon(name: str) -> QtGui.QIcon:
    """
    Load an icon from the 'resources' directory.

    Parameters
    ----------
    name : str
        The name of the icon to load.

    Returns
    -------
    QtGui.QIcon
        The loaded icon.
    """
    return QtGui.QIcon(os.path.join(__res_dir__, name))
