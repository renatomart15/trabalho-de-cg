from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
from models import Modelo3DComTextura 
from tabuleiro import Tabuleiro

projection = None

TURNO_JOGADOR = 0
TURNO_INIMIGO = 1
estado_atual = TURNO_JOGADOR

def inicializar_shaders(vertex_path, fragment_path):
    with open(vertex_path, "r") as f:
        vertex_src = f.read()
    with open(fragment_path, "r") as f:
        fragment_src = f.read()

    return compileProgram(
        compileShader(vertex_src, GL_VERTEX_SHADER),
        compileShader(fragment_src, GL_FRAGMENT_SHADER),
    )

def redimensionar_janela(window, largura, altura):
    # Garante que não dividiremos por zero se a janela for minimizada
    if altura == 0:
        altura = 1
        
    # 1. Atualiza o Viewport para ocupar a tela cheia nova
    glViewport(0, 0, largura, altura)
    
    # 2. Recalcula a proporção (Aspect Ratio) para o tabuleiro não distorcer
    proporcao = largura / altura
    
    # Se você usa uma câmera Perspectiva (3D Real), atualize a matriz assim:
    # (Verifique no seu main.py se a sua variável se chama 'projection')
    global projection
    projection = pyrr.matrix44.create_perspective_projection_matrix(45.0, proporcao, 0.1, 100.0)
    
    # NOTA: Se o seu jogo usa câmera Ortográfica (Estilo Into the Breach clássico/Isométrico),
    # em vez da linha de cima, você usaria algo assim:
    # projection = pyrr.matrix44.create_orthogonal_projection_matrix(-10.0 * proporcao, 10.0 * proporcao, -10.0, 10.0, 0.1, 100.0)

def mapear_clique_mouse(window, botao, acao, modificadores):
    # Só queremos registrar o clique quando o jogador APERTAR o botão ESQUERDO do mouse
    if botao == glfw.MOUSE_BUTTON_LEFT and acao == glfw.PRESS:
        # Pega a posição (X, Y) do cursor na tela (em pixels)
        x_pixel, y_pixel = glfw.get_cursor_pos(window)
        largura, altura = glfw.get_window_size(window)
        
        print(f"Clique detectado na tela: Pixels X={x_pixel:.1f}, Y={y_pixel:.1f}")
        
        # TODO: Converter essa coordenada para os índices [row][col] da matriz!

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

    # ATIVE ESTA LINHA AQUI: Diz ao GLFW para chamar nossa função quando a janela mudar de tamanho
    glfw.set_framebuffer_size_callback(window, redimensionar_janela)

    glEnable(GL_DEPTH_TEST) 

    global projection # Avisa que vamos mexer na variável do topo do arquivo
    projection = pyrr.matrix44.create_perspective_projection_matrix(45.0, 800 / 600, 0.1, 100.0)

    # IMPORTANTE: Carregamos os dois Shaders separados
    vertex_shader = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    shader_tabuleiro = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_tabuleiro.glsl")

    meu_tabuleiro = Tabuleiro()
    
    # Instancia o trator passando o modelo e a imagem da textura
    meu_trator = Modelo3DComTextura("assets/trator.obj", "assets/trator_textura.jpeg", escala=0.4, altura=0.3)

    # Instancia a casa
    minha_casa = Modelo3DComTextura("assets/casa.obj", "assets/casa_textura.jpeg", escala=0.001, altura=-0.3)

    # Instanciando o inimigo: vamos colocar altura=0.2 para ele flutuar de leve sobre o bloco
    meu_mosquito = Modelo3DComTextura("assets/mosquito.obj", "assets/mosquito_textura.png", escala=0.05, altura=0.3)

    minha_escavadeira = Modelo3DComTextura("assets/escavadeira.obj", "assets/escavadeira_textura.jpeg", escala=0.13, altura=0.1)

    barata = Modelo3DComTextura("assets/barata.obj", "assets/barata_textura.png", escala=0.1, altura=0.1)

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

        # --- DESENHO AUTOMATIZADO DE ENTIDADES ---
        glUseProgram(vertex_shader)
        glUniformMatrix4fv(glGetUniformLocation(vertex_shader, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(vertex_shader, "projection"), 1, GL_FALSE, projection)

        tempo_atual = glfw.get_time()

        # Varre a matriz lógica do tabuleiro
        for row in range(8):
            for col in range(8):
                # Converte os índices da matriz para coordenadas do mundo 3D OpenGL
                x_mundo = col - 3.5
                z_mundo = row - 3.5
                
                id_entidade = meu_tabuleiro.entities[row][col]

                if id_entidade == 1:   # Trator (Jogador 1)
                    meu_trator.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                    
                elif id_entidade == 2: # Escavadeira (Jogador 1) - Balança de leve com o motor
                    minha_escavadeira.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                    
                elif id_entidade == 10: # Mosquito Mutante (Jogador 2 - Flutua rápido)
                    meu_mosquito.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 5.0)
                    
                elif id_entidade == 11: # Barata Mutante (Jogador 2 - Vibra rápido)
                    barata.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 8.0)

                # Se for casa
                elif id_entidade == 50: # Casa / Estrutura Urbana (Estática)
                    minha_casa.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=0)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()