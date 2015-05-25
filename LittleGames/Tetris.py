#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import random
import sys
import pygame
from pygame.locals import *

# game configuration
FPS               = 60        # frames per second
CELL_SIZE         = 17        # size of cells of a tetromino
ROWS              = 20
COLUMNS           = 10
GAME_AREA_WIDTH   = COLUMNS * CELL_SIZE
GAME_AREA_HEIGHT  = ROWS * CELL_SIZE
MENU_WIDTH        = 6 * CELL_SIZE
MENU_HEIGHT       = GAME_AREA_HEIGHT
SCREEN_WIDTH      = GAME_AREA_WIDTH + MENU_WIDTH
SCREEN_HEIGHT     = GAME_AREA_HEIGHT
NEXT_AREA_HEIGHT  = 5 * CELL_SIZE
LEVEL_AREA_HEIGHT = 4 * CELL_SIZE
GOAL_AREA_HEIGHT  = 4 * CELL_SIZE

TETROMINO_COLOR      = (244, 119,  89)
BACKGROUND_COLOR     = ( 50,  50,  50)
CELL_FRAME_COLOR     = ( 20,  20,  20)
DASH_LINE_COLOR      = (10,   50, 255)
FONT_COLOR           = (255, 255,   0)
LEVEL_FONT_COLOR     = (  0, 255, 255)
GHOST_COLOR          = (255, 255, 255)
HELP_TEXT_COLOR      = (255, 255, 255)
WIN_TEXT_COLOR       = (255, 255,   0)
GAME_OVER_TEXT_COLOR = (  0,   0, 255)

Ghelp_text = (
    "{:>5s} --> {:<s}".format("ESC", "exit"),
    "{:>5s} --> {:<s}".format("P", "pause/continue"),
    "{:>5s} --> {:<s}".format("ENTER", "restart"),
    "{:>5s} --> {:<s}".format("UP", "rotate"),
    "{:>5s} --> {:<s}".format("LEFT", "move left"),
    "{:>5s} --> {:<s}".format("RIGHT", "move right"),
    "{:>5s} --> {:<s}".format("DOWN", "soft drop"),
    "{:>5s} --> {:<s}".format("SPACE", "hard drop"),
    "",
    "Press <P> to begin"
)

Gwin_text = (
    "{}".format("YOU WIN!"),
    ""
)

Ggame_over_text = (
    "{}".format("GAME OVER!"),
    ""
)

# tetrominoes
# Assuming all cells of a tetromino ard laid out on a
# 4*4 grid, where each cell is either occupied or not.
# And so that we can represent each tetromino as a si-
# mple 16 bit integer. This idea come from
# http://codeincomplete.com/posts/2011/10/10/javascript_tetris/
Gtetrominoe_I = {
    'blocks': (0x0F00, 0x2222, 0x00F0, 0x4444),
}
Gtetrominoe_J = {
    'blocks': (0x8E00, 0x6440, 0x0E20, 0x44C0),
}
Gtetrominoe_L = {
    'blocks': (0x2E00, 0x4460, 0x0E80, 0xC440),
}
Gtetrominoe_O = {
    'blocks': (0x6600, 0x6600, 0x6600, 0x6600),
}
Gtetrominoe_S = {
    'blocks': (0x6C00, 0x4620, 0x06C0, 0x8C40),
}
Gtetrominoe_T = {
    'blocks': (0x4E00, 0x4640, 0x0E40, 0x4C40),
}
Gtetrominoe_Z = {
    'blocks': (0xC600, 0x2640, 0x0C60, 0x4C80),
}

Gtetrominoes = (
    Gtetrominoe_I,
    Gtetrominoe_J,
    Gtetrominoe_L,
    Gtetrominoe_O,
    Gtetrominoe_S,
    Gtetrominoe_T,
    Gtetrominoe_Z
)

# A simple function to choose a monospaced font. Maybe wrong :D
def get_font():
    if sys.platform.startswith('linux'):
        return 'monospace'
    elif sys.platform.startswith('win'):
        return 'consolas'
    elif sys.platform.startswith('os'):
        return 'monaco'
    else:
        return pygame.font.get_default_font()

