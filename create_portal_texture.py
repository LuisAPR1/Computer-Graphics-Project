import pygame
import sys
import numpy as np

pygame.init()

# Criar uma superfície para a textura de pedra
surface = pygame.Surface((256, 256))

# Cor base para pedra (cinza médio)
base_color = (120, 120, 125)
surface.fill(base_color)

# Criar uma textura de pedra uniforme e clean
# Vamos usar ruído sutil para simular a textura da pedra

# Gerar um padrão de ruído sutíl
noise_scale = 15  # Tamanho do ruído (maior = mais uniforme)
for x in range(256):
    for y in range(256):
        # Criar variação sutil na cor base
        noise = np.random.normal(0, 1) * 8  # Desvio padrão pequeno para textura sutil
        
        # Adicionar pequenas veias de pedra para dar profundidade
        vein_effect = 0
        if (x + y) % noise_scale == 0 or (x - y) % noise_scale == 0:
            vein_effect = 5
        
        # Calcular cor final com ruído
        r = max(0, min(255, base_color[0] + noise + vein_effect))
        g = max(0, min(255, base_color[1] + noise))
        b = max(0, min(255, base_color[2] + noise - vein_effect))
        
        # Aplicar a cor ao pixel
        surface.set_at((x, y), (int(r), int(g), int(b)))

# Adicionar um sutíl efeito circular para dar profundidade
# mas mantendo o aspecto clean e uniforme
center = (128, 128)
for radius in range(10, 130, 30):
    # Círculos muito sutis para adicionar profundidade sem perder uniformidade
    color_mod = 8 if radius < 100 else 5
    pygame.draw.circle(surface, 
                      (base_color[0] + color_mod, 
                       base_color[1] + color_mod, 
                       base_color[2] + color_mod), 
                      center, radius, 2)

# Adicionar um contorno externo para definir os limites
pygame.draw.circle(surface, (base_color[0] - 20, base_color[1] - 20, base_color[2] - 20), 
                  center, 125, 3)

# Adicionar centro roxo
purple_center_radius = 40
purple_color = (128, 0, 170)  # Cor roxa vibrante
purple_glow_color = (180, 100, 255)  # Cor roxa mais clara para o brilho interno

# Desenhar gradiente do roxo
for r in range(purple_center_radius, 0, -1):
    # Criar um gradiente do roxo escuro para o roxo claro
    blend_factor = r / purple_center_radius
    color = (
        int(purple_color[0] * blend_factor + purple_glow_color[0] * (1 - blend_factor)),
        int(purple_color[1] * blend_factor + purple_glow_color[1] * (1 - blend_factor)),
        int(purple_color[2] * blend_factor + purple_glow_color[2] * (1 - blend_factor))
    )
    pygame.draw.circle(surface, color, center, r)

# Salvar a imagem
pygame.image.save(surface, "Images/portal_texture.png")
print("Textura de pedra com centro roxo para o portal criada com sucesso!") 