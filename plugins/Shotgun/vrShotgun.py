import os

from PySide2 import QtCore, QtGui

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
    infoGif = None

    def __init__(self, parent=None):
        super(vrShotgun, self).__init__(parent)
        parent.layout().addWidget(self)
        self.setupUi(self)

        # Set up the gif animation, but don't start playing it until the widget is shown
        gif_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "vred_shotgun_menu.gif"
        )
        self.infoGif = QtGui.QMovie(gif_path)
        self._gifLabel.setMovie(self.infoGif)

        self.context = sgtk.context.deserialize(os.environ.get("SGTK_CONTEXT"))
        QtCore.QTimer.singleShot(0, self.init)

    def init(self):
        self.engine = sgtk.platform.start_engine(
            "tk-vred", self.context.sgtk, self.context
        )

        # Set the version text in the plugin dialog once the engine is initialized
        self._versionLabel.setText("tk-vred {}".format(self.engine.version))

        file_to_open = os.environ.get("SGTK_FILE_TO_OPEN", None)
        if file_to_open:
            vrController.newScene()
            vrFileIO.load(file_to_open)

    def __del__(self):
        self.destroyMenu()

    def showEvent(self, event):
        """
        Reimplement QWidget event handler to receive signal when this widget
        becomes visible, at which point the gif will start playing.

        :param QShowEvent event: event that is sent when the widget is shown.
        """
        self.infoGif.start()

    def hideEvent(self, event):
        """
        Reimplement QWidget event handler to receive signal when this widget
        is hidden, at which point the gif will stop playing.

        :param QHideEvent event: event that is sent when the widget is hidden.
        """
        self.infoGif.stop()


try:
    if os.getenv("SHOTGUN_ENABLE") == "1":
        shotgun = vrShotgun(VREDPluginWidget)
except Exception as e:
    logger.exception(e)
