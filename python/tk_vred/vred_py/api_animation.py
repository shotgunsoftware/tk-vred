# Copyright (c) 2023 Autodesk.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

from .base import VREDPyBase


class VREDPyAnimation(VREDPyBase):
    """VRED Python API material helper class."""

    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyAnimation, self).__init__(vred_py)

    def is_animation_clip(self, clip_node):
        """
        Return True if the clip is an Animation Clip.

        This method compatible with only VRED API v1.

        :param clip_node: The clip to check.
        :type clip_node: vrNodePtr
        """

        return clip_node.getType() == self.vred_py.clip_type()

    def get_animation_clips(self, top_level_only=True, anim_type=None):
        """
        Return all animation clip nodes.

        This method compatible with only VRED API v1.

        :param top_level_only: True will return only the top-level animation clip nodes, else
            False will return all animation clip nodes. This only works with type 'AnimClip'.
        :type top_level_only: bool
        :param anim_type: The type of animation clip nodes to return.
        :type anim_type: str

        :return: The animation clip nodes.
        :rtype: list<vrNodePtr>
        """

        # TODO support multiple animation types to accept

        anim_type = anim_type or self.vred_py.clip_type()

        top_level_nodes = self.vred_py.vrAnimWidgets.getAnimClipNodes()

        if top_level_only and anim_type == self.vred_py.clip_type():
            return top_level_nodes

        # Recurse to get all child nodes
        nodes = []
        while top_level_nodes:
            node = top_level_nodes.pop()
            node_type = node.getType()
            num_children = node.getNChildren()

            if node_type == anim_type:
                nodes.append(node)

            for i in range(num_children):
                top_level_nodes.append(node.getChild(i))

        return nodes

    def get_empty_animation_clips(self):
        """
        Return all empty animation clips.

        This method compatible with only VRED API v1.

        :return: All empty animation clips.
        :rtype: list<vrNodePtr>
        """

        def _get_empty_clips(clip, empty_clips=None):
            """
            Recursive helper function to get all empty clip nodes.

            If the current clip is empty, addi to the list of empty clips.

            :param clip: The current clip to check if empty.
            :type clip: vrNodePtr
            :param empty_clips: The list of empty clips to append to.
            :type empty_emptys: list

            :return: True if the current clip is empty, else False.
            :rtype: bool
            """

            node_type = clip.getType()
            num_children = clip.getNChildren()

            is_empty = True
            if num_children > 0:
                # Recurse on all children to determine if this clip is empty or not.
                for i in range(num_children):
                    child = clip.getChild(i)
                    if child.getType() != self.vred_py.clip_type():
                        # Child is not a clip - so this current clip is not empty.
                        # Recurse on the child, but do not alter the is_empty state of this clip, since
                        # we already know it is not empty.
                        is_empty = False
                        _get_empty_clips(child, empty_clips)
                    else:
                        # Recurse on the child clip, set the is_empty state of this clip to not empty,
                        # only if the child clip is also not empty.
                        if not _get_empty_clips(child, empty_clips):
                            is_empty = False

            if is_empty:
                if node_type == self.vred_py.clip_type():
                    # Only add the clip if it is an Animation Clip
                    empty_clips.append(clip)
                return True
            return False

        top_level_clips = self.vred_py.vrAnimWidgets.getAnimClipNodes()
        empty_clips = []
        for clip in top_level_clips:
            _get_empty_clips(clip, empty_clips)

        return empty_clips

    def get_empty_variant_set_groups(self):
        """
        Find all empty variant set groups.

        NOTE this does not work because the groups returned by getGroupedVariantSets does not
        include groups that are empty.
        """

        vset_groups = self.vred_py.vrVariantSets.getGroupedVariantSets()

        empty_groups = []
        for vset_group_name, vsets in vset_groups.items():
            if not vsets:
                empty_groups.append(vset_group_name)

        return empty_groups
