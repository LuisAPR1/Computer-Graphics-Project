import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from cTerrain import Terrain
from cData import Data
import math
from cShader import Shader
from lava import Lava
from cTerrain import TERRAIN_SIZE
from cModel import Model
from cSound import Sound, SOUND_PICKUP, SOUND_CHILLJAZZ, SOUND_PAUSEMENU, SOUND_BOUNCE, SOUND_LAVASOUND, SOUND_LOSESONG, SOUND_WALK, SOUND_MANDOLINE, SOUND_VUVUZELA, SOUND_CRUMHORN, SOUND_DIGERIDOO, SOUND_FAIL
import sys
import os
import numpy as np
from guitar_hero import GuitarHeroMinigame
import time

SCREEN_WIDTH = 1545
SCREEN_HEIGHT = 800
FRAMERATE = 144
GRAVITY = 0.05
PLAYER_SPEED = 0.5
JUMP_SPEED = 1
RADIUS = 1.0
COLLECTION_RADIUS = 6.0  # MODIFIED: Increased collection radius
MAX_CLIMB_SLOPE = 1000.0  # Tangente do ângulo máximo de subida (e.g., 1.0 para 45 graus)
MOUSE_SENSITIVITY = 0.2  # Default mouse sensitivity value

GAME_SETTINGS = {
    "SCREEN_WIDTH": SCREEN_WIDTH,
    "SCREEN_HEIGHT": SCREEN_HEIGHT,
    "FRAMERATE": FRAMERATE,
    "GRAVITY": GRAVITY,
    "PLAYER_SPEED": PLAYER_SPEED,
    "JUMP_SPEED": JUMP_SPEED,
    "RADIUS": RADIUS,
    "COLLECTION_RADIUS": COLLECTION_RADIUS,
    "MAX_CLIMB_SLOPE": MAX_CLIMB_SLOPE,
    "MOUSE_SENSITIVITY": MOUSE_SENSITIVITY
}

# Helper functions for animations
def lerp(a, b, t):
    return a * (1 - t) + b * t

def lerp_vec3(v1, v2, t):
    return tuple(lerp(c1, c2, t) for c1, c2 in zip(v1, v2))

def ease_out_quad(t): # Decelerating to zero velocity
    return t * (2 - t)

def ease_in_quad(t): # Accelerating from zero velocity
    return t * t

def ease_in_out_smooth(t): # Smooth step (cubic)
    return t * t * (3.0 - 2.0 * t)

# Function to update global variables from GAME_SETTINGS
def update_global_settings():
    global SCREEN_WIDTH, SCREEN_HEIGHT, FRAMERATE, GRAVITY, PLAYER_SPEED, JUMP_SPEED, RADIUS, COLLECTION_RADIUS, MAX_CLIMB_SLOPE, MOUSE_SENSITIVITY
    SCREEN_WIDTH = GAME_SETTINGS["SCREEN_WIDTH"]
    SCREEN_HEIGHT = GAME_SETTINGS["SCREEN_HEIGHT"]
    FRAMERATE = GAME_SETTINGS["FRAMERATE"]
    GRAVITY = GAME_SETTINGS["GRAVITY"]
    PLAYER_SPEED = GAME_SETTINGS["PLAYER_SPEED"]
    JUMP_SPEED = GAME_SETTINGS["JUMP_SPEED"]
    RADIUS = GAME_SETTINGS["RADIUS"]
    COLLECTION_RADIUS = GAME_SETTINGS["COLLECTION_RADIUS"]
    MAX_CLIMB_SLOPE = GAME_SETTINGS["MAX_CLIMB_SLOPE"]
    MOUSE_SENSITIVITY = GAME_SETTINGS["MOUSE_SENSITIVITY"]

class Player:
    def __init__(self, terrain):
        self.x = 500.0
        self.z = 512.0
        self.y = terrain.get_height_bicubic(self.x, self.z) + RADIUS
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.on_ground = False
        # Store last position for movement detection
        self._last_pos = (self.x, self.y, self.z)
        self.max_health = 100
        self.health = self.max_health

