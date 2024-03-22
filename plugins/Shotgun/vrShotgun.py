# Cannot use sgtk.platform.qt as it is not initialized at this point
try:
    from PySide2 import QtCore
except ModuleNotFoundError:
    from PySide6 import QtCore

import os
import uiTools
import sgtk
import vrFileIO
import vrScenegraph


sgtk.LogManager().initialize_base_file_handler("tk-vred")
logger = sgtk.LogManager.get_logger(__name__)
vrShotgun_form, vrShotgun_base = uiTools.loadUiType("vrShotgunGUI.ui")
shotgun = None


class vrShotgun(vrShotgun_form, vrShotgun_base):
    """
    Class object to create a Scripts Plugin in VRED.

    IMPORTANT: For VRED Design, a special exception is made for the "Shotgun"
    plugin to run (custom scripts plugins are not supported). So this plugin
    file must be named "vrShotgun.py" with the class name "vrShotgun", and the
    plugin must be created from the UI file "vrShotgunGUI.ui".
    """

    def __init__(self, parent=None):
        """Initialize the plugin."""
        super(vrShotgun, self).__init__(parent)
        parent.layout().addWidget(self)
        self.setupUi(self)
        QtCore.QTimer.singleShot(0, self.init)

    def __del__(self):
        """Clean up the plugin."""
        self.destroyMenu()

    def init(self):
        """Initialize the plugin."""
        # Get the SG context and start the VRED engine
        context = sgtk.context.deserialize(os.environ.get("SGTK_CONTEXT"))
        sgtk.platform.start_engine("tk-vred", context.sgtk, context)
        # Open file at start up, if given
        file_to_open = os.environ.get("SGTK_FILE_TO_OPEN", None)
        if file_to_open:
            vrFileIO.load(
                [file_to_open],
                vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )


def onDestroyVREDScriptPlugin():
    """
    This method is called before this VRED plugin is destroyed.

    This method is defined outside of the vrFlowProductionTrackingPlugin class.

    In this plugin we want to destroy the VRED engine, which will handle any
    necessary clean up.
    """
    current_engine = sgtk.platform.current_engine()
    if current_engine:
        current_engine.destroy()


# Create the VRED plugin
try:
    if os.getenv("SHOTGUN_ENABLE") == "1":
        shotgun = vrShotgun(VREDPluginWidget)
except Exception as e:
    logger.exception(e)
