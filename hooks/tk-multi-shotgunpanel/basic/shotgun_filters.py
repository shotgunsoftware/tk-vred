# Copyright (c) 2020 Autdesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.
import sgtk
import pprint

HookBaseClass = sgtk.get_hook_baseclass()


class VREDShotgunFilters(HookBaseClass):
    """
    Controls the filter configuration for the Shotgun Panel.

    Via this hook, the data that is retrieved for the Shotgun Panel can be controlled.
    """

    def get_link_filters(self, sg_location, entity_type, context_project, context_user):
        """
        Returns a filter string which links the entity type up to a particular
        location.

        This hook will perform any custom handling for entity types that are not
        included in the default entity types covered by the base hook class. For any
        default entity types, the base hook implementation will be called.

        :param sg_location: Location object describing the object for
                            which associated items should be retrieved.
        :param entity_type: The entity type to link to the location.
        :param context_project: The current context project.
        :param context_user: The current context user.

        :returns: Standard SG api3 filters that can be used to retrieve
                  associated data
        """

        if sg_location.entity_type == "Playlist":
            link_filters = []

            if entity_type == "Version":
                link_filters.append(["playlists", "in", [sg_location.entity_dict]])

            elif entity_type == "Note":
                link_filters.append(["note_links", "in", [sg_location.entity_dict]])

            else:
                link_filters.append(["entity", "is", sg_location.entity_dict])

            self.logger.debug(
                "%s Resolved %s into the following sg query:\n%s"
                % (self, sg_location, pprint.pformat(link_filters))
            )

            return link_filters

        # Fallback to base hook implementation
        return super(VREDShotgunFilters, self).get_link_filters(
            sg_location, entity_type, context_project, context_user
        )
