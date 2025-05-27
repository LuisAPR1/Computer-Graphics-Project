from OpenGL.GL import *

MODEL_FILES = {
    'MODEL_KEY': 'Models/key.obj',
    'MODEL_PORTAL': 'Models/portal.obj',
    'MODEL_COLUMN': 'Models/column.obj',
    'MODEL_CRUMHORN': 'Models/Instruments/crumhorn.obj',
    'MODEL_VUVUZELA': 'Models/Instruments/vuvuzela.obj',
    'MODEL_DIGERIDOO': 'Models/Instruments/digeridoo.obj',
    'MODEL_MANDOLINE': 'Models/Instruments/mandoline.obj',
    'MODEL_HAND_IDLE': 'Models/hands.obj'
}

class Model:
    def __init__(self):
        self.models = {} # Stores raw model data (vertices, faces, etc.)
        self.display_lists = {} # Stores compiled display list IDs

    def _load_obj(self, path):
        vertexs = []
        texcoords = []
        normals = []
        faces = []
        try:
            with open(path, 'r') as f:
                for line in f:
                    if line.startswith('v '):
                        parts = line.strip().split()
                        vertexs.append(tuple(map(float, parts[1:4])))
                    elif line.startswith('vt '):
                        parts = line.strip().split()
                        texcoords.append(tuple(map(float, parts[1:3])))
                    elif line.startswith('vn '):
                        parts = line.strip().split()
                        normals.append(tuple(map(float, parts[1:4])))
                    elif line.startswith('f '):
                        face = []
                        for v_data in line.strip().split()[1:]:
                            vals = v_data.split('/')
                            vi = int(vals[0]) - 1
                            ti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else -1 # Use -1 for missing
                            ni = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else -1 # Use -1 for missing
                            face.append((vi, ti, ni))
                        faces.append(face)
        except FileNotFoundError:
            print(f"Error: Model file not found at {path}")
            return None, None, None, None # Indicate loading failure
        except Exception as e:
            print(f"Error loading OBJ file {path}: {e}")
            return None, None, None, None # Indicate loading failure
        return vertexs, texcoords, normals, faces

    def load(self):
        for key, path in MODEL_FILES.items():
            data = self._load_obj(path)
            if data[0] is not None: # Check if loading was successful (vertexs is not None)
                self.models[key] = data
            else:
                print(f"Failed to load model: {key} from {path}")

    def _render_model_immediate(self, model_id):
        if model_id not in self.models:
            # print(f"Warning: Model {model_id} not found for immediate rendering.")
            return
        vertexs, texcoords, normals, faces = self.models[model_id]
        if not vertexs: # Extra check if model data is empty
            # print(f"Warning: Model {model_id} has no vertex data.")
            return

        for face in faces:
            if len(face) == 3:
                glBegin(GL_TRIANGLES)
            elif len(face) == 4:
                glBegin(GL_QUADS)
            else:
                glBegin(GL_POLYGON)
            for vi, ti, ni in face:
                if normals and ni != -1 and ni < len(normals):
                    glNormal3f(*normals[ni])
                if texcoords and ti != -1 and ti < len(texcoords):
                    glTexCoord2f(*texcoords[ti])
                glVertex3f(*vertexs[vi])
            glEnd()

    def create_display_list(self, model_id):
        if model_id not in self.models:
            print(f"Cannot create display list: Model {model_id} not loaded.")
            return
        if model_id in self.display_lists:
            # print(f"Display list for {model_id} already exists.")
            return self.display_lists[model_id]

        list_id = glGenLists(1)
        glNewList(list_id, GL_COMPILE)
        self._render_model_immediate(model_id) # Use the immediate mode rendering logic
        glEndList()
        self.display_lists[model_id] = list_id
        # print(f"Created display list for {model_id} with ID: {list_id}")
        return list_id

    def draw(self, model_id, use_display_list=True):
        if use_display_list and model_id in self.display_lists:
            # print(f"Drawing {model_id} using display list {self.display_lists[model_id]}")
            glCallList(self.display_lists[model_id])
        elif model_id in self.models:
            # print(f"Drawing {model_id} using immediate mode.")
            self._render_model_immediate(model_id)
        else:
            print(f"Warning: Model {model_id} not found for drawing.")