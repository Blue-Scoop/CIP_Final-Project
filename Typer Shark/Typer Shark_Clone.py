import pygame
import random
import sys
import os

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Typer Shark Clone")

# Colors
BG_COLOR = (0, 20, 40)
TEXT_COLOR = (0, 255, 255)
MATCHED_COLOR = (0, 255, 200)
LOSING_LIFE_COLOR = (255, 50, 50)
GAME_OVER_BG = (0, 0, 0)
GAME_OVER_TEXT = (0, 180, 255)

# Fonts
FONT_SIZE = 36
FONT = pygame.font.SysFont("consolas", FONT_SIZE)
TITLE_FONT = pygame.font.SysFont("comicsansms", 64, True)

# Game parameters
MAX_LIVES = 5
MAX_SHARKS = 5  # Maximum number of sharks on screen
SHARK_SPEED_MIN = 60   # pixels per second
SHARK_SPEED_MAX = 130
SPAWN_INTERVALS = {
    "regular": 5000,      # 5 seconds
    "tiger": 10000,       # 10 seconds
    "mutated": 20000,     # 20 seconds
    "great_white": 30000  # 30 seconds
}
SPAWN_ACCELERATION = 0.90  # spawn interval multiplier

# Initialize clock
clock = pygame.time.Clock()

# Load words from file
def load_words():
    words = {
        "regular": [],
        "tiger": [],
        "great_white": [],
        "mutated": []
    }
    file_path = 'Typer Shark/shark_game_words.txt'
    try:
        with open(file_path, 'r') as f:
            category = None
            for line in f:
                line = line.strip()
                if not line:  # Skips empty lines
                    continue
                if line.startswith("#"):
                    category = line[2:].strip().lower()
                    print(f"Category found: {category}")
                    if category not in words:
                        print(f"Warning: Unknown category '{category}' ignored.")
                elif category in words:
                    words[category].append(line.lower())
                    print(f"Added word '{line.lower()}' to category '{category}'")
            print(f"Loaded words: {words}")
            for cat in words:
                if not words[cat]:
                    print(f"Warning: No words found for category '{cat}'.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found. Please ensure it exists.")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"Error loading words: {e}")
        pygame.quit()
        sys.exit()
    return words

# Load images for sharks
def load_shark_images():
    try:
        # Load and scale images
        regular_img = pygame.image.load("Typer Shark/blue-mako-shark-removebg-preview.png")
        regular_img = pygame.transform.smoothscale(regular_img, (120, 70))
        tiger_img = pygame.image.load("Typer Shark/tiger-shark-removebg-preview.png")
        tiger_img = pygame.transform.smoothscale(tiger_img, (150, 70))
        great_white_img = pygame.image.load("Typer Shark/great-white-shark-removebg-preview.png")
        great_white_img = pygame.transform.smoothscale(great_white_img, (200, 100))
        mutated_img = pygame.image.load("Typer Shark/mutated-toxic-shark-removebg-preview.png")
        mutated_img = pygame.transform.smoothscale(mutated_img, (120, 100))
        return {
            "regular": regular_img,
            "tiger": tiger_img,
            "great_white": great_white_img,
            "mutated": mutated_img
        }
    except pygame.error as e:
        print(f"Error loading images: {e}")

# Shark class
class Shark:
    def __init__(self, word, y, speed, category, image):
        self.word = word
        self.y = y
        self.speed = speed
        self.x = WIDTH
        self.matched_len = 0
        self.surface = None
        self.image = image
        self.update_surface()

    def update_surface(self):
        matched_text = self.word[:self.matched_len]
        unmatched_text = self.word[self.matched_len:]

        matched_surf = FONT.render(matched_text, True, MATCHED_COLOR)
        unmatched_surf = FONT.render(unmatched_text, True, TEXT_COLOR)

        total_width = matched_surf.get_width() + unmatched_surf.get_width()
        height = FONT_SIZE

        self.surface = pygame.Surface((total_width, height), pygame.SRCALPHA)
        self.surface.blit(matched_surf, (0, 0))
        self.surface.blit(unmatched_surf, (matched_surf.get_width(), 0))

    def update(self, dt):
        self.x -= self.speed * dt
        if self.x + self.surface.get_width() < 0:
            return False
        return True

    def draw(self, surface):
        surface.blit(self.surface, (self.x, self.y))
        surface.blit(self.image, (self.x - 80, self.y - 10))  # Adjust position of the shark image

    def match_char(self, char):
        char = char.lower()
        if self.matched_len < len(self.word) and self.word[self.matched_len] == char:
            self.matched_len += 1
            self.update_surface()
            return self.matched_len == len(self.word)
        else:
            self.matched_len = 0
            self.update_surface()
            return False

def draw_text_center(text, font, color, surface, y):
    text_surf = font.render(text, True, color)
    x = (WIDTH - text_surf.get_width()) // 2
    surface.blit(text_surf, (x, y))

