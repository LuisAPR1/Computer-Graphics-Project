from OpenGL.GL import *
from OpenGL.GLU import *
import math

STATE_FPS = 0
STATE_TPS = 1
STATE_TPS_FREE = 2
PI = math.pi
CAMERA_MAX_DISTANCE = 10.0
CAMERA_SMOOTHING_SPEED = 0.03  # Was 0.01, increase for faster smoothing
CAMERA_SPEED = PI/180*0.2

class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.yaw = 0.0
        self.last_yaw = 0.0
        self.pitch = -PI/2
        self.distance = 0.4
        self.lambda_ = 1.0
        self.state = STATE_TPS

    def refresh(self):
        self.vx = math.cos(self.yaw) * math.cos(self.pitch)
        self.vy = math.sin(self.pitch)
        self.vz = math.sin(self.yaw) * math.cos(self.pitch)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.x, self.y, self.z,
                  self.x + self.vx, self.y + self.vy, self.z + self.vz,
                  0, 1, 0)

    def get_lava_lambda(self, Py, Qy, height):
        Vy = Qy - Py
        D = -height
        if Vy == 0.0:
            return 1.0
        lambda_ = -(Py + D) / Vy
        if lambda_ < 0.0 or lambda_ > 1.0:
            return 1.0
        return lambda_

    def update(self, Terrain, Lava, player_x, player_y, player_z):
        self.vx = math.cos(self.yaw) * math.cos(self.pitch)
        self.vy = math.sin(self.pitch)
        self.vz = math.sin(self.yaw) * math.cos(self.pitch)
        # Câmera segue o player
        if self.get_state() == STATE_FPS:
            self.set_pos(player_x, player_y + 0.5, player_z)
        else:
            # Colisão com terreno e lava (igual ao C++)
            if hasattr(Terrain, 'get_segment_intersection_lambda'):
                new_lambda = Terrain.get_segment_intersection_lambda(
                    player_x, player_y, player_z,
                    self.vx, self.vy, self.vz, CAMERA_MAX_DISTANCE)
            else:
                new_lambda = 1.0
            if Lava is not None and hasattr(Lava, 'get_height'):
                lava_lambda = self.get_lava_lambda(player_y, player_y - CAMERA_MAX_DISTANCE * self.vy, Lava.get_height())
                new_lambda = min(new_lambda, lava_lambda)
            # Suavização
            if self.lambda_ < new_lambda:
                self.lambda_ += CAMERA_SMOOTHING_SPEED
                if self.lambda_ > new_lambda:
                    self.lambda_ = new_lambda
            else:
                self.lambda_ = new_lambda
            self.distance = CAMERA_MAX_DISTANCE * self.lambda_ * 0.85
            self.set_pos(player_x - self.distance * self.vx,
                         player_y - self.distance * self.vy,
                         player_z - self.distance * self.vz)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.x, self.y, self.z,
                  self.x + self.vx, self.y + self.vy, self.z + self.vz,
                  0, 1, 0)

    def set_state(self, s):
        self.state = s
    def get_state(self):
        return self.state
    def set_pos(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.refresh()
    def get_distance(self):
        return self.distance
    def get_direction_vector(self):
        return self.vx, self.vy, self.vz
    def rotate_yaw(self, angle):
        self.yaw += angle
        self.refresh()
    def set_yaw(self, angle):
        self.yaw = angle
    def get_yaw(self):
        return self.yaw
    def set_last_yaw(self, angle):
        self.last_yaw = angle
    def get_last_yaw(self):
        return self.last_yaw
    def rotate_pitch(self, angle):
        limit = 89.0 * PI / 180.0
        self.pitch += angle
        if self.pitch < -limit:
            self.pitch = -limit
        if self.pitch > limit:
            self.pitch = limit
        self.refresh()
    def set_pitch(self, angle):
        self.pitch = angle
    def get_pitch(self):
        return self.pitch
    def get_x(self):
        return self.x
    def get_y(self):
        return self.y
    def get_z(self):
        return self.z