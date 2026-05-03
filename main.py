from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
from tabuleiro import Tabuleiro
from models import Trator  # Importa sua nova classe


def inicializar_shaders(vertex_path, fragment_path):
    """
    Compila os códigos GLSL para execução na GPU.
    """
    with open(vertex_path, "r") as f:
        vertex_src = f.read()
    with open(fragment_path, "r") as f:
        fragment_src = f.read()

    shader = compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER),
    )
    return shader


def main():
    # --- INICIALIZAÇÃO DO GLFW ---
    if not glfw.init():
        return

    # Definindo a versão do OpenGL (3.3 Core Profile)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(800, 600, "Into the Valley", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Habilita o Teste de Profundidade para o 3D funcionar corretamente
    glEnable(GL_DEPTH_TEST)

    # --- PREPARAÇÃO DOS RECURSOS ---
    shader_tactico = inicializar_shaders(
        "shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl"
    )

    meu_tabuleiro = Tabuleiro()

    meu_trator = Trator(meu_tabuleiro.vbo, meu_tabuleiro.vao)

    # --- MATRIZES DE CÂMERA E PROJEÇÃO ---[cite: 2]
    # 'eye' é a posição da câmera, 'target' é para onde ela olha[cite: 2]
    view = pyrr.matrix44.create_look_at(
        eye=[10, 10, 10],
        target=[0, 0, 0],
        up=[0, 1, 0],
    )

    projection = pyrr.matrix44.create_perspective_projection_matrix(
        fovy=45, aspect=800 / 600, near=0.1, far=100.0
    )

    # --- LOOP PRINCIPAL ---[cite: 2]
    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(shader_tactico)

        # 1. Cálcula o ângulo de animação baseado no tempo real
        # O np.sin cria o movimento de vai-e-vem (oscilação)
        tempo_atual = glfw.get_time()
        animacao_pa = np.sin(tempo_atual * 3) * 20  # O '* 3' controla a velocidade

        # 2. Configura as matrizes globais (View/Projection)
        view_loc = glGetUniformLocation(shader_tactico, "view")
        proj_loc = glGetUniformLocation(shader_tactico, "projection")
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)

        # 3. Desenha o Tabuleiro
        meu_tabuleiro.draw(shader_tactico)

        # 4. Desenha o Trator passando o ângulo calculado
        x_grid = 2 - 3.5
        z_grid = 2 - 3.5
        # Passamos o 'animacao_pa' para o método desenhar do seu model
        meu_trator.desenhar(shader_tactico, x_grid, z_grid, angulo_pa=animacao_pa)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    main()
