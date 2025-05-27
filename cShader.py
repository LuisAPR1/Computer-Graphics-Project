from OpenGL.GL import *

SHADER_PROGRAMS = {
    'PROGRAM_SIMPLE_TERRAIN': ('Shaders/simple.vert', 'Shaders/terrain.frag'),
    'PROGRAM_SIMPLE_LIGHTBEAM': ('Shaders/simple.vert', 'Shaders/lightbeam.frag'),
    'PROGRAM_SIMPLE_LIGHTBALL': ('Shaders/simple.vert', 'Shaders/lightball.frag'),
    'PROGRAM_COMPLEX_NORMALMAP_LAVAGLOW': ('Shaders/complex.vert', 'Shaders/lavaglow.frag'),
    'PROGRAM_COMPLEX_NORMALMAP': ('Shaders/complex.vert', 'Shaders/normalmap.frag'),
    'PROGRAM_COMPLEX_DIDGERIDOO': ('Shaders/complex.vert', 'Shaders/didgeridoo.frag'),
    'PROGRAM_COMPLEX_CRUMHORN': ('Shaders/complex.vert', 'Shaders/crumhorn.frag'),
    'PROGRAM_COMPLEX_VUVUZELA': ('Shaders/complex.vert', 'Shaders/vuvuzela.frag'),
    'PROGRAM_COMPLEX_MANDOLINE': ('Shaders/complex.vert', 'Shaders/mandoline.frag'),
}

class Shader:
    def __init__(self):
        self.programs = {}
        self.current_prog_id = None

    def _load_shader_source(self, filename):
        with open(filename, 'r') as f:
            return f.read()

    def _compile_shader(self, source, shader_type, name=''):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        # Check compilation
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error = glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f'Error compiling {name} shader: {error}')
        return shader

    def load(self):
        for key, (vert_path, frag_path) in SHADER_PROGRAMS.items():
            program = glCreateProgram()

            # Load sources
            vert_src = self._load_shader_source(vert_path)
            frag_src = self._load_shader_source(frag_path)

            # Compile shaders
            vert_shader = self._compile_shader(vert_src, GL_VERTEX_SHADER, vert_path)
            frag_shader = self._compile_shader(frag_src, GL_FRAGMENT_SHADER, frag_path)

            # Attach and link
            glAttachShader(program, vert_shader)
            glAttachShader(program, frag_shader)
            glLinkProgram(program)

            # Check linking
            if not glGetProgramiv(program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(program).decode()
                raise RuntimeError(f'Error linking program {key}: {error}')

            # Clean up shaders
            glDeleteShader(vert_shader)
            glDeleteShader(frag_shader)

            self.programs[key] = program

    def activate(self, program_id):
        if program_id not in self.programs:
            raise ValueError(f"Program '{program_id}' not loaded.")
        glUseProgram(self.programs[program_id])
        self.current_prog_id = program_id

    def deactivate(self):
        glUseProgram(0)
        self.current_prog_id = None

    def set_uniform(self, uniform, value):
        if self.current_prog_id is None:
            return
        loc = glGetUniformLocation(self.programs[self.current_prog_id], uniform)
        if loc == -1:
            return
        if isinstance(value, int):
            glUniform1i(loc, value)
        elif isinstance(value, float):
            glUniform1f(loc, value)
        else:
            raise TypeError("Unsupported uniform type.")

    def get_location(self, uniform):
        if self.current_prog_id is None:
            return -1
        return glGetUniformLocation(self.programs[self.current_prog_id], uniform)