def set_static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

@set_static_var('tetrominoes', [])
def random_tetromino():
    # random_tetromino.tetrominoes must be initialized first
    if random_tetromino.tetrominoes == []:
        random_tetromino.tetrominoes = [
            i for i in range(7) for _ in range(4)
        ]
        random.shuffle(random_tetromino.tetrominoes)
    random_index = random_tetromino.tetrominoes.pop()
    return Gtetrominoes[random_index]

def map_to_each_cell(tetromino, grid_pos, direction, map_fn, aux_data=None):
    # map_fn must have the form --> map_fn(grid_x, grid_y, aux_data)
    # where grid_x and grid_y denotes the position of a cell of tetromino
    bit   = 0x8000
    block = tetromino['blocks'][direction]
    col, row = 0, 0
    grid_x, grid_y = grid_pos
    while bit > 0:
        if block & bit:
            map_fn(grid_x+col, grid_y+row, aux_data)
        col += 1
        bit >>= 1
        if (col == 4):
            col = 0
            row += 1

def grid_pos_to_cell_rect(grid_x, grid_y):
    return (grid_x*CELL_SIZE, grid_y*CELL_SIZE, CELL_SIZE, CELL_SIZE)

def draw_cell(surface, cell_rect):
    pygame.draw.rect(surface, TETROMINO_COLOR, cell_rect, 0)
    pygame.draw.rect(surface, CELL_FRAME_COLOR, cell_rect, 1)

def _draw_tetromino_aux(grid_x, grid_y, surface):
    draw_cell(surface, grid_pos_to_cell_rect(grid_x, grid_y))

def draw_tetromino(surface, grid_pos, tetromino, direction):
    # grid_pos means the (left, top) of the 4*4 grid
    map_to_each_cell(tetromino, grid_pos, direction, _draw_tetromino_aux, surface)

# This class manages level and grade.
class Level(object):

    _level_pos = (GAME_AREA_WIDTH + CELL_SIZE*1.5,
            NEXT_AREA_HEIGHT + CELL_SIZE*2)
    _goal_pos  = (GAME_AREA_WIDTH + CELL_SIZE*2.5,
            NEXT_AREA_HEIGHT + LEVEL_AREA_HEIGHT + CELL_SIZE*2)
    _score_pos = (GAME_AREA_WIDTH + CELL_SIZE,
            NEXT_AREA_HEIGHT + LEVEL_AREA_HEIGHT + GOAL_AREA_HEIGHT + CELL_SIZE*3)
    _top_level = 15
    _lines_needed_per_level = 3
    _scores = (100, 300, 500, 800)
    _init_speed = 0.6
    _fasted_speed = 0.05
    _speed_increment = (_fasted_speed-_init_speed)/float((_top_level-1))

    def __init__(self, screen):
        self._level = 1
        self._goal  = 3
        self._score = 0
        self._speed = self._init_speed  # seconds needed to drop one row
        self._screen = screen

    def get_speed(self):
        return self._speed

    def get_score(self):
        return self._score

    def add_score(self, score):
        self._score += score

    # used to add score according to lines removed
    #   and to check if the player wins.
    # score = self._scores[removed_lines-1] * (self._level*0.5 + 0.5)
    def remove_lines(self, removed_lines):
        score = self._scores[removed_lines-1] * (self._level*0.5 + 0.5)
        self.add_score(int(score))
        self._goal -= removed_lines
        if self._goal <= 0:
            return self._level_up()
        return False

    def draw(self, font):
        level_texture = font.render("{0}/{1}".format(
                str(self._level), self._top_level), True, LEVEL_FONT_COLOR)
        goal_texture  = font.render(str(self._goal), True, LEVEL_FONT_COLOR)
        grade_texture = font.render(str(self._score).zfill(6), True, LEVEL_FONT_COLOR)
        self._screen.blit(level_texture, self._level_pos)
        self._screen.blit(goal_texture, self._goal_pos)
        self._screen.blit(grade_texture, self._score_pos)

    def _level_up(self):
        self._level += 1
        if self._level == self._top_level + 1:
            return True
        self._goal = self._level * self._lines_needed_per_level
        self._speed += self._speed_increment
        return False

