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
import errno
import shutil
import subprocess
import tempfile

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class VREDPublishLMVFilePlugin(HookBaseClass):
    TMPDIR = None

    @property
    def vred_bin_dir(self):
        return os.path.dirname(os.getenv("TK_VRED_EXECPATH"))

    def _get_translator(self):
        """Get viewing-vpb-lmv.exe file path"""
        return os.path.join(self.vred_bin_dir, "LMV", "viewing-vpb-lmv.exe")

    def _is_translator_installed(self):
        return os.path.exists(self._get_translator())

    def _get_thumbnail_extractor(self):
        """Get extractMetaData.exe file path"""
        return os.path.join(self.vred_bin_dir, "extractMetaData.exe")

    @property
    def settings(self):
        base_settings = super(VREDPublishLMVFilePlugin, self).settings or {}

        # settings specific to this class
        publish_settings = {
            "VRED LMV Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }

        base_settings.update(publish_settings)

        work_settings = {
            "VRED LMV Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            }
        }

        base_settings.update(work_settings)

        return base_settings

    def validate(self, settings, item):
        publisher = self.parent

        publish_template_setting = settings.get("VRED LMV Publish Template")
        publish_template = publisher.engine.get_template_by_name(
            publish_template_setting.value
        )

        if not publish_template:
            return False

        item.properties["vred_publish_template"] = publish_template

        work_template_setting = settings.get("VRED LMV Work Template")
        work_template = publisher.engine.get_template_by_name(
            work_template_setting.value
        )

        if not work_template:
            return False

        item.properties["vred_work_template"] = work_template

        return True

    def accept(self, settings, item):
        base_accept = super(VREDPublishLMVFilePlugin, self).accept(settings, item)

        base_accept.update(
            {"accepted": True, "visible": True, "checked": True, "enabled": False}
        )
        return base_accept

    @staticmethod
    def makedirs(path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def _translate_file(self, source_path, item):
        engine_logger = self.parent.engine.logger

        self.logger.info("Starting the translation")

        # PublishedFile id
        publish_id = item.properties.sg_publish_data["id"]

        # Version id
        version_id = item.properties.sg_version_data["id"]

        # Get translator
        translator = self._get_translator()

        # Temporal dir
        self.TMPDIR = tempfile.mkdtemp(prefix="sgtk_")

        # VRED file name
        file_name = os.path.basename(source_path)

        # JSON file
        self.logger.info("Creating JSON file")
        index_path = os.path.join(self.TMPDIR, "index.json")
        with open(index_path, "w") as _:
            pass

        # Copy source file locally
        self.logger.info("Copy file {} locally.".format(source_path))
        source_path_temporal = os.path.join(self.TMPDIR, file_name)
        shutil.copyfile(source_path, source_path_temporal)

        # Execute translation command
        command = [translator, index_path, source_path_temporal]

        self.logger.info("LMV execution: {}".format(" ".join(command)))

        try:
            engine_logger.debug("Command for translation: {}".format(" ".join(command)))
            subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True)
        except Exception as e:
            engine_logger.debug("Command for translation failed: {}".format(e))
            self.logger.error("Error ocurred {!r}".format(e))
            raise
        else:
            engine_logger.debug("Translation ran sucessfully")

        output_directory = os.path.join(self.TMPDIR, "output")

        # Rename svf file
        name, _ = os.path.splitext(file_name)
        svf_file_old_name = "{}.svf".format(name)
        svf_file_new_name = "{}.svf".format(version_id)
        source_file = os.path.join(output_directory, "1", svf_file_old_name)
        target_file = os.path.join(output_directory, "1", svf_file_new_name)
        os.rename(source_file, target_file)

        base_name = os.path.join(self.TMPDIR, "{}".format(version_id))

        self.logger.info("LMV files copied.")

        thumbnail_data = self._get_thumbnail_data(item, source_path_temporal)
        if thumbnail_data:
            images_path_temporal = os.path.join(output_directory, "images")

            if not os.path.exists(images_path_temporal):
                self.makedirs(images_path_temporal)

            thumb_big_filename = "{}.jpg".format(version_id)
            thumb_small_filename = "{}_thumb.jpg".format(version_id)
            thumb_big_path = os.path.join(images_path_temporal, thumb_big_filename)
            thumb_small_path = os.path.join(images_path_temporal, thumb_small_filename)

            with open(thumb_big_path, "wb") as thumbnail:
                thumbnail.write(thumbnail_data)
                self.logger.info("LMV image created.")

            with open(thumb_small_path, "wb") as thumbnail:
                thumbnail.write(thumbnail_data)
                self.logger.info("LMV thumbnail created.")

            self.logger.info("Updating thumbnail.")
            self.parent.engine.shotgun.upload_thumbnail(
                "PublishedFile", publish_id, thumb_small_path
            )

            self.logger.info("Uploading sg_uploaded_movie")
            self.parent.engine.shotgun.upload(
                entity_type="Version",
                entity_id=version_id,
                path=thumb_small_path,
                field_name="sg_uploaded_movie",
            )

            self.logger.info("ZIP package")
            zip_path = shutil.make_archive(
                base_name=base_name, format="zip", root_dir=output_directory
            )

            item.properties["thumb_small_path"] = thumb_small_path
        else:
            self.logger.info("ZIP package without images")
            zip_path = shutil.make_archive(
                base_name=base_name, format="zip", root_dir=output_directory
            )

        self.logger.info("Uploading lmv files")
        self.parent.engine.shotgun.upload(
            entity_type="Version",
            entity_id=version_id,
            path=zip_path,
            field_name="sg_translation_files",
        )

        self.parent.engine.shotgun.update(
            entity_type="Version",
            entity_id=version_id,
            data=dict(sg_translation_type="LMV"),
        )

        self.logger.info("LMV processing finished successfully.")
        self.logger.info("Translate VRED file to LMV file locally (DONE).")

    def _upload_thumbnail_without_lmv(self, source_path, item):
        publish_id = item.properties.sg_publish_data["id"]
        version_id = item.properties.sg_version_data["id"]

        self.TMPDIR = tempfile.mkdtemp(prefix="sgtk_")

        # VRED file name
        file_name = os.path.basename(source_path)

        # Copy source file locally
        self.logger.info("Copy file {} locally.".format(source_path))
        source_path_temporal = os.path.join(self.TMPDIR, file_name)
        shutil.copyfile(source_path, source_path_temporal)

        output_directory = os.path.join(self.TMPDIR, "output")

        thumbnail_data = self._get_thumbnail_data(item, source_path_temporal)
        if thumbnail_data:
            images_path_temporal = os.path.join(output_directory, "images")

            if not os.path.exists(images_path_temporal):
                self.makedirs(images_path_temporal)

            thumb_big_filename = "{}.jpg".format(version_id)
            thumb_small_filename = "{}_thumb.jpg".format(version_id)
            thumb_big_path = os.path.join(images_path_temporal, thumb_big_filename)
            thumb_small_path = os.path.join(images_path_temporal, thumb_small_filename)

            with open(thumb_big_path, "wb") as thumbnail:
                thumbnail.write(thumbnail_data)

            with open(thumb_small_path, "wb") as thumbnail:
                thumbnail.write(thumbnail_data)

            self.logger.info("Updating thumbnail.")
            self.parent.engine.shotgun.upload_thumbnail(
                "PublishedFile", publish_id, thumb_small_path
            )

            self.logger.info("Uploading sg_uploaded_movie")
            self.parent.engine.shotgun.upload(
                entity_type="Version",
                entity_id=version_id,
                path=thumb_small_path,
                field_name="sg_uploaded_movie",
            )

            item.properties["thumb_small_path"] = thumb_small_path

    def _get_thumbnail_data(self, item, source_temporal_path):
        path = item.get_thumbnail_as_path()
        data = None

        if not path:
            extractor = self._get_thumbnail_extractor()
            path = tempfile.NamedTemporaryFile(
                suffix=".jpg", prefix="sgtk_thumb", delete=False
            ).name

            command = [extractor, "--icv", path, source_temporal_path]

            try:
                subprocess.check_call(command, stderr=subprocess.STDOUT, shell=True)
                self.parent.engine.logger.debug(
                    "Getting thumbnail data with command {}".format(command)
                )
            except Exception as e:
                self.logger.error("Thumbnail extractor failed {!r}".format(e))
                self.parent.engine.logger.error(
                    "Error extracting thumbnail data {}".format(e)
                )
                path = None
            else:
                self.parent.engine.logger.debug("Thumbnail data extracted successfully")

        if path:
            with open(path, "rb") as fh:
                data = fh.read()

        return data

    def _get_target_path(self, item):
        root_path = item.properties.publish_template.root_path
        version_id = str(item.properties.sg_version_data["id"])
        target_path = os.path.join(root_path, "translations", "lmv", version_id)
        images_path = os.path.join(root_path, "translations", "images")
        self.makedirs(images_path)

        return target_path

    def _copy_work_to_publish(self, settings, item):
        source_path = item.properties["path"]
        # LMV translation disabled
        # self._translate_file(source_path, item)

        self._upload_thumbnail_without_lmv(source_path, item)

    def get_publish_type(self, settings, item):
        return "VRED"

    def publish(self, settings, item):
        # Create version
        path = item.properties["path"]
        file_name = os.path.basename(path)
        name, extension = os.path.splitext(file_name)
        item.properties["publish_name"] = name
        super(VREDPublishLMVFilePlugin, self).publish(settings, item)

        if self._is_translator_installed():
            self._copy_work_to_publish(settings, item)

        thumbnail_path = item.get_thumbnail_as_path()
        if not thumbnail_path and "thumb_small_path" in item.properties:
            self.parent.engine.shotgun.upload_thumbnail(
                entity_type="Version",
                entity_id=item.properties["sg_version_data"]["id"],
                path=item.properties["thumb_small_path"],
            )

        try:
            shutil.rmtree(self.TMPDIR)
        except Exception as e:
            pass

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["vred.session"]

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        publisher = self.parent

        shotgun_url = publisher.sgtk.shotgun_url

        media_page_url = "%s/page/media_center" % (shotgun_url,)
        review_url = "https://www.shotgunsoftware.com/features/#review"

        return """
                Publishes the file to Shotgun in a valid LMV format (In case translator is installed)<br>
                Upload the file to Shotgun for review.<br><br>

                A <b>Version</b> entry will be created in Shotgun and a transcoded
                copy of the file will be attached to it. The file can then be reviewed
                via the project's <a href='%s'>Media</a> page, <a href='%s'>RV</a>, or
                the <a href='%s'>Shotgun Review</a> mobile app.
                """ % (
            media_page_url,
            review_url,
            review_url,
        )
