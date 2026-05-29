# tabuleiro.py
import numpy as np
from OpenGL.GL import *
import pyrr
from PIL import Image
import ctypes  # Mantido para evitar NameError no uso de ctypes.c_void_p

class Tabuleiro:
    def __init__(self, mapa_id=1):
        # Guardamos qual é o mapa atual ativo
        self.mapa_id = mapa_id

        # 0: Chão comum (Grama)
        # 1: Rio Jaguaribe (Água)
        # 2: Cidade/Construção (Concreto)
        self.grid = np.zeros((8, 8), dtype=int)
        
        # MATRIZ LÓGICA DE ENTIDADES (O cérebro de posições do jogo)
        # 0: Vazio
        # 1: Trator (Jogador 1)
        # 2: Escavadeira (Jogador 1)
        # 10: Mosquito Mutante (Jogador 2)
        # 11: Barata Mutante (Jogador 2)
        # 50: Casa (Edifícios Civis)
        self.entities = np.zeros((8, 8), dtype=int)

        # Configura o design de terreno e posições das peças com base no mapa_id
        self.setup_map()

        # Inicialização dos Buffers Geométricos do OpenGL
        self.vbo = None
        self.vao = None
        self.generate_tile_vbo()

        # Carregamento das Texturas das Células
        self.tex_grama = self.carregar_textura_tabuleiro("assets/grama.jpg")
        self.tex_agua = self.carregar_textura_tabuleiro("assets/agua.jpg")
        self.tex_concreto = self.carregar_textura_tabuleiro("assets/concreto.jpg")

    def setup_map(self):
        """Configura designs de terreno e posicionamentos iniciais diferentes para cada mapa."""
        
        if self.mapa_id == 1:
            # --- MAPA 1: O RIO CENTRAL (Seu mapa original) ---
            # Curso do Rio Jaguaribe na coluna 3
            for i in range(8):
                self.grid[i][3] = 1
            
            # Cidades/Zonas de concreto
            self.grid[2][2] = 2
            self.grid[5][5] = 2
            
            # Posicionamento Inicial das Unidades e Estruturas
            self.entities[0][0] = 1   # Trator
            self.entities[1][2] = 2   # Escavadeira
            self.entities[7][7] = 10  # Mosquito
            self.entities[6][5] = 11  # Barata
            self.entities[2][2] = 50  # Casa 1
            self.entities[5][5] = 50  # Casa 2

        elif self.mapa_id == 2:
            # --- MAPA 2: OS CANAIS CRUZADOS (Corte Diagonal) ---
            # O rio cruza o mapa na diagonal, limitando o avanço terrestre direto
            for i in range(8):
                self.grid[i][i] = 1 
            
            # Cidades protegidas nos cantos e no centro tático
            self.grid[0][7] = 2
            self.grid[7][0] = 2
            self.grid[3][4] = 2
            
            # Posicionamento Inicial (Separados pelo rio diagonal!)
            self.entities[2][0] = 1   # Trator
            self.entities[4][1] = 2   # Escavadeira
            self.entities[1][6] = 10  # Mosquito (Muriçoca)
            self.entities[2][5] = 11  # Barata
            
            self.entities[0][7] = 50  # Casa no canto superior direito
            self.entities[3][4] = 50  # Casa no centro comercial

        elif self.mapa_id == 3:
            # --- MAPA 3: A CHEIA DO JAGUARIBE (Inundação) ---
            # Uma grande cruz de água central isolando o mapa em 4 quadrantes secos
            for i in range(8):
                self.grid[3][i] = 1  # Linha 3 inteira é água
                self.grid[4][i] = 1  # Linha 4 inteira é água
                self.grid[i][3] = 1  # Coluna 3 inteira é água

            # Cidades isoladas nas "ilhas" restantes de terra firme
            self.grid[1][1] = 2
            self.grid[1][6] = 2
            self.grid[6][6] = 2

            # Posicionamento Inicial tático
            self.entities[0][1] = 1   # Trator
            self.entities[1][0] = 2   # Escavadeira
            self.entities[7][6] = 10  # Mosquito (Ideal para flutuar no meio do lago)
            self.entities[6][7] = 11  # Barata
            
            self.entities[1][1] = 50  # Casa na ilha noroeste
            self.entities[1][6] = 50  # Casa na ilha nordeste
            self.entities[6][6] = 50  # Casa na ilha sudeste

    def generate_tile_vbo(self):
        """Gera o cubo geométrico elemental que serve para renderizar cada bloco do grid."""
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # Array contendo posições (X, Y, Z) e Coordenadas de Textura (U, V) para um cubo completo
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

            # Face Superior (Onde as entidades pisam de fato)
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

        # Atributo 1: Coordenadas de Textura UV (Deslocamento inicial de 3 floats)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def draw(self, shader_program):
        """Varre a matriz grid e desenha cada tile no mundo usando a textura correspondente."""
        glBindVertexArray(self.vao)
        model_loc = glGetUniformLocation(shader_program, "model")
        
        glActiveTexture(GL_TEXTURE0)
        glUniform1i(glGetUniformLocation(shader_program, "u_texture"), 0)
        
        for row in range(8):
            for col in range(8):
                # Centraliza o mapa de 8x8 na origem (0,0) do ambiente 3D
                x_pos = col - 3.5
                z_pos = row - 3.5
                
                translation = pyrr.matrix44.create_from_translation([x_pos, -0.5, z_pos])
                glUniformMatrix4fv(model_loc, 1, GL_FALSE, translation)
                
                # Renderiza a textura correta mapeada na matriz de terrenos (self.grid)
                tipo_terreno = self.grid[row][col]
                if tipo_terreno == 1:    # Rio Jaguaribe (Água)
                    glBindTexture(GL_TEXTURE_2D, self.tex_agua)
                elif tipo_terreno == 2:  # Cidades (Concreto)
                    glBindTexture(GL_TEXTURE_2D, self.tex_concreto)
                else:                    # Chão comum (Grama = ID 0)
                    glBindTexture(GL_TEXTURE_2D, self.tex_grama)
                
                glDrawArrays(GL_TRIANGLES, 0, 36)

        glBindTexture(GL_TEXTURE_2D, 0)
        glBindVertexArray(0)

    def carregar_textura_tabuleiro(self, caminho):
        """Carrega arquivos de imagem do disco e gera uma textura id no OpenGL."""
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