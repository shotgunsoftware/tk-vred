# For Python2 integer division
from __future__ import division

import os

from PySide2 import QtCore, QtGui
import uiTools

import sgtk

import vrFileIO
import vrScenegraph


sgtk.LogManager().initialize_base_file_handler("tk-vred")
logger = sgtk.LogManager.get_logger(__name__)
vrShotgun_form, vrShotgun_base = uiTools.loadUiType("vrShotgunGUI.ui")

# The vrShotgun plugin module instance
shotgun = None


class vrShotgun(vrShotgun_form, vrShotgun_base):
    context = None
    gif_aspect_ratio = None

    def __init__(self, parent=None):
        super(vrShotgun, self).__init__(parent)
        parent.layout().addWidget(self)
        self.setupUi(self)

        # Set up the gif animation, but don't start playing it until the widget is shown
        gif_movie = QtGui.QMovie("vred_shotgun_menu.gif")
        gif_movie.jumpToFrame(0)
        movie_size = gif_movie.currentImage().size()
        self.gif_aspect_ratio = movie_size.width() / movie_size.height()
        self.gif_label.setMovie(gif_movie)

        self.context = sgtk.context.deserialize(os.environ.get("SGTK_CONTEXT"))
        QtCore.QTimer.singleShot(0, self.init)

    def init(self):
        engine = sgtk.platform.start_engine("tk-vred", self.context.sgtk, self.context)

        # Set the version text in the plugin dialog once the engine is initialized
        self.version_label.setText("tk-vred {}".format(engine.version))

        file_to_open = os.environ.get("SGTK_FILE_TO_OPEN", None)
        if file_to_open:
            vrFileIO.load(
                [file_to_open],
                vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )

    def __del__(self):
        self.destroyMenu()

    def showEvent(self, event):
        """
        Reimplement QWidget event handler to receive signal when this widget
        becomes visible, at which point the gif will start playing.

        :param QShowEvent event: event that is sent when the widget is shown.
        """
        gif_movie = self.gif_label.movie()
        if gif_movie:
            gif_movie.start()

    def hideEvent(self, event):
        """
        Reimplement QWidget event handler to receive signal when this widget
        is hidden, at which point the gif will stop playing.

        :param QHideEvent event: event that is sent when the widget is hidden.
        """
        gif_movie = self.gif_label.movie()
        if gif_movie:
            gif_movie.stop()

    def resizeEvent(self, event):
        """Reimplement resize event handler to keep gif animation aspect ratio."""
        rect = self.geometry()
        gif_movie = self.gif_label.movie()
        if gif_movie:
            width = rect.height() * self.gif_aspect_ratio
            if width <= rect.width():
                size = QtCore.QSize(width, rect.height())
            else:
                height = rect.width() / self.gif_aspect_ratio
                size = QtCore.QSize(rect.width(), height)

            # Scale the gif animation and then adjust this widget and the most
            # top-level widget to fit to the new gif scaled size
            gif_movie.setScaledSize(size)
            self.adjustSize()
            self.parentWidget().parentWidget().adjustSize()

        return super(vrShotgun, self).resizeEvent(event)


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
        shotgun = vrShotgun(VREDPluginWidget)
except Exception as e:
    logger.exception(e)
