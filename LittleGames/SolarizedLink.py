#! /usr/bin/env python
# -*- encoding: utf-8 -*-

import copy
import math
import random
import sys

import pygame
from pygame.locals import *


BLACK  = (  0,   0,   0)
RED    = (255,   0,   0)
ORANGE = (255, 204,   0)
WHITE  = (255, 255, 255)
BLUE   = (  0,   0, 255)

# game configuration
BACKGROUND_COLOR    = (253, 246, 227)
GRID_COLOR          = ( 38, 139, 210)
FPS                 = 30
LEFT_POS            = 50
TOP_POS             = 50
CELL_SIZE           = 40
ROWS_COUNT          = 12
COLS_COUNT          = 12
TILE_SPECIES        = ROWS_COUNT * 2
TILE_COUNT          = COLS_COUNT // 2    # per species
SIDEBAR_WIDTH       = 80
GAME_TIME           = 300    # seconds
SCREEN_WIDTH        = CELL_SIZE * COLS_COUNT + LEFT_POS * 2 + SIDEBAR_WIDTH
SCREEN_HEIGHT       = CELL_SIZE * ROWS_COUNT + TOP_POS * 2
# display message
MESSAGE_FONT_SIZE   = 20
MESSAGE_FONT_COLOR  = BLACK
# linked lines
LINKED_LINE_COLOR   = ORANGE
LINKED_LINE_WIDTH   = 3
# buttons' configuration
BUTTON_TITLE_SIZE   = 14
Gbutton_start_y     = TOP_POS + BUTTON_TITLE_SIZE*2
BUTTON_RADIUS       = 40
BUTTON_COLOR        = (190, 200, 200)
BUTTON_LEFT         = SCREEN_WIDTH - SIDEBAR_WIDTH - 10
BUTTON_RECT_SIZE    = BUTTON_RADIUS * 2
# timer
TIMER_POS = (BUTTON_LEFT, Gbutton_start_y)
# hints button
HINT_COLOR         = ( 12, 199, 110)
HINT_COUNT         = 6
HINT_FONT_SIZE     = BUTTON_RADIUS
HINT_BUTTON_RECT   = (BUTTON_LEFT,
                       Gbutton_start_y + 3*BUTTON_RADIUS,
                       BUTTON_RECT_SIZE,
                       BUTTON_RECT_SIZE)
# pause button
PAUSE_COLOR         = (125, 100, 110)
PAUSE_RECT1         = (BUTTON_RADIUS/2,  BUTTON_RADIUS/2, 10, BUTTON_RADIUS)
PAUSE_RECT2         = (BUTTON_RADIUS+5,  BUTTON_RADIUS/2, 10, BUTTON_RADIUS)
PAUSE_TRIANGLE      = [(BUTTON_RADIUS/2, BUTTON_RADIUS/2),
                       (BUTTON_RADIUS/2, BUTTON_RADIUS/2+BUTTON_RADIUS),
                       (BUTTON_RADIUS/2 + BUTTON_RADIUS, BUTTON_RADIUS)]
PAUSE_BUTTON_RECT   = (BUTTON_LEFT,
                       Gbutton_start_y + 6*BUTTON_RADIUS,
                       BUTTON_RECT_SIZE,
                       BUTTON_RECT_SIZE)
# restart button
RESTART_COLOR       = (  0,  43,  54)
RESTART_BUTTON_RECT = (BUTTON_LEFT,
                       Gbutton_start_y + 9*BUTTON_RADIUS,
                       BUTTON_RECT_SIZE,
                       BUTTON_RECT_SIZE)
RESTART_POINTS1     = [(20, 20), (60, 60)]
RESTART_POINTS2     = [(60, 20), (20, 60)]


