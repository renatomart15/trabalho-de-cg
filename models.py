import numpy as np
from OpenGL.GL import *
import pyrr


class UnidadeMovel:
    def __init__(self):
        # Usaremos o mesmo VBO de cubo do tabuleiro para as partes do robô
        self.vbo = None
        self.posicao = [0, 0, 0]
        self.rotacao = 0

    def draw_cube(self, shader_program, transform_matrix, color):
        """Desenha um cubo individual com uma cor e transformação específica."""
        model_loc = glGetUniformLocation(shader_program, "model")
        color_loc = glGetUniformLocation(shader_program, "u_color")

        glUniformMatrix4fv(model_loc, 1, GL_FALSE, transform_matrix)
        glUniform3f(color_loc, *color)
        glDrawArrays(GL_TRIANGLES, 0, 36)


class Trator(UnidadeMovel):
    def __init__(self, vbo_referencia, vao_referencia):
        super().__init__()
        self.vbo = vbo_referencia
        self.vao = vao_referencia # Guardamos a referência do VAO

    def desenhar(self, shader_program, x, z, angulo_pa=0):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        # 1. MATRIZ RAIZ (Posição global do Trator no grid)[cite: 2]
        matriz_base = pyrr.matrix44.create_from_translation([x, 0.0, z])

        # --- PARTE 1: CHASSI (Base do Trator) ---
        # Escalamos o cubo para parecer uma base larga e baixa
        escala_chassi = pyrr.matrix44.create_from_scale([0.8, 0.3, 0.8])
        transform_chassi = pyrr.matrix44.multiply(escala_chassi, matriz_base)
        self.draw_cube(
            shader_program, transform_chassi, [0.8, 0.6, 0.0]
        )  # Amarelo Trator[cite: 2]

        # --- PARTE 2: CABINE (Hierarquia: Presa à Base) ---
        # Subimos a cabine um pouco em relação à base (0.3 no eixo Y)
        pos_cabine = pyrr.matrix44.create_from_translation([0.0, 0.3, 0.0])
        escala_cabine = pyrr.matrix44.create_from_scale([0.4, 0.4, 0.4])

        # Multiplicamos: Base * Posição Relativa * Escala
        transform_cabine = pyrr.matrix44.multiply(pos_cabine, matriz_base)
        transform_cabine = pyrr.matrix44.multiply(escala_cabine, transform_cabine)
        self.draw_cube(
            shader_program, transform_cabine, [0.2, 0.2, 0.2]
        )  # Preto/Vidro[cite: 2]

        # --- PARTE 3: A PÁ (Hierarquia: Presa à Base, mas na frente) ---
        pos_pa = pyrr.matrix44.create_from_translation([0.0, 0.1, 0.5])
        rot_pa = pyrr.matrix44.create_from_x_rotation(np.radians(angulo_pa))
        escala_pa = pyrr.matrix44.create_from_scale([0.9, 0.2, 0.1])

        transform_pa = pyrr.matrix44.multiply(rot_pa, matriz_base)
        transform_pa = pyrr.matrix44.multiply(pos_pa, transform_pa)
        transform_pa = pyrr.matrix44.multiply(escala_pa, transform_pa)
        self.draw_cube(shader_program, transform_pa, [0.7, 0.7, 0.7])  # Metal[cite: 2]
        glBindVertexArray(0)
