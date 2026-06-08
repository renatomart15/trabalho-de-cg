# render_utils.py
from OpenGL.GL import *
import numpy as np
import pyrr
import math
from PIL import Image

def desenhar_borda_cursor(shader_program, x_centro, z_centro, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.5):
    vertices = np.array([
        [x_centro - tamanho, 0.01, z_centro - tamanho], 
        [x_centro + tamanho, 0.01, z_centro - tamanho], 
        [x_centro + tamanho, 0.01, z_centro + tamanho], 
        [x_centro - tamanho, 0.01, z_centro + tamanho]  
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
    
    model_loc = glGetUniformLocation(shader_program, "model")
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, pyrr.matrix44.create_identity())
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 1)
    glUniform4f(glGetUniformLocation(shader_program, "u_solid_color"), cor_rgb[0], cor_rgb[1], cor_rgb[2], 1.0)
    
    glLineWidth(4.0) 
    glDrawArrays(GL_LINE_LOOP, 0, 4)
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
    glLineWidth(1.0)
    
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])


def desenhar_barra_vida(shader_program, x_centro, z_centro, hp_atual, hp_maximo, view_mat):
    """Desenha a vida flutuante rotacionada perfeitamente (Billboard) para a tela."""
    view_mat = np.array(view_mat, dtype=np.float32).reshape(4, 4)

    # Extração dos eixos da tela a partir da matriz de View da Câmera
    cam_right = np.array([view_mat[0][0], view_mat[1][0], view_mat[2][0]], dtype=np.float32)
    cam_up    = np.array([view_mat[0][1], view_mat[1][1], view_mat[2][1]], dtype=np.float32)

    y_flutuante = 1.3     
    tamanho_bloco = 0.08  
    espacamento = 0.2     

    pos_centro_vida = np.array([x_centro, y_flutuante, z_centro], dtype=np.float32)
    offset_inicial = -((hp_maximo - 1) * espacamento) / 2.0

    for i in range(hp_maximo):
        deslocamento_x = offset_inicial + (i * espacamento)
        centro_bloco = pos_centro_vida + (cam_right * deslocamento_x)

        if i < hp_atual:
            cor_rgb = [0.2, 0.9, 0.2]  # Verde ativo
        else:
            cor_rgb = [0.2, 0.2, 0.2]  # Cinza inativo

        v0 = centro_bloco - cam_right * tamanho_bloco - cam_up * tamanho_bloco
        v1 = centro_bloco + cam_right * tamanho_bloco - cam_up * tamanho_bloco
        v2 = centro_bloco + cam_right * tamanho_bloco + cam_up * tamanho_bloco
        v3 = centro_bloco - cam_right * tamanho_bloco + cam_up * tamanho_bloco

        vertices = np.array([v0, v1, v2, v3], dtype=np.float32)

        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
        
        model_loc = glGetUniformLocation(shader_program, "model")
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, pyrr.matrix44.create_identity())
        
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)
        
        glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 1)
        glUniform4f(glGetUniformLocation(shader_program, "u_solid_color"), cor_rgb[0], cor_rgb[1], cor_rgb[2], 1.0)
        
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        
        glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glDeleteBuffers(1, [vbo])
        glDeleteVertexArrays(1, [vao])

def desenhar_sombra_circulo(shader_program, x_centro, z_centro, raio=0.25):
    """Desenha um círculo plano escuro e translúcido rente ao chão para simular a sombra de unidades voadoras."""
    # Criamos os vértices de um círculo (Triangle Fan)
    num_segmentos = 16
    vertices = [[x_centro, 0.01, z_centro]] # Vértice central (Y levemente acima do chão para evitar z-fighting)
    
    for i in range(num_segmentos + 1):
        angulo = i * (2.0 * math.pi / num_segmentos)
        x = x_centro + math.cos(angulo) * raio
        z = z_centro + math.sin(angulo) * raio
        vertices.append([x, 0.01, z])
        
    vertices = np.array(vertices, dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
    
    model_loc = glGetUniformLocation(shader_program, "model")
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, pyrr.matrix44.create_identity())
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    # Habilitamos o Blending para que a sombra pareça realista e translúcida
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 1)
    # Cor: Preto (0.0, 0.0, 0.0) com 40% de opacidade (0.4)
    glUniform4f(glGetUniformLocation(shader_program, "u_solid_color"), 0.0, 0.0, 0.0, 0.4)
    
    glDrawArrays(GL_TRIANGLE_FAN, 0, len(vertices))
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
    glDisable(GL_BLEND)
    
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])


