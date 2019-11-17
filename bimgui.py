"""
This module holds the base class for BImgui operators
"""
import functools

import bpy
import blf

from . bimgui_io import BImGuiIO as IO
from . drawlist import DrawList

def _parse_space_string(string):
    if string == 'VIEW3D':
        return bpy.types.SpaceView3D
    if string == 'PROPERTIES':
        return bpy.types.SpaceProperties
    if string == 'CLIP_EDITOR':
        return bpy.types.SpaceClipEditor
    if string == 'OUTLINER':
        return bpy.types.SpaceOutliner
    else:
        return None

def _load_style():
    # Style variables
    theme = bpy.context.preferences.themes['Default']
    return {
        "spacing": 5,
        "padding": 5,
        "font_size": 11,
        "dpi": bpy.context.preferences.system.dpi,
        "texcolor": tuple(theme.user_interface.wcol_toolbar_item.text),
        "texcolor_sel": tuple(theme.user_interface.wcol_toolbar_item.text_sel),
        "button": tuple(theme.user_interface.wcol_toolbar_item.inner),
        "button_hovered": tuple(theme.user_interface.wcol_toolbar_item.inner_sel),
        "checkbox_center": (*tuple(theme.user_interface.wcol_toolbar_item.text), 1.0),
        "progress": tuple(theme.user_interface.wcol_progress.item),
        "window_background_color": (0, 0, 0, 0.5)
    }

def bimgui_draw(space, **kwargs):
    """
    You need to decorate the draw callbacks with this function
    It will take care of reading data
    """
    def decorator(func):
        base = func.__dict__.setdefault('bimgui_unwrapped', func)
        callback_data = func.__dict__.setdefault('bimgui', [])
        callback_data.append({
            'space': _parse_space_string(space),
            'region': kwargs.get('region', 'WINDOW'),
            'stage': kwargs.get('stage', 'POST_PIXEL'),
            'index': len(callback_data)
        })
        index = len(callback_data) - 1
        @functools.wraps(base)
        def wrapper(*args):
            io = args[1]
            lid = args[2]
            io.set_current_listener(lid)
            base(args[0])
            io.signal_processed(lid)
        callback_data[index]['drawfn'] = wrapper
        return wrapper
    return decorator