# Use this class to manage tetrominoes.
class TetrisManager(object):

    _init_moving_pos = [3, 0]
    _next_pos = [COLUMNS + 1, 2]

    def __init__(self, screen, font):
        self._grid           = [ [None]*COLUMNS for _ in xrange(ROWS) ]
        self._curr_pos       = self._init_moving_pos[:]
        self._direction      = 0
        self._screen         = screen
        self._font           = font
        self._moving         = random_tetromino()
        self._next           = random_tetromino()
        self._time           = 0.0
        self._level          = Level(screen)
        self._is_pause       = True
        self._is_win         = False
        self._is_game_over   = False
        self._pause_textures = self._get_pause_textures()

    def set_time(self, time_passed_seconds):
        self._time += time_passed_seconds

    def get_speed(self):
        return self._level.get_speed()

    def is_pause(self):
        return self._is_pause

    def pause(self):
        self._is_pause = not self._is_pause

    def is_game_over(self):
        return self._is_game_over

    def game_over(self):
        self._draw_game_over_text()

    def is_win(self):
        return self._is_win

    def win(self):
        self._draw_win_text()

    def draw_pause(self):
        self._screen.fill(BACKGROUND_COLOR)
        for i, texture in enumerate(self._pause_textures):
            self._screen.blit(texture, (CELL_SIZE*2, (i+2)*1.5*CELL_SIZE))

    def draw(self):
        self._draw_ghost()
        self._draw_curr_tetromino()
        self._draw_next_tetromino()
        self._level.draw(self._font)
        for row in xrange(ROWS):
            for col in xrange(COLUMNS):
                if self._grid[row][col]:
                    draw_cell(self._screen, grid_pos_to_cell_rect(col, row))

    def restart(self):
        self.__init__(self._screen, self._font)
        self._is_pause = True

    def remove_lines(self):
        self._update_curr_tetromino()
        removed_lines = self._check_lines()
        if removed_lines > 0:
            self._is_win = self._level.remove_lines(removed_lines)
        return removed_lines

    def drop_freely(self):
        if (self._time > self.get_speed()):
            self._time -= self.get_speed()
            self._drop()

    def softland(self):
        y = self._curr_pos[1]
        is_unoccupied = self.move('down')
        self._add_score(self._curr_pos[1]-y)
        if not is_unoccupied:
            self.remove_lines()

    def hardland(self):
        y = self._curr_pos[1]
        while self.move('down'):
            pass
        self._add_score((self._curr_pos[1]-y)*2)
        self.remove_lines()

    def move(self, direction):
        x, y = self._curr_pos
        if direction == 'left':
            x -= 1
        elif direction == 'right':
            x += 1
        elif direction == 'down':
            y += 1
        else:
            raise ValueError("direction must be 'left', 'right' or 'down'")

        if self.is_unoccupied((x, y)):
            self._curr_pos[0] = x
            self._curr_pos[1] = y
            return True
        return False

    def rotate(self):
        old_direction = self._direction
        self._direction = (self._direction+1) % 4
        if not self.is_unoccupied(self._curr_pos):
            self._direction = old_direction

    def is_unoccupied(self, pos):
        result = []
        map_to_each_cell(self._moving, pos,
            self._direction, self._is_cell_unoccupied, result)
        return all(result)

    def _is_cell_unoccupied(self, x, y, result):
        if (0 <= x < COLUMNS) and (0 <= y < ROWS) and self._get_block(x, y):
            result.append(True)
        else:
            result.append(False)

    def _get_block(self, x, y):
        if self._grid[y][x] == None:
            return True
        else: return False

    def _add_a_cell(self, x, y, aux_data=None):
        self._grid[y][x] = True

    def _add_curr_tetromino(self):
        map_to_each_cell(self._moving, self._curr_pos, self._direction,
            self._add_a_cell)

    def _add_score(self, score):
        self._level.add_score(score)

    def _draw_curr_tetromino(self):
        draw_tetromino(self._screen, self._curr_pos, self._moving, self._direction)

    def _draw_next_tetromino(self):
        draw_tetromino(self._screen, self._next_pos, self._next, 0)

    def _draw_ghost_aux(self, x, y, aux_data=None):
        pygame.draw.rect(self._screen, GHOST_COLOR, grid_pos_to_cell_rect(x, y), 1)

    def _draw_ghost(self):
        old_pos = self._curr_pos[:]
        while self.move('down'):
            pass
        map_to_each_cell(self._moving, self._curr_pos, self._direction,
                         self._draw_ghost_aux)
        self._curr_pos = old_pos

    def _drop(self):
        if not self.move('down'):
            self.remove_lines()

    def _check_lines(self):
        removed_lines = 0
        row = ROWS - 1
        while row > 0:
            if all(self._grid[row]):
                for i in reversed(xrange(1, row+1)):
                    self._grid[i] = self._grid[i-1][:]
                row += 1        # check this line again since it was changed
                removed_lines += 1
            row -= 1
        if all(self._grid[0]): self._grid[0] = [None] * COLUMNS
        return removed_lines

    def _update_curr_tetromino(self):
        self._add_curr_tetromino()
        self._moving = self._next
        self._next = random_tetromino()
        self._curr_pos = self._init_moving_pos[:]
        self._direction = 0
        if not self.is_unoccupied(self._curr_pos):
            self._is_game_over = True

    def _get_pause_textures(self):
        font = pygame.font.SysFont(get_font(), CELL_SIZE, False, False)
        textures = []
        for text in Ghelp_text:
            textures.append(font.render(text, True, HELP_TEXT_COLOR))
        return textures

    def _draw_text(self, texts, color, size):
        self._screen.fill(BACKGROUND_COLOR)
        font = pygame.font.SysFont(get_font(), CELL_SIZE*2, True, True)
        textures = []
        for text in texts:
            textures.append(font.render(text, True, color))
        score_text = str(self._level.get_score()).center(size)
        textures.append(font.render(score_text, True, color))
        for i, texture in enumerate(textures):
            self._screen.blit(texture, (CELL_SIZE*3, (i+6)*CELL_SIZE))

    def _draw_win_text(self):
        self._draw_text(Gwin_text, WIN_TEXT_COLOR, 8)

    def _draw_game_over_text(self):
        self._draw_text(Ggame_over_text, GAME_OVER_TEXT_COLOR, 10)

