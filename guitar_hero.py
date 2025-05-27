import pygame
import random
import time
import math
import os

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Cores para as notas musicais
COLORS = {
    1: (255, 0, 0),    # Vermelho
    2: (0, 255, 0),    # Verde
    3: (0, 0, 255),    # Azul
    4: (255, 255, 0)   # Amarelo
}

# Teclas para pressionar
KEYS = {
    1: pygame.K_1,
    2: pygame.K_2,
    3: pygame.K_3,
    4: pygame.K_4
}

# Teclas para mudar dificuldade
DIFFICULTY_KEYS = {
    pygame.K_7: 0,  # Fácil
    pygame.K_8: 1,  # Médio
    pygame.K_9: 2,  # Difícil
    pygame.K_0: 3   # Muito Difícil
}

# Configurações de dificuldade
DIFFICULTY_SETTINGS = {
    # [velocidade, intervalo_spawn, notas_simultaneas, acertos_necessários, max_erros, chance_sequencia, max_notas_sequencia]
    0: [4, 1.3, 1, 10, 10, 0.1, 2],    # Fácil 
    1: [5, 1.1, 2, 15, 8, 0.2, 2],   # Médio 
    2: [6, 0.9, 3, 25, 7, 0.3, 3],   # Difícil 
    3: [6, 0.9, 3, 35, 8, 0.3, 3]    # Muito Difícil 
}

#    # [velocidade, intervalo_spawn, notas_simultaneas, acertos_necessários, max_erros, chance_sequencia, max_notas_sequencia]
 #   0: [4, 1.3, 1, 15, 10, 0.1, 2],    # Fácil 
 #   1: [5, 1.1, 2, 25, 8, 0.2, 2],   # Médio 
 #   2: [6, 0.9, 3, 35, 7, 0.3, 3],   # Difícil 
 #   3: [6, 0.9, 3, 35, 8, 0.3, 3]    # Muito Difícil 

# Nomes das dificuldades
DIFFICULTY_NAMES = {
    0: "Fácil",
    1: "Médio",
    2: "Difícil",
    3: "Muito Difícil"
}

