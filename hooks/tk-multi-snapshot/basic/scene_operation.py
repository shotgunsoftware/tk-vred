import sgtk

HookClass = sgtk.get_hook_baseclass()


class SceneOperation(HookClass):
    def execute(self, operation, file_path=None, context=None, parent_action=None, file_version=None, read_only=None, **kwargs):
        if operation == "current_path":
            # Get the current file path.
            current_path = self.parent.engine.get_current_file()

            if current_path is None:
                return ""  # it's a new file
            else:
                return current_path
        else:
            if operation == "open":
                self.parent.engine.log_info("Scene Operation, Open file: "+file_path)
                self.parent.engine.reset_scene()
                self.parent.engine.load_file(file_path)

            elif operation == "save":
                # If file path not specified save in place.
                if file_path is None:
                    file_path = self.parent.engine.get_current_file()
                self.parent.engine.log_info("Scene Operation, Save file: "+file_path)
                self.parent.engine.save_current_file(file_path)

            elif operation == "save_as":
                self.parent.engine.log_info("Scene Operation, Save_as file: "+file_path)
                self.parent.engine.save_current_file(file_path)

            elif operation == "reset":
                self.parent.engine.log_info("Scene Operation, Reset Scene")
                # Reset the Scene in VRED
                self.parent.engine.reset_scene()
               
            sgtk.platform.current_engine().menu.create()

            return True