def main():
    running = True
    score = 0
    lives = MAX_LIVES
    typed_text = ""

    words = load_words()
    # Checks if any category has words before proceeding
    if not any(words[cat] for cat in words):
        print("Error: No valid words loaded from file. Check 'Typer Shark/shark_game_words.txt'.")
        pygame.quit()
        sys.exit()
    
    shark_images = load_shark_images()
    sharks = []

    # Timers for spawning sharks
    spawn_timers = {
        "regular": 0,
        "tiger": 0,
        "mutated": 0,
        "great_white": 0
    }
    game_over = False
    restart_debounce = 0  # To prevent rapid restarts

    while running:
        dt = max(clock.tick(60) / 1000.0, 0.001)  # Ensure dt is reasonable
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_BACKSPACE:
                    typed_text = typed_text[:-1]
                elif event.unicode.isalpha() or event.unicode in ['@', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    typed_text += event.unicode.lower()
                    matched_shark = None
                    for shark in sharks:
                        if shark.word.startswith(typed_text):
                            matched_shark = shark
                            break
                    if matched_shark:
                        matched_shark.matched_len = len(typed_text)
                        matched_shark.update_surface()

                        for shark in sharks:
                            if shark != matched_shark:
                                shark.matched_len = 0
                                shark.update_surface()

                        if typed_text == matched_shark.word:
                            score += len(matched_shark.word) * 10
                            sharks.remove(matched_shark)
                            typed_text = ""
                    else:
                        for shark in sharks:
                            if shark.matched_len != 0:
                                shark.matched_len = 0
                                shark.update_surface()
                        typed_text = ""
                elif event.key == pygame.K_RETURN:
                    typed_text = ""
            elif event.type == pygame.KEYDOWN and game_over and now - restart_debounce > 500:
                if event.key == pygame.K_SPACE:  # Only restart on SPACE key
                    score = 0
                    lives = MAX_LIVES
                    typed_text = ""
                    sharks.clear()
                    game_over = False
                    restart_debounce = now

        if not game_over:
            # Check if we can spawn new sharks based on their timers
            if len(sharks) < MAX_SHARKS:
                if now - spawn_timers["regular"] > SPAWN_INTERVALS["regular"]:
                    category = "regular"
                    if words[category]:  # Check if the selected category has words
                        word = random.choice(words[category])
                        y = random.randint(50, HEIGHT - 50)
                        speed = random.uniform(SHARK_SPEED_MIN + score * 0.05, SHARK_SPEED_MAX)
                        new_shark = Shark(word, y, speed, category, shark_images[category])
                        sharks.append(new_shark)
                        spawn_timers[category] = now  # Reset timer for this category

                if now - spawn_timers["tiger"] > SPAWN_INTERVALS["tiger"]:
                    category = "tiger"
                    if words[category]:  # Check if the selected category has words
                        word = random.choice(words[category])
                        y = random.randint(50, HEIGHT - 50)
                        speed = random.uniform(SHARK_SPEED_MIN + score * 0.05, SHARK_SPEED_MAX)
                        new_shark = Shark(word, y, speed, category, shark_images[category])
                        sharks.append(new_shark)
                        spawn_timers[category] = now  # Reset timer for this category

                if now - spawn_timers["mutated"] > SPAWN_INTERVALS["mutated"]:
                    category = "mutated"
                    if words[category]:  # Check if the selected category has words
                        word = random.choice(words[category])
                        y = random.randint(50, HEIGHT - 50)
                        speed = random.uniform(SHARK_SPEED_MIN + score * 0.05, SHARK_SPEED_MAX)
                        new_shark = Shark(word, y, speed, category, shark_images[category])
                        sharks.append(new_shark)
                        spawn_timers[category] = now  # Reset timer for this category

                if now - spawn_timers["great_white"] > SPAWN_INTERVALS["great_white"]:
                    category = "great_white"
                    if words[category]:  # Check if the selected category has words
                        word = random.choice(words[category])
                        y = random.randint(50, HEIGHT - 50)
                        speed = random.uniform(SHARK_SPEED_MIN + score * 0.05, SHARK_SPEED_MAX)
                        new_shark = Shark(word, y, speed, category, shark_images[category])
                        sharks.append(new_shark)
                        spawn_timers[category] = now  # Reset timer for this category

            for shark in sharks[:]:
                alive = shark.update(dt)
                if not alive:
                    sharks.remove(shark)
                    lives -= 1
                    typed_text = ""
                    for s in sharks:
                        s.matched_len = 0
                        s.update_surface()
                    if lives <= 0:
                        game_over = True

        screen.fill(BG_COLOR)

        for shark in sharks:
            shark.draw(screen)

        draw_text_center(f"Score: {score}", FONT, TEXT_COLOR, screen, 10)
        draw_text_center(f"Lives: {lives}", FONT, TEXT_COLOR, screen, 50)

        typed_surf = FONT.render(typed_text, True, MATCHED_COLOR)
        screen.blit(typed_surf, (WIDTH//2 - typed_surf.get_width()//2, HEIGHT - 60))

        draw_text_center("Typer Shark", TITLE_FONT, (0, 220, 255), screen, HEIGHT - 120)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(GAME_OVER_BG)
            screen.blit(overlay, (0,0))
            draw_text_center("GAME OVER", TITLE_FONT, GAME_OVER_TEXT, screen, HEIGHT//2 - 80)
            draw_text_center(f"Final Score: {score}", FONT, GAME_OVER_TEXT, screen, HEIGHT//2)
            draw_text_center("Press SPACE to restart", FONT, GAME_OVER_TEXT, screen, HEIGHT//2 + 50)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
