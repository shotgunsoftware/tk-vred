# Copyright (c) 2015 Shotgun Software Inc.
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


class VREDShotgunFields(HookBaseClass):
    """
    Controls the field configuration for the Shotgun Panel.

    Via this hook, the visual appearance of the Shotgun Panel can be controlled.
    When the shotgun panel displays a UI element, it will call this hook
    in order to determine how that particular object should be formatted.
    """

    def get_main_view_definition(self, entity_type):
        """
        Controls the rendering of items in the various item listings.

        Should return a dictionary with the following keys:

        - top_left: content to display in the top left area of the item
        - top_right: content to display in the top right area of the item
        - body: content to display in the main area of the item

        Base hook method is overriden to support Playlist entity type.

        :param entity_type: Shotgun entity type to provide a template for
        :returns: Dictionary containing template strings
        """

        if entity_type == "Playlist":
            return {
                "title": "{type} {code}",
                "body": """
                        Updated By: {updated_by} on {updated_at}<br>
                        Description: {description}
                        """,
            }

        return super(VREDShotgunFields, self).get_main_view_definition(entity_type)

    def get_entity_tabs_definition(self, entity_type, shotgun_globals):
        """
        Define which tabs are shown in the Shotgun Panel for an item of
        a given entity type.

        Override the base hook method to implement custom handling for
        non-default entity types, e.g. Playlist.

        :param entity_type: Shotgun entity type to provide tab info for.
        :returns: Dictionary
        """

        values = super(VREDShotgunFields, self).get_entity_tabs_definition(
            entity_type, shotgun_globals
        )

        # Custom handling for non-default entity types
        if entity_type == "Playlist":
            values["publishes"]["enabled"] = False
            values["tasks"]["enabled"] = False
            values["versions"]["tooltip"] = "Double-click to load Version for review"

        return values

    def get_entity_default_tab(self, entity_type):
        """
        Return the name of the default tab for this entity type. Tab name should
        be one of the defined tab names in tk-multi-shotgunpanel AppDialog.ENTITY_TABS.

        Override base hook to handle non-default entity types.
        """

        if entity_type == "Playlist":
            return "versions"

        return super(VREDShotgunFields, self).get_entity_default_tab(entity_type)
