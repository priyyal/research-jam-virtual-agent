from abc import ABC, abstractmethod
from collections import deque

import pygame

class Actor(ABC):
    def __init__(self, maze):
        self.x = 0
        self.y = 0
        self.maze = maze
        self.move_delay = 150
        self.last_move_time = pygame.time.get_ticks()
        self.color = (255, 255, 255)

    def move(self):
        """Moves the player based on key input, ensuring valid movement in the maze."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time < self.move_delay:
            return  # Don't move if the delay hasn't passed

        new_x, new_y = self._get_direction()
        if self.maze.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.last_move_time = current_time  # Reset timer on move

    @abstractmethod
    def _get_direction(self) -> tuple[int, int]:
        ...

    def draw(self):
        """Draws the player on the screen."""
        pygame.draw.rect(
            self.maze.screen, self.color,
            (self.x * self.maze.cell_size, self.y * self.maze.cell_size, self.maze.cell_size, self.maze.cell_size)
        )

class Player(Actor):
    def __init__(self, maze):
        super().__init__(maze)
        self.color = (0, 255, 0)

    def _get_direction(self):
        dx, dy = 0, 0
        # speed = 0.05

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_RIGHT]:
            dx = 1
        elif keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_DOWN]:
            dy = 1
        # dx *= speed
        # dy *= speed
        new_x, new_y = self.x + dx, self.y + dy
        return new_x, new_y

    def draw(self):
        # Draw Pac-Man as a yellow circle
        pygame.draw.circle(
            self.maze.screen,
            (255, 255, 0),   # yellow
            (
                self.x * self.maze.cell_size + self.maze.cell_size // 2,
                self.y * self.maze.cell_size + self.maze.cell_size // 2
            ),
            self.maze.cell_size // 2 - 4
        )



class Enemy(Actor):
    def __init__(self, maze, player):
        super().__init__(maze)
        self.color = (255, 0, 0)
        self.player = player

    def _get_direction(self):
        queue = deque([((self.x, self.y), [])])  # (current position, path taken)
        visited = set()

        while queue:
            (x, y), path = queue.popleft()
            if (x, y) == (self.player.x, self.player.y):
                if len(path) < 1:
                    continue
                return path[1]  # first element is current position, so get the next element

            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Check all possible moves (up, down, left, right)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if self.maze.is_walkable(nx, ny) and (nx, ny) not in visited:
                    queue.append(((nx, ny), path + [(x, y)]))

        raise IndexError('Error finding next decision for Enemy.')


    def draw(self):
        # Draw enemy as a red circle
        pygame.draw.circle(
            self.maze.screen,
            (255, 0, 0),   # red
            (
                self.x * self.maze.cell_size + self.maze.cell_size // 2,
                self.y * self.maze.cell_size + self.maze.cell_size // 2
            ),
            self.maze.cell_size // 2 - 4
        )
