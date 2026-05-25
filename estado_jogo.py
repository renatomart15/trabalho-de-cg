# estado_jogo.py
from config import TURNO_JOGADOR, TURNO_INIMIGO, MODO_NAVEGACAO, HP_INICIAL, DANO_UNIDADE

class EstadoJogo:
    def __init__(self, tabuleiro):
        self.tabuleiro = tabuleiro
        self.turno_atual = TURNO_JOGADOR
        self.estado_seletor = MODO_NAVEGACAO
        
        self.cursor_row = 4
        self.cursor_col = 4
        
        self.peca_selecionada = None
        self.pos_selecionada = None
        
        self.hp_unidades = {}
        self.inicializar_vidas()

    def inicializar_vidas(self):
        """Mapeia a vida de todas as peças (incluindo as casas) no início do jogo."""
        for r in range(8):
            for c in range(8):
                id_peca = self.tabuleiro.entities[r][c]
                if id_peca != 0:
                    self.hp_unidades[(r, c)] = HP_INICIAL.get(id_peca, 3)

    def alternar_turno(self):
        """Limpa as seleções e passa o controle do turno."""
        self.peca_selecionada = None
        self.pos_selecionada = None
        self.estado_seletor = MODO_NAVEGACAO
        self.turno_atual = TURNO_INIMIGO if self.turno_atual == TURNO_JOGADOR else TURNO_JOGADOR
        print(f"🔄 Turno alterado! Agora é a vez do: {'JOGADOR (Robôs)' if self.turno_atual == TURNO_JOGADOR else 'INIMIGO (Insetos)'}")

    def aplicar_ataque(self, alvo_r, alvo_c):
        """Aplica o dano na unidade alvo e remove-a se o HP chegar a zero."""
        alvo_id = self.tabuleiro.entities[alvo_r][alvo_c]
        dano = DANO_UNIDADE.get(self.peca_selecionada, 1)
        
        hp_atual = self.hp_unidades.get((alvo_r, alvo_c), 3) - dano
        print(f"💥 BUM! Peça {self.peca_selecionada} atacou Peça {alvo_id} causando {dano} de dano!")

        if hp_atual <= 0:
            print(f"💀 A Peça {alvo_id} em [{alvo_r}][{alvo_c}] foi destruída!")
            self.tabuleiro.entities[alvo_r][alvo_c] = 0
            self.hp_unidades.pop((alvo_r, alvo_c), None)
        else:
            self.hp_unidades[(alvo_r, alvo_c)] = hp_atual
            print(f"Peça sobrevivente restou com {hp_atual} de HP.")
            
        self.alternar_turno()