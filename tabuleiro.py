import numpy as np
from OpenGL.GL import *
import pyrr

class Tabuleiro:
    def __init__(self):
        # Criamos uma matriz 8x8 para representar o grid do Vale
        # 0: Chão comum
        # 1: Rio Jaguaribe
        # 2: Cidade/Construção
        self.grid = np.zeros((8, 8), dtype=int)
        self.setup_map()

        self.vbo = glGenBuffers(1)
        self.generate_tile_vbo()

    def setup_map(self):
        for i in range(8):
            self.grid[i][3] = 1

        self.grid[2][2] = 2
        self.grid[5][5] = 2

    def generate_tile_vbo(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        # Vértices de um cubo unitário (x, y, z)
        vertices = np.array([
            # Face Traseira (Z = -0.5)
            -0.5, -0.5, -0.5,   0.5, -0.5, -0.5,   0.5,  0.5, -0.5,
            0.5,  0.5, -0.5,  -0.5,  0.5, -0.5,  -0.5, -0.5, -0.5,

            # Face Frontal (Z = 0.5)
            -0.5, -0.5,  0.5,   0.5, -0.5,  0.5,   0.5,  0.5,  0.5,
            0.5,  0.5,  0.5,  -0.5,  0.5,  0.5,  -0.5, -0.5,  0.5,

            # Face Esquerda (X = -0.5)
            -0.5,  0.5,  0.5,  -0.5,  0.5, -0.5,  -0.5, -0.5, -0.5,
            -0.5, -0.5, -0.5,  -0.5, -0.5,  0.5,  -0.5,  0.5,  0.5,

            # Face Direita (X = 0.5)
            0.5,  0.5,  0.5,   0.5,  0.5, -0.5,   0.5, -0.5, -0.5,
            0.5, -0.5, -0.5,   0.5, -0.5,  0.5,   0.5,  0.5,  0.5,

            # Face Inferior (Y = -0.5) - O "chão" do tile
            -0.5, -0.5, -0.5,   0.5, -0.5, -0.5,   0.5, -0.5,  0.5,
            0.5, -0.5,  0.5,  -0.5, -0.5,  0.5,  -0.5, -0.5, -0.5,

            # Face Superior (Y = 0.5) - Onde as unidades ficam
            -0.5,  0.5, -0.5,   0.5,  0.5, -0.5,   0.5,  0.5,  0.5,
            0.5,  0.5,  0.5,  -0.5,  0.5,  0.5,  -0.5,  0.5, -0.5
        ], dtype='float32')

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # 3. Explicamos para o OpenGL o layout dos dados (O QUE Faltava!)
        # Atributo 0 (aPos no shader): 3 floats (x, y, z)
        glVertexAttribPointer(
            0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, ctypes.c_void_p(0)
        )
        glEnableVertexAttribArray(0)

        # 4. Desvinculamos para evitar erros em outros objetos
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def set_tile_color(self, shader_program, tile_type):
        """
        Envia a cor para o Uniform do Shader baseada no tipo de terreno[cite: 2].
        """
        color_loc = glGetUniformLocation(shader_program, "u_color")
        
        if tile_type == 1: # Rio Jaguaribe (Azul)[cite: 2]
            glUniform3f(color_loc, 0.0, 0.4, 0.8)
        elif tile_type == 2: # Cidade (Cinza/Concreto)[cite: 2]
            glUniform3f(color_loc, 0.5, 0.5, 0.5)
        else: # Solo seco (Laranja/Sertão)[cite: 2]
            glUniform3f(color_loc, 0.8, 0.5, 0.2)

    def draw(self, shader_program):
        # Ativamos o VAO que contém todas as configurações do cubo
        glBindVertexArray(self.vao)
        
        model_loc = glGetUniformLocation(shader_program, "model")
        
        for row in range(8):
            for col in range(8):
                x_pos = col - 3.5
                z_pos = row - 3.5
                
                translation = pyrr.matrix44.create_from_translation([x_pos, -0.5, z_pos])
                glUniformMatrix4fv(model_loc, 1, GL_FALSE, translation)
                
                self.set_tile_color(shader_program, self.grid[row][col])
                
                # Agora o OpenGL sabe exatamente o que fazer com os 36 vértices
                glDrawArrays(GL_TRIANGLES, 0, 36)

        glBindVertexArray(0)
