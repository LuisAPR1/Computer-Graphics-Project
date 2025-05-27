import math
from OpenGL.GL import *

FLOW_SPEED = 0.2
LAVA_HEIGHT_MAX = 4.0
LAVA_HEIGHT_MIN = 1.0
PI = math.pi

class Lava:
    def __init__(self):
        self.height = (LAVA_HEIGHT_MAX + LAVA_HEIGHT_MIN) / 2.0
        self.ang = 0.0
        self.up = True
        self.terrain_size = 0.0

    def load(self, terrain_size):
        self.terrain_size = terrain_size
        # Não usa display lists, apenas armazena o tamanho

    def draw(self, tex_id, shader):
        glPushMatrix()
        glTranslatef(0.0, self.height, 0.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0*16); glVertex3f(self.terrain_size, 0.0, 0.0)
        glTexCoord2f(1.0*16, 1.0*16); glVertex3f(0.0, 0.0, 0.0)
        glTexCoord2f(1.0*16, 0.0); glVertex3f(0.0, 0.0, self.terrain_size)
        glTexCoord2f(0.0, 0.0); glVertex3f(self.terrain_size, 0.0, self.terrain_size)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

    def get_height(self):
        return self.height

    def get_height_max(self):
        return LAVA_HEIGHT_MAX

    def update(self):
        if self.up:
            self.ang = math.fmod(self.ang + FLOW_SPEED, 360)
            self.height = ((LAVA_HEIGHT_MAX - LAVA_HEIGHT_MIN)/2.0) * math.sin(self.ang * (PI/180)) + (LAVA_HEIGHT_MAX + LAVA_HEIGHT_MIN)/2.0
            self.up = (self.height < LAVA_HEIGHT_MAX)
        else:
            self.ang = math.fmod(self.ang - FLOW_SPEED, 360)
            self.height = ((LAVA_HEIGHT_MAX - LAVA_HEIGHT_MIN)/2.0) * math.sin(self.ang * (PI/180)) + (LAVA_HEIGHT_MAX + LAVA_HEIGHT_MIN)/2.0
            self.up = (self.height <= LAVA_HEIGHT_MIN) 