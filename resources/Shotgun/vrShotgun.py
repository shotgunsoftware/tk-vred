import os
import sys
from PySide2 import QtCore
import vrFileIO
import vrController

# Make Shotgun libraries visible
sys.path.append(r"C:\Program Files\Shotgun\Python\Lib\site-packages")

import tank

tank.LogManager().initialize_base_file_handler("tk-vred")
logger = tank.LogManager.get_logger(__name__)

from PySide2 import QtWidgets
import uiTools

vrShotgun_form, vrShotgun_base = uiTools.loadUiType('vrShotgunGUI.ui')


class vrShotgun(vrShotgun_form, vrShotgun_base):
    context = None
    engine = None

    def __init__(self, parent=None):
        super(vrShotgun, self).__init__(parent)
        parent.layout().addWidget(self)
        self.setupUi(self)
        if 'SHOTGUN_ENABLE' in os.environ and os.environ['SHOTGUN_ENABLE'] == '1':
            self.context = tank.context.deserialize(os.environ.get("TANK_CONTEXT"))
            self.engine = tank.platform.start_engine('tk-vred', self.context.tank, self.context)
            QtCore.QTimer.singleShot(0, self.init)

    def init(self):
        file_to_open = os.environ.get("SGTK_FILE_TO_OPEN", None)
        if file_to_open:
            vrController.newScene()
            vrFileIO.load(file_to_open)

    def __del__(self):
        self.destroyMenu()

    def getVredMainWindow(self):
        from shiboken2 import wrapInstance
        return wrapInstance(VREDMainWindowId, QtWidgets.QMainWindow)

try:
    customMenu = vrShotgun(VREDPluginWidget)
except Exception as e:
    logger.exception(e)