class Note:
    def __init__(self, lane, speed=5):
        self.lane = lane  # 1, 2, 3, ou 4
        self.x = SCREEN_WIDTH  # Posição horizontal (começa na direita)
        self.speed = speed
        self.width = 0  # Será definido dinamicamente
        self.height = 0  # Será definido dinamicamente
        self.active = True
        self.color = COLORS[lane]
        self.glow_alpha = 0
        self.is_part_of_sequence = False  # Indica se é parte de uma sequência rápida
        self.sequence_id = 0  # ID da sequência a que pertence (para identificação visual)
        # Rotação para notas musicais
        self.rotation = 0
        self.note_type = random.randint(1, 2)  # 1 = nota normal, 2 = colcheia
    
    def update(self, note_width, note_height):
        self.x -= self.speed
        self.width = note_width
        self.height = note_height
        
        # Efeito de brilho ao entrar na zona de acerto
        if self.x < 160:
            self.glow_alpha = min(180, self.glow_alpha + 12)
        else:
            self.glow_alpha = max(0, self.glow_alpha - 8)
        
        # Verifica se a nota saiu da tela
        if self.x < -50:
            self.active = False
            
        # Rotação para notas musicais
        self.rotation = (self.rotation + 1) % 360
    
    def draw(self, surface, y, hit_zone_x, hit_zone_width, use_musical_notes=False):
        if not self.active:
            return
        
        if use_musical_notes:
            self._draw_musical_note(surface, y)
        else:
            self._draw_regular_note(surface, y, hit_zone_x, hit_zone_width)
    
    def _draw_musical_note(self, surface, y):
        # Desenhar uma nota musical realista
        center_x = self.x + self.width // 2
        center_y = y
        
        # Tamanho muito reduzido para as notas musicais
        note_size = max(self.width, self.height) * 0.5  # 50% do tamanho original
        
        # Criar superfície temporária para desenhar a nota musical com rotação
        note_surface = pygame.Surface((int(note_size*1.5), int(note_size*2)), pygame.SRCALPHA)
        
        # Cabeça da nota (elipse preenchida)
        head_width = note_size * 0.7
        head_height = note_size * 0.5
        head_rect = pygame.Rect(0, 0, head_width, head_height)
        head_rect.center = (note_surface.get_width()//2, note_surface.get_height()//2)
        
        # Inclinar a cabeça da nota (notação musical padrão)
        angle = 35
        
        # Desenhar cabeça preenchida e contorno
        pygame.draw.ellipse(note_surface, (0, 0, 0), head_rect)  # Nota preta sólida
        pygame.draw.ellipse(note_surface, (100, 100, 100), head_rect, 1)  # Borda para detalhe
        
        # Adicionar brilho na cabeça da nota
        highlight_rect = pygame.Rect(head_rect)
        highlight_rect.width = head_rect.width * 0.3
        highlight_rect.height = head_rect.height * 0.3
        highlight_rect.center = (head_rect.centerx - head_rect.width * 0.2, 
                                head_rect.centery - head_rect.height * 0.2)
        pygame.draw.ellipse(note_surface, (80, 80, 80), highlight_rect)
        
        # Desenhar a haste da nota
        stem_start_x = head_rect.right - 2
        stem_start_y = head_rect.centery
        stem_length = note_size * 1.2
        stem_width = max(2, int(head_width//10))
        pygame.draw.line(note_surface, (0, 0, 0), 
                        (stem_start_x, stem_start_y), 
                        (stem_start_x, stem_start_y - stem_length), 
                        stem_width)
        
        # Adicionar bandeira para colcheias (nota tipo 2)
        if self.note_type == 2:
            flag_start_x = stem_start_x
            flag_start_y = stem_start_y - stem_length
            flag_control_x = flag_start_x + note_size * 0.5
            flag_end_x = flag_start_x + note_size * 0.4
            flag_end_y = flag_start_y + note_size * 0.4
            
            # Desenhar uma curva suave para a bandeira
            points = [(flag_start_x, flag_start_y)]
            for t in range(1, 10):
                t = t / 10
                # Fórmula da curva Bézier quadrática
                bx = (1-t)**2 * flag_start_x + 2*(1-t)*t*flag_control_x + t**2 * flag_end_x
                by = (1-t)**2 * flag_start_y + 2*(1-t)*t*flag_control_x + t**2 * flag_end_y
                points.append((bx, by))
            points.append((flag_end_x, flag_end_y))
            
            # Desenhar a bandeira como uma linha espessa
            if len(points) > 1:
                pygame.draw.lines(note_surface, (0, 0, 0), False, points, stem_width)
        
        # Aplicar efeito de brilho à nota musical
        if self.glow_alpha > 0:
            glow_surf = pygame.Surface((note_surface.get_width() + 16, note_surface.get_height() + 16), pygame.SRCALPHA)
            glow_rect = glow_surf.get_rect(center=(glow_surf.get_width()//2, glow_surf.get_height()//2))
            
            # Cor do brilho baseada na corda
            glow_color = (*self.color, self.glow_alpha)
            pygame.draw.ellipse(glow_surf, glow_color, glow_rect)
            
            # Criar uma camada de brilho temporária
            combined_surf = pygame.Surface((glow_surf.get_width(), glow_surf.get_height()), pygame.SRCALPHA)
            combined_surf.blit(glow_surf, (0, 0))
            combined_surf.blit(note_surface, ((glow_surf.get_width() - note_surface.get_width())//2, 
                                             (glow_surf.get_height() - note_surface.get_height())//2))
            
            # Aplicar rotação
            if self.is_part_of_sequence:
                # Girar com base no tempo para notas em sequência
                rotated_surf = pygame.transform.rotate(combined_surf, self.rotation // 3)
            else:
                # Girar com inclinação fixa para notas normais
                rotated_surf = pygame.transform.rotate(combined_surf, angle)
                
            rotated_rect = rotated_surf.get_rect(center=(center_x, center_y))
            surface.blit(rotated_surf, rotated_rect)
        else:
            # Aplicar rotação diretamente à nota sem brilho
            if self.is_part_of_sequence:
                rotated_surf = pygame.transform.rotate(note_surface, self.rotation // 3)
            else:
                rotated_surf = pygame.transform.rotate(note_surface, angle)
                
            rotated_rect = rotated_surf.get_rect(center=(center_x, center_y))
            surface.blit(rotated_surf, rotated_rect)
    
    def _draw_regular_note(self, surface, y, hit_zone_x, hit_zone_width):
        # Método original de desenho para outros instrumentos
        # Sombra da nota
        shadow_rect = pygame.Rect(self.x + 6, y - self.height//2 + 4, self.width, self.height)
        pygame.draw.rect(surface, (30, 30, 30, 120), shadow_rect, border_radius=10)
        
        # Gradiente da nota
        note_rect = pygame.Rect(self.x, y - self.height//2, self.width, self.height)
        gradient = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Cor especial para notas em sequência
        if self.is_part_of_sequence:
            # Adiciona um efeito pulsante para notas em sequência
            pulse = (pygame.time.get_ticks() % 1000) / 1000.0
            brightness = 80 + int(60 * pulse)
            base_color = self.color
        else:
            brightness = 60
            base_color = self.color
            
        for i in range(self.width):
            # Gradiente horizontal (da esquerda para a direita)
            color = [min(255, int(c + brightness * (i/self.width))) for c in base_color]
            pygame.draw.line(gradient, color, (i, 0), (i, self.height))
        surface.blit(gradient, note_rect)
        
        # Contorno da nota
        border_color = (255, 255, 255)
        if self.is_part_of_sequence:
            # Contorno especial para notas em sequência
            border_color = (255, 220, 100)  # Dourado
            
        pygame.draw.rect(surface, border_color, note_rect, 2, border_radius=10)
        
        # Efeito de brilho ao entrar na zona de acerto
        if self.glow_alpha > 0:
            glow = pygame.Surface((self.width+16, self.height+16), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*self.color, self.glow_alpha), glow.get_rect())
            surface.blit(glow, (note_rect.x-8, note_rect.y-8), special_flags=pygame.BLEND_RGBA_ADD)

class GuitarHeroMinigame:
    def __init__(self, instrument_id):
        self.instrument_id = instrument_id
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.last_spawn_time = 0
        self.running = True
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.start_time = time.time()
        self.duration = 20
        self.completed = False
        self.success = False
        self.bg_gradient = self.create_bg_gradient()
        self.last_width = SCREEN_WIDTH
        self.last_height = SCREEN_HEIGHT
        self.flash_fail = False
        self.flash_timer = 0.0
        self.flash_duration = 0.18  # duração do flash em segundos
        self.failed_lanes = []  # lista de lanes que falharam
        self.fail_count = 0     # contador de falhas
        
        # Efeitos de acerto
        self.hit_flashes = []  # Lista para armazenar efeitos de flash ao acertar
        
        # Carrega imagem de fundo específica para o instrumento
        self.bg_image = None
        if self.instrument_id == "MODEL_MANDOLINE":
            try:
                self.bg_image = pygame.image.load("Images/minigame_mandoline.png")
            except pygame.error:
                print("Erro ao carregar imagem de fundo para mandolim")
        elif self.instrument_id == "MODEL_CRUMHORN":
            try:
                self.bg_image = pygame.image.load("Images/minigame_crumhorn.png")
            except pygame.error:
                print("Erro ao carregar imagem de fundo para crumhorn")
        elif self.instrument_id == "MODEL_VUVUZELA":
            try:
                self.bg_image = pygame.image.load("Images/minigame_vuvuzela.png")
            except pygame.error:
                print("Erro ao carregar imagem de fundo para vuvuzela")
        elif self.instrument_id == "MODEL_DIGERIDOO":
            try:
                self.bg_image = pygame.image.load("Images/minigame_digeridoo.png")
            except pygame.error:
                print("Erro ao carregar imagem de fundo para digeridoo")
        
        # Flag para determinar se o instrumento usa visualização especial
        self.use_special_visualization = self.instrument_id in ["MODEL_MANDOLINE", "MODEL_VUVUZELA", "MODEL_CRUMHORN", "MODEL_DIGERIDOO"]
        
        # Definir estilo visual específico para cada instrumento
        self.instrument_style = {
            "MODEL_MANDOLINE": {
                "string_positions": [0.35, 0.42, 0.52, 0.60],  # Posições relativas das cordas
                "use_musical_notes": True,                     # Usar notas musicais em vez de blocos
                "hit_zone_height": 0.03,                      # Altura relativa da zona de acerto
                "note_width_factor": 0.05,                    # Fator de largura da nota
                "note_height_factor": 0.025,                  # Fator de altura da nota
                "flash_size": 15                              # Tamanho do efeito de flash
            },
            "MODEL_VUVUZELA": {
                "string_positions": [0.33, 0.41, 0.53, 0.62],  # Posições ligeiramente diferentes
                "use_musical_notes": True,                     # Usar notas musicais em vez de blocos
                "hit_zone_height": 0.045,                     # Zona de acerto maior
                "note_width_factor": 0.08,                    # Notas mais largas
                "note_height_factor": 0.04,                   # Notas mais altas
                "flash_size": 20                              # Flash maior
            },
            "MODEL_CRUMHORN": {
                "string_positions": [0.32, 0.40, 0.54, 0.63],  # Posições diferentes para o crumhorn
                "use_musical_notes": True,                     # Usar notas musicais em vez de blocos
                "hit_zone_height": 0.04,                      # Zona de acerto média
                "note_width_factor": 0.07,                    # Notas ligeiramente menores
                "note_height_factor": 0.035,                  # Notas ligeiramente menores
                "flash_size": 18                              # Flash médio
            },
            "MODEL_DIGERIDOO": {
                "string_positions": [0.30, 0.38, 0.56, 0.65],  # Posições mais distantes entre si
                "use_musical_notes": True,                     # Usar notas musicais em vez de blocos
                "hit_zone_height": 0.05,                      # Zona de acerto maior
                "note_width_factor": 0.09,                    # Notas mais largas
                "note_height_factor": 0.045,                  # Notas mais altas
                "flash_size": 22                              # Flash maior
            }
        }
        
        # Usar estilo padrão se o instrumento não estiver definido
        if self.instrument_id not in self.instrument_style:
            self.instrument_style[self.instrument_id] = {
                "string_positions": [0.35, 0.45, 0.55, 0.65],  # Posições padrão
                "use_musical_notes": True,                     # Usar notas musicais por padrão
                "hit_zone_height": 0.04,                      # Zona de acerto padrão
                "note_width_factor": 0.08,                    # Largura padrão
                "note_height_factor": 0.04,                   # Altura padrão
                "flash_size": 20                              # Tamanho do flash padrão
            }
        
        # Sistema de dificuldade
        self.difficulty = 1  # Médio por padrão
        self.apply_difficulty_settings()
        
        # Feedback visual para mudança de dificuldade
        self.difficulty_message = ""
        self.difficulty_message_timer = 0
        self.difficulty_message_duration = 2.0  # Duração da mensagem em segundos
        
        # Teclas pressionadas atualmente
        self.keys_held = {1: False, 2: False, 3: False, 4: False}
        
        # Controle de sequências
        self.sequence_counter = 0  # Contador para IDs de sequência
        self.last_sequence_time = 0  # Tempo da última sequência gerada
        
    def apply_difficulty_settings(self):
        # Aplica as configurações baseadas na dificuldade atual
        settings = DIFFICULTY_SETTINGS[self.difficulty]
        self.note_speed = settings[0]
        self.spawn_interval = settings[1]
        self.simultaneous_notes = settings[2]
        self.success_threshold = settings[3]
        self.max_fails = settings[4]
        self.sequence_chance = settings[5]  # Chance de gerar uma sequência
        self.max_sequence_notes = settings[6]  # Número máximo de notas em uma sequência
    
    def create_bg_gradient(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            r = 30 + int(80 * y / SCREEN_HEIGHT)
            g = 0 + int(30 * y / SCREEN_HEIGHT)
            b = 60 + int(120 * y / SCREEN_HEIGHT)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        return surf
    
    def spawn_note(self):
        current_time = time.time()
        
        # Verifica se deve gerar uma sequência rápida
        if (self.sequence_chance > 0 and 
            random.random() < self.sequence_chance and 
            current_time - self.last_sequence_time > 2.0):  # Intervalo mínimo entre sequências
            
            # Gera uma sequência de notas rápidas
            self.spawn_sequence()
            self.last_sequence_time = current_time
            return
        
        # Determina quantas notas serão geradas simultaneamente
        num_notes = min(self.simultaneous_notes, 4)  # Máximo de 4 lanes
        
        # Para dificuldade fácil, garante apenas uma nota por vez
        if self.difficulty == 0:
            num_notes = 1
        # Para outras dificuldades, varia o número de notas simultâneas
        else:
            # Chance de ter menos notas do que o máximo permitido
            if random.random() < 0.5:
                num_notes = max(1, random.randint(1, num_notes))
        
        # Seleciona lanes aleatórias sem repetição
        available_lanes = list(range(1, 5))
        selected_lanes = []
        
        for _ in range(num_notes):
            if not available_lanes:
                break
            lane = random.choice(available_lanes)
            available_lanes.remove(lane)
            selected_lanes.append(lane)
        
        # Cria as notas
        for lane in selected_lanes:
            note = Note(lane, speed=self.note_speed)
            self.notes.append(note)
    
    def spawn_sequence(self):
        # Gera uma sequência de notas rápidas na mesma lane
        self.sequence_counter += 1  # Incrementa o contador de sequências
        sequence_id = self.sequence_counter
        
        # Escolhe uma lane aleatória para a sequência
        lane = random.randint(1, 4)
        
        # Determina quantas notas terá na sequência (2 a max_sequence_notes)
        num_notes = random.randint(2, self.max_sequence_notes)
        
        # Intervalo entre notas da sequência (mais curto que o normal)
        sequence_interval = 0.2 - (self.difficulty * 0.03)  # 0.2s no fácil, 0.11s no muito difícil
        
        # Cria as notas da sequência com pequeno intervalo horizontal entre elas
        for i in range(num_notes):
            note = Note(lane, speed=self.note_speed)
            note.is_part_of_sequence = True
            note.sequence_id = sequence_id
            # Posiciona as notas com um pequeno intervalo entre elas (à direita da tela)
            note.x = SCREEN_WIDTH + i * (note.speed * sequence_interval * 60)  # 60 é aproximadamente o FPS
            self.notes.append(note)
    
    def update(self, dt):
        current_time = time.time()
        if current_time - self.start_time > self.duration:
            self.running = False
            self.success = self.score >= self.success_threshold
            self.completed = True
            return
            
        # Gera novas notas com base no intervalo de spawn
        if current_time - self.last_spawn_time > self.spawn_interval:
            self.spawn_note()
            self.last_spawn_time = current_time
            
        # Dimensões dinâmicas para as notas e hit zones com base no estilo do instrumento
        style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
        note_width = int(self.last_width * style["note_width_factor"])
        note_height = int(self.last_height * style["note_height_factor"])
        
        # Atualiza todas as notas
        for note in self.notes:
            note.update(note_width, note_height)
            
        # Detectar falha: nota passou da zona de acerto sem ser pressionada
        hit_zone_x = int(self.last_width * 0.1)
        hit_zone_width = int(self.last_width * 0.05)
        
        for note in self.notes:
            if note.active and note.x < hit_zone_x - hit_zone_width:
                note.active = False
                self.combo = 0
                self.flash_fail = True
                self.flash_timer = self.flash_duration
                if note.lane not in self.failed_lanes:
                    self.failed_lanes.append(note.lane)
                self.fail_count += 1
                if self.fail_count >= self.max_fails:
                    self.running = False
                    self.success = False
                    self.completed = True
                    
        # As notas só desaparecem após passarem completamente pelo limite esquerdo da tela
        self.notes = [note for note in self.notes if note.x > -50]
        
        # Atualizar timer do flash
        if self.flash_fail:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_fail = False
                self.failed_lanes = []  # Limpa lanes que estavam piscando
    
    def handle_key_press(self, key):
        # Verifica se é uma tecla de mudança de dificuldade
        if key in DIFFICULTY_KEYS:
            self.difficulty = DIFFICULTY_KEYS[key]
            self.apply_difficulty_settings()
            return
        
        # Verifica se é uma tecla de nota
        lane = None
        for l, k in KEYS.items():
            if key == k:
                lane = l
                self.keys_held[lane] = True  # Marca a tecla como pressionada
                break
        
        if lane is None:
            return
            
        hit = False
        hit_zone_x = int(self.last_width * 0.1)
        hit_zone_width = int(self.last_width * 0.05)
        
        # Ajustar a tolerância da zona de acerto com base no instrumento
        style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
        # A tolerância é inversamente proporcional ao tamanho da nota
        tolerance = int(20 * (0.08 / style["note_width_factor"]))
        
        for note in self.notes:
            if note.lane == lane and note.active:
                # Verifica se a nota está na zona de acerto (esquerda)
                if hit_zone_x - hit_zone_width <= note.x <= hit_zone_x + hit_zone_width:
                    # Marca a nota como acertada
                    note.active = False
                    
                    # Notas em sequência valem mais pontos
                    if note.is_part_of_sequence:
                        self.score += 2
                    else:
                        self.score += 1
                        
                    self.combo += 1
                    if self.combo > self.max_combo:
                        self.max_combo = self.combo
                    
                    # Adicionar efeito visual de flash ao acertar
                    # (lane, posição x, alpha inicial, tamanho inicial)
                    style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
                    flash_size = style["flash_size"]
                    self.hit_flashes.append((lane, hit_zone_x, 240, flash_size))
                    
                    hit = True
                    break
        
        if not hit:
            self.combo = 0
    
    def handle_key_release(self, key):
        lane = None
        for l, k in KEYS.items():
            if key == k:
                lane = l
                self.keys_held[lane] = False  # Marca a tecla como liberada
                break
    
    def draw(self, surface):
        width, height = surface.get_size()
        self.last_width = width
        self.last_height = height
        
        # Fundo gradiente ou imagem
        if self.bg_image:
            # Redimensiona a imagem para o tamanho atual da tela
            bg_resized = pygame.transform.scale(self.bg_image, (width, height))
            surface.blit(bg_resized, (0, 0))
            
            # Obter estilo do instrumento atual
            style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
            
            # Cálculo das posições das "cordas" para o instrumento
            string_positions = [
                height * style["string_positions"][0],
                height * style["string_positions"][1],
                height * style["string_positions"][2],
                height * style["string_positions"][3]
            ]
            
            # Efeito de "cordas" vibrantes para o instrumento
            for i in range(1, 5):
                y = string_positions[i-1]
                # Desenhar cordas vibrantes
                amplitude = 2 + (2 if self.keys_held[i] else 0)  # Amplitude maior quando pressionada
                points = []
                wave_freq = 0.05  # Frequência da onda da corda
                wave_speed = pygame.time.get_ticks() * 0.001  # Velocidade da animação
                
                # Gerar pontos para a linha ondulada
                for x in range(0, width, 5):
                    # Criar uma onda senoidal que varia com o tempo
                    y_offset = amplitude * math.sin(wave_freq * x + wave_speed * 3)
                    points.append((x, y + y_offset))
                
                # Desenhar corda vibrante
                if len(points) > 1:
                    # Cor da corda baseada na lane
                    cord_color = COLORS[i]
                    
                    # Desenhar uma linha de sombra para dar profundidade
                    shadow_points = [(p[0], p[1]+2) for p in points]
                    pygame.draw.aalines(surface, (30, 30, 30, 150), False, shadow_points, 2)
                    
                    # Desenhar a corda principal
                    pygame.draw.aalines(surface, cord_color, False, points, 3)
                    
                    # Desenhar uma linha mais fina e clara para o brilho da corda
                    highlight_color = (min(255, cord_color[0] + 70), 
                                       min(255, cord_color[1] + 70), 
                                       min(255, cord_color[2] + 70))
                    pygame.draw.aalines(surface, highlight_color, False, 
                                       [(p[0], p[1] - 1) for p in points], 1)
        else:
            # Usa o gradiente padrão para outros instrumentos
            bg = pygame.transform.smoothscale(self.bg_gradient, (width, height))
            surface.blit(bg, (0, 0))
            
            # Desenhar linhas horizontais para as lanes
            for i in range(1, 5):
                y = (height // 6) * i + 60
                # Destaca a lane se a tecla estiver pressionada
                if self.keys_held[i]:
                    pygame.draw.line(surface, COLORS[i], (0, y), (width, y), 3)
                else:
                    pygame.draw.line(surface, (100, 100, 100), (0, y), (width, y), 2)
                key_text = self.font.render(str(i), True, COLORS[i])
                surface.blit(key_text, (width * 0.08 - key_text.get_width()//2, y - 15))
            
        # Título (mostra o nome do instrumento sem o prefixo MODEL_)
        instrument_name = self.instrument_id.replace('MODEL_', '').replace('_', ' ').title()
        title = self.title_font.render(f"Toque o {instrument_name}", True, (255, 215, 0))
        shadow = self.title_font.render(f"Toque o {instrument_name}", True, (0,0,0))
        surface.blit(shadow, (width//2 - title.get_width()//2 + 3, 23))
        surface.blit(title, (width//2 - title.get_width()//2, 20))
        
        # Indicador de dificuldade
        difficulty_text = self.font.render(f"Dificuldade: {DIFFICULTY_NAMES[self.difficulty]}", True, (255, 215, 0))
        surface.blit(difficulty_text, (width//2 - difficulty_text.get_width()//2, 60))
        
        # Zona de acerto (esquerda)
        hit_zone_x = int(width * 0.1)
        hit_zone_width = int(width * 0.05)
        
        for i in range(1, 5):
            # Usar as posições de corda específicas para mandolim ou posições padrão para outros instrumentos
            style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
            
            if self.use_special_visualization:
                # Usar as posições específicas para o instrumento atual
                string_positions = [
                    height * style["string_positions"][0],
                    height * style["string_positions"][1],
                    height * style["string_positions"][2],
                    height * style["string_positions"][3]
                ]
                y = string_positions[i-1]
                
                # Zona de acerto baseada no estilo do instrumento
                hit_zone_height = style["hit_zone_height"]
                rect = pygame.Rect(hit_zone_x - hit_zone_width, y - int(height * hit_zone_height/2), 
                                  hit_zone_width * 2, int(height * hit_zone_height))
            else:
                y = (height // 6) * i + 60
                
                # Zona de acerto padrão para instrumentos sem visualização especial
                rect = pygame.Rect(hit_zone_x - hit_zone_width, y - int(height*0.025), hit_zone_width * 2, int(height*0.05))
                
            # Desenhar números das teclas
            key_text = self.font.render(str(i), True, COLORS[i])
            surface.blit(key_text, (width * 0.08 - key_text.get_width()//2, y - 15))
            
            # Desenhar zona de acerto
            zone = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            for x in range(rect.width):
                alpha = 80 + int(80 * x / rect.width)
                pygame.draw.line(zone, (80, 80, 80, alpha), (x, 0), (x, rect.height))
            # Efeito de flash vermelho apenas na lane que falhou
            if self.flash_fail and i in self.failed_lanes:
                flash_alpha = int(180 * (self.flash_timer / self.flash_duration))
                pygame.draw.rect(zone, (255, 0, 0, flash_alpha), (0, 0, rect.width, rect.height), border_radius=8)
            # Destaca a zona de acerto se a tecla estiver pressionada
            elif self.keys_held[i]:
                pygame.draw.rect(zone, (*COLORS[i], 80), (0, 0, rect.width, rect.height), border_radius=8)
            surface.blit(zone, rect)
            pygame.draw.rect(surface, (255,255,255,80), rect, 2, border_radius=8)
        
        # Notas
        for note in self.notes:
            style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
            use_musical_notes = style.get("use_musical_notes", False)
            
            if self.use_special_visualization:
                # Usar as posições específicas para o instrumento atual
                string_positions = [
                    height * style["string_positions"][0],
                    height * style["string_positions"][1],
                    height * style["string_positions"][2],
                    height * style["string_positions"][3]
                ]
                y = string_positions[note.lane-1]
            else:
                y = (height // 6) * note.lane + 60
                
            note.draw(surface, y, hit_zone_x, hit_zone_width, use_musical_notes)
            
        # Desenhar efeitos de flash para acertos
        hit_flashes_to_keep = []
        for hit_flash in self.hit_flashes:
            lane, x, alpha, size = hit_flash
            style = self.instrument_style.get(self.instrument_id, self.instrument_style.get("MODEL_MANDOLINE"))
            
            if self.use_special_visualization:
                # Usar as posições específicas para o instrumento atual
                string_positions = [
                    height * style["string_positions"][0],
                    height * style["string_positions"][1],
                    height * style["string_positions"][2],
                    height * style["string_positions"][3]
                ]
                y = string_positions[lane-1]
            else:
                y = (height // 6) * lane + 60
                
            # Desenhar o flash como um círculo colorido que diminui
            flash_surf = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            color = COLORS[lane]
            # Cor mais brilhante para o flash
            bright_color = (min(255, color[0] + 100), min(255, color[1] + 100), min(255, color[2] + 100), alpha)
            pygame.draw.circle(flash_surf, bright_color, (size, size), size)
            
            # Desenhar um círculo interno mais claro
            inner_size = size * 0.6
            inner_color = (min(255, color[0] + 150), min(255, color[1] + 150), min(255, color[2] + 150), alpha)
            pygame.draw.circle(flash_surf, inner_color, (size, size), inner_size)
            
            # Posicionar e desenhar o flash
            flash_rect = flash_surf.get_rect(center=(x, y))
            surface.blit(flash_surf, flash_rect, special_flags=pygame.BLEND_RGBA_ADD)
            
            # Atualizar parâmetros do flash
            alpha -= 15  # Diminuir opacidade
            size += 3    # Aumentar tamanho
            
            # Manter o flash se ainda estiver visível
            if alpha > 0:
                hit_flashes_to_keep.append((lane, x, alpha, size))
                
        # Atualizar lista de flashes
        self.hit_flashes = hit_flashes_to_keep
        
        # Exibir contador de falhas
        fail_text = self.font.render(f"Erros: {self.fail_count}/{self.max_fails}", True, (255, 80, 80))
        surface.blit(fail_text, (width - fail_text.get_width() - 18, 18))
        
        # Placar
        score_text = self.font.render(f"Pontuação: {self.score}/{self.success_threshold}", True, (255, 255, 255))
        surface.blit(score_text, (20, 20))
        combo_text = self.font.render(f"Combo: {self.combo}", True, (255, 255, 255))
        surface.blit(combo_text, (20, 50))
        time_left = max(0, self.duration - (time.time() - self.start_time))
        time_text = self.font.render(f"Tempo: {int(time_left)}s", True, (255, 255, 255))
        surface.blit(time_text, (width - time_text.get_width() - 20, 50))
        
        # Instruções
        instructions = self.font.render("Pressione as teclas 1-4 quando as notas chegarem na zona de acerto", True, (200, 200, 200))
        surface.blit(instructions, (width//2 - instructions.get_width()//2, height - 60))

    
    def draw_results(self, surface):
        width, height = surface.get_size()
        surface.fill((0, 0, 0))
        
        # Only show the collection image if the player succeeded
        if self.success:
            # Get the instrument name in lowercase for image filename
            instrument_name = self.instrument_id.replace('MODEL_', '').lower()
            collection_image_path = f'Images/{instrument_name}_col.png'
            
            try:
                # Try to load the instrument-specific collection image
                collection_image = pygame.image.load(collection_image_path)
                
                # MODIFICADO: Redimensionar a imagem para preencher toda a tela
                # em vez de manter a proporção da imagem original
                new_width = width
                new_height = height
                
                # Scale to fill the entire screen
                collection_image = pygame.transform.smoothscale(collection_image, (new_width, new_height))
                
                # Position at (0,0) to cover the entire screen instead of centering
                surface.blit(collection_image, (0, 0))
                
                # Add "Press SPACE to continue" text at the bottom
                # MODIFICADO: Melhorar a visibilidade do texto com fundo e sombra
                # Sombra do texto
                shadow_text = self.font.render("Pressione ESPAÇO para continuar", True, (0, 0, 0))
                shadow_rect = shadow_text.get_rect(center=(width//2 + 2, height - 28))
                surface.blit(shadow_text, shadow_rect)
                
                # Texto principal
                continue_text = self.font.render("Pressione ESPAÇO para continuar", True, (255, 255, 255))
                continue_rect = continue_text.get_rect(center=(width//2, height - 30))
                surface.blit(continue_text, continue_rect)
                
                return  # Exit the method here to avoid drawing the default screen
                
            except Exception as e:
                # Fallback to the original results screen if image loading fails
                print(f"Erro ao carregar imagem {collection_image_path}: {e}")
        
        # Default results screen (shown on failure or if image loading fails)
        if self.success:
            result_text = self.title_font.render("Sucesso!", True, (0, 255, 0))
            msg = "Você dominou o instrumento!"
        else:
            result_text = self.title_font.render("Falhou!", True, (255, 0, 0))
            msg = "Tente novamente para dominar o instrumento."
        surface.blit(result_text, (width//2 - result_text.get_width()//2, height//3))
        msg_text = self.font.render(msg, True, (255, 255, 255))
        surface.blit(msg_text, (width//2 - msg_text.get_width()//2, height//2))
        score_text = self.font.render(f"Pontuação final: {self.score}", True, (255, 255, 255))
        surface.blit(score_text, (width//2 - score_text.get_width()//2, height//2 + 40))
        combo_text = self.font.render(f"Combo máximo: {self.max_combo}", True, (255, 255, 255))
        surface.blit(combo_text, (width//2 - combo_text.get_width()//2, height//2 + 70))
        continue_text = self.font.render("Pressione ESPAÇO para continuar", True, (200, 200, 200))
        surface.blit(continue_text, (width//2 - continue_text.get_width()//2, height - 50))