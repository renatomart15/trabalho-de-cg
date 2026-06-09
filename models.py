import numpy as np
from OpenGL.GL import *
import pyrr
import ctypes
from PIL import Image

class Modelo3DComTextura:
    def __init__(self, obj_path, texture_path, escala=0.4, altura=0.5, rotacao_inicial_y=0.0, rotacao_inicial_x=0.0):
        self.vao = None
        self.vbo = None
        self.texture_id = None
        self.num_vertices = 0
        
        self.escala = escala
        self.altura = altura
        self.rotacao_inicial_y = rotacao_inicial_y
        self.rotacao_inicial_x = rotacao_inicial_x
        
        self.carregar_obj_manual(obj_path)
        self.carregar_textura_gpu(texture_path)

    def carregar_obj_manual(self, obj_path):
        vertices = []
        texturas = []
        normais = []
        dados_finais = []

        with open(obj_path, 'r') as f:
            for linha in f:
                partes = linha.split()
                if not partes:
                    continue
                
                if partes[0] == 'v':
                    vertices.append([float(partes[1]), float(partes[2]), float(partes[3])])
                elif partes[0] == 'vt':
                    texturas.append([float(partes[1]), float(partes[2])])
                elif partes[0] == 'vn':
                    normais.append([float(partes[1]), float(partes[2]), float(partes[3])])
                elif partes[0] == 'f':
                    for vertice_info in partes[1:]:
                        sub_partes = vertice_info.split('/')
                        idx_v = int(sub_partes[0]) - 1
                        dados_finais.extend(vertices[idx_v])
                        
                        
                        if len(sub_partes) > 1 and sub_partes[1] != '':
                            idx_vt = int(sub_partes[1]) - 1
                            dados_finais.extend(texturas[idx_vt])
                        else:
                            dados_finais.extend([0.0, 0.0]) # Fallback UV
                            
                        
                        if len(sub_partes) > 2 and sub_partes[2] != '':
                            idx_vn = int(sub_partes[2]) - 1
                            dados_finais.extend(normais[idx_vn])
                        else:
                            dados_finais.extend([0.0, 1.0, 0.0]) # Fallback Normal (apontando pra cima)

        dados_array = np.array(dados_finais, dtype='float32')
        
        
        self.num_vertices = len(dados_array) // 8  

        
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, dados_array.nbytes, dados_array, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * dados_array.itemsize, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 8 * dados_array.itemsize, ctypes.c_void_p(3 * dados_array.itemsize))
        glEnableVertexAttribArray(1)
        
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 8 * dados_array.itemsize, ctypes.c_void_p(5 * dados_array.itemsize))
        glEnableVertexAttribArray(2)

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
        
        matriz_escala = pyrr.matrix44.create_from_scale([self.escala, self.escala, self.escala]) 
        
        vibracao = np.sin(angulo_pa * 0.5) * 0.02

        matriz_posicao = pyrr.matrix44.create_from_translation([x, self.altura + vibracao, z])
        
        transformacao_final = pyrr.matrix44.multiply(matriz_escala, matriz_posicao)
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, transformacao_final)
        
        glDrawArrays(GL_TRIANGLES, 0, self.num_vertices)
        
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindVertexArray(0)