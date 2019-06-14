import sgtk
import vrFileIO
import vrScenegraph
import vrFieldAccess
import os
import vrMaterialPtr

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
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
        return_ref_list = []
        _nodeList = vrScenegraph.getAllNodes()
        for _node in _nodeList:
            _filePath = None
            if _node.hasAttachment("FileInfo"):
                _att = _node.getAttachment("FileInfo")
                _filePath = vrFieldAccess.vrFieldAccess(_att).getString("filename")
            if _filePath is not None:
                return_ref_list.append({
                        "node": _node.getName(),
                        "type": _node.getType(),
                        "path": _filePath,
                        "oldpath": _filePath
                    })
        return return_ref_list
    
    def update(self, items):
        """
        Perform replacements given a number of scene items passed from the app.
        Once a selection has been performed in the main UI and the user clicks
        the update button, this method is called.
        The items parameter is a list of dictionaries on the same form as was
        generated by the scan_scene hook above. The path key now holds
        the that each node should be updated *to* rather than the current path.
        """
        engine = self.parent.engine
        logger = engine.logger
        logger.debug("update scene")
        logger.debug(items)

        # Perform update for each item selected.
        for item in items:
            self._update_node(item)
        
    def _update_node(self, item):
        """
        Perform an update of the selected node, applies transformation and materials
        :param item: item to be updated
        """
        nodes = vrScenegraph.findNodes(item['node'])

        if len(nodes) > 0:
            node = nodes[0]
            new_node = vrFileIO.loadGeometry(item["path"])
            name, extension = os.path.splitext(os.path.basename(item["path"]))
            if name == new_node.getName():
                materials_dict = self._obtain_materials()
                self._apply_transformations(node, new_node, materials_dict)

            # Delete the node
            vrScenegraph.deleteNode(node, True)
    
    def _obtain_materials(self):
        """
        Obtain a materials list with respective nodes
        :return: list of materials
        """
        materials = vrMaterialPtr.getAllMaterials()
        materials_dict = []

        for material in materials:
            if material.getName() == 'DefaultShader':
                continue

            material_nodes = material.getNodes()

            nodes_names = [node.getName() for node in material_nodes]
            materials_dict.append({
                'name': material.getName(),
                'material': material,
                'nodes': nodes_names
            })

        return materials_dict
    
    def _apply_transformations(self, old_node, new_node, materials):
        """
        Recursive to apply transformations and materials to node and childs
        :param old_node: previous node with transformations and materials
        :param new_node: new node to apply transformations and materials
        :param materials: list of materials
        """
        if old_node.getName() == 'Surface':
            return

        vrScenegraph.copyTransformation(old_node, new_node)

        self._apply_materials(old_node, new_node, materials)

        for i in range(0, old_node.getNChildren()):
            for j in range(0, new_node.getNChildren()):
                if old_node.getChild(i).getName() == new_node.getChild(j).getName():
                    self._apply_transformations(old_node.getChild(i), new_node.getChild(j), materials)
                    break
                    
    def _apply_materials(self, old_node, new_node, materials):
        """
        Apply materials for the new node based on old node
        :param old_node: old node with materials
        :param new_node: new node to apply materials
        :param materials: materials list
        """
        materials_to_apply = []

        for material in materials:
            if old_node.getName() in material.get('nodes'):
                materials_to_apply.append(material.get('material'))

        vrScenegraph.applyMaterial([new_node, ], materials_to_apply, False, False)
