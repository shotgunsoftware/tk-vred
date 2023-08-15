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


class VREDPyNode(VREDPyBase):
    """VRED Python API utility class."""

    def __init__(self, vred_py):
        """Initialize"""
        super(VREDPyNode, self).__init__(vred_py)

    def get_root_node(self, api_version=None):
        """
        Return the root node.

        Use the specified api version to get the root node.

        :param api_version: The VRED API version used to get the root node.
        :type api_version: str (v1|v2)
        """

        api_version = api_version or self.vred_py.v1()
        self.vred_py.check_api_version(api_version)

        if api_version == self.vred_py.v1():
            return self.vred_py.vrScenegraph.getRootNode()
        else:
            try:
                return self.vred_py.vrNodeService.getRootNode()
            except AttributeError:
                raise self.vred_py.VREDPyNotSupportedError(
                    "vrNodeService.getRootNode() function not supported in current version of VRED."
                )

    def is_geometry_node(self, node):
        """
        Return True if the node is a geometry node.

        Do not include surface nodes.

        This method compatible with only VRED API v2.

        :param node: The node to check.
        :type node: vrNodePtr | vrdNode

        :return: True if the node is a geometry node, else False.
        :rtype: bool
        """

        if isinstance(node, self.vred_py.vrdSurfaceNode):
            # Do not include surface nodes
            return False

        return isinstance(node, self.vred_py.vrdGeometryNode)

    def get_nodes(self, items, api_version=None):
        """
        Return a list of node objects.

        :param items: The list of items to convert to nodes. This list may contain one of:
            str - the node name
            int - the node id
            dict - the node data with required key "id"
            vrNodePtr - the node object (v1)
            vrdNode - the node object (v2)
        :type items: list
        :param api_version: The VRED API version to use for conversion. For v1, nodes of type
            vrNodePtr will be returned. For v2, nodes of type vrdNode will be returned.
        :type api_version: str

        :return: The list of nodes converted from the given items.
        :rtype: list<vrNodePtr> | list<vrdNode>
        """

        api_version = api_version or self.vred_py.v1()
        self.vred_py.check_api_version(api_version)

        nodes = []
        if not items:
            return nodes

        if not isinstance(items, (list, tuple)):
            items = [items]

        for item in items:
            if isinstance(item, dict):
                item = item.get("id")

            node = None
            if isinstance(item, self.vred_py.vrNodePtr.vrNodePtr):
                if api_version == self.vred_py.v1():
                    node = item
                else:
                    node = self.vred_py.vrNodeService.getNodeFromId(item.getID())
            elif isinstance(item, self.vred_py.vrdNode):
                if api_version == self.vred_py.v1():
                    node = self.vred_py.vrNodePtr.toNode(item.getObjcetId())
                else:
                    node = item
            elif isinstance(item, int):
                if api_version == self.vred_py.v1():
                    node = self.vred_py.vrNodePtr.toNode(item)
                else:
                    node = self.vred_py.vrNodeService.getNodeFromId(item)
            else:
                try:
                    if api_version == self.vred_py.v1():
                        node = self.vred_py.vrScenegraph.findNode(item)
                    else:
                        node = self.vred_py.vrNodeService.findNode(item)
                except Exception:
                    pass

            if node:
                nodes.append(node)
            else:
                raise self.vred_py.VREDPyError(
                    "Failed to convert {} to node".format(item)
                )

        return nodes

    def get_geometry_nodes(self, root_node=None, has_mat_uvs=None, has_light_uvs=None):
        """
        Return all geometry nodes in the subtree of the root_node.

        Nodes within the subtree of the given root node will be checked. If no root node is given
        then the top root node will be used.

        :param root_node: The subtree of this root node will be checked. If None, the scene
            graph root node will be used.
        :type root_node: vrdNode

        :return: The list of geometry nodes.
        :rtype: list<vrdNode>
        """

        def _get_geometry_nodes(node, result, has_mat_uvs=None, has_light_uvs=None):
            """
            Recursive helper function to get geoemtry nodes.

            :param node: The current node.
            :type node: vrdNode
            :param has_mat_uvs: ...
            """

            if not node:
                return

            is_geom = self.is_geometry_node(node)

            if is_geom:
                if has_mat_uvs is None and has_light_uvs is None:
                    # Add geometry regardless of material/light UVs
                    result.append(node)
                elif has_mat_uvs is None and has_light_uvs is None:
                    # Add geometry based on both material/light UVs
                    if (
                        node.hasUVSet(self.vred_py.vrUVTypes.MaterialUVSet)
                        == has_mat_uvs
                        and node.hasUVSet(self.vred_py.vrUVTypes.LightmapUVSet)
                        == has_light_uvs
                    ):
                        result.append(node)
                elif has_mat_uvs is None:
                    # Add only geometry based on light UVs, ignore material UVs
                    if (
                        node.hasUVSet(self.vred_py.vrUVTypes.LightmapUVSet)
                        == has_light_uvs
                    ):
                        result.append(node)
                elif has_light_uvs is None:
                    # Add only geometry based on material UVs, ignore light UVs
                    if (
                        node.hasUVSet(self.vred_py.vrUVTypes.MaterialUVSet)
                        == has_mat_uvs
                    ):
                        result.append(node)

            for child in node.getChildren():
                _get_geometry_nodes(
                    child, result, has_mat_uvs=has_mat_uvs, has_light_uvs=has_light_uvs
                )

        root_node = root_node or self.get_root_node(api_version=self.vred_py.v2())
        nodes = []
        _get_geometry_nodes(
            root_node, nodes, has_mat_uvs=has_mat_uvs, has_light_uvs=has_light_uvs
        )
        return nodes

    def get_hidden_nodes(
        self, root_node=None, ignore_node_types=None, api_version=None
    ):
        """
        Return a list of the hidden nodes in the scene graph.

        If a node is hidden, all of its children are hidden but the node's children will
        not be included in the list of hidden nodes returned.

        :param root_node: The node to check subtree only for hidden nodes. If None, then
            the scene graph root node will be used to check all nodes.
        :param root_node: vrNodePtr | vrdNode
        :param ignore_node_types: A list of node types to exclude from the result. All children
            of these types of nodes will also be ignored (regardless of the child node type).
            This list of types must correspond to the `api_version`.
        :type ignore_node_types: list<str> (for v1) | list<class> (for v2)
        :param api_version: The VRED API version used to retrieve and return hidden node.
        :type api_version: str
        """

        api_version = api_version or self.vred_py.v1()
        self.vred_py.check_api_version(api_version)

        ignore_node_types = ignore_node_types or []

        if root_node is None:
            nodes = [self.get_root_node(api_version=api_version)]
        else:
            nodes = [root_node]

        hidden = []
        while nodes:
            node = nodes.pop()

            if isinstance(node, self.vred_py.vrNodePtr.vrNodePtr):
                # v1
                if node.getType() in ignore_node_types:
                    continue

                if not node.getActive():
                    hidden.append(node)
                else:
                    # Only check children if the parent is not hidden
                    for i in range(node.getNChildren()):
                        nodes.append(node.getChild(i))
            else:
                # v2
                if type(node) in ignore_node_types:
                    continue

                if not node.isVisible():
                    hidden.append(node)
                else:
                    # Only check children if the parent is not hidden
                    for child in node.getChildren():
                        nodes.append(child)

        return hidden

    def delete_nodes(self, nodes, force=False):
        """
        Delete the given nodes.

        :param nodes: The nodes to delete. The elements in the list must be uniform.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        :param force: Applicable for v1 only. Force delete if true, else undeleteable nodes are
            also deleted. Default is false.
        :type force: bool
        """

        if not nodes:
            return

        # Check the first node to detect which api version to use to delete.
        # Assumes the list has uniform elements
        if isinstance(nodes[0], self.vred_py.vrNodePtr.vrNodePtr):
            self.vred_py.vrScenegraph.deleteNodes(nodes, force)

        elif isinstance(nodes[0], self.vred_py.vrdNode):
            self.vred_py.vrNodeService.removeNodes(nodes)

        else:
            raise self.vred_py.VREDPyError("Not a node {}".format(nodes[0]))

    def set_to_b_side(self, nodes, b_side=True):
        """
        Set the given nodes to the B-Side.

        This method handles a list of v1 or v2 VRED APi nodes.

        :param nodes: THe list of nodes to set.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        :param b_side: True to set to B-Side.
        :type b_side:bool
        """

        if not nodes:
            return

        for node in nodes:
            # Check if we're handling a v1 or v2 node object
            if isinstance(node, self.vred_py.vrNodePtr.vrNodePtr):
                self.vred_py.vrNodeUtils.setToBSide(node, b_side)
            elif isinstance(node, self.vred_py.vrdGeometryNode):
                node.setToBSide(b_side)
            else:
                raise self.vred_py.VREDPyError("Not a geometry node {}".format(node))

    def show_nodes(self, nodes):
        """
        Show the nodes.

        :param nodes: The nodes to show. The elements in the list must be uniform.
        :type nodes: list<vrNodePtr> | list<vrdNode>
        """

        if not nodes:
            return

        # Check the first node to detect which api version to use to delete.
        # Assumes the list has uniform elements
        if isinstance(nodes[0], self.vred_py.vrNodePtr.vrNodePtr):
            self.vred_py.vrScenegraph.showNodes(nodes)

        elif isinstance(nodes[0], self.vred_py.vrdNode):
            for node in nodes:
                node.setVisibilityFlag(True)

        else:
            raise self.vred_py.VREDPyError("Not a node {}".format(nodes[0]))

    def group_nodes(self, nodes):
        """
        Group the given nodes.

        Group the nodes by selecting all nodes, then calling the group selection method, and
        then finally deselecting all nodes.

        NOTE that this will create the group in the scene graph UI and select the text to edit
        the name of the group created.

        This method compatible with only VRED API v1.

        :param nodes: The nodes to group.
        :type nodes: list<vrNodePtr>
        """

        select = True
        self.vred_py.vrScenegraph.selectNodes(nodes, select)
        self.vred_py.vrScenegraph.groupSelection()
        self.vred_py.vrScenegraph.deselectAll()
