# Copyright (c) 2020 Shotgun Software Inc.
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

HookClass = sgtk.get_hook_baseclass()


class BreakdownSceneOperation(HookClass):
    """
    Breakdown operations for VRED.

    This implementation handles detection of VRED source references.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the hook."""

        super(BreakdownSceneOperation, self).__init__(*args, **kwargs)

        self.vredpy = self.parent.engine.vredpy

    def scan_scene(self):
        """
        The scan scene method is executed once at startup and its purpose is
        to analyze the current scene and return a list of references that are
        to be potentially operated on.
        The return data structure is a list of dictionaries. Each scene reference
        that is returned should be represented by a dictionary with three keys:
        - "node": The name of the 'node' that is to be operated on. Most DCCs have
          a concept of a node, path or some other way to address a particular
          object in the scene.
        - "type": The object type that this is. This is later passed to the
          update method so that it knows how to handle the object.
        - "path": Path on disk to the referenced object.
        Toolkit will scan the list of items, see if any of the objects matches
        any templates and try to determine if there is a more recent version
        available. Any such versions are then displayed in the UI as out of date.
        """

        refs = []

        for r in self.vredpy.vrReferenceService.getSceneReferences():

            # we only want to keep the top references
            has_parent = self.vredpy.vrReferenceService.getParentReferences(r)
            if has_parent:
                continue

            if r.hasSourceReference():
                node_type = "source_reference"
                path = r.getSourcePath()
            elif r.hasSmartReference():
                node_type = "smart_reference"
                path = r.getSmartPath()
            else:
                node_type = "reference"
                path = None

            if path:
                refs.append({"node": r.getName(), "type": node_type, "path": path})

        return refs

    def update(self, items):
        """
        Perform replacements given a number of scene items passed from the app.
        Once a selection has been performed in the main UI and the user clicks
        the update button, this method is called.
        The items parameter is a list of dictionaries on the same form as was
        generated by the scan_scene hook above. The path key now holds
        the that each node should be updated *to* rather than the current path.
        """

        for item in items:

            node_name = item["node"]
            node_type = item["type"]
            path = item["path"]

            ref_node = self.get_reference_by_name(node_name)
            if not ref_node:
                self.logger.error(
                    "Couldn't get reference node named {}".format(node_name)
                )
                return

            new_node_name = os.path.splitext(os.path.basename(path))[0]

            if node_type == "source_reference":
                ref_node.setSourcePath(path)
                ref_node.loadSourceReference()
                ref_node.setName(new_node_name)
            elif node_type == "smart_reference":
                ref_node.setSmartPath(path)
                self.vredpy.vrReferenceService.reimportSmartReferences(
                    [ref_node]
                )  # noqa


    def get_reference_by_name(self, ref_name):
        """
        Get a reference node from its name.

        :param ref_name: Name of the reference we want to get the associated node from
        :returns: The reference node associated to the reference name
        """

        ref_list = self.vredpy.vrReferenceService.getSceneReferences()
        for r in ref_list:
            if r.getName() == ref_name:
                return r
        return None