class Grid(object):

    def __init__(self, rows, columns, init_value=None):
        self._data = [[init_value] * columns for _ in range(rows)]
        self._rows = rows
        self._cols = columns

    @classmethod
    def from_lists(cls, lists):
        rows = len(lists)
        cols = len(lists[0])
        grid = cls(rows, cols)
        grid._data = copy.deepcopy(lists)
        return grid

    def _validate_index(self, index):
        if not isinstance(index, int):
            raise TypeError("grid indices must be integers, not {0}".format(type(index)))
        if not 0 <= index < self._rows:
            raise IndexError("grid index out of range")

    def __getitem__(self, index):
        self._validate_index(index)
        return self._data[index]

    def __setitem__(self, index, value):
        self._validate_index(index)
        self._data[index] = value

    def rows(self):
        return self._rows

    def cols(self):
        return self._cols

    def randomize(self):
        indices = list(self.valid_indices())
        max_index = len(indices) - 1
        for i, pos in enumerate(indices):
            random_index = random.randint(i, max_index)
            r1, c1 = pos
            r2, c2 = indices[random_index]
            grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]

    def valid_indices(self):
        return ((row, col) for row in range(self._rows)
                             for col in range(self._cols)
                               if self._data[row][col] is not None)

    def get_value(self, grid_pos):
        row, col = grid_pos
        return self._data[row][col]

    def set_value(self, grid_pos, value):
        row, col = grid_pos
        self._data[row][col] = value

    def set_all(self, value):
        for row in range(self._rows):
            for col in range(self._cols):
                self._data[row][col] = value

    def set_row(self, row_index, value):
        self[row_index] = [value] * self._cols

    def get_row(self, row_index):
        return self._data[row_index][:]

    def set_col(self, col_index, value):
        for row in range(self._rows):
            self[row][col_index] = value

    def get_col(self, col_index):
        result = []
        for row in range(self._rows):
            result.append(self._data[row][col_index])
        return result


class LinkGameButton(object):

    def __init__(self, rect, title_surface=None,
                 normal_surface=None,
                 highlight_surface=None,
                 button_down_surface=None):
        self._rect = pygame.Rect(rect)
        # button surface:
        # once a button surface is None, create three default surface
        if button_down_surface is None:
            normal_surface, highlight_surface, button_down_surface = \
                self.create_default_surfaces()
        self._normal_surf      = normal_surface
        self._highlight_surf   = highlight_surface
        self._button_down_surf = button_down_surface
        # button states:
        self._is_mouse_button_down          = False
        self._is_mouse_hover                = False
        self._last_mouse_down_within_button = False
        # button title
        self._title_surface = None
        if title_surface is not None:
            self.set_title(title_surface)
        self._click_handlers = []
        self._enter_handlers = []
        self._exit_handlers  = []
        self._down_handlers  = []
        self._up_handlers    = []
        self._hover_handlers = []

    def add_click_handler(self, handler):
        self._click_handlers.append(handler)

    def add_enter_handler(self, handler):
        self._enter_handlers.append(handler)

    def add_exit_handler(self, handler):
        self._exit_handlers.append(handler)

    def add_down_handler(self, handler):
        self._down_handlers.append(handler)

    def add_up_handler(self, handler):
        self._up_handlers.append(handler)

    def add_hover_handler(self, handler):
        self._hover_handlers.append(handler)

    def draw(self, surface):
        if self._is_mouse_button_down:
            surface.blit(self._button_down_surf, self._rect)
        elif self._is_mouse_hover:
            surface.blit(self._highlight_surf, self._rect)
        else:
            surface.blit(self._normal_surf, self._rect)
        if self._title_surface is not None:
            self._draw_title_surface(surface)

    def set_normal_surface(self, surface):
        self._normal_surf = surface

    def set_highlight_surface(self, surface):
        self._highlight_surf = surface

    def set_button_down_surface(self, surface):
        self._button_down_surf = surface

    def handle_event(self, event):
        if not event.type in (MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP):
            return

        if self._collidepoint(event.pos):
            # case 1: mouse enter the button
            if not self._is_mouse_hover:
                self._is_mouse_hover = True
                self._mouse_enter(event)
            # case 2: mouse is moving within the button
            if event.type == MOUSEMOTION:
                self._mouse_move(event)
            # case 3: mouse button down within the button
            if event.type == MOUSEBUTTONDOWN:
                self._last_mouse_down_within_button = True
                self._is_mouse_button_down = True
                self._mouse_button_down(event)

        if not self._collidepoint(event.pos):
            # case 4: mouse exit the button
            if self._is_mouse_hover:
                self._is_mouse_hover = False
                self._mouse_exit(event)
            if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP):
                self._last_mouse_down_within_button = False

        if event.type == MOUSEBUTTONUP:
            # case 5: mouse button up
            if self._is_mouse_button_down:
                self._is_mouse_button_down = False
                self._mouse_button_up(event)
            # case 6: mouse clicked
            if self._last_mouse_down_within_button:
                self._is_mouse_button_down = False
                self._mouse_click(event)

    def set_title(self, title_surface):
        self._title_surface = title_surface
        w, h = self._rect[2], self._rect[3]
        self._title_x = self._rect[0] + (w - title_surface.get_size()[0])/2
        self._title_y = self._rect[1] - title_surface.get_size()[1]

    def _draw_title_surface(self, surface):
        surface.blit(self._title_surface, (self._title_x, self._title_y))

    def _mouse_enter(self, event):
        for handler in self._enter_handlers:
            handler(event)

    def _mouse_exit(self, event):
        for handler in self._exit_handlers:
            handler(event)

    def _mouse_move(self, event):
        for handler in self._hover_handlers:
            handler(event)

    def _mouse_button_down(self, event):
        for handler in self._down_handlers:
            handler(event)

    def _mouse_button_up(self, event):
        for handler in self._up_handlers:
            handler(event)

    def _mouse_click(self, event):
        for handler in self._click_handlers:
            handler(event)

    def _collidepoint(self, pos):
        return self._rect.collidepoint(pos)

    def create_default_surfaces(self, radius=BUTTON_RADIUS, color=BUTTON_COLOR):
        n_surf = create_circle_surface(radius, color, 1)
        h_surf = create_circle_surface(radius, color, 0)
        b_surf = h_surf
        return n_surf, h_surf, b_surf

