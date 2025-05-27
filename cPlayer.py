from OpenGL.GL import *
from OpenGL.GLU import *
import math
from cBicho import Bicho

class Player(Bicho):
    def __init__(self):
        super().__init__()
        self.fade = True

    def set_fade(self, b):
        self.fade = b

    def draw(self, Data, Camera, Lava, Shader):
        glPushMatrix()
        glTranslatef(self.get_x(), self.get_y(), self.get_z())
        yaw_rad = math.radians(self.get_yaw())
        pitch = self.get_pitch()
        if math.cos(yaw_rad) >= 0.0:
            glRotatef(pitch, math.cos(yaw_rad), 0.0, -math.sin(yaw_rad))
        else:
            glRotatef(pitch, -math.cos(yaw_rad), 0.0, math.sin(yaw_rad))
        # Exemplo simples (sem shader):
        if Camera is None or getattr(Camera, 'get_state', lambda: None)() != 'STATE_FPS':
            glColor3f(1, 1, 1)
            quad = gluNewQuadric()
            gluSphere(quad, 0.5, 16, 16)  # RADIUS = 0.5
            gluDeleteQuadric(quad)
        glPopMatrix() 