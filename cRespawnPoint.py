from OpenGL.GL import *
from OpenGL.GLU import *

CIRCLE_RADIUS = 2.0
AURA_HEIGHT = 3.0
HEIGHT_OFFSET = 0.05

class RespawnPoint:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

    def draw(self, tex_id, activated, Shader):
        glPushMatrix()
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glTranslatef(self.x, self.y + HEIGHT_OFFSET, self.z)
        # circle
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex3f(CIRCLE_RADIUS, 0, -CIRCLE_RADIUS)
        glTexCoord2f(1.0, 1.0); glVertex3f(-CIRCLE_RADIUS, 0, -CIRCLE_RADIUS)
        glTexCoord2f(1.0, 0.0); glVertex3f(-CIRCLE_RADIUS, 0, CIRCLE_RADIUS)
        glTexCoord2f(0.0, 0.0); glVertex3f(CIRCLE_RADIUS, 0, CIRCLE_RADIUS)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        # aura
        glDepthMask(GL_FALSE)
        glDisable(GL_CULL_FACE)
        quad = gluNewQuadric()
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        if activated:
            glColor4f(1.0, 0.4, 0.0, 0.6)
        else:
            glColor4f(0.5, 0.5, 1.0, 0.6)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBEAM')
        Shader.set_uniform('hmax', AURA_HEIGHT)
        gluCylinder(quad, CIRCLE_RADIUS, CIRCLE_RADIUS, AURA_HEIGHT, 16, 16)
        Shader.deactivate()
        glTranslatef(0, 0, HEIGHT_OFFSET)
        gluDisk(quad, 0, CIRCLE_RADIUS, 16, 16)
        glColor4f(1, 1, 1, 1)
        gluDeleteQuadric(quad)
        glEnable(GL_CULL_FACE)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
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