import settings
from lore_data import LORE_STRINGS, LANG_EN, LANG_PT

STRINGS = {
    # Menu
    "menu_start": {LANG_EN: "START GAME", LANG_PT: "INICIAR JOGO"},
    "menu_how_to": {LANG_EN: "HOW TO PLAY", LANG_PT: "COMO JOGAR"},
    "menu_quit": {LANG_EN: "QUIT", LANG_PT: "SAIR"},
    "menu_language": {LANG_EN: "LANGUAGE", LANG_PT: "IDIOMA"},
    "menu_nav": {LANG_EN: "Use UP/DOWN to navigate, ENTER to select", LANG_PT: "Use CIMA/BAIXO para navegar, ENTER para selecionar"},
    "game_title": {LANG_EN: "Ctrl + Alt + Math", LANG_PT: "Ctrl + Alt + Math"},
    "game_subtitle": {LANG_EN: "A Mathematical Rebellion", LANG_PT: "Uma Rebelião Matemática"},
    "intro_1": {LANG_EN: "In a world where math is forbidden,", LANG_PT: "Em um mundo onde a matemática é proibida,"},
    "intro_2": {LANG_EN: "you are the last mathematician.", LANG_PT: "você é o último matemático."},
    "intro_3": {LANG_EN: "Fight the regime with forbidden theorems.", LANG_PT: "Lute contra o regime com teoremas proibidos."},

    # HUD
    "hp": {LANG_EN: "HP", LANG_PT: "PV"},
    "rigor": {LANG_EN: "Rigor", LANG_PT: "Rigor"},
    "entropy": {LANG_EN: "Entropy", LANG_PT: "Entropia"},
    "wave": {LANG_EN: "Wave", LANG_PT: "Onda"},
    "skill_points": {LANG_EN: "Skill Points", LANG_PT: "Pontos de Habilidade"},
    "controls_move": {LANG_EN: "WASD: Move", LANG_PT: "WASD: Mover"},
    "controls_atk": {LANG_EN: "Space: Atk", LANG_PT: "Espaço: Atk"},
    "controls_pitagoras": {LANG_EN: "1: Pitagoras", LANG_PT: "1: Pitágoras"},
    "controls_reflexao": {LANG_EN: "2: Reflexao", LANG_PT: "2: Reflexão"},
    "controls_rewind": {LANG_EN: "R: Rewind", LANG_PT: "R: Desfazer"},
    "controls_skills": {LANG_EN: "Tab: Skills", LANG_PT: "Tab: Habilidades"},
    "controls_pause": {LANG_EN: "Esc: Pause", LANG_PT: "Esc: Pausa"},
    "controls_quit_menu": {LANG_EN: "Q: Quit Menu", LANG_PT: "Q: Sair p/ Menu"},

    # How to Play
    "how_to_title": {LANG_EN: "HOW TO PLAY", LANG_PT: "COMO JOGAR"},
    "how_to_intro": {LANG_EN: "You are a mathematician fighting the regime.", LANG_PT: "Você é um matemático lutando contra o regime."},
    "how_to_move": {LANG_EN: "Use WASD or Arrow Keys to move around the arena.", LANG_PT: "Use WASD ou Setas para se mover na arena."},
    "how_to_combat": {LANG_EN: "COMBAT:", LANG_PT: "COMBATE:"},
    "how_to_space": {LANG_EN: "  Space - Basic attack (melee range)", LANG_PT: "  Espaço - Ataque básico (curto alcance)"},
    "how_to_1": {LANG_EN: "  1 - Pitagoras theorem attack (if unlocked)", LANG_PT: "  1 - Ataque do teorema de Pitágoras (se desbloqueado)"},
    "how_to_2": {LANG_EN: "  2 - Reflexao defensive burst (if unlocked)", LANG_PT: "  2 - Explosão defensiva de Reflexão (se desbloqueado)"},
    "how_to_r": {LANG_EN: "  R - Ctrl+Z rewind (if unlocked, increases Entropy)", LANG_PT: "  R - Desfazer Ctrl+Z (se desbloqueado, aumenta Entropia)"},
    "how_to_skills": {LANG_EN: "SKILL TREE:", LANG_PT: "ÁRVORE DE HABILIDADES:"},
    "how_to_tab": {LANG_EN: "  Press Tab to open the skill tree.", LANG_PT: "  Pressione Tab para abrir a árvore de habilidades."},
    "how_to_spend": {LANG_EN: "  Spend skill points to unlock theorem abilities.", LANG_PT: "  Gaste pontos de habilidade para desbloquear teoremas."},
    "how_to_prereq": {LANG_EN: "  Each skill has prerequisites that must be unlocked first.", LANG_PT: "  Cada habilidade tem pré-requisitos necessários."},
    "how_to_enemies": {LANG_EN: "ENEMIES:", LANG_PT: "INIMIGOS:"},
    "how_to_censor": {LANG_EN: "  Censor Linear - Moves directly toward you", LANG_PT: "  Censor Linear - Move-se diretamente para você"},
    "how_to_strawman": {LANG_EN: "  Falacia Espantalho - Erratic, creates decoys", LANG_PT: "  Falácia Espantalho - Errático, cria iscas"},
    "how_to_bayesian": {LANG_EN: "  Inquisidor Bayesiano - Predicts your movement", LANG_PT: "  Inquisidor Bayesiano - Prevê seu movimento"},
    "how_to_boss": {LANG_EN: "  O Grande Simplificador - The final boss", LANG_PT: "  O Grande Simplificador - O chefe final"},
    "how_to_win": {LANG_EN: "Survive all waves and defeat the boss to win!", LANG_PT: "Sobreviva a todas as ondas e vença o chefe para ganhar!"},
    "how_to_return": {LANG_EN: "Press Esc to return", LANG_PT: "Pressione Esc para retornar"},

    # Pause
    "paused": {LANG_EN: "PAUSED", LANG_PT: "PAUSADO"},
    "press_esc_resume": {LANG_EN: "Press Esc to resume", LANG_PT: "Pressione Esc para continuar"},
    "press_q_quit": {LANG_EN: "Press Q to quit to main menu", LANG_PT: "Pressione Q para sair para o menu principal"},
    "press_q_quit_short": {LANG_EN: "Press Q to quit to menu", LANG_PT: "Pressione Q para sair para o menu"},

    # Game Over
    "game_over": {LANG_EN: "GAME OVER", LANG_PT: "FIM DE JOGO"},
    "fell_at": {LANG_EN: "You fell at: {room}", LANG_PT: "Você caiu em: {room}"},
    "fell_battle": {LANG_EN: "You fell in battle", LANG_PT: "Você caiu em batalha"},
    "regime_silenced": {LANG_EN: "The regime has silenced another mind.", LANG_PT: "O regime silenciou outra mente."},
    "upgrades_lost": {LANG_EN: "All upgrades lost. Progress saved.", LANG_PT: "Melhorias perdidas. Progresso salvo."},
    "press_enter_return": {LANG_EN: "Press ENTER to return to map", LANG_PT: "Pressione ENTER para voltar ao mapa"},

    # Victory
    "victory": {LANG_EN: "VICTORY!", LANG_PT: "VITÓRIA!"},
    "defeated_boss": {LANG_EN: "You defeated O Grande Simplificador!", LANG_PT: "Você derrotou O Grande Simplificador!"},
    "complexity_survives": {LANG_EN: "You proved that complexity survives.", LANG_PT: "Você provou que a complexidade sobrevive."},
    "math_never_forgotten": {LANG_EN: "Mathematics will never be forgotten.", LANG_PT: "A matemática nunca será esquecida."},
    "victory_quote": {LANG_EN: "\"The universe cannot be reduced to simple answers.\"", LANG_PT: "\"O universo não pode ser reduzido a respostas simples.\""},
    "press_enter_play_again": {LANG_EN: "Press ENTER to play again, Esc to quit to menu", LANG_PT: "Pressione ENTER para jogar novamente, Esc p/ sair"},

    # Waves
    "wave_count": {LANG_EN: "Wave {wave}", LANG_PT: "Onda {wave}"},
    "press_key_begin": {LANG_EN: "Press any key to begin", LANG_PT: "Pressione qualquer tecla para começar"},
    "wave_complete": {LANG_EN: "WAVE COMPLETE", LANG_PT: "ONDA CONCLUÍDA"},
    "earned_skill_point": {LANG_EN: "You earned 1 Skill Point!", LANG_PT: "Você ganhou 1 Ponto de Habilidade!"},
    "press_tab_skills": {LANG_EN: "Press Tab to open Skill Tree", LANG_PT: "Pressione Tab p/ Árvore de Habilidades"},
    "press_key_continue": {LANG_EN: "Press any key to continue", LANG_PT: "Pressione qualquer tecla para continuar"},

    # Skill Tree
    "skill_tree_title": {LANG_EN: "SKILL TREE", LANG_PT: "ÁRVORE DE HABILIDADES"},
    "cost_free": {LANG_EN: "Free", LANG_PT: "Grátis"},
    "cost_label": {LANG_EN: "Cost: {cost}", LANG_PT: "Custo: {cost}"},
    "skill_unlocked_ok": {LANG_EN: "OK", LANG_PT: "OK"},
    "skill_tree_footer": {LANG_EN: "Click to unlock | Tab / Esc to close", LANG_PT: "Clique p/ desbloquear | Tab / Esc p/ fechar"},

    # Feedback / Floating Text
    "qed": {LANG_EN: "QED", LANG_PT: "QED"},
    "qed_full": {LANG_EN: "Quod Erat Demonstrandum", LANG_PT: "Quod Erat Demonstrandum"},
    "qed_translated": {LANG_EN: "\"What was to be demonstrated\"", LANG_PT: "\"Como se queria demonstrar\""},
    "eliminated": {LANG_EN: "exists=0 (eliminated)", LANG_PT: "existe=0 (eliminado)"},
    "map_title": {LANG_EN: "THE FORBIDDEN ARCHIVE", LANG_PT: "O ARQUIVO PROIBIDO"},
    "press_enter_room": {LANG_EN: "Press ENTER to enter", LANG_PT: "Pressione ENTER para entrar"},
    "room_completed_replay": {LANG_EN: "Completed - ENTER to replay", LANG_PT: "Concluído - ENTER p/ jogar de novo"},
    "unknown": {LANG_EN: "???", LANG_PT: "???"},
    "map_footer": {LANG_EN: "WASD: Navigate | ENTER: Enter | ESC: Menu", LANG_PT: "WASD: Navegar | ENTER: Entrar | ESC: Menu"},
    "class_label": {LANG_EN: "Class: {name}", LANG_PT: "Classe: {name}"},
    "theme_label": {LANG_EN: "Theme: {name}", LANG_PT: "Tema: {name}"},
    "miss": {LANG_EN: "Miss", LANG_PT: "Errou"},
    "crit": {LANG_EN: "CRIT!", LANG_PT: "CRÍT!"},
    "blocked": {LANG_EN: "BLOCKED", LANG_PT: "BLOQUEADO"},
    "no_hit": {LANG_EN: "NO HIT", LANG_PT: "NÃO ACERTOU"},

    # Enemies
    "enemy_censor": {LANG_EN: "Censor Linear", LANG_PT: "Censor Linear"},
    "enemy_strawman": {LANG_EN: "Falacia Espantalho", LANG_PT: "Falácia Espantalho"},
    "enemy_bayesian": {LANG_EN: "Inquisidor Bayesiano", LANG_PT: "Inquisidor Bayesiano"},
    "enemy_boss": {LANG_EN: "O Grande Simplificador", LANG_PT: "O Grande Simplificador"},
    "enemy_unknown": {LANG_EN: "Unknown Entity", LANG_PT: "Entidade Desconhecida"},
    "lore_unknown": {LANG_EN: "A mysterious figure lurking in the mathematical shadows.", LANG_PT: "Uma figura misteriosa espreitando nas sombras matemáticas."},

    "lore_censor": {
        LANG_EN: "A relentless enforcer of mathematical purity. It seeks to eliminate any equation that doesn't fit the regime's narrow logic.",
        LANG_PT: "Um executor implacável da pureza matemática. Busca eliminar qualquer equação que não se encaixe na lógica estreita do regime."
    },
    "lore_strawman": {
        LANG_EN: "Distorts reality by creating false targets. It avoids direct confrontation by manipulating the observer's perception.",
        LANG_PT: "Distorce a realidade criando alvos falsos. Evita o confronto direto manipulando a percepção do observador."
    },
    "lore_bayesian": {
        LANG_EN: "Calculates every possibility. It doesn't just attack where you are, but where you are most likely to be.",
        LANG_PT: "Calcula todas as possibilidades. Não ataca apenas onde você está, mas onde é mais provável que você esteja."
    },
    "lore_boss": {
        LANG_EN: "The ultimate authority of the regime. It reduces the infinite complexity of the universe into a single, suffocating truth.",
        LANG_PT: "A autoridade máxima do regime. Reduz a complexidade infinita do universo em uma verdade única e sufocante."
    },

    # Skills
    "skill_axioma_name": {LANG_EN: "Axioma Básico", LANG_PT: "Axioma Básico"},
    "skill_axioma_desc": {
        LANG_EN: "The foundation of all\nmathematical thought.\nforall x: f(x) = f(x)",
        LANG_PT: "A base de todo\npensamento matemático.\npara todo x: f(x) = f(x)"
    },
    "skill_derivada_name": {LANG_EN: "Derivada", LANG_PT: "Derivada"},
    "skill_derivada_desc": {
        LANG_EN: "Predict enemy movement.\ndf/dx shows the\ndirection of change.",
        LANG_PT: "Preveja o movimento inimigo.\ndf/dx mostra a\ndireção da mudança."
    },
    "skill_pitagoras_name": {LANG_EN: "Pitágoras", LANG_PT: "Pitágoras"},
    "skill_pitagoras_desc": {
        LANG_EN: "Geometric attack (r<=3).\nd = sqrt(dx^2+dy^2)\nDeals 25 damage.",
        LANG_PT: "Ataque geométrico (r<=3).\nd = sqrt(dx^2+dy^2)\nCausa 25 de dano."
    },
    "skill_ctrlz_name": {LANG_EN: "Ctrl+Z", LANG_PT: "Ctrl+Z"},
    "skill_ctrlz_desc": {
        LANG_EN: "Rewind 2 turns back.\nR^-1: undo(R) -> R^-2\nPress R to undo.",
        LANG_PT: "Volte 2 turnos atrás.\nR^-1: desfazer(R) -> R^-2\nPressione R p/ desfazer."
    },
    "skill_bayes_name": {LANG_EN: "Bayes", LANG_PT: "Bayes"},
    "skill_bayes_desc": {
        LANG_EN: "Improved prediction.\nP(A|B) = P(B|A)\n* P(A) / P(B)",
        LANG_PT: "Previsão aprimorada.\nP(A|B) = P(B|A)\n* P(A) / P(B)"
    },
    "skill_reflexao_name": {LANG_EN: "Reflexão", LANG_PT: "Reflexão"},
    "skill_reflexao_desc": {
        LANG_EN: "Barrier cells block enemies.\ntheta_i=theta_r: reflection\nsymmetry. Press 2.",
        LANG_PT: "Células barreira bloqueiam.\ntheta_i=theta_r: simetria\nde reflexão. Pressione 2."
    },
    "skill_entropia_name": {LANG_EN: "Entropia Controlada", LANG_PT: "Entropia Controlada"},
    "skill_entropia_desc": {
        LANG_EN: "Reduce entropy gain\nfrom rewinding.\ndS -> 0",
        LANG_PT: "Reduza o ganho de entropia\nao desfazer turnos.\ndS -> 0"
    },
    "skill_teoria_jogos_name": {LANG_EN: "Teoria dos Jogos", LANG_PT: "Teoria dos Jogos"},
    "skill_teoria_jogos_desc": {
        LANG_EN: "Reveal enemy targets.\nNash equilibrium:\nno regrets strategy.",
        LANG_PT: "Revele os alvos inimigos.\nEquilíbrio de Nash:\nestratégia sem arrependimento."
    },

    # Waves Narrative
    "wave_1_narr": {LANG_EN: "Mathematics is forbidden.\nBut reality still obeys it.", LANG_PT: "A matemática é proibida.\nMas a realidade ainda a obedece."},
    "wave_1_post": {LANG_EN: "You recover a lost axiom\nfrom a censored archive.", LANG_PT: "Você recupera um axioma perdido\nde um arquivo censurado."},
    "wave_2_narr": {LANG_EN: "The regime sends more censors.\nThey cannot erase what is proven.", LANG_PT: "O regime envia mais censores.\nEles não podem apagar o que foi provado."},
    "wave_2_post": {LANG_EN: "Derivatives and integrals\nwhisper in the static.", LANG_PT: "Derivadas e integrais\nsussurram na estática."},
    "wave_3_narr": {LANG_EN: "Rhetorical tricksters enter the field.\nThey distort your theorems.", LANG_PT: "Trapaceiros retóricos entram em campo.\nEles distorcem seus teoremas."},
    "wave_3_post": {LANG_EN: "You see through their\nlogical fallacies.", LANG_PT: "Você enxerga através de suas\nfalácias lógicas."},
    "wave_4_narr": {LANG_EN: "An Inquisidor Bayesiano joins.\nIt calculates your every move.", LANG_PT: "Um Inquisidor Bayesiano se junta.\nEle calcula cada movimento seu."},
    "wave_4_post": {LANG_EN: "Probability bends to your will.\nThe end approaches.", LANG_PT: "A probabilidade se curva à sua vontade.\nO fim se aproxima."},
    "wave_5_narr": {LANG_EN: "O Grande Simplificador approaches.\nIt wants to reduce all thought\nto one dimension.", LANG_PT: "O Grande Simplificador se aproxima.\nEle quer reduzir todo o pensamento\na uma dimensão."},

    # Map Rooms
    "room_archive_name": {LANG_EN: "The Archive", LANG_PT: "O Arquivo"},
    "room_archive_narr": {LANG_EN: "A safe haven where forbidden knowledge persists.", LANG_PT: "Um refúgio seguro onde o conhecimento proibido persiste."},
    "room_library_name": {LANG_EN: "Censored Library", LANG_PT: "Biblioteca Censurada"},
    "room_library_narr": {LANG_EN: "Books burn themselves as you enter.", LANG_PT: "Livros se queimam sozinhos ao entrar."},
    "room_logic_name": {LANG_EN: "Logic Chamber", LANG_PT: "Câmara da Lógica"},
    "room_logic_narr": {LANG_EN: "Every argument here must be proven.", LANG_PT: "Todo argumento aqui deve ser provado."},
    "room_gallery_name": {LANG_EN: "Proof Gallery", LANG_PT: "Galeria de Provas"},
    "room_gallery_narr": {LANG_EN: "Theorems hang on walls like paintings.", LANG_PT: "Teoremas pendem nas paredes como quadros."},
    "room_hall_name": {LANG_EN: "Derivative Hall", LANG_PT: "Salão da Derivada"},
    "room_hall_narr": {LANG_EN: "Rates of change echo through corridors.", LANG_PT: "Taxas de mudança ecoam pelos corredores."},
    "room_maze_name": {LANG_EN: "Fallacy Maze", LANG_PT: "Labirinto da Falácia"},
    "room_maze_narr": {LANG_EN: "Every path leads to a logical trap.", LANG_PT: "Cada caminho leva a uma armadilha lógica."},
    "room_tower_name": {LANG_EN: "Induction Tower", LANG_PT: "Torre da Indução"},
    "room_tower_narr": {LANG_EN: "Prove the base case to ascend.", LANG_PT: "Prove o caso base para ascender."},
    "room_dungeon_name": {LANG_EN: "Probability Dungeon", LANG_PT: "Masmorra da Probabilidade"},
    "room_dungeon_narr": {LANG_EN: "Bayesian inference is your only light.", LANG_PT: "A inferência Bayesiana é sua única luz."},
    "room_boss_censor_name": {LANG_EN: "The Censor General", LANG_PT: "O Censor Geral"},
    "room_boss_censor_narr": {LANG_EN: "The head of all censorship awaits.", LANG_PT: "O chefe de toda a censura aguarda."},
    "room_boss_engine_name": {LANG_EN: "The Reduction Engine", LANG_PT: "O Motor de Redução"},
    "room_boss_engine_narr": {LANG_EN: "It reduces complexity to nothing.", LANG_PT: "Ele reduz a complexidade a nada."},
    "room_boss_final_name": {LANG_EN: "O Grande Simplificador", LANG_PT: "O Grande Simplificador"},
    "room_boss_final_narr": {LANG_EN: "The final boss. It wants one-dimensional thought.", LANG_PT: "O chefe final. Ele quer o pensamento unidimensional."},
    "room_victory_name": {LANG_EN: "The Unbound Theorem", LANG_PT: "O Teorema Liberto"},
    "room_victory_narr": {LANG_EN: "Mathematics cannot be contained.", LANG_PT: "A matemática não pode ser contida."},
    "room_sanctuary_name": {LANG_EN: "Integral Sanctuary", LANG_PT: "Santuário Integral"},
    "room_sanctuary_narr": {LANG_EN: "Accumulated knowledge flows here.", LANG_PT: "Conhecimento acumulado flui aqui."},
    "room_vault_name": {LANG_EN: "Matrix Vault", LANG_PT: "Cofre de Matrizes"},
    "room_vault_narr": {LANG_EN: "Linear transformations guard this room.", LANG_PT: "Transformações lineares guardam esta sala."},
    "room_lab_name": {LANG_EN: "Chaos Theory Lab", LANG_PT: "Laboratório de Teoria do Caos"},
    "room_lab_narr": {LANG_EN: "Small changes have massive consequences.", LANG_PT: "Pequenas mudanças têm consequências massivas."},
}

# Merge Lore Strings
STRINGS.update(LORE_STRINGS)

def t(key, **kwargs):
    lang = getattr(settings, "LANGUAGE", LANG_EN)
    text = STRINGS.get(key, {}).get(lang, key)
    if kwargs:
        return text.format(**kwargs)
    return text
