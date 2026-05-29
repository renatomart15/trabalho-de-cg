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
        """
        Configura designs de terreno com rotas livres para peças terrestres 
        (sem rios contínuos) e mantém o posicionamento Defensores-Esquerda vs Atacantes-Direita.
        """
        
        if self.mapa_id == 1:
            # --- MAPA 1: O RIO INTERROMPIDO (Lagos Centrais) ---
            # Em vez de uma coluna inteira de água, deixamos pontes de terra nas pontas e no centro
            self.grid[0][3] = 1  # Lago ao Norte
            self.grid[1][3] = 1
            self.grid[3][3] = 1  # Lago Central
            self.grid[4][3] = 1
            self.grid[6][3] = 1  # Lago ao Sul
            self.grid[7][3] = 1
            # Linhas 2 e 5 na coluna 3 são GRAMA (0), servindo como pontes naturais!

            # Cidades/Zonas de concreto (Lado Esquerdo)
            self.grid[2][1] = 2
            self.grid[5][2] = 2
            
            # [DEFENSORES] - Lado Esquerdo
            self.entities[2][0] = 1   # Trator
            self.entities[5][0] = 2   # Escavadeira
            self.entities[2][1] = 50  # Casa 1
            self.entities[5][2] = 50  # Casa 2
            
            # [ATACANTES] - Lado Direito
            self.entities[1][6] = 10  # Muriçoca
            self.entities[6][6] = 11  # Barata

        elif self.mapa_id == 2:
            # --- MAPA 2: OS CANAIS FRAGMENTADOS (Diagonal Aberta) ---
            # Rompemos a diagonal do rio para criar passagens terrestres livres
            self.grid[0][0] = 1
            self.grid[1][1] = 1
            # (2,2) é livre
            self.grid[3][3] = 1
            self.grid[4][4] = 1
            # (5,5) é livre
            self.grid[6][6] = 1
            self.grid[7][7] = 1
            
            # Zonas urbanas recuadas na retaguarda esquerda
            self.grid[1][2] = 2
            self.grid[4][1] = 2
            self.grid[6][2] = 2
            
            # [DEFENSORES] - Lado Esquerdo
            self.entities[2][0] = 1   # Trator
            self.entities[5][0] = 2   # Escavadeira
            self.entities[1][2] = 50  
            self.entities[4][1] = 50  
            self.entities[6][2] = 50  
            
            # [ATACANTES] - Lado Direito
            self.entities[2][6] = 10  # Muriçoca
            self.entities[5][6] = 11  # Barata

        elif self.mapa_id == 3:
            # --- MAPA 3: PEQUENOS AÇUDES (Quadrantes Conectados) ---
            # Transformamos a grande cruz de inundação em 4 poças/açudes isolados no centro
            self.grid[2][3] = 1
            self.grid[2][4] = 1
            self.grid[5][3] = 1
            self.grid[5][4] = 1

            # Cidades nas ilhas do Quadrante Esquerdo
            self.grid[1][1] = 2
            self.grid[6][1] = 2
            self.grid[1][2] = 2

            # [DEFENSORES] - Quadrante Esquerdo
            self.entities[1][0] = 1   # Trator
            self.entities[6][0] = 2   # Escavadeira
            self.entities[1][1] = 50  
            self.entities[1][2] = 50  
            self.entities[6][1] = 50  

            # [ATACANTES] - Quadrante Direito
            self.entities[1][6] = 10  # Muriçoca
            self.entities[6][6] = 11  # Barata

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