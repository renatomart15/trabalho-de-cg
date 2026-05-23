import numpy as np
from OpenGL.GL import *
import pyrr
from PIL import Image
import ctypes  # Adicionado para evitar NameError no uso de ctypes.c_void_p

class Tabuleiro:
    def __init__(self):
        # 1. Criamos uma matriz 8x8 para representar o grid do Vale
        # 0: Chão comum (Grama)
        # 1: Rio Jaguaribe (Água)
        # 2: Cidade/Construção (Concreto)
        self.grid = np.zeros((8, 8), dtype=int)
        self.setup_map()

        # 2. Inicialização dos Buffers Geométricos
        self.vbo = glGenBuffers(1)
        self.generate_tile_vbo()

        # 3. Carregamento das Texturas
        self.tex_grama = self.carregar_textura_tabuleiro("assets/grama.jpg")
        self.tex_agua = self.carregar_textura_tabuleiro("assets/agua.jpg")
        self.tex_concreto = self.carregar_textura_tabuleiro("assets/concreto.jpg")

        # 4. MATRIZ LÓGICA DE ENTIDADES (O cérebro de posições do jogo)
        # 0: Vazio
        # 1: Trator (Jogador 1)
        # 2: Escavadeira (Jogador 1)
        # 10: Mosquito Mutante (Jogador 2)
        # 11: Barata Mutante (Jogador 2)
        self.entities = np.zeros((8, 8), dtype=int)

        # Posicionamento inicial estratégico das peças no Grid
        self.entities[0][0] = 1   # Trator começa na Linha 0, Coluna 0
        self.entities[1][2] = 2   # Escavadeira começa na Linha 1, Coluna 2
        self.entities[7][7] = 10  # Mosquito começa na Linha 7, Coluna 7
        self.entities[6][5] = 11  # Barata começa na Linha 6, Coluna 5

        # CASAS
        self.entities[2][2] = 50  # Casa na primeira cidade
        self.entities[5][5] = 50  # Casa na segunda cidade

    def setup_map(self):
        # Cria o curso do Rio Jaguaribe na coluna 3
        for i in range(8):
            self.grid[i][3] = 1

        # Posiciona as duas cidades/zonas de construção
        self.grid[2][2] = 2
        self.grid[5][5] = 2

    def generate_tile_vbo(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Array contendo posições (X, Y, Z) e Coordenadas de Textura (U, V)
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

            # Face Superior (Onde as entidades pisam)
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

        # Atributo 0: Posição XYZ (Stride: 5 * 4 bytes = 20)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # Atributo 1: Coordenadas de Textura UV (Começa após o deslocamento de 3 floats)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self, shader_program):
        glBindVertexArray(self.vao)
        model_loc = glGetUniformLocation(shader_program, "model")
        
        glActiveTexture(GL_TEXTURE0)
        glUniform1i(glGetUniformLocation(shader_program, "u_texture"), 0)
        
        for row in range(8):
            for col in range(8):
                x_pos = col - 3.5
                z_pos = row - 3.5
                
                translation = pyrr.matrix44.create_from_translation([x_pos, -0.5, z_pos])
                glUniformMatrix4fv(model_loc, 1, GL_FALSE, translation)
                
                # Renderiza a textura correta mapeada na matriz de terreno
                tipo_terreno = self.grid[row][col]
                if tipo_terreno == 1:    # Rio Jaguaribe
                    glBindTexture(GL_TEXTURE_2D, self.tex_agua)
                elif tipo_terreno == 2:  # Cidades
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