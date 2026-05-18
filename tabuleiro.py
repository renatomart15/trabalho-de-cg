import numpy as np
from OpenGL.GL import *
import pyrr
from PIL import Image

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

        self.tex_grama = self.carregar_textura_tabuleiro("assets/grama.jpg")
        self.tex_agua = self.carregar_textura_tabuleiro("assets/agua.jpg")
        self.tex_concreto = self.carregar_textura_tabuleiro("assets/concreto.jpg")

    def setup_map(self):
        for i in range(8):
            self.grid[i][3] = 1

        self.grid[2][2] = 2
        self.grid[5][5] = 2

    def generate_tile_vbo(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Cada linha agora tem: X, Y, Z,  U, V
        vertices = np.array([
            # Face Traseira
            -0.5, -0.5, -0.5,  0.0, 0.0,
             0.5, -0.5, -0.5,  1.0, 0.0,
             0.5,  0.5, -0.5,  1.0, 1.0,
             0.5,  0.5, -0.5,  1.0, 1.0,
            -0.5,  0.5, -0.5,  0.0, 1.0,
            -0.5, -0.5, -0.5,  0.0, 0.0,

            # Face Frontal
            -0.5, -0.5,  0.5,  0.0, 0.0,
             0.5, -0.5,  0.5,  1.0, 0.0,
             0.5,  0.5,  0.5,  1.0, 1.0,
             0.5,  0.5,  0.5,  1.0, 1.0,
            -0.5,  0.5,  0.5,  0.0, 1.0,
            -0.5, -0.5,  0.5,  0.0, 0.0,

            # Face Esquerda
            -0.5,  0.5,  0.5,  1.0, 0.0,
            -0.5,  0.5, -0.5,  1.0, 1.0,
            -0.5, -0.5, -0.5,  0.0, 1.0,
            -0.5, -0.5, -0.5,  0.0, 1.0,
            -0.5, -0.5,  0.5,  0.0, 0.0,
            -0.5,  0.5,  0.5,  1.0, 0.0,

            # Face Direita
            0.5,  0.5,  0.5,  1.0, 0.0,
            0.5,  0.5, -0.5,  1.0, 1.0,
            0.5, -0.5, -0.5,  0.0, 1.0,
            0.5, -0.5, -0.5,  0.0, 1.0,
            0.5, -0.5,  0.5,  0.0, 0.0,
            0.5,  0.5,  0.5,  1.0, 0.0,

            # Face Inferior
            -0.5, -0.5, -0.5,  0.0, 1.0,
             0.5, -0.5, -0.5,  1.0, 1.0,
             0.5, -0.5,  0.5,  1.0, 0.0,
             0.5, -0.5,  0.5,  1.0, 0.0,
            -0.5, -0.5,  0.5,  0.0, 0.0,
            -0.5, -0.5, -0.5,  0.0, 1.0,

            # Face Superior (Onde o trator e as casas pisam)
            -0.5,  0.5, -0.5,  0.0, 1.0,
             0.5,  0.5, -0.5,  1.0, 1.0,
             0.5,  0.5,  0.5,  1.0, 0.0,
             0.5,  0.5,  0.5,  1.0, 0.0,
            -0.5,  0.5,  0.5,  0.0, 0.0,
            -0.5,  0.5, -0.5,  0.0, 1.0
        ], dtype='float32')

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Agora o stride mudou para 5 * itemsize (20 bytes)
        # Atributo 0: Posição XYZ
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Atributo 1: Coordenadas de Textura UV (começa após o 3º float)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)

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
        glBindVertexArray(self.vao)
        model_loc = glGetUniformLocation(shader_program, "model")
        
        # Ativa a unidade de textura 0
        glActiveTexture(GL_TEXTURE0)
        glUniform1i(glGetUniformLocation(shader_program, "u_texture"), 0)
        
        for row in range(8):
            for col in range(8):
                x_pos = col - 3.5
                z_pos = row - 3.5
                
                translation = pyrr.matrix44.create_from_translation([x_pos, -0.5, z_pos])
                glUniformMatrix4fv(model_loc, 1, GL_FALSE, translation)
                
                # Seleciona a textura correta com base no valor da matriz
                tipo_terreno = self.grid[row][col]
                if tipo_terreno == 1:    # Rio Jaguaribe
                    glBindTexture(GL_TEXTURE_2D, self.tex_agua)
                elif tipo_terreno == 2:  # Cidade
                    glBindTexture(GL_TEXTURE_2D, self.tex_concreto)
                else:                    # Chão comum (0)
                    glBindTexture(GL_TEXTURE_2D, self.tex_grama)
                
                glDrawArrays(GL_TRIANGLES, 0, 36)

        glBindTexture(GL_TEXTURE_2D, 0)
        glBindVertexArray(0)

    def carregar_textura_tabuleiro(self, caminho):
        img = Image.open(caminho)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGBA").tobytes()
        width, height = img.size

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glBindTexture(GL_TEXTURE_2D, 0)
        return tex_id