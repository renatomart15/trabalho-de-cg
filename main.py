from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
from models import TratorComTextura 
from tabuleiro import Tabuleiro

def inicializar_shaders(vertex_path, fragment_path):
    with open(vertex_path, "r") as f:
        vertex_src = f.read()
    with open(fragment_path, "r") as f:
        fragment_src = f.read()

    return compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER),
    )

def main():
    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    window = glfw.create_window(800, 600, "Into the Valley - Sprint 1", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST) 

    # IMPORTANTE: Carregamos os dois Shaders separados
    shader_trator = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    shader_tabuleiro = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_tabuleiro.glsl")

    meu_tabuleiro = Tabuleiro()
    
    # Instancia o trator passando o modelo e a imagem da textura
    meu_trator = TratorComTextura("assets/trator.obj", "assets/trator_textura.jpeg")

    view = pyrr.matrix44.create_look_at(eye=[9, 9, 9], target=[0, 0, 0], up=[0, 1, 0])
    projection = pyrr.matrix44.create_perspective_projection_matrix(fovy=45, aspect=800 / 600, near=0.1, far=100.0)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.12, 0.12, 0.12, 1.0) 

        # --- 1. DESENHAR TABULEIRO (COR SÓLIDA) ---
        glUseProgram(shader_tabuleiro)
        glUniformMatrix4fv(glGetUniformLocation(shader_tabuleiro, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(shader_tabuleiro, "projection"), 1, GL_FALSE, projection)
        glBindTexture(GL_TEXTURE_2D, 0) # Garante que nenhuma textura está vazando aqui
        meu_tabuleiro.draw(shader_tabuleiro)

        # --- 2. DESENHAR TRATOR (TEXTURIZADO) ---
        glUseProgram(shader_trator)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "projection"), 1, GL_FALSE, projection)

        tempo_atual = glfw.get_time()
        animacao_motor = np.sin(tempo_atual * 10)

        x_grid = 2 - 3.5
        z_grid = 4 - 3.5
        meu_trator.desenhar(shader_trator, x_grid, z_grid, angulo_pa=animacao_motor)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()