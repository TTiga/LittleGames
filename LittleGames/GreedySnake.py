# -*- encoding: utf-8 -*-

import pygame

import enum
import random
import sys
from collections import deque

FPS = 100
ROWS = 35
COLUMNS = 40
CELL_SIZE = 12
BACKGROUND_COLOR = (229, 229, 229)
SCREEN_HEIGHT = ROWS * CELL_SIZE
SCREEN_WIDTH = COLUMNS * CELL_SIZE


@enum.unique
class Direction(enum.IntEnum):
    UP = -1
    DOWN = 1
    LEFT = -2
    RIGHT = 2


def is_opposite_direction(d1, d2):
    return d1 + d2 == 0


Gkey_to_direction = {
    pygame.K_UP: Direction.UP,
    pygame.K_DOWN: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT
}


def get_direction(key):
    return Gkey_to_direction.get(key, None)


class Snake(object):

    HEAD_COLOR = (102, 102, 102)
    BODY_COLOR = (51, 51, 51)
    UPDATE_RATE = 90   # milliseconds
    GROWING_STEPS = 4

    def __init__(self, cols, rows, back_color, cell_size):
        self.cols, self.rows = cols, rows
        self.back_color = back_color
        self.head = [cols//2, rows-2]
        self.body = deque([[cols//2, rows-1]])
        self.cell_size = cell_size
        self.direction = Direction.UP
        self.growing = False
        self.turning = False
        self.growing_steps = Snake.GROWING_STEPS

        cell_rect = (0, 0, self.cell_size, self.cell_size)
        self.head_cell = pygame.Surface((self.cell_size, self.cell_size))
        self.head_cell.fill(back_color)
        pygame.draw.rect(self.head_cell, Snake.HEAD_COLOR, cell_rect, 1)

        self.body_cell = pygame.Surface((self.cell_size, self.cell_size))
        pygame.draw.rect(self.body_cell, Snake.BODY_COLOR, cell_rect)
        pygame.draw.rect(self.body_cell, back_color, cell_rect, 1)

    def init(self):
        self.__init__(self.cols, self.rows, self.back_color, self.cell_size)

    def get_head(self):
        return self.head

    def get_body(self):
        return self.body

    def get_head_pos(self):
        col, row = self.head
        return (col*self.cell_size, row*self.cell_size)

    def turn(self, direction):
        if not isinstance(direction, Direction):
            raise TypeError("Invalid direction")
        if not is_opposite_direction(self.direction, direction) and not self.turning:
            self.direction = direction
            self.turning = True

    def grow(self):
        self.growing = True
        self.growing_steps = Snake.GROWING_STEPS

    def go_ahead(self):
        self.body.appendleft(self.head[:])
        if self.direction == Direction.UP:
            self.head[1] -= 1
        elif self.direction == Direction.DOWN:
            self.head[1] += 1
        elif self.direction == Direction.LEFT:
            self.head[0] -= 1
        elif self.direction == Direction.RIGHT:
            self.head[0] += 1
        if self.turning:
            self.turning = False

    def run(self):
        self.go_ahead()
        if self.growing:
            self.growing_steps -= 1
            self.growing = not (self.growing_steps == 0)
        else:
            self.body.pop()

    def draw(self, surface):
        surface.blit(self.head_cell, self.get_head_pos())
        for col, row in self.body:
            surface.blit(self.body_cell, (col*self.cell_size, row*self.cell_size))


def get_apple():
    col = random.randint(0, COLUMNS-1)
    row = random.randint(0, ROWS-1)
    return pygame.Rect(col*CELL_SIZE, row*CELL_SIZE, CELL_SIZE-1, CELL_SIZE-1)


class GameState(enum.Enum):
    PLAYING = 0
    PAUSE = 1
    WIN = 2
    FAIL = 3


class Game(object):

    def __init__(self):
        pygame.display.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.user_event_id = pygame.USEREVENT + 1

        self.event_handlers = {}
        self.key_handlers = {}
        self.add_handler(pygame.QUIT, lambda event: sys.exit())
        self.add_handler(pygame.KEYDOWN, self.key_down_handler)
        self.add_timer_handler(Snake.UPDATE_RATE, self.run_snake)

        self.add_key_handler(pygame.K_UP, self.key_direction_handler)
        self.add_key_handler(pygame.K_DOWN, self.key_direction_handler)
        self.add_key_handler(pygame.K_LEFT, self.key_direction_handler)
        self.add_key_handler(pygame.K_RIGHT, self.key_direction_handler)
        self.add_key_handler(pygame.K_p, self.key_p_handler)
        self.add_key_handler(pygame.K_SPACE, self.key_space_handler)

        self.init()

    def init(self):
        self.state = GameState.PLAYING
        self.snake = Snake(COLUMNS, ROWS, BACKGROUND_COLOR, CELL_SIZE)
        self.apple = self.get_apple()
        self.total_time_passed = 0.0
        self.score = 0
        self.refresh_caption("Greedy Snake Score: {0}".format(self.score))

    def refresh_caption(self, caption):
        pygame.display.set_caption(caption)

    def run_snake(self, event):
        if self.state == GameState.PLAYING:
            self.snake.run()

    def add_handler(self, event_type, handler):
        self.event_handlers[event_type] = handler

    def add_key_handler(self, key_value, handler):
        self.key_handlers[key_value] = handler

    def add_timer_handler(self, milliseconds, handler):
        new_event_id = self.user_event_id
        self.user_event_id += 1
        self.add_handler(new_event_id, handler)
        pygame.time.set_timer(new_event_id, milliseconds)

    def key_down_handler(self, event):
        handler = self.key_handlers.get(event.key, None)
        if handler is not None:
            handler(event)

    def key_direction_handler(self, event):
        if self.state == GameState.PLAYING:
            self.snake.turn(get_direction(event.key))

    def key_p_handler(self, event):
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSE
            self.refresh_caption("Greedy Snake Pause...")
        elif self.state == GameState.PAUSE:
            self.state = GameState.PLAYING
            self.refresh_caption("Greedy Snake Score: {0}".format(self.score))

    def key_space_handler(self, event):
        if self.state == GameState.WIN or self.state == GameState.FAIL:
            self.init()

    def get_apple(self):
        # TODO : refine Game.getapple()
        if self.is_win():
            return None
        while True:
            apple = get_apple()
            apple_pos = list(apple.topleft)
            apple_pos[0] //= CELL_SIZE
            apple_pos[1] //= CELL_SIZE
            if apple_pos != self.snake.get_head() and (not apple_pos in self.snake.get_body()):
                return apple

    def is_win(self):
        return len(self.snake.get_body()) + 1 == ROWS * COLUMNS

    def is_fail(self):
        return self.snake.get_head() in self.snake.get_body() or (
                not 0 <= self.snake.get_head()[0] < COLUMNS) or (
                not 0 <= self.snake.get_head()[1] < ROWS)

    def run(self):
        time_passed = self.clock.tick(FPS) / 1000.
        self.total_time_passed += time_passed
        for event in pygame.event.get():
            handler = self.event_handlers.get(event.type, None)
            if handler is not None:
                handler(event)
        if self.state == GameState.PLAYING:
            if self.apple.collidepoint(self.snake.get_head_pos()):
                self.snake.grow()
                self.apple = self.get_apple()
                self.score += 5
                self.refresh_caption("Greedy Snake Score: {0}".format(self.score))
            if self.is_win():
                self.state = GameState.WIN
                self.refresh_caption("You Win! Totoal time used {0:.3}!".format(self.total_time_passed))
            elif self.is_fail():
                self.state = GameState.FAIL
                self.refresh_caption("Game Over! Score: {0}!".format(self.score))

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        self.snake.draw(self.screen)
        if self.apple is not None:
            self.screen.fill((255, 0, 0), self.apple)
        pygame.display.update()


def main():
    game = Game()
    while True:
        game.run()
        game.draw()


if __name__ == '__main__':
    main()
