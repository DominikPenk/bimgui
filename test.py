import bpy
from . bimgui import BImGUI_OperatorOperator

class TestUIOperator(BImGUI_OperatorOperator):
    bl_idname = "wm.test_ui"
    bl_label = "Test BImGUI"

    ui_windows = [ ('VIEW3D', 'draw_view3d'), ('PROPERTIES', 'draw_view3d')  ]

    def init(self, context, event):
        self._bool = False

    def draw_view3d(self):
        self.begin_ui((100, 100))

        self.label("Label")

        if(self.button("Test Button")):
            print("Hello, World!")
        self.same_line()
        if(self.button("Test Button 2")):
            print("Hello, World 2!")

        self._bool = self.checkbox("Boolean", self._bool)

        self.progress("Sample Progress", 25)

        self.progress("Sample Progress", 57, False)

        self.end_ui()

    def run(self, context, event):
        self._should_close = self.io.is_key_down('ESC')
        if self._should_close:
            print("Stop")