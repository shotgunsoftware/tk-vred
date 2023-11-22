# Copyright (c) 2023 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from collections import namedtuple

import sgtk
from sgtk.platform.qt import QtGui

sg_qwidgets = sgtk.platform.import_framework("tk-framework-qtwidgets", "sg_qwidgets")
SGQWidget = sg_qwidgets.SGQWidget


class ExportToLibraryWidget(SGQWidget):
    """Widget to provide UI to export published files to a Material Library."""

    def __init__(self, parent):
        """Initialize"""

        super(ExportToLibraryWidget, self).__init__(parent, layout_direction=QtGui.QBoxLayout.TopToBottom)

        self.__bundle = sgtk.platform.current_bundle()

        # Widget values 
        self.__accepted = False
        self.__create_on_export = None
        self.__material_library = None

        # Widget data
        self.__material_libraries = None
        self.__setup_data()

        # Widget UI
        self.__UI = namedtuple("UI", [
            "create_button",
            "create_widget",
            "add_widget",
            "library_name_line_edit",
            "library_path_line_edit",
            "libraries_combobox"
        ])
        self.__ui = self.__setup_ui()
        self.__ui.create_button.setChecked(True)

    @property
    def hide_tk_title_bar(self):
        """Hint to hide the Toolkit title bar."""
        return True

    @property
    def accepted(self):
        """Get the exit code of the dialog."""
        return self.__accepted
    
    @property
    def create_on_export(self):
        """Get the option to Create Material on export."""
        return self.__create_on_export
    
    @property
    def material_libarry(self):
        """
        Get the Material Library to export to.

        If `create_on_export` is True, then this will be a dictionary defining the library to
        first create. If `create_on_export` is False, then this will be a dictionary defining a
        Material Library that already exist.
        """
        return self.__material_library
    
    def __setup_data(self):
        """Set up and retreive the necessary data for the widget.""" 

        # NOTE should we filter by project?
        self.__material_libraries = self.__bundle.shotgun.find(
            "AssetLibrary",
            filters=[
                ["sg_type", "is", "Material"],
            ],
            fields=[
                "code",
                "sg_path",
                "custom_non_project_entity01_sg_material_libraries_custom_non_project_entity01s",
                "sg_published_files",
            ]
        )

    def __setup_ui(self):
        """Set up the widget UI."""

        from sgtk.platform.qt import QtGui

        library_name_label = QtGui.QLabel("Name")
        library_name_line_edit= QtGui.QLineEdit()
        create_name_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.TopToBottom,
            child_widgets=[
                library_name_label, library_name_line_edit,
            ],
        )
        # create_name_widget.layout().setSpacing(0)
        create_name_widget.layout().setContentsMargins(0, 0, 0, 0)

        library_path_label = QtGui.QLabel("Path")
        library_path_line_edit = QtGui.QLineEdit()
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        library_path_line_edit.setSizePolicy(size_policy)
        library_path_file_chooser_button = QtGui.QPushButton("...")
        library_path_file_chooser_button.setMaximumWidth(32)
        library_path_file_chooser_button.clicked.connect(
            lambda checked=None, le=library_path_line_edit: le.setText(
                QtGui.QFileDialog.getExistingDirectory(
                    self,
                    "Select Folder",
                    "/home",
                    QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks,
                )
            )
        )
        create_path_edit_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.LeftToRight,
            child_widgets=[
                library_path_line_edit, library_path_file_chooser_button
            ],
        )
        # create_path_edit_widget.layout().setSpacing(5)
        create_path_edit_widget.layout().setContentsMargins(0, 0, 0, 0)
        create_path_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.TopToBottom,
            child_widgets=[
                library_path_label, create_path_edit_widget,
            ],
        )
        # create_path_widget.layout().setSpacing(5)
        create_path_widget.layout().setContentsMargins(0, 0, 0, 0)
        create_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.TopToBottom,
            child_widgets=[create_name_widget, create_path_widget],
        )

        # Add to existing Material Library button
        add_label = QtGui.QLabel("Add to Existing")
        libraries_combobox = QtGui.QComboBox()
        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        libraries_combobox.setSizePolicy(size_policy)
        for library in self.__material_libraries:
            libraries_combobox.addItem(library["code"], userData=library)

        # Create Material Library button
        create_button = QtGui.QCheckBox("Create Material Library")
        create_button.toggled.connect(self._on_create_toggled)
        # Export (accept) button
        export_button = QtGui.QPushButton("Export")
        export_button.clicked.connect(self._on_export)
        # Cancel (reject) button
        cancel_button = QtGui.QPushButton("Cancel")
        cancel_button.clicked.connect(self._on_cancel)

        # Container widgets
        add_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.LeftToRight,
            child_widgets=[
                add_label, libraries_combobox,
            ],
        )
        button_container_widget = SGQWidget(
            self,
            layout_direction=QtGui.QBoxLayout.LeftToRight,
            child_widgets=[
                None, export_button, cancel_button,
            ],
        )

        # Add widgets to layout
        self.add_widgets([create_button, create_widget, add_widget, button_container_widget])

        return self.__UI(
            create_button=create_button,
            create_widget=create_widget,
            add_widget=add_widget,
            library_name_line_edit=library_name_line_edit,
            library_path_line_edit=library_path_line_edit,
            libraries_combobox=libraries_combobox,
        )

    def _on_create_toggled(self, checked):
        """Called when the Create Material Library button toggled."""

        self.__ui.create_widget.setEnabled(checked)
        self.__ui.add_widget.setEnabled(not checked)

    def _on_cancel(self):
        """Reject and close the dialog."""

        self.__create_on_export = None
        self.__material_library = None
        self.__accepted = False
        self.close()

    def _on_export(self):
        """Accept and close the dialog."""

        # Set the options based on the current UI
        self.__create_on_export = self.__ui.create_button.isChecked()
        if self.__create_on_export:
            code = self.__ui.library_name_line_edit.text()
            if not code:
                raise Exception("Missing required Libarry name")
            path = self.__ui.library_path_line_edit.text()
            if not path:
                raise Exception("Missing required Libarry path")
            self.__material_library = {
                "project": self.__bundle.context.project,
                "code": code,
                "sg_path": path,
                "sg_type": "Material",
            }
        else:
            self.__material_library = self.__ui.libraries_combobox.currentData()
            if not self.__material_library:
                raise Exception("Missing required Libarry selection")

        # Accept and close the dialog widget
        self.__accepted = True
        self.close()
