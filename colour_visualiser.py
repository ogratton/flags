"""
The problem with the colour_extractor is that one has to define what (e.g.) "red" *is*.
The naïve solution is to define a "true" red, and hope that a dark red is close enough to
it that is isn't declared black by virtue of proximity.

This code tries to visualise the 3D colour space so we can see what the Flags._reduce_colour function
is trying to do

Adapted from:
http://www.poketcode.com/pyglet_demos.html
https://github.com/jjstrydom/pyglet_examples
"""
from colour_extractor import Colour, COLOURS
from typing import NewType, Tuple
from random import randint
from copy import deepcopy
from pyglet.gl import gl
from pyglet.gl import glu
import pyglet
import os


# TODO this can be tidied up endlessly


# Pyglet uses RGBA colour from 0-1, so the last value is opacity
RGBAColour = NewType('Colour', Tuple[float, float, float, float])

DIST_BACK = 300
BLACK = RGBAColour((0.0, 0.0, 0.0, 1))
GREY = RGBAColour((0.5, 0.5, 0.5, 1))
WHITE = RGBAColour((1.0, 1.0, 1.0, 1))

# models
BOX = 0
SPHERE = 1
PYRAMID = 2


def rand_colour():
    return Colour((randint(0, 255), randint(0, 255), randint(0, 255)))


def new_rgba(rgb: Colour) -> RGBAColour:
    return RGBAColour((rgb[0]/255, rgb[1]/255, rgb[2]/255, 1))


class World:
    """
    Collection of OBJ models within the larger simulation.
    """

    def __init__(self, coords, models, background_color=GREY):

        # original copies of each type of model
        self.models = models

        self.cube = Cube([0, 0, 0], 255)

        # make the objects for the cube
        box_model = deepcopy(self.models[BOX])
        box_model.x, box_model.y, box_model.z = list(self.cube.centre)
        box_model.color = WHITE  # doesn't matter cos not filled in
        box_model.scale = self.cube.edge_length/2
        self.box_model = box_model

        self.colour_models = []
        for colour in COLOURS.values():
            colour_model = deepcopy(self.models[SPHERE])
            colour_model.x, colour_model.y, colour_model.z = colour
            colour_model.color = new_rgba(colour)
            colour_model.scale = 5
            self.colour_models.append(colour_model)

        random_colours = [
            # rand_colour(),
            # rand_colour(),
            # rand_colour()
        ]

        print(*random_colours, sep='\n')

        self.rand_col_models = []
        for rc in random_colours:
            rc_model = deepcopy(self.models[PYRAMID])
            rc_model.x, rc_model.y, rc_model.z = rc
            rc_model.color = new_rgba(rc)
            rc_model.scale = 5
            self.rand_col_models.append(rc_model)

        # sets the background color
        gl.glClearColor(*background_color)

        # where the camera starts off:
        [self.x, self.y, self.z] = coords
        # rotation values
        self.rx = self.ry = self.rz = 0
        self.cx, self.cy, self.cz = 0, 0, 0

    def draw(self):
        # clears the screen with the background color
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

        gl.glLoadIdentity()

        # # sets the position for the camera
        gl.glTranslatef(self.x, self.y, self.z)

        # sets the rotation for the camera
        gl.glRotatef(self.rx, 1, 0, 0)
        gl.glRotatef(self.ry, 0, 1, 0)
        gl.glRotatef(self.rz, 0, 0, 1)

        self.render_model(self.box_model, fill=False)

        for colour_model in self.colour_models:
            self.render_model(colour_model, frame=False)

        for rc_model in self.rand_col_models:
            self.render_model(rc_model, frame=False)

    def render_model(self, model, fill=True, frame=True):

        if fill:
            # sets fill mode
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

            # draws the current model
            self.draw_model(model)

        if frame:
            # sets wire-frame mode
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

            # draws the current model wire-frame
            temp_color = model.color
            model.color = WHITE
            self.draw_model(model)
            model.color = temp_color

    def draw_model(self, model):

        # gl.glLoadIdentity()
        gl.glPushMatrix()

        # sets the color
        gl.glColor4f(*model.color)

        # sets the position
        gl.glTranslatef(model.x - self.cx, model.y - self.cy, model.z - self.cz)

        # sets the rotation
        gl.glRotatef(model.rx, 1, 0, 0)
        gl.glRotatef(model.ry, 0, 1, 0)
        gl.glRotatef(model.rz, 0, 0, 1)

        # sets the scale
        gl.glScalef(model.scale, model.scale, model.scale)

        # draws the quads
        pyglet.graphics.draw_indexed(len(model.vertices) // 3, gl.GL_QUADS, model.quad_indices,
                                     ('v3f', model.vertices))

        # draws the triangles
        pyglet.graphics.draw_indexed(len(model.vertices) // 3, gl.GL_TRIANGLES, model.triangle_indices,
                                     ('v3f', model.vertices))

        gl.glPopMatrix()

    def update(self):
        """
        Main update loop
        This isn't an animation, so we don't need to do anything too extravagant
        """
        self.cx = self.box_model.x
        self.cy = self.box_model.y
        self.cz = self.box_model.z


