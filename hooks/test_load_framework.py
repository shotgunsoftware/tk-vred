import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

# lmv = sgtk.platform.import_framework(
#     "tk-framework-lmv", "translator"
# )


class TestLoadFramework(HookBaseClass):
    def test_load(self):
        lmv = self.load_framework("tk-framework-lmv_v0.x.x")
        print(lmv)