class BImGUIOperator(bpy.types.Operator):
    """
    This base class is an abstract modal operator that you can use to create a UI
    Implement the init function to to initialization work
    """

    def __init__(self):
        self._should_close = False
        #pylint: disable=invalid-name
        self.io = IO()

        # Check which hooks are required
        self._draw_handles = []
        # Add draw handlers
        for window in self.__get_draw_functions():
            self._draw_handles += window.__dict__['bimgui']
        self._draw_event = None

        self.draw_list = DrawList()
        self.style = _load_style()

        # "Forward" decleration
        self._last_region = None
        self._next_position = None
        self._current_top_left = None
        self._current_bottom_right = None
        self._current_line_start = 0
        self._current_window_has_background = False

    def __get_draw_functions(self):
        callables = [getattr(self, method) for method in dir(self)
                     if callable(getattr(self, method))]
        return [method for method in callables if 'bimgui' in dir(method)]

    def _register_handles(self, context):
        for window in self._draw_handles:
            # Register this window to io
            window['listener'] = self.io.register_listener()
            window['handle'] = window['space'].draw_handler_add(
                window['drawfn'],
                (self, self.io, window['listener']),
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
        for handle in self._draw_handles:
            handle["space"].draw_handler_remove(
                handle["handle"],
                handle['region'])
            self.io.unregister_listener(handle['listener'])
            handle['handle'] = None
            handle['listener'] = None
        # Redraw all windows
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

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
        Implement this function if you need to to something in the invoke function
        """

    def run(self, context, event):
        """
        Implement this function if you want to do something whenever the modal callback is called
        """

    def invoke(self, context, event):
        self.init(context, event)
        self._last_region = ((0, 0), (0, 0))
        self._next_position = (0, 0)

        self._register_handles(context)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        """
        This function is called periodically by blender
        """
        self.io.handle_input(event)
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

    def begin_ui(self, top_left=(10, 10), with_background=False):
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

        self.draw_list.clear()

    def end_ui(self):
        """
        Call this function at the end of your callback.
        This function will actually render the entire gui
        """
        # Draw background
        if self._current_window_has_background:
            size = (
                self._current_bottom_right[0] - self._current_top_left[0] + 2*self.style["padding"],
                self._current_top_left[1] - self._current_bottom_right[1] + 2*self.style["padding"]
            )
            position = (
                self._current_top_left[0] - self.style["padding"],
                self._current_top_left[1] + self.style["padding"]
            )
            self.draw_list.channel = -1
            self.draw_list.add_filled_rectangle(
                position,
                size,
                self.style["window_background_color"])

        self.draw_list.draw()

    def is_hovered(self, region=None):
        """
        Returns wether the curser is over the given region
        If you call this function without a region argument it will check,
        if the last ui elment added is hovered
        """
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
        """
        Return the mouse position relative to the current window
        """
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
        blf.size(0, self.style["font_size"], self.style["dpi"])
        text_size = blf.dimensions(0, text)
        size = (2 * self.style["padding"] + text_size[0], 2 * self.style["padding"] + text_size[1])

        is_hovered = self.is_hovered((self._next_position, size))

        self.draw_list.add_text(
            text,
            (
                self._next_position[0] + self.style["padding"],
                self._next_position[1] - self.style["padding"]
            ),
            **self.style)
        self.draw_list.add_filled_rectangle(
            self._next_position,
            size,
            self.style["button_hovered"] if is_hovered else self.style["button"])

        self._newline(size)
        return self.is_hovered() and self.io.mouse_clicked['LEFTMOUSE']

    def checkbox(self, text, value):
        """
        Draw a checkbox where the state is given by value
        Returns True if the checkbox is checked False otherwise
        """
        blf.size(0, self.style["font_size"], self.style["dpi"])
        text_size = blf.dimensions(0, text)
        box_size = 2 * self.style["padding"] + text_size[1]
        size = (box_size + 2 * self.style["padding"] + text_size[0], box_size)

        is_hovered = self.is_hovered((self._next_position, size))

        # Draw background rect
        self.draw_list.add_filled_rectangle(
            self._next_position, 
            (box_size, box_size),
            self.style["button_hovered"] if is_hovered else self.style["button"])

        # Draw dot if value is True
        if value:
            self.draw_list.channel = 1
            self.draw_list.add_filled_rectangle(
                (
                    self._next_position[0] + self.style["padding"],
                    self._next_position[1] - self.style["padding"]
                ),
                (
                    box_size - 2 * self.style["padding"],
                    box_size - 2 * self.style["padding"]
                ),
                self.style["checkbox_center"]
            )

        self.draw_list.add_text(
            text,
            (
                self._next_position[0] + box_size + self.style["padding"],
                self._next_position[1] - self.style["padding"]
            ),
            **self.style
        )
        self._newline(size)
        return not value if is_hovered and self.io.mouse_clicked['LEFTMOUSE'] else value

    def label(self, text, with_background=False):
        """
        Draw a label
        """
        blf.size(0, self.style["font_size"], self.style["dpi"])
        text_size = blf.dimensions(0, text)
        size = (
            (
                text_size[0] + 2 * self.style["padding"],
                2 * self.style["padding"] + text_size[1]
            ) if with_background
            else text_size)

        position = (
            (
                self._next_position[0] + self.style["padding"],
                self._next_position[1] - self.style["padding"]
            ) if with_background
            else self._next_position)

        self.draw_list.add_text(
            text,
            position,
            **self.style
        )        
        self._newline(size)

    def progress(self, text, value, show_progress = True):
        """
        Draws a progress bar
        """
        blf.size(0, self.style["font_size"], self.style["dpi"])
        full_text = "{} (100%)".format(text) if show_progress else text
        text_size = blf.dimensions(0, full_text)
        size = (2 * self.style["padding"] + text_size[0], 2 * self.style["padding"] + text_size[1])

        self.draw_list.add_text(
            "{} ({}%)".format(text, int(value)) if show_progress else text,
            #pylint: disable=line-too-long
            (self._next_position[0] + self.style["padding"], self._next_position[1]- self.style["padding"]),
            **self.style)

        alpha = min(1.0, max(0.0, value / 100))
        self.draw_list.add_filled_rectangle(
            self._next_position,
            (alpha * size[0], size[1]),
            self.style["progress"])
        self.draw_list.add_filled_rectangle(
            (self._next_position[0] + alpha * size[0], self._next_position[1]),
            ((1.0 - alpha) * size[0], size[1]),
            self.style["button"])
        self._newline(size)

    def same_line(self, col= None):
        """
        The next element will be drawn at on the same line as the previous one
        """
        self._next_position = (
            # pylint: disable=line-too-long
            self._last_region[0][0] + self._last_region[1][0] + self.style["spacing"] if col is None else self._current_line_start + col,
            self._last_region[0][1])
