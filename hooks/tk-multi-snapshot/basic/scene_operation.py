import sgtk

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
        operations = engine.operations
        logger = engine.logger

        if operation == "current_path":
            current_path = operations.get_current_file()

            if current_path is None:
                return ""  # it's a new file
            else:
                return current_path
        else:
            if operation == "open":
                logger.debug("Scene Operation, Open file: " + file_path)
                operations.reset_scene()
                operations.load_file(file_path)

            elif operation == "save":
                if file_path is None:
                    file_path = operations.get_current_file()

                logger.debug("Scene Operation, Save file: " + file_path)
                operations.save_current_file(file_path)

            elif operation == "save_as":
                logger.debug("Scene Operation, Save_as file: " + file_path)
                operations.save_current_file(file_path)

            elif operation == "reset":
                logger.debug("Scene Operation, Reset Scene")
                operations.reset_scene()

            engine.menu.create()

            return True
