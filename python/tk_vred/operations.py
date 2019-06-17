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
import vrRenderSettings
import vrScenegraph


class VREDOperations(object):
    MESSAGES = {
        "success": "loaded successfully",
        "error": "Error loading the file(s)",
    }

    def __init__(self, engine):
        """Initialize attributes."""
        self.render_path = None
        self._engine = engine
        self.logger = self._engine.logger

    def get_current_file(self):
        """Get the current file."""
        return vrFileIO.getFileIOFilePath()

    def load_file(self, file_path):
        """Load a new file into VRED. This will reset the workspace."""
        can_load = self._engine.execute_hook_method("file_usage_hook", "file_attempt_open", path=file_path)

        if not can_load:
            return

        self.logger.debug("Loading file: {}".format(file_path))
        vrFileIO.load(file_path)
        self.prepare_render_path(file_path)

    def import_file(self, file_path):
        """Import a file into VRED. This will reset not the workspace."""
        can_import = self._engine.execute_hook_method("file_usage_hook", "file_attempt_open", path=file_path)

        if not can_import:
            return

        self.logger.debug("Importing File: {}".format(file_path))
        vrFileIO.loadGeometry(file_path)
        self.prepare_render_path(file_path)

    def reset_scene(self):
        """Resets the Scene in VRED."""
        self.logger.debug("Reset Scene")
        self._engine.current_file_closed()
        vrController.newScene()

    def save_current_file(self, file_path):
        """Tell VRED to save the out the current project as a file."""
        self.logger.debug("Save File: {}".format(file_path))

        vrFileIO.save(file_path)
        if not os.path.exists(file_path.decode('utf-8')):
            msg = "VRED Failed to save file {}".format(file_path)
            self.logger.error(msg)
            raise Exception(msg)

        allowed_to_open = self._engine.execute_hook_method("file_usage_hook", "file_attempt_open", path=file_path)
        if not allowed_to_open:
            raise Exception("Can't save file: a lock for this path already exists")

        self.prepare_render_path(file_path)

    def get_render_path(self, file_path):
        """
        Get render path when the file is selected or saved
        """
        self.logger.debug('Generating render path')
        try:
            template = self._engine.get_template_by_name(self._engine.get_setting('render_template'))
            context_fields = self._engine.context.as_template_fields(template, validate=True)
            scene_name = file_path.split(os.path.sep)[-1].replace('.vpb', '')
            context_fields.update({'scene_name': scene_name})
            path = template.apply_fields(context_fields)
            self.logger.debug('Path value: {0}'.format(path))
            if not os.path.exists(path):
                os.makedirs(path)
            path = os.path.sep.join([path, scene_name+'.png'])
            self.logger.debug('Full path value: {0}'.format(path))
        except Exception as err:
            self.logger.debug("Error generating render path: {0}".format(err))
            path = None

        return path

    def prepare_render_path(self, file_path):
        """
        Prepare render path when the file selected or saved
        """
        path = self.get_render_path(file_path)

        if path:
            self.render_path = path
            vrRenderSettings.setRenderFilename(self.render_path)

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

        return dict(message_type="information", message_code=self.MESSAGES["success"], publish_path=path,
                    is_error=False)

    def do_load(self, path):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        self.reset_scene()
        self.load_file(path)

        return dict(message_type="information", message_code=self.MESSAGES["success"], publish_path=path,
                    is_error=False)

    def get_references(self):
        """Get references."""
        self.logger.debug("Getting references")

        references = []

        for node in vrScenegraph.getAllNodes():
            path = None

            if node.hasAttachment("FileInfo"):
                path = vrFieldAccess.vrFieldAccess(node.getAttachment("FileInfo")).getString("filename")

            if path is not None:
                references.append({
                    "node": node.getName(),
                    "type": node.getType(),
                    "path": path,
                    "oldpath": path,
                })

        return references