class OBJModel:
    """
    Load an OBJ model from file.
    (Code unchanged from source. See credits file)
    """

    def __init__(self, coords=(0, 0, 0), scale=1, color=WHITE, path=None):
        self.vertices = []
        self.quad_indices = []
        self.triangle_indices = []

        # translation and rotation values
        [self.x, self.y, self.z] = coords
        self.rx = self.ry = self.rz = 0
        self.scale = scale

        # color of the model
        self.color = color

        # if path is provided
        if path:
            self.load(path)

    def clear(self):
        # not sure why this is necessary (doesn't seem to be)
        self.vertices = self.vertices[:]
        self.quad_indices = self.quad_indices[:]
        self.triangle_indices = self.triangle_indices[:]

    def load(self, path):
        self.clear()

        with open(path) as obj_file:
            for line in obj_file.readlines():
                # reads the file line by line
                data = line.split()

                # every line that begins with a 'v' is a vertex
                if data[0] == 'v':
                    # loads the vertices
                    x, y, z = data[1:4]
                    self.vertices.extend((float(x), float(y), float(z)))

                # every line that begins with an 'f' is a face
                elif data[0] == 'f':
                    # loads the faces
                    for _ in data[1:]:
                        if len(data) == 5:
                            # quads
                            # Note: in obj files the first index is 1, so we must subtract one for each
                            # retrieved value
                            vi_1, vi_2, vi_3, vi_4 = data[1:5]
                            self.quad_indices.extend((int(vi_1) - 1, int(vi_2) - 1, int(vi_3) - 1, int(vi_4) - 1))

                        elif len(data) == 4:
                            # triangles
                            # Note: in obj files the first index is 1, so we must subtract one for each
                            # retrieved value
                            vi_1, vi_2, vi_3 = data[1:4]
                            self.triangle_indices.extend((int(vi_1) - 1, int(vi_2) - 1, int(vi_3) - 1))


class Cube(object):
    """
    Bounding box
    """

    def __init__(self, v_min: list, edge_length: float):
        """
        :param v_min: the minimum vertex of the cube (closest to origin)
        :param edge_length: the length of each edge (currently always a perfect cube)
        """

        self.v_min = v_min
        self.edge_length = edge_length
        self.centre = [j + 0.5 * edge_length for j in v_min]

    def __repr__(self):
        return "Cube from {0} with edge length {1}".format(self.v_min, self.edge_length)


class Window(pyglet.window.Window):
    """
    Takes care of all the viewing functionality
    """

    def __init__(self, *args, ** kwargs):
        super().__init__(*args, **kwargs)

        # Load models from files
        self.models = []
        self.model_names = ['box.obj', 'uv_sphere.obj', 'pyramid.obj']
        for name in self.model_names:
            self.models.append(OBJModel((0, 0, 0), path=os.path.join('obj', name)))

        self.world = World([0, 0, -DIST_BACK], self.models)

        @self.event
        def on_resize(width, height):
            # sets the viewport
            gl.glViewport(0, 0, width, height)

            # sets the projection
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            glu.gluPerspective(90.0, width / height, 0.1, 10000.0)

            # sets the model view
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glLoadIdentity()

            return pyglet.event.EVENT_HANDLED

        @self.event
        def on_draw():
            self.world.draw()

        @self.event
        def on_key_press(symbol, _modifiers):
            if symbol == pyglet.window.key.ESCAPE:
                # exit
                self.close()

        @self.event
        def on_mouse_scroll(_x, _y, _scroll_x, scroll_y):
            # scroll the MOUSE WHEEL to zoom
            self.world.z += scroll_y / 0.5

        @self.event
        def on_mouse_drag(_x, _y, dx, dy, button, _modifiers):
            # click the LEFT MOUSE BUTTON to rotate
            if button == pyglet.window.mouse.LEFT:
                self.world.ry += dx / 5.0
                self.world.rx -= dy / 5.0

            # click the LEFT and RIGHT MOUSE BUTTONS simultaneously to pan
            if button == pyglet.window.mouse.LEFT | pyglet.window.mouse.RIGHT:
                self.world.x += dx / 10.0
                self.world.y += dy / 10.0

        @self.event
        def update(_dt):
            self.world.update()

        pyglet.clock.schedule_interval(update, 1/60)


if __name__ == "__main__":
    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    Window(config=config, width=1200, height=900, caption='Colour Viewer', resizable=True)
    pyglet.app.run()
