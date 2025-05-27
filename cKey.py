import math
from OpenGL.GL import *
from OpenGL.GLU import *

LEVITATION_SPEED = 2.0
BEACON_MIN_RADIUS = 0.75
BEACON_HEIGHT = 140.0

class Key:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.ang = 0.0
        self.deployed = False

    def draw_levitating(self, Shader, Model, Data, dist):
        quad = gluNewQuadric()
        glPushMatrix()
        self.ang = math.fmod(self.ang + LEVITATION_SPEED, 360)
        glTranslatef(self.x, self.y + 0.5 + (math.sin(self.ang * math.pi / 180)) / 2, self.z)
        glRotatef(self.ang, 0.0, 1.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_KEY'))
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_KEY_NMAP'))
        glDisable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        Shader.activate('PROGRAM_COMPLEX_NORMALMAP')
        Shader.set_uniform('colorMap', 0)
        Shader.set_uniform('normalMap', 1)
        Shader.set_uniform('invRadius', 0.0)
        Shader.set_uniform('alpha', 1.0)
        Model.draw('MODEL_KEY')
        Shader.deactivate()
        glPopMatrix()
        # beacon
        glPushMatrix()
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glDisable(GL_CULL_FACE)
        glTranslatef(self.x, self.y, self.z)
        glRotatef(-90, 1.0, 0.0, 0.0)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBEAM')
        Shader.set_uniform('hmax', BEACON_HEIGHT - self.y)
        radius = max(dist / 100, BEACON_MIN_RADIUS)
        gluCylinder(quad, radius, radius, BEACON_HEIGHT - self.y, 16, 16)
        Shader.deactivate()
        gluDeleteQuadric(quad)
        glEnable(GL_CULL_FACE)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glPopMatrix()

    def draw_picked(self, playerx, playery, playerz, camera_yaw, Model, Data, Shader):
        glPushMatrix()
        self.ang = math.fmod(self.ang + LEVITATION_SPEED, 360)
        glTranslatef(playerx, playery + 0.7, playerz)
        glRotatef(self.ang, 0.0, 1.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_KEY'))
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_KEY_NMAP'))
        glDisable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        Shader.activate('PROGRAM_COMPLEX_NORMALMAP')
        Shader.set_uniform('colorMap', 0)
        Shader.set_uniform('normalMap', 1)
        Shader.set_uniform('invRadius', 0.0)
        Shader.set_uniform('alpha', 1.0)
        Model.draw('MODEL_KEY')
        Shader.deactivate()
        glPopMatrix()

    def draw_deployed(self, holex, holey, holez, yaw, Model, Data, Shader):
        glPushMatrix()
        glTranslatef(holex, holey, holez)
        glRotatef(yaw, 0, 1, 0)
        glRotatef(180 + 45, 1, 0, 0)
        glTranslatef(0, -0.69, 0)
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_KEY'))
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_KEY_NMAP'))
        glDisable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        Shader.activate('PROGRAM_COMPLEX_NORMALMAP')
        Shader.set_uniform('colorMap', 0)
        Shader.set_uniform('normalMap', 1)
        Shader.set_uniform('invRadius', 0.0)
        Shader.set_uniform('alpha', 1.0)
        Model.draw('MODEL_KEY')
        Shader.deactivate()
        glPopMatrix()

    def set_pos(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    def get_x(self):
        return self.x
    def get_y(self):
        return self.y
    def get_z(self):
        return self.z
    def deploy(self):
        self.deployed = True
    def is_deployed(self):
        return self.deployed 