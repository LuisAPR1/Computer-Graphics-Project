from OpenGL.GL import *
from PIL import Image
import numpy as np

TEXTURE_FILES = {
    'IMG_GRASS': 'Textures/grass.png',
    'IMG_ROCK': 'Textures/rock.png',
    'IMG_LAVA': 'Textures/lava.png',
    'IMG_SKYBOX': 'Textures/skybox.png',
    'IMG_PLAYER': 'Textures/player.png',
    'IMG_PLAYER_NMAP': 'Textures/playerNmap.png',
    'IMG_CIRCLE_ON': 'Textures/circle_on.png',
    'IMG_CIRCLE_OFF': 'Textures/circle_off.png',
    'IMG_VORTEX': 'Textures/vortex.png',
    'IMG_KEY': 'Textures/key.png',
    'IMG_KEY_NMAP': 'Textures/keyNmap.png',
    'IMG_PORTAL': 'Textures/portal.png',
    'IMG_PORTAL_NMAP': 'Textures/portalNmap.png',
    'IMG_COLUMN': 'Textures/column.png',
    'IMG_COLUMN_NMAP': 'Textures/columnNmap.png',
}

class Data:
    def __init__(self):
        self.textures = {}
        self.sizes = {}

    def load(self):
        for key, path in TEXTURE_FILES.items():
            try:
                img = Image.open(path).convert('RGBA')
                img_data = np.array(img)
                width, height = img.size
                tex_id = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, tex_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
                glGenerateMipmap(GL_TEXTURE_2D)
                self.textures[key] = tex_id
                self.sizes[key] = (width, height)
            except Exception as e:
                print(f'Erro ao carregar textura {path}: {e}')

    def get_id(self, key):
        return self.textures.get(key, 0)

    def get_size(self, key):
        return self.sizes.get(key, (0, 0)) 