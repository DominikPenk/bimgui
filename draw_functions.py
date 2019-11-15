import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

def draw_rectangle(position, size, color):
    # Draw the button
    vertices = (
        position, 
        (position[0] + size[0], position[1]),
        (position[0], position[1] - size[1]),
        (position[0] + size[0], position[1] - size[1]))
    indices = ((0, 1, 2), (2, 1, 3))

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def get_rectangle(position, size, color):
    vertices = (
        position, 
        (position[0] + size[0], position[1]),
        (position[0], position[1] - size[1]),
        (position[0] + size[0], position[1] - size[1]))
    indices = ((0, 1, 2), (2, 1, 3))
    colors = [color, color, color, color]
    return { "pos": vertices, "indices": indices, "color" : colors }

class WidgetData:
    def __init__(self):
        self.text_data = []
        self.geometry_data = []

# All draw functions return the size of the widget
def button(text, position, style, bimgui):
    data = WidgetData()
    blf.size(0, style["font_size"], style["dpi"])
    text_size = blf.dimensions(0, text)
    size = (2 * style["padding"] + text_size[0], 2 * style["padding"] + text_size[1])
    
    is_hovered = bimgui.is_hovered((position, size))

    data.text_data = [{
        "font_size": style["font_size"],
        "dpi": style["dpi"],
        "position":  (position[0] + style["padding"], position[1] - text_size[1] - style["padding"]),
        "text": text,
        "color": (*style["texcolor"], 1)
    }]
    data.geometry_data = [get_rectangle(position, size, style["button_hovered"] if is_hovered else style["button"])]
    return size, data

def checkbox(text, value, position, style, bimgui):
    data = WidgetData()
    
    blf.size(0, style["font_size"], style["dpi"])
    text_size = blf.dimensions(0, text)
    box_size = 2 * style["padding"] + text_size[1]
    size = (box_size + 2 * style["padding"] + text_size[0], box_size)

    is_hovered = bimgui.is_hovered((position, size))

    # Draw background rect
    data.geometry_data.append(get_rectangle(position, (box_size, box_size), style["button_hovered"] if is_hovered else style["button"]))

    # Draw dot if value is True
    if value:
        data.geometry_data.append(
            get_rectangle(
            (position[0] + style["padding"], position[1] - style["padding"]),
            (box_size - 2 * style["padding"], box_size - 2 * style["padding"]),
            style["checkbox_center"])
        )

    data.text_data = [{
        "font_size": style["font_size"],
        "dpi": style["dpi"],
        "position": (position[0] + box_size + style["padding"], position[1] - text_size[1] - style["padding"]),
        "text": text,
        "color": (*style["texcolor"], 1)
    }]
    
    return size, data

def label(text, position, style, with_background):
    data = WidgetData()

    blf.size(0, style["font_size"], style["dpi"])
    text_size = blf.dimensions(0, text)
    size = (
        text_size[0] + 2 * style["padding"] if with_background else text_size[0], 
        2 * style["padding"] + text_size[1])

    data.text_data = [{
        "font_size": style["font_size"],
        "dpi": style["dpi"],
        "position": (position[0], position[1] - text_size[1] - style["padding"]) if not with_background else (position[0] + style["padding"], position[1] - text_size[1] - style["padding"]),
        "text": text,
        "color": (*style["texcolor"], 1)
    }]
    if with_background:
        data.geometry_data = [get_rectangle(position, size, style["button"])]
    else:
        blf.position(0, position[0], position[1] - text_size[1] - style["padding"], 0)   

    return size, data

def progress(text, value, show_progress, position, style):
    data = WidgetData()
    blf.size(0, style["font_size"], style["dpi"])
    full_text = "{} (100%)".format(text) if show_progress else text
    text_size = blf.dimensions(0, full_text)
    size = (2 * style["padding"] + text_size[0], 2 * style["padding"] + text_size[1])
    
    data.text_data = [{
        "font_size": style["font_size"],
        "dpi": style["dpi"],
        "position":  (position[0] + style["padding"], position[1] - text_size[1] - style["padding"]),
        "text": "{} ({}%)".format(text, int(value)) if show_progress else text,
        "color": (*style["texcolor"], 1)
    }]

    alpha = min(1.0, max(0.0, value / 100))
    col_left = style["progress"]
    col_right = style["button"]
    data.geometry_data = [{
        "pos" : (
            position, 
            (position[0] + alpha * size[0], position[1]),
            (position[0], position[1] - size[1]),
            (position[0] + alpha * size[0], position[1] - size[1]),

            (position[0] + alpha * size[0], position[1]),
            (position[0] + size[0], position[1]),
            (position[0] + alpha * size[0], position[1] - size[1]),
            (position[0] + size[0], position[1] - size[1])),
        "indices" : (
            (0, 1, 2), (2, 1, 3),
            (4, 5, 6), (6, 5, 7)),
        "color" : [col_left, col_left, col_left, col_left, col_right, col_right, col_right, col_right]
    }]
    return size, data