# ----
# create tiles and methods to draw tiles
Gtile_color0 = (123, 178, 123)
Gtile_color1 = (45,  123, 167)
Gtile_color2 = (129, 128, 143)
Gtile_color3 = (231, 122, 101)

def _circle_tile(width, color):
    return lambda surf, x, y: pygame.draw.circle(surf, color, (x, y), 10, width)

def _rect_tile(width, color):
    return lambda surf, x, y: pygame.draw.rect(surf, color, (x-10, y-10, 20, 20), width)

def _triangle_tile(width, color):
    def draw_triangle(surf, x, y):
        point_list = [(x, y-10), (x-10, y+7), (x+14, y+7)]
        pygame.draw.polygon(surf, color, point_list, width)
    return draw_triangle

def _Gtitles_init():
    tiles = {}
    index = 0
    for width in (0, 3):
        for color in (Gtile_color0, Gtile_color1, Gtile_color2, Gtile_color3):
            tiles[index] = _circle_tile(width, color)
            index += 1
            tiles[index] = _rect_tile(width, color)
            index += 1
            tiles[index] = _triangle_tile(width, color)
            index += 1
    return tiles

Gtiles = _Gtitles_init()

def get_tiles(species, counts):
    result = [s for s in range(species)
                  for _ in range(counts)]
    random.shuffle(result)
    return result

def draw_tile(surface, index, row, col):
    x = LEFT_POS + int((col + 0.5) * CELL_SIZE)
    y = TOP_POS + int((row + 0.5) * CELL_SIZE)
    if Gtiles.get(index, None) is not None:
        Gtiles[index](surface, x, y)
# ----

def linked_row(grid, col, row1, row2):
    row1, row2 = min(row1, row2), max(row1, row2)
    for row in range(row1 + 1, row2):
        if grid[row][col] is not None:
            return False
    return row1 != row2

def linked_col(grid, row, col1, col2):
    col1, col2 = min(col1, col2), max(col1, col2)
    for col in range(col1 + 1, col2):
        if grid[row][col] is not None:
            return False
    return col1 != col2

def linked_directly(grid, grid_pos1, grid_pos2):
    row1, col1 = grid_pos1
    row2, col2 = grid_pos2
    if col1 == col2:
        return linked_row(grid, col1, row1, row2)
    if row1 == row2:
        return linked_col(grid, row1, col1, col2)
    return False

