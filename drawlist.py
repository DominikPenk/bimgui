"""
This module implements the DrawList class.
The class can be used to create multiple simple shapes which are drawn with view draw calls
"""
import bgl
import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

class DrawList:
    """
    Implements some low level primitives for rendering
    """
    def __init__(self):
        self._geometry = dict()
        self._text = dict()

        self._current_channel = 0

    def clear(self):
        """
        Clears the drawlist
        """
        self._geometry = dict()
        self._text = dict()
        self._current_channel = 0

    def draw(self):
        """
        This will draw the data
        """
        shader = gpu.shader.from_builtin('2D_FLAT_COLOR')

        layers = set(self._geometry.keys()).union(set(self._text.keys()))
        layers = sorted(layers)

        # Draw all elements
        bgl.glEnable(bgl.GL_BLEND)
        for layer in layers:
            if layer in self._geometry:
                batch = batch_for_shader(
                    shader, 'TRIS',
                    {
                        "pos": self._geometry[layer]["pos"],
                        "color": self._geometry[layer]["color"]
                    },
                    indices=self._geometry[layer]["indices"])
                batch.draw(shader)
            # Draw text
            for text_data in self._text.get(layer, []):
                blf.size(0, text_data["font_size"], text_data["dpi"])
                # Get text size
                text_size = blf.dimensions(0, text_data["text"])
                blf.position(
                    0,
                    text_data["position"][0],
                    text_data["position"][1] - text_size[1],
                    0)
                blf.color(0, *text_data["color"])
                blf.draw(0, text_data["text"])
        bgl.glDisable(bgl.GL_BLEND)

    @property
    def channel(self):
        """
        Set the current channel to add geometry
        Channels are drawn in ascending order
        """
        return self._current_channel

    @channel.setter
    def channel(self, value):
        assert isinstance(value, int), "Channel can only be an interger"
        self._current_channel = value

    @property
    def geometry(self):
        """
        Returns the geomtry data for the current layer
        """
        return self._geometry.setdefault(
            self._current_channel,
            {
                "pos": [],
                "color": [],
                "indices": []
            }
        )

    @property
    def text(self):
        """
        Returns the text data list for the current layer
        """
        return self._text.setdefault(self._current_channel, [])

    def add_filled_rectangle(self, position, size, color):
        """
        Add a colored rectangle to the draw list
        """
        vertices = (
            position,
            (position[0] + size[0], position[1]),
            (position[0], position[1] - size[1]),
            (position[0] + size[0], position[1] - size[1]))
        offset = len(self.geometry["pos"])
        indices = (
            (offset + 0, offset + 1, offset + 2),
            (offset + 2, offset + 1, offset + 3))
        colors = [color, color, color, color]
        self.geometry["pos"] += vertices
        self.geometry["indices"] += indices
        self.geometry["color"] += colors

    def add_text(self, text, position, **kwargs):
        """
        Add text to draw to the renderlist
        """
        self.text.append({
            "font_size": kwargs.get("font_size", 11),
            "dpi": kwargs.get("dpi", bpy.context.preferences.system.dpi),
            "position":  (position[0], position[1]),
            "text": text,
            "color": (*kwargs.get("color", (1, 1, 1)), 1)
        })
