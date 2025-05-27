import numpy as np
from OpenGL.GL import *
from PIL import Image

TERRAIN_SIZE = 1024
MAX_HEIGHT = 64.0
SCALE_FACTOR = 256.0 / MAX_HEIGHT

class Coord:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class Vector:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class Triangle:
    def __init__(self):
        self.N = Vector()
        self.barycenter = Coord()
        self.vertexs = [Coord(), Coord(), Coord()]

class Terrain:
    def __init__(self):
        self.heightmap = [0] * (TERRAIN_SIZE * TERRAIN_SIZE)
        self.triangles = []
        self.tex_grass = None
        self.tex_rock = None
        self.tex_lava = None
        # VBO/VAO attributes
        self.vbo_vertices = None
        self.vbo_normals = None
        self.vbo_texcoords = None
        self.vbo_indices = None
        self.index_count = 0

    def load(self, level):
        if level < 10:
            filename = f"Levels/terrain0{level}.raw"
        else:
            filename = f"Levels/terrain{level}.raw"
        try:
            with open(filename, "rb") as f:
                data = f.read(TERRAIN_SIZE * TERRAIN_SIZE)
                self.heightmap = list(data)
        except Exception as e:
            print(f"Erro ao carregar heightmap: {e}")
            self.heightmap = [0] * (TERRAIN_SIZE * TERRAIN_SIZE)
        self.build_vbo()  # Build VBOs after loading heightmap

    def load_textures(self):
        # Carrega as texturas de grass, rock e lava
        self.tex_grass = self._load_texture('Textures/grass.png')
        self.tex_rock = self._load_texture('Textures/rock.png')
        self.tex_lava = self._load_texture('Textures/lava.png')

    def _load_texture(self, filename):
        img = Image.open(filename)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGB").tobytes()
        width, height = img.size
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return tex_id

    def get_vertex_height(self, x, z):
        idx = int(z) * TERRAIN_SIZE + int(x)
        if 0 <= idx < len(self.heightmap):
            return self.heightmap[idx] / SCALE_FACTOR
        return 0.0

    def get_height(self, x, z):
        if x < 0 or x > TERRAIN_SIZE-1 or z < 0 or z > TERRAIN_SIZE-1:
            return 0.0
        intx = int(x)
        intz = int(z)
        fracx = x - intx
        fracz = z - intz
        h00 = self.get_vertex_height(intx, intz)
        h10 = self.get_vertex_height(intx+1, intz)
        h01 = self.get_vertex_height(intx, intz+1)
        h11 = self.get_vertex_height(intx+1, intz+1)
        h0 = h00 * (1 - fracx) + h10 * fracx
        h1 = h01 * (1 - fracx) + h11 * fracx
        return h0 * (1 - fracz) + h1 * fracz

    def cubic_interp(self, p0, p1, p2, p3, t):
        # Interpolação cúbica de Catmull-Rom
        return (
            0.5 * (
                (2 * p1) +
                (-p0 + p2) * t +
                (2*p0 - 5*p1 + 4*p2 - p3) * t * t +
                (-p0 + 3*p1 - 3*p2 + p3) * t * t * t
            )
        )

    def get_height_bicubic(self, x, z):
        # Garante que x e z estão dentro dos limites
        if x < 1: x = 1
        if x > TERRAIN_SIZE - 3: x = TERRAIN_SIZE - 3
        if z < 1: z = 1
        if z > TERRAIN_SIZE - 3: z = TERRAIN_SIZE - 3

        intx = int(x)
        intz = int(z)
        fracx = x - intx
        fracz = z - intz

        # Pega 4x4 amostras ao redor do ponto
        heights = []
        for dz in range(-1, 3):
            row = []
            for dx in range(-1, 3):
                row.append(self.get_vertex_height(intx + dx, intz + dz))
            heights.append(row)

        # Interpola nas linhas (x)
        col_heights = []
        for row in heights:
            col_heights.append(self.cubic_interp(row[0], row[1], row[2], row[3], fracx))
        # Interpola entre as linhas (z)
        return self.cubic_interp(col_heights[0], col_heights[1], col_heights[2], col_heights[3], fracz)

    def build_vbo(self):
        step = 2  # Same as before for performance
        vertices = []
        normals = []
        texcoords = []
        indices = []
        w = TERRAIN_SIZE
        h = TERRAIN_SIZE
        vert_index = {}
        idx = 0
        for z in range(0, h-1, step):
            for x in range(0, w-1, step):
                quad = []
                for dz, dx in [(0,0), (0,step), (step,step), (step,0)]:
                    vx = x + dx
                    vz = z + dz
                    vy = self.get_vertex_height(vx, vz)
                    vertices.extend([vx, vy, vz])
                    nx, ny, nz = self._compute_normal(vx, vy, vz)
                    normals.extend([nx, ny, nz])
                    texcoords.extend([vx / w * 16, vz / h * 16])
                    quad.append(idx)
                    idx += 1
                # Two triangles per quad
                indices.extend([quad[0], quad[1], quad[2], quad[0], quad[2], quad[3]])
        self.index_count = len(indices)
        vertices = np.array(vertices, dtype=np.float32)
        normals = np.array(normals, dtype=np.float32)
        texcoords = np.array(texcoords, dtype=np.float32)
        indices = np.array(indices, dtype=np.uint32)
        # Generate and bind VBOs
        if self.vbo_vertices:
            glDeleteBuffers(1, [self.vbo_vertices])
        if self.vbo_normals:
            glDeleteBuffers(1, [self.vbo_normals])
        if self.vbo_texcoords:
            glDeleteBuffers(1, [self.vbo_texcoords])
        if self.vbo_indices:
            glDeleteBuffers(1, [self.vbo_indices])
        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        self.vbo_normals = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        self.vbo_texcoords = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_texcoords)
        glBufferData(GL_ARRAY_BUFFER, texcoords.nbytes, texcoords, GL_STATIC_DRAW)
        self.vbo_indices = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo_indices)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def draw(self, data=None):
        if not self.vbo_vertices or not self.vbo_normals or not self.vbo_texcoords or not self.vbo_indices:
            return
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glVertexPointer(3, GL_FLOAT, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glNormalPointer(GL_FLOAT, 0, None)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_texcoords)
        glTexCoordPointer(2, GL_FLOAT, 0, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.vbo_indices)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)

    def _compute_normal(self, x, y, z):
        def get_height(xx, zz):
            if 0 <= xx < TERRAIN_SIZE and 0 <= zz < TERRAIN_SIZE:
                return self.get_vertex_height(xx, zz)
            return y
        left_y  = get_height(x-1, z) if x > 0 else y
        right_y = get_height(x+1, z) if x < TERRAIN_SIZE-1 else y
        up_y    = get_height(x, z-1) if z > 0 else y
        down_y  = get_height(x, z+1) if z < TERRAIN_SIZE-1 else y
        X = [2.0, right_y - left_y, 0.0]
        Z = [0.0, down_y - up_y, 2.0]
        N = [
            Z[1]*X[2] - Z[2]*X[1],
            Z[2]*X[0] - Z[0]*X[2],
            Z[0]*X[1] - Z[1]*X[0]
        ]
        norm = (N[0]**2 + N[1]**2 + N[2]**2) ** 0.5
        if norm == 0:
            return 0.0, 1.0, 0.0
        return N[0]/norm, N[1]/norm, N[2]/norm