def linked_through_one_corner(grid, grid_pos1, grid_pos2):
    '''return corner_pos or False'''
    row1, col1 = grid_pos1
    row2, col2 = grid_pos2
    if grid[row2][col1] is None and \
         linked_directly(grid, grid_pos1, (row2, col1)) and \
           linked_directly(grid, grid_pos2, (row2, col1)):
        return (row2, col1)
    if grid[row1][col2] is None and \
         linked_directly(grid, grid_pos1, (row1, col2)) and \
           linked_directly(grid, grid_pos2, (row1, col2)):
        return (row1, col2)
    return False

def _is_linked_to_up_or_down(grid, row1, col1, row2, col2, edge_index):
    if row1 == edge_index or \
            (linked_row(grid, col1, row1, edge_index) and grid[edge_index][col1] is None):
        if row2 == edge_index or \
                (linked_row(grid, col2, row2, edge_index) and grid[edge_index][col2] is None):
            return True
    return False

def _is_linked_to_left_or_right(grid, row1, col1, row2, col2, edge_index):
    if col1 == edge_index or \
            (linked_col(grid, row1, col1, edge_index) and grid[row1][edge_index] is None):
        if col2 == edge_index or \
                (linked_col(grid, row2, col2, edge_index) and grid[row2][edge_index] is None):
            return True
    return False

def _two_corners_outside(grid, row1, col1, row2, col2, row_len, col_len):
    if _is_linked_to_up_or_down(grid, row1, col1, row2, col2, 0):
        return [(-1, col1), (-1, col2)]
    if _is_linked_to_up_or_down(grid, row1, col1, row2, col2, row_len - 1):
        return [(row_len, col1), (row_len, col2)]
    if _is_linked_to_left_or_right(grid, row1, col1, row2, col2, 0):
        return [(row1, -1), (row2, -1)]
    if _is_linked_to_left_or_right(grid, row1, col1, row2, col2, col_len - 1):
        return [(row1, col_len), (row2, col_len)]

    return False

def _probe_row(grid, col, grid_pos, range_list):
    for r in range_list:
        if grid[r][col] is not None:
            break
        corner = linked_through_one_corner(grid, (r, col), grid_pos)
        if corner:
            return [(r, col), corner]
    return False

def _probe_col(grid, row, grid_pos, range_list):
    for c in range_list:
        if grid[row][c] is not None:
            break
        corner = linked_through_one_corner(grid, (row, c), grid_pos)
        if corner:
            return [(row, c), corner]
    return False

def _two_corners_inside(grid, row1, col1, row2, col2, row_len, col_len):
    grid_pos2 = (row2, col2)
    for range_list in (reversed(range(row1)), range(row1 + 1, row_len)):
        corners = _probe_row(grid, col1, grid_pos2, range_list)
        if corners:
            return corners
    for range_list in (reversed(range(col1)), range(col1 + 1, col_len)):
        corners = _probe_col(grid, row1, grid_pos2, range_list)
        if corners:
            return corners
    return False

def linked_through_two_corners(grid, grid_pos1, grid_pos2):
    ''' return [corner_pos1, corner_pos2] or False'''
    if grid_pos1 == grid_pos2:
        return False
    row1, col1 = grid_pos1
    row2, col2 = grid_pos2
    row_len, col_len = grid.rows(), grid.cols()
    result = _two_corners_inside(grid, row1, col1, row2, col2, row_len, col_len)
    if result:
        return result
    result = _two_corners_outside(grid, row1, col1, row2, col2, row_len, col_len)
    if result:
        return result

    return False


