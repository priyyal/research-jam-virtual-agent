import os
from copy import deepcopy
import random
import asyncio

import csv, datetime
import pygame
from maze import Maze
from actors import Player, Enemy


class Game:
    def __init__(
            self,
            width,
            height,
            fps=60,
            num_levels=1,
            participant_id="UNKNOWN",
            time_per_hallway=50,
            enemy_speed=500,
            assistant_type="mixed",
            round_times=None, wrong_penalty=5, seed=None,
            gender_sequence="MFN",
            agent_accuracy=50,
            unify_names=True,
    ) -> None:
        pygame.init()
        self.width = width
        self.height = height
        self.participant_id = participant_id
        self.max_time = time_per_hallway
        self.enemy_move_delay = enemy_speed
        self.assistant_type = assistant_type
        if seed is not None:
            random.seed(seed)

        self.round_times = round_times if round_times is not None else [90, 60, 40]
        self.wrong_penalty = wrong_penalty

        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.num_levels = num_levels  # then each block is 9 trials
        self.image_filenames = [
            f for f in os.listdir("images/assistants") if f.endswith(".png")
        ]
        self.agent_meta = {
            "F1.png": {"name": "Ava",   "gender": "female"},
            "F2.png": {"name": "Mira",  "gender": "female"},
            "F3.png": {"name": "Lena",  "gender": "female"},

            "M1.png": {"name": "Ethan", "gender": "male"},
            "M2.png": {"name": "Noah",  "gender": "male"},
            "M3.png": {"name": "Leo",   "gender": "male"},

            "N1.png": {"name": "Alex",  "gender": "neutral"},
            "N2.png": {"name": "Riley", "gender": "neutral"},
            "N3.png": {"name": "Jordan","gender": "neutral"},
        }
        self.gender_names = {
            "male": "John",
            "female": "Mira",
            "neutral": "Robin",
        }

        # Game stats
        self.max_health = 100
        self.health = self.max_health
        self.gender_sequence = (gender_sequence or "MFN").upper()
        self.agent_accuracy = int(agent_accuracy)
        self.unify_names = bool(unify_names)



        self.participant_id = self.participant_id.replace(" ", "").replace("/", "_")

        # Per-hallway time limits (seconds)
        #self.round_times = [90, 60, 40]   round 3 could be 35–40; adjust as needed
        self.max_time = self.round_times[0]  # default for drawing bar before round starts
        self.time_remaining = self.max_time * 1000  # milliseconds

        self.font = pygame.font.SysFont("Arial", 28)

        os.makedirs("data", exist_ok=True)

        # Unique run ID based on timestamp (safe for filenames)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

        self.run_id = timestamp

        self.log_path = (
            f"data/"
            f"{self.participant_id}_"
            f"{self.assistant_type}_"
            f"{self.num_levels}hallways_"
            f"{timestamp}.csv"
        )


        self.logfile = open(self.log_path, "w", newline="")
        self.logwriter = csv.writer(self.logfile)

        self.logwriter.writerow(
            [
                "timestamp",
                "participant_id",
                "run_id",
                "hallway",
                "trial",
                "agent_image",
                "agent_name",
                "agent_gender",
                "agent_suggestion",
                "agent_truthfulness",
                "correct_door",
                "player_choice",
                "correct",
                "reaction_time_ms",
                "compliance",
                "health_at_choice",
                "health_after",
                "time_remaining",
            ]
        )

        self.logfile.flush()
        print(f"[LOG] Writing trial data to: {self.log_path}")

    async def run(self):
        hallway_image = pygame.image.load("images/hallway.png")
        hallway_image = pygame.transform.scale(hallway_image, (self.width, self.height))

        # MAIN LOOP: 3 Hallways
        for level in range(self.num_levels):
            print(f"\n=== Entering Hallway {level + 1} ===")

            # Set PER-ROUND TIMER
            self.max_time = (
                self.round_times[level]
                if level < len(self.round_times)
                else self.round_times[-1]
            )
            hallway_start_time = pygame.time.get_ticks()
            self.time_remaining = self.max_time * 1000

            # Pac-Man Maze first
            await self._run_trial()

            # After maze, start hallway phase
            ordered_filenames = self._build_trial_filenames()

            for trial_index, filename in enumerate(ordered_filenames, start=1):
                print(f"\nAgent {trial_index}/9 in Hallway {level + 1}")
                pygame.event.clear()  # clear leftovers

                # Load image
                assistant_image = pygame.image.load(
                    f"images/assistants/{filename}"
                ).convert_alpha()


                # FORCE all agents to same size
                MAX_W = 340
                MAX_H = 340
                assistant_image = self.scale_to_fit(assistant_image, MAX_W, MAX_H)

                meta = self.agent_meta.get(filename, {})
                agent_name = meta.get("name", "Agent")
                agent_gender = meta.get("gender", "unknown")

                if self.unify_names and agent_gender in self.gender_names:
                    agent_name = self.gender_names[agent_gender]

                correct_door = random.choice(["left", "right"])
                agent_suggestion = self._agent_suggestion_for_accuracy(correct_door)
                agent_truthfulness = (agent_suggestion == correct_door)

                bubble_scale = 0.11

                text_bubble_image = pygame.image.load(f"images/{agent_suggestion}-speech-bubble.png")
                text_bubble_image = pygame.transform.scale(
                    text_bubble_image,
                    (
                        int(text_bubble_image.get_width() * bubble_scale),
                        int(text_bubble_image.get_height() * bubble_scale),
                    ),
                )

                # timestamp when this agent appears (for reaction time)
                agent_shown_time = pygame.time.get_ticks()

                show_hallway = True

                # HALLWAY LOOP (until choice made or time up)
                while show_hallway:
                    self.clock.tick(self.fps)

                    # hallway-wide timer (unchanged logic)
                    elapsed_time = pygame.time.get_ticks() - hallway_start_time
                    self.time_remaining = (self.max_time * 1000) - elapsed_time

                    self.screen.blit(hallway_image, (0, 0))
                    self.screen.blit(
                        assistant_image,
                        (
                            self.width // 2 - assistant_image.get_width() // 2,
                            self.height // 2 - assistant_image.get_height() // 2,
                        ),
                    )
                    self.screen.blit(
                        text_bubble_image,
                        (
                            self.width // 2 - text_bubble_image.get_width() // 2,
                            self.height // 2
                            - text_bubble_image.get_height()
                            - assistant_image.get_height() // 2 -15,
                        ),
                    )

                    # DRAW AGENT NAME under the speech bubble
                    name_text = self.font.render(agent_name, True, (255, 255, 255))


                    name_x = self.width // 2 - name_text.get_width() // 2
                    #name_y = bubble_y + text_bubble_image.get_height() + 6  # just below bubble
                    name_y = self.height // 2 - assistant_image.get_height() // 2 - 18

                    self.screen.blit(name_text, (name_x, name_y))

                    self._draw_health_bar()
                    self._draw_timer_bar()

                    # timer ran out
                    if self.time_remaining <= 0:
                        self._game_over("You have to be quicker!")
                        return

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            close_game()

                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_LEFT:
                                self._flash_choice("left")

                                # NEW MEASURES
                                reaction_time_ms = pygame.time.get_ticks() - agent_shown_time
                                compliance = ("left" == agent_suggestion)
                                health_at_choice = self.health

                                # log BEFORE applying health penalty
                                self._log_decision(
                                    level,
                                    trial_index,
                                    "left",
                                    correct_door,
                                    filename,
                                    agent_name,
                                    agent_gender,
                                    agent_suggestion,
                                    agent_truthfulness,
                                    reaction_time_ms,
                                    compliance,
                                    health_at_choice,
                                )

                                if correct_door != "left":
                                    self._update_health(-self.wrong_penalty)


                                show_hallway = False

                            elif event.key == pygame.K_RIGHT:
                                self._flash_choice("right")

                                # NEW MEASURES
                                reaction_time_ms = pygame.time.get_ticks() - agent_shown_time
                                compliance = ("right" == agent_suggestion)
                                health_at_choice = self.health

                                # log BEFORE applying health penalty
                                self._log_decision(
                                    level,
                                    trial_index,
                                    "right",
                                    correct_door,
                                    filename,
                                    agent_name,
                                    agent_gender,
                                    agent_suggestion,
                                    agent_truthfulness,
                                    reaction_time_ms,
                                    compliance,
                                    health_at_choice,
                                )

                                if correct_door != "right":
                                    self._update_health(-self.wrong_penalty)


                                show_hallway = False

                            elif event.key == pygame.K_x:
                                self._show_x_ray()

                    if self.health <= 0:
                        self._game_over("You ran out of health!")
                        return
                    
                    await asyncio.sleep(0)
                    pygame.display.update()

            print(f"Completed Hallway {level + 1}")  # hallway finished

            # Short pause / transition before next maze
            if level < self.num_levels - 1:  # if not the last hallway
                self._hallway_complete_screen(level + 1)
            else:
                print("All hallways completed successfully!")
                self._final_victory_screen()
                return

        pygame.quit()

    async def _run_trial(self):
        maze = Maze(self.screen)
        player = Player(maze)
        enemy = Enemy(maze, player)
        enemy_move_time = pygame.time.get_ticks()
        enemy_move_delay = 300  # milliseconds
        enemy_is_active = False

        while True:
            self.screen.fill("black")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close_game()

            if (player.x, player.y) == maze.goal:
                print("Goal reached!")
                return
            else:
                player.move()
                if (player.x, player.y) != (0, 0) and not enemy_is_active:
                    # Player moved - start the enemy
                    enemy_is_active = True
                    enemy_move_time = pygame.time.get_ticks()

                maze.draw()
                player.draw()

                if enemy_is_active:
                    if (pygame.time.get_ticks() - enemy_move_time) > enemy_move_delay:
                        try:
                            enemy.move()
                        except IndexError:
                            print("Player was caught!")
                            self._game_over("The enemy caught you!")
                            close_game()
                        enemy_move_time = pygame.time.get_ticks()
                    enemy.draw()

            await asyncio.sleep(0)
            pygame.display.update()
            self.clock.tick(self.fps)

    def _update_health(self, delta):
        self.health = max(0, min(self.max_health, self.health + delta))
        print(f"Health updated: {self.health}")

    def _build_trial_filenames(self):
        """Return exactly 9 filenames in gender blocks, ordered by self.gender_sequence."""
        males = sorted([f for f in self.image_filenames if f.startswith("M")])[:3]
        females = sorted([f for f in self.image_filenames if f.startswith("F")])[:3]
        neutrals = sorted([f for f in self.image_filenames if f.startswith("N")])[:3]

        group_map = {"M": males, "F": females, "N": neutrals}

        seq = getattr(self, "gender_sequence", "MFN")
        seq = (seq or "MFN").upper()
        if seq not in {"MFN", "MNF", "FMN", "FNM", "NMF", "NFM"}:
            seq = "MFN"  # safe default

        filenames = []
        for ch in seq:
            filenames.extend(group_map[ch])

        # safety: ensure we always return 9 if possible
        return filenames[:9]

    def _agent_suggestion_for_accuracy(self, correct_door):
        """Given correct_door, return agent suggestion consistent with configured accuracy."""
        acc = int(getattr(self, "agent_accuracy", 50))
        if acc not in (0, 50, 100):
            acc = 50

        if acc == 100:
            return correct_door
        if acc == 0:
            return "left" if correct_door == "right" else "right"

        truthful = random.random() < 0.5
        if truthful:
            return correct_door
        return "left" if correct_door == "right" else "right"


    def _draw_health_bar(self):
        bar_width = 300
        bar_height = 25
        x, y = 40, 40
        fill = (self.health / self.max_health) * bar_width
        pygame.draw.rect(self.screen, (255, 0, 0), (x, y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (0, 255, 0), (x, y, fill, bar_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)

        text = self.font.render(f"Health: {int(self.health)}", True, (255, 255, 255))
        self.screen.blit(text, (x, y - 30))

    def _draw_timer_bar(self):
        bar_width = 300
        bar_height = 25
        x, y = 460, 40
        ratio = self.time_remaining / (self.max_time * 1000)
        fill = max(0, min(1, ratio)) * bar_width
        pygame.draw.rect(self.screen, (0, 0, 0), (x, y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (255, 255, 0), (x, y, fill, bar_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)
        text = self.font.render(
            f"Time Left: {int(self.time_remaining / 1000)}s", True, (255, 255, 255)
        )
        self.screen.blit(text, (x, y - 30))

    def _game_over(self, message):
        """Show a Game Over screen and reset."""
        self.screen.fill((0, 0, 0))
        text1 = self.font.render("GAME OVER", True, (255, 0, 0))
        text2 = self.font.render(message, True, (255, 255, 255))
        self.screen.blit(
            text1,
            (self.width // 2 - text1.get_width() // 2, self.height // 2 - 40),
        )
        self.screen.blit(
            text2,
            (self.width // 2 - text2.get_width() // 2, self.height // 2 + 10),
        )
        pygame.display.update()
        pygame.time.delay(3000)
        print(message)
        self.health = self.max_health
        self.time_remaining = self.max_time * 1000

    def _hallway_complete_screen(self, next_hallway_number):
        """Show short message before next hallway begins."""
        self.screen.fill((0, 0, 0))
        msg = self.font.render("Hallway complete!", True, (0, 255, 0))
        next_msg = self.font.render(
            f"Entering Hallway {next_hallway_number + 1}...", True, (255, 255, 255)
        )
        self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, self.height // 2 - 30))
        self.screen.blit(
            next_msg, (self.width // 2 - next_msg.get_width() // 2, self.height // 2 + 10)
        )
        pygame.display.update()
        pygame.time.delay(2000)
        print(f"Transitioning to Hallway {next_hallway_number + 1}")

    def _final_victory_screen(self):
        """Display the final completion message."""
        self.screen.fill((0, 0, 0))
        text1 = self.font.render("🎉 ALL HALLWAYS COMPLETED! 🎉", True, (0, 255, 0))
        text2 = self.font.render("Great job!", True, (255, 255, 255))
        self.screen.blit(
            text1,
            (self.width // 2 - text1.get_width() // 2, self.height // 2 - 40),
        )
        self.screen.blit(
            text2,
            (self.width // 2 - text2.get_width() // 2, self.height // 2 + 10),
        )
        pygame.display.update()
        pygame.time.delay(3000)
        print("All hallways complete – exiting game.")
        pygame.quit()
        raise SystemExit

    def _flash_choice(self, choice):
        flash_color = (0, 255, 0)

        # DOOR BOUNDING BOXES (from hallway.png)
        LEFT_DOOR_X = 40
        RIGHT_DOOR_X = 595
        DOOR_Y = 85
        DOOR_WIDTH = 180
        DOOR_HEIGHT = 330

        x = LEFT_DOOR_X if choice == "left" else RIGHT_DOOR_X

        pygame.draw.rect(self.screen, flash_color, (x, DOOR_Y, DOOR_WIDTH, DOOR_HEIGHT), 6)
        pygame.display.update()
        pygame.time.delay(250)

    def _log_decision(
            self,
            hallway,
            trial,
            choice,
            correct_door,
            agent_filename,
            agent_name,
            agent_gender,
            agent_suggestion,
            agent_truthfulness,
            reaction_time_ms,
            compliance,
            health_at_choice,
    ):
        correct = (choice == correct_door)
        timestamp = datetime.datetime.now().isoformat()

        self.logwriter.writerow(
            [
                timestamp,
                self.participant_id,
                self.run_id,
                hallway + 1,
                trial,
                agent_filename,
                agent_name,
                agent_gender,
                agent_suggestion,
                agent_truthfulness,
                correct_door,
                choice,
                correct,
                int(reaction_time_ms),
                int(compliance),
                int(health_at_choice),
                int(self.health),  # health_after (will equal health_at_choice here; penalty applied after log)
                round(self.time_remaining / 1000, 2),
                ]
        )
        self.logfile.flush()

        try:
            import platform

            row = {
                "participant_id": self.participant_id,
                "run_id": self.run_id,
                "hallway": hallway + 1,
                "trial": trial,
                "agent_image": agent_filename,
                "agent_name": agent_name,
                "agent_gender": agent_gender,
                "agent_suggestion": agent_suggestion,
                "agent_truthfulness": agent_truthfulness,
                "correct_door": correct_door,
                "player_choice": choice,
                "correct": correct,
                "reaction_time_ms": reaction_time_ms,
                "compliance": compliance,
                "health_at_choice": health_at_choice,
                "health_after": self.health,
                "time_remaining": self.time_remaining / 1000
            }

            platform.window.saveTrialLog(row)

        except Exception as e:
            print("Supabase log skipped:", e)

    def _show_x_ray(self):
        pygame.draw.rect(self.screen, (210, 74, 210), (80, 80, 100, 400))
        pygame.draw.rect(self.screen, (100, 54, 100), (680, 80, 100, 400))

    def scale_to_fit(self, image, max_w, max_h):
        w, h = image.get_size()
        scale = min(max_w / w, max_h / h)
        new_size = (int(w * scale), int(h * scale))
        return pygame.transform.smoothscale(image, new_size)



def close_game():
    print("Closing game...")
    pygame.quit()
    raise SystemExit


async def main():
    game = Game(800, 800, num_levels=3)
    await game.run()
    print("----------------------SCRIPT COMPLETE----------------------")


if __name__ == "__main__":
    asyncio.run(main())
