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

# O cursor começa no meio do tabuleiro (Linha 4, Coluna 4)
cursor_row = 4
cursor_col = 4

# Gerenciamento de seleção
peca_selecionada = None  
pos_selecionada = None   

# Estados do Seletor
MODO_NAVEGACAO = 0
MODO_MOVIMENTACAO = 1
estado_seletor = MODO_NAVEGACAO

# Define o raio de movimentação máximo de cada unidade (em blocos)
ALCANCE_MOVIMENTO = {
    1: 3,  # Trator anda até 3 blocos
    2: 2,  # Escavadeira anda até 2 blocos
    10: 4, # Mosquito voa até 4 blocos
    11: 2  # Barata anda até 2 blocos
}

# --- AJUSTE AQUI: Começa vazia para não estourar o erro do OpenGL antes da hora ---
meu_tabuleiro = None

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
    
    # --- COMENTE OU DESLIGUE A TEXTURA ATIVA PARA EVITAR LINHAS PRETAS ---
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    # Ativa a cor sólida e envia os valores RGB para o Fragment Shader
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 1)
    glUniform4f(glGetUniformLocation(shader_program, "u_solid_color"), cor_rgb[0], cor_rgb[1], cor_rgb[2], 1.0)
    
    glLineWidth(4.0) 
    glDrawArrays(GL_LINE_LOOP, 0, 4)
    
    # Desativa a cor sólida para os próximos objetos
    glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
    
    glLineWidth(1.0)
    glBindBuffer(GL_ARRAY_BUFFER, 0)
    glBindVertexArray(0)
    glDeleteBuffers(1, [vbo])
    glDeleteVertexArrays(1, [vao])

def gerenciar_teclado(window, tecla, codigo_scancode, acao, modificadores):
    global cursor_row, cursor_col
    global estado_seletor, peca_selecionada, pos_selecionada, estado_atual, meu_tabuleiro

    # Só processa o movimento quando a tecla for APERTADA (PRESS)
    if acao == glfw.PRESS:
        # Movimento para Cima (W ou Seta para Cima)
        if tecla == glfw.KEY_W or tecla == glfw.KEY_UP:
            if cursor_row > 0:
                cursor_row -= 1
                
        # Movimento para Baixo (S)
        elif tecla == glfw.KEY_S or tecla == glfw.KEY_DOWN:
            if cursor_row < 7:
                cursor_row += 1
                
        # Movimento para Esquerda (A)
        elif tecla == glfw.KEY_A or tecla == glfw.KEY_LEFT:
            if cursor_col > 0:
                cursor_col -= 1
                
        # Movimento para Direita (D)
        elif tecla == glfw.KEY_D or tecla == glfw.KEY_RIGHT:
            if cursor_col < 7:
                cursor_col += 1
                
        # Botão de Ação (Espaço ou Enter)
        elif tecla == glfw.KEY_SPACE or tecla == glfw.KEY_ENTER:
            # --- ETAPA 1: SELECIONAR A PEÇA ---
            if estado_seletor == MODO_NAVEGACAO:
                id_peca = meu_tabuleiro.entities[cursor_row][cursor_col]
                
                if estado_atual == TURNO_JOGADOR and id_peca in [1, 2]:
                    peca_selecionada = id_peca
                    pos_selecionada = (cursor_row, cursor_col)
                    estado_seletor = MODO_MOVIMENTACAO
                    print(f"Peça {id_peca} selecionada em [{cursor_row}][{cursor_col}]. Escolha o destino!")
                
                elif estado_atual == TURNO_INIMIGO and id_peca in [10, 11]:
                    peca_selecionada = id_peca
                    pos_selecionada = (cursor_row, cursor_col)
                    estado_seletor = MODO_MOVIMENTACAO
                    print(f"Inseto {id_peca} selecionado em [{cursor_row}][{cursor_col}]. Escolha o destino!")
                
                else:
                    print("Nenhuma peça sua nesta posição!")

            # --- ETAPA 2: MOVER A PEÇA ---
            # --- ETAPA 2: MOVER A PEÇA (COM VALIDAÇÃO DE ALCANCE) ---
            elif estado_seletor == MODO_MOVIMENTACAO:
                destino_id = meu_tabuleiro.entities[cursor_row][cursor_col]
                origem_row, orig_col = pos_selecionada

                # 1. Calcula a Distância de Manhattan (passos verticais + passos horizontais)
                distancia = abs(cursor_row - origem_row) + abs(cursor_col - orig_col)
                
                # Descobre o limite de passos para a peça atual (padrão 2 se não listado)
                limite_passos = ALCANCE_MOVIMENTO.get(peca_selecionada, 2)

                # Regra A: O destino deve estar vazio (0) e dentro do limite de passos
                if destino_id == 0 and distancia <= limite_passos:
                    # Executa o movimento na matriz
                    meu_tabuleiro.entities[origem_row][orig_col] = 0
                    meu_tabuleiro.entities[cursor_row][cursor_col] = peca_selecionada
                    
                    print(f"Peça movida para [{cursor_row}][{cursor_col}] (Distância: {distancia}/{limite_passos})!")

                    # Limpa a seleção e volta ao modo navegação
                    peca_selecionada = None
                    pos_selecionada = None
                    estado_seletor = MODO_NAVEGACAO

                    # Passa o turno automaticamente
                    estado_atual = TURNO_INIMIGO if estado_atual == TURNO_JOGADOR else TURNO_JOGADOR
                    print(f"Turno alterado! Agora é a vez do Turno: {estado_atual}")

                elif (cursor_row, cursor_col) == pos_selecionada:
                    # Cancelar seleção ao clicar na mesma peça
                    print("Seleção cancelada.")
                    peca_selecionada = None
                    pos_selecionada = None
                    estado_seletor = MODO_NAVEGACAO
                    
                elif distancia > limite_passos:
                    # Bloqueio por distância muito longa
                    print(f"Muito longe! O {peca_selecionada} só move {limite_passos} blocos. Tentou mover {distancia}.")
                    
                else:
                    print("Espaço ocupado! Escolha um bloco vazio.")
                    
        print(f"Cursor movido para: Linha {cursor_row}, Coluna {cursor_col}")

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
    if altura == 0:
        altura = 1
        
    glViewport(0, 0, largura, altura)
    proporcao = largura / altura
    
    global projection
    projection = pyrr.matrix44.create_perspective_projection_matrix(45.0, proporcao, 0.1, 100.0)

