import os

from PySide2 import QtCore
from PySide2 import QtWidgets

import vrFileIO
import vrController
import uiTools

import sgtk

sgtk.LogManager().initialize_base_file_handler("tk-vred")
logger = sgtk.LogManager.get_logger(__name__)
vrShotgun_form, vrShotgun_base = uiTools.loadUiType("vrShotgunGUI.ui")


class vrShotgun(vrShotgun_form, vrShotgun_base):
    context = None
    engine = None

    def __init__(self, parent=None):
        super(vrShotgun, self).__init__(parent)
        parent.layout().addWidget(self)
        self.setupUi(self)
        self.context = sgtk.context.deserialize(os.environ.get("SGTK_CONTEXT"))
        QtCore.QTimer.singleShot(0, self.init)

    def init(self):
        self.engine = sgtk.platform.start_engine(
            "tk-vred", self.context.sgtk, self.context
        )
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
    if os.getenv("SHOTGUN_ENABLE") == "1":
        shotgun = vrShotgun(VREDPluginWidget)
except Exception as e:
    logger.exception(e)
