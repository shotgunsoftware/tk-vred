# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSessionSceneCollector(HookBaseClass):
    """
    Collector that operates on the VRED session for scene items only.

    This collector ignores the VRED session materials.
    
    Should inherit from the base VREDSessionCollector.
    """

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current scene open in a DCC and parents a subtree of items
        under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """

        # create an item representing the current VRED session
        item = self.collect_current_vred_session(settings, parent_item)

        # look at the render folder to find rendered images on disk
        self.collect_rendered_images(item)
