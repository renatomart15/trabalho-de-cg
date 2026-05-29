# main.py
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
import math

# Importações dos nossos submódulos e configurações organizadas
from config import *
from regras_combate import*
from estado_jogo import EstadoJogo
from render_utils import desenhar_borda_cursor, desenhar_barra_vida

from models import Modelo3DComTextura 
from tabuleiro import Tabuleiro

projection = None
game = None  # Objeto gerenciador do EstadoGlobal

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

def gerenciar_teclado(window, key, scancode, action, mods):
    global game
    if action != glfw.PRESS and action != glfw.REPEAT:
        return

    # 1. Movimentação do Cursor
    if key == glfw.KEY_UP and game.cursor_row > 0:
        game.cursor_row -= 1
    elif key == glfw.KEY_DOWN and game.cursor_row < 7:
        game.cursor_row += 1
    elif key == glfw.KEY_LEFT and game.cursor_col > 0:
        game.cursor_col -= 1
    elif key == glfw.KEY_RIGHT and game.cursor_col < 7:
        game.cursor_col += 1
    
    # 2. Cancelar Seleção (ESC / Backspace)
    elif (key == glfw.KEY_BACKSPACE or key == glfw.KEY_ESCAPE) and game.estado_seletor == MODO_MOVIMENTACAO:
        print(f"Seleção da peça {game.peca_selecionada} cancelada!")
        game.peca_selecionada = None
        game.pos_selecionada = None
        game.estado_seletor = MODO_NAVEGACAO

    # 3. Botão de Seleção / Movimentação (ESPAÇO)
    elif key == glfw.KEY_SPACE:
        # A) Selecionar Peça
        if game.estado_seletor == MODO_NAVEGACAO:
            id_peca = game.tabuleiro.entities[game.cursor_row][game.cursor_col]
            
            if game.turno_atual == TURNO_JOGADOR and id_peca in [1, 2]:
                game.peca_selecionada = id_peca
                game.pos_selecionada = (game.cursor_row, game.cursor_col)
                game.estado_seletor = MODO_MOVIMENTACAO
                print(f"Robô {id_peca} selecionado. Espaço para MOVER ou 'A' para ATACAR!")
            
            elif game.turno_atual == TURNO_INIMIGO and id_peca in [10, 11]:
                game.peca_selecionada = id_peca
                game.pos_selecionada = (game.cursor_row, game.cursor_col)
                game.estado_seletor = MODO_MOVIMENTACAO
                print(f"Inseto {id_peca} selecionado. Espaço para MOVER ou 'A' para ATACAR!")

        # B) Mover Peça Selecionada
        elif game.estado_seletor == MODO_MOVIMENTACAO:
            alvo_id = game.tabuleiro.entities[game.cursor_row][game.cursor_col]
            origem_row, orig_col = game.pos_selecionada

            if (game.cursor_row, game.cursor_col) == game.pos_selecionada:
                game.peca_selecionada = None
                game.pos_selecionada = None
                game.estado_seletor = MODO_NAVEGACAO
                print("Peça solta.")
                return

            # Destino vazio -> Move validando o caminho e o terreno (passando game.tabuleiro)
            if alvo_id == 0:
                if validar_movimento(origem_row, orig_col, game.cursor_row, game.cursor_col, game.peca_selecionada, game.tabuleiro):
                    hp_atual = game.hp_unidades.pop((origem_row, orig_col), HP_INICIAL.get(game.peca_selecionada, 3))
                    game.tabuleiro.entities[origem_row][orig_col] = 0
                    game.tabuleiro.entities[game.cursor_row][game.cursor_col] = game.peca_selecionada
                    game.hp_unidades[(game.cursor_row, game.cursor_col)] = hp_atual

                    print("Peça movida com sucesso!")
                    game.alternar_turno()
                else:
                    print("Movimento inválido! Fora de alcance ou bloqueado por água/obstáculos.")

    # 4. Botão de Ataque Direto (A)
    elif key == glfw.KEY_A and game.estado_seletor == MODO_MOVIMENTACAO:
        if game.pos_selecionada is None:
            return
            
        origem_row, orig_col = game.pos_selecionada
        dist_ataque = calcular_distancia_ataque(origem_row, orig_col, game.cursor_row, game.cursor_col, game.peca_selecionada)
        
        alvo_id = game.tabuleiro.entities[game.cursor_row][game.cursor_col]
        limite_ataque = ALCANCE_ATAQUE.get(game.peca_selecionada, 1)

        if verificar_inimigo(game.peca_selecionada, alvo_id) and dist_ataque <= limite_ataque:
            game.aplicar_ataque(game.cursor_row, game.cursor_col)
        else:
            print("Alvo inválido ou fora do alcance de ataque!")

    # 5. Passar Turno Voluntariamente (P)
    elif key == glfw.KEY_P:
        print("Turno passado voluntariamente.")
        game.alternar_turno()

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
    if altura == 0: altura = 1
    glViewport(0, 0, largura, altura)
    global projection
    projection = pyrr.matrix44.create_perspective_projection_matrix(45.0, largura / altura, 0.1, 100.0)

