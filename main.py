from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
from models import Modelo3DComTextura 
from tabuleiro import Tabuleiro

projection = None

# Novos estados para o seletor de ações
MODO_ATAQUE = 2

# Definição de HP padrão para cada tipo de unidade
HP_INICIAL = {
    1: 5,  # Trator: 5 HP
    2: 4,  # Escavadeira: 4 HP
    10: 3, # Mosquito: 3 HP
    11: 3  # Barata: 3 HP
}

# Definição de Dano de cada unidade
DANO_UNIDADE = {
    1: 2,  # Trator tira 2 de HP
    2: 3,  # Escavadeira tira 3 de HP
    10: 1, # Mosquito tira 1 de HP
    11: 2  # Barata tira 2 de HP
}

# Define o alcance do ataque de cada unidade (em blocos de distância)
ALCANCE_MOVIMENTO = {
    1: 2,  # Trator anda até 2 blocos
    2: 1,  # <<<<< MUDADO AQUI: Escavadeira agora anda apenas 1 bloco!
    10: 2, # Mosquito anda até 2 blocos
    11: 2  # Barata anda até 2 blocos
}

ALCANCE_ATAQUE = {
    1: 1,  # Trator: ataca a 1 bloco
    2: 2,  # Escavadeira: ataca a 2 blocos (com aquela regra especial)
    10: 1, # Mosquito: ataca a 1 bloco
    11: 1  # Barata: ataca a 1 bloco
}

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

def realizar_ataque_logica(alvo_r, alvo_c):
    global peca_selecionada, pos_selecionada, estado_seletor, estado_atual, hp_unidades
    
    alvo_id = meu_tabuleiro.entities[alvo_r][alvo_c]
    dano = DANO_UNIDADE.get(peca_selecionada, 1)
    hp_atual = hp_unidades.get((alvo_r, alvo_c), 3) - dano
    
    print(f"💥 BUM! Peça {peca_selecionada} atacou Peça {alvo_id} causando {dano} de dano!")

    if hp_atual <= 0:
        print(f"💀 A Peça {alvo_id} em [{alvo_r}][alvo_c] foi completamente destruída!")
        meu_tabuleiro.entities[alvo_r][alvo_c] = 0
        hp_unidades.pop((alvo_r, alvo_c), None)
    else:
        hp_unidades[(alvo_r, alvo_c)] = hp_atual
        print(f"Peça sobrevivente restou com {hp_atual} de HP.")

    # Como o ataque foi concluído, encerra o turno desta peça obrigatoriamente
    peca_selecionada = None
    pos_selecionada = None
    estado_seletor = MODO_NAVEGACAO
    estado_atual = TURNO_INIMIGO if estado_atual == TURNO_JOGADOR else TURNO_JOGADOR
    print(f"Turno alterado! Agora é a vez do: {estado_atual}")

