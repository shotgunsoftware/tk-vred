import sgtk

import vrController
import vrFileIO
import vrScenegraph

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
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

        engine = self.parent.engine
        logger = engine.logger

        logger.debug(
            "Scene Operation: op: {}{}".format(
                operation,
                ", file path: {}".format(file_path)
                if file_path
                else "",  # Ternary requires >= Python 2.5
            )
        )

        if operation == "current_path":
            current_path = vrFileIO.getFileIOFilePath()

            if current_path is None:
                return ""  # it's a new file
            else:
                return current_path
        else:
            if operation == "open":
                vrFileIO.load([file_path], vrScenegraph.getRootNode(), True, False)
                engine.set_render_path(file_path)

            elif operation == "save":
                if file_path is None:
                    file_path = vrFileIO.getFileIOFilePath()

                engine.save_current_file(file_path)
                engine.set_render_path(file_path)

            elif operation == "save_as":
                engine.save_current_file(file_path)
                engine.set_render_path(file_path)

            elif operation == "reset":
                vrController.newScene()

            engine.menu_generator.create_menu()

            return True