def mapear_clique_mouse(window, botao, acao, modificadores):
    if botao == glfw.MOUSE_BUTTON_LEFT and acao == glfw.PRESS:
        x_pixel, y_pixel = glfw.get_cursor_pos(window)
        print(f"Clique detectado na tela: Pixels X={x_pixel:.1f}, Y={y_pixel:.1f}")

def main():
    # Avisa o Python que vamos modificar a instância global aqui dentro
    global meu_tabuleiro

    if not glfw.init():
        return

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    monitor_principal = glfw.get_primary_monitor()
    modo_video = glfw.get_video_mode(monitor_principal)
    largura_tela = modo_video.size.width
    altura_tela = modo_video.size.height

    window = glfw.create_window(largura_tela, altura_tela, "Breach in the Jaguaribe", monitor_principal, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    glfw.set_framebuffer_size_callback(window, redimensionar_janela)
    glfw.set_mouse_button_callback(window, mapear_clique_mouse)
    glfw.set_key_callback(window, gerenciar_teclado)

    glEnable(GL_DEPTH_TEST) 

    global projection
    redimensionar_janela(window, largura_tela, altura_tela)

    vertex_shader = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    
    # --- AJUSTE AQUI: O tabuleiro só é criado AGORA, com a GPU devidamente ligada e pronta ---
    meu_tabuleiro = Tabuleiro()
    
    meu_trator = Modelo3DComTextura("assets/trator.obj", "assets/trator_textura.jpeg", escala=0.4, altura=0.3)
    minha_casa = Modelo3DComTextura("assets/casa.obj", "assets/casa_textura.jpeg", escala=0.001, altura=-0.3)
    meu_mosquito = Modelo3DComTextura("assets/mosquito.obj", "assets/mosquito_textura.png", escala=0.05, altura=0.3)
    minha_escavadeira = Modelo3DComTextura("assets/escavadeira.obj", "assets/escavadeira_textura.jpeg", escala=0.13, altura=0.1)
    barata = Modelo3DComTextura("assets/barata.obj", "assets/barata_textura.png", escala=0.1, altura=0.1)
    minha_seta = Modelo3DComTextura("assets/seta.obj", "assets/seta_textura.png", escala=0.2, altura=1.2)

    view = pyrr.matrix44.create_look_at(eye=[9, 9, 9], target=[0, 0, 0], up=[0, 1, 0])

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.12, 0.12, 0.12, 1.0) 

        glUseProgram(vertex_shader)
        glUniformMatrix4fv(glGetUniformLocation(vertex_shader, "view"), 1, GL_FALSE, view)
        glUniformMatrix4fv(glGetUniformLocation(vertex_shader, "projection"), 1, GL_FALSE, projection)

        meu_tabuleiro.draw(vertex_shader)

        tempo_atual = glfw.get_time()

        for row in range(8):
            for col in range(8):
                x_mundo = col - 3.5
                z_mundo = row - 3.5
                
                id_entidade = meu_tabuleiro.entities[row][col]

                if id_entidade == 1:   
                    meu_trator.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                elif id_entidade == 2: 
                    minha_escavadeira.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                elif id_entidade == 10: 
                    meu_mosquito.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 5.0)
                elif id_entidade == 11: 
                    barata.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 8.0)
                elif id_entidade == 50: 
                    minha_casa.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=0)
        
        # --- 3. DESENHAR PONTEIRO VISUAL DO CURSOR E ÁREA DE MOVIMENTO ---
        x_cursor_mundo = cursor_col - 3.5
        z_cursor_mundo = cursor_row - 3.5

        # A) Desenha a seta na posição do cursor
        if estado_seletor == MODO_MOVIMENTACAO:
            minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=tempo_atual * 15.0)
        else:
            minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=0)

        # B) SE UMA PEÇA ESTIVER SELECIONADA: Mostra a malha de alcance
        if estado_seletor == MODO_MOVIMENTACAO and pos_selecionada is not None:
            origem_row, orig_col = pos_selecionada
            limite_passos = ALCANCE_MOVIMENTO.get(peca_selecionada, 2)

            for r in range(8):
                for c in range(8):
                    dist = abs(r - origem_row) + abs(c - orig_col)
                    id_ocupante = meu_tabuleiro.entities[r][c]

                    if dist <= limite_passos and id_ocupante == 0:
                        x_valido = c - 3.5
                        z_valido = r - 3.5
                        # [1.0, 1.0, 1.0] garante cor branca pura com brilho máximo no shader
                        desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.35)

        # C) Desenha a borda do cursor principal por cima (com tamanho 0.5 padrão)
        if estado_seletor == MODO_MOVIMENTACAO:
            desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[1.0, 0.8, 0.0], tamanho=0.5)
        else:
            desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[0.2, 0.8, 0.2], tamanho=0.5)
        
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()