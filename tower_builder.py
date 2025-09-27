import pygame
import pymunk
import pymunk.pygame_util
import random
import os
import json
import requests

# --- Configurações ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 900

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("StackOut Torre Real com Música")
clock = pygame.time.Clock()
draw_options = pymunk.pygame_util.DrawOptions(screen)
font = pygame.font.SysFont("Arial", 28)
font_big = pygame.font.SysFont("Arial", 36)

# --- Inicializar música ---
pygame.mixer.init()
music_path = r"C:\Users\User Gamer\Downloads\Tower_builder\Computer World (2009 Remaster) - Kraftwerk (youtube).mp3"
if os.path.exists(music_path):
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(-1)
else:
    print("Arquivo de música não encontrado!")

# --- Arquivo de info do jogador ---
info_file = "player_info.json"
player_info = {"nick": "", "email": ""}
if os.path.exists(info_file):
    with open(info_file, "r") as f:
        player_info = json.load(f)

input_active = player_info["nick"] == "" or player_info["email"] == ""
current_field = "nick"
input_text = ""

# --- API de recorde ---
SERVER_URL = "http://127.0.0.1:5000"  # troque pelo IP público ou da rede para outros PCs

def get_recorde_mundial():
    try:
        r = requests.get(f"{SERVER_URL}/recorde", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                "nick": data.get("player", ""),
                "email": data.get("email", ""),
                "pontuacao": data.get("world_record", 0)
            }
    except Exception as e:
        print("Erro ao buscar recorde mundial:", e)
    return {"nick": "indisponível", "email": "", "pontuacao": 0}

def enviar_recorde(nick, email, pontuacao):
    try:
        r = requests.post(f"{SERVER_URL}/recorde",
                          json={"nick": nick, "email": email, "pontuacao": pontuacao},
                          timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                "nick": data.get("recorde", {}).get("nick", nick),
                "email": data.get("recorde", {}).get("email", email),
                "pontuacao": data.get("recorde", {}).get("pontuacao", pontuacao)
            }
    except Exception as e:
        print("Erro ao enviar recorde:", e)
    return {"nick": nick, "email": email, "pontuacao": pontuacao}

# --- Física ---
space = pymunk.Space()
space.gravity = (0, GRAVITY)
blocks = []

def create_block(y=50, width=60, height=20):
    x = random.randint(width//2, WIDTH - width//2)
    body = pymunk.Body(1, pymunk.moment_for_box(1, (width, height)))
    body.position = x, y
    shape = pymunk.Poly.create_box(body, (width, height))
    shape.friction = 0.6
    space.add(body, shape)
    blocks.append((body, shape))
    return body, shape

initial_block, initial_shape = create_block(y=HEIGHT-50)
initial_block.position = WIDTH//2, HEIGHT-50

floor_body = pymunk.Body(body_type=pymunk.Body.STATIC)
floor_width = 100
floor_shape = pymunk.Segment(
    floor_body,
    (initial_block.position.x - floor_width//2, initial_block.position.y + 10),
    (initial_block.position.x + floor_width//2, initial_block.position.y + 10),
    5
)
floor_shape.friction = 1.0
space.add(floor_body, floor_shape)

NEW_BLOCK_INTERVAL = 60
frame_count = 0
paused = False
personal_record = 0
stack_height = 0

# --- Buscar recorde mundial inicial ---
recorde_mundial = get_recorde_mundial()

def get_connected_blocks(base_block, all_blocks):
    connected = set()
    stack = [base_block]
    while stack:
        b = stack.pop()
        connected.add(b)
        for other_b, _ in all_blocks:
            if other_b in connected:
                continue
            if abs(other_b.position.x - b.position.x) < 35 and 0 < (b.position.y - other_b.position.y) < 25:
                stack.append(other_b)
    return connected

# --- Loop principal ---
running = True
while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Digitação do nick/email ---
        if input_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if current_field == "nick":
                        player_info["nick"] = input_text
                        input_text = ""
                        current_field = "email"
                    else:
                        player_info["email"] = input_text
                        with open(info_file, "w") as f:
                            json.dump(player_info, f)
                        input_active = False
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode

        # --- Pausa ---
        if not input_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused

    if input_active:
        prompt = "Digite seu nick:" if current_field == "nick" else "Digite seu e-mail:"
        prompt_surface = font.render(prompt, True, BLACK)
        screen.blit(prompt_surface, (50, HEIGHT//2 - 50))
        box_rect = pygame.Rect(50, HEIGHT//2, 300, 40)
        pygame.draw.rect(screen, GRAY, box_rect)
        txt_surface = font.render(input_text, True, BLACK)
        screen.blit(txt_surface, (box_rect.x + 5, box_rect.y + 5))
    else:
        if not paused:
            keys = pygame.key.get_pressed()
            if blocks:
                current_block = blocks[-1][0]
                if keys[pygame.K_LEFT]:
                    current_block.position = (current_block.position.x - 5, current_block.position.y)
                if keys[pygame.K_RIGHT]:
                    current_block.position = (current_block.position.x + 5, current_block.position.y)
                if keys[pygame.K_DOWN]:
                    current_block.position = (current_block.position.x, current_block.position.y + 5)

            frame_count += 1
            if frame_count >= NEW_BLOCK_INTERVAL:
                create_block()
                frame_count = 0

            space.step(1/FPS)

            for b, s in blocks[:]:
                if b.position.y > HEIGHT + 50:
                    space.remove(b, s)
                    blocks.remove((b, s))

            connected_blocks = get_connected_blocks(initial_block, blocks)
            stack_height = len(connected_blocks)

            # --- Atualizar recordes ---
            if stack_height > personal_record:
                personal_record = stack_height
                if personal_record > recorde_mundial["pontuacao"]:
                    recorde_mundial = enviar_recorde(player_info["nick"], player_info["email"], personal_record)

        xs = [b.position.x for b, s in blocks]
        if xs:
            avg_x = sum(xs)/len(xs)
            tilt = avg_x - WIDTH//2
            if tilt < 0:
                color_intensity = min(255, int(-tilt*2))
                pygame.draw.rect(screen, (color_intensity, 0, 0), (0, 0, WIDTH//2, HEIGHT))
            elif tilt > 0:
                color_intensity = min(255, int(tilt*2))
                pygame.draw.rect(screen, (color_intensity, 0, 0), (WIDTH//2, 0, WIDTH//2, HEIGHT))

        text = font.render(f"Altura: {stack_height}", True, BLACK)
        screen.blit(text, (10, 10))

        if paused:
            pause_text = font_big.render("PAUSA", True, BLACK)
            screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - 100))
            personal_text = font.render(f"Recorde Pessoal: {personal_record}", True, BLACK)
            world_text = font.render(
                f"Mundial: {recorde_mundial['pontuacao']} ({recorde_mundial['nick']})",  # <-- só nick e pontuação
                True, BLACK
            )
            screen.blit(personal_text, (WIDTH//2 - personal_text.get_width()//2, HEIGHT//2))
            screen.blit(world_text, (WIDTH//2 - world_text.get_width()//2, HEIGHT//2 + 40))

        space.debug_draw(draw_options)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
