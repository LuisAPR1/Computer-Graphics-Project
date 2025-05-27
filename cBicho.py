class Bicho:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.max_health = 0
        self.health = 0
        self.state = 0

    def set_pos(self, x, y, z):
        self.x, self.y, self.z = x, y, z
    def set_x(self, x): self.x = x
    def set_y(self, y): self.y = y
    def set_z(self, z): self.z = z
    def get_x(self): return self.x
    def get_y(self): return self.y
    def get_z(self): return self.z

    def set_vel(self, vx, vy, vz):
        self.vx, self.vy, self.vz = vx, vy, vz
    def set_vx(self, vx): self.vx = vx
    def set_vy(self, vy): self.vy = vy
    def set_vz(self, vz): self.vz = vz
    def get_vx(self): return self.vx
    def get_vy(self): return self.vy
    def get_vz(self): return self.vz

    def set_yaw(self, ang): self.yaw = ang
    def set_pitch(self, ang): self.pitch = ang
    def get_yaw(self): return self.yaw
    def get_pitch(self): return self.pitch

    def set_state(self, s): self.state = s
    def get_state(self): return self.state

    def set_max_health(self, max_h): self.max_health = max_h
    def get_max_health(self): return self.max_health
    def set_health(self, h): self.health = h
    def get_health(self): return self.health 