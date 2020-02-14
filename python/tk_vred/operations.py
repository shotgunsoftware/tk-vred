# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import vrController
import vrFileIO
import vrFieldAccess
import vrFileDialog
import vrRenderSettings
import vrScenegraph

from tank_vendor import six


class VREDOperations(object):
    MESSAGES = {
        "success": "loaded successfully",
        "error": "Error loading the file(s)",
    }

    def __init__(self, engine):
        """Initialize attributes."""
        self._engine = engine
        self.logger = self._engine.logger

    def get_current_file(self):
        """Get the current file."""
        return vrFileIO.getFileIOFilePath()

    def load_file(self, file_path):
        """Load a new file into VRED. This will reset the workspace."""
        can_load = self._engine.execute_hook_method(
            "file_usage_hook", "file_attempt_open", path=file_path
        )

        if not can_load:
            return

        self.logger.debug("Loading file: {}".format(file_path))
        vrFileIO.load(file_path)
        self.set_render_path(file_path)

    def import_file(self, file_path):
        """Import a file into VRED. This will reset not the workspace."""
        self.logger.debug("Importing File: {}".format(file_path))
        vrFileIO.loadGeometry(file_path)

    def reset_scene(self):
        """Resets the Scene in VRED."""
        self.logger.debug("Reset Scene")
        self._engine.current_file_closed()
        vrController.newScene()

    def save_current_file(self, file_path):
        """Tell VRED to save the out the current project as a file."""
        self.logger.debug("Save File: {}".format(file_path))

        vrFileIO.save(file_path)

        if not os.path.exists(six.ensure_str(str(file_path))):
            msg = "VRED Failed to save file {}".format(file_path)
            self.logger.error(msg)
            raise Exception(msg)

        allowed_to_open = self._engine.execute_hook_method(
            "file_usage_hook", "file_attempt_open", path=file_path
        )
        if not allowed_to_open:
            raise Exception("Can't save file: a lock for this path already exists")

        self.set_render_path(file_path)

    def get_render_path(self):
        """
        Get render path when the file is selected or saved
        """
        return vrRenderSettings.getRenderFilename()

    def set_render_path(self, file_path=None):
        """
        Prepare render path when the file selected or saved
        """
        render_template = self._engine.get_template_by_name(
            self._engine.get_setting("render_template")
        )
        if not render_template:
            self.logger.debug("Couldn't get render template from engine settings")
            return

        if file_path is None:
            file_path = self.get_current_file()
            if file_path is None:
                self.logger.debug("Couldn't get current scene path")
                return

        work_template = self._engine.sgtk.template_from_path(file_path)
        if not work_template:
            self.logger.debug(
                "Couldn't find a template which match the current scene path"
            )
            return
        template_fields = work_template.get_fields(file_path)

        # update the template fields with the context ones to be sure to have all the required fields
        context_fields = self._engine.context.as_template_fields(render_template)
        for k in context_fields:
            if k not in template_fields.keys():
                template_fields[k] = context_fields[k]

        missing_keys = render_template.missing_keys(template_fields, skip_defaults=True)
        if missing_keys:
            self.logger.debug(
                "Couldn't resolve render path from template: missing keys %s"
                % str(missing_keys)
            )
            return

        render_path = render_template.apply_fields(template_fields)

        # be sure the render folder is created
        render_folder = os.path.dirname(render_path)
        if not os.path.isdir(render_folder):
            os.makedirs(render_folder)

        vrRenderSettings.setRenderFilename(render_path)

    def save_before_publish(self, path):
        """
        Save the scene before publish in order to get the latest changes
        """
        self.save_current_file(path)

    def save_after_publish(self, path):
        """
        Save the scene after publish in order to get a new version in the workfiles folder
        """
        self.save_current_file(path)

    def create_reference(self, path):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        self.load_file([path], vrScenegraph.getRootNode(), False, False)

    def do_import(self, path):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        self.import_file(path)

        return dict(
            message_type="information",
            message_code=self.MESSAGES["success"],
            publish_path=path,
            is_error=False,
        )

    def do_load(self, path):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        self.reset_scene()
        self.load_file(path)

        return dict(
            message_type="information",
            message_code=self.MESSAGES["success"],
            publish_path=path,
            is_error=False,
        )

    def get_references(self):
        """Get references."""
        self.logger.debug("Getting references")

        references = []

        for node in vrScenegraph.getAllNodes():
            path = None

            if node.hasAttachment("FileInfo"):
                path = vrFieldAccess.vrFieldAccess(
                    node.getAttachment("FileInfo")
                ).getString("filename")

            if path is not None:
                references.append(
                    {
                        "node": node.getName(),
                        "type": node.getType(),
                        "path": path,
                        "oldpath": path,
                    }
                )

        return references

    def open_save_as_dialog(self):
        """
        Launch a Qt file browser to select a file, then save the supplied
        project to that path.
        """
        path = vrFileDialog.getSaveFileName(
            caption="Save As",
            filename="",
            filter=[
                "VRED Essentials Project Binary (*.vpe)",
                "VRED Project Binary (*.vpb)",
                "VRED Project File (*.vpf)",
            ],
        )

        if path:
            self.save_current_file(path)

    @staticmethod
    def get_geometry_nodes():
        """
        Returns all the geometry nodes of the current VRED scene

        :return: A list of VRED geometry nodes
        :rtype: list
        """

        root_node = vrScenegraph.getRootNode()

        node_list = []
        for n in range(0, root_node.getNChildren()):

            child_node = root_node.getChild(n)
            if child_node.getType() != "Geometry":
                continue

            node_list.append(child_node)

        return node_list

    def get_geometry_node_by_id(self, node_id):
        """
        Get the geometry node given it id

        :param node_id: ID of the node we want to find
        :return: The VRED geometry node
        :rtype: vrNodePtr
        """

        geometry_nodes = self.get_geometry_nodes()

        for geometry_node in geometry_nodes:
            geometry_node_id = geometry_node.fields().getID()
            if geometry_node_id == node_id:
                return geometry_node

        return None

    def export_geometry(self, geometry_node, path):
        """
        Export geometry node to an osb file

        :param geometry_node: Geometry node to export
        :param path: Path to export the geometry
        """

        if geometry_node.getType() != "Geometry":
            raise ValueError("Couldn't export geometry node: bad node type")

        vrFileIO.saveGeometry(geometry_node, path)