def carregar_textura_menu(caminho):
    #   Carregar uma imagem 2d do disco para ser usada na inteface

    img = Image.open(caminho)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img_data = img.convert("RGBA").tobytes()
    width, height = img.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glBindTexture(GL_TEXTURE_2D, 0)

    return tex_id



def desenhar_botao_texturizado(shader_program, x_centro, y_centro, larg, alt, texture_id):
    """Desenha um retângulo 2D na tela aplicando uma imagem/textura."""
    # Matriz com Posição (X, Y, Z) e Coordenadas de Textura (U, V)
    vertices = np.array([
        [x_centro - larg/2, y_centro - alt/2, 0.0,   0.0, 0.0],
        [x_centro + larg/2, y_centro - alt/2, 0.0,   1.0, 0.0],
        [x_centro + larg/2, y_centro + alt/2, 0.0,   1.0, 1.0],
        [x_centro - larg/2, y_centro + alt/2, 0.0,   0.0, 1.0]
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    # Atributo Posição (stride de 5 floats)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(0))
    # Atributo UV (começa depois dos 3 primeiros floats)
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
    
    # Anula as matrizes 3D para renderizar em 2D absoluto
    identidade = pyrr.matrix44.create_identity()
    glUniformMatrix4fv(glGetUniformLocation(shader_program, "model"), 1, GL_FALSE, identidade)
    glUniformMatrix4fv(glGetUniformLocation(shader_program, "view"), 1, GL_FALSE, identidade)
    glUniformMatrix4fv(glGetUniformLocation(shader_program, "projection"), 1, GL_FALSE, identidade)
    
    # Ativa a textura
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glUniform1i(glGetUniformLocation(shader_program, "u_texture"), 0)
    
    # Desliga a cor sólida para o Shader usar a imagem
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
    
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
    
    glBindTexture(GL_TEXTURE_2D, 0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])
    


def desenhar_botao_menu(shader_program, x_centro, y_centro, larg, alt, cor_rgb):
    """Desenha um retângulo preenchido em 2D direto na tela usando coordenadas NDC (-1 a 1)."""
    vertices = np.array([
        [x_centro - larg/2, y_centro - alt/2, 0.0],
        [x_centro + larg/2, y_centro - alt/2, 0.0],
        [x_centro + larg/2, y_centro + alt/2, 0.0],
        [x_centro - larg/2, y_centro + alt/2, 0.0]
    ], dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
    
    # Anula as matrizes 3D para renderizar em 2D absoluto na tela
    identidade = pyrr.matrix44.create_identity()
    glUniformMatrix4fv(glGetUniformLocation(shader_program, "model"), 1, GL_FALSE, identidade)
    glUniformMatrix4fv(glGetUniformLocation(shader_program, "view"), 1, GL_FALSE, identidade)
    glUniformMatrix4fv(glGetUniformLocation(shader_program, "projection"), 1, GL_FALSE, identidade)
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 1)
    glUniform4f(glGetUniformLocation(shader_program, "u_solid_color"), cor_rgb[0], cor_rgb[1], cor_rgb[2], 1.0)
    
    glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
    
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])    



def desenhar_sombra_circulo(shader_program, x_centro, z_centro, raio=0.25):
    """Desenha um círculo plano escuro e translúcido rente ao chão para simular a sombra de unidades voadoras."""
    num_segmentos = 16
    # Vértice central (Y levemente acima do chão em 0.01 para evitar z-fighting/piscados na malha)
    vertices = [[x_centro, 0.01, z_centro]] 
    
    for i in range(num_segmentos + 1):
        angulo = i * (2.0 * math.pi / num_segmentos)
        x = x_centro + math.cos(angulo) * raio
        z = z_centro + math.sin(angulo) * raio
        vertices.append([x, 0.01, z])
        
    vertices = np.array(vertices, dtype=np.float32)

    vao = glGenVertexArrays(1)
    vbo = glGenBuffers(1)
    
    glBindVertexArray(vao)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
    
    model_loc = glGetUniformLocation(shader_program, "model")
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, pyrr.matrix44.create_identity())
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    # Habilitamos o Blending temporariamente para que a sombra pareça realista e translúcida
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 1)
    # Cor: Preto (0.0, 0.0, 0.0) com 40% de opacidade (0.4)
    glUniform4f(glGetUniformLocation(shader_program, "u_solid_color"), 0.0, 0.0, 0.0, 0.4)
    
    glDrawArrays(GL_TRIANGLE_FAN, 0, len(vertices))
    
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
    glDisable(GL_BLEND)
    
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])