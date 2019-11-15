import bpy
import blf

from . bimgui_io import BImGui_IO as IO
from . draw_functions import *

class BImGUI_OperatorOperator(bpy.types.Operator):
    """
    This base class is an abstract modal operator that you can use to create a UI
    Implement the init function to to initialization work
    Implement the draw function to draw elements into a view
    """
    def __init__(self):
        self._should_close = False
        self.io = IO()

        # Check which hooks are required
        self._draw_handles = []
        for window in self.ui_windows:
            self._draw_handles.append(self._parse_window(window))
        self._draw_event = None

    def _parse_space_string(self, string):
        if string == 'VIEW3D':
            return bpy.types.SpaceView3D
        if string == 'PROPERTIES':
            return bpy.types.SpaceProperties
        if string == 'CLIP_EDITOR':
            return bpy.types.SpaceClipEditor
        if string == 'OUTLINER':
            return bpy.types.SpaceOutliner

    def _parse_window(self, window):
        if type(window) is list or type(window) is tuple:
            # if the length is 2 we expect a string and a callback
            if len(window) == 2:
                return {
                    "space": self._parse_space_string(window[0]),
                    "region": 'WINDOW',
                    "stage": 'POST_PIXEL',
                    "handle": None,
                    "drawfn": getattr(self, window[1])
                }
            elif len(window) == 3:
                return {
                    "space": self._parse_space_string(window[0]),
                    "region": 'WINDOW',
                    "stage": window[2],
                    "handle": None,
                    "drawfn": getattr(self, window[1])
                }
            else:
                raise "Invalid window {}".format(window)
        else: 
            raise "Invalid window {}".format(window) 

    def _register_handles(self, context):
        for window in self._draw_handles:
            window['handle'] = window['space'].draw_handler_add(
                window['drawfn'],
                (),
                window['region'],
                window['stage'])
            
        # Force initial redraw
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        self._draw_event = context.window_manager.event_timer_add(0.01, window=context.window)

    def _unregister_handlers(self, context):
        context.window_manager.event_timer_remove(self._draw_event)
        _draw_event = None
        for h in self._draw_handles:
            h["space"].draw_handler_remove(
                h["handle"],
                h['region'])
            h['handle'] = None
        
        # Redraw all windows
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

    def _load_style(self):
        # Style variables
        theme = bpy.context.preferences.themes['Default']

        self.style = {
            "spacing": 5,
            "padding": 5,
            "font_size": 11,
            "dpi": bpy.context.preferences.system.dpi,
            "texcolor": tuple(theme.user_interface.wcol_toolbar_item.text),
            "texcolor_sel": tuple(theme.user_interface.wcol_toolbar_item.text_sel),
            "button": tuple(theme.user_interface.wcol_toolbar_item.inner),
            "button_hovered": tuple(theme.user_interface.wcol_toolbar_item.inner_sel),
            "checkbox_center": (*tuple(theme.user_interface.wcol_toolbar_item.text), 1.0),
            "progress": tuple(theme.user_interface.wcol_progress.item)
        }

    def _add_draw_data(self, draw_data):
        for layer_id, geometry in enumerate(draw_data.geometry_data):
            if layer_id >= len(self._geometry_render_list):
                self._geometry_render_list.append({"pos": [], "indices": [], "color": []})
            index_offset = len(self._geometry_render_list[layer_id]["pos"])
            self._geometry_render_list[layer_id]["indices"] += [tuple(i + index_offset for i in tri) for tri in geometry["indices"]]
            self._geometry_render_list[layer_id]["pos"] += geometry["pos"]
            self._geometry_render_list[layer_id]["color"] += geometry["color"]
        
        self._text_render_list += draw_data.text_data


    def _newline(self, size):
        self._last_region = (self._next_position, size)
        self._next_position = (
            self._current_line_start,
            self._next_position[1] - size[1] - self.style['spacing']) 
        self._current_bottom_right = (
            max(self._last_region[0][0] + size[0], self._current_bottom_right[0]),
            min(self._last_region[0][1] - size[1], self._current_bottom_right[1]))

    def init(self, context, event):
        """
        Implement this function for initialization (do not override __init__)
        """
        pass

    def run(self, context, event):
        """
        Implement this function if you want to do something whenever the modal callback is called
        """
        pass

    def invoke(self, context, event):
        self.init(context, event)
        self._last_region = ((0, 0), (0, 0))
        self._next_position = (0, 0)

        self._load_style()

        self._register_handles(context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """
        This function is called periodically by blender
        """
        self.io._handle_input(event)
        self.run(context, event)

        # Enforce redraw
        if event.type.startswith("TIMER"):
            for window in bpy.context.window_manager.windows:
                for area in window.screen.areas:
                    area.tag_redraw()
        
        # Check if the UI should be closed
        if self._should_close:
            self._unregister_handlers(context)
            return {'CANCELLED'}
            
        # Pass on event to other modal operators
        return {'PASS_THROUGH'}
        
    def begin_ui(self, top_left = (10, 10), with_background = False):
        """
        Call this function at the start of your callbacks!
        """
        region = bpy.context.region

        self._current_window_has_background = with_background
        self._current_line_start = top_left[0]
        
        self._last_region = ((top_left[0], region.height - top_left[0]), (0, 0))
        self._current_top_left = self._last_region[0]
        self._current_bottom_right = self._last_region[0]
        self._next_position = self._last_region[0]

        self._geometry_render_list = []
        self._text_render_list = []

    def end_ui(self):
        """
        Call this function at the end of your callback.
        This function will actually render the entire gui
        """
        # Draw background
        if self._current_window_has_background:
            size = (
                self._current_bottom_right[0] - self._current_top_left[0] + 2 * self.style["padding"],
                self._current_top_left[1] - self._current_bottom_right[1] + 2 * self.style["padding"]
            )
            position = (
                self._current_top_left[0] - self.style["padding"],
                self._current_top_left[1] + self.style["padding"]
            )
            draw_rectangle(position, size, (0, 0, 0, 1))

        # Draw Geometry
        shader = gpu.shader.from_builtin('2D_FLAT_COLOR')
        for layer in self._geometry_render_list:
            batch = batch_for_shader(
                shader,'TRIS',
                {"pos": layer["pos"], "color": layer["color"]},
                indices=layer["indices"])
            batch.draw(shader)
        
        # Draw Text
        for text_data in self._text_render_list:
            blf.size(0, text_data["font_size"], text_data["dpi"])
            blf.position(0, *text_data["position"], 0)
            blf.color(0, *text_data["color"])
            blf.draw(0, text_data["text"])


    def is_hovered(self, region=None):
        if not region:
            region = self._last_region
        if not region:
            return False
        else:
            mouse_pos = self.get_mouse_pos()
            rx = mouse_pos[0] - region[0][0]
            ry = region[0][1] - mouse_pos[1] 
            return rx >= 0 and rx <= region[1][0] and ry >= 0 and ry <= region[1][1]

    def get_mouse_pos(self):
        region = bpy.context.region
        if len(self.io.mouse_pos) == 2:
            return [self.io.mouse_pos[0] - region.x, self.io.mouse_pos[1] - region.y]
        else:
            return [-1000, -1000]

    def button(self, text):
        """
        Draws a button with given text.
        Returns True if the button was clicked
        """
        size, data = button(text, self._next_position, self.style, self)
        self._add_draw_data(data)
        self._newline(size)
        return self.is_hovered() and self.io.mouse_clicked['LEFTMOUSE']

    def checkbox(self, text, value):
        """
        Draw a checkbox where the state is given by value
        Returns True if the checkbox is checked False otherwise
        """
        size, data = checkbox(text, value, self._next_position, self.style, self)
        self._add_draw_data(data)
        self._newline(size)
        return not value if self.is_hovered() and self.io.mouse_clicked['LEFTMOUSE'] else value

    def label(self, text, with_background = False):
        """ 
        Draw a label
        """
        size, data = label(text, self._next_position, self.style, with_background)
        self._add_draw_data(data)
        self._newline(size)

    def progress(self, text, value, show_progress = True):
        """
        Draws a progress bar
        """
        size, data = progress(text, value, show_progress, self._next_position, self.style)
        self._add_draw_data(data)
        self._newline(size)

    def same_line(self, col = None):
        """
        The next element will be drawn at on the same line as the previous one
        """
        self._next_position = (
            self._last_region[0][0] + self._last_region[1][0] + self.style["spacing"] if col is None else self._current_line_start + col,
            self._last_region[0][1])