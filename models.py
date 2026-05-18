import numpy as np
from OpenGL.GL import *
import pyrr
import ctypes
from PIL import Image

class Modelo3DComTextura:
    def __init__(self, obj_path, texture_path, escala=0.4, altura=0.5):
        self.vao = None
        self.vbo = None
        self.texture_id = None
        self.num_vertices = 0
        
        # Guardamos as propriedades únicas deste modelo
        self.escala = escala
        self.altura = altura
        
        self.carregar_obj_manual(obj_path)
        self.carregar_textura_gpu(texture_path)

    def carregar_obj_manual(self, obj_path):
        # Listas para armazenar os dados brutos do arquivo
        vertices = []
        texturas = []
        dados_finais = []

        # Lê o arquivo linha por linha para cruzar posições e UVs de forma garantida
        with open(obj_path, 'r') as f:
            for linha in f:
                partes = linha.split()
                if not partes:
                    continue
                
                # 'v' representa posição do vértice (X, Y, Z)
                if partes[0] == 'v':
                    vertices.append([float(partes[1]), float(partes[2]), float(partes[3])])
                # 'vt' representa coordenada de textura (U, V)
                elif partes[0] == 'vt':
                    texturas.append([float(partes[1]), float(partes[2])])
                # 'f' representa a face (triângulo) que une os índices
                elif partes[0] == 'f':
                    for vertice_info in partes[1:]:
                        # O formato de face costuma ser: indice_vertice/indice_uv/indice_normal
                        sub_partes = vertice_info.split('/')
                        idx_v = int(sub_partes[0]) - 1
                        
                        # Adiciona a posição XYZ
                        dados_finais.extend(vertices[idx_v])
                        
                        # Se houver coordenada de textura associada na face
                        if len(sub_partes) > 1 and sub_partes[1] != '':
                            idx_vt = int(sub_partes[1]) - 1
                            dados_finais.extend(texturas[idx_vt])
                        else:
                            # Fallback caso essa face específica não tenha mapeamento UV
                            dados_finais.extend([0.0, 0.0])

        dados_array = np.array(dados_finais, dtype='float32')
        self.num_vertices = len(dados_array) // 5  # Cada vértice tem 3 de posição + 2 de UV

        # Configuração do VAO e VBO na GPU
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, dados_array.nbytes, dados_array, GL_STATIC_DRAW)

        # Passo (stride) é de 5 floats (5 * 4 bytes = 20 bytes)
        # Atributo 0: Posição (X, Y, Z)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * dados_array.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Atributo 1: Coordenadas de Textura (U, V) - Começa após o 3º float
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * dados_array.itemsize, ctypes.c_void_p(3 * dados_array.itemsize))
        glEnableVertexAttribArray(1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def carregar_textura_gpu(self, texture_path):
        img = Image.open(texture_path)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGBA").tobytes()
        width, height = img.size

        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glBindTexture(GL_TEXTURE_2D, 0)

    def desenhar(self, shader_program, x, z, angulo_pa=0):
        glBindVertexArray(self.vao)
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform1i(glGetUniformLocation(shader_program, "u_texture"), 0)

        model_loc = glGetUniformLocation(shader_program, "model")
        
        # Usa a escala definida na criação do objeto
        matriz_escala = pyrr.matrix44.create_from_scale([self.escala, self.escala, self.escala]) 
        
        vibracao = np.sin(angulo_pa * 0.5) * 0.02
        # Usa a altura definida na criação do objeto somada à vibração do motor
        matriz_posicao = pyrr.matrix44.create_from_translation([x, self.altura + vibracao, z])
        
        transformacao_final = pyrr.matrix44.multiply(matriz_escala, matriz_posicao)
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, transformacao_final)
        
        glDrawArrays(GL_TRIANGLES, 0, self.num_vertices)
        
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindVertexArray(0)