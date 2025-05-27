import math
from OpenGL.GL import *
from OpenGL.GLU import *

COLUMN_HEIGHT = 7.0
ENERGY_BALL_RADIUS = 1.0
GATHERNG_AREA_SIDE = 4.0

class Column:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.yaw = 0.0

    def draw(self, Shader, Model, Data, id):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_COLUMN'))
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_COLUMN_NMAP'))
        glDisable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        Shader.activate('PROGRAM_COMPLEX_NORMALMAP')
        Shader.set_uniform('colorMap', 0)
        Shader.set_uniform('normalMap', 1)
        Shader.set_uniform('invRadius', 0.0)
        Shader.set_uniform('alpha', 1.0)
        Model.draw('MODEL_COLUMN')
        Shader.deactivate()
        # color dye
        if id == 0:
            glColor3f(1.0, 0.0, 0.0)
        elif id == 1:
            glColor3f(1.0, 1.0, 0.0)
        elif id == 2:
            glColor3f(0.0, 1.0, 0.0)
        elif id == 3:
            glColor3f(0.1, 0.1, 1.0)
        elif id == 4:
            glColor3f(1.0, 0.0, 1.0)
        glTranslatef(0, COLUMN_HEIGHT + ENERGY_BALL_RADIUS, 0)
        glEnable(GL_BLEND)
        quad = gluNewQuadric()
        Shader.activate('PROGRAM_SIMPLE_LIGHTBALL')
        gluSphere(quad, ENERGY_BALL_RADIUS, 32, 32)
        Shader.deactivate()
        gluDeleteQuadric(quad)
        glDisable(GL_BLEND)
        glColor4f(1, 1, 1, 1)
        glPopMatrix()

    def set_column(self, x, y, z, yaw):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw

    def inside_gathering_area(self, posx, posy, posz):
        if self.yaw == -90:
            return (posz <= self.z + GATHERNG_AREA_SIDE/2 and posz >= self.z - GATHERNG_AREA_SIDE/2 and posx <= self.x and posx >= self.x - GATHERNG_AREA_SIDE)
        elif self.yaw == 90:
            return (posz <= self.z + GATHERNG_AREA_SIDE/2 and posz >= self.z - GATHERNG_AREA_SIDE/2 and posx <= self.x + GATHERNG_AREA_SIDE and posx >= self.x)
        else: # yaw == 180
            return (posz <= self.z and posz >= self.z - GATHERNG_AREA_SIDE and posx <= self.x + GATHERNG_AREA_SIDE/2 and posx >= self.x - GATHERNG_AREA_SIDE/2)

    def get_x(self):
        return self.x
    def get_y(self):
        return self.y
    def get_z(self):
        return self.z
    def get_hole_x(self):
        if self.yaw == -90:
            return self.x - 1.5
        elif self.yaw == 90:
            return self.x + 1.5
        else: # yaw == 180
            return self.x
    def get_hole_y(self):
        return self.y + 1.0
    def get_hole_z(self):
        if self.yaw == 180:
            return self.z - 1.5
        else:
            return self.z
    def get_yaw(self):
        return self.yaw 