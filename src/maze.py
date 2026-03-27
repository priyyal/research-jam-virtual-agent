import random
from collections import deque

import pygame


class Maze:
    def __init__(self, screen, complexity = 0, cell_size = 64) -> None:
        self.screen = screen
        self.num_cols = 12
        self.num_rows = 12
        screen_w = screen.get_width()
        screen_h = screen.get_height()

        self.cell_size = min(
            screen_w // self.num_cols,
            screen_h // self.num_rows
        )

        self.grid = [[1 for _ in range(self.num_cols)] for _ in range(self.num_rows)]  # 1 = wall, 0 = path
        self.start = (0, 0)

        # Generate maze using DFS
        stack = []
        start_x, start_y = 0, 0
        self.grid[start_y][start_x] = 0
        stack.append((start_x, start_y))

        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]  # Up, Down, Left, Right

        while stack:
            x, y = stack[-1]
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.num_cols and 0 <= ny < self.num_rows and self.grid[ny][nx] == 1:
                    self.grid[y + dy // 2][x + dx // 2] = 0  # Remove wall
                    self.grid[ny][nx] = 0
                    stack.append((nx, ny))
                    break
            else:
                # If no valid moves were found, backtrack
                stack.pop()

        self.goal = self._get_furthest_point()


    def draw(self):
        for y in range(self.num_rows):
            for x in range(self.num_cols):
                color = (255, 255, 255) if self.is_walkable(x, y) else (0, 0, 0)
                offset_x = (self.screen.get_width() - self.num_cols * self.cell_size) // 2
                offset_y = (self.screen.get_height() - self.num_rows * self.cell_size) // 2

                pygame.draw.rect(
                    self.screen,
                    color,
                    (
                        offset_x + x * self.cell_size,
                        offset_y + y * self.cell_size,
                        self.cell_size,
                        self.cell_size
                    )
                )


        pygame.draw.rect(self.screen, (0, 0, 255), (offset_x + self.goal[0] * self.cell_size, offset_y + self.goal[1] * self.cell_size, self.cell_size, self.cell_size))

    def is_walkable(self, x, y):
        """Checks if a position is walkable."""
        return 0 <= x < self.num_cols and 0 <= y < self.num_rows and self.grid[y][x] == 0


    def _get_furthest_point(self):
        # TODO: Code could be refactored to combine with other BFS, but leaving as is for now
        visited = set()
        queue = deque([(self.start[0], self.start[1], 0)])  # (x, y, distance)

        farthest_point = self.start
        max_distance = 0

        while queue:
            x, y, distance = queue.popleft()

            if (x, y) in visited:
                continue
            visited.add((x, y))

            # If this point is further than the current farthest point, update
            if distance > max_distance:
                max_distance = distance
                farthest_point = (x, y)

            # Explore neighbors
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if self.is_walkable(nx, ny) and (nx, ny) not in visited:
                    queue.append((nx, ny, distance + 1))

        return farthest_point
