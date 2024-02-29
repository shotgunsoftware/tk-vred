import os

# Cannot use sgtk.platform.qt as it is not initialized at this point
try:
    from PySide2 import QtCore, QtWidgets
except ModuleNotFoundError:
    from PySide6 import QtCore, QtWidgets


import sgtk

import vrFileIO
import vrScenegraph


sgtk.LogManager().initialize_base_file_handler("tk-vred")
logger = sgtk.LogManager.get_logger(__name__)

# The vrFlowProductionTrackingPlugin plugin module instance
flow_production_tracking_plugin = None


class vrFlowProductionTrackingPlugin(QtCore.QObject):
    def __init__(self, parent=None):
        super(vrFlowProductionTrackingPlugin, self).__init__(parent)
        QtCore.QTimer.singleShot(1, self.init)

    def __del__(self):
        self.destroyMenu()

    def init(self):
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
    onDestroyVREDScriptPlugin() is called before this plugin is destroyed. In this
    plugin we want to destroy the VRED engine, which will handle any necessary clean up.
    """
    current_engine = sgtk.platform.current_engine()
    if current_engine:
        current_engine.destroy()


try:
    if os.getenv("SHOTGUN_ENABLE") == "1":
        flow_production_tracking_plugin = vrFlowProductionTrackingPlugin()
    label = QtWidgets.QLabel(VREDPluginWidget)
    label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter);
    label.setScaledContents(True)
    label.setText("Flow Production Tracking menu installed in main menu bar.")
    VREDPluginWidget.layout().addWidget(label)
except Exception as e:
    logger.exception(e)
