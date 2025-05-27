import pygame
from guitar_hero import GuitarHeroMinigame

# Inicialização do Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Teste de Guitar Hero')

# Criação do minigame
minigame = GuitarHeroMinigame('MODEL_GUITAR')
clock = pygame.time.Clock()

# Loop principal
running = True
while running:
    # Tratamento de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            minigame.handle_key_press(event.key)
        elif event.type == pygame.KEYUP:
            # Tratamento para liberação de teclas (necessário para notas longas)
            minigame.handle_key_release(event.key)

    # Atualização do jogo
    dt = clock.tick(60) / 1000
    minigame.update(dt)

    # Rend888843211ização
    if minigame.running:
        minigame.draw(screen)
    else:
        minigame.draw_results(screen)

    pygame.display.flip()

pygame.quit()