class CricleTimer(object):

    def __init__(self, seconds, radius, title_surface=None,
                 time_over_half_color=ORANGE, time_out_color=RED):
        self._time = seconds
        self._curr_time = 0.
        self._radius = radius
        self._arc_len = radius * 2
        self._time_ratio = math.pi*2. / self._time
        self._time_out_color = time_out_color
        self._time_over_half_color = time_over_half_color
        self._title_surface = title_surface
        self._time_out_handler = []
        self._first_time_out   = True
        # offsets used to draw title surface
        if title_surface is not None:
            self._title_x_offset = \
                    self._radius - title_surface.get_size()[0]/2.
            self._title_y_offset = \
                    -title_surface.get_size()[1]

    def add_time_out_handler(self, handler):
        self._time_out_handler.append(handler)

    def add_curr_time(self, seconds):
        self._curr_time = min(self._time, self._curr_time + seconds)
        if self._curr_time == self._time and self._first_time_out:
            for handler in self._time_out_handler:
                handler(self)

    def reset_time(self, seconds):
        self._curr_time = 0.
        self._time = seconds
        self._time_ratio = math.pi*2. / self._time

    def get_curr_time(self):
        return self._curr_time

    def draw(self, screen, color, pos):
        x, y = pos
        self._draw_title_surface(screen, x, y)
        color = self._change_color(color)   # if time passed over half or three-quarter
        self._draw_timer(screen, color, x, y)

    def _draw_title_surface(self, screen, x, y):
        if self._title_surface is not None:
            screen.blit(self._title_surface,
                        (x + self._title_x_offset, y + self._title_y_offset))

    def _change_color(self, color):
        if self._curr_time * 2 >= self._time:
            color = self._time_over_half_color
        if self._curr_time * 4 >= self._time * 3:
            color = self._time_out_color
        return color

    def _draw_timer(self, screen, color, x, y):
        if self._curr_time == self._time:
            pygame.draw.circle(screen, color,
                    (x + self._radius, y + self._radius), self._radius, 0)
            return
        pygame.draw.circle(screen, color,
                           (x + self._radius, y + self._radius), self._radius, 1)
        # calling pygame.draw.arc three times for anti-alias
        pygame.draw.arc(screen, color, (x, y, self._arc_len, self._arc_len),
                        0.5*math.pi,
                        0.5*math.pi + self._time_ratio * self._curr_time,
                        self._radius)
        pygame.draw.arc(screen, color, (x, y, self._arc_len, self._arc_len),
                        0.5*math.pi + 0.01,
                        0.5*math.pi + self._time_ratio * self._curr_time + 0.01,
                        self._radius)
        pygame.draw.arc(screen, color, (x, y, self._arc_len, self._arc_len),
                        0.5*math.pi + 0.02,
                        0.5*math.pi + self._time_ratio * self._curr_time + 0.02,
                        self._radius)


def create_circle_surface(radius, color, circle_width=1):
    # return a square surface that the circle will fill
    # place that can't be filled will be set as transparent
    transparent_surface = pygame.Surface((radius*2, radius*2), SRCALPHA)
    transparent_surface.fill((0, 0, 0, 0))
    pygame.draw.circle(transparent_surface, color,
                       (radius, radius), radius, circle_width)
    return transparent_surface


class HintButton(LinkGameButton):

    def __init__(self, title_surface):
        super(HintButton, self).__init__(HINT_BUTTON_RECT, title_surface)
        self._set_hint()

    def draw(self, surface):
        super(HintButton, self).draw(surface)
        self._draw_hint_count(surface)

    def get_hint_count(self):
        return self._hint

    def set_hint_count(self, value):
        self._hint = value

    def _draw_hint_count(self, surface):
        if self._hint != self._old_hint:
            self._hint_surface = self._font.render(str(self._hint), True, HINT_COLOR)
            self._old_hint = self._hint
        surface.blit(self._hint_surface, (self._hint_x, self._hint_y))

    def _set_hint(self):
        self._hint, self._old_hint = HINT_COUNT, HINT_COUNT
        self._font = pygame.font.Font(pygame.font.get_default_font(), HINT_FONT_SIZE)
        self._hint_surface = self._font.render(str(self._hint), True, HINT_COLOR)
        w, h = HINT_BUTTON_RECT[2], HINT_BUTTON_RECT[3]
        self._hint_x = HINT_BUTTON_RECT[0] + (w - self._hint_surface.get_size()[0])/2
        self._hint_y = HINT_BUTTON_RECT[1] + (h - self._hint_surface.get_size()[1])/2


class RestartButton(LinkGameButton):

    def __init__(self, title_surface):
        n_surf, h_surf, b_surf = self.create_default_surfaces()
        self._draw_restart_surf(n_surf, h_surf, b_surf)
        super(RestartButton, self).__init__(RESTART_BUTTON_RECT, title_surface,
                                            n_surf, h_surf, b_surf)

    def _draw_restart_surf(self, *surfaces):
        for surf in surfaces:
            pygame.draw.lines(surf, RESTART_COLOR, False, RESTART_POINTS1, 5)
            pygame.draw.lines(surf, RESTART_COLOR, False, RESTART_POINTS2, 5)