def gerenciar_teclado(window, key, scancode, action, mods):
    global cursor_row, cursor_col, estado_seletor, peca_selecionada, pos_selecionada, estado_atual, hp_unidades
    global ALCANCE_MOVIMENTO, ALCANCE_ATAQUE

    if action == glfw.PRESS or action == glfw.REPEAT:
        # Movimentação básica do cursor
        if key == glfw.KEY_UP and cursor_row > 0:
            cursor_row -= 1
        elif key == glfw.KEY_DOWN and cursor_row < 7:
            cursor_row += 1
        elif key == glfw.KEY_LEFT and cursor_col > 0:
            cursor_col -= 1
        elif key == glfw.KEY_RIGHT and cursor_col < 7:
            cursor_col += 1
        
        # --- TECLA DE CANCELAR / SOLTAR A PEÇA (BACKSPACE ou ESC) ---
        elif (key == glfw.KEY_BACKSPACE or key == glfw.KEY_ESCAPE) and estado_seletor == MODO_MOVIMENTACAO:
            print(f"Seleção da peça {peca_selecionada} cancelada!")
            peca_selecionada = None
            pos_selecionada = None
            estado_seletor = MODO_NAVEGACAO

        # --- BOTÃO DE AÇÃO PRINCIPAL (ESPAÇO) ---
        elif key == glfw.KEY_SPACE:
            
            # ETAPA 1: SELECIONAR A PEÇA
            if estado_seletor == MODO_NAVEGACAO:
                id_peca = meu_tabuleiro.entities[cursor_row][cursor_col]
                
                if estado_atual == TURNO_JOGADOR and id_peca in [1, 2]:
                    peca_selecionada = id_peca
                    pos_selecionada = (cursor_row, cursor_col)
                    estado_seletor = MODO_MOVIMENTACAO
                    print(f"🤖 Peça {id_peca} selecionada. Espaço para MOVER ou 'A' para ATACAR daqui!")
                
                elif estado_atual == TURNO_INIMIGO and id_peca in [10, 11]:
                    peca_selecionada = id_peca
                    pos_selecionada = (cursor_row, cursor_col)
                    estado_seletor = MODO_MOVIMENTACAO
                    print(f"🪲 Peça {id_peca} selecionada. Espaço para MOVER ou 'A' para ATACAR daqui!")

            # ETAPA 2: REALIZAR A MOVIMENTAÇÃO (CLICOU EM CASA VAZIA)
            elif estado_seletor == MODO_MOVIMENTACAO:
                alvo_id = meu_tabuleiro.entities[cursor_row][cursor_col]
                origem_row, orig_col = pos_selecionada

                # Clicar na própria posição -> Solta a peça
                if (cursor_row, cursor_col) == pos_selecionada:
                    print("Peça solta.")
                    peca_selecionada = None
                    pos_selecionada = None
                    estado_seletor = MODO_NAVEGACAO
                    return

                # Casa vazia -> Tenta andar
                if alvo_id == 0:
                    diff_r = abs(cursor_row - origem_row)
                    diff_r = abs(cursor_row - origem_row)
                    diff_c = abs(cursor_col - orig_col)
                    
                    movimento_valido = False
                    
                    if peca_selecionada == 2: # Escavadeira
                        if max(diff_r, diff_c) <= 1:
                            movimento_valido = True
                    else: # Trator e Insetos
                        limite_passos = ALCANCE_MOVIMENTO.get(peca_selecionada, 2)
                        if (diff_r + diff_c) <= limite_passos:
                            movimento_valido = True

                    if movimento_valido:
                        # Executa o movimento na matriz
                        hp_atual = hp_unidades.pop((origem_row, orig_col), HP_INICIAL.get(peca_selecionada, 3))
                        meu_tabuleiro.entities[origem_row][orig_col] = 0
                        meu_tabuleiro.entities[cursor_row][cursor_col] = peca_selecionada
                        hp_unidades[(cursor_row, cursor_col)] = hp_atual

                        print("Peça movida! Turno finalizado por movimento.")
                        
                        # <<<<< MUDANÇA CRÍTICA AQUI >>>>>
                        # Em vez de ir para o MODO_ATAQUE, limpamos a seleção e passamos o turno imediatamente!
                        peca_selecionada = None
                        pos_selecionada = None
                        estado_seletor = MODO_NAVEGACAO
                        estado_atual = TURNO_INIMIGO if estado_atual == TURNO_JOGADOR else TURNO_JOGADOR
                        print(f"Vez do: {estado_atual}")
                    else:
                        if peca_selecionada == 2:
                            print("⚠️ Escavadeira só anda 1 quadrado (reto ou diagonal).")
                        else:
                            print(f"Movimento inválido! Limite: {ALCANCE_MOVIMENTO.get(peca_selecionada, 2)} bloco(s).")

        # --- BOTÃO DE ATAQUE DIRETO (TECLA A) ---
        elif key == glfw.KEY_A and estado_seletor == MODO_MOVIMENTACAO:
            if pos_selecionada is None:
                return
                
            atacante_row, atacante_col = pos_selecionada
            diff_r = abs(cursor_row - atacante_row)
            diff_c = abs(cursor_col - atacante_col)
            dist_ataque = diff_r + diff_c
            
            # Regra da diagonal imediata da Escavadeira
            if peca_selecionada == 2 and diff_r == 1 and diff_c == 1:
                dist_ataque = 1

            alvo_id = meu_tabuleiro.entities[cursor_row][cursor_col]
            limite_ataque = ALCANCE_ATAQUE.get(peca_selecionada, 1)

            eh_inimigo = (peca_selecionada in [1, 2] and alvo_id in [10, 11]) or (peca_selecionada in [10, 11] and id_peca in [1, 2])
            eh_inimigo = (peca_selecionada in [1, 2] and alvo_id in [10, 11]) or (peca_selecionada in [10, 11] and alvo_id in [1, 2])

            if eh_inimigo and dist_ataque <= limite_ataque:
                realizar_ataque_logica(cursor_row, cursor_col)
                
                # <<<<< MUDANÇA CRÍTICA AQUI >>>>>
                # Após atacar a partir do lugar atual, limpa tudo e passa o turno imediatamente!
                print("Ataque realizado! Turno finalizado por ataque.")
                peca_selecionada = None
                pos_selecionada = None
                estado_seletor = MODO_NAVEGACAO
                estado_atual = TURNO_INIMIGO if estado_atual == TURNO_JOGADOR else TURNO_JOGADOR
                print(f"Vez do: {estado_atual}")
            else:
                print("Alvo inválido ou fora do alcance de ataque a partir da sua posição atual!")

        # --- BOTÃO DE PASSAR TURNO MANUAL (TECLA P) ---
        elif key == glfw.KEY_P:
            print("Turno passado voluntariamente.")
            peca_selecionada = None
            pos_selecionada = None
            estado_seletor = MODO_NAVEGACAO
            estado_atual = TURNO_INIMIGO if estado_atual == TURNO_JOGADOR else TURNO_JOGADOR
            print(f"Vez do: {estado_atual}")
        # --- BOTÃO DE ATAQUE (TECLA A) ---
        elif key == glfw.KEY_A and estado_seletor in [MODO_MOVIMENTACAO, MODO_ATAQUE]:
            if pos_selecionada is None:
                return
                
            atacante_row, atacante_col = pos_selecionada
            diff_r = abs(cursor_row - atacante_row)
            diff_c = abs(cursor_col - atacante_col)
            dist_ataque = diff_r + diff_c
            
            # Regra da diagonal imediata da Escavadeira (ID 2)
            if peca_selecionada == 2 and diff_r == 1 and diff_c == 1:
                dist_ataque = 1

            alvo_id = meu_tabuleiro.entities[cursor_row][cursor_col]
            limite_ataque = ALCANCE_ATAQUE.get(peca_selecionada, 1)

            eh_inimigo = (peca_selecionada in [1, 2] and alvo_id in [10, 11]) or (peca_selecionada in [10, 11] and alvo_id in [1, 2])

            if eh_inimigo and dist_ataque <= limite_ataque:
                realizar_ataque_logica(cursor_row, cursor_col)
            else:
                print("Alvo inválido ou fora do alcance de ataque!")

        # --- BOTÃO DE PASSAR TURNO (TECLA P) ---
        elif key == glfw.KEY_P:
            print("Turno finalizado.")
            peca_selecionada = None
            pos_selecionada = None
            estado_seletor = MODO_NAVEGACAO
            estado_atual = TURNO_INIMIGO if estado_atual == TURNO_JOGADOR else TURNO_JOGADOR
            print(f"Vez do: {estado_atual}")

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

