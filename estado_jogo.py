# estado_jogo.py
from config import (
    TURNO_JOGADOR,
    TURNO_INIMIGO,
    MODO_NAVEGACAO,
    HP_INICIAL,
    DANO_UNIDADE,
    MAX_TURNOS_PARTIDA
)


class EstadoJogo:
    def __init__(self, tabuleiro):
        self.tabuleiro = tabuleiro
        self.turno_atual = TURNO_JOGADOR
        self.estado_seletor = MODO_NAVEGACAO

        self.cursor_row = 4
        self.cursor_col = 4

        self.peca_selecionada = None
        self.pos_selecionada = None

        self.jogo_finalizado = False
        self.resultado_vencedor = None  # "DEFENSORES" ou "ATACANTES"

        # 🔑 CORREÇÃO 1: Adicionado o contador de turnos que estava faltando!
        self.turno_contador = 1

        self.hp_unidades = {}
        self.inicializar_vidas()

    def inicializar_vidas(self):
        for r in range(8):
            for c in range(8):
                id_peca = self.tabuleiro.entities[r][c]
                if id_peca != 0:
                    self.hp_unidades[(r, c)] = HP_INICIAL.get(id_peca, 3)

    def verificar_fim_de_jogo(self):
        """Analisa o tabuleiro para determinar se houve um vencedor e muda o estado do jogo."""
        if self.jogo_finalizado:
            return True

        existe_robo = False
        existe_inseto = False
        existe_casa = False

        # Varre as 64 casas do tabuleiro diretamente para não depender do dicionário de HP
        for r in range(8):
            for c in range(8):
                id_peca = self.tabuleiro.entities[r][c]
                
                if id_peca in [1, 2]:    # IDs dos seus Robôs (Trator, Escavadeira)
                    existe_robo = True
                elif id_peca in [10, 11]: # IDs dos seus Insetos (Mosquito, Barata)
                    existe_inseto = True
                elif id_peca == 50:       # ID da Casa
                    existe_casa = True

        # CONDICIONAL 1: Insetos destruíram todas as casas -> Vitória dos Atacantes
        if not existe_casa:
            self.jogo_finalizado = True
            self.resultado_vencedor = "ATACANTES"
            print("▶️ FIM DE JOGO: Casas destruídas! ATACANTES VENCERAM.")
            return True

        # CONDICIONAL 2: Insetos destruíram todos os robôs -> Vitória dos Atacantes
        if not existe_robo:
            self.jogo_finalizado = True
            self.resultado_vencedor = "ATACANTES"
            print("▶️ FIM DE JOGO: Robôs destruídos! ATACANTES VENCERAM.")
            return True

        # CONDICIONAL 3: Robôs eliminaram todos os insetos -> Vitória dos Defensores
        if not existe_inseto:
            self.jogo_finalizado = True
            self.resultado_vencedor = "DEFENSORES"
            print("▶️ FIM DE JOGO: Insetos eliminados! DEFENSORES VENCERAM.")
            return True

        # CONDICIONAL 4: Defensores resistiram ao limite de turnos
        if self.turno_contador > MAX_TURNOS_PARTIDA:
            self.jogo_finalizado = True
            self.resultado_vencedor = "DEFENSORES"
            print("▶️ FIM DE JOGO: Turnos esgotados! DEFENSORES VENCERAM.")
            return True

        return False

    def alternar_turno(self):
        self.peca_selecionada = None
        self.pos_selecionada = None
        self.estado_seletor = MODO_NAVEGACAO
        
        # 🔑 CORREÇÃO 2: Incrementa o turno_contador quando o ciclo de turnos avança
        if self.turno_atual == TURNO_INIMIGO:
            self.turno_contador += 1
            print(f"⏰ Avançando para o Turno: {self.turno_contador}/{MAX_TURNOS_PARTIDA}")

        self.turno_atual = (
            TURNO_INIMIGO if self.turno_atual == TURNO_JOGADOR else TURNO_JOGADOR
        )

        # 🔑 CORREÇÃO 3: Força a checagem imediatamente no momento da troca de turno
        self.verificar_fim_de_jogo()

    def causar_dano(self, r, c, quantidade):
        if (r, c) not in self.hp_unidades:
            return

        self.hp_unidades[(r, c)] -= quantidade
        hp_restante = self.hp_unidades[(r, c)]

        if hp_restante <= 0:
            self.tabuleiro.entities[r][c] = 0
            self.hp_unidades.pop((r, c), None)

    def aplicar_ataque(self, alvo_r, alvo_c):
        """Aplica o dano base e calcula o efeito de empurrão (apenas para robôs e insetos)."""
        origem_r, origem_c = self.pos_selecionada
        id_atacante = self.peca_selecionada
        id_alvo = self.tabuleiro.entities[alvo_r][alvo_c]

        # 1. APLICAR DANO DIRETO INICIAL
        dano_base = DANO_UNIDADE.get(id_atacante, 1)

        # Salva o HP antes do ataque para saber se o alvo vai sobreviver
        hp_alvo_antes = self.hp_unidades.get((alvo_r, alvo_c), 0)
        self.causar_dano(alvo_r, alvo_c, dano_base)

        if hp_alvo_antes - dano_base <= 0:
            self.alternar_turno()
            return

        if id_alvo == 50:
            self.alternar_turno()
            return

        dir_r = alvo_r - origem_r
        dir_c = alvo_c - origem_c

        if dir_r != 0:
            dir_r = 1 if dir_r > 0 else -1
        if dir_c != 0:
            dir_c = 1 if dir_c > 0 else -1

        dest_r = alvo_r + dir_r
        dest_c = alvo_c + dir_c

        # 3. VERIFICAR CENÁRIOS DE COLISÃO
        if not (0 <= dest_r < 8 and 0 <= dest_c < 8):
            self.causar_dano(alvo_r, alvo_c, 1)

        elif self.tabuleiro.entities[dest_r][dest_c] != 0:
            self.causar_dano(alvo_r, alvo_c, 1)
            self.causar_dano(dest_r, dest_c, 1)

        elif self.tabuleiro.grid[dest_r][dest_c] == 1:
            if id_alvo != 10:  # Se não for o mosquito voador, afoga
                self.causar_dano(
                    alvo_r, alvo_c, self.hp_unidades.get((alvo_r, alvo_c), 99)
                )
            else:
                self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        else:
            self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        self.alternar_turno()

    def deslocar_entidade_fisicamente(self, r_orig, c_orig, r_dest, c_dest):
        id_peca = self.tabuleiro.entities[r_orig][c_orig]
        hp_atual = self.hp_unidades.pop((r_orig, c_orig), HP_INICIAL.get(id_peca, 3))

        self.tabuleiro.entities[r_orig][c_orig] = 0
        self.tabuleiro.entities[r_dest][c_dest] = id_peca
        self.hp_unidades[(r_dest, c_dest)] = hp_atual