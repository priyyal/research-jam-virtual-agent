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

    def run(self):
        hallway_image = pygame.image.load('images/hallway.png')
        hallway_image = pygame.transform.scale(hallway_image, (self.width, self.height))
        shrink_factor = 0.15

        for _ in range(self.num_levels):
            randomized_filenames = deepcopy(self.image_filenames)
            random.shuffle(randomized_filenames)

            for filename in randomized_filenames:
                self._run_trial()
                assistant_image = pygame.image.load(f"images/assistants/{filename}")  # randomly selected
                assistant_image = pygame.transform.scale(assistant_image, (assistant_image.get_width() * shrink_factor, assistant_image.get_height() * shrink_factor))
                direction = random.choice(['left', 'right'])
                text_bubble_image = pygame.image.load(f"images/{direction}-speech-bubble.png")
                text_bubble_image = pygame.transform.scale(text_bubble_image, (text_bubble_image.get_width() * shrink_factor, text_bubble_image.get_height() * shrink_factor))
                show_hallway = True
                while show_hallway:
                    self.screen.blit(hallway_image, (0, 0))
                    self.screen.blit(assistant_image, (self.width // 2 - assistant_image.get_width() // 2, self.height // 2 - assistant_image.get_height() // 2))
                    self.screen.blit(text_bubble_image, (self.width // 2 - text_bubble_image.get_width() // 2, self.height // 2 - text_bubble_image.get_height() - assistant_image.get_height() // 2))

                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            close_game()

                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_LEFT:
                                print('left')
                                show_hallway = False
                            elif event.key == pygame.K_RIGHT:
                                print('right')
                                show_hallway = False
                            elif event.key == pygame.K_x:
                                print('x-ray')
                                self._show_x_ray()

                    pygame.display.update()
                    self.clock.tick(self.fps)

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
                            return
                        enemy_move_time = pygame.time.get_ticks()
                    enemy.draw()

            pygame.display.update()
            self.clock.tick(self.fps)

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
    Game(800, 800).run()
    print('----------------------SCRIPT COMPLETE----------------------')


if __name__ == "__main__":
    main()