def desenhar_barra_vida(shader_program, x_centro, z_centro, hp_atual, hp_maximo):
    """
    Desenha pequenos quadradinhos de vida flutuando logo acima da unidade.
    Cada ponto de HP atual será um quadradinho verde, e o HP perdido fica cinza escuro.
    """
    y_flutuante = 1.3  # Altura acima da peça (ajuste conforme o tamanho do modelo)
    tamanho_bloco = 0.08  # Tamanho de cada quadradinho de vida
    espacamento = 0.2    # Espaço entre o centro de cada quadradinho

    # Calcula o ponto de partida à esquerda para centralizar os blocos
    inicio_x = x_centro - ((hp_maximo - 1) * espacamento) / 2.0

    for i in range(hp_maximo):
        x_bloco = inicio_x + (i * espacamento)
        
        # Define a cor: Verde se a peça ainda tem esse ponto de vida, Cinza se perdeu
        if i < hp_atual:
            cor_rgb = [0.2, 0.9, 0.2]  # Verde vivo
        else:
            cor_rgb = [0.2, 0.2, 0.2]  # Vermelho escuro ou cinza (vida perdida)

        # Vértices do quadradinho vertical (virado ligeiramente para a câmera em X/Y)
        vertices = np.array([
            [x_bloco - tamanho_bloco, y_flutuante - tamanho_bloco, z_centro],
            [x_bloco + tamanho_bloco, y_flutuante - tamanho_bloco, z_centro],
            [x_bloco + tamanho_bloco, y_flutuante + tamanho_bloco, z_centro],
            [x_bloco - tamanho_bloco, y_flutuante + tamanho_bloco, z_centro]
        ], dtype=np.float32)

        # Compila e envia para a GPU temporariamente
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
        
        # Desenha o quadrado preenchido
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        
        glUniform1i(glGetUniformLocation(shader_program, "u_use_solid_color"), 0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glDeleteBuffers(1, [vbo])
        glDeleteVertexArrays(1, [vao])

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

    # Dentro da função main(), logo após criar o 'meu_tabuleiro':
    global hp_unidades
    hp_unidades = {}
    
    # Mapeia a vida inicial de todas as peças encontradas no tabuleiro
    for r in range(8):
        for c in range(8):
            id_peca = meu_tabuleiro.entities[r][c]
            if id_peca != 0:
                hp_unidades[(r, c)] = HP_INICIAL.get(id_peca, 3)
    
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

        # <<<<< CORREÇÃO 1: RESETAR O MODO DE COR SÓLIDA PARA AS TEXTURAS VOLTAREM >>>>>
        glUniform1i(glGetUniformLocation(vertex_shader, "u_use_solid_color"), 0)

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
        
        # --- 3. DESENHAR PONTEIRO VISUAL DO CURSOR E ÁREAS DE AÇÃO ---
        x_cursor_mundo = cursor_col - 3.5
        z_cursor_mundo = cursor_row - 3.5

        # A) Desenha a seta na posição do cursor
        if estado_seletor in [MODO_MOVIMENTACAO, MODO_ATAQUE]:
            minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=tempo_atual * 15.0)
        else:
            minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=0)

        # B) SE UMA PEÇA ESTIVER SELECIONADA: Mostra a malha de ações (Apenas em MODO_MOVIMENTACAO)
        if estado_seletor == MODO_MOVIMENTACAO and pos_selecionada is not None:
            origem_row, orig_col = pos_selecionada
            
            if peca_selecionada == 2:
                limite_passos = 1
            else:
                limite_passos = ALCANCE_MOVIMENTO.get(peca_selecionada, 2)
                
            limite_ataque = ALCANCE_ATAQUE.get(peca_selecionada, 1)

            for r in range(8):
                for c in range(8):
                    if r == origem_row and c == orig_col:
                        continue

                    diff_row = abs(r - origem_row)
                    diff_col = abs(c - orig_col)
                    
                    if peca_selecionada == 2:
                        pode_mover = max(diff_row, diff_col) <= limite_passos
                    else:
                        pode_mover = (diff_row + diff_col) <= limite_passos
                    
                    dist_ataque = diff_row + diff_col
                    if peca_selecionada == 2 and diff_row == 1 and diff_col == 1:
                        dist_ataque = 1

                    pode_atacar = dist_ataque <= limite_ataque
                    id_ocupante = meu_tabuleiro.entities[r][c]
                    x_valido = c - 3.5
                    z_valido = r - 3.5

                    # Inimigos Reais atacáveis a partir da posição atual
                    if id_ocupante != 0:
                        eh_inimigo = (peca_selecionada in [1, 2] and id_ocupante in [10, 11]) or (peca_selecionada in [10, 11] and id_ocupante in [1, 2])
                        if eh_inimigo and pode_atacar:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 0.1, 0.1], tamanho=0.35)

                    # Espaços vazios (Zonas de projeção)
                    else:
                        if pode_mover and pode_atacar:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[0.6, 0.0, 0.0], tamanho=0.35)
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.22)
                        elif pode_mover:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.35)
                        elif pode_atacar:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[0.6, 0.0, 0.0], tamanho=0.35)

        # C) CONFIGURAÇÃO DE COR DO CURSOR PRINCIPAL
        if estado_seletor == MODO_MOVIMENTACAO:
            # Modo Seleção: Amarelo
            desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[1.0, 0.8, 0.0], tamanho=0.5)
        else:
            # Modo Navegação Livre: Verde
            desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[0.2, 0.8, 0.2], tamanho=0.5)

        # <<<<< CORREÇÃO 2: ATUALIZAR A TELA E RECOLHER OS EVENTOS DO TECLADO >>>>>
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()