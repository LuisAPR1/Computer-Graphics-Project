import pygame

SOUND_AMBIENT = 'ambient'
SOUND_SWISH = 'swish'
SOUND_WARP = 'warp'
SOUND_UNLOCK = 'unlock'
SOUND_ENERGYFLOW = 'energyflow'
SOUND_BOUNCE = 'bounce'
SOUND_PICKUP = 'pickup'
SOUND_SCREWGRAVITY = 'screwgravity'
SOUND_CHILLJAZZ = 'chilljazz'
SOUND_PAUSEMENU = 'pausemenu'
SOUND_LAVASOUND = 'lavasound'
SOUND_LOSESONG = 'losesong'
SOUND_WALK = 'walk'
# Add instrument sound constants
SOUND_MANDOLINE = 'mandoline'
SOUND_VUVUZELA = 'vuvuzela'
SOUND_CRUMHORN = 'crumhorn'
SOUND_DIGERIDOO = 'digeridoo'

SOUND_FILES = {
    SOUND_AMBIENT: 'Sounds/ambient.mp3',
    SOUND_SWISH: 'Sounds/swish.wav',
    SOUND_WARP: 'Sounds/warp.wav',
    SOUND_UNLOCK: 'Sounds/unlock.wav',
    SOUND_ENERGYFLOW: 'Sounds/energyflow.wav',
    SOUND_BOUNCE: 'Sounds/bounce.wav',
    SOUND_PICKUP: 'Sounds/pickup.wav',
    SOUND_SCREWGRAVITY: 'Sounds/screwgravity.wav',
    SOUND_CHILLJAZZ: 'Sounds/chillJazz.mp3',
    SOUND_PAUSEMENU: 'Sounds/pausemenu.mp3',
    SOUND_LAVASOUND: 'Sounds/lavasound.mp3',
    SOUND_LOSESONG: 'Sounds/losesong.mp3',
    SOUND_WALK: 'Sounds/walk.mp3',  # Using bounce.wav as the walking sound
    # Add instrument sound file paths
    SOUND_MANDOLINE: 'Sounds/mandolim.mp3',
    SOUND_VUVUZELA: 'Sounds/vuvuzela.mp3',
    SOUND_CRUMHORN: 'Sounds/Crumhorn.mp3',
    SOUND_DIGERIDOO: 'Sounds/Didgeridoo.mp3',
}

class Sound:
    def __init__(self):
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)  # Aumentar o número total de canais de áudio disponíveis
        self.sounds = {}
        self.ambient_channel = None
        self.bounce_channel = None
        self.menu_music_channel = None
        self.pause_menu_channel = None
        self.lava_channel = None
        self.lose_song_channel = None
        self.walk_channel = pygame.mixer.Channel(10)  # Usar um canal fixo dedicado para os passos
        self.lava_sound_timer = 0
        self.lava_sound_interval = 0.3
        self.is_walking = False
        self.walk_sound_timer = 0
        self.walk_sound_interval = 0.4  # Slightly faster for better walking rhythm with bounce sound
        self.running_sound_interval = 0.2  # Faster interval for running

    def load(self):
        for key, path in SOUND_FILES.items():
            try:
                self.sounds[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f'Erro ao carregar som {path}: {e}')

    def play(self, sound_id):
        if sound_id == SOUND_AMBIENT:
            if self.ambient_channel is None or not self.ambient_channel.get_busy():
                self.ambient_channel = self.sounds[sound_id].play(loops=-1)
                if self.ambient_channel:
                    self.ambient_channel.set_volume(0.25)
        elif sound_id == SOUND_CHILLJAZZ:
            if self.menu_music_channel is None or not self.menu_music_channel.get_busy():
                self.menu_music_channel = self.sounds[sound_id].play(loops=-1)
                if self.menu_music_channel:
                    self.menu_music_channel.set_volume(0.3)
        elif sound_id == SOUND_PAUSEMENU:
            if self.pause_menu_channel is None or not self.pause_menu_channel.get_busy():
                self.pause_menu_channel = self.sounds[sound_id].play(loops=-1)
                if self.pause_menu_channel:
                    self.pause_menu_channel.set_volume(0.25)
        else:
            self.sounds.get(sound_id, None) and self.sounds[sound_id].play()

    def play_bounce(self, vol=1.0):
        if SOUND_BOUNCE in self.sounds:
            self.bounce_channel = self.sounds[SOUND_BOUNCE].play()
            if self.bounce_channel:
                self.bounce_channel.set_volume(vol)

    def play_lava_sound(self, dt):
        # Toca o som da lava com um intervalo curto para criar uma sensação rápida e repetitiva
        self.lava_sound_timer += dt
        if self.lava_sound_timer >= self.lava_sound_interval:
            if SOUND_LAVASOUND in self.sounds:
                self.lava_channel = self.sounds[SOUND_LAVASOUND].play()
                if self.lava_channel:
                    self.lava_channel.set_volume(0.4)  # Volume reduzido para não ser muito irritante
            self.lava_sound_timer = 0

    def stop_lava_sound(self):
        if self.lava_channel and self.lava_channel.get_busy():
            self.lava_channel.stop()
        self.lava_sound_timer = 0

    def play_lose_song(self):
        # Toca a música de game over
        if SOUND_LOSESONG in self.sounds:
            self.lose_song_channel = self.sounds[SOUND_LOSESONG].play(loops=-1)
            if self.lose_song_channel:
                self.lose_song_channel.set_volume(0.3)  # Volume mais baixo para não ser muito alto
    
    def stop_lose_song(self):
        # Para a música de game over
        if self.lose_song_channel and self.lose_song_channel.get_busy():
            self.lose_song_channel.stop()

    def play_walk_sound(self, dt, is_running=False):
        # Se não está andando, não reproduz o som
        if not self.is_walking:
            return
            
        # Escolhe o intervalo baseado se está correndo ou não
        interval = self.running_sound_interval if is_running else self.walk_sound_interval
        
        # Atualiza o timer e verifica se está na hora de tocar o som
        self.walk_sound_timer += dt
        if self.walk_sound_timer >= interval:
            if SOUND_WALK in self.sounds:
                # Verifica se o canal dedicado para passos não está ocupado
                if not self.walk_channel.get_busy():
                    # Reproduz o som no canal dedicado
                    self.walk_channel.play(self.sounds[SOUND_WALK])
                    # Use a lower volume for the walk sound
                    self.walk_channel.set_volume(0.3)
                # Reinicia o timer mesmo se o som ainda estiver tocando
                self.walk_sound_timer = 0
    
    def start_walking(self):
        self.is_walking = True
        # Zera o timer para garantir que o som comece imediatamente
        self.walk_sound_timer = self.walk_sound_interval
    
    def stop_walking(self):
        self.is_walking = False
        # Para qualquer som no canal de passos
        self.walk_channel.stop()
            
    def stop_all(self):
        pygame.mixer.stop()
        self.lava_sound_timer = 0
        self.walk_sound_timer = 0
        self.is_walking = False

    def stop_menu_music(self):
        if self.menu_music_channel and self.menu_music_channel.get_busy():
            self.menu_music_channel.stop()
            
    def stop_pause_menu_music(self):
        if self.pause_menu_channel and self.pause_menu_channel.get_busy():
            self.pause_menu_channel.stop()

    def update(self):
        pass  # pygame.mixer não precisa de update explícito 