# Copyright (c) 2017 Shotgun Software Inc.
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


class VREDPublishOBSFilePlugin(HookBaseClass):
    @property
    def settings(self):
        # inherit the settings from the base publish plugin
        base_settings = super(VREDPublishOBSFilePlugin, self).settings or {}

        # settings specific to this class
        publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        base_settings.update(publish_settings)

        workfile_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        base_settings.update(workfile_settings)

        translator_settings = {
            "Translator": {
                "type": "dictionary",
                "default": None
            }
        }

        base_settings.update(translator_settings)

        return base_settings

    def validate(self, settings, item):
        publisher = self.parent

        publish_template_setting = settings.get("Publish Template")
        publish_template = publisher.engine.get_template_by_name(publish_template_setting.value)

        if not publish_template:
            return False

        if publish_template:
            item.properties["publish_template"] = publish_template

        workfile_template_setting = settings.get("Work Template")
        workfile_template = publisher.engine.get_template_by_name(workfile_template_setting.value)

        if not workfile_template:
            return False

        item.properties["work_template"] = workfile_template

        item.properties["translator"] = settings.get("Translator")

        return True

    def accept(self, settings, item):
        base_accept = super(VREDPublishOBSFilePlugin, self).accept(settings, item)

        base_accept.update({"checked": False})

        return base_accept

    @property
    def item_filters(self):
        return ["vred.session"]
