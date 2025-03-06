# Copyright (c) 2024 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.


import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDSceneOperationsHook(HookBaseClass):
    """Hook class that sets up VRED events to update the Data Validation App."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__scene_event_callbacks = []

    def register_scene_events(self, reset_callback, change_callback):
        """
        Register events for when the scene has changed.

        The function reset_callback provided will reset the current Data Validation App,
        when called. The function change_callback provided will display a warning in the
        Data Validation App UI that the scene has changed and the current validatino state
        may be stale.

        :param reset_callback: Callback function to reset the Data Validation App.
        :type reset_callback: callable
        :param change_callback: Callback function to handle the changes to the scene.
        :type change_callback: callable
        """

        if self.__scene_event_callbacks:
            return

        vredpy = self.parent.engine.vredpy

        # Register VRED scene events. Wrap in try-except to avoid failing if the event is not
        # supported by the current VRED version.
        try:
            self.__scene_event_callbacks.append(
                (vredpy.vrFileIOService.newScene, reset_callback)
            )
        except AttributeError as e:
            self.parent.logger.warning(
                f"Data Validation failed to register scene event: {e}"
            )

        try:
            self.__scene_event_callbacks.append(
                (
                    vredpy.vrScenegraphService.scenegraphChanged,
                    lambda change_type: self.__handle_scene_graph_changed_event(
                        change_type, change_callback
                    ),
                )
            )
        except AttributeError as e:
            self.parent.logger.warning(
                f"Data Validation failed to register scene event: {e}"
            )

        try:
            self.__scene_event_callbacks.append(
                (
                    vredpy.vrNodeService.nodesAdded,
                    lambda nodes: change_callback(text="Nodes added"),
                )
            )
        except AttributeError as e:
            self.parent.logger.warning(
                f"Data Validation failed to register scene event: {e}"
            )

        try:
            self.__scene_event_callbacks.append(
                (
                    vredpy.vrNodeService.nodesRemoved,
                    lambda nodes: change_callback(text="Nodes removed"),
                )
            )
        except AttributeError as e:
            self.parent.logger.warning(
                f"Data Validation failed to register scene event: {e}"
            )

        try:
            self.__scene_event_callbacks.append(
                (
                    vredpy.vrMaterialService.materialsChanged,
                    lambda: change_callback(text="Materials changed"),
                )
            )
        except AttributeError as e:
            self.parent.logger.warning(
                f"Data Validation failed to register scene event: {e}"
            )

        try:
            self.__scene_event_callbacks.append(
                (
                    vredpy.vrReferenceService.referencesChanged,
                    lambda nodes: change_callback(text="References changed"),
                )
            )
        except AttributeError as e:
            self.parent.logger.warning(
                f"Data Validation failed to register scene event: {e}"
            )

        for vred_signal, callback in self.__scene_event_callbacks:
            vred_signal.connect(callback)

    def unregister_scene_events(self):
        """Unregister the scene events."""

        for vred_signal, callback in self.__scene_event_callbacks:
            vred_signal.disconnect(callback)

        self.__scene_event_callbacks = []

    def __handle_scene_graph_changed_event(self, change_type, scene_change_callback):
        """
        Intermediate callback handler the VRED scene graph changed event.

        :param change_type: The VRED scene graph change type.
        :type change_type: vrScenegraphTypes.ChangeFlag
        :param scene_change_callback: The callback to execute.
        :type scene_change_callback: function
        """

        vredpy = self.parent.engine.vredpy

        if change_type == vredpy.vrScenegraphTypes.ChangeFlag.GraphChanged:
            warning_text = "Graph changed"
        elif change_type == vredpy.vrScenegraphTypes.ChangeFlag.MetadataChanged:
            warning_text = "Metadata changed"
        elif change_type == vredpy.vrScenegraphTypes.ChangeFlag.NodeChanged:
            warning_text = "Node changed"
        else:
            warning_text = None

        scene_change_callback(text=warning_text)
