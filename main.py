import os
import sys
from copy import deepcopy
import random

import pygame
from maze import Maze
from actors import Player, Enemy


class Game:
    def __init__(self, width, height, fps = 60, num_levels = 1) -> None:
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.num_levels = num_levels    # then each block is 9 trials
        self.image_filenames = [f for f in os.listdir('images/assistants') if f.endswith('.png')]

        # Game stats
        self.max_health = 100
        self.health = self.max_health
        self.max_time = 50  # seconds per hallway
        self.time_remaining = self.max_time * 1000  # milliseconds
        self.font = pygame.font.SysFont("Arial", 28)

    def run(self):
        hallway_image = pygame.image.load('images/hallway.png')
        hallway_image = pygame.transform.scale(hallway_image, (self.width, self.height))
        shrink_factor = 0.15

        self.time_remaining = self.max_time * 1000
        game_start_time = pygame.time.get_ticks()
        # --- MAIN LOOP: 3 Hallways --- #
        for level in range(self.num_levels):
            print(f"\n=== Entering Hallway {level + 1} ===")

            # 1️⃣ Pac-Man Maze first
            self._run_trial()

            # After maze, start hallway phase
            randomized_filenames = deepcopy(self.image_filenames)
            random.shuffle(randomized_filenames)

            #self.time_remaining = self.max_time * 1000
            #hallway_start_time = pygame.time.get_ticks()
            #peek_trials = random.sample(range(1, 10), 3)
            #print(f"Peek trials for hallway {level + 1}: {peek_trials}")

            for trial_index, filename in enumerate(randomized_filenames[:9], start=1):
                print(f"\nAgent {trial_index}/9 in Hallway {level + 1}")
                pygame.event.clear()  # clear leftovers

                assistant_image = pygame.image.load(f"images/assistants/{filename}")
                assistant_image = pygame.transform.scale(
                    assistant_image,
                    (assistant_image.get_width() * shrink_factor,
                     assistant_image.get_height() * shrink_factor)
                )
                direction = random.choice(['left', 'right'])
                text_bubble_image = pygame.image.load(f"images/{direction}-speech-bubble.png")
                text_bubble_image = pygame.transform.scale(
                    text_bubble_image,
                    (text_bubble_image.get_width() * shrink_factor,
                     text_bubble_image.get_height() * shrink_factor)
                )

                correct_door = random.choice(['left', 'right'])
                show_hallway = True

                #if trial_index in peek_trials:
                 #   print(f"Hint shown for agent {trial_index} (correct door: {correct_door})")
                  #  self._show_hint(correct_door)

                # --- HALLWAY LOOP (until choice made or time up) --- #
                while show_hallway:
                    dt = self.clock.tick(self.fps)
                    #self.time_remaining -= dt
                    elapsed_time = pygame.time.get_ticks() - game_start_time
                    self.time_remaining = (self.max_time*1000) - elapsed_time

                    self.screen.blit(hallway_image, (0, 0))
                    self.screen.blit(
                        assistant_image,
                        (self.width // 2 - assistant_image.get_width() // 2,
                         self.height // 2 - assistant_image.get_height() // 2)
                    )
                    self.screen.blit(
                        text_bubble_image,
                        (self.width // 2 - text_bubble_image.get_width() // 2,
                         self.height // 2 - text_bubble_image.get_height() - assistant_image.get_height() // 2)
                    )

                    self._draw_health_bar()
                    self._draw_timer_bar()

                    #timer ran out
                    if self.time_remaining <= 0:
                        self._game_over("You have to be quicker!")
                        return

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            close_game()

                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_LEFT:
                                self._flash_choice("left")
                                self._log_decision(level, trial_index, "left", correct_door)
                                if correct_door != 'left':
                                    self._update_health(-5)
                                show_hallway = False

                            elif event.key == pygame.K_RIGHT:
                                self._flash_choice("right")
                                self._log_decision(level, trial_index, "right", correct_door)
                                if correct_door != 'right':
                                    self._update_health(-5)
                                show_hallway = False

                            elif event.key == pygame.K_x:
                                self._show_x_ray()

                    if self.health <= 0:
                        self._game_over("You ran out of health!")
                        return

                    pygame.display.update()

            print(f"Completed Hallway {level + 1}")   # hallway finished

            # Short pause / transition before next maze
            if level < self.num_levels - 1:  # if not the last hallway
                self._hallway_complete_screen(level + 1)
            else:
                print("All hallways completed successfully!")
                self._final_victory_screen()
                return

        # After all 3 hallways done
        #print(" All hallways completed successfully!")
        #self._game_over("All hallways completed! Great job.")



        pygame.quit()

    def _run_trial(self):
        maze = Maze(self.screen)
        player = Player(maze)
        enemy = Enemy(maze, player)
        enemy_move_time = pygame.time.get_ticks()
        enemy_move_delay = 500 # milliseconds
        enemy_is_active = False

        while True:
            self.screen.fill("black")
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    close_game()

            if (player.x, player.y) == maze.goal:
                print('Goal reached!')
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
                            print('Player was caught!')
                            self._game_over("The enemy caught you!")
                            close_game()
                        enemy_move_time = pygame.time.get_ticks()
                    enemy.draw()

            pygame.display.update()
            self.clock.tick(self.fps)

    def _update_health(self, delta):
        self.health = max(0, min(self.max_health, self.health + delta))
        print(f"Health updated: {self.health}")
    """"
    def _show_hint(self, correct_door):
        #Briefly shows which door is correct.
        hint_color = (0, 100, 255)  # blue hint color
        width = 200
        height = 400
        y = self.height // 2 - height // 2

        if correct_door == "left":
            x = 80
        else:
            x = self.width - width - 80

        pygame.draw.rect(self.screen, hint_color, (x, y, width, height), 6)
        pygame.display.update()
        pygame.time.delay(1500)  # show for 2 seconds
    """


    def _draw_health_bar(self):
        bar_width = 300
        bar_height = 25
        x, y = 40, 40
        fill = (self.health/self.max_health) * bar_width
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
        text = self.font.render(f"Time Left: {int(self.time_remaining / 1000)}s", True, (255, 255, 255))
        self.screen.blit(text, (x, y - 30))

    def _game_over(self, message):
        """Show a Game Over screen and reset."""
        self.screen.fill((0, 0, 0))
        text1 = self.font.render("GAME OVER", True, (255, 0, 0))
        text2 = self.font.render(message, True, (255, 255, 255))
        self.screen.blit(text1, (self.width // 2 - text1.get_width() // 2, self.height // 2 - 40))
        self.screen.blit(text2, (self.width // 2 - text2.get_width() // 2, self.height // 2 + 10))
        pygame.display.update()
        pygame.time.delay(3000)
        print(message)
        self.health = self.max_health
        self.time_remaining = self.max_time * 1000

    def _hallway_complete_screen(self, next_hallway_number):
        """Show short message before next hallway begins."""
        self.screen.fill((0, 0, 0))
        msg = self.font.render(f"Hallway complete!", True, (0, 255, 0))
        next_msg = self.font.render(f"Entering Hallway {next_hallway_number + 1}...", True, (255, 255, 255))
        self.screen.blit(msg, (self.width // 2 - msg.get_width() // 2, self.height // 2 - 30))
        self.screen.blit(next_msg, (self.width // 2 - next_msg.get_width() // 2, self.height // 2 + 10))
        pygame.display.update()
        pygame.time.delay(2000)
        print(f"Transitioning to Hallway {next_hallway_number + 1}")

    def _final_victory_screen(self):
        """Display the final completion message."""
        self.screen.fill((0, 0, 0))
        text1 = self.font.render("🎉 ALL HALLWAYS COMPLETED! 🎉", True, (0, 255, 0))
        text2 = self.font.render("Great job!", True, (255, 255, 255))
        self.screen.blit(text1, (self.width // 2 - text1.get_width() // 2, self.height // 2 - 40))
        self.screen.blit(text2, (self.width // 2 - text2.get_width() // 2, self.height // 2 + 10))
        pygame.display.update()
        pygame.time.delay(3000)
        print("All hallways complete – exiting game.")
        pygame.quit()
        sys.exit()

    def _flash_choice(self, choice):
        """Flash the chosen door briefly for visual feedback."""
        flash_color = (0, 255, 0)  # bright green for now
        width = 200
        height = 400
        y = self.height // 2 - height // 2

        if choice == "left":
            x = 80
        else:
            x = self.width - width - 80

        pygame.draw.rect(self.screen, flash_color, (x, y, width, height), 5)
        pygame.display.update()
        pygame.time.delay(300)

    def _log_decision(self, hallway, trial, choice, correct_door):
        correct = (choice == correct_door)
        print(f"Hallway {hallway + 1}, Trial {trial}: chose {choice}, correct = {correct}, Health = {self.health}")

    def _show_x_ray(self):
        pygame.draw.rect(self.screen, (210, 74, 210), (80, 80, 100, 400))
        pygame.draw.rect(self.screen, (100, 54, 100), (680, 80, 100, 400))

def close_game():
    print('Closing game...')
    pygame.quit()
    sys.exit()


def main():
    # Ghost
    # Pacman
    # 10 assistants
    # Maze
    Game(800, 800, num_levels=3).run()
    print('----------------------SCRIPT COMPLETE----------------------')


if __name__ == "__main__":
    main()
