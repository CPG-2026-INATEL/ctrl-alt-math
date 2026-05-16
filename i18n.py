import settings
from lore_data import LORE_STRINGS, LANG_EN, LANG_PT

STRINGS = {
    # Menu
    "menu_start": {LANG_EN: "START GAME", LANG_PT: "INICIAR JOGO"},
    "menu_how_to": {LANG_EN: "HOW TO PLAY", LANG_PT: "COMO JOGAR"},
    "menu_quit": {LANG_EN: "QUIT", LANG_PT: "SAIR"},
    "menu_language": {LANG_EN: "LANGUAGE", LANG_PT: "IDIOMA"},
    "menu_difficulty": {LANG_EN: "DIFFICULTY", LANG_PT: "DIFICULDADE"},
    "difficulty_easy": {LANG_EN: "EASY", LANG_PT: "FÁCIL"},
    "difficulty_medium": {LANG_EN: "MEDIUM", LANG_PT: "MÉDIO"},
    "difficulty_hard": {LANG_EN: "HARD", LANG_PT: "DIFÍCIL"},
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
    "how_to_r": {LANG_EN: "  R - Ctrl+Z rewind (+10 HP, increases Entropy)", LANG_PT: "  R - Desfazer Ctrl+Z (+10 HP, aumenta Entropia)"},
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
    "upgrades_lost": {LANG_EN: "All upgrades lost.", LANG_PT: "Melhorias perdidas."},
    "press_enter_return": {LANG_EN: "Press ENTER to return to map", LANG_PT: "Pressione ENTER para voltar ao mapa"},

    # Victory
    "victory": {LANG_EN: "VICTORY!", LANG_PT: "VITÓRIA!"},
    "defeated_boss": {LANG_EN: "You defeated O Grande Simplificador!", LANG_PT: "Você derrotou O Grande Simplificador!"},
    "complexity_survives": {LANG_EN: "You proved that complexity survives.", LANG_PT: "Você provou que a complexidade sobrevive."},
    "math_never_forgotten": {LANG_EN: "Mathematics will never be forgotten.", LANG_PT: "A matemática nunca será esquecida."},
    "victory_quote": {LANG_EN: "\"The universe cannot be reduced to simple answers.\"", LANG_PT: "\"O universo não pode ser reduzido a respostas simples.\""},
    "press_enter_play_again": {LANG_EN: "Press ENTER to continue, Esc for new game", LANG_PT: "Pressione ENTER para continuar, Esc p/ novo jogo"},

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
    "out_of_reach": {LANG_EN: "OUT OF REACH", LANG_PT: "FORA DE ALCANCE"},
    "out_of_range": {LANG_EN: "OUT OF RANGE", LANG_PT: "FORA DE ALCANCE"},
    "not_enough_rigor": {LANG_EN: "NOT ENOUGH RIGOR", LANG_PT: "RIGOR INSUFICIENTE"},
    "rewind_locked": {LANG_EN: "REWIND LOCKED", LANG_PT: "REBOBINAR BLOQUEADO"},
    "no_rewind_available": {LANG_EN: "NO REWIND AVAILABLE", LANG_PT: "SEM REBOBINAR DISPONIVEL"},
    "wait": {LANG_EN: "Wait", LANG_PT: "Aguardar"},

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
        LANG_EN: "Predict enemy movement.\n+5% Dmg per tile moved\nthis turn. df/dx.",
        LANG_PT: "Preveja o movimento.\n+5% Dano por bloco movido\nneste turno. df/dx."
    },
    "skill_pitagoras_name": {LANG_EN: "Pitágoras", LANG_PT: "Pitágoras"},
    "skill_pitagoras_desc": {
        LANG_EN: "Geometric attack (r<=3).\nd = sqrt(dx^2+dy^2)\nDeals 25 damage.",
        LANG_PT: "Ataque geométrico (r<=3).\nd = sqrt(dx^2+dy^2)\nCausa 25 de dano."
    },
    "skill_ctrlz_name": {LANG_EN: "Ctrl+Z", LANG_PT: "Ctrl+Z"},
    "skill_ctrlz_desc": {
        LANG_EN: "Rewind to the previous turn.\nRestore +10 HP on rewind.\nPress R.",
        LANG_PT: "Volte ao turno anterior.\nRecupere +10 HP ao rebobinar.\nPressione R."
    },
    "skill_bayes_name": {LANG_EN: "Bayes", LANG_PT: "Bayes"},
    "skill_bayes_desc": {
        LANG_EN: "Improved prediction.\nP(A|B) = P(B|A)\n* P(A) / P(B)",
        LANG_PT: "Previsão aprimorada.\nP(A|B) = P(B|A)\n* P(A) / P(B)"
    },
    "skill_reflexao_name": {LANG_EN: "Reflexão", LANG_PT: "Reflexão"},
    "skill_reflexao_desc": {
        LANG_EN: "High-energy pulse (r<=2).\nArea damage skill.\nDeals 15 damage.",
        LANG_PT: "Pulso de alta energia (r<=2).\nHabilidade de dano em área.\nCausa 15 de dano."
    },
    "skill_entropia_name": {LANG_EN: "Entropia Controlada", LANG_PT: "Entropia Controlada"},
    "skill_entropia_desc": {
        LANG_EN: "Halve rewind entropy gain.\ndS -> dS/2\nMakes time theft safer.",
        LANG_PT: "Reduz pela metade a entropia do rewind.\ndS -> dS/2\nTorna o rewind mais seguro."
    },
    "skill_teoria_jogos_name": {LANG_EN: "Teoria dos Jogos", LANG_PT: "Teoria dos Jogos"},
    "skill_teoria_jogos_desc": {
        LANG_EN: "Reveal enemy targets.\nNash equilibrium:\nno regrets strategy.",
        LANG_PT: "Revele os alvos inimigos.\nEquilíbrio de Nash:\nestratégia sem arrependimento."
    },

    # Skill Flavor Lore
    "skill_axioma_flavor": {LANG_EN: "The first thing they tried to erase was the equal sign.", LANG_PT: "A primeira coisa que tentaram apagar foi o sinal de igual."},
    "skill_derivada_flavor": {LANG_EN: "Change is the only constant the Regime fears.", LANG_PT: "A mudança é a única constante que o Regime teme."},
    "skill_pitagoras_flavor": {LANG_EN: "Triangles: the sharpest weapons in the archive.", LANG_PT: "Triângulos: as armas mais afiadas do arquivo."},
    "skill_ctrlz_flavor": {LANG_EN: "Time is just another variable we can manipulate.", LANG_PT: "O tempo é apenas mais uma variável que podemos manipular."},
    "skill_bayes_flavor": {LANG_EN: "Uncertainty is where rebellion grows.", LANG_PT: "A incerteza é onde a rebelião cresce."},
    "skill_reflexao_flavor": {LANG_EN: "Your own hatred will be your downfall.", LANG_PT: "Seu próprio ódio será sua ruína."},
    "skill_entropia_flavor": {LANG_EN: "Order is a fragile illusion.", LANG_PT: "A ordem é uma ilusão frágil."},
    "skill_teoria_jogos_flavor": {LANG_EN: "We are playing a game they already lost.", LANG_PT: "Estamos jogando um jogo que eles já perderam."},

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
    "room_lab_name": {LANG_EN: "Chaos Lab", LANG_PT: "Laboratório do Caos"},
    "room_lab_narr": {LANG_EN: "Small changes have massive consequences.", LANG_PT: "Pequenas mudanças têm consequências massivas."},
    
    # Intent Tooltips
    "tip_attack_area": {LANG_EN: "ATTACK AREA", LANG_PT: "ÁREA DE ATAQUE"},
    "tip_attack_desc": {LANG_EN: "Enemy will hit this tile next turn.", LANG_PT: "Inimigo atingirá este bloco no próximo turno."},
    "tip_move_vector": {LANG_EN: "MOVEMENT VECTOR", LANG_PT: "VETOR DE MOVIMENTO"},
    "tip_move_desc": {LANG_EN: "Enemy plans to relocate to this position.", LANG_PT: "Inimigo planeja se realocar para esta posição."},
    "tip_decoy_area": {LANG_EN: "DECOY INDICATOR", LANG_PT: "INDICADOR DE DECOY"},
    "tip_decoy_desc": {LANG_EN: "A false threat created to confuse you.", LANG_PT: "Uma ameaça falsa criada para te confundir."},
    "tip_player_move": {LANG_EN: "REACHABLE AREA", LANG_PT: "ÁREA ALCANÇÁVEL"},
    "tip_player_move_desc": {LANG_EN: "Tiles you can move to this turn.", LANG_PT: "Blocos para os quais você pode se mover este turno."},
    "tip_player_attack": {LANG_EN: "TARGET AREA", LANG_PT: "ÁREA DE ALVO"},
    "tip_player_attack_desc": {LANG_EN: "Tiles currently within your strike range.", LANG_PT: "Blocos atualmente dentro do seu alcance de ataque."},

    # Lobby / Multiplayer
    "lobby_title": {LANG_EN: "LAN MULTIPLAYER", LANG_PT: "MULTIPLAYER LAN"},
    "lobby_host": {LANG_EN: "Host Game", LANG_PT: "Hospedar Jogo"},
    "lobby_join": {LANG_EN: "Join Game", LANG_PT: "Entrar no Jogo"},
    "lobby_back": {LANG_EN: "Back", LANG_PT: "Voltar"},
    "lobby_hosting": {LANG_EN: "Hosting Game...", LANG_PT: "Hospedando Jogo..."},
    "lobby_waiting": {LANG_EN: "Waiting for player... IP: {ip}", LANG_PT: "Aguardando jogador... IP: {ip}"},
    "lobby_player_joined": {LANG_EN: "Player 2 connected!", LANG_PT: "Jogador 2 conectado!"},
    "lobby_start_prompt": {LANG_EN: "Press ENTER to start game", LANG_PT: "Pressione ENTER para comecar"},
    "lobby_esc_cancel": {LANG_EN: "ESC to cancel", LANG_PT: "ESC para cancelar"},
    "lobby_choose_help": {LANG_EN: "Host on one PC, join from another on the same LAN.", LANG_PT: "Hospede em um PC e entre de outro na mesma rede."},
    "lobby_share_ip": {LANG_EN: "Share this IP with the second player.", LANG_PT: "Compartilhe este IP com o segundo jogador."},
    "lobby_joining": {LANG_EN: "Join Game", LANG_PT: "Entrar no Jogo"},
    "lobby_enter_ip": {LANG_EN: "Enter host IP address:", LANG_PT: "Digite o IP do host:"},
    "lobby_scan_hint": {LANG_EN: "Ctrl+S to scan LAN", LANG_PT: "Ctrl+S para escanear LAN"},
    "lobby_join_help": {LANG_EN: "You can type an IP or scan/click a discovered host.", LANG_PT: "Voce pode digitar um IP ou escanear/clicar em um host encontrado."},
    "lobby_scanning": {LANG_EN: "Scanning LAN...", LANG_PT: "Escaneando LAN..."},
    "lobby_found": {LANG_EN: "Found {n} host(s)", LANG_PT: "{n} host(s) encontrado(s)"},
    "lobby_no_hosts": {LANG_EN: "No hosts found", LANG_PT: "Nenhum host encontrado"},
    "lobby_select_host": {LANG_EN: "Select a host:", LANG_PT: "Selecione um host:"},
    "lobby_connected": {LANG_EN: "Connected!", LANG_PT: "Conectado!"},
    "lobby_press_start": {LANG_EN: "Press ENTER to ready up", LANG_PT: "Pressione ENTER para pronto"},
    "lobby_connected_help": {LANG_EN: "Both players are in. Click or press ENTER to continue.", LANG_PT: "Os dois jogadores entraram. Clique ou pressione ENTER para continuar."},
    "lobby_waiting_host": {LANG_EN: "Waiting for host to start...", LANG_PT: "Aguardando o host iniciar..."},
    "mp_vote_hint": {LANG_EN: "Stand on a room and press ENTER to vote — both players must agree", LANG_PT: "Vá a uma sala e pressione ENTER para votar — ambos devem concordar"},
    "mp_waiting_partner": {LANG_EN: "Waiting for partner to confirm this room...", LANG_PT: "Aguardando parceiro confirmar esta sala..."},
    "mp_vote_mismatch": {LANG_EN: "Partner wants: {room} — navigate to agree!", LANG_PT: "Parceiro quer: {room} — navegue para concordar!"},
    "mp_vote_entering": {LANG_EN: "Both agreed! Entering room...", LANG_PT: "Ambos concordaram! Entrando na sala..."},
    "menu_multiplayer": {LANG_EN: "LAN Co-op", LANG_PT: "Co-op LAN"},
    "menu_achievements": {LANG_EN: "Achievements", LANG_PT: "Conquistas"},
    "achievements_title": {LANG_EN: "ACHIEVEMENTS", LANG_PT: "CONQUISTAS"},

    # Achievements
    "ach_first_room_name": {LANG_EN: "The First Proof", LANG_PT: "A Primeira Prova"},
    "ach_first_room_desc": {LANG_EN: "Complete your first room.", LANG_PT: "Complete sua primeira sala."},
    "ach_no_damage_name": {LANG_EN: "Untouchable", LANG_PT: "Intocável"},
    "ach_no_damage_desc": {LANG_EN: "Complete a room without taking damage.", LANG_PT: "Complete uma sala sem sofrer dano."},
    "ach_fast_win_name": {LANG_EN: "Efficient Thinker", LANG_PT: "Pensador Eficiente"},
    "ach_fast_win_desc": {LANG_EN: "Complete a room in less than 10 turns.", LANG_PT: "Complete uma sala em menos de 10 turnos."},
    "ach_skill_master_name": {LANG_EN: "Forbidden Knowledge", LANG_PT: "Conhecimento Proibido"},
    "ach_skill_master_desc": {LANG_EN: "Unlock 5 or more skills.", LANG_PT: "Desbloqueie 5 ou mais habilidades."},
    "ach_crit_thinking_name": {LANG_EN: "Critical Thinking", LANG_PT: "Pensamento Crítico"},
    "ach_crit_thinking_desc": {LANG_EN: "Land 3 critical hits in a single room.", LANG_PT: "Acerte 3 golpes críticos em uma única sala."},
    "ach_math_god_name": {LANG_EN: "Q.E.D.", LANG_PT: "Q.E.D."},
    "ach_math_god_desc": {LANG_EN: "Reach the ultimate conclusion of the proof.", LANG_PT: "Alcance a conclusão definitiva da prova."},
    "ach_stars_1": {LANG_EN: "Easy", LANG_PT: "Fácil"},
    "ach_stars_2": {LANG_EN: "Medium", LANG_PT: "Médio"},
    "ach_stars_3": {LANG_EN: "Hard", LANG_PT: "Difícil"},
    "ach_locked": {LANG_EN: "Locked", LANG_PT: "Bloqueado"},
    "achievement_unlocked_toast": {LANG_EN: "Achievement Unlocked!", LANG_PT: "Conquista Desbloqueada!"},
    "lore_toast_title": {LANG_EN: "BERNOULLI LOG", LANG_PT: "REGISTRO BERNOULLI"},
    "ach_reset_hint": {LANG_EN: "Press R to Reset All Achievements", LANG_PT: "Pressione R para Reiniciar Conquistas"},
    "map_title": {LANG_EN: "WORLD ARCHIVE", LANG_PT: "ARQUIVO MUNDIAL"},
}

# Merge Lore Strings
STRINGS.update(LORE_STRINGS)

def t(key, **kwargs):
    lang = getattr(settings, "LANGUAGE", LANG_EN)
    text = STRINGS.get(key, {}).get(lang, key)
    if kwargs:
        return text.format(**kwargs)
    return text
