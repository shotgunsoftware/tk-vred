# Copyright (c) 2024 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

from typing import Callable, Union

from sgtk.platform.qt import QtCore, QtGui


class ProgressBarWidget(QtGui.QDialog):
    """A widget to display a progress of an operation that is executing."""

    def __init__(self, indeterminate_mode=True, parent=None):
        """Initialize"""

        super().__init__(parent)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.__job_id = None
        self.__abort_callback = None
        self.__signal_slots = []

        # ---- Setup the UI ----

        self.__progress_label = QtGui.QLabel(self)

        self.__progress_bar = QtGui.QProgressBar(self)
        if indeterminate_mode:
            self.__progress_bar.setMinimum(0)
            self.__progress_bar.setMaximum(0)
        else:
            self.__progress_bar.setRange(0, 100)
            self.__progress_bar.setValue(0)

        self.__abort_button = QtGui.QPushButton("Abort", self)
        self.__abort_button.setToolTip("Abort the operation in progress.")
        self.__abort_button.clicked.connect(self.abort)

        self.__close_button = QtGui.QPushButton("Close", self)
        self.__close_button.setDefault(True)
        self.__close_button.setToolTip(
            "Close the dialog. The operation will continue in the background."
        )
        self.__close_button.clicked.connect(self.accept)

        button_layout = QtGui.QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        button_layout.addStretch()
        button_layout.addWidget(self.__abort_button)
        button_layout.addWidget(self.__close_button)

        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        layout.addWidget(self.__progress_label)
        layout.addWidget(self.__progress_bar)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        if parent:
            center = parent.rect().center()
        else:
            center = QtCore.QRect()
        x = center.x() - self.width() / 2
        y = center.y() - self.height() / 2
        self.setGeometry(x, y, 400, 100)

        # Hide the abort button until an abort slot is provided
        self.__abort_button.setVisible(False)

    # --------------------------------------------------------------------------
    # Properties

    @property
    def job_id(self):
        """Get or set the job ID that is being tracked by the progress bar."""
        return self.__job_id

    @job_id.setter
    def job_id(self, value: int):
        self.__job_id = value

    @property
    def text(self):
        """Get or set the text that is displayed with the progrss bar."""
        return self.__progress_label.text()

    @text.setter
    def text(self, value: str):
        self.__progress_label.setText(value)

    # --------------------------------------------------------------------------
    # Public methods

    def connect(self, signal: QtCore.Signal, slot: Callable):
        """
        Connect the given signal to the given slot.

        Keep track of signal/slot connections so that they can be disconnected
        when the widget is destroyed.

        :param signal: The signal to connect.
        :param slot: The slot to connect.
        """

        self.__signal_slots.append((signal, slot))
        signal.connect(slot)

    def set_abort_callback(self, abort_callback: Union[Callable[[int], None], None]):
        """
        Set whether the operation can be aborted.

        An button will be displayed to allow the user to abort the operation, if
        the operation can be aborted.

        :param abort: Whether the operation can be aborted.
        """

        self.__abort_callback = abort_callback
        self.__abort_button.setVisible(self.__abort_callback is not None)

    def abort(self):
        """Abort the operation in progress."""

        self.__abort_callback(self.__job_id)
        self.destroy()

    def destroy(self):
        """Clean up and destroy this widget."""

        for signal, slot in self.__signal_slots:
            signal.disconnect(slot)

        self.accept()
        self.deleteLater()

    # --------------------------------------------------------------------------
    # Public slots

    def update(self, job_id: int, progress: int):
        """
        Callback to udpate the progress of the operation.

        The progress bar value will be updated to the given value.

        :param job_id: The job ID that is being tracked by the progress bar.
        :param progress: The progress value to set. This value should be between
            0 and 100.
        """

        print(type(progress))
        if self.__job_id is None or self.__job_id != job_id:
            return

        self.__progress_bar.setValue(progress)

    def finish(self, job_id: int):
        """
        Callback to finish the operation.

        This widget will be cleaned up and destroyed.

        :param job_id: The job ID that is being tracked by the progress bar.
        """

        if self.__job_id is None or self.__job_id != job_id:
            return

        self.destroy()
