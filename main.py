# main.py
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import glfw
import pyrr
import numpy as np
import math

from config import *
from regras_combate import*
from estado_jogo import EstadoJogo
from render_utils import desenhar_borda_cursor, desenhar_barra_vida, carregar_textura_menu, desenhar_botao_texturizado, desenhar_botao_menu, desenhar_sombra_circulo

from models import Modelo3DComTextura 
from tabuleiro import Tabuleiro

estado_app = "MENU"
opcao_menu = 1
projection = None
game = None  


def gerenciar_teclado(window, key, scancode, action, mods):
    global game, estado_app, opcao_menu

    if action != glfw.PRESS and action != glfw.REPEAT:
        return
    
    # -------------------------------------------------------------------------
    # 1. LOGICA DO MENU 
    # -------------------------------------------------------------------------
    if estado_app == "MENU":
        if key == glfw.KEY_LEFT and opcao_menu > 1:
            opcao_menu -= 1
        elif key == glfw.KEY_RIGHT and opcao_menu < 3:
            opcao_menu += 1
        elif key == glfw.KEY_SPACE or key == glfw.KEY_ENTER:
            # Importações internas caso necessário para garantir o escopo
            from tabuleiro import Tabuleiro
            from estado_jogo import EstadoJogo
            
            game = EstadoJogo(Tabuleiro(mapa_id=opcao_menu))
            estado_app = "JOGO"
        return # Sai para não misturar inputs do menu com os do jogo

    # -------------------------------------------------------------------------
    # 2. TRAVAS DE SEGURANÇA PARA A PARTIDA EM ANDAMENTO
    # -------------------------------------------------------------------------
   
    if game is None or game.jogo_finalizado:
        return

    # -------------------------------------------------------------------------
    # 3. CONTROLES DO JOGO 
    # -------------------------------------------------------------------------
    # Movimentação do Cursor
    if key == glfw.KEY_UP and game.cursor_row > 0:
        game.cursor_row -= 1
    elif key == glfw.KEY_DOWN and game.cursor_row < 7:
        game.cursor_row += 1
    elif key == glfw.KEY_LEFT and game.cursor_col > 0:
        game.cursor_col -= 1
    elif key == glfw.KEY_RIGHT and game.cursor_col < 7:
        game.cursor_col += 1
    
    # Cancelar seleção
    elif (key == glfw.KEY_BACKSPACE or key == glfw.KEY_ESCAPE) and game.estado_seletor == MODO_MOVIMENTACAO:
        game.peca_selecionada = None
        game.pos_selecionada = None
        game.estado_seletor = MODO_NAVEGACAO

    # Ação de Seleção ou Movimento (Espaço)
    elif key == glfw.KEY_SPACE:
        if game.estado_seletor == MODO_NAVEGACAO:
            id_peca = game.tabuleiro.entities[game.cursor_row][game.cursor_col]
            
            if game.turno_atual == TURNO_JOGADOR and id_peca in [1, 2]:
                game.peca_selecionada = id_peca
                game.pos_selecionada = (game.cursor_row, game.cursor_col)
                game.estado_seletor = MODO_MOVIMENTACAO

            elif game.turno_atual == TURNO_INIMIGO and id_peca in [10, 11]:
                game.peca_selecionada = id_peca
                game.pos_selecionada = (game.cursor_row, game.cursor_col)
                game.estado_seletor = MODO_MOVIMENTACAO
            
        elif game.estado_seletor == MODO_MOVIMENTACAO:
            alvo_id = game.tabuleiro.entities[game.cursor_row][game.cursor_col]
            origem_row, orig_col = game.pos_selecionada

            if (game.cursor_row, game.cursor_col) == game.pos_selecionada:
                game.peca_selecionada = None
                game.pos_selecionada = None
                game.estado_seletor = MODO_NAVEGACAO
                return

            if alvo_id == 0:
                if validar_movimento(origem_row, orig_col, game.cursor_row, game.cursor_col, game.peca_selecionada, game.tabuleiro):
                    hp_atual = game.hp_unidades.pop((origem_row, orig_col), HP_INICIAL.get(game.peca_selecionada, 3))
                    game.tabuleiro.entities[origem_row][orig_col] = 0
                    game.tabuleiro.entities[game.cursor_row][game.cursor_col] = game.peca_selecionada
                    game.hp_unidades[(game.cursor_row, game.cursor_col)] = hp_atual
                    game.alternar_turno()
                
    # Comando de Ataque (A)
    elif key == glfw.KEY_A and game.estado_seletor == MODO_MOVIMENTACAO:
        if game.pos_selecionada is None:
            return
            
        origem_row, orig_col = game.pos_selecionada
        dist_ataque = calcular_distancia_ataque(origem_row, orig_col, game.cursor_row, game.cursor_col, game.peca_selecionada)
        
        alvo_id = game.tabuleiro.entities[game.cursor_row][game.cursor_col]
        limite_ataque = ALCANCE_ATAQUE.get(game.peca_selecionada, 1)

        if verificar_inimigo(game.peca_selecionada, alvo_id) and dist_ataque <= limite_ataque:
            game.aplicar_ataque(game.cursor_row, game.cursor_col)

    # Passar Turno Manual (P)
    elif key == glfw.KEY_P:
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
    global game, projection, estado_app

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

    
    game = None

    redimensionar_janela(window, largura_tela, altura_tela)
    vertex_shader = inicializar_shaders("shaders/vertex_shader.glsl", "shaders/fragment_shader.glsl")
    
    meu_trator = Modelo3DComTextura("assets/trator.obj", "assets/trator_textura.jpeg", escala=0.4, altura=0.3)
    minha_casa = Modelo3DComTextura("assets/casa.obj", "assets/casa_textura.jpeg", escala=0.001, altura=-0.3)
    meu_mosquito = Modelo3DComTextura("assets/mosquito.obj", "assets/mosquito_textura.png", escala=0.05, altura=0.3)
    minha_escavadeira = Modelo3DComTextura("assets/escavadeira.obj", "assets/escavadeira_textura.jpeg", escala=0.13, altura=0.1)
    barata = Modelo3DComTextura("assets/barata.obj", "assets/barata_textura.png", escala=0.1, altura=0.1)
    minha_seta = Modelo3DComTextura("assets/seta.obj", "assets/seta_textura.png", escala=0.2, altura=1.2)

    view = pyrr.matrix44.create_look_at(eye=[9, 9, 9], target=[0, 0, 0], up=[0, 1, 0])

    text_btao_mapa1 = carregar_textura_menu("assets/btn_mapa1.png")
    text_btao_mapa2 = carregar_textura_menu("assets/btn_mapa2.png")
    text_btao_mapa3 = carregar_textura_menu("assets/btn_mapa3.png")

    tex_escavadeira_5 = carregar_textura_menu("assets/tratordedesmatamento5.png")
    tex_escavadeira_4 = carregar_textura_menu("assets/tratordedesmatamento4.png")
    tex_escavadeira_3 = carregar_textura_menu("assets/tratordedesmatamento3.png")
    tex_escavadeira_2 = carregar_textura_menu("assets/tratordedesmatamento2.png")
    tex_escavadeira_1 = carregar_textura_menu("assets/tratordedesmatamento1.png")

    tex_mosquito_1 = carregar_textura_menu("assets/muricocamutante1.png")
    tex_mosquito_2 = carregar_textura_menu("assets/muricocamutante2.png")
    tex_mosquito_3 = carregar_textura_menu("assets/muricocamutante3.png")

    tex_trator_1 = carregar_textura_menu("assets/tratoragricola1.png")
    tex_trator_2 = carregar_textura_menu("assets/tratoragricola2.png")
    tex_trator_3 = carregar_textura_menu("assets/tratoragricola3.png")
    tex_trator_4 = carregar_textura_menu("assets/tratoragricola4.png")
    tex_trator_5 = carregar_textura_menu("assets/tratoragricola5.png") 

    tex_barata_1 = carregar_textura_menu("assets/baratamutante1.png")
    tex_barata_2 = carregar_textura_menu("assets/baratamutante2.png")
    tex_barata_3 = carregar_textura_menu("assets/baratamutante3.png")
    tex_barata_4 = carregar_textura_menu("assets/baratamutante4.png")

    tex_padrao = tex_trator_5

    tex_vitoria_defensores = carregar_textura_menu("assets/defensores.png")
    tex_vitoria_atacantes = carregar_textura_menu("assets/atacantes.png")

    texturas_hud = {
        1:  {5: tex_trator_5, 4: tex_trator_4, 3: tex_trator_3, 2: tex_trator_2, 1: tex_trator_1},
        2:  {4: tex_escavadeira_4, 3: tex_escavadeira_3, 2: tex_escavadeira_2, 1: tex_escavadeira_1},
        10: {3: tex_mosquito_3, 2: tex_mosquito_2, 1: tex_mosquito_1},
        11: {4: tex_barata_4, 3: tex_barata_3, 2: tex_barata_2, 1: tex_barata_1}
    }

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # ---------------------------------------------------------------------
        # ESTADO: MENU PRINCIPAL
        # ---------------------------------------------------------------------
        if estado_app == "MENU":
            glClearColor(0.15, 0.15, 0.15, 1.0)
            glUseProgram(vertex_shader)

            glUniform1i(glGetUniformLocation(vertex_shader, "u_use_lighting"), 0)
            glDisable(GL_DEPTH_TEST)

            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            tamanho_borda_larg = 0.38
            tamanho_borda_alt = 0.53
            cor_branca = [1.0, 1.0, 1.0]

            if opcao_menu == 1:
                desenhar_botao_menu(vertex_shader, -0.5, 0.0, tamanho_borda_larg, tamanho_borda_alt, cor_branca)     
            elif opcao_menu == 2:
                desenhar_botao_menu(vertex_shader, 0.0, 0.0, tamanho_borda_larg, tamanho_borda_alt, cor_branca)      
            elif opcao_menu == 3:
                desenhar_botao_menu(vertex_shader, 0.5, 0.0, tamanho_borda_larg, tamanho_borda_alt, cor_branca)      

            desenhar_botao_texturizado(vertex_shader, -0.5, 0.0, 0.35, 0.5, text_btao_mapa1)   
            desenhar_botao_texturizado(vertex_shader,  0.0, 0.0, 0.35, 0.5, text_btao_mapa2)   
            desenhar_botao_texturizado(vertex_shader,  0.5, 0.0, 0.35, 0.5, text_btao_mapa3)   

            glDisable(GL_BLEND)
            glEnable(GL_DEPTH_TEST)

        # ---------------------------------------------------------------------
        # ESTADO: JOGO ATIVO
        # ---------------------------------------------------------------------
        elif estado_app == "JOGO" and game is not None:
            
            # CENÁRIO A: O JOGO ACABOU 
            if game.jogo_finalizado:
                if game.resultado_vencedor == "DEFENSORES":
                    glClearColor(0.05, 0.25, 0.05, 1.0) # Verde escuro
                    textura_mensagem = tex_vitoria_defensores
                else:
                    glClearColor(0.25, 0.05, 0.05, 1.0) # Vermelho escuro
                    textura_mensagem = tex_vitoria_atacantes
                
                glDisable(GL_DEPTH_TEST) 
                glEnable(GL_BLEND)       
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

               
                desenhar_botao_texturizado(vertex_shader, 0.0, 0.0, 1.4, 0.7, textura_mensagem)

                glDisable(GL_BLEND)

            # CENÁRIO B: PARTIDA ROLANDO NORMALMENTE
            else:
                glEnable(GL_DEPTH_TEST)
                glClearColor(0.12, 0.12, 0.12, 1.0) 
                glUseProgram(vertex_shader)

                glUniform1i(glGetUniformLocation(vertex_shader, "u_use_lighting"), 1)
                glUniform3f(glGetUniformLocation(vertex_shader, "viewPos"), 9.0, 9.0, 9.0) 

                if game.tabuleiro.mapa_id in [2, 3]:
                    glUniform3f(glGetUniformLocation(vertex_shader, "lightPos"), 2.0, 18.0, 2.0)
                    glUniform3f(glGetUniformLocation(vertex_shader, "lightColor"), 1.0, 0.98, 0.92) 
                    glUniform1f(glGetUniformLocation(vertex_shader, "ambientStrength"), 0.45) 
                else:
                    glUniform3f(glGetUniformLocation(vertex_shader, "lightPos"), 0.0, 15.0, 0.0)
                    glUniform3f(glGetUniformLocation(vertex_shader, "lightColor"), 0.6, 0.6, 0.65) 
                    glUniform1f(glGetUniformLocation(vertex_shader, "ambientStrength"), 0.6)

                glUniformMatrix4fv(glGetUniformLocation(vertex_shader, "view"), 1, GL_FALSE, view)
                glUniformMatrix4fv(glGetUniformLocation(vertex_shader, "projection"), 1, GL_FALSE, projection)
                glUniform1i(glGetUniformLocation(vertex_shader, "u_use_solid_color"), 0)
                
                game.tabuleiro.draw(vertex_shader)
                tempo_atual = glfw.get_time()

                # Desenhar as unidades no tabuleiro
                for row in range(8):
                    for col in range(8):
                        x_mundo = col - 3.5
                        z_mundo = row - 3.5
                        id_entidade = game.tabuleiro.entities[row][col]

                        if id_entidade == 0:
                            continue
                    
                        if id_entidade == 1: 
                            meu_trator.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                        elif id_entidade == 2: 
                            minha_escavadeira.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual)
                        
                        elif id_entidade == 10: 
                            offset_levitacao = 0.5 + math.sin(tempo_atual * 3.0) * 0.12
                            altura_original = meu_mosquito.altura
                            
                            meu_mosquito.altura = altura_original + offset_levitacao
                            meu_mosquito.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 5.0)
                            meu_mosquito.altura = altura_original  
                            
                            raio_dinamico = 0.28 - (offset_levitacao * 0.1)
                            desenhar_sombra_circulo(vertex_shader, x_mundo, z_mundo, raio=raio_dinamico)

                        elif id_entidade == 11: 
                            barata.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=tempo_atual * 8.0)
                        elif id_entidade == 50: 
                            minha_casa.desenhar(vertex_shader, x_mundo, z_mundo, angulo_pa=0)

                        if id_entidade in [1, 2, 10, 11, 50]:
                            hp_atual = game.hp_unidades.get((row, col), 3)
                            hp_max = HP_INICIAL.get(id_entidade, 3)
                            desenhar_barra_vida(vertex_shader, x_mundo, z_mundo, hp_atual, hp_max, view)
                
                
                glUniform1i(glGetUniformLocation(vertex_shader, "u_use_lighting"), 0)
                x_cursor_mundo = game.cursor_col - 3.5
                z_cursor_mundo = game.cursor_row - 3.5

                if game.estado_seletor in [MODO_MOVIMENTACAO, MODO_ATAQUE]:
                    minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=tempo_atual * 15.0)
                else:
                    minha_seta.desenhar(vertex_shader, x_cursor_mundo, z_cursor_mundo, angulo_pa=0)

                if game.estado_seletor == MODO_MOVIMENTACAO and game.pos_selecionada is not None:
                    origem_row, orig_col = game.pos_selecionada
                    limite_ataque = ALCANCE_ATAQUE.get(game.peca_selecionada, 1)

                    for r in range(8):
                        for c in range(8):
                            if r == origem_row and c == orig_col: continue

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
                                    desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 0.8, 0.0], tamanho=0.35)
                                elif pode_mover:
                                    desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[1.0, 1.0, 1.0], tamanho=0.35)
                                elif pode_atacar:
                                    desenhar_borda_cursor(vertex_shader, x_valido, z_valido, cor_rgb=[0.6, 0.0, 0.0], tamanho=0.35)

                if game.estado_seletor == MODO_MOVIMENTACAO:
                    desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[1.0, 0.8, 0.0], tamanho=0.5)
                else:
                    desenhar_borda_cursor(vertex_shader, x_cursor_mundo, z_cursor_mundo, cor_rgb=[0.2, 0.8, 0.2], tamanho=0.5)

               
                if game.peca_selecionada is not None:
                    glDisable(GL_DEPTH_TEST)
                    glEnable(GL_BLEND)
                    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

                    x_placa = 0.65
                    y_placa = -0.65
                    larg_placa = 0.6
                    alt_placa = 0.5

                    hp_atual = game.hp_unidades.get(game.pos_selecionada, 0)
                    textura_para_desenhar = texturas_hud.get(game.peca_selecionada, {}).get(hp_atual, tex_padrao)

                    desenhar_botao_menu(vertex_shader, x_placa, y_placa, larg_placa + 0.02, alt_placa + 0.02, [1.0, 1.0, 1.0])                                                     

                    desenhar_botao_texturizado(vertex_shader, x_placa, y_placa, larg_placa, alt_placa, textura_para_desenhar)
                    
                    glDisable(GL_BLEND)
                    glEnable(GL_DEPTH_TEST)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()