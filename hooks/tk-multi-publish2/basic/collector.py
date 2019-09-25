# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import sgtk
import vrScenegraph

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionCollector(HookBaseClass):
    """
    Collector that operates on the vred session. Should inherit from the basic
    collector hook.
    """
    @property
    def settings(self):
        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """

        # grab any base class settings
        collector_settings = super(VREDSessionCollector, self).settings or {}

        # settings specific to this collector
        vred_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                               "correspond to a template defined in "
                               "templates.yml. If configured, is made available"
                               "to publish plugins via the collected item's "
                               "properties. ",
            },
        }

        # update the base settings with these settings
        collector_settings.update(vred_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current scene open in a DCC and parents a subtree of items
        under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """
        publisher = self.parent
        operations = publisher.engine.operations

        # get the path to the current file
        path = operations.get_current_file()

        # create an item representing the current VRED session
        item = self.collect_current_vred_session(settings, parent_item)

        self._collect_session_renders(item)
        self._collect_geometries(item, path)

    def collect_current_vred_session(self, settings, parent_item):
        """
        Creates an item that represents the current VRED session.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance

        :returns: Item of type vred.session
        """

        publisher = self.parent
        operations = publisher.engine.operations

        # get the path to the current file
        path = operations.get_current_file()

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current VRED Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "vred.session",
            "VRED Session",
            display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "vred.png"
        )
        session_item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")
        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value)

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template
            self.logger.debug("Work template defined for VRED collection.")

        self.logger.info("Collected current VRED scene")

        # Need to store the path on properties to backward compatibility
        # TODO: clean LMV plugin to remove the path query
        session_item.properties["path"] = path

        return session_item

    def _collect_session_renders(self, parent_item):
        """
        Creates items for session renders to be exported.

        :param parent_item: Parent Item instance
        """
        publisher = self.parent
        engine = publisher.engine
        base_dir = os.path.dirname(engine.operations.get_render_path())
        files = os.listdir(base_dir)

        if not files:
            return

        for file_name in files:
            path = os.path.join(base_dir, file_name)
            item = super(VREDSessionCollector, self)._collect_file(parent_item, path)
            item.type = "vred.session.renders"
            item.name = file_name
            item.display_type = "VRED Session Render"
    
    def _collect_geometries(self, parent_item, parent_path):
        """
        Creates items for osb to be exported.

        :param parent_item: Parent Item instance
        :param parent_path: Parent path
        """

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "publish_vred_osb.png")
        
        rootNode = vrScenegraph.getRootNode()
        for n in range(0, rootNode.getNChildren()):
            childNode = rootNode.getChild(n)

            if childNode.getType() != "Geometry":
                continue

            fieldAcc = childNode.fields()
            item = super(VREDSessionCollector, self)._collect_file(parent_item, parent_path)
            item.name = childNode.getName()
            item.type = 'vred.session.geometry'
            item.display_type = 'Geometry Node'
            item.properties['node_id'] = fieldAcc.getID()
            item.set_icon_from_path(icon_path)
