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
import tempfile
import traceback
from subprocess import Popen, PIPE, STDOUT

import sgtk
from sgtk.util.filesystem import ensure_folder_exists

HookBaseClass = sgtk.get_hook_baseclass()


class VREDPublishLMVFilePlugin(HookBaseClass):
    @staticmethod
    def _get_translator():
        return r"C:\Program Files\Autodesk\VREDPro-11.2\Bin\WIN64\LMV\viewing-vpb-lmv.exe"

    def _is_translator_installed(self):
        return os.path.exists(self._get_translator())

    @staticmethod
    def _get_thumbnail_extractor():
        return r"C:\Program Files\Autodesk\VREDPro-11.2\Bin\WIN64\extractMetaData.exe"

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
        publish_template = publisher.engine.get_template_by_name(publish_template_setting.value)

        if not publish_template:
            return False

        item.properties["vred_publish_template"] = publish_template

        work_template_setting = settings.get("VRED LMV Work Template")
        work_template = publisher.engine.get_template_by_name(work_template_setting.value)

        if not work_template:
            return False

        item.properties["vred_work_template"] = work_template

        return True

    def accept(self, settings, item):
        base_accept = super(VREDPublishLMVFilePlugin, self).accept(settings, item)

        base_accept.update({
            "checked": True,
            "enabled": False,
            "accepted": True if self._is_translator_installed() else False
        })
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

    def _translate_file(self, source_path, target_path, item):
        self.logger.info("Starting the translation")

        # Get translator
        translator = self._get_translator()

        # Temporal dir
        tmpdir = tempfile.mkdtemp(prefix='sgtk_')

        # VRED file name
        file_name = os.path.basename(source_path)

        # JSON file
        self.logger.info("Creating JSON file")
        index_path = os.path.join(tmpdir, 'index.json')
        with open(index_path, 'w') as _:
            pass

        # Copy source file locally
        self.logger.info("Copy file {} locally.".format(source_path))
        source_path_temporal = os.path.join(tmpdir, file_name)
        shutil.copyfile(source_path, source_path_temporal)

        # Execute translation command
        command = [translator, index_path, source_path_temporal]
        self.logger.info("LMV execution: {}".format(" ".join(command)))
        lmv_subprocess = Popen('"'+'" "'.join(command)+'"', stdout=PIPE, stderr=STDOUT, shell=True)
        while lmv_subprocess.poll() is None:
            self.logger.debug("LMV processing ... [{}]".format(lmv_subprocess.stdout.next().replace('\n', '')))

        if lmv_subprocess.returncode == 0:
            target_path_parent = os.path.dirname(target_path)

            if os.path.exists(target_path):
                shutil.rmtree(target_path)

            if not os.path.exists(target_path_parent):
                self.makedirs(target_path_parent)

            output_directory = os.path.join(tmpdir, "output")
            shutil.copytree(output_directory, target_path)

            self.logger.info("LMV files copied.")
        else:
            self.logger.error("LMV processing fail.")
            return

        publish_id = item.properties.sg_publish_data["id"]
        thumbnail_data = self._get_thumbnail_data(item)
        if thumbnail_data:
            images_path = os.path.join(target_path_parent, 'images')

            if not os.path.exists(images_path):
                self.makedirs(images_path)

            thumb_big_filename = "{}.jpg".format(publish_id)
            thumb_small_filename = "{}_thumb.jpg".format(publish_id)
            thumb_big_path = os.path.join(images_path, thumb_big_filename)
            thumb_small_path = os.path.join(images_path, thumb_small_filename)

            with open(thumb_big_path, 'wb') as thumbnail:
                thumbnail.write(thumbnail_data)
                self.logger.info("LMV image created.")

            with open(thumb_small_path,'wb') as thumbnail:
                thumbnail.write(thumbnail_data)
                self.logger.info("LMV thumbnail created.")

            self.logger.info("Updating thumbnail.")
            self.parent.engine.shotgun.upload_thumbnail("PublishedFile", publish_id, thumb_small_path)

        self.logger.info("Cleaning...")
        shutil.rmtree(tmpdir)

        self.logger.info("Updating translation status.")
        self.parent.engine.shotgun.update("PublishedFile", publish_id, dict(sg_translation_status="Completed"))

        self.logger.info("LMV processing finished successfully.")
        self.logger.info('Translate VRED file to LMV file locally (DONE).')

    def _get_thumbnail_data(self, item):
        path = item.get_thumbnail_as_path()
        data = None

        if not path:
            extractor = self._get_thumbnail_extractor()
            path = tempfile.NamedTemporaryFile(suffix=".jpg", prefix="sgtk_thumb", delete=False).name

            command = [extractor, "--icv", path, item.properties.path]

            try:
                command_line_process = Popen(command, stdout=PIPE, stderr=STDOUT)
                process_output, _ = command_line_process.communicate()

                if command_line_process.returncode != 0:
                    self.logger.error("Thumbnail extractor failed {!r}".format(process_output))
                    path = None
            except Exception as e:
                self.logger.error("Thumbnail extractor failed {!r}".format(e))
                path = None

        if path:
            with open(path, "rb") as fh:
                data = fh.read()

        return data

    def _get_target_path(self, item):
        root_path = item.properties.publish_template.root_path
        publish_id = str(item.properties.sg_publish_data['id'])
        target_path = os.path.join(root_path, 'translations', 'lmv', publish_id)
        images_path = os.path.join(root_path, 'translations', 'images')
        self.makedirs(images_path)

        return target_path

    def _copy_work_to_publish(self, settings, item):
        source_path = item.properties["path"]
        target_path = self._get_target_path(item)

        try:
            publish_folder = os.path.dirname(target_path)
            ensure_folder_exists(publish_folder)
            self._translate_file(source_path, target_path, item)
        except Exception as e:
            raise Exception(
                "Failed to copy work file from '%s' to '%s'.\n%s" %
                (source_path, target_path, traceback.format_exc())
            )

        self.logger.debug("Copied work file '%s' to publish file '%s'." % (source_path, target_path))

    def get_publish_type(self, settings, item):
        return "VRED"

    def publish(self, settings, item):
        self._copy_work_to_publish(settings, item)

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
        return "Publishes the file to Shotgun in a valid LMV format."
