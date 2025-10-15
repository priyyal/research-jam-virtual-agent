import os
import sys
from copy import deepcopy
import random

import pygame
from maze import Maze
from actors import Player, Enemy

# -----------------------------
# Experiment / gameplay constants
# -----------------------------
HEALTH_MAX = 100
HEALTH_PENALTY_WRONG = 15
HALLWAY_PAUSE_MS = 250       # brief pause after a choice
FPS_DEFAULT = 60
NUM_HALLWAYS = 3
AGENTS_PER_HALLWAY = 9
MAX_TRIAL_SECONDS = 30
TIME_PENALTY_PER_SEC = 1

# Asset paths
ASSISTANT_DIR = "images/assistants"
HALLWAY_IMG = "images/hallway.png"
SPEECH_LEFT = "images/left-speech-bubble.png"
SPEECH_RIGHT = "images/right-speech-bubble.png"


# -----------------------------
# UI helpers
# -----------------------------
def draw_health_bar(surface, x, y, w, h, health, health_max=HEALTH_MAX):
    """Simple top HUD health bar."""
    # frame
    pygame.draw.rect(surface, (30, 30, 30), (x - 2, y - 2, w + 4, h + 4), border_radius=4)
    pygame.draw.rect(surface, (200, 200, 200), (x - 1, y - 1, w + 2, h + 2), width=1, border_radius=4)
    # fill
    pct = max(0.0, min(1.0, health / float(health_max)))
    fill_w = int(w * pct)
    color = (60, 200, 80) if pct > 0.5 else (250, 190, 30) if pct > 0.25 else (220, 60, 60)
    pygame.draw.rect(surface, color, (x, y, fill_w, h), border_radius=3)


def load_png(path):
    img = pygame.image.load(path).convert_alpha()
    return img

def log_event(event_type, **kwargs):
    """Prints key player activity events to terminal."""
    parts = [f"[{event_type.upper()}]"]
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    print(" ".join(parts), flush=True)