class PauseButton(LinkGameButton):

    def __init__(self, pause_title, not_pause_title):
        n_surf, h_surf, b_surf = self.create_default_surfaces()
        self._draw_not_pause_surface(n_surf, h_surf, b_surf)
        super(PauseButton, self).__init__(PAUSE_BUTTON_RECT,
                                          not_pause_title,
                                          n_surf, h_surf, b_surf)
        self._pause = False
        self._pause_title = pause_title
        self._not_pause_title = not_pause_title
        self.add_click_handler(self._default_pause_handler)

    def is_pause(self):
        return self._pause

    def set_pause(self, boolean):
        if boolean != self._pause:
            self._change_surfaces()
        self._pause = boolean

    def draw(self, surface):
        super(PauseButton, self).draw(surface)
        self._draw_title_surface(surface)

    def _default_pause_handler(self, event):
        self._change_surfaces()
        self._pause = not self._pause

    def _draw_pause_surface(self, *surfaces):
        for surf in surfaces:
            pygame.draw.polygon(surf, PAUSE_COLOR, PAUSE_TRIANGLE)

    def _draw_not_pause_surface(self, *surfaces):
        for surf in surfaces:
            pygame.draw.rect(surf, PAUSE_COLOR, PAUSE_RECT1)
            pygame.draw.rect(surf, PAUSE_COLOR, PAUSE_RECT2)

    def _change_surfaces(self):
        ''' changed surfaces of the button when self._pause was changed'''
        n_surf, h_surf, b_surf = self.create_default_surfaces()
        if self._pause:
            self._draw_not_pause_surface(n_surf, h_surf, b_surf)
            self.set_title(self._not_pause_title)
        if not self._pause:
            self._draw_pause_surface(n_surf, h_surf, b_surf)
            self.set_title(self._pause_title)
        self.set_normal_surface(n_surf)
        self.set_highlight_surface(h_surf)
        self.set_button_down_surface(b_surf)


def draw_grid(screen, color, rows, cols, cell_size, left_top_pos=(0,0)):
    row_length = cols * cell_size
    col_length = rows * cell_size
    left, top = left_top_pos
    for i in range(left, left + row_length + 1, cell_size):
        pygame.draw.line(screen, color, (i, top), (i, top + col_length))
    for i in range(top, top + col_length + 1, cell_size):
        pygame.draw.line(screen, color, (left, i), (left + row_length, i))

def draw_background(screen):
    screen.fill(BACKGROUND_COLOR)
    draw_grid(screen, GRID_COLOR, ROWS_COUNT,
              COLS_COUNT, CELL_SIZE, (LEFT_POS, TOP_POS))

def draw_rect(surface, color, grid_pos, width,
              cell_size=CELL_SIZE,
              left_top=(LEFT_POS, TOP_POS)):
    left, top = left_top
    r, c = grid_pos
    x, y = left + c*cell_size, top + r*cell_size
    pygame.draw.rect(surface, color, (x, y, cell_size, cell_size), width)

def draw_text_in_center(surface, text_surface,
                        left_top=(LEFT_POS, TOP_POS)):
    left, top = left_top
    surf_w, surf_h = surface.get_size()
    font_w, font_h = text_surface.get_size()
    x = (surf_w - font_w)//2 + left
    y = (surf_h - font_h)//2 + top
    rect = surface.blit(text_surface, (x, y))