# UI
# TODO: The screen should be updated portion by portion
# draw_fonts(screen, font)
#     includes <Next>, <Level> and <Goal>
# drae_background(screen)
#     screen.fill(BACKGROUND_COLOR)
#    draw_matrices(screen)
#    draw_dashed_line_frame(screen)

def draw_fonts(screen, font):
    next_texture  = font.render("Next", True, FONT_COLOR)
    level_texture = font.render("Level", True, FONT_COLOR)
    goal_texture  = font.render("Goal", True, FONT_COLOR)

    screen.blit(next_texture,
        (GAME_AREA_WIDTH + CELL_SIZE*1.5,
         CELL_SIZE/2))
    screen.blit(level_texture,
        (GAME_AREA_WIDTH + CELL_SIZE*1.5,
         CELL_SIZE/2 + NEXT_AREA_HEIGHT))
    screen.blit(goal_texture,
        (GAME_AREA_WIDTH + CELL_SIZE*1.5,
         CELL_SIZE/2 + LEVEL_AREA_HEIGHT + NEXT_AREA_HEIGHT))

# draw a dashed line which is perpendicular to the surface.
def draw_dashed_line(surface, color, start_pos, end_pos, dashed_len=5, width=2):
    if start_pos[0] == end_pos[0]:
        length = abs(end_pos[1]-start_pos[1])
        for i in range(0, length//dashed_len, 2):
            pygame.draw.line(surface, color,
                (start_pos[0], start_pos[1] + dashed_len*i),
                (start_pos[0], start_pos[1] + dashed_len*(i+1)),
                width)

    elif start_pos[1] == end_pos[1]:
        length = abs(end_pos[0]-start_pos[0])
        for i in range(0, length//dashed_len, 2):
            pygame.draw.line(surface, color,
                (start_pos[0] + dashed_len*i, start_pos[1]),
                (start_pos[0] + dashed_len*(i+1), start_pos[1]),
                width)
    else:
        raise ValueError("the dashed line must be perpendicular to the surface.")

def draw_dashed_line_frame(screen):
    draw_dashed_line(screen, DASH_LINE_COLOR,
        (GAME_AREA_WIDTH, 0),
        (GAME_AREA_WIDTH, GAME_AREA_HEIGHT))

    draw_dashed_line(screen, DASH_LINE_COLOR,
        (GAME_AREA_WIDTH, NEXT_AREA_HEIGHT),
        (SCREEN_WIDTH, NEXT_AREA_HEIGHT))

    draw_dashed_line(screen, DASH_LINE_COLOR,
        (GAME_AREA_WIDTH, NEXT_AREA_HEIGHT + LEVEL_AREA_HEIGHT),
        (SCREEN_WIDTH, NEXT_AREA_HEIGHT + LEVEL_AREA_HEIGHT))

    draw_dashed_line(screen, DASH_LINE_COLOR,
        (GAME_AREA_WIDTH, NEXT_AREA_HEIGHT + LEVEL_AREA_HEIGHT + GOAL_AREA_HEIGHT),
        (SCREEN_WIDTH, NEXT_AREA_HEIGHT + LEVEL_AREA_HEIGHT + GOAL_AREA_HEIGHT))

def draw_matrices(screen):
    for x in xrange(CELL_SIZE, GAME_AREA_WIDTH, CELL_SIZE):
        pygame.draw.line(screen, CELL_FRAME_COLOR,
            (x, 0), (x, GAME_AREA_HEIGHT), 2)

    for y in xrange(CELL_SIZE, GAME_AREA_HEIGHT, CELL_SIZE):
        pygame.draw.line(screen, CELL_FRAME_COLOR,
            (0, y), (GAME_AREA_WIDTH, y), 2)

    for y in xrange(CELL_SIZE, GAME_AREA_HEIGHT, CELL_SIZE):
        for x in xrange(CELL_SIZE, GAME_AREA_WIDTH, CELL_SIZE):
            pygame.draw.circle(screen, CELL_FRAME_COLOR, (x, y), 3)

def draw_background(screen):
    screen.fill(BACKGROUND_COLOR)
    draw_matrices(screen)
    draw_dashed_line_frame(screen)

# Handle game events
#     Quit --> exit()
#     KEYDOWN --> Gkeydown_handlers[event.key](event.key)
def key_up_handler(manager):
    manager.rotate()

def key_down_handler(manager):
    manager.softland()

def key_left_handler(manager):
    manager.move('left')

def key_right_handler(manager):
    manager.move('right')

def key_space_handler(manager):
    manager.hardland()

def key_p_handler(manager):
    manager.pause()

def key_esc_handler(manager):
    exit()

def key_enter_handler(manager):
    manager.restart()

Gkeydown_handlers = {
    K_UP    : key_up_handler,
    K_DOWN  : key_down_handler,
    K_LEFT  : key_left_handler,
    K_RIGHT : key_right_handler,
    K_SPACE : key_space_handler,
    K_p     : key_p_handler,
    K_ESCAPE: key_esc_handler,
    K_RETURN: key_enter_handler
}

def handle_events(manager):
    drop = True
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
        if event.type == KEYDOWN:
            Gkeydown_handlers.get(event.key, lambda _: None)(manager)
            drop = False
    if drop:
        manager.drop_freely()

def main():

    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont(get_font(), int(1.3*CELL_SIZE), False, True)
    pygame.key.set_repeat(100, 50)
    manager = TetrisManager(screen, font)

    while True:
        time_passed_seconds = clock.tick(FPS)/1000.
        pygame.display.set_caption("Tetris    FPS: %.2f" % clock.get_fps())
        handle_events(manager)
        pygame.display.update()

        if not manager.is_pause():
            if manager.is_win():
                manager.win()
            elif manager.is_game_over():
                manager.game_over()
            else:
                manager.set_time(time_passed_seconds)
                draw_background(screen)
                draw_fonts(screen, font)
                manager.draw()
        else:
            manager.draw_pause()

if __name__ == '__main__':
    main()
