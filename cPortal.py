import math
from OpenGL.GL import *
from OpenGL.GLU import *

PORTAL_SIDE = 3.0
PORTAL_SPEED = 2.0

class Portal:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.ang = 0.0
        self.receptors = [(0.0, 0.0) for _ in range(5)]

    def draw(self, Data, activated, Shader, Model):
        # Save current OpenGL states
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glPushMatrix()
        
        # vortex
        if activated:
            glPushMatrix()
            glTranslatef(self.x, self.y, self.z)
            self.ang = math.fmod(self.ang + PORTAL_SPEED, 360)
            glTranslatef(0, PORTAL_SIDE/2, 0)
            glRotatef(self.ang, 0.0, 0.0, 1.0)
            glDisable(GL_LIGHTING)
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glDisable(GL_CULL_FACE)
            glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_VORTEX'))
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 1.0); glVertex3f(PORTAL_SIDE/2, -PORTAL_SIDE/2, 0)
            glTexCoord2f(1.0, 1.0); glVertex3f(-PORTAL_SIDE/2, -PORTAL_SIDE/2, 0)
            glTexCoord2f(1.0, 0.0); glVertex3f(-PORTAL_SIDE/2, PORTAL_SIDE/2, 0)
            glTexCoord2f(0.0, 0.0); glVertex3f(PORTAL_SIDE/2, PORTAL_SIDE/2, 0)
            glEnd()
            glEnable(GL_CULL_FACE)
            glDisable(GL_BLEND)
            glDisable(GL_TEXTURE_2D)
            glEnable(GL_LIGHTING)
            glPopMatrix()
            
        # portal
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        
        # Set up textures
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_PORTAL'))
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, Data.get_id('IMG_PORTAL_NMAP'))
        
        # Set up shader
        Shader.activate('PROGRAM_COMPLEX_NORMALMAP')
        Shader.set_uniform('colorMap', 0)
        Shader.set_uniform('normalMap', 1)
        Shader.set_uniform('invRadius', 0.0)
        Shader.set_uniform('alpha', 1.0)
        
        # Draw the portal model
        Model.draw('MODEL_PORTAL')
        
        # Clean up shader
        Shader.deactivate()
        
        # Draw light balls
        glEnable(GL_BLEND)
        quad = gluNewQuadric()
        glTranslatef(0, PORTAL_SIDE*3/2, 0)
        glColor3f(0.0, 1.0, 0.0)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBALL')
        gluSphere(quad, 0.2, 16, 16)
        Shader.deactivate()
        glTranslatef(PORTAL_SIDE/2, -PORTAL_SIDE/2, 0)
        glColor3f(1.0, 1.0, 0.0)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBALL')
        gluSphere(quad, 0.2, 16, 16)
        Shader.deactivate()
        glTranslatef(-PORTAL_SIDE, 0, 0)
        glColor3f(0.2, 0.2, 1.0)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBALL')
        gluSphere(quad, 0.2, 16, 16)
        Shader.deactivate()
        glTranslatef(0, -(PORTAL_SIDE-1), 0)
        glColor3f(1.0, 0.0, 1.0)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBALL')
        gluSphere(quad, 0.2, 16, 16)
        Shader.deactivate()
        glTranslatef(PORTAL_SIDE, 0, 0)
        glColor3f(1.0, 0.0, 0.0)
        Shader.activate('PROGRAM_SIMPLE_LIGHTBALL')
        gluSphere(quad, 0.2, 16, 16)
        Shader.deactivate()
        gluDeleteQuadric(quad)
        glDisable(GL_BLEND)
        glColor4f(1, 1, 1, 1)
        
        # Clean up textures
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        
        glPopMatrix()
        
        # Restore OpenGL states
        glPopMatrix()
        glPopAttrib()

    def set_pos(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        # vermelho
        self.receptors[0] = (self.x + PORTAL_SIDE/2, self.y + 1.0)
        # amarelo
        self.receptors[1] = (self.x + PORTAL_SIDE/2, self.y + PORTAL_SIDE)
        # verde
        self.receptors[2] = (self.x, self.y + PORTAL_SIDE*3/2)
        # azul
        self.receptors[3] = (self.x - PORTAL_SIDE/2, self.y + PORTAL_SIDE)
        # violeta
        self.receptors[4] = (self.x - PORTAL_SIDE/2, self.y + 1.0)

    def inside_portal(self, px, py, pz, r):
        return ((px - r <= self.x + (PORTAL_SIDE/2) and px + r >= self.x - (PORTAL_SIDE/2)) and
                (py - r <= self.y + PORTAL_SIDE and py + r >= self.y))

    def get_x(self):
        return self.x
    def get_y(self):
        return self.y
    def get_z(self):
        return self.z
    def get_receptor_x(self, i):
        return self.receptors[i][0]
    def get_receptor_y(self, i):
        return self.receptors[i][1] 