def main():
    global game, projection

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
    glfw.set_key_callback(window, gerenciar_teclado)
    glEnable(GL_DEPTH_TEST) 

    redimensionar_janela(window, largura_tela, altura_tela)
    vertex_shader = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    
    # Inicializa tabuleiro e estado unificado do jogo
    meu_tabuleiro = Tabuleiro()
    game = EstadoJogo(meu_tabuleiro)
    
    # Carregamento de Malhas e Assets Técnicos
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
        glUniform1i(glGetUniformLocation(vertex_shader, "u_use_solid_color"), 0)

        game.tabuleiro.draw(vertex_shader)
        tempo_atual = glfw.get_time()

        # --- Renderização de Modelos e Vidas ---
        for row in range(8):
            for col in range(8):
                x_mundo = col - 3.5
                z_mundo = row - 3.5
                id_entidade = game.tabuleiro.entities[row][col]

                if id_entidade == 0:
                    continue

                # Desenho das malhas 3D
                if id_entidade == 1: 
                    meu_trator.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                elif id_entidade == 2: 
                    minha_escavadeira.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                
                elif id_entidade == 10: 
                    # Efeito de Levitação: Calcula uma oscilação vertical baseada no seno do tempo
                    offset_levitacao = 0.5 + math.sin(tempo_atual * 3.0) * 0.12
                    altura_original = meu_mosquito.altura
                    
                    # Aplica a altura somada com a oscilação e desenha
                    meu_mosquito.altura = altura_original + offset_levitacao
                    meu_mosquito.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 5.0)
                    meu_mosquito.altura = altura_original  # Restaura a propriedade
                    
                    # Desenha a sombra dinâmica no chão (encolhe conforme o mosquito sobe)
                    raio_dinamico = 0.28 - (offset_levitacao * 0.1)
                    desenhar_sombra_circulo(vertex_shader, x_mundo, z_mundo, raio=raio_dinamico)

                elif id_entidade == 11: 
                    barata.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 8.0)
                elif id_entidade == 50: 
                    minha_casa.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=0)

                # Desenho da interface de vida flutuante (Robôs, Insetos e Casas)
                if id_entidade in [1, 2, 10, 11, 50]:
                    hp_atual = game.hp_unidades.get((row, col), 3)
                    hp_max = HP_INICIAL.get(id_entidade, 3)
                    desenhar_barra_vida(vertex_shader, x_mundo, z_mundo, hp_atual, hp_max, view)
        
        # --- Desenho do Cursor e Projeções Táticas ---
        x_cursor_mundo = game.cursor_col - 3.5
        z_cursor_mundo = game.cursor_row - 3.5

        if game.estado_seletor in [MODO_MOVIMENTACAO, MODO_ATAQUE]:
            minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=tempo_atual * 15.0)
        else:
            minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=0)

        # Renderização da grade de previsão ativa (Respeitando caminhos por água)
        if game.estado_seletor == MODO_MOVIMENTACAO and game.pos_selecionada is not None:
            origem_row, orig_col = game.pos_selecionada
            limite_ataque = ALCANCE_ATAQUE.get(game.peca_selecionada, 1)

            for r in range(8):
                for c in range(8):
                    if r == origem_row and c == orig_col: continue

                    # Passando game.tabuleiro para validar caminhos na previsão tática visual
                    pode_mover = validar_movimento(origem_row, orig_col, r, c, game.peca_selecionada, game.tabuleiro)
                    dist_ataque = calcular_distancia_ataque(origem_row, orig_col, r, c, game.peca_selecionada)
                    pode_atacar = dist_ataque <= limite_ataque
                    
                    id_ocupante = game.tabuleiro.entities[r][c]
                    x_valido = c - 3.5
                    z_valido = r - 3.5

                    if id_ocupante != 0:
                        if verificar_inimigo(game.peca_selecionada, id_ocupante) and pode_atacar:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 0.1, 0.1], tamanho=0.35)
                    else:
                        if pode_mover and pode_atacar:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[0.6, 0.0, 0.0], tamanho=0.35)
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.22)
                        elif pode_mover:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.35)
                        elif pode_atacar:
                            desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[0.6, 0.0, 0.0], tamanho=0.35)

        # Define a cor do cursor principal
        if game.estado_seletor == MODO_MOVIMENTACAO:
            desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[1.0, 0.8, 0.0], tamanho=0.5)
        else:
            desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[0.2, 0.8, 0.2], tamanho=0.5)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()