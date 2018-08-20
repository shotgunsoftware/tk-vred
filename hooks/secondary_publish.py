# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import tank
from tank import Hook
from tank import TankError
from os.path import isfile,basename,dirname,splitext
from os import remove
from subprocess import check_call,CalledProcessError
from string import split
from pprint import pformat
from collections import namedtuple
import vrScenegraph
import vrFileIO

class PublishHook(Hook):
    """
    Single hook that implements publish functionality for secondary tasks
    """
    def execute(
        self, tasks, work_template, comment, thumbnail_path, sg_task, primary_task,
        primary_publish_path, progress_cb, user_data, **kwargs):
        """
        Main hook entry point
        :param tasks:                   List of secondary tasks to be published.  Each task is a
                                        dictionary containing the following keys:
                                        {
                                            item:   Dictionary
                                                    This is the item returned by the scan hook
                                                    {
                                                        name:           String
                                                        description:    String
                                                        type:           String
                                                        other_params:   Dictionary
                                                    }

                                            output: Dictionary
                                                    This is the output as defined in the configuration - the
                                                    primary output will always be named 'primary'
                                                    {
                                                        name:             String
                                                        publish_template: template
                                                        tank_type:        String
                                                    }
                                        }

        :param work_template:           template
                                        This is the template defined in the config that
                                        represents the current work file

        :param comment:                 String
                                        The comment provided for the publish

        :param thumbnail:               Path string
                                        The default thumbnail provided for the publish

        :param sg_task:                 Dictionary (shotgun entity description)
                                        The shotgun task to use for the publish

        :param primary_publish_path:    Path string
                                        This is the path of the primary published file as returned
                                        by the primary publish hook

        :param progress_cb:             Function
                                        A progress callback to log progress during pre-publish.  Call:

                                            progress_cb(percentage, msg)

                                        to report progress to the UI

        :param primary_task:            The primary task that was published by the primary publish hook.  Passed
                                        in here for reference.  This is a dictionary in the same format as the
                                        secondary tasks above.

        :param user_data:               A dictionary containing any data shared by other hooks run prior to
                                        this hook. Additional data may be added to this dictionary that will
                                        then be accessible from user_data in any hooks run after this one.

        :returns:                       A list of any tasks that had problems that need to be reported
                                        in the UI.  Each item in the list should be a dictionary containing
                                        the following keys:
                                        {
                                            task:   Dictionary
                                                    This is the task that was passed into the hook and
                                                    should not be modified
                                                    {
                                                        item:...
                                                        output:...
                                                    }

                                            errors: List
                                                    A list of error messages (strings) to report
                                        }
        """
        self.parent.engine.log_info("Starting secondary publish")
        
        scene_path = self.parent.engine.get_current_file()
        fields = work_template.get_fields(scene_path)
        
        returnErrors = []
        
        for task in tasks:
            # Log info
            self.parent.engine.log_info("Publish Node "+task["item"]["name"])  
            self.parent.engine.log_info("Template: {}".format(str(task["output"]["publish_template"])))       
            
            # Get the publish path
            progress_cb(10.0, "Get the publish path",task)
            try:
                fields["nodeName"] = task["item"]["name"]
                publish_path = task["output"]["publish_template"].apply_fields(fields)
            except:
                returnErrors.append({
                        "task":task,
                        "errors":["Failed to get Publish Path"]
                    })
                return returnErrors
            
            # Get and select the node to save based on the id and node name
            progress_cb(30.0, "Get and select the node to save based on the id and node name",task)
            _rootNode = vrScenegraph.getRootNode()
            vrNodePtr = None
            for _n in range(0,_rootNode.getNChildren()):
                _childNode = _rootNode.getChild(_n)
                if _childNode.getType() == "Geometry":
                    if _childNode.getName() == task["item"]["name"] and _childNode.fields().getID() == task["item"]["other_params"]["NodeID"]:
                        vrNodePtr = _childNode
                        break

            if vrNodePtr is None:
                returnErrors.append({
                        "task":task,
                        "errors": ["Failed to Get Node "+task["item"]["name"]]
                    })
            else:
                # Save file to publish path
                progress_cb(60.0, "Save file to publish path",task)
                try:
                    vrFileIO.saveGeometry(vrNodePtr, publish_path)
                except:
                    returnErrors.append({
                        "task":task,
                        "errors":["Failed to save Node ( "+task["item"]["name"]+" )Geometry OSB file for "+publish_path]
                    }) 
            
            # Register the published file 
            progress_cb(90.0, "Register the published file",task)
            
            self._register_publish(
                publish_path,
                self._get_publish_name(publish_path, task["output"]["publish_template"], fields), 
                sg_task, 
                fields["version"], 
                task["output"]["tank_type"],
                comment,
                thumbnail_path,
                [])
            
            progress_cb(100.0,"Task Complete",task)
        return returnErrors
    
    
    def _register_publish(self, path, name, sg_task, publish_version, tank_type, comment, thumbnail_path, dependency_paths):
        """
        Helper method to register publish using the
        specified publish info.
        """
        # construct args:
        args = {
            "tk": self.parent.tank,
            "context": self.parent.context,
            "comment": comment,
            "path": path,
            "name": name,
            "version_number": publish_version,
            "thumbnail_path": thumbnail_path,
            "task": sg_task,
            "dependency_paths": dependency_paths,
            "published_file_type":tank_type,
        }

        self.parent.log_debug("Register publish in shotgun: %s" % str(args))

        # register publish;
        sg_data = tank.util.register_publish(**args)

        return sg_data
    
    
    def _get_publish_name(self, path, template, fields=None):
        """
        Return the 'name' to be used for the file - if possible
        this will return a 'versionless' name
        """
        # first, extract the fields from the path using the template:
        fields = fields.copy() if fields else template.get_fields(path)
        if "name" in fields and fields["name"]:
            # well, that was easy!
            name = fields["name"]
        else:
            # find out if version is used in the file name:
            template_name, _ = os.path.splitext(os.path.basename(template.definition))
            version_in_name = "{version}" in template_name

            # extract the file name from the path:
            name, _ = os.path.splitext(os.path.basename(path))
            delims_str = "_-. "
            if version_in_name:
                # looks like version is part of the file name so we
                # need to isolate it so that we can remove it safely.
                # First, find a dummy version whose string representation
                # doesn't exist in the name string
                version_key = template.keys["version"]
                dummy_version = 9876
                while True:
                    test_str = version_key.str_from_value(dummy_version)
                    if test_str not in name:
                        break
                    dummy_version += 1

                # now use this dummy version and rebuild the path
                fields["version"] = dummy_version
                path = template.apply_fields(fields)
                name, _ = os.path.splitext(os.path.basename(path))

                # we can now locate the version in the name and remove it
                dummy_version_str = version_key.str_from_value(dummy_version)

                v_pos = name.find(dummy_version_str)
                # remove any preceeding 'v'
                pre_v_str = name[:v_pos].rstrip("v")
                post_v_str = name[v_pos + len(dummy_version_str):]

                if (pre_v_str and post_v_str
                    and pre_v_str[-1] in delims_str
                    and post_v_str[0] in delims_str):
                    # only want one delimiter - strip the second one:
                    post_v_str = post_v_str.lstrip(delims_str)

                versionless_name = pre_v_str + post_v_str
                versionless_name = versionless_name.strip(delims_str)

                if versionless_name:
                    # great - lets use this!
                    name = versionless_name
                else:
                    # likely that version is only thing in the name so
                    # instead, replace the dummy version with #'s:
                    zero_version_str = version_key.str_from_value(0)
                    new_version_str = "#" * len(zero_version_str)
                    name = name.replace(dummy_version_str, new_version_str)

        return name+"-"+fields["nodeName"]