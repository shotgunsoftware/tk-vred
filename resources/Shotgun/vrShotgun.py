# vrPySideExample

import os
import sys
import traceback

import logging
logging.basicConfig(filename=os.path.expanduser('~/AppData/Roaming/Shotgun/logs/vrShotgun.log'), level=logging.DEBUG)

from PySide2 import QtWidgets
from PySide2 import QtCore
import uiTools
import vrController
import vrFileIO
import vrMovieExport

logging.info('\n\n\nShotgun Plugin ({})'.format(sys.version))

vrShotgun_form, vrShotgun_base = uiTools.loadUiType('vrShotgunGUI.ui')

class vrShotgun(vrShotgun_form, vrShotgun_base):

    context = None
    engine = None

    def __init__(self, parent=None):
        super(vrShotgun, self).__init__(parent)
        parent.layout().addWidget(self)
        self.setupUi(self)
        if 'SHOTGUN_ENABLE' in os.environ and os.environ['SHOTGUN_ENABLE'] == '1':
            logging.info("Shotgun is enabled")
            logging.info("Starting Engine")

            # Make Shotgun libraries visible
            sys.path.append(r"C:\Program Files\Shotgun\Python\Lib\site-packages")

            # Launch the Engine
            import tank
            self.context = tank.context.deserialize(os.environ.get("TANK_CONTEXT"))
            self.engine = tank.platform.start_engine('tk-vred', self.context.tank, self.context)
        else:
            logging.info("Shotgun plugin loaded however shotgun was not enabled!!")

    def __del__(self):
        self.destroyMenu()

    def getVredMainWindow(self):
        from shiboken2 import wrapInstance
        return wrapInstance(VREDMainWindowId, QtWidgets.QMainWindow)

try:
    customMenu = vrShotgun(VREDPluginWidget)
except Exception as w:
    v = traceback.format_exc()
    logging.error('Error {}:\n{}'.format(w, v))
