import sgtk

import vrController
import vrFileIO
import vrScenegraph

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the current file.
    """

    def execute(
        self,
        operation,
        file_path=None,
        context=None,
        parent_action=None,
        file_version=None,
        read_only=None,
        **kwargs
    ):
        """
        Main hook entry point

        :param operation:       String
                                Scene operation to perform

        :param file_path:       String
                                File path to use if the operation requires it (e.g. open)

        :param context:         Context
                                The context the file operation is being performed in.

        :param parent_action:   This is the action that this scene operation is being executed for.

        :param file_version:    The version/revision of the file to be opened.

        :param read_only:       Specifies if the file should be opened read-only or not

        :returns:               Depends on operation:
                                'current_path' - Return the current scene file path as a String
                                all others     - True
        """

        self.logger.debug(
            "{self} executing operation '{op}' on file '{path}'".format(
                self=self, op=operation, path=file_path
            )
        )

        if operation == "current_path":
            current_path = vrFileIO.getFileIOFilePath()
            return "" if current_path is None else current_path

        if operation == "open":
            vrFileIO.load(
                [file_path],
                vrScenegraph.getRootNode(),
                newFile=True,
                showImportOptions=False,
            )
            self.parent.engine.set_render_path(file_path)

        elif operation == "save":
            if file_path is None:
                file_path = vrFileIO.getFileIOFilePath()

            self.parent.engine.save_current_file(file_path)

        elif operation == "save_as":
            self.parent.engine.save_current_file(file_path)

        elif operation == "reset":
            vrController.newScene()

        return True