class MainMenu:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.font_title = None
        self.font_options = None
        self.selected = 0  # 0 = Start, 1 = Options, 2 = Quit
        self.options = ['Start', 'Options', 'Quit']
        self.running = True
        self.screen = None
        self.bg_color_top = (40, 0, 40)  # Dark purple
        self.bg_color_bottom = (0, 0, 20)  # Deep blue
        self.title_color = (255, 215, 0)  # Gold
        self.selected_color = (255, 255, 0)  # Yellow
        self.unselected_color = (200, 200, 200)  # Light gray
        self.highlight_color = (128, 0, 128)  # Purple
        self.time = 0
        self.sound = None  # Para gerenciar a música de fundo

    def init(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()  # Inicializa o mixer para reproduzir a música
       
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        # Carregar imagem de fundo
        self.background_img = pygame.image.load('Images/background.png').convert()
        self.background_img = pygame.transform.scale(self.background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        # Try to load a nicer font, fall back to system fonts if unavailable
        try:
            self.font_title = pygame.font.Font(None, 80)  # Default bold font
            self.font_options = pygame.font.Font(None, 46)
        except:
            self.font_title = pygame.font.SysFont('Arial', 72, bold=True)
            self.font_options = pygame.font.SysFont('Arial', 42)
            
        # Inicializa e toca a música de fundo do menu
        self.sound = Sound()
        self.sound.load()
        self.sound.play(SOUND_CHILLJAZZ)

    def loop(self):
        self.running = True
        self.time = 0
        action = 'quit'
        while self.running:
            dt = 1.0 / FRAMERATE
            self.update_sky_lighting(dt)
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    action = 'quit'
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                        action = 'quit'
                    elif event.key == K_UP or event.key == K_w:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key == K_DOWN or event.key == K_s:
                        self.selected = (self.selected + 1) % len(self.options)
                    elif event.key == K_RETURN or event.key == K_SPACE:
                        if self.selected == 0:  # Start
                            self.running = False
                            action = 'start'
                        elif self.selected == 1:  # Options
                            self.running = False # ADDED: Exit main menu loop
                            action = 'options'
                        elif self.selected == 2:  # Quit
                            self.running = False
                            action = 'quit'
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True
            # Verificar se o mouse está sobre algum botão
            for i, option in enumerate(self.options):
                y_pos = SCREEN_HEIGHT//2 + i * 70
                text = self.font_options.render(option, True, self.selected_color if i == self.selected else self.unselected_color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
                if text_rect.collidepoint(mouse_pos):
                    self.selected = i
                    if mouse_clicked:
                        if self.selected == 0:
                            self.running = False
                            action = 'start'
                        elif self.selected == 1:
                            self.running = False # ADDED: Exit main menu loop
                            action = 'options'
                        elif self.selected == 2:
                            self.running = False
                            action = 'quit'
            self.render()
        
        # Para a música quando sair do menu principal
        if self.sound:
            self.sound.stop_menu_music()
            
        return action

    def render(self):
        # Desenhar imagem de fundo
        if hasattr(self, 'background_img'):
            self.screen.blit(self.background_img, (0, 0))
        else:
            # Draw gradient background
            for y in range(SCREEN_HEIGHT):
                r = self.bg_color_top[0] + (self.bg_color_bottom[0] - self.bg_color_top[0]) * y / SCREEN_HEIGHT
                g = self.bg_color_top[1] + (self.bg_color_bottom[1] - self.bg_color_top[1]) * y / SCREEN_HEIGHT
                b = self.bg_color_top[2] + (self.bg_color_bottom[2] - self.bg_color_top[2]) * y / SCREEN_HEIGHT
                pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Draw menu options with highlight effect for selected item
        for i, option in enumerate(self.options):
            y_pos = SCREEN_HEIGHT//2 + i * 70
            text = self.font_options.render(option, True, self.selected_color if i == self.selected else self.unselected_color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_pos))
            if i == self.selected:
                smoothFactor = (1 - math.cos(self.time * 1.2)) / 2
                pulse_factor = 1 + smoothFactor * 0.13  # efeito mais visível
                padding = 26
                width_growth = int((text_rect.width + padding) * (pulse_factor - 1))
                height_growth = int((text_rect.height + padding) * (pulse_factor - 1))
                highlight_rect = pygame.Rect(
                    SCREEN_WIDTH//2 - (text_rect.width + padding)//2 - width_growth//2,
                    text_rect.centery - (text_rect.height + padding)//2 - height_growth//2,
                    text_rect.width + padding + width_growth,
                    text_rect.height + padding + height_growth
                )
                pygame.draw.rect(self.screen, (180, 80, 255), highlight_rect, border_radius=16)
            self.screen.blit(text, text_rect)

        # Draw footer text
        version_text = self.font_options.render('v1.0', True, (100, 100, 100))
        version_rect = version_text.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        self.screen.blit(version_text, version_rect)

        pygame.display.flip()

    def update_sky_lighting(self, dt):
        # Update day-night cycle
        self.time += dt

class OptionsMenu:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.font_title = None
        self.font_options = None
        self.font_values = None
        self.selected_option_index = 0
        self.running = True
        self.screen = None
        self.bg_color_top = (20, 20, 60)  # Darker blue for options
        self.bg_color_bottom = (0, 0, 10)   # Very dark blue
        self.title_color = (255, 215, 0)    # Gold
        self.selected_color = (255, 255, 0) # Yellow
        self.unselected_color = (200, 200, 200) # Light gray
        self.value_color = (150, 255, 150) # Light green for values
        self.time = 0
        
        # Apenas manter as configurações de tamanho de tela e FPS
        self.settings_items = ["SCREEN_WIDTH", "SCREEN_HEIGHT", "FRAMERATE", "MOUSE_SENSITIVITY"]
        self.current_values = {
            "SCREEN_WIDTH": GAME_SETTINGS["SCREEN_WIDTH"],
            "SCREEN_HEIGHT": GAME_SETTINGS["SCREEN_HEIGHT"],
            "FRAMERATE": GAME_SETTINGS["FRAMERATE"],
            "MOUSE_SENSITIVITY": GAME_SETTINGS["MOUSE_SENSITIVITY"]
        }

        # For text input
        self.editing_value = False
        self.current_editing_key = None
        self.input_text = ""
        
        # Para os botões de incremento/decremento
        self.button_rects = {}

    def init(self):
        pygame.init() # Ensure pygame is initialized
        pygame.font.init()
        self.screen = pygame.display.set_mode((GAME_SETTINGS["SCREEN_WIDTH"], GAME_SETTINGS["SCREEN_HEIGHT"]))
        try:
            self.font_title = pygame.font.Font(None, 70)
            self.font_options = pygame.font.Font(None, 40)
            self.font_values = pygame.font.Font(None, 40)
        except:
            self.font_title = pygame.font.SysFont('Arial', 60, bold=True)
            self.font_options = pygame.font.SysFont('Arial', 36)
            self.font_values = pygame.font.SysFont('Arial', 36)

    def get_button_rects(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_y = screen_height - 100
        
        # Criar botão maior
        button_width = 200
        button_height = 50
        
        # Posicionar o botão no centro
        back_rect = pygame.Rect(
            screen_width // 2 - button_width // 2,
            button_y,
            button_width,
            button_height
        )
        
        # Retornar None para o botão Aplicar que não será mais usado
        return None, back_rect

    def handle_input(self):
        action = None
        mouse_clicked = False
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                action = 'menu' # Go back to main menu
            elif event.type == KEYDOWN:
                if self.editing_value:
                    if event.key == K_RETURN:
                        self.apply_input_value()
                    elif event.key == K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == K_ESCAPE:
                        self.editing_value = False
                        self.current_editing_key = None
                        self.input_text = ""
                    else:
                        # Allow numbers, '.', and '-' (for negative numbers if needed)
                        if event.unicode.isdigit() or event.unicode == '.' or (event.unicode == '-' and not self.input_text):
                            self.input_text += event.unicode
                else:
                    if event.key == K_ESCAPE:
                        self.running = False
                        action = 'menu'
                    elif event.key == K_UP or event.key == K_w:
                        self.selected_option_index = (self.selected_option_index - 1) % len(self.settings_items)
                    elif event.key == K_DOWN or event.key == K_s:
                        self.selected_option_index = (self.selected_option_index + 1) % len(self.settings_items)
                    elif event.key == K_RETURN: # Start editing selected value
                        self.current_editing_key = self.settings_items[self.selected_option_index]
                        # Attempt to convert current value to string, handle floats/ints appropriately
                        current_val = self.current_values[self.current_editing_key]
                        if isinstance(current_val, float):
                            self.input_text = f"{current_val:.2f}" # Format float to 2 decimal places
                        else:
                            self.input_text = str(current_val)
                        self.editing_value = True
                    elif event.key == K_LEFT or event.key == K_a:
                        self.modify_value(self.settings_items[self.selected_option_index], -1)
                    elif event.key == K_RIGHT or event.key == K_d:
                        self.modify_value(self.settings_items[self.selected_option_index], 1)

            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

        # Verificar cliques nos botões de incremento/decremento
        if mouse_clicked and not self.editing_value:
            for key in self.settings_items:
                if key in self.button_rects:
                    if self.button_rects[key]['decrement'].collidepoint(mouse_pos):
                        self.modify_value(key, -1)
                        break
                    elif self.button_rects[key]['increment'].collidepoint(mouse_pos):
                        self.modify_value(key, 1)
                        break

        if not self.editing_value:
            # Calculando as posições com base no tamanho atual da janela
            screen_width = self.screen.get_width()
            screen_height = self.screen.get_height()
            
            for i, key in enumerate(self.settings_items):
                # Posição vertical ajustada ao tamanho da tela
                option_y_pos = screen_height // 3 + 100 + i * 50
                
                # Define clickable area for each option text (name and value)
                option_labels = {
                    "SCREEN_WIDTH": "Largura da Tela",
                    "SCREEN_HEIGHT": "Altura da Tela",
                    "FRAMERATE": "Taxa de Quadros (FPS)",
                    "MOUSE_SENSITIVITY": "Sensibilidade do Mouse"
                }
                
                name_text_surf = self.font_options.render(f"{option_labels[key]}: ", True, self.unselected_color)
                name_text_rect = name_text_surf.get_rect(topleft=(screen_width // 2 - 300, option_y_pos))

                value_str = f"{self.current_values[key]:.2f}" if isinstance(self.current_values[key], float) else str(self.current_values[key])
                value_text_surf = self.font_values.render(value_str, True, self.value_color)
                value_text_rect = value_text_surf.get_rect(midleft=(name_text_rect.right + 10, option_y_pos + name_text_rect.height // 2))
                
                full_rect = name_text_rect.union(value_text_rect) # Combine rects for easier click detection
                
                # Add some padding to the clickable area
                clickable_rect = full_rect.inflate(20, 10)

                if clickable_rect.collidepoint(mouse_pos):
                    self.selected_option_index = i
                    if mouse_clicked:
                        self.current_editing_key = key
                        current_val = self.current_values[self.current_editing_key]
                        if isinstance(current_val, float):
                            self.input_text = f"{current_val:.2f}"
                        else:
                            self.input_text = str(current_val)
                        self.editing_value = True
                        break # Process one click at a time

        # Check for "Back to Menu" button
        _, back_button_rect = self.get_button_rects()

        if back_button_rect.collidepoint(mouse_pos) and mouse_clicked:
            self.running = False
            action = 'menu'

        return action

    def save_settings(self):
        global GAME_SETTINGS
        # Atualiza apenas as configurações que estamos modificando (screen size e FPS)
        for key in self.settings_items:
            GAME_SETTINGS[key] = self.current_values[key]
        update_global_settings()
        
        # Aplicar as configurações imediatamente
        if GAME_SETTINGS["SCREEN_WIDTH"] != self.screen.get_width() or GAME_SETTINGS["SCREEN_HEIGHT"] != self.screen.get_height():
            self.screen = pygame.display.set_mode((GAME_SETTINGS["SCREEN_WIDTH"], GAME_SETTINGS["SCREEN_HEIGHT"]))
        
        # Aqui você também poderia salvar em um arquivo
        print("Configurações salvas:", {k: GAME_SETTINGS[k] for k in self.settings_items})

    def modify_value(self, key, direction):
        value = self.current_values[key]
        
        # Definir os passos para cada tipo de configuração
        if key == "FRAMERATE":
            step = 5  # Ajuste de 5 em 5 para o framerate
        elif key == "MOUSE_SENSITIVITY":
            step = 0.05  # Passo pequeno para a sensibilidade do mouse
        else:  # SCREEN_WIDTH ou SCREEN_HEIGHT
            step = 50  # Ajuste de 50 em 50 para dimensões da tela
            
        # Aplicar o passo na direção correta
        if direction > 0:
            self.current_values[key] += step
        else:
            self.current_values[key] -= step
            
        # Garantir valores mínimos
        if key == "SCREEN_WIDTH" or key == "SCREEN_HEIGHT":
            self.current_values[key] = max(400, self.current_values[key])  # Mínimo de 400 pixels
        if key == "FRAMERATE":
            self.current_values[key] = max(30, self.current_values[key])  # Mínimo de 30 FPS
        if key == "MOUSE_SENSITIVITY":
            self.current_values[key] = max(0.05, min(1.0, self.current_values[key]))  # Entre 0.05 e 1.0
            
        # Aplicar configurações imediatamente
        self.save_settings()

    def apply_input_value(self):
        if self.current_editing_key:
            try:
                original_value = GAME_SETTINGS[self.current_editing_key]
                if isinstance(original_value, int):
                    new_value = int(self.input_text)
                elif isinstance(original_value, float):
                    new_value = float(self.input_text)
                else: # Should not happen with current GAME_SETTINGS
                    new_value = self.input_text

                self.current_values[self.current_editing_key] = new_value
                
                # Aplicar configurações imediatamente
                self.save_settings()
            except ValueError:
                # Handle error if conversion fails (e.g., non-numeric input for number)
                # For now, just revert to original or do nothing
                pass # Or maybe log an error, or show a message to the user
        self.editing_value = False
        self.current_editing_key = None
        self.input_text = ""

    def render(self):
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Gradient background
        for y_grad in range(screen_height):
            r = self.bg_color_top[0] + (self.bg_color_bottom[0] - self.bg_color_top[0]) * y_grad / screen_height
            g = self.bg_color_top[1] + (self.bg_color_bottom[1] - self.bg_color_top[1]) * y_grad / screen_height
            b = self.bg_color_top[2] + (self.bg_color_bottom[2] - self.bg_color_top[2]) * y_grad / screen_height
            pygame.draw.line(self.screen, (int(r), int(g), int(b)), (0, y_grad), (screen_width, y_grad))

        # Title
        title_surf = self.font_title.render("Configurações de Vídeo", True, self.title_color)
        title_rect = title_surf.get_rect(center=(screen_width // 2, screen_height // 4))
        self.screen.blit(title_surf, title_rect)

        # Subtitle with explanation
        subtitle_surf = self.font_options.render("Use as setas, mouse ou A/D para ajustar os valores", True, self.unselected_color)
        subtitle_rect = subtitle_surf.get_rect(center=(screen_width // 2, title_rect.bottom + 30))
        self.screen.blit(subtitle_surf, subtitle_rect)

        # Options and values
        option_labels = {
            "SCREEN_WIDTH": "Largura da Tela",
            "SCREEN_HEIGHT": "Altura da Tela",
            "FRAMERATE": "Taxa de Quadros (FPS)",
            "MOUSE_SENSITIVITY": "Sensibilidade do Mouse"
        }
        
        # Resetar o dicionário de retângulos dos botões
        self.button_rects = {}

        for i, key in enumerate(self.settings_items):
            option_y_pos = screen_height // 3 + 100 + i * 50
            option_color = self.selected_color if i == self.selected_option_index else self.unselected_color
            
            # Draw option name
            name_text_surf = self.font_options.render(f"{option_labels[key]}: ", True, option_color)
            name_text_rect = name_text_surf.get_rect(topleft=(screen_width // 2 - 300, option_y_pos))
            self.screen.blit(name_text_surf, name_text_rect)
            
            # Draw value or input box
            if self.editing_value and self.current_editing_key == key:
                # Draw input box with current text
                input_background = pygame.Rect(name_text_rect.right, option_y_pos - 5, 150, 40)
                pygame.draw.rect(self.screen, (50, 50, 70), input_background)
                pygame.draw.rect(self.screen, self.selected_color, input_background, 2)
                
                input_text_surf = self.font_values.render(self.input_text, True, self.value_color)
                input_text_rect = input_text_surf.get_rect(midleft=(name_text_rect.right + 10, option_y_pos + name_text_rect.height // 2))
                self.screen.blit(input_text_surf, input_text_rect)
            else:
                # Draw current value
                value_str = str(self.current_values[key])
                value_text_surf = self.font_values.render(value_str, True, self.value_color)
                value_text_rect = value_text_surf.get_rect(midleft=(name_text_rect.right + 10, option_y_pos + name_text_rect.height // 2))
                self.screen.blit(value_text_surf, value_text_rect)
                
                # Desenhar botões de decremento e incremento
                button_size = 30
                decrement_rect = pygame.Rect(value_text_rect.right + 20, option_y_pos, button_size, button_size)
                increment_rect = pygame.Rect(decrement_rect.right + 10, option_y_pos, button_size, button_size)
                
                # Armazenar os retângulos dos botões para verificação de cliques
                self.button_rects[key] = {
                    'decrement': decrement_rect,
                    'increment': increment_rect
                }
                
                # Desenhar botões
                pygame.draw.rect(self.screen, (50, 50, 70), decrement_rect, border_radius=5)
                pygame.draw.rect(self.screen, (80, 80, 100), decrement_rect, 2, border_radius=5)
                decrement_text = self.font_options.render("-", True, self.unselected_color)
                decrement_text_rect = decrement_text.get_rect(center=decrement_rect.center)
                self.screen.blit(decrement_text, decrement_text_rect)
                
                pygame.draw.rect(self.screen, (50, 50, 70), increment_rect, border_radius=5)
                pygame.draw.rect(self.screen, (80, 80, 100), increment_rect, 2, border_radius=5)
                increment_text = self.font_options.render("+", True, self.unselected_color)
                increment_text_rect = increment_text.get_rect(center=increment_rect.center)
                self.screen.blit(increment_text, increment_text_rect)

        # Draw back button only (no apply button)
        _, back_button_rect = self.get_button_rects()
        
        pygame.draw.rect(self.screen, (40, 40, 60), back_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, (50, 50, 70), back_button_rect, 2, border_radius=5)
        back_text = self.font_options.render("Voltar", True, self.unselected_color)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        self.screen.blit(back_text, back_text_rect)

        pygame.display.flip()

    def loop(self):
        self.running = True
        action = 'menu' # Default action if loop exits unexpectedly
        while self.running:
            dt = 1.0 / GAME_SETTINGS["FRAMERATE"] # Use game setting for framerate
            self.time += dt # For animations if any

            returned_action = self.handle_input()
            if returned_action: # If handle_input returned an action (e.g. 'menu')
                action = returned_action
                self.running = False # Exit options loop

            self.render()
            self.clock.tick(GAME_SETTINGS["FRAMERATE"]) # Control options menu framerate
        
        # Ensure screen is updated before returning to main menu, especially if resolution changed
        if GAME_SETTINGS["SCREEN_WIDTH"] != self.screen.get_width() or GAME_SETTINGS["SCREEN_HEIGHT"] != self.screen.get_height():
             pygame.display.set_mode((GAME_SETTINGS["SCREEN_WIDTH"], GAME_SETTINGS["SCREEN_HEIGHT"]))

        return action

class Game:
    def __init__(self):
        self.Terrain = Terrain()
        self.Data = Data()
        self.Shader = Shader()
        self.Model = Model()
        self.Sound = Sound()  # MODIFIED: Initialize Sound
        self.sky_dome_list = None  # Sky dome display list
        self.sun_display_list = None  # Sun display list
        self.cloud_display_lists = []  # Cloud display lists
        self.sky_color = (0.3, 0.5, 0.9)  # Sky blue color
        self.Player = Player(self.Terrain)
        self.clock = pygame.time.Clock()
        self.yaw = 0.0
        self.pitch = 0.0
        self.lava = Lava()
        self.instruments = []
        self.instrument_display_lists = {}  # Adicionado para armazenar display lists
        self.cloud_positions = []  # Posições das nuvens no céu
        self.cloud_movement = 0.0  # Para animar o movimento das nuvens
        self.beam_height = 1000.0  # Altura dos raios de luz que apontam para o céu
        self.beam_pulse_time = 0.0  # Tempo para efeito de pulsação dos raios
        self.running = True
        self.paused = False
        self.font = None
        self.pause_menu_selected = 0  # 0 = Resume, 1 = Return to Main Menu, 2 = Quit
        self.guitar_hero_minigame = None  # Minigame de Guitar Hero
        self.in_minigame = False  # Flag para indicar se está no minigame
        self.time = 0.0  # Adicionar atributo time para pulsação do menu
        self.game_over = False
        self.show_game_over_message = False
        self.game_over_message_start_time = 0
        self.lava_damage_per_second = 175 # MODIFICADO: Reduzido o dano da lava para 175 (era 350)
        self.health_font = None # Font for health text
        self.current_minigame_instrument = None # Reference to the instrument for current minigame
        self.instrument_sound_channel = None # Channel for instrument sound playback
        
        # Portal properties
        self.portal_display_list = None
        self.portal_pos = (505.0, 0.0, 525.0)  # Moved further back (z=525 instead of 517)
        self.portal_scale = (0.08, 0.08, 0.08)  # Much smaller scale
        self.portal_rotation = 0.0  # Fixed rotation (no longer animated)
        self.portal_active = False  # Portal começa desativado até coletar todos os instrumentos
        self.portal_texture_id = None  # Para armazenar o ID da textura do portal
        self.in_gg_screen = False  # Para controlar a tela GG
        self.gg_screen_start_time = 0  # Para temporizar a tela GG

        # --- Cutscene Attributes ---
        self.in_instrument_pickup_cutscene = False
        self.cutscene_instrument_animating = None # Stores the instrument object
        self.cutscene_start_time = 0.0
        self.cutscene_duration = 3.0  # MODIFIED: Increased duration for better visibility
        self.original_player_yaw = 0.0
        self.original_player_pitch = 0.0
        self.cutscene_target_camera_yaw = 0.0
        self.cutscene_target_camera_pitch = 0.0
        # Note: instrument's animated_pos and animated_scale will be stored in the instrument's dict directly
        # End Cutscene Attributes

        # Track if fail sound has been played
        self.fail_sound_played = False

        # Define difficulties for each instrument
        self.INSTRUMENT_DIFFICULTIES = {
            "MODEL_CRUMHORN": 0,  # Easy (was Hard)
            "MODEL_VUVUZELA": 1,   # Medium
            "MODEL_MANDOLINE": 2,   # Hard (was Easy)
            "MODEL_DIGERIDOO": 3    # Very Hard
        }
        self.instrument_icons = {} # To store loaded instrument icons

    def init(self):
        pygame.font.init()
        pygame.mixer.init()  # MODIFIED: Initialize mixer for sound
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)

        # --- START: Image-based Loading Screen ---
        glClearColor(0.1, 0.1, 0.1, 1.0) # Dark gray background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Setup for 2D rendering for loading screen
        glMatrixMode(GL_PROJECTION)
        glPushMatrix() # Save current projection matrix
        glLoadIdentity()
        gluOrtho2D(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0) # Y-axis down

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix() # Save current modelview matrix
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)

        # Load loading screen image
        loading_texture_id = None
        try:
            loading_surface = pygame.image.load('Images/loading_screen.png').convert_alpha()
            # Scale image to fit screen if needed
            loading_surface = pygame.transform.scale(loading_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
            loading_texture_data = pygame.image.tostring(loading_surface, "RGBA", True) # FLIPPED
            loading_texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, loading_texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, SCREEN_WIDTH, SCREEN_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, loading_texture_data)
        except pygame.error as e:
            print(f"Warning: Could not load Images/loading_screen.png: {e}. Falling back to plain background.")
            loading_texture_id = None

        def display_loading_screen():
            glClear(GL_COLOR_BUFFER_BIT)
            
            if loading_texture_id is not None:
                glBindTexture(GL_TEXTURE_2D, loading_texture_id)
                glColor4f(1.0, 1.0, 1.0, 1.0)
                glBegin(GL_QUADS)
                glTexCoord2f(0, 1); glVertex2f(0, 0)
                glTexCoord2f(1, 1); glVertex2f(SCREEN_WIDTH, 0)
                glTexCoord2f(1, 0); glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
                glTexCoord2f(0, 0); glVertex2f(0, SCREEN_HEIGHT)
                glEnd()
            
            pygame.display.flip()
            pygame.event.pump() # Process events to keep window responsive
            for event in pygame.event.get(): # Basic event handling to allow quit during loading
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Display loading screen and load assets
        display_loading_screen()
        self.Terrain.load(0)
        display_loading_screen()
        self.Data.load()
        display_loading_screen()
        self.Shader.load()
        display_loading_screen()
        self.Model.load()
        display_loading_screen()
        self.Sound.load()
        display_loading_screen()
        self.lava.load(TERRAIN_SIZE)
        display_loading_screen()
        
        # Load portal texture
        try:
            portal_texture_surface = pygame.image.load('Images/portal_texture.png').convert_alpha()
            portal_texture_data = pygame.image.tostring(portal_texture_surface, "RGBA", True)
            self.portal_texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.portal_texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, portal_texture_surface.get_width(), 
                         portal_texture_surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, portal_texture_data)
            print("Portal texture loaded successfully")
        except Exception as e:
            print(f"Warning: Could not load portal texture: {e}. Using default color instead.")
            # If texture fails to load, we'll use a default color in the render method
            self.portal_texture_id = None
        display_loading_screen()
        
        # Create display list for hands model after loading
        if 'MODEL_HAND_IDLE' in self.Model.models: 
            self.Model.create_display_list('MODEL_HAND_IDLE')
        else:
            print("Warning: MODEL_HAND_IDLE not loaded, cannot create display list for hands.")
        display_loading_screen()

        # Create display list for portal
        if 'MODEL_PORTAL' in self.Model.models:
            self.portal_display_list = glGenLists(1)
            glNewList(self.portal_display_list, GL_COMPILE)
            self.Model.draw('MODEL_PORTAL')
            glEndList()
            print("Portal model loaded successfully")
        else:
            print("Warning: MODEL_PORTAL not found, portal will not be displayed")
        display_loading_screen()

        # Clean up loading screen resources
        if loading_texture_id is not None:
            glDeleteTextures(1, [loading_texture_id])
        
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

        # Restore OpenGL state for 3D rendering
        glMatrixMode(GL_PROJECTION)
        glPopMatrix() # Restore original projection
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix() # Restore original modelview
        # --- END: Animated Loading Screen ---

        # --- START: Main 3D Scene Setup (Matrices, Lighting, etc.) ---
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, (SCREEN_WIDTH/SCREEN_HEIGHT), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity() 
        
        self.initialize_clouds()
        glEnable(GL_DEPTH_TEST)
        
        # Setup lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set default material properties
        mat_ambient = [0.2, 0.2, 0.2, 1.0]
        mat_diffuse = [0.8, 0.8, 0.8, 1.0]
        mat_specular = [0.5, 0.5, 0.5, 1.0]
        mat_shininess = [50.0]
        
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess)
        
        # We'll enable GL_NORMALIZE to ensure proper lighting with scaled objects
        glEnable(GL_NORMALIZE)
        
        # Create sky dome display list
        self.create_sky_dome()
        
        # Initialize font for pause menu
        self.font = pygame.font.Font(None, 36)
        try:
            self.health_font = pygame.font.SysFont('Arial', 20, bold=True)
        except:
            self.health_font = pygame.font.Font(None, 24) # Fallback font

        instrument_y_offset = 3.0
        instrument_scale = (1.5, 1.5, 1.5)
        crumhorn_y_offset = 1.5  # Y offset reduzido para o Crumhorn ficar mais próximo do chão

        player_initial_x = 500.0
        player_initial_z = 512.0
        
        # Distribuir instrumentos em pontos distantes do mapa em terreno elevado (longe da lava)
        # Usando coordenadas em diferentes quadrantes do mapa (TERRAIN_SIZE = 1024)
        self.instruments = [
            # Nordeste - longe do ponto inicial (em terreno mais elevado)
            {"id": "MODEL_CRUMHORN", "pos_xz": (882.36, 137.37), "y_offset": 0.8, "scale": instrument_scale, "collected": False, "flying": False, "color": (0.6, 0.4, 0.2), "shader_id": "PROGRAM_COMPLEX_CRUMHORN"},  # Área mais distante do jogador
            {"id": "MODEL_VUVUZELA", "pos_xz": (812.65, 792.25), "y_offset": instrument_y_offset, "scale": instrument_scale, "collected": False, "flying": False, "color": (1.0, 0.84, 0.0), "shader_id": "PROGRAM_COMPLEX_VUVUZELA"},
            # Noroeste - outro quadrante (em área montanhosa)
            {"id": "MODEL_DIGERIDOO", "pos_xz": (264.80, 861.17), "y_offset": instrument_y_offset, "scale": instrument_scale, "collected": False, "flying": False, "color": (0.4, 0.2, 0.05), "shader_id": "PROGRAM_COMPLEX_DIDGERIDOO"},
            # Sudoeste - nova posição para a mandolina
            {"id": "MODEL_MANDOLINE", "pos_xz": (418.78, 260.40), "y_offset": instrument_y_offset, "scale": instrument_scale, "collected": False, "flying": False, "color": (0.8, 0.3, 0.1), "shader_id": "PROGRAM_COMPLEX_MANDOLINE"},
        ]
        
        for instrument in self.instruments:
            x, z = instrument["pos_xz"]
            if x < 1: x = 1
            if x > TERRAIN_SIZE - 3: x = TERRAIN_SIZE - 3
            if z < 1: z = 1
            if z > TERRAIN_SIZE - 3: z = TERRAIN_SIZE - 3
            instrument["pos"] = (x, self.Terrain.get_vertex_height(x, z) + instrument["y_offset"], z)
        
        # Load instrument icons
        for instrument_data in self.instruments:
            instrument_id = instrument_data["id"]
            # Sanitize instrument_id for filename if needed, though current IDs are fine
            icon_path = f"Images/icon_{instrument_id}.png"
            try:
                icon_surface = pygame.image.load(icon_path).convert_alpha()
                icon_surface = pygame.transform.smoothscale(icon_surface, (35, 35)) # Scaled icon size
                self.instrument_icons[instrument_id] = icon_surface
            except pygame.error as e:
                self.instrument_icons[instrument_id] = None
                print(f"Warning: Could not load icon {icon_path} for {instrument_id}: {e}")
        
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        self.font = pygame.font.SysFont("Arial", 24)
        
        # Criar display lists para os instrumentos
        for instrument in self.instruments:
            self.instrument_display_lists[instrument["id"]] = glGenLists(1)
            glNewList(self.instrument_display_lists[instrument["id"]], GL_COMPILE)
            self.Model.draw(instrument["id"])
            glEndList()

        # Create day-night cycle
        self.day_night_cycle = 0.0  # 0.0 = noon, 0.5 = sunset/sunrise, 1.0 = midnight
        
        # Create sun and clouds
        self.create_sun()
        self.create_clouds()

    def loop(self):
        self.running = True
        while self.running:
            # Update cloud movement
            self.cloud_movement += 0.001
            
            # Calcular o delta time para atualizações
            dt = 1.0 / FRAMERATE
            
            # Atualizar o tempo para animações (incluindo pulsação do menu de pausa)
            self.time += dt
            self.beam_pulse_time += dt
            
            # Atualizar ciclo dia/noite
            self.day_night_cycle = (self.day_night_cycle + dt * 0.0025) % 1.0  # Ciclo completo a cada ~400 segundos
            
            mouse_pos = pygame.mouse.get_pos() # Get mouse_pos for pause menu even during cutscene hover
            mouse_clicked = False # Reset mouse_clicked each frame

            # --- Start of Segregated Event Handling ---
            if self.in_gg_screen:
                # Event handling for GG screen
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.running = False
                        return 'quit'
                    elif event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            # Sair da tela GG e voltar ao menu principal
                            return 'menu'
            elif self.in_minigame and self.guitar_hero_minigame:
                # Event handling for minigame
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.running = False
                        return 'quit'
                    elif event.type == KEYDOWN:
                        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                            self.guitar_hero_minigame.handle_key_press(event.key)
                        elif event.key == pygame.K_ESCAPE:
                            self.in_minigame = False
                            # Stop the instrument sound
                            self.stop_instrument_sound()
                            # Minigame exit should handle mouse visibility/grab
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif event.key == pygame.K_SPACE and self.guitar_hero_minigame.completed:
                            if self.guitar_hero_minigame.success:
                                # Use the saved instrument reference directly
                                if hasattr(self, 'current_minigame_instrument') and self.current_minigame_instrument:
                                    instrument = self.current_minigame_instrument
                                    if not instrument["collected"]:
                                        # Mark instrument as flying rather than immediately collected
                                        instrument["flying"] = True
                                        instrument["fly_start_time"] = time.time()
                                        instrument["fly_duration"] = 2.0  # Duration of flying animation in seconds
                                        # Save original position for animation
                                        instrument["fly_start_pos"] = list(instrument["pos"])
                                        # Save original scale if not already saved
                                        if "original_scale_for_anim" not in instrument:
                                            instrument["original_scale_for_anim"] = list(instrument["scale"])
                                        # Play pickup sound again for the final collection
                                        self.Sound.play(SOUND_PICKUP)
                                # Clear the reference
                                self.current_minigame_instrument = None
                            self.in_minigame = False
                            # Stop the instrument sound
                            self.stop_instrument_sound()
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                    # No MOUSEBUTTONDOWN or MOUSEMOTION specific to minigame in this section
                    # GuitarHeroMinigame.draw handles its own button interactions if any

            elif self.game_over:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.running = False
                        return 'quit'
                    elif event.type == KEYDOWN:
                        if event.key == pygame.K_ESCAPE: # Allow exit at any time with ESC
                            # Parar a música de game over antes de voltar ao menu
                            self.Sound.stop_lose_song()
                            return 'menu'
            
            elif self.paused:
                # Event handling for pause menu
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.running = False
                        return 'quit'
                    elif event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            self.paused = False
                            # Parar som do menu de pausa ao sair
                            self.Sound.stop_pause_menu_music()
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            self.pause_menu_selected = (self.pause_menu_selected - 1) % 3
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.pause_menu_selected = (self.pause_menu_selected + 1) % 3
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.pause_menu_selected == 0:  # Resume
                                self.paused = False
                                # Parar som do menu de pausa
                                self.Sound.stop_pause_menu_music()
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                            elif self.pause_menu_selected == 1:  # Options
                                # TODO: Options menu implementation
                                pass
                            elif self.pause_menu_selected == 2:  # Quit
                                # Parar som do menu de pausa
                                self.Sound.stop_pause_menu_music()
                                self.running = False
                                return 'menu'  # Return to main menu
                    elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                        mouse_clicked = True # Will be processed below by pause menu mouse logic
                
                # Pause menu mouse click logic (outside event loop but uses mouse_clicked and mouse_pos)
                options = ['Resume', 'Return to Main Menu', 'Quit']
                for i, option in enumerate(options):
                    # Recalculate text_rect for button collision
                    # (Simplified: assumes font is loaded, which it is by this point)
                    text_surf_for_rect = self.font.render(option, True, (0,0,0)) # Color doesn't matter for rect
                    text_rect_for_collision = text_surf_for_rect.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 -50 + i * 70)) # APPROXIMATION of pause menu layout
                    
                    # Use a more accurate button rect calculation if possible, this is simplified
                    button_width = 450 
                    button_height = 70
                    button_spacing = 30
                    start_y = SCREEN_HEIGHT // 2 - (len(options) * (button_height + button_spacing) - button_spacing) // 2 + 20
                    
                    button_actual_rect = pygame.Rect(
                        SCREEN_WIDTH // 2 - button_width // 2,
                        start_y + i * (button_height + button_spacing),
                        button_width,
                        button_height
                    )

                    if button_actual_rect.collidepoint(mouse_pos):
                        self.pause_menu_selected = i
                        if mouse_clicked:
                            if i == 0: # Resume
                                self.paused = False
                                # Parar som do menu de pausa ao sair
                                self.Sound.stop_pause_menu_music()
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                            elif i == 1: # Return to Main Menu
                                # Parar som do menu de pausa ao sair
                                self.Sound.stop_pause_menu_music()
                                return 'menu'
                            elif i == 2: # Quit
                                # Parar som do menu de pausa ao sair
                                self.Sound.stop_pause_menu_music()
                                self.running = False
                                return 'quit'
            
            else: # Normal Gameplay (not in cutscene, not in minigame, not game over, not paused)
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.running = False
                    elif event.type == KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.in_minigame and self.guitar_hero_minigame:
                                # Voltar ao jogo principal
                                self.in_minigame = False
                                # Stop the instrument sound
                                self.stop_instrument_sound()
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                                # Clear the current minigame instrument reference
                                self.current_minigame_instrument = None
                            else:
                                # Parar o som da lava ao pausar o jogo
                                self.Sound.stop_lava_sound()
                                # Parar o som de passos ao pausar o jogo
                                self.Sound.stop_walking()
                                # Toggle pause state
                                self.paused = not self.paused
                                if self.paused:
                                    # Pausar o jogo
                                    pygame.mouse.set_visible(True)
                                    pygame.event.set_grab(False)
                                    self.pause_menu_selected = 0  # Reset para "Resume"
                                    self.Sound.play(SOUND_PAUSEMENU)
                                else:
                                    # Despausar o jogo
                                    pygame.mouse.set_visible(False)
                                    pygame.event.set_grab(True)
                                self.Sound.stop_pause_menu_music()
                        elif event.key == K_e:
                            self.collect_instruments()
                        # No pause menu key navigation here, it's handled when self.paused is true
                    elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                        mouse_clicked = True # General click, not used by player movement
                    elif event.type == MOUSEMOTION and not self.paused and not self.in_minigame and not self.game_over: # Guarded
                        rel_x, rel_y = event.rel
                        sensitivity = MOUSE_SENSITIVITY  # Use global sensitivity setting
                        self.yaw += rel_x * sensitivity
                        self.pitch -= rel_y * sensitivity
                        self.pitch = max(-89.0, min(45.0, self.pitch))  # Limit upward view to 45 degrees
            # --- End of Segregated Event Handling ---


            # --- Start of Update Logic ---
            if self.in_minigame and self.guitar_hero_minigame:
                self.guitar_hero_minigame.update(dt)
            # Only update game state if not paused, not game_over, not in_gg_screen
            elif not self.paused and not self.game_over and not self.in_gg_screen:
                keys = pygame.key.get_pressed() # Get fresh state for continuous actions
                self.update_player(keys)
                
                # Atualizar instrumentos reposicionados
                self.update_repositioned_instruments(dt)
                
                # Update flying instruments
                self.update_flying_instruments()
                
                self.lava.update()
                
                if self.Player.y - RADIUS < self.lava.get_height():
                    # Verifica se este é o primeiro contato com a lava
                    if not hasattr(self, 'lava_contact_time') or not hasattr(self, 'in_lava'):
                        self.lava_contact_time = 0.0
                        self.in_lava = True
                        # Tocar o som imediatamente ao entrar na lava pela primeira vez
                        self.Sound.stop_lava_sound()  # Para garantir que não há nenhum som tocando
                        # Tocar o som da lava imediatamente
                        if SOUND_LAVASOUND in self.Sound.sounds:
                            self.Sound.lava_channel = self.Sound.sounds[SOUND_LAVASOUND].play()
                            if self.Sound.lava_channel:
                                self.Sound.lava_channel.set_volume(0.4)
                        self.Sound.lava_sound_timer = 0  # Reseta o timer
                    
                    # Aumenta o tempo de contato com a lava
                    self.lava_contact_time += dt
                    
                    # Fator de dano que aumenta gradualmente nos primeiros 2 segundos
                    damage_factor = min(1.0, self.lava_contact_time / 2.0)
                    
                    # Calcula o dano com o fator de redução
                    damage_taken = self.lava_damage_per_second * dt * damage_factor
                    self.Player.health -= damage_taken
                    self.Player.health = max(0, self.Player.health)
                    
                    # Continuar tocando o som da lava regularmente enquanto o jogador está na lava
                    self.Sound.play_lava_sound(dt)

                    if self.Player.health <= 0 and not self.game_over:
                        self.game_over = True
                        self.show_game_over_message = True
                        self.game_over_message_start_time = time.time()
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                        # Parar som da lava quando o jogador morre
                        self.Sound.stop_lava_sound()
                        # Parar som de passos quando o jogador morre
                        self.Sound.stop_walking()
                        # Tocar a música de game over
                        self.Sound.play_lose_song()
                else:
                    # Jogador saiu da lava
                    if hasattr(self, 'in_lava') and self.in_lava:
                        self.in_lava = False
                        self.Sound.stop_lava_sound()
                    
                    # Resetar o tempo de contato com a lava quando sair dela
                    if hasattr(self, 'lava_contact_time'):
                        self.lava_contact_time = 0.0
            # --- End of Update Logic ---

            # Verifique se é hora de voltar ao menu após a tela de game over
            if self.game_over and self.show_game_over_message and time.time() - self.game_over_message_start_time > 10.0:
                print("Tempo de exibição da tela Game Over atingido, voltando ao menu")
                # After 10 seconds, automatically return to menu
                # Parar a música de game over antes de voltar ao menu
                self.Sound.stop_lose_song()
                return 'menu'
            
            self.render()
            self.clock.tick(FRAMERATE)
        
        # Parar o som do menu de pausa se estiver tocando quando sair do jogo
        self.Sound.stop_pause_menu_music()
        # Também parar o som da lava se estiver tocando
        self.Sound.stop_lava_sound()
        # Parar a música de game over se estiver tocando
        self.Sound.stop_lose_song()
        # Parar o som de passos se estiver tocando
        self.Sound.stop_walking()
        return 'quit'  # Default return action

    # MODIFIED: Added method to handle instrument collection (cutscene removed)
    def collect_instruments(self):
        if self.in_minigame: # Don't try to collect if already in minigame
            return

        for instrument in self.instruments:
            if not instrument["collected"] and not instrument.get("flying", False): # Only consider uncollected instruments
                dx = instrument["pos"][0] - self.Player.x
                dz = instrument["pos"][2] - self.Player.z
                dist = math.hypot(dx, dz)

                if dist < COLLECTION_RADIUS:
                    # Play pickup sound
                    self.Sound.play(SOUND_PICKUP)
                    
                    # Start minigame directly (skip cutscene)
                    self.start_instrument_minigame(instrument)
                    break

    def start_instrument_pickup_cutscene(self, instrument):
        self.in_instrument_pickup_cutscene = True
        self.cutscene_instrument_animating = instrument
        self.cutscene_start_time = time.time()

        self.original_player_yaw = self.yaw
        self.original_player_pitch = self.pitch

        inst_pos = instrument["pos"]
        cam_eye_y = self.Player.y + 1.7 # Player's eye height relative to player's base y

        dx = inst_pos[0] - self.Player.x
        dy = inst_pos[1] - cam_eye_y 
        dz = inst_pos[2] - self.Player.z

        target_yaw_raw = math.degrees(math.atan2(dx, -dz))
        
        # Normalize yaw difference for smoother interpolation
        yaw_diff = (target_yaw_raw - self.original_player_yaw + 180) % 360 - 180
        self.cutscene_target_camera_yaw = self.original_player_yaw + yaw_diff

        horizontal_dist = math.hypot(dx, dz)
        if horizontal_dist < 0.01: 
            self.cutscene_target_camera_pitch = 90 if dy > 0 else -90
        else:
            self.cutscene_target_camera_pitch = math.degrees(math.atan2(dy, horizontal_dist))
        
        self.cutscene_target_camera_pitch = max(-89.0, min(89.0, self.cutscene_target_camera_pitch))

        instrument["animated_pos"] = list(instrument["pos"]) # Make a mutable copy
        instrument["animated_scale"] = list(instrument["scale"]) # Make a mutable copy
        
        # Save original position and scale for both cutscene and flying animations
        if "original_pos_for_anim" not in instrument:
            instrument["original_pos_for_anim"] = list(instrument["pos"])
        if "original_scale_for_anim" not in instrument:
            instrument["original_scale_for_anim"] = list(instrument["scale"])

        pygame.mouse.set_visible(True) 
        pygame.event.set_grab(False)

    def end_instrument_pickup_cutscene(self, skipped=False):
        self.in_instrument_pickup_cutscene = False
        instrument_that_was_animating = self.cutscene_instrument_animating
        self.cutscene_instrument_animating = None # Clear this first

        if instrument_that_was_animating:
            # Restore its scale in case it's not marked "collected" by minigame later
            # and needs to be re-rendered normally.
            # This might not be strictly necessary if minigame outcome handles collection state.
            instrument_that_was_animating["animated_scale"] = list(instrument_that_was_animating["original_scale_for_anim"])

            # Start the minigame for the instrument
            self.guitar_hero_minigame = GuitarHeroMinigame(instrument_that_was_animating["id"])
            difficulty = self.INSTRUMENT_DIFFICULTIES.get(instrument_that_was_animating["id"], 0)
            self.guitar_hero_minigame.difficulty = difficulty
            self.guitar_hero_minigame.apply_difficulty_settings()
            self.in_minigame = True
            
            # Mouse for minigame is usually visible and not grabbed.
            # GuitarHeroMinigame itself might manage this, but good to ensure here.
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        else: # If no instrument was animating (e.g. cutscene ended prematurely by other means)
            pygame.mouse.set_visible(False) # Default back to gameplay mouse state
            pygame.event.set_grab(True)


    def update_instrument_pickup_cutscene(self, dt):
        elapsed_time = time.time() - self.cutscene_start_time
        
        # Skip logic is now handled by event loop calling end_instrument_pickup_cutscene directly

        if elapsed_time >= self.cutscene_duration:
            self.end_instrument_pickup_cutscene()
            return

        progress = elapsed_time / self.cutscene_duration

        # Phase 1: Camera Turn (e.g., 0% to 50% of duration)
        cam_turn_duration_factor = 0.5 # Camera turn finishes halfway
        if progress < cam_turn_duration_factor:
            t_cam = progress / cam_turn_duration_factor
            eased_t_cam = ease_in_out_smooth(t_cam)
            self.yaw = lerp(self.original_player_yaw, self.cutscene_target_camera_yaw, eased_t_cam)
            self.pitch = lerp(self.original_player_pitch, self.cutscene_target_camera_pitch, eased_t_cam)
        else: 
            self.yaw = self.cutscene_target_camera_yaw
            self.pitch = self.cutscene_target_camera_pitch

        # Phase 2: Instrument Animation (e.g., 30% to 90% of duration)
        instrument_anim_start_factor = 0.25 
        instrument_anim_end_factor = 0.90 
        instrument = self.cutscene_instrument_animating

        if instrument and progress >= instrument_anim_start_factor and progress < instrument_anim_end_factor :
            # Normalize progress for instrument animation phase
            t_instr_norm = (progress - instrument_anim_start_factor) / (instrument_anim_end_factor - instrument_anim_start_factor)
            t_instr_norm = min(max(t_instr_norm, 0.0), 1.0) 
            
            eased_t_instr_pos = ease_in_quad(t_instr_norm) 
            eased_t_instr_scale = ease_out_quad(t_instr_norm)

            # Target position for instrument (approximate hand position in view)
            cam_x, cam_y_eye, cam_z = self.Player.x, self.Player.y + 1.7, self.Player.z 
            r_yaw = math.radians(self.yaw) 
            r_pitch = math.radians(self.pitch)

            # Normalized Look/Forward vector (F)
            look_dx = math.cos(r_pitch) * math.sin(r_yaw)
            look_dy = math.sin(r_pitch)
            look_dz = -math.cos(r_pitch) * math.cos(r_yaw)
            
            # Normalized Right vector (S) - purely horizontal
            cam_right_x = math.sin(r_yaw + math.pi / 2)
            # cam_right_y = 0
            cam_right_z = -math.cos(r_yaw + math.pi / 2)

            # Normalized Up vector (U) = S x F
            # S = (cam_right_x, 0, cam_right_z)
            # F = (look_dx, look_dy, look_dz)
            # U_x = S_y*F_z - S_z*F_y = 0*look_dz - cam_right_z*look_dy
            up_dx = -cam_right_z * look_dy
            # U_y = S_z*F_x - S_x*F_z
            up_dy = cam_right_z * look_dx - cam_right_x * look_dz
            # U_z = S_x*F_y - S_y*F_x = cam_right_x*look_dy - 0*look_dx
            up_dz = cam_right_x * look_dy
            
            # Target offsets in view space (from hand model's local transform)
            # Hands model is translated by (0.15, 0.2, -0.7) in its own view space.
            # This means:
            # - 0.15 units to the right of camera center
            # - 0.2 units above camera center
            # - 0.7 units in front of camera (along negative Z view axis)
            
            offset_right = 0.15  # Corresponds to hand model's X translation
            offset_up = 0.2     # Corresponds to hand model's Y translation
            offset_forward = 0.70 # Corresponds to - (hand model's Z translation)

            # Calculate target world position: P_world = Eye_world + offset_right * S_world + offset_up * U_world + offset_forward * F_world
            target_pos_x = cam_x     + offset_right * cam_right_x + offset_up * up_dx + offset_forward * look_dx
            target_pos_y = cam_y_eye + offset_right * 0           + offset_up * up_dy + offset_forward * look_dy # cam_right_y is 0 for S_world
            target_pos_z = cam_z     + offset_right * cam_right_z + offset_up * up_dz + offset_forward * look_dz
            instrument_target_pos = (target_pos_x, target_pos_y, target_pos_z)
            
            instrument_final_scale = (0.01, 0.01, 0.01) # Very small

            instrument["animated_pos"] = lerp_vec3(instrument["original_pos_for_anim"], instrument_target_pos, eased_t_instr_pos)
            instrument["animated_scale"] = lerp_vec3(instrument["original_scale_for_anim"], instrument_final_scale, eased_t_instr_scale)
        
        elif instrument and progress >= instrument_anim_end_factor: # After animation window, ensure it's at final state
            # (This part might not be strictly needed if end_instrument_pickup_cutscene is called, 
            #  but good for ensuring final state if animation ends slightly before cutscene_duration)
            instrument["animated_scale"] = (0.01, 0.01, 0.01) # Keep it small / hidden


    # Add new method to render the pause menu
    def render_pause_menu(self, surface):
        # Dark semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Black with 180 alpha (0-255)
        surface.blit(overlay, (0, 0))
        
        # --- Title Styling ---
        try:
            # Usar uma fonte mais impactante e mais visível
            title_font_name = 'Arial Black'
            pause_title_font = pygame.font.SysFont(title_font_name, 110, bold=True)
        except:
            # Fallback para Arial ou fonte padrão
            try:
                pause_title_font = pygame.font.SysFont('arial', 100, bold=True)
            except:
                pause_title_font = pygame.font.Font(None, 110)
        
        title_text_content = 'GAME PAUSED'
        title_color = (255, 255, 0)  # Amarelo brilhante para melhor visibilidade
        outline_color = (0, 0, 0)    # Contorno preto para contraste

        # Efeito de sombra para melhorar a visibilidade
        shadow_offset = 5  # Aumentado
        shadow_color = (50, 50, 50)
        for offset_x, offset_y in [(shadow_offset, shadow_offset), 
                                    (-shadow_offset, shadow_offset), 
                                    (shadow_offset, -shadow_offset), 
                                    (-shadow_offset, -shadow_offset)]:
            title_surf_shadow = pause_title_font.render(title_text_content, True, shadow_color)
            title_rect_shadow = title_surf_shadow.get_rect(center=(SCREEN_WIDTH // 2 + offset_x, SCREEN_HEIGHT // 4 + offset_y))
            surface.blit(title_surf_shadow, title_rect_shadow)
        
        # Contorno mais grosso para o texto - aumentando offsets e adicionando mais posições
        outline_offsets = [
            (5, 0), (-5, 0), (0, 5), (0, -5),  # Contorno principal mais grosso
            (4, 4), (-4, 4), (4, -4), (-4, -4),  # Diagonais principais
            (3, 5), (5, 3), (-3, 5), (-5, 3), (3, -5), (5, -3), (-3, -5), (-5, -3),  # Posições adicionais
            (2, 5), (5, 2), (-2, 5), (-5, 2), (2, -5), (5, -2), (-2, -5), (-5, -2)   # Para contorno ainda mais completo
        ]
        
        for offset_x, offset_y in outline_offsets:
            title_surf_outline = pause_title_font.render(title_text_content, True, outline_color)
            title_rect_outline = title_surf_outline.get_rect(center=(SCREEN_WIDTH // 2 + offset_x, SCREEN_HEIGHT // 4 + offset_y))
            surface.blit(title_surf_outline, title_rect_outline)
        
        # Texto principal
        title_surf = pause_title_font.render(title_text_content, True, title_color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        surface.blit(title_surf, title_rect)
        
        # --- Button Styling & Layout ---
        button_font_size = 48
        try:
            button_font = pygame.font.SysFont('arial', button_font_size)
        except:
            button_font = pygame.font.Font(None, button_font_size + 6) # Default fallback with slight size increase

        options = ['Resume', 'Return to Main Menu', 'Quit']
        button_width = 450
        button_height = 70
        button_spacing = 30 # Space between buttons
        start_y = SCREEN_HEIGHT // 2 - (len(options) * (button_height + button_spacing) - button_spacing) // 2 + 20 # Center block vertically

        base_button_color = (70, 70, 90, 220)       # Dark grayish blue, slightly transparent
        highlight_button_color = (100, 100, 130, 255) # Lighter blue for highlight
        selected_button_color = (120, 60, 180, 255)   # Purple for selection confirmed by pulse
        text_color = (230, 230, 230)               # Light gray for text
        selected_text_color = (255, 255, 0)        # Yellow for selected text
        button_border_radius = 15

        for i, option_text in enumerate(options):
            button_y = start_y + i * (button_height + button_spacing)
            button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - button_width // 2,
                button_y,
                button_width,
                button_height
            )

            current_button_bg_color = base_button_color
            current_text_color = text_color

            # Check for mouse hover for visual feedback (distinct from keyboard selection)
            mouse_pos = pygame.mouse.get_pos()
            is_hovered = button_rect.collidepoint(mouse_pos)

            if i == self.pause_menu_selected:
                current_text_color = selected_text_color
                # Pulsing effect for the selected button (keyboard focus)
                smoothFactor = (1 - math.cos(self.time * 2.5)) / 2 # Faster pulse
                pulse_intensity = 0.15 
                pulse_r = int(selected_button_color[0] + (255 - selected_button_color[0]) * smoothFactor * pulse_intensity)
                pulse_g = int(selected_button_color[1] + (255 - selected_button_color[1]) * smoothFactor * pulse_intensity)
                pulse_b = int(selected_button_color[2] + (255 - selected_button_color[2]) * smoothFactor * pulse_intensity)
                current_button_bg_color = (pulse_r, pulse_g, pulse_b, selected_button_color[3])
                
                # Draw a border or stronger highlight for keyboard-selected item
                pygame.draw.rect(surface, (255, 255, 100, 180), button_rect.inflate(10, 10), border_radius=button_border_radius + 5)
            elif is_hovered:
                current_button_bg_color = highlight_button_color # Hover color if not keyboard selected

            # Draw the button background
            pygame.draw.rect(surface, current_button_bg_color, button_rect, border_radius=button_border_radius)
            
            # Render and draw text
            text_surf = button_font.render(option_text, True, current_text_color)
            text_rect = text_surf.get_rect(center=button_rect.center)
            surface.blit(text_surf, text_rect)
        
        # --- Controls Hint ---
        hint_font_size = 28
        try:
            hint_font = pygame.font.SysFont('arial', hint_font_size)
        except:
            hint_font = pygame.font.Font(None, hint_font_size + 4)

        hint_text_content = 'Use W/S or Arrow Keys to Navigate, Enter/Space to Select'
        hint_color = (180, 180, 180, 200) # Light gray with some transparency
        
        hint_surf = hint_font.render(hint_text_content, True, hint_color)
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        surface.blit(hint_surf, hint_rect)

    def update_player(self, keys):
        # Calcular vetores de direção baseados na orientação da câmera
        r_yaw_camera = math.radians(self.yaw)
        
        # Vetor para frente (direção da câmera no plano XZ)
        forward_x = math.sin(r_yaw_camera)
        forward_z = -math.cos(r_yaw_camera)
        
        # Vetor para direita (perpendicular à direção da câmera no plano XZ)
        right_x = math.sin(r_yaw_camera + math.pi/2)
        right_z = -math.cos(r_yaw_camera + math.pi/2)

        move_x_dir = 0.0
        move_z_dir = 0.0
        current_player_speed = PLAYER_SPEED # Renomeado para clareza
        is_running = False
        
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            current_player_speed *= 3
            is_running = True
            
        if keys[pygame.K_w]:
            move_x_dir += forward_x
            move_z_dir += forward_z
        if keys[pygame.K_s]:
            move_x_dir -= forward_x
            move_z_dir -= forward_z
        if keys[pygame.K_a]:
            move_x_dir -= right_x
            move_z_dir -= right_z
        if keys[pygame.K_d]:
            move_x_dir += right_x
            move_z_dir += right_z

        # Verificar se o jogador está se movendo para gerenciar o som de passos
        is_moving = math.hypot(move_x_dir, move_z_dir) > 0
        
        # Gerencia o som de passos baseado no movimento e no estado do chão
        if is_moving and self.Player.on_ground:
            # Só inicia o som de passos se não estiver andando ainda
            if not self.Sound.is_walking:
                self.Sound.start_walking()
            
            # Chama play_walk_sound em cada frame para manter o som consistente
            self.Sound.play_walk_sound(1.0 / FRAMERATE, is_running)
        else:
            # Para o som se o jogador parou ou está no ar
            if self.Sound.is_walking:
                self.Sound.stop_walking()
        
        length = math.hypot(move_x_dir, move_z_dir)
        if length > 0:
            move_x_dir /= length
            move_z_dir /= length
            
        # Movimento horizontal pretendido
        intended_vx = move_x_dir * current_player_speed
        intended_vz = move_z_dir * current_player_speed
        
        # Lógica de verificação de inclinação
        final_vx = intended_vx
        final_vz = intended_vz

        if math.hypot(intended_vx, intended_vz) > 0.001: # Se houver movimento horizontal significativo
            next_player_x = self.Player.x + intended_vx
            next_player_z = self.Player.z + intended_vz

            # Garante que as coordenadas para get_height_bicubic estejam dentro dos limites seguros
            safe_current_player_x = max(1.0, min(self.Player.x, TERRAIN_SIZE - 3.0))
            safe_current_player_z = max(1.0, min(self.Player.z, TERRAIN_SIZE - 3.0))
            safe_next_player_x = max(1.0, min(next_player_x, TERRAIN_SIZE - 3.0))
            safe_next_player_z = max(1.0, min(next_player_z, TERRAIN_SIZE - 3.0))
            
            current_terrain_y = self.Terrain.get_height_bicubic(safe_current_player_x, safe_current_player_z)
            next_terrain_y = self.Terrain.get_height_bicubic(safe_next_player_x, safe_next_player_z)
            
            delta_y = next_terrain_y - current_terrain_y
            delta_xz = math.hypot(intended_vx, intended_vz)

            if delta_xz > 0.0001: # Evitar divisão por zero
                slope = delta_y / delta_xz
                if slope > MAX_CLIMB_SLOPE and delta_y > 0: # Tentando subir uma encosta muito íngreme
                    final_vx = 0.0
                    final_vz = 0.0
        
        self.Player.vx = final_vx # Define a velocidade horizontal efetiva do jogador
        self.Player.vz = final_vz
        
        # Lógica de pulo e gravidade
        if keys[pygame.K_SPACE] and self.Player.on_ground:
            self.Player.vy = JUMP_SPEED
            self.Player.on_ground = False
            # Tocar som de salto
            self.Sound.play_bounce(vol=0.6)
            
        self.Player.vy -= GRAVITY # Aplica gravidade
        
        # Atualiza a posição do jogador usando as velocidades processadas
        new_x = self.Player.x + self.Player.vx
        new_z = self.Player.z + self.Player.vz
        
        # Margem de segurança para impedir que o jogador saia do terreno
        # Adicionamos o RADIUS para considerar o tamanho do jogador
        border_margin = RADIUS + 0.5  # Margem adicional para evitar problemas de precisão
        
        # Verifica se a nova posição está dentro dos limites do terreno
        if new_x < border_margin:
            new_x = border_margin
            self.Player.vx = 0  # Para o movimento nesta direção
        elif new_x > TERRAIN_SIZE - border_margin:
            new_x = TERRAIN_SIZE - border_margin
            self.Player.vx = 0  # Para o movimento nesta direção
            
        if new_z < border_margin:
            new_z = border_margin
            self.Player.vz = 0  # Para o movimento nesta direção
        elif new_z > TERRAIN_SIZE - border_margin:
            new_z = TERRAIN_SIZE - border_margin
            self.Player.vz = 0  # Para o movimento nesta direção
        
        # Atualiza a posição com os valores corrigidos
        self.Player.x = new_x
        self.Player.y += self.Player.vy
        self.Player.z = new_z
        
        # Colisão com o chão e ajuste de altura
        # Usa as coordenadas X, Z finais do jogador para calcular ground_y
        final_player_safe_x = max(1.0, min(self.Player.x, TERRAIN_SIZE - 3.0))
        final_player_safe_z = max(1.0, min(self.Player.z, TERRAIN_SIZE - 3.0))
        ground_y = self.Terrain.get_height_bicubic(final_player_safe_x, final_player_safe_z) + RADIUS
        
        if self.Player.y <= ground_y:
            self.Player.y = ground_y
            self.Player.vy = 0
            self.Player.on_ground = True
        else:
            self.Player.on_ground = False

        # Print player coordinates if moved
        current_pos = (self.Player.x, self.Player.y, self.Player.z)
        if current_pos != self.Player._last_pos:
            self.Player._last_pos = current_pos
            
        # Verificar colisão com o portal
        if self.portal_active and not self.in_gg_screen:
            portal_x, portal_y, portal_z = self.portal_pos
            # Calcular distância do jogador ao portal
            dx = self.Player.x - portal_x
            dz = self.Player.z - portal_z
            dy = self.Player.y - portal_y
            
            # Distância no plano XZ
            dist_xz = math.sqrt(dx*dx + dz*dz)
            
            # Escala do portal para determinar o raio de colisão
            portal_radius = 0.5 * max(self.portal_scale)  # Metade do tamanho para o raio
            
            # Se o jogador estiver próximo o suficiente do portal
            if dist_xz < portal_radius * 4 and abs(dy) < 2.0:  # Multiplicado por 4 para aumentar a área de colisão
                # Ativar a tela GG imediatamente quando tocar o portal
                self.in_gg_screen = True
                self.gg_screen_start_time = time.time()
                
                # Desativar controles do jogador durante a tela GG
                self.Player.vx = 0
                self.Player.vz = 0
                
                # Parar todos os sons ativos
                self.Sound.stop_lava_sound()
                self.Sound.stop_walking()
                
                # Tocar som para o final do jogo
                self.Sound.play(SOUND_PICKUP)  # Usar um som existente
        
        # Verificar se os instrumentos reposicionados estão próximos
        # Agora é tratado no método update_repositioned_instruments

    def draw_light_beam(self, x, y, z, r, g, b, beam_height_factor=1.0):
        """Desenha um raio de luz colorido que aponta para o céu com efeito de pulsação"""
        beam_width = 1.2  # Largura do raio aumentada
        
        # Ajustar a posição inicial do raio para ficar acima do instrumento
        # e evitar que atravesse o modelo
        y_offset = 2.5  # Altura acima do instrumento para iniciar o raio
        beam_start_y = y + y_offset
        
        # Calcular o fator de pulsação com amplitude maior e frequência ajustada
        pulse_factor = 0.3 + 0.7 * math.sin(self.beam_pulse_time * 3.0)  # Pulsação mais intensa (0.3 a 1.0)
        
        # Ajustar a transparência e intensidade da cor com base na pulsação
        alpha_base = 0.5 + 0.4 * pulse_factor  # Varia entre 0.5 e 0.9 (mais visível)
        alpha_top = 0.2 + 0.3 * pulse_factor  # Varia entre 0.2 e 0.5 (mais visível no topo)
        
        # Ajustar a intensidade da cor com base na pulsação
        color_intensity = 0.8 + 0.4 * pulse_factor  # Intensidade da cor varia com a pulsação
        r_base = r * color_intensity
        g_base = g * color_intensity
        b_base = b * color_intensity
        
        # No need to disable lighting since it's already disabled globally
        
        # Configurar transparência
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Modo aditivo para efeito de brilho
        
        # Desenhar o raio de luz como um prisma quadrangular
        glBegin(GL_QUADS)
        
        # Definir cor com transparência (último valor é alpha)
        glColor4f(r_base, g_base, b_base, alpha_base)
        # Base do raio (acima do instrumento)
        glVertex3f(x - beam_width/2, beam_start_y, z - beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y, z - beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y, z + beam_width/2)
        glVertex3f(x - beam_width/2, beam_start_y, z + beam_width/2)
        
        # Topo do raio (no céu)
        # A cor no topo é mais clara e mais transparente
        adjusted_beam_height = self.beam_height * beam_height_factor
        glColor4f(r_base + 0.3, g_base + 0.3, b_base + 0.3, alpha_top)
        glVertex3f(x - beam_width/2, beam_start_y + adjusted_beam_height, z - beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y + adjusted_beam_height, z - beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y + adjusted_beam_height, z + beam_width/2)
        glVertex3f(x - beam_width/2, beam_start_y + adjusted_beam_height, z + beam_width/2)
        
        # Lados do raio
        glColor4f(r_base, g_base, b_base, alpha_base)
        # Lado 1
        glVertex3f(x - beam_width/2, beam_start_y, z - beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y, z - beam_width/2)
        glColor4f(r_base + 0.3, g_base + 0.3, b_base + 0.3, alpha_top)
        glVertex3f(x + beam_width/2, beam_start_y + adjusted_beam_height, z - beam_width/2)
        glVertex3f(x - beam_width/2, beam_start_y + adjusted_beam_height, z - beam_width/2)
        
        glColor4f(r_base, g_base, b_base, alpha_base)
        # Lado 2
        glVertex3f(x + beam_width/2, beam_start_y, z - beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y, z + beam_width/2)
        glColor4f(r_base + 0.3, g_base + 0.3, b_base + 0.3, alpha_top)
        glVertex3f(x + beam_width/2, beam_start_y + adjusted_beam_height, z + beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y + adjusted_beam_height, z - beam_width/2)
        
        glColor4f(r_base, g_base, b_base, alpha_base)
        # Lado 3
        glVertex3f(x + beam_width/2, beam_start_y, z + beam_width/2)
        glVertex3f(x - beam_width/2, beam_start_y, z + beam_width/2)
        glColor4f(r_base + 0.3, g_base + 0.3, b_base + 0.3, alpha_top)
        glVertex3f(x - beam_width/2, beam_start_y + adjusted_beam_height, z + beam_width/2)
        glVertex3f(x + beam_width/2, beam_start_y + adjusted_beam_height, z + beam_width/2)
        
        glColor4f(r_base, g_base, b_base, alpha_base)
        # Lado 4
        glVertex3f(x - beam_width/2, beam_start_y, z + beam_width/2)
        glVertex3f(x - beam_width/2, beam_start_y, z - beam_width/2)
        glColor4f(r_base + 0.3, g_base + 0.3, b_base + 0.3, alpha_top)
        glVertex3f(x - beam_width/2, beam_start_y + adjusted_beam_height, z - beam_width/2)
        glVertex3f(x - beam_width/2, beam_start_y + adjusted_beam_height, z + beam_width/2)
        
        glEnd()
        
        # Restaurar configurações
        glDisable(GL_BLEND)
        # No need to enable lighting
        glColor3f(1.0, 1.0, 1.0)

    def create_sky_dome(self):
        # Create a sky dome display list with gradient colors
        self.sky_dome_list = glGenLists(1)
        glNewList(self.sky_dome_list, GL_COMPILE)
        
        # Draw a large hemisphere for the sky
        radius = 1000.0
        slices = 32
        stacks = 16
        
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + (i - 1) / stacks)
            z0  =  radius * math.sin(lat0)
            zr0 =  radius * math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + i / stacks)
            z1 = radius * math.sin(lat1)
            zr1 = radius * math.cos(lat1)
            
            # Calculate color gradient for this stack
            # Top of dome is more vibrant, horizon is lighter
            factor_0 = (i - 1) / stacks  # 0 at top, 1 at horizon
            factor_1 = i / stacks
            
            # Bright blue at top fading to lighter blue/white at horizon
            r0 = 0.4 + 0.6 * factor_0
            g0 = 0.6 + 0.4 * factor_0
            b0 = 1.0
            
            r1 = 0.4 + 0.6 * factor_1
            g1 = 0.6 + 0.4 * factor_1
            b1 = 1.0
            
            glBegin(GL_QUAD_STRIP)
            
            for j in range(slices + 1):
                longt = 2 * math.pi * j / slices
                x = math.cos(longt)
                y = math.sin(longt)
                
                # Set color for each vertex
                glColor3f(r0, g0, b0)
                glVertex3f(x * zr0, z0, y * zr0)
                
                glColor3f(r1, g1, b1)
                glVertex3f(x * zr1, z1, y * zr1)
            
            glEnd()
        
        glEndList()
        
    def create_sun(self):
        # Create a sun display list with a visible yellow sphere
        self.sun_display_list = glGenLists(1)
        glNewList(self.sun_display_list, GL_COMPILE)
        
        # Draw a yellow sphere for the sun
        glColor3f(1.0, 1.0, 0.7)  # Bright yellow/white
        quadric = gluNewQuadric()
        gluSphere(quadric, 90.0, 32, 32)  # Large sphere for the sun
        
        glEndList()
    
    def initialize_clouds(self):
        # Inicializar posições aleatórias para as nuvens
        self.cloud_positions = []
        num_clouds = 15  # Número de nuvens no céu
        
        for _ in range(num_clouds):
            # Posição aleatória no céu
            angle = np.random.uniform(0, 2 * math.pi)
            distance = np.random.uniform(300, 800)  # Distância do centro
            height = np.random.uniform(250, 500)    # Altura acima do horizonte - INCREASED
            scale = np.random.uniform(30, 100)      # Tamanho da nuvem
            
            x = math.cos(angle) * distance
            z = math.sin(angle) * distance
            y = height
            
            self.cloud_positions.append({
                'pos': (x, y, z),
                'scale': scale,
                'speed': np.random.uniform(0.2, 1.0)  # Velocidade de movimento
            })
    
    def create_clouds(self):
        # Create cloud display lists
        self.cloud_display_lists = []
        
        # Criar diferentes formas de nuvens
        for _ in range(3):  # 3 tipos diferentes de nuvens
            cloud_list = glGenLists(1)
            glNewList(cloud_list, GL_COMPILE)
            
            # Desenhar uma nuvem como conjunto de esferas brancas
            num_puffs = np.random.randint(3, 7)  # Número de "puffs" na nuvem
            
            for i in range(num_puffs):
                # Posição relativa de cada puff
                x_offset = np.random.uniform(-0.8, 0.8)
                y_offset = np.random.uniform(-0.3, 0.3)
                z_offset = np.random.uniform(-0.8, 0.8)
                size = np.random.uniform(0.5, 1.0)  # Tamanho relativo do puff
                
                glPushMatrix()
                glTranslatef(x_offset, y_offset, z_offset)
                glColor4f(1.0, 1.0, 1.0, 0.8)  # Branco com transparência
                
                # Desenhar esfera para o puff
                quadric = gluNewQuadric()
                gluSphere(quadric, size, 12, 12)
                
                glPopMatrix()
            
            glEndList()
            self.cloud_display_lists.append(cloud_list)

    def render(self):
        # Se estiver na tela GG, renderizar apenas ela
        if self.in_gg_screen:
            print("Renderizando tela GG (tela de conclusão do jogo)")
            self.render_gg_screen()
            return
            
        # Se estiver no minigame, renderizar a interface 2D do Guitar Hero
        # No need to deactivate shader since we're not using them
        if self.in_minigame and self.guitar_hero_minigame:
            # Criar uma superfície temporária para desenhar o minigame
            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            
            # Desenhar o minigame ou a tela de resultados
            if self.guitar_hero_minigame.completed:
                if self.guitar_hero_minigame.success:
                    self.guitar_hero_minigame.draw_results(temp_surface)
                else:
                    # Make sure instrument sound is stopped immediately at failure
                    if not self.fail_sound_played:
                        # Stop the instrument sound first
                        self.stop_instrument_sound()
                        # Then play the fail sound
                        self.Sound.play(SOUND_FAIL)
                        self.fail_sound_played = True
                    
                    # Load and display the fail image when player fails
                    try:
                        fail_img = pygame.image.load('Images/fail.png')
                        # Stretch to fill entire screen
                        fail_img = pygame.transform.scale(fail_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                        temp_surface.blit(fail_img, (0, 0))
                        
                        # Add instruction text at bottom of screen
                        instruction_font = pygame.font.Font(None, 36)
                        instruction_text = instruction_font.render("Press ESC or SPACE to continue", True, (255, 255, 255))
                        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
                        temp_surface.blit(instruction_text, instruction_rect)
                    except pygame.error as e:
                        print(f"Error loading fail.png: {e}")
                        # Fallback to original results display if image can't be loaded
                        self.guitar_hero_minigame.draw_results(temp_surface)
            else:
                self.guitar_hero_minigame.draw(temp_surface)
            
            # Corrigir inversão vertical do texto
            temp_surface = pygame.transform.flip(temp_surface, False, True)
            
            # Converter a superfície para um formato que o OpenGL possa usar
            # Salvar o estado atual do OpenGL
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            
            # Desabilitar recursos 3D
            glDisable(GL_DEPTH_TEST)
            # No lighting to disable
            
            # Limpar a tela
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Converter a superfície pygame para uma textura OpenGL
            texture_data = pygame.image.tostring(temp_surface, "RGBA", 1)
            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, SCREEN_WIDTH, SCREEN_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
            
            # Desenhar a textura como um quad na tela
            glEnable(GL_TEXTURE_2D)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(0, 0)
            glTexCoord2f(1, 0); glVertex2f(SCREEN_WIDTH, 0)
            glTexCoord2f(1, 1); glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
            glTexCoord2f(0, 1); glVertex2f(0, SCREEN_HEIGHT)
            glEnd()
            glDisable(GL_TEXTURE_2D)
            
            # Deletar a textura
            glDeleteTextures(1, [texture_id])
            
            # Restaurar o estado do OpenGL
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            
            # Reabilitar recursos 3D
            glEnable(GL_DEPTH_TEST)
            # No lighting to enable
            
            # Atualizar a tela
            pygame.display.flip()
            return
        
        # Renderização normal do jogo 3D
        # Calculate sky color based on time of day
        if self.day_night_cycle < 0.5:  # Day
            factor = 1.0 - abs(self.day_night_cycle - 0.25) * 4.0  # Brightest at noon
            sky_r = 0.3 + 0.2 * factor  # Blue sky
            sky_g = 0.5 + 0.2 * factor
            sky_b = 0.9 * factor
            # Cores mais vibrantes durante o dia
            sky_r = min(0.4 + 0.3 * factor, 0.7)  # Azul mais vibrante
            sky_g = min(0.6 + 0.3 * factor, 0.9)
            sky_b = min(1.0 * factor, 1.0)
        else:  # Night
            factor = 1.0 - abs(self.day_night_cycle - 0.75) * 4.0  # Darkest at midnight
            sky_r = 0.02 + 0.1 * factor  # Dark blue night sky
            sky_g = 0.02 + 0.1 * factor
            sky_b = 0.1 + 0.2 * factor
            # Adicionar um tom roxo/azulado à noite
            sky_r = 0.05 + 0.1 * factor
            sky_g = 0.05 + 0.05 * factor
            sky_b = 0.2 + 0.2 * factor
        
        glClearColor(sky_r, sky_g, sky_b, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        cx, cy, cz = self.Player.x, self.Player.y + 1.7, self.Player.z
        r_yaw_camera = math.radians(self.yaw)
        r_pitch_camera = math.radians(self.pitch)
        
        dx_camera_look = math.cos(r_pitch_camera) * math.sin(r_yaw_camera)
        dy_camera_look = math.sin(r_pitch_camera)
        dz_camera_look = -math.cos(r_pitch_camera) * math.cos(r_yaw_camera)
        
        gluLookAt(cx, cy, cz,
                 cx + dx_camera_look, cy + dy_camera_look, cz + dz_camera_look,
                 0, 1, 0)

        # Draw sky dome centered on camera
        glPushMatrix()
        glTranslatef(cx, cy - 50, cz)  # Position dome below the camera to create horizon effect
        # Sky doesn't need lighting
        glCallList(self.sky_dome_list)
        
        # Setup directional light from static sun position
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # Position the sun at a fixed position in the sky (high up and slightly to the side)
        sun_x, sun_y, sun_z = 500.0, 800.0, -500.0
        
        # Set up light position as directional (w=0.0 for directional light)
        glLightfv(GL_LIGHT0, GL_POSITION, [sun_x, sun_y, sun_z, 0.0])
        
        # Set light colors
        ambient_light = [0.3, 0.3, 0.3, 1.0]  # Ambient light level
        diffuse_light = [1.0, 0.95, 0.8, 1.0]  # Slightly yellowish sunlight
        specular_light = [0.8, 0.8, 0.8, 1.0]  # Specular component
        
        glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse_light)
        glLightfv(GL_LIGHT0, GL_SPECULAR, specular_light)
        
        # Draw the sun at the light position
        glPushMatrix()
        glTranslatef(sun_x, sun_y, sun_z)
        glDisable(GL_LIGHTING)  # Disable lighting for the sun itself so it appears bright
        glDisable(GL_DEPTH_TEST)  # Ensure sun is always visible
        glCallList(self.sun_display_list)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glPopMatrix()
        
        # Draw clouds
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        for i, cloud in enumerate(self.cloud_positions):
            x, y, z = cloud['pos']
            scale = cloud['scale']
            speed = cloud['speed']
            
            # Mover nuvens lentamente pelo céu
            angle = math.atan2(z, x) + speed * self.cloud_movement
            distance = math.sqrt(x*x + z*z)
            
            new_x = math.cos(angle) * distance
            new_z = math.sin(angle) * distance
            
            glPushMatrix()
            glTranslatef(new_x, y, new_z)
            glScalef(scale, scale * 0.5, scale)  # Achatamento vertical para parecer mais com nuvens
            
            # Usar um dos modelos de nuvem aleatoriamente
            cloud_model = self.cloud_display_lists[i % len(self.cloud_display_lists)]
            glCallList(cloud_model)
            
            glPopMatrix()
        
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)  # Disable lighting after sky elements
        glPopMatrix()

        # Re-enable lighting for terrain and objects
        glEnable(GL_LIGHTING)
        
        # Draw lava directly without shader
        self.lava.draw(self.Data.get_id("IMG_LAVA"), None)
        
        glEnable(GL_TEXTURE_2D)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.Data.get_id("IMG_GRASS"))
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.Data.get_id("IMG_ROCK"))
        glActiveTexture(GL_TEXTURE0)
        
        # Restore terrain shader for rocks
        self.Shader.activate("PROGRAM_SIMPLE_TERRAIN")
        self.Shader.set_uniform("tex_top", 0)
        self.Shader.set_uniform("tex_side", 1)
        self.Shader.set_uniform("height", self.lava.get_height())
        self.Shader.set_uniform("hmax", self.lava.get_height_max())
        self.Terrain.draw(self.Data)
        self.Shader.deactivate()
        glDisable(GL_TEXTURE_2D)
        
        # Draw portal near player spawn
        if self.portal_display_list and self.portal_active:
            # Get terrain height at portal position for proper placement
            portal_x, _, portal_z = self.portal_pos
            portal_y = self.Terrain.get_height_bicubic(portal_x, portal_z) + 0.01  # Almost at ground level (was 0.1)
            
            # Update portal position with correct height
            self.portal_pos = (portal_x, portal_y, portal_z)
            
            # Draw fixed portal (no rotation updates)
            glPushMatrix()
            glTranslatef(portal_x, portal_y, portal_z)
            glRotatef(self.portal_rotation, 0, 1, 0)  # Fixed rotation angle
            glScalef(self.portal_scale[0], self.portal_scale[1], self.portal_scale[2])
            
            # Apply texture if available
            if self.portal_texture_id:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, self.portal_texture_id)
            
            # Draw with solid color, no transparency
            glDisable(GL_LIGHTING)
            
            # Use opaque rendering with normal blending 
            # (only for glow effect if no texture)
            if not self.portal_texture_id:
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                
                # Pulse glow effect
                glow_intensity = 0.5 + 0.3 * math.sin(self.time * 2.0)
                glColor4f(0.2, 0.6, 1.0, 1.0)  # Solid blue color
            else:
                # If texture is available, use white color without blending
                glColor3f(1.0, 1.0, 1.0)  # White color for texture
            
            # Draw portal
            if self.portal_display_list:
                glCallList(self.portal_display_list)
            
            # Clean up states
            if self.portal_texture_id:
                glDisable(GL_TEXTURE_2D)
            glDisable(GL_BLEND)
            glEnable(GL_LIGHTING)
            glColor3f(1.0, 1.0, 1.0)  # Reset color
            glPopMatrix()
        
        # Draw instrument shadows first (before drawing the instruments)
        for instrument in self.instruments:
            if not instrument["collected"] and not instrument.get("flying", False):
                # Scale factor for shadow based on instrument scale
                shadow_scale = sum(instrument["scale"]) / 3.0 * 1.5  # Avg scale * 1.5
                
                if self.in_instrument_pickup_cutscene and self.cutscene_instrument_animating and self.cutscene_instrument_animating["id"] == instrument["id"]:
                    # Use animated position for shadow during cutscene and adjust shadow scale
                    cutscene_progress = (time.time() - self.cutscene_start_time) / self.cutscene_duration
                    if cutscene_progress < 0.9:  # Only draw shadow during first 90% of animation 
                        anim_shadow_scale = sum(instrument["animated_scale"]) / 3.0 * 1.5
                        self.draw_instrument_shadow(
                            instrument["animated_pos"][0], 
                            instrument["animated_pos"][1], 
                            instrument["animated_pos"][2],
                            anim_shadow_scale,
                            instrument["id"]  # Pass the instrument ID for accurate shadow shape
                        )
                else:
                    # Draw regular shadow for non-animated instruments
                    self.draw_instrument_shadow(
                        instrument["pos"][0], 
                        instrument["pos"][1], 
                        instrument["pos"][2],
                        shadow_scale,
                        instrument["id"]  # Pass the instrument ID for accurate shadow shape
                    )
        
        # Desenhar os raios de luz para instrumentos não coletados e não voando
        glDisable(GL_LIGHTING)  # Disable lighting for the beams (they provide their own colors)
        
        # Find the next instrument to collect (uncollected one with the lowest difficulty)
        next_instrument_to_collect = None
        lowest_difficulty = float('inf')
        
        for inst in self.instruments:
            if not inst["collected"] and not inst.get("flying", False):
                # Check difficulty level of this instrument
                inst_difficulty = self.INSTRUMENT_DIFFICULTIES.get(inst["id"], 999)  # Default high value if not found
                if inst_difficulty < lowest_difficulty:
                    lowest_difficulty = inst_difficulty
                    next_instrument_to_collect = inst
        
        # Only draw beam for the next instrument to collect (easiest one)
        if next_instrument_to_collect:
            x, y, z = next_instrument_to_collect["pos"]
            r, g, b = next_instrument_to_collect["color"]
            self.draw_light_beam(x, y, z, r, g, b)
            
        # Still draw beams for flying instruments (currently being collected)
        for instrument in self.instruments:
            if instrument.get("flying", False):
                # Draw a special beam effect for flying instruments
                x, y, z = instrument["pos"]
                r, g, b = instrument["color"]
                
                # Make the beam brighter and larger for flying instruments
                r = min(1.0, r + 0.3)
                g = min(1.0, g + 0.3)
                b = min(1.0, b + 0.3)
                
                # Calculate beam effect based on flying progress
                elapsed_time = time.time() - instrument.get("fly_start_time", time.time())
                progress = min(1.0, elapsed_time / instrument.get("fly_duration", 1.0))
                
                # Draw shorter beam that fades as the instrument flies away
                fade_factor = 1.0 - progress
                if fade_factor > 0.1:  # Only draw if still visible
                    self.draw_light_beam(x, y, z, r, g, b, beam_height_factor=fade_factor * 1.5)
        glEnable(GL_LIGHTING)  # Re-enable lighting for instruments

        # Setup enhanced lighting model for instruments (Phong lighting)
        # Set OpenGL to use Phong lighting model (GL_LIGHT_MODEL_LOCAL_VIEWER for proper specular highlights)
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
        
        # Enable color material to allow per-vertex colors to work with lighting
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Enable lighting for instruments
        for instrument in self.instruments:
            if not instrument["collected"]:
                self.Shader.activate(instrument["shader_id"])
                glPushMatrix()
                glTranslatef(instrument["pos"][0], instrument["pos"][1], instrument["pos"][2])
                
                # Aplicar rotação própria para instrumentos reposicionados
                if instrument.get("repositioned", False) and "self_rotation" in instrument:
                    glRotatef(instrument["self_rotation"], 0, 1, 0)  # Rotação no eixo Y
                
                glScalef(instrument["scale"][0], instrument["scale"][1], instrument["scale"][2])
                glCallList(self.instrument_display_lists[instrument["id"]])  # Usar display list
                glPopMatrix()
                self.Shader.deactivate()
        
        # Reset lighting settings
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_FALSE)
        glColor3f(1.0, 1.0, 1.0)
        glDisable(GL_LIGHTING)  # Disable lighting for 2D elements

        # --- Render 2D elements (FPS counter and pause menu if paused) ---
        fps = self.clock.get_fps()
        
        # Criar uma superfície Pygame para elementos 2D
        screen_surface = pygame.display.get_surface()
        pygame_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Renderizar o FPS na superfície Pygame
        fps_text = self.font.render(f"FPS: {fps:.1f}", True, (255, 255, 0))
        pygame_surface.blit(fps_text, (10, 10))
        
        # --- Render "Find the Instrument" HUD --- 
        if not self.game_over and not self.paused: # Only show when playing
            next_instrument_to_find = None
            for inst in self.instruments:
                if not inst["collected"]:
                    next_instrument_to_find = inst
                    break

            icon_x_offset = 20 # Initial X position for elements
            hud_y_position = SCREEN_HEIGHT - 70 # MODIFIED: Lowered HUD Y position

            if next_instrument_to_find:
                instrument_id_str = next_instrument_to_find["id"]
                instrument_name = instrument_id_str.replace("MODEL_", "").replace("_", " ").title()
                
                find_text_content = f"Find: {instrument_name}"
                find_text_font = self.font # Using existing game font (Arial 24)
                find_text_surf = find_text_font.render(find_text_content, True, (255, 223, 0)) # Gold-ish color

                current_x = icon_x_offset
                icon_to_draw = self.instrument_icons.get(instrument_id_str)
                # text_y_position = 20 # Top padding for the HUD elements # REMOVED, using hud_y_position

                if icon_to_draw:
                    icon_rect = icon_to_draw.get_rect(topleft=(current_x, hud_y_position))
                    pygame_surface.blit(icon_to_draw, icon_rect)
                    current_x = icon_rect.right + 10 # Add padding between icon and text
                
                text_rect = find_text_surf.get_rect(topleft=(current_x, hud_y_position))
                # Adjust text to be vertically centered with icon if icon was drawn
                if icon_to_draw:
                    text_rect.centery = icon_rect.centery
                
                pygame_surface.blit(find_text_surf, text_rect)

            elif all(inst["collected"] for inst in self.instruments):
                all_collected_font = self.font
                all_collected_surf = all_collected_font.render("All instruments collected!", True, (0, 255, 0)) # Green color
                all_collected_rect = all_collected_surf.get_rect(topleft=(icon_x_offset, hud_y_position))
                pygame_surface.blit(all_collected_surf, all_collected_rect)
        # --- End "Find the Instrument" HUD ---

        # Render Health Bar
        health_bar_width = 250
        health_bar_height = 25
        # Increased padding from screen edges
        health_bar_x = SCREEN_WIDTH - health_bar_width - 30 
        health_bar_y = 30 
        
        # Background of health bar (darker red)
        pygame.draw.rect(pygame_surface, (80, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        
        # Current health (vibrant green)
        current_health_percentage = self.Player.health / self.Player.max_health
        current_health_width = current_health_percentage * health_bar_width
        
        health_color = (0, 220, 0) # Vibrant green
        if current_health_percentage < 0.3: # If health is low, change color to red
            health_color = (220, 0, 0)
        elif current_health_percentage < 0.6: # If health is medium, change color to yellow
            health_color = (220, 220, 0)

        if current_health_width > 0: # Draw only if health is positive
             pygame.draw.rect(pygame_surface, health_color, (health_bar_x, health_bar_y, current_health_width, health_bar_height))
        
        # Border for health bar (slightly thicker and brighter)
        pygame.draw.rect(pygame_surface, (220, 220, 220), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 3)

        # Health text (positioned below the bar, left-aligned)
        health_text_content = f"{int(self.Player.health)}/{self.Player.max_health}"
        health_text_surf = self.health_font.render(health_text_content, True, (255, 255, 255)) # White text
        # Align text to the left of the health bar
        text_x = health_bar_x 
        # Position text below the health bar with a small margin
        text_y = health_bar_y + health_bar_height + 5 
        pygame_surface.blit(health_text_surf, (text_x, text_y))


        # Render "You Lost" message if game is over
        if self.game_over and self.show_game_over_message:
            print("Renderizando tela de Game Over (jogador perdeu)")
            self.render_game_over_screen(pygame_surface)
        
        # Render pause menu if game is paused
        if self.paused:
            self.render_pause_menu(pygame_surface)
        
        # Inverter a superfície para corrigir a orientação ao desenhar como textura OpenGL
        pygame_surface = pygame.transform.flip(pygame_surface, False, True)
        
        # Converter a superfície Pygame para uma textura OpenGL
        # Salvar o estado atual do OpenGL
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Desabilitar recursos 3D
        glDisable(GL_DEPTH_TEST)
        # No lighting to disable
        
        # Converter a superfície pygame para uma textura OpenGL
        texture_data = pygame.image.tostring(pygame_surface, "RGBA", 1)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, SCREEN_WIDTH, SCREEN_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        # Desenhar a textura como um quad na tela
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(SCREEN_WIDTH, 0)
        glTexCoord2f(1, 1); glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
        glTexCoord2f(0, 1); glVertex2f(0, SCREEN_HEIGHT)
        glEnd()
        
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        
        # Deletar a textura
        glDeleteTextures(1, [texture_id])
        
        # Restaurar o estado do OpenGL
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        # Reabilitar recursos 3D
        glEnable(GL_DEPTH_TEST)
        # No lighting to enable

        pygame.display.flip()

    def draw_instrument_shadow(self, x, y, z, scale_factor=1.0, instrument_id=None):
        """Creates a shadow that matches the actual shape of the instrument by projecting it onto the ground"""
        if not instrument_id:
            return  # Need instrument_id to create proper shadow

        # Find ground height at instrument position
        ground_y = self.Terrain.get_height_bicubic(x, z)
        
        # Calculate light direction from sun position
        sun_x, sun_y, sun_z = 500.0, 800.0, -500.0  # Same as in render()
        
        # Vector from instrument to light source
        light_dir_x = sun_x - x
        light_dir_y = sun_y - y
        light_dir_z = sun_z - z
        
        # Normalize the light direction
        length = math.sqrt(light_dir_x**2 + light_dir_y**2 + light_dir_z**2)
        if length > 0:
            light_dir_x /= length
            light_dir_y /= length
            light_dir_z /= length
        
        # Calculate offset for shadow (prevents z-fighting)
        shadow_y_offset = 0.01
        
        # Set up shadow rendering state
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        
        # Calculate shadow alpha based on sun height
        # Higher sun = darker shadow
        shadow_alpha = max(0.3, min(0.7, 0.7 - light_dir_y * 0.4))
        
        # Handle case when light is almost horizontal (to prevent extreme projections)
        if abs(light_dir_y) < 0.1:
            # Fall back to a simple scaled disc shadow when the sun is near the horizon
            glPushMatrix()
            glTranslatef(x, ground_y + shadow_y_offset, z)
            glColor4f(0.0, 0.0, 0.0, shadow_alpha)
            
            # Draw a simple disc shadow as fallback
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0, 0, 0)  # center
            
            segments = 32
            shadow_radius = 1.5 * scale_factor
            for i in range(segments + 1):
                angle = 2.0 * math.pi * i / segments
                x_pos = math.cos(angle) * shadow_radius
                z_pos = math.sin(angle) * shadow_radius
                glVertex3f(x_pos, 0, z_pos)
            glEnd()
            glPopMatrix()
        else:
            # Calculate shadow projection point
            # This is where the light ray from the instrument intersects the ground
            # Ground is at y = ground_y, light ray starts at (x,y,z) and goes in direction (-light_dir_x, -light_dir_y, -light_dir_z)
            # Parameter t for ray: point = (x,y,z) + t * (-light_dir_x, -light_dir_y, -light_dir_z)
            # When y component = ground_y: y + t * (-light_dir_y) = ground_y
            # Solve for t: t = (y - ground_y) / light_dir_y
            t = (y - ground_y) / light_dir_y
            
            shadow_x = x - t * light_dir_x
            shadow_z = z - t * light_dir_z
            
            # Create a matrix transform that will flatten the object
            glPushMatrix()
            
            # Position at the shadow projection point
            glTranslatef(shadow_x, ground_y + shadow_y_offset, shadow_z)
            
            # Flatten the object along the Y-axis and scale it
            glScalef(scale_factor, 0.01, scale_factor)
            
            # Render the shadow in black with transparency
            glColor4f(0.0, 0.0, 0.0, shadow_alpha)
            
            # Draw the instrument model as shadow
            glCallList(self.instrument_display_lists[instrument_id])
            
            glPopMatrix()
        
        # Restore rendering state
        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)
        glColor3f(1.0, 1.0, 1.0)

    def update_flying_instruments(self):
        """Updates the animation of instruments that are in the flying state"""
        current_time = time.time()
        
        for instrument in self.instruments:
            if instrument.get("flying", False) and not instrument.get("collected", False):
                # Calculate animation progress
                elapsed_time = current_time - instrument["fly_start_time"]
                progress = min(1.0, elapsed_time / instrument["fly_duration"])
                
                # If animation is complete, mark as collected and stop flying
                if progress >= 1.0:
                    instrument["collected"] = True
                    instrument["flying"] = False
                    
                    # Verificar se todos os instrumentos foram coletados para ativar o portal
                    self.check_all_instruments_collected()
                    
                    continue
                
                # Apply easing for smoother animation
                eased_progress = ease_out_quad(progress)
                
                # Get starting position and calculate flight path
                start_x, start_y, start_z = instrument["fly_start_pos"]
                
                # Target: fly upward and spin
                target_y = start_y + 30.0  # Fly up by 30 units
                
                # Update position - moving upward
                instrument["pos"] = (
                    start_x,
                    lerp(start_y, target_y, eased_progress),
                    start_z
                )
                
                # Add rotation effect - store in instrument dict if not already there
                if "fly_rotation" not in instrument:
                    instrument["fly_rotation"] = 0.0
                
                # Increase rotation speed as the instrument flies up
                rotation_speed = 720.0  # Degrees per second (2 full rotations)
                instrument["fly_rotation"] += rotation_speed * (1.0 / FRAMERATE)
                
                # Scale down as it flies up and disappears
                scale_factor = 1.0 - eased_progress
                instrument["scale"] = (
                    instrument["original_scale_for_anim"][0] * scale_factor,
                    instrument["original_scale_for_anim"][1] * scale_factor, 
                    instrument["original_scale_for_anim"][2] * scale_factor
                )
    
    def check_all_instruments_collected(self):
        """Verifica se todos os instrumentos foram coletados e reposiciona-os no spawn do jogador"""
        all_collected = True
        for instrument in self.instruments:
            if not instrument.get("collected", False):
                all_collected = False
                break
                
        # Se todos os instrumentos foram coletados, reposicioná-los no spawn
        if all_collected and not hasattr(self, 'instruments_repositioned'):
            self.instruments_repositioned = True
            # Desativar o portal, vamos usar os instrumentos agora
            self.portal_active = False
            
            # Ponto de spawn do jogador
            spawn_x, spawn_z = 500.0, 512.0
            spawn_y = self.Terrain.get_height_bicubic(spawn_x, spawn_z) + 3.0  # Altura acima do terreno
            
            # Configurar os instrumentos para girarem em círculo no spawn
            radius = 5.0  # Raio do círculo
            for i, instrument in enumerate(self.instruments):
                # Ângulo inicial baseado no índice do instrumento (distribuir uniformemente)
                angle = (i / len(self.instruments)) * 2 * math.pi
                
                # Configurar instrumento para exibição no spawn
                instrument["collected"] = False  # Torná-lo visível novamente
                instrument["repositioned"] = True  # Marcar como reposicionado
                instrument["rotation_angle"] = angle  # Ângulo para posicionamento no círculo
                instrument["rotation_speed"] = 0.2 + (i * 0.05)  # Velocidade de rotação, varia por instrumento
                instrument["hover_offset"] = 0.0  # Para animação de flutuação
                instrument["hover_speed"] = 0.5 + (i * 0.1)  # Velocidade de flutuação
                instrument["scale"] = (1.0, 1.0, 1.0)  # Escala normal
                
                # Calcular posição inicial no círculo
                x = spawn_x + math.cos(angle) * radius
                z = spawn_z + math.sin(angle) * radius
                instrument["pos"] = (x, spawn_y, z)
            
            # Tocar som para o reposicionamento
            self.Sound.play(SOUND_PICKUP)

    def update_repositioned_instruments(self, dt):
        """Atualiza a animação dos instrumentos reposicionados"""
        if not hasattr(self, 'instruments_repositioned') or not self.instruments_repositioned:
            return
            
        # Ponto de spawn do jogador
        spawn_x, spawn_z = 500.0, 512.0
        spawn_y = self.Terrain.get_height_bicubic(spawn_x, spawn_z) + 3.0
        
        # Raio do círculo
        radius = 5.0
        
        # Atualizar cada instrumento
        for instrument in self.instruments:
            if instrument.get("repositioned", False):
                # Atualizar ângulo de rotação
                instrument["rotation_angle"] += instrument["rotation_speed"] * dt
                
                # Atualizar offset de flutuação
                instrument["hover_offset"] = math.sin(self.time * instrument["hover_speed"]) * 0.5
                
                # Calcular nova posição
                angle = instrument["rotation_angle"]
                x = spawn_x + math.cos(angle) * radius
                z = spawn_z + math.sin(angle) * radius
                y = spawn_y + instrument["hover_offset"]
                
                # Atualizar posição
                instrument["pos"] = (x, y, z)
                
                # Fazer o instrumento girar sobre seu próprio eixo
                if "self_rotation" not in instrument:
                    instrument["self_rotation"] = 0.0
                instrument["self_rotation"] += 120.0 * dt  # 120 graus por segundo
        
        # Verificar se o jogador está próximo do centro
        dx = self.Player.x - spawn_x
        dz = self.Player.z - spawn_z
        distance = math.sqrt(dx*dx + dz*dz)
        
        # Se o jogador estiver próximo do centro (dentro do raio do círculo)
        if distance < radius * 1.5 and not self.in_gg_screen:
            # Ativar a tela GG
            self.in_gg_screen = True
            self.gg_screen_start_time = time.time()
            
            # Desativar controles do jogador durante a tela GG
            self.Player.vx = 0
            self.Player.vz = 0
            
            # Parar todos os sons ativos
            self.Sound.stop_lava_sound()
            self.Sound.stop_walking()
            
            # Tocar som para o final do jogo
            self.Sound.play(SOUND_PICKUP)

    def render_gg_screen(self):
        """Renderiza a tela 'GG' quando o jogador entra no portal ou se aproxima dos instrumentos"""
        # Criar uma superfície temporária para desenhar a tela GG
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        try:
            # Tentar carregar e exibir a imagem gg.png
            print("Tentando carregar gg.png para a tela GG")
            # Tentar caminho absoluto e relativo
            img_path = os.path.join(os.getcwd(), 'Images', 'gg.png')
            print(f"Tentando caminho absoluto: {img_path}")
            
            if os.path.exists(img_path):
                gg_img = pygame.image.load(img_path)
            else:
                print("Caminho absoluto não encontrado, tentando caminho relativo")
                gg_img = pygame.image.load('Images/gg.png')
                
            # Redimensionar para preencher toda a tela
            gg_img = pygame.transform.scale(gg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            temp_surface.blit(gg_img, (0, 0))
            print("gg.png carregado com sucesso na tela GG")
            
            # Calcular tempo desde que a tela GG foi ativada
            elapsed_time = time.time() - self.gg_screen_start_time
            remaining_time = max(0, 10 - elapsed_time)
            
            # Adicionar texto de instrução na parte inferior da tela
            try:
                instruction_font = pygame.font.SysFont("Arial", 40)
            except:
                instruction_font = pygame.font.Font(None, 50)
            
            if remaining_time > 0:
                instruction_text = instruction_font.render(
                    f"Voltando ao menu em {int(remaining_time)} segundos... (ESC para sair)", 
                    True, (255, 255, 255)
                )
            else:
                instruction_text = instruction_font.render("Voltando ao menu...", True, (255, 255, 255))
                
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            temp_surface.blit(instruction_text, instruction_rect)
            
        except pygame.error as e:
            print(f"ERRO AO CARREGAR gg.png na tela GG: {e}")
            print(f"Caminho atual: {os.getcwd()}")
            # Fallback para o método original caso a imagem não seja encontrada
            
            # Preencher o fundo com gradiente roxo-escuro para preto
            for y in range(SCREEN_HEIGHT):
                # Calcular cor do gradiente - mais roxo no topo, mais escuro embaixo
                factor = 1.0 - (y / SCREEN_HEIGHT)
                r = int(80 * factor)
                g = int(0 * factor)
                b = int(100 * factor)
                pygame.draw.line(temp_surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
                
            # Calcular tempo desde que a tela GG foi ativada
            elapsed_time = time.time() - self.gg_screen_start_time
            
            # Fonte para o texto GG
            try:
                gg_font = pygame.font.SysFont("Arial Black", 200, bold=True)
            except:
                gg_font = pygame.font.Font(None, 240)
                
            # Renderizar "FIM!" com efeito pulsante
            pulse_factor = 1.0 + 0.2 * math.sin(elapsed_time * 3.0)
            
            # Texto principal
            gg_text = gg_font.render("FIM!", True, (255, 100, 255))
            gg_text = pygame.transform.scale(gg_text, 
                                            (int(gg_text.get_width() * pulse_factor), 
                                            int(gg_text.get_height() * pulse_factor)))
            gg_rect = gg_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            
            # Sombra do texto
            shadow_offset = 10
            shadow_text = gg_font.render("FIM!", True, (40, 0, 40))
            shadow_text = pygame.transform.scale(shadow_text, 
                                                (int(shadow_text.get_width() * pulse_factor), 
                                                int(shadow_text.get_height() * pulse_factor)))
            shadow_rect = shadow_text.get_rect(center=(SCREEN_WIDTH//2 + shadow_offset, 
                                                    SCREEN_HEIGHT//2 - 50 + shadow_offset))
            
            # Desenhar primeiro a sombra, depois o texto principal
            temp_surface.blit(shadow_text, shadow_rect)
            temp_surface.blit(gg_text, gg_rect)
            
            # Subtexto
            try:
                subtitle_font = pygame.font.SysFont("Arial", 40)
            except:
                subtitle_font = pygame.font.Font(None, 50)
                
            subtitle_text = subtitle_font.render("Você completou o jogo! Pressione ESC para sair", True, (200, 200, 200))
            subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150))
            temp_surface.blit(subtitle_text, subtitle_rect)
        
        # Corrigir inversão vertical do texto
        temp_surface = pygame.transform.flip(temp_surface, False, True)
        
        # Configurar OpenGL para renderização 2D
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Desabilitar recursos 3D
        glDisable(GL_DEPTH_TEST)
        
        # Limpar a tela
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Converter a superfície pygame para uma textura OpenGL
        texture_data = pygame.image.tostring(temp_surface, "RGBA", 1)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, SCREEN_WIDTH, SCREEN_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        # Desenhar a textura como um quad na tela
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(SCREEN_WIDTH, 0)
        glTexCoord2f(1, 1); glVertex2f(SCREEN_WIDTH, SCREEN_HEIGHT)
        glTexCoord2f(0, 1); glVertex2f(0, SCREEN_HEIGHT)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        
        # Deletar a textura
        glDeleteTextures(1, [texture_id])
        
        # Restaurar o estado do OpenGL
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        
        # Atualizar a tela
        pygame.display.flip()

    def start_instrument_minigame(self, instrument):
        """Start the Guitar Hero minigame directly for an instrument"""
        # Save reference to the instrument for later
        self.current_minigame_instrument = instrument
        
        # Reset fail sound flag
        self.fail_sound_played = False
        
        # Create and configure the minigame
        self.guitar_hero_minigame = GuitarHeroMinigame(instrument["id"])
        difficulty = self.INSTRUMENT_DIFFICULTIES.get(instrument["id"], 0)
        self.guitar_hero_minigame.difficulty = difficulty
        self.guitar_hero_minigame.apply_difficulty_settings()
        
        # Play the corresponding instrument sound
        instrument_id = instrument["id"]
        instrument_sound = None
        
        if instrument_id == "MODEL_MANDOLINE" and SOUND_MANDOLINE in self.Sound.sounds:
            instrument_sound = SOUND_MANDOLINE
        elif instrument_id == "MODEL_VUVUZELA" and SOUND_VUVUZELA in self.Sound.sounds:
            instrument_sound = SOUND_VUVUZELA
        elif instrument_id == "MODEL_CRUMHORN" and SOUND_CRUMHORN in self.Sound.sounds:
            instrument_sound = SOUND_CRUMHORN
        elif instrument_id == "MODEL_DIGERIDOO" and SOUND_DIGERIDOO in self.Sound.sounds:
            instrument_sound = SOUND_DIGERIDOO
            
        if instrument_sound:
            # Play the instrument sound with continuous looping
            sound_channel = self.Sound.sounds[instrument_sound].play(loops=-1)
            if sound_channel:
                # Set volume to an appropriate level
                sound_channel.set_volume(0.7)
                # Store the channel to stop it later
                self.instrument_sound_channel = sound_channel
        
        # Set minigame flag and prepare UI
        self.in_minigame = True
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        
    def stop_instrument_sound(self):
        """Stop the instrument sound that's playing during a minigame."""
        if self.instrument_sound_channel and self.instrument_sound_channel.get_busy():
            self.instrument_sound_channel.stop()
        self.instrument_sound_channel = None

    def render_game_over_screen(self, surface):
        """Renderiza a tela de fim de jogo com a imagem gg.png"""
        try:
            # Carregar e exibir a imagem de game over
            print("Tentando carregar gg.png para a tela de Game Over")
            # Tentar caminho absoluto e relativo
            img_path = os.path.join(os.getcwd(), 'Images', 'gg.png')
            print(f"Tentando caminho absoluto: {img_path}")
            
            if os.path.exists(img_path):
                game_over_img = pygame.image.load(img_path)
            else:
                print("Caminho absoluto não encontrado, tentando caminho relativo")
                game_over_img = pygame.image.load('Images/gg.png')
                
            # Redimensionar para preencher toda a tela
            game_over_img = pygame.transform.scale(game_over_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            surface.blit(game_over_img, (0, 0))
            print("gg.png carregado com sucesso na tela de Game Over")
            
            # Adicionar texto de instrução na parte inferior da tela
            instruction_font = pygame.font.Font(None, 36)
            
            # Determinar o texto de instrução baseado no tempo
            elapsed_time = time.time() - self.game_over_message_start_time
            remaining_time = max(0, 10 - elapsed_time)
            
            if remaining_time > 0:
                instruction_text = instruction_font.render(
                    f"Voltando ao menu em {int(remaining_time)} segundos... (ESC para sair)", 
                    True, (255, 255, 255)
                )
            else:
                instruction_text = instruction_font.render("Voltando ao menu...", True, (255, 255, 255))
                
            instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            surface.blit(instruction_text, instruction_rect)
            
        except pygame.error as e:
            print(f"ERRO AO CARREGAR gg.png na tela de Game Over: {e}")
            print(f"Caminho atual: {os.getcwd()}")
            print(f"Conteúdo da pasta Images: {os.listdir('Images') if os.path.exists('Images') else 'Pasta não encontrada'}")
            # Fallback para a exibição original de game over caso a imagem não possa ser carregada
            try:
                game_over_font = pygame.font.SysFont('arial', 100, bold=True)
            except:
                game_over_font = pygame.font.Font(None, 120)
            
            lost_text_surf = game_over_font.render("You Lost!", True, (255, 50, 50))
            lost_text_rect = lost_text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Simple black outline for better visibility
            outline_color = (0,0,0)
            positions = [(-2, -2), (2, -2), (-2, 2), (2, 2), (-2,0), (2,0), (0,-2), (0,2)]
            for pos_off in positions:
                outline_surf = game_over_font.render("You Lost!", True, outline_color)
                outline_rect = outline_surf.get_rect(center=(lost_text_rect.centerx + pos_off[0], lost_text_rect.centery + pos_off[1]))
                surface.blit(outline_surf, outline_rect)

            surface.blit(lost_text_surf, lost_text_rect)

            # Optional: Hint to press ESC or wait
            hint_font = self.font # Reuse existing font
            hint_text_content = "Returning to menu..."
            if time.time() - self.game_over_message_start_time < 3.0: # If still within the 3s window for ESC
                hint_text_content = "Press ESC or wait to return to menu"

            hint_text = hint_font.render(hint_text_content, True, (200, 200, 200))
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            surface.blit(hint_text, hint_rect)

def run_game():
    # Main game loop that handles transitions between menus and gameplay
    pygame.init()  # Initialize Pygame modules once at the start
    # pygame.font.init() # pygame.init() handles this
    # pygame.mixer.init() # Game.init() handles this if needed, or initialize here if used globally

    action = 'menu'
    
    while action != 'quit':
        if action == 'menu':
            # pygame.quit() # REMOVED
            menu = MainMenu()
            # menu.init() already calls pygame.init() internally for safety, and sets display mode
            menu.init()
            action = menu.loop()
        elif action == 'start':
            # pygame.quit() # REMOVED
            game = Game()
            # game.init() handles its own pygame initializations (like mixer) and OpenGL display mode
            game.init()
            action = game.loop()  # Get the next action from the game loop
        elif action == 'options':
            options_menu = OptionsMenu()
            # if not pygame.get_init(): pygame.init() # REMOVED - pygame already initialized
            # options_menu.init() already calls pygame.init() for safety and sets display mode
            options_menu.init() 
            action = options_menu.loop()
            # After options, if action is 'menu', MainMenu.init() will be called, 
            # which re-initializes the screen with current (potentially updated) GAME_SETTINGS.
    
    # Clean up and exit
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run_game()