# -----------------------------
# Core game
# -----------------------------
class Game:
    def __init__(self, width: int, height: int, fps: int = FPS_DEFAULT, num_levels: int = 1) -> None:
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Virtual Agent Trust Game")
        self.clock = pygame.time.Clock()
        self.fps = fps

        # one "level" = Pac-Man stage -> then 9 hallway trials (one per agent)
        self.num_levels = num_levels

        # health
        self.health = HEALTH_MAX

        # only keep .png assistant sprites
        self.image_filenames = [
            f for f in os.listdir(ASSISTANT_DIR)
            if f.lower().endswith(".png")
        ]

        # pre-load hallway background & speech bubbles
        self.hallway_image = load_png(HALLWAY_IMG)
        self.hallway_image = pygame.transform.smoothscale(self.hallway_image, (self.width, self.height))

        self.say_left_img = load_png(SPEECH_LEFT)
        self.say_right_img = load_png(SPEECH_RIGHT)

        # assistant scaling (keep them reasonable on screen)
        self.assistant_scale = 0.15  # tweak if too big/small

        # speech bubble scaling (relative to original)
        self.bubble_scale = 0.15
        self.say_left_img = pygame.transform.smoothscale(
            self.say_left_img,
            (int(self.say_left_img.get_width() * self.bubble_scale),
             int(self.say_left_img.get_height() * self.bubble_scale))
        )
        self.say_right_img = pygame.transform.smoothscale(
            self.say_right_img,
            (int(self.say_right_img.get_width() * self.bubble_scale),
             int(self.say_right_img.get_height() * self.bubble_scale))
        )

    # ------------- public API -------------
    def run(self):
        """
		Session flow:
		  for each hallway:
			play maze once -> then do AGENTS_PER_HALLWAY agent trials
		Health NEVER ends the session; we just clamp at [0, HEALTH_MAX].
		Assistants are cycled without immediate repeats; pool reshuffles as needed.
		"""
        # assistant queue helper
        assistant_pool = deepcopy(self.image_filenames)
        random.shuffle(assistant_pool)

        def next_assistant_filename():
            nonlocal assistant_pool
            if not assistant_pool:                   # recycle pool if empty
                assistant_pool = deepcopy(self.image_filenames)
                random.shuffle(assistant_pool)
            return assistant_pool.pop()

        # we treat num_levels as “sessions”; most people will just use 1
        for _ in range(self.num_levels):
            for _ in range(NUM_HALLWAYS):
                # 1) Maze segment before this hallway (urgency buffer)
                self._run_maze_trial()

                # 2) Hallway with N agents
                for _ in range(AGENTS_PER_HALLWAY):
                    filename = next_assistant_filename()
                    self._run_hallway_trial(filename)

        pygame.quit()



    # ------------- internals -------------
    def _run_maze_trial(self):
        """Run the Pac-Man style maze stage until the player reaches the goal or is caught."""
        maze = Maze(self.screen)
        player = Player(maze)
        enemy = Enemy(maze, player)

        enemy_move_time = pygame.time.get_ticks()
        enemy_move_delay = 500  # ms
        enemy_is_active = False

        while True:
            self.screen.fill("black")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    close_game()

            # goal reached -> proceed to hallway
            if (player.x, player.y) == maze.goal:
                # optional: short visual confirmation
                pygame.display.update()
                return

            # player update
            player.move()
            if (player.x, player.y) != (0, 0) and not enemy_is_active:
                enemy_is_active = True
                enemy_move_time = pygame.time.get_ticks()

            # draw maze and actors
            maze.draw()
            player.draw()

            # enemy update/draw (with simple chase timing)
            if enemy_is_active:
                if (pygame.time.get_ticks() - enemy_move_time) > enemy_move_delay:
                    try:
                        enemy.move()
                    except IndexError:
                        # caught by enemy -> end trial
                        # (no explicit health change here per requirement)
                        return
                    enemy_move_time = pygame.time.get_ticks()
                enemy.draw()

            # (optional) show current health during maze too
            draw_health_bar(self.screen, 20, 18, self.width - 40, 16, self.health)

            pygame.display.update()
            self.clock.tick(self.fps)

    def _run_hallway_trial(self, assistant_filename: str):
        """One agent trial in the hallway. Health changes but never ends the session."""
        # load & scale assistant sprite
        assistant_img = load_png(os.path.join(ASSISTANT_DIR, assistant_filename))
        assistant_img = pygame.transform.smoothscale(
            assistant_img,
            (int(assistant_img.get_width() * self.assistant_scale),
             int(assistant_img.get_height() * self.assistant_scale))
        )

        # ground-truth correct door for this trial
        correct_door = random.choice(["left", "right"])

        # for now, agent advice is random (later: tie to per-agent lie rate)
        advise = random.choice(["left", "right"])
        bubble_img = self.say_left_img if advise == "left" else self.say_right_img

        # positions
        assistant_rect = assistant_img.get_rect(center=(self.width // 2, self.height // 2 - 40))
        bubble_rect = bubble_img.get_rect(midbottom=(assistant_rect.centerx, assistant_rect.top - 10))

        # timing
        start_ticks = pygame.time.get_ticks()
        selected = None
        choosing = True
        while choosing:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        close_game()
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        selected = "left"; print("left", flush=True); choosing = False
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        selected = "right"; print("right", flush=True); choosing = False
                    elif event.key == pygame.K_x:
                        self._show_x_ray()

            # draw hallway + agent + speech bubble + health bar
            self.screen.blit(self.hallway_image, (0, 0))
            self.screen.blit(assistant_img, assistant_rect)
            self.screen.blit(bubble_img, bubble_rect)
            draw_health_bar(self.screen, 20, 18, self.width - 40, 16, self.health)

            # optional: show a simple countdown text
            elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0
            remaining = max(0, int(MAX_TRIAL_SECONDS - elapsed))
            font = pygame.font.SysFont(None, 28)
            t_surf = font.render(f"Time: {remaining}s", True, (230, 230, 230))
            self.screen.blit(t_surf, (20, 40))

            pygame.display.update()
            self.clock.tick(self.fps)

        # resolve choice
        end_ticks = pygame.time.get_ticks()
        elapsed_sec = (end_ticks - start_ticks) / 1000.0

        # wrong-door penalty
        if selected is not None and selected != correct_door:
            self.health -= HEALTH_PENALTY_WRONG

        # time penalty if too slow (soft limit)
        if elapsed_sec > MAX_TRIAL_SECONDS:
            over = elapsed_sec - MAX_TRIAL_SECONDS
            self.health -= int(over * TIME_PENALTY_PER_SEC)

        # clamp health and NEVER end session from health reaching 0
        self.health = max(0, min(HEALTH_MAX, self.health))

        log_event("hallway_start", agent=assistant_filename, advise=advise, correct=correct_door)
        log_event("choice_made", selected=selected, correct=correct_door)
        log_event("health_update", new_health=self.health)


        # tiny pause so player can see result before next agent
        pygame.time.delay(HALLWAY_PAUSE_MS)


    def _show_x_ray(self):
        """Simple placeholder peek: draw colored columns at left/right door areas."""
        # You can adjust these rectangles to match your hallway art's door positions.
        left_rect = pygame.Rect(80, 80, 100, self.height - 160)
        right_rect = pygame.Rect(self.width - 180, 80, 100, self.height - 160)
        s = pygame.Surface((left_rect.width, left_rect.height), pygame.SRCALPHA)
        s.fill((210, 74, 210, 100))  # semi-transparent purple
        self.screen.blit(s, (left_rect.x, left_rect.y))

        s2 = pygame.Surface((right_rect.width, right_rect.height), pygame.SRCALPHA)
        s2.fill((100, 54, 100, 100))  # semi-transparent darker purple
        self.screen.blit(s2, (right_rect.x, right_rect.y))
        pygame.display.update()

        # flash briefly
        pygame.time.delay(200)


# -----------------------------
# App bootstrap
# -----------------------------
def close_game():
    print("Closing game...")
    pygame.quit()
    sys.exit()


def main():
    # Window size can be tuned to your hallway background image aspect
    Game(800, 800, fps=FPS_DEFAULT, num_levels=1).run()
    print("----------------------SCRIPT COMPLETE----------------------")


if __name__ == "__main__":
    main()
