# Copyright (c) 2024 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

import os
from typing import Callable, Union

from sgtk.platform.qt import QtCore, QtGui


class VREDFileIOProgressWidget(QtGui.QDialog):
    """A widget to display progress for VRED async Filoe I/O operations."""

    def __init__(
        self,
        vredpy,
        num_files: int,
        use_default_signals: bool = True,
        abort_callback: Union[Callable[[int], None], None] = None,
        indeterminate: bool = False,
        parent: QtGui.QWidget = None,
    ):
        """
        Initialize.

        :parm vredpy: The VRED Python API instance.
        :param num_files: The number of files this progress bar is tracking.
            This is required to determine the progress value and when the
            operation is complete.
        :param indeterminate: True will animate the progress bar indeterminately
            else the progress bar will animate determinately. Determinate
            animation requires the `update` method to be called as the operation
            progresses.
        :param use_default_signals: True will connect the default signals to the
            default slots. False will not connect any signals to slots.
        :param parent: The parent widget.
        """

        super().__init__(parent)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.vredpy = vredpy
        self.__total_jobs = num_files
        self.__completed_jobs = 0
        self.__job_id = None
        self.__abort_callback = None
        self.__signal_slots = []
        self.__default_status = "Please wait..."

        # ---- Setup the UI ----

        self.__file_label = QtGui.QLabel(self)
        file_text_layout = QtGui.QHBoxLayout()
        file_text_layout.setContentsMargins(0, 0, 0, 0)
        file_text_layout.setSpacing(0)
        file_text_layout.addStretch()
        file_text_layout.addWidget(self.__file_label)
        file_text_layout.addStretch()
        file_text_widget = QtGui.QWidget(self)
        file_text_widget.setLayout(file_text_layout)

        self.__progress_status_label = QtGui.QLabel(self.__default_status, self)
        text_layout = QtGui.QHBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        text_layout.addStretch()
        text_layout.addWidget(self.__progress_status_label)
        text_layout.addStretch()
        text_layout_widget = QtGui.QWidget(self)
        text_layout_widget.setLayout(text_layout)

        self.__progress_bar = QtGui.QProgressBar(self)
        if indeterminate:
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
        layout.setSpacing(10)
        layout.addWidget(file_text_widget)
        layout.addWidget(text_layout_widget)
        layout.addWidget(self.__progress_bar)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        if parent:
            center = parent.rect().center()
        else:
            center = QtCore.QRect()
        x = center.x() - self.width() / 2
        y = center.y() - self.height() / 2
        self.setGeometry(x, y, 400, 150)

        # ---- Iniiialize the widget ----

        # Set the abort callback. If None, the button will be hidden.
        self.set_abort_callback(abort_callback)

        # Connect the default signals to the default slots, if specified,
        # otherwise caller must set up the signals and slots manually.
        if use_default_signals:
            self.__setup_default_signals()

    def __del__(self):
        """Destructor."""

        for signal, slot in self.__signal_slots:
            signal.disconnect(slot)

    # --------------------------------------------------------------------------
    # Properties

    @property
    def job_id(self):
        """Get or set the job ID of the operation that is being tracked."""
        return self.__job_id

    @job_id.setter
    def job_id(self, value: int):
        self.__job_id = value

    # --------------------------------------------------------------------------
    # Public methods

    def set_connection(self, signal: QtCore.Signal, slot: Callable):
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

        self.__abort_callback(self.job_id)
        self.job_completed(force=True)

    def job_completed(self, force: bool = False):
        """Called when a file I/O job has completed."""

        self.__completed_jobs += 1
        if not force and self.__completed_jobs < self.__total_jobs:
            return

        # If all jobs are complete, destroy the widget.
        while self.__signal_slots:
            signal, slot = self.__signal_slots.pop()
            signal.disconnect(slot)
        self.accept()
        self.deleteLater()

    def is_job_valid(self, job_id: int):
        """
        Check if the given job ID is valid.

        The job ID is valid if it matches the job ID of the operation that is
        being tracked, or if it belongs to the import operation that is being
        tracked (e.g. file conversion that may be triggered before import).

        :param job_id: The job ID to check.
        :return: True if the job ID is valid, False otherwise.
        """

        if self.job_id == job_id:
            return True

        if self.vredpy.vrFileIOService.jobBelongsToImport(job_id, self.job_id):
            return True

        return False

    # --------------------------------------------------------------------------
    # Public slots

    def on_update(
        self,
        job_id: int,
        file: str = None,
        progress: Union[int, None] = None,
        status: str = None,
    ):
        """
        Callback to trigger when the operation progress is updated.

        The progress bar value will be updated to the given value.

        :param job_id: The job ID of the operation that is being tracked.
        :param file: The file that is being processed.
        :param progress: The progress value to set. This value should be between
            0 and 100.
        :param status: The status of the operation.
        """

        if not self.is_job_valid(job_id):
            return

        if progress is None:
            progress = 0

        job_progress = min(100, max(0, progress))
        current_progress = 100 * self.__completed_jobs / self.__total_jobs
        total_progress = job_progress / self.__total_jobs + current_progress
        self.__progress_bar.setValue(total_progress)

        if file:
            base_name = os.path.basename(file)
            self.__file_label.setText(base_name)
            self.__file_label.setToolTip(file)

        if status:
            self.__progress_status_label.setText(f"{status}...")
        else:
            self.__progress_status_label.setText(self.__default_status)

    def on_finish(self, job_id: int, file: str = None, state=None):
        """
        Callback to trigger when the operation is complete.

        This widget will be cleaned up and destroyed.

        :param job_id: The job ID of the operation that is being tracked.
        """

        if not self.is_job_valid(job_id):
            return

        if isinstance(state, self.vredpy.vrKernelServices.vrCADFileTypes.JobState):
            if state == self.vredpy.vrKernelServices.vrCADFileTypes.JobState.kFailed:
                self.on_failed(job_id, file, "Job failed.")
                return

            if (
                state
                == self.vredpy.vrKernelServices.vrCADFileTypes.JobState.kIncomplete
            ):
                self.on_failed(
                    job_id,
                    file,
                    "Job finished, but not all parts of an assembly were imported successfully.",
                )
                return

            if state == self.vredpy.vrKernelServices.vrCADFileTypes.JobState.kUnknown:
                self.on_failed(job_id, file, "Job finished with an unknown state.")
                return

        self.job_completed()

    def on_failed(self, job_id: int, file: str = None, description: str = None):
        """
        Callback to trigger when the operation failed.

        This widget will be cleaned up and destroyed.

        :param job_id: The job ID of the operation that is being tracked.
        :param file: The file that was being processed when the operation failed.
        :param description: A description of the failure.
        """

        if not self.is_job_valid(job_id):
            return

        QtGui.QMessageBox.critical(
            self.parentWidget(),
            "VRED Error",
            f"An error occurred while processing {file}.\n\n{description}",
        )

        self.job_completed()

    # --------------------------------------------------------------------------
    # Private methods

    def __setup_default_signals(self):
        """Set up the default signal slots to update the progress bar."""

        self.set_connection(
            self.vredpy.vrFileIOService.fileConversionStarted,
            lambda job_id, file: self.on_update(
                job_id, file, 0, f"Starting file conversion"
            ),
        )
        self.set_connection(
            self.vredpy.vrFileIOService.fileConversionProgressChanged,
            self.on_update,
        )
        self.set_connection(
            self.vredpy.vrFileIOService.fileConversionFailed,
            self.on_failed,
        )
        self.set_connection(
            self.vredpy.vrFileIOService.fileLoadingStarted,
            lambda job_id, file: self.on_update(job_id, file, 0, f"Loading"),
        )
        self.set_connection(
            self.vredpy.vrFileIOService.fileLoadingProgressChanged,
            self.on_update,
        )
        self.set_connection(
            self.vredpy.vrFileIOService.fileLoadingFinished,
            self.on_finish,
        )
        self.set_connection(
            self.vredpy.vrFileIOService.fileLoadingFailed,
            self.on_failed,
        )
