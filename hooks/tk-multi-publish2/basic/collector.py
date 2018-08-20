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
import vrFieldAccess

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionCollector(HookBaseClass):
    """
    Collector that operates on the vred session. Should inherit from the basic
    collector hook.
    """
    @property
    def settings(self):
        collector_settings = super(VREDSessionCollector, self).settings or {}
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
        engine = publisher.engine
        path = engine.get_current_file()

        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current VRED Session"

        session_item = super(VREDSessionCollector, self)._collect_file(parent_item, path, frame_sequence=True)

        # get the icon path to display for this item
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "vred.png"
        )
        session_item.set_icon_from_path(icon_path)
        session_item.type = "vred.session"
        session_item.name = display_name
        session_item.display_type = "VRED Session"

        self._collect_session_renders(session_item)
        self._collect_geometries(session_item, path)

    def _collect_session_renders(self, parent_item):
        """
        Creates items for session renders to be exported.

        :param parent_item: Parent Item instance
        """
        publisher = self.parent
        engine = publisher.engine
        base_dir = os.path.dirname(engine.get_render_path(parent_item.properties.get("path")))
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
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "publish_vred_osb.png"
        )
        
        rootNode = vrScenegraph.getRootNode()
        for n in range(0, rootNode.getNChildren()):
            childNode = rootNode.getChild(n)
            if childNode.getType() == "Geometry":
                # Add node Info
                fieldAcc = childNode.fields()
                item = super(VREDSessionCollector, self)._collect_file(parent_item, parent_path)
                item.name = childNode.getName()
                item.type = 'vred.session.geometry'
                item.display_type = 'Geometry Node'
                item.properties['node_id'] = fieldAcc.getID()
                item.set_icon_from_path(icon_path)