class LinkGame(object):

    def __init__(self, screen, rows, cols):
        self._grid = Grid(rows, cols)
        self._button_init()
        self._randomly_fill_grid(self._grid)
        self._screen             = screen
        self._selected           = None
        self._linked_line_points = None
        self._hint_pos1          = None
        self._hint_pos2          = None
        self._msg_font           = pygame.font.Font(pygame.font.get_default_font(), MESSAGE_FONT_SIZE)
        self._message            = None
        self._game_over          = False
        self._win                = False
        self._couples            = rows * cols // 2

    def add_time(self, seconds):
        if not self._pause_button.is_pause():
            self._timer.add_curr_time(seconds)

    def handle_event(self, event):
        self._restart_button.handle_event(event)
        if self._win or self._game_over:
            return
        self._pause_button.handle_event(event)
        if self._pause_button.is_pause():
            return
        self._hint_button.handle_event(event)
        if event.type == MOUSEBUTTONDOWN:
            grid_pos = self._validate_mouse_pos(event.pos)
            if grid_pos is not None:
                self._handle_mouse_click(grid_pos)

    def draw(self):
        self._draw_buttons()
        if  self._pause_button.is_pause() or self._game_over or self._win:
            self._draw_pause()
            # message must be drawn when paused
            if self._message is not None:
                self._draw_msg()
        else:
            # draw tiles
            for row, col in self._grid.valid_indices():
                draw_tile(self._screen, self._grid[row][col], row, col)
            # if hint was used, draw hints
            self._draw_hint()
            # if a tile was selected, draw a rect
            if self._selected is not None:
                draw_rect(self._screen, LINKED_LINE_COLOR, self._selected, LINKED_LINE_WIDTH)

    def linked(self):
        return self._linked_line_points is not None

    def handle_linked(self):
        self._draw_linked_animation()     # minus paused time
        self._grid.set_value(self._selected, None)
        self._grid.set_value(self._linked_pos, None)
        if self._selected in (self._hint_pos1, self._hint_pos2):
            self._hint_pos1 = None
            self._hint_pos2 = None
        self._selected = None
        self._linked_line_points = None
        self._linked_pos = None
        self._couples -= 1
        # check if all done
        if self._couples == 0:
            self._win = True
            self._send_msg("All done. Times used: {:.2f}s. Restart?".format(self._timer.get_curr_time()))
            return
        # check if the remaining grid exist any couple
        couple = self._search_for_a_couple()
        if couple is None:
            self._get_a_couple()
            self._send_msg("No more match. Randomizing... Click <Continue> to continue")

    def _button_init(self):
        self._set_button_font_and_titles()
        self._timer = CricleTimer(GAME_TIME, BUTTON_RADIUS, self._timer_title)
        self._timer.add_time_out_handler(self._time_out_handler)
        self._hint_button = HintButton(self._hint_title)
        self._hint_button.add_click_handler(self._use_hint_handler)
        self._pause_button = PauseButton(self._pause_title, self._not_pause_title)
        self._pause_button.add_click_handler(self._pause_handler)
        self._restart_button = RestartButton(self._restart_title)
        self._restart_button.add_click_handler(self._restart_handler)

    def _set_button_font_and_titles(self):
        self._button_title_font = pygame.font.Font(pygame.font.get_default_font(), BUTTON_TITLE_SIZE)
        self._timer_title       = self._button_title_font.render('TIMER', True, BUTTON_COLOR)
        self._hint_title        = self._button_title_font.render('HINTS', True, BUTTON_COLOR)
        self._pause_title       = self._button_title_font.render('CONTINUE', True, BUTTON_COLOR)
        self._not_pause_title   = self._button_title_font.render('PAUSE', True, BUTTON_COLOR)
        self._restart_title     = self._button_title_font.render('RESTART', True, BUTTON_COLOR)

    def _use_hint_handler(self, event):
        remaining_hint = self._hint_button.get_hint_count()
        if remaining_hint > 0:
            self._hint_button.set_hint_count(remaining_hint - 1)
            self._use_hint()

    def _use_hint(self):
        result = self._search_for_a_couple()
        if result is None:
            result = self._get_a_couple()
            self._send_msg("No more match. Randomizing... Click <Continue> to continue")
        self._hint_pos1, self._hint_pos2 = result

    def _time_out_handler(self, timer=None):
        self._send_msg("Game over. Restart?")
        self._game_over = True

    def _pause_handler(self, event):
        # when game in progress, message was removed
        if self._message is not None and not self._pause_button.is_pause():
            self._message = None

    def _restart_handler(self, event):
        self.__init__(self._screen, self._grid.rows(), self._grid.cols())

    def _randomly_fill_grid(self, grid):
        col = 0
        row = 0
        for i in get_tiles(TILE_SPECIES, TILE_COUNT):
            grid[row][col] = i
            col += 1
            if col == grid.cols():
                col = 0
                row += 1
        while self._search_for_a_couple() is None:
            self._grid.randomize()

    def _linked(self, grid_pos1, grid_pos2):

        if self._grid.get_value(grid_pos2) != self._grid.get_value(grid_pos1):
            return False

        if linked_directly(self._grid, grid_pos1, grid_pos2):
            return [grid_pos1, grid_pos2]

        corner = linked_through_one_corner(self._grid, grid_pos1, grid_pos2)
        if corner:
            return [grid_pos1, corner, grid_pos2]

        corners = linked_through_two_corners(self._grid, grid_pos1, grid_pos2)
        if corners:
            corner1, corner2 = corners
            return [grid_pos1, corner1, corner2, grid_pos2]

        return False

    def _draw_linked_lines(self, grid_points):
        points = [(LEFT_POS + (c+0.5)*CELL_SIZE, TOP_POS + (r+0.5)*CELL_SIZE)
                     for r, c in grid_points]
        pygame.draw.lines(self._screen, LINKED_LINE_COLOR, False, points, LINKED_LINE_WIDTH)

    def _draw_hint(self):
        if self._hint_pos1 is not None and self._hint_pos2 is not None:
            draw_rect(self._screen, RED, self._hint_pos1, LINKED_LINE_WIDTH)
            draw_rect(self._screen, RED, self._hint_pos2, LINKED_LINE_WIDTH)

    def _draw_pause(self):
        pygame.draw.rect(self._screen, WHITE,
                         (LEFT_POS, TOP_POS, CELL_SIZE*COLS_COUNT+1, CELL_SIZE*ROWS_COUNT+1))

    def _draw_buttons(self):
        self._restart_button.draw(self._screen)
        self._pause_button.draw(self._screen)
        self._hint_button.draw(self._screen)
        self._timer.draw(self._screen, BUTTON_COLOR, TIMER_POS)

    def _draw_linked_animation(self):
        self._draw_linked_lines(self._linked_line_points)
        pygame.display.update()
        paused_time = pygame.time.delay(200) / 1000.
        self.add_time(-paused_time)

    def _validate_mouse_pos(self, pos):
        x, y = pos
        row = (y-TOP_POS) // CELL_SIZE
        col = (x-LEFT_POS) // CELL_SIZE
        if 0 <= row < self._grid.rows() and \
                0 <= col < self._grid.cols():
            return (row, col)
        return None

    def _handle_mouse_click(self, grid_pos):
        if self._grid.get_value(grid_pos) is None:
            return
        if self._selected is None:
            self._selected = grid_pos
            return
        linked_points = self._linked(self._selected, grid_pos)
        if linked_points:
            self._linked_line_points = linked_points
            self._linked_pos = grid_pos
            draw_rect(self._screen, LINKED_LINE_COLOR, grid_pos, LINKED_LINE_WIDTH)
        else:
            self._selected = grid_pos

    def _get_a_couple(self):
        result = self._search_for_a_couple()
        while result is None:
            self._grid.randomize()
            result = self._search_for_a_couple()
        return result

    def _search_for_a_couple(self):
        for grid_pos1 in self._grid.valid_indices():
            for grid_pos2 in self._grid.valid_indices():
                if self._linked(grid_pos1, grid_pos2):
                    result = [grid_pos1, grid_pos2]
                    return result
        return None

    def _send_msg(self, str_msg):
        self._message = str_msg
        self._pause_button.set_pause(True)

    def _draw_msg(self):
        text_surf = self._msg_font.render(self._message, True, MESSAGE_FONT_COLOR)
        draw_text_in_center(self._screen, text_surf, (0, 0))


def main():

    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()
    game   = LinkGame(screen, ROWS_COUNT, COLS_COUNT)

    while True:

        pygame.display.set_caption("Solarized Link    FPS: {:.2f}".format(clock.get_fps()))
        time_passed_seconds = clock.tick(FPS+3) / 1000.
        game.add_time(time_passed_seconds)
        draw_background(screen)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            game.handle_event(event)
        game.draw()

        pygame.display.update()

        if game.linked():
            game.handle_linked()

if __name__ == '__main__':
    main()

