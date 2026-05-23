from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
from models import Modelo3DComTextura 
from tabuleiro import Tabuleiro

projection = None

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
    shader_trator = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    shader_tabuleiro = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_tabuleiro.glsl")

    meu_tabuleiro = Tabuleiro()
    
    # Instancia o trator passando o modelo e a imagem da textura
    meu_trator = Modelo3DComTextura("assets/trator.obj", "assets/trator_textura.jpeg", escala=0.4, altura=0.5)

    # Instancia a casa
    minha_casa = Modelo3DComTextura("assets/casa.obj", "assets/casa_textura.jpeg", escala=0.001, altura=-0.3)

    # Instanciando o inimigo: vamos colocar altura=0.2 para ele flutuar de leve sobre o bloco
    meu_mosquito = Modelo3DComTextura("assets/mosquito.obj", "assets/mosquito_textura.png", escala=0.05, altura=0.3)

    minha_escavadeira = Modelo3DComTextura("assets/escavadeira.obj", "assets/escavadeira_textura.jpeg", escala=0.13, altura=0.1)

    view = pyrr.matrix44.create_look_at(eye=[9, 9, 9], target=[0, 0, 0], up=[0, 1, 0])
    projection = pyrr.matrix44.create_perspective_projection_matrix(fovy=45, aspect=800 / 600, near=0.1, far=100.0)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.12, 0.12, 0.12, 1.0) 

        glUseProgram(shader_trator)
        meu_tabuleiro.draw(shader_trator)

        # Esta linha DEVE usar a variável 'projection' que a função de redimensionar atualiza!
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "projection"), 1, GL_FALSE, projection)

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

        # --- 3. DESENHAR AS CASAS AUTOMATICAMENTE NOS QUADRADOS CINZAS ---
        glUseProgram(shader_trator)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "projection"), 1, GL_FALSE, projection)

        # Varre as linhas (row) e colunas (col) da matriz mapeada no seu tabuleiro
        for row in range(8):
            for col in range(8):
                # Verifica se o tipo de terreno atual é 2 (Cidade/Construção cinza)
                if meu_tabuleiro.grid[row][col] == 2:
                    
                    # Usa exatamente o mesmo cálculo de posicionamento do tabuleiro
                    x_pos = col - 3.5
                    z_pos = row - 3.5
                    
                    # Desenha a casa na coordenada correta do grid cinza
                    # Passamos angulo_pa=0 para que ela fique estática
                    minha_casa.desenhar(shader_trator, x_pos, z_pos, angulo_pa=0)

        # --- 4. DESENHAR O INIMIGO (MOSQUITO) ---
        glUseProgram(shader_trator)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "projection"), 1, GL_FALSE, projection)

        # Posição no grid
        x_mosquito = 2 - 3.5
        z_mosquito = 7 - 3.5

        # Criamos um efeito de flutuação rápida usando o tempo atual
        tempo_voo = glfw.get_time() * 5.0 
        
        # Passamos o tempo_voo no 'angulo_pa'. 
        # Como nossa classe faz um np.sin(angulo_pa) * 0.02, o mosquito vai oscilar suavemente no ar!
        meu_mosquito.desenhar(shader_trator, x_mosquito, z_mosquito, angulo_pa=tempo_voo)

        # --- 5. DESENHAR A ESCAVADEIRA ---
        glUseProgram(shader_trator)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(shader_trator, "projection"), 1, GL_FALSE, projection)

        # Escolhe a posição no grid (Coluna 1, Linha 4)
        x_escavadeira = 1 - 3.5
        z_escavadeira = 4 - 3.5

        # Como ela é um veículo pesado, podemos dar o mesmo efeito de vibração do motor do trator!
        # Usamos o tempo do GLFW para fazê-la tremer de leve
        tempo_motor = glfw.get_time()
        
        # Desenha o modelo na tela
        minha_escavadeira.desenhar(shader_trator, x_escavadeira, z_escavadeira, angulo_pa=tempo_motor)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()