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
import subprocess
import sys

import sgtk
import vrFileIO

HookBaseClass = sgtk.get_hook_baseclass()


class VREDFbxPublishPlugin(HookBaseClass):
    """
    Plugin for exporting an FBX file from VRED to finally import it into a new Maya scene.
    """

    @property
    def icon(self):
        """
        Path to an png icon on disk
        """
        return os.path.join(self.disk_location, "icons", "maya.png")

    @property
    def name(self):
        """
        One line display name describing the plugin
        """
        return "Publish FBX to Shotgun"

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        loader_url = "https://support.shotgunsoftware.com/hc/en-us/articles/219033078"

        return """
        Exports an FBX file from VRED and publishes it to Shotgun. A <b>Publish</b> entry will be
        created in Shotgun which will include a reference to the file's current
        path on disk. Other users will be able to access the published file via
        the <b><a href='%s'>Loader</a></b> so long as they have access to
        the file's location on disk.

        <h3>File versioning</h3>
        The <code>version</code> field of the resulting <b>Publish</b> in
        Shotgun will also reflect the version number identified in the filename.
        The basic worklfow recognizes the following version formats by default:

        <ul>
        <li><code>filename.v###.ext</code></li>
        <li><code>filename_v###.ext</code></li>
        <li><code>filename-v###.ext</code></li>
        </ul>

        <br><br><i>NOTE: any amount of version number padding is supported.</i>
        """ % (
            loader_url,
        )

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["vred.session"]

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """

        path = item.properties.get("path")
        fbx_path = "{}.fbx".format(os.path.splitext(path)[0])

        item.local_properties.path = fbx_path
        item.local_properties.publish_path = fbx_path

        return super(VREDFbxPublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        vred_export_script = os.path.join(
            self.disk_location, "scripts", "export_fbx_from_vred.py"
        )

        # get the path to create and publish
        path = vrFileIO.getFileIOFilePath()

        # need to recompute the path in case the vpb file has been versioned in between
        publish_path = item.properties.path
        fbx_path = "{}.fbx".format(os.path.splitext(path)[0])
        item.local_properties.path = fbx_path
        item.local_properties.publish_path = fbx_path

        if not os.path.isfile(fbx_path):
            self.logger.info("Exporting FBX file from VRED...")
            vred_cmd = [
                sys.executable,
                "-console",
                "-nogui",
                "-postpython",
                "\"import sys; sys.argv=[r'{}']; execfile(r'{}')\"".format(
                    fbx_path, vred_export_script
                ),
                path,
            ]
            try:
                subprocess.call(" ".join(vred_cmd))
            except Exception as e:
                self.logger.error("Couldn't perform FBX export: {}".format(e))
                return
        else:
            self.logger.warning("FBX file already exists on disk")

        # Now that the path has been generated, hand it off to the
        super(VREDFbxPublishPlugin, self).publish(settings, item)

    def finalize(self, settings, item):
        """
        Execute the finalization pass. This pass executes once all the publish
        tasks have completed, and can for example be used to version up files.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        self.logger.info("FBX file has been exported and published to Shotgun!")

    def get_publish_type(self, settings, item):
        """
        Get a publish type for the supplied settings and item.

        :param settings: This plugin instance's configured settings
        :param item: The item to determine the publish type for

        :return: A publish type or None if one could not be found.
        """

        # publish type explicitly set or defined on the item
        publish_type = item.get_property("publish_type")
        if publish_type:
            return publish_type

        # fall back to the path info hook logic
        publisher = self.parent
        path = item.get_property("path")

        # get the publish path components
        path_info = publisher.util.get_file_path_components(path)

        # determine the publish type
        extension = path_info["extension"]

        # ensure lowercase and no dot
        if extension:
            extension = extension.lstrip(".").lower()

            for type_def in settings["File Types"].value:

                publish_type = type_def[0]
                file_extensions = type_def[1:]

                if extension in file_extensions:
                    # found a matching type in settings. use it!
                    return publish_type

        # --- no pre-defined publish type found...

        if extension:
            # publish type is based on extension
            publish_type = "%s File" % extension.capitalize()
        else:
            # no extension, assume it is a folder
            publish_type = "Folder"

        return publish_type
