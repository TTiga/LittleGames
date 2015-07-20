# -*- encoding: utf-8 -*-

import collections
import random
import sys

import pygame

FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)


def get_length(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return ((x2-x1)**2 + (y2-y1)**2) ** 0.5

def normalize(velocity, factor=1):
    length = get_length(velocity, (0, 0))
    velocity[0] /= (length / factor)
    velocity[1] /= (length / factor)

def set_static_var(var, value):
    def decorate(func):
        setattr(func, var, value)
        return func
    return decorate


def draw_grid(surface, color, rows, cols, cell_size, left_top_pos=(0, 0)):
    row_length = cols * cell_size
    col_length = rows * cell_size
    left, top = left_top_pos
    for i in range(left, left+row_length+1, cell_size):
        pygame.draw.line(surface, color, (i, top), (i, top + col_length))
    for i in range(top, top+col_length+1, cell_size):
        pygame.draw.line(surface, color, (left, i), (left + row_length, i))

def draw_text(text, surface, color, font, pos, on_center=True, anti_alias=False):
    x, y = pos
    text_surf = font.render(text, anti_alias, color)
    if on_center:
        w, h = text_surf.get_size()
        x -= w // 2
        y -= h // 2
    surface.blit(text_surf, (x, y))


@set_static_var('curr_id', pygame.USEREVENT)
def get_userevent_id():
    get_userevent_id.curr_id += 1
    return get_userevent_id.curr_id


class Clip(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

    def draw(self, surface):
        raise NotImplementedError


class TextClip(Clip):

    def __init__(self, font, pos, life_frames, velocity, text, color, on_center=False):
        Clip.__init__(self)
        self.pos = list(pos)
        self.max_life = life_frames
        self.velocity = list(velocity)
        self.on_center = on_center
        self.life = life_frames
        self.text_surf = font.render(text, False, color)

    def draw(self, surface):
        x, y = self.pos
        if self.on_center:
            w, h = self.text_surf.get_size()
            x -= w//2
            y -= h//2
        self.text_surf.set_alpha(255 * self.life//self.max_life)
        surface.blit(self.text_surf, (x, y))
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.life -= 1
        return self.life == 0


class RangeClip(Clip):

    def __init__(self, radius, pos, life_frames):
        Clip.__init__(self)
        self.pos = pos
        self.life = life_frames
        self.max_life = life_frames
        d = radius * 2
        self.rect = pygame.Rect(0, 0, d, d)
        self.rect.center = pos
        self.radius = radius

    def finished(self):
        return self.life == 0

    def draw(self, surface):
        self.radius *= (self.life / self.max_life)
        radius = int(self.radius)
        if radius > 0:
            x, y = int(self.pos[0]), int(self.pos[1])
            pygame.draw.circle(surface, GREEN, (x, y), radius, 1)
        self.life -= 1
        return self.life == 0

    def is_collided_with(self, sprite):
        return pygame.sprite.collide_circle(self, sprite)


class ProgressClip(Clip):

    def __init__(self, size, pos, life_frames, color):
        Clip.__init__(self)
        self.image = self._create_image(size, color)
        self.bar_width = size * (2/3)
        self.bar_height = size / 6
        self.bar_pos = (size/6, size * (5/12))
        bar_rect = (self.bar_pos, (self.bar_width, self.bar_height))
        pygame.draw.rect(self.image, color, bar_rect, 1)

        self.max_life = life_frames
        self.life = 0
        self.pos = pos
        self.color = color

    def draw(self, surface):
        width = self.bar_width * (self.life/self.max_life)
        progress_bar = (self.bar_pos, (width, self.bar_height))
        pygame.draw.rect(self.image, self.color, progress_bar, 0)
        surface.blit(self.image, self.pos)
        self.life += 1
        return self.life > self.max_life

    def finished(self):
        return self.life > self.max_life

    def _create_image(self, size, color):
        backgroud = pygame.Surface((size, size))
        backgroud.set_alpha(125)
        backgroud.fill(color)
        image = pygame.Surface((size, size), pygame.SRCALPHA)
        image.blit(backgroud, (0, 0))
        return image


class Messager(Clip):

    def __init__(self, font, pos, life_frames, color=BLACK, on_center=True):
        Clip.__init__(self)
        self.font = font
        self.pos = pos
        self.max_life = life_frames
        self.color = color
        self.life = 0
        self.on_center = on_center
        self.msg_surfs = []
        self.life_velocity = +1

    def add_message(self, *messages):
        self.msg_surfs.clear()
        for msg in messages:
            text_surf = self.font.render(msg, False, self.color)
            self.msg_surfs.append(text_surf)
        self.life = 0
        self.life_velocity = +1

    def draw(self, surface):
        self._draw_helper(surface)
        self.life += self.life_velocity
        if self.life >= self.max_life:
            self.life_velocity = -1
        return self.life == 0

    def _draw_helper(self, surface):
        # Text rendered by pygame.font.Font.render can only be a single line.
        # This function is defined for rendering multi-line messages.
        x, y = self.pos
        height = self.font.get_height()
        if len(self.msg_surfs) > 1:
            height *= 1.2
        y -= len(self.msg_surfs)/2 * height
        if self.on_center:
            for i, text_surf in enumerate(self.msg_surfs):
                w = text_surf.get_width() / 2
                text_surf.set_alpha(255 * self.life//self.max_life)
                surface.blit(text_surf, (x - w, y + i*height))
        else:
            for i, text_surf in enumerate(self.msg_surfs):
                text_surf.set_alpha(255 * self.life//self.max_life)
                surface.blit(text_surf, (x, y + i*height))


class ClipPainter(pygame.sprite.Group):

    def __init__(self):
        pygame.sprite.Group.__init__(self)

    def add_clip(self, clip):
        self.add(clip)

    def remove_clip(self, clip):
        self.remove(clip)

    def clips(self):
        return self.sprites()

    def draw(self, surface):
        for clip in self.sprites():
            if clip.draw(surface):
                self.remove(clip)


class Monster(pygame.sprite.Sprite):

    def __init__(self, size, radius, level, image, birthplace):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect(birthplace, (size, size))
        self.image = image
        self.radius = radius
        self.pos = list(self.rect.center)
        self.direction = None
        self.tracking_towers = TowerList()

        self.level = level
        self.max_life = 20 * level
        self.life = self.max_life
        self.defense = (level/25) ** 2
        self.speed = (1 + level/50) * FPS/100
        self.speed_factor = 1
        self.money = 4 * level
        self.update_lifebar()

    def set_direction(self, direction):
        self.direction = direction

    def update_lifebar(self):
        rect = self.image.get_rect()
        left = rect.left + 6
        right = rect.right - 6
        top = rect.top + 2
        pygame.draw.line(self.image, RED, (left, top), (right, top), 2)
        right = left + (right - left) * (self.life / self.max_life)
        pygame.draw.line(self.image, GREEN, (left, top), (right, top), 2)

    def get_hurt(self, attack):
        damage = max(1, attack - self.defense)
        self.life -= damage
        self.update_lifebar()

    def get_money(self):
        return self.money

    def walk(self):
        distance = self.speed * self.speed_factor
        if self.direction == Direction.LEFT:
            self.pos[0] -= distance
        elif self.direction == Direction.RIGHT:
            self.pos[0] += distance
        elif self.direction == Direction.UP:
            self.pos[1] -= distance
        elif self.direction == Direction.DOWN:
            self.pos[1] += distance
        else:
            raise ValueError('Invalid direction')
        self.rect.center = self.pos


class MonsterList(pygame.sprite.Group):

    def __init__(self):
        pygame.sprite.Group.__init__(self)

    def monsters(self):
        return self.sprites()

    def remove_all(self):
        self.remove(*self.sprites())

class MonsterFactory(object):

    def __init__(self, monster_size):

        self.monster_size = monster_size
        self.monster_radius = monster_size//2 - 3
        self.font = pygame.font.SysFont(pygame.font.get_default_font(), 13, True)
        self.monster_group = 5
        self.reset()

    def reset(self):
        self.monster_count = 0

    def get_monster_image(self, level):
        # build a blank image
        image = pygame.Surface((self.monster_size, self.monster_size), pygame.SRCALPHA)
        rect = image.get_rect()
        # draw monster's body
        pygame.draw.circle(image, (76, 0, 153), rect.center, self.monster_radius, 0)
        pygame.draw.circle(image, RED, rect.center, self.monster_radius, 2)
        # draw monster's level
        level_surf = self.font.render(str(level), False, BLACK)
        x, y = rect.bottomright
        w, h = level_surf.get_size()
        image.blit(level_surf, (x - w, y - h))
        return image

    def produce_monster(self, birth_pos):
        level = self.monster_count // self.monster_group + 1
        image = self.get_monster_image(level)
        monster = Monster(self.monster_size, self.monster_radius, level, image, birth_pos)
        self.monster_count += 1
        return monster


def get_tower_init_image(size):
    image = pygame.Surface((size, size))
    image.fill((50, 210, 210))
    return image


class Tower(pygame.sprite.Sprite):

    def __init__(self, image, attack_range, level_moneys, level_times):
        pygame.sprite.Sprite.__init__(self)
        complete_image = get_tower_init_image(image.get_size()[0])
        complete_image.blit(image, (0, 0))
        self.image = complete_image
        self.rect = image.get_rect()
        self._level = 0
        self.level_moneys = level_moneys
        self.level_times = level_times
        self.updating = False
        self.level_up_progress = None
        self.attack_range = attack_range
        self.attack_power = self._level
        self.tracking_monsters = MonsterList()

        self.bullet_speed_factor = 1

    def get_nearest_monster(self):
        m_dist = float('inf')
        m_dest = None
        for m in self.tracking_monsters:
            length = get_length(self.center, m.pos)
            if length < m_dist:
                m_dist = length
                m_dest = m
        return m_dest

    def track(self, monster):
        self.tracking_monsters.add(monster)
        self.track_handler(monster)

    def track_handler(self, monster):
        # empty on purpose
        pass

    def untrack(self, monster):
        self.tracking_monsters.remove(monster)
        self.untrack_handler(monster)

    def untrack_handler(self, monster):
        # empty on purpose
        pass

    def get_level(self):
        return self._level

    def set_level(self, value):
        if not 0 <= value < len(self.level_moneys):
            raise ValueError('Invalid tower level')
        self._level = value
    level = property(get_level, set_level)

    def set_pos(self, pos):
        self.rect.topleft = pos

    def get_pos(self):
        return self.rect.topleft
    pos = property(get_pos, set_pos)

    @property
    def center(self):
        return self.rect.center

    @property
    def top_level(self):
        return len(self.level_moneys)-1

    def get_level_up_money(self):
        return self.level_moneys[self._level+1]

    def get_level_up_time(self):
        return self.level_times[self._level+1]

    def get_sell_money(self):
        return int(sum(self.level_moneys[:self._level+1]) * 0.6)

    def level_up(self, level_up_progress):
        self.updating = True
        self.level_up_progress = level_up_progress
        self.attack_range += 10
        self.attack_power += 1
        self.level += 1
        self.update_image()
        for m in self.tracking_monsters:
            self.untrack(m)

    def run(self, game):
        # updating
        if self.updating:
            if self.level_up_progress.finished():
                self.updating = False
                self.level_up_progress = None
            return
        # searching
        x, y = self.center
        square_attack_range = self.attack_range ** 2
        for m in self.tracking_monsters:
            x1, y1 = m.pos
            if (x1-x)**2 + (y1-y)**2 > square_attack_range:
                self.untrack(m)
        for m_list in game.monster_lists:
            for m in m_list:
                x1, y1 = m.pos
                if (x1-x)**2 + (y1-y)**2 < square_attack_range and not m in self.tracking_monsters:
                    self.track(m)

    def update_image(self):
        h = self.image.get_rect().bottom - 4
        for i in range(self.level):
            pygame.draw.rect(self.image, BLACK, (1 + 4*i, h, 3, 3), 1)

    def draw(self, surface):
        # empty on purpose
        pass

    def hit(self, monster):
        # empty on purpose
        pass

    def run_bullet(self, bullet):
        square_attack_range = self.attack_range ** 2
        x, y = self.center
        if bullet.enabled:
            if bullet.tracking:
                if bullet.target.life <= 0:
                    bullet.tracking = False
                else:
                    bullet.update_velocity(self.bullet_speed_factor)
            bullet.walk()
            x1, y1 = bullet.pos
            if (x-x1)**2 + (y-y1)**2 <= square_attack_range:
                for m in self.tracking_monsters:
                    if bullet.is_hit_monster(m):
                        self.hit(m)
                        bullet.enabled = False
            else:
                bullet.enabled = False

        if not bullet.enabled and not self.updating:
            m = self.get_nearest_monster()
            if m is not None:
                bullet.target = m
                bullet.pos = list(self.center)
                bullet.tracking = True
                bullet.enabled = True


class Bullet(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.radius = 3
        pygame.draw.circle(self.image, BLACK, self.rect.center, self.radius, 1)
        self.tracking = False
        self.enabled = False
        self._pos = list(self.rect.center)
        self._target = None
        self.velocity = [0, 0]

    def get_pos(self):
        return self._pos
    
    def set_pos(self, value):
        self._pos[0] = value[0]
        self._pos[1] = value[1]
        self.rect.center = self._pos
    pos = property(get_pos, set_pos)

    def get_target(self):
        return self._target

    def set_target(self, value):
        self._target = value
    target = property(get_target, set_target)

    def update_velocity(self, normalize_factor=1):
        if self._target is not None:
            self.velocity[0] = self._target.pos[0] - self.pos[0]
            self.velocity[1] = self._target.pos[1] - self.pos[1]
            normalize(self.velocity, normalize_factor)

    def walk(self):
        self._pos[0] += self.velocity[0]
        self._pos[1] += self.velocity[1]
        self.rect.center = self._pos

    def is_hit_target(self):
        return self.is_hit_monster(self._target)

    def is_hit_monster(self, monster):
        return pygame.sprite.collide_circle(self, monster)


class BulletList(pygame.sprite.Group):

    def __init__(self, *bullets):
        pygame.sprite.Group.__init__(self, *bullets)


class MultiShotTower(Tower):

    def __init__(self, image, attack_range, level_moneys, level_times):
        Tower.__init__(self, image, attack_range, level_moneys, level_times)
        self.bullets = BulletList(Bullet())

    def level_up(self, level_up_progress):
        Tower.level_up(self, level_up_progress)
        self.bullets.add(Bullet())

    def run(self, game):
        Tower.run(self, game)
        for bullet in self.bullets:
            self.run_bullet(bullet)

    def draw_floating(self, surface):
        for i, bullet in enumerate(self.bullets):
            if bullet.enabled:
                surface.blit(bullet.image, 
                             (bullet.rect.left + i*2, bullet.rect.top + i*2))

    def hit(self, monster):
        monster.get_hurt(self.attack_power)

class QuickShotTower(Tower):

    def __init__(self, image, attack_range, level_moneys, level_times):
        Tower.__init__(self, image, attack_range, level_moneys, level_times)
        self.bullet = Bullet()
        self.bullet_speed_factor = 1.5

    def level_up(self, level_up_progress):
        Tower.level_up(self, level_up_progress)
        self.bullet_speed_factor += 0.5
        self.attack_power += 0.2

    def run(self, game):
        Tower.run(self, game)
        self.run_bullet(self.bullet)

    def hit(self, monster):
        monster.get_hurt(self.attack_power)

    def draw_floating(self, surface):
        if self.bullet.enabled:
            surface.blit(self.bullet.image, self.bullet.rect)


class RangeTower(Tower):

    def __init__(self, image, attack_range, level_moneys, level_times):
        Tower.__init__(self, image, attack_range, level_moneys, level_times)
        self.bullet = Bullet()
        self.clip_painter = ClipPainter()

    def run(self, game):
        Tower.run(self, game)
        self.run_bullet(self.bullet)
        for clip in self.clip_painter.clips():
            for m_list in game.monster_lists:
                for m in m_list:
                    if clip.is_collided_with(m):
                        m.get_hurt(self.attack_power)

    def hit(self, monster):
        monster.get_hurt(self.attack_power)
        range_clip = RangeClip(self.attack_range/2, monster.pos, FPS)
        self.clip_painter.add_clip(range_clip)


    def draw_floating(self, surface):
        if self.bullet.enabled:
            surface.blit(self.bullet.image, self.bullet.rect)
        self.clip_painter.draw(surface)


class TrapTower(Tower):

    def __init__(self, image, attack_range, level_moneys, level_times):
        Tower.__init__(self, image, attack_range, level_moneys, level_times)
        self.trap_factor = 0.25

    def level_up(self, level_up_progress):
        Tower.level_up(self, level_up_progress)
        self.trap_factor += 0.25

    def track_handler(self, monster):
        monster.speed_factor = max(
            0.1, monster.speed_factor - self.trap_factor)

    def untrack_handler(self, monster):
        monster.speed_factor = min(
            1, monster.speed_factor + self.trap_factor)

    def draw_floating(self, surface):
        if not self.updating:
            for m in self.tracking_monsters:
                pygame.draw.line(surface, (127, 0, 255), self.center, m.pos)


class TowerFactory(object):

    def __init__(self, size, level_moneys, level_times):
        self.size = size
        self.level_moneys = list(level_moneys)
        self.level_times = list(level_times)

    def get_money(self):
        return self.level_moneys[0]

    def get_time(self):
        return self.level_times[0]

    def is_mine(self, tower):
        raise NotImplementedError

    def get_range(self):
        raise NotImplementedError

    def get_init_image(self):
        raise NotImplementedError

    def produce_tower(self):
        raise NotImplementedError


class MultiShotTowerFactory(TowerFactory):

    def __init__(self, size, level_moneys, level_times):
        TowerFactory.__init__(self, size, level_moneys, level_times)

    def _draw_circle(self, image, x, y):
        pygame.draw.circle(image, (178, 0, 178), (x, y), 3, 0)

    def get_init_image(self):
        image = pygame.Surface((self.size-1, self.size-1), pygame.SRCALPHA)
        x, y = image.get_rect().center
        self._draw_circle(image, x, y)
        self._draw_circle(image, x-5, y-5)
        self._draw_circle(image, x-5, y+5)
        self._draw_circle(image, x+5, y-5)
        self._draw_circle(image, x+5, y+5)
        return image

    def get_range(self):
        return self.size*3

    def is_mine(self, tower):
        return isinstance(tower, MultiShotTower)

    def produce_tower(self):
        image = self.get_init_image()
        money = self.get_money()
        attack_range = self.get_range()
        tower = MultiShotTower(image, attack_range, self.level_moneys, self.level_times)
        return tower

class QuickShotTowerFactory(TowerFactory):

    def __init__(self, size, level_moneys, level_times):
        TowerFactory.__init__(self, size, level_moneys, level_times)

    def _draw_circle(self, image, x, y):
        pygame.draw.circle(image, (255, 128, 0), (x, y), 3, 0)

    def get_init_image(self):
        image = pygame.Surface((self.size-1, self.size-1), pygame.SRCALPHA)
        x, y = image.get_rect().center
        self._draw_circle(image, x, y)
        self._draw_circle(image, x-7, y)
        self._draw_circle(image, x+7, y)
        self._draw_circle(image, x, y-7)
        self._draw_circle(image, x, y+7)
        return image

    def is_mine(self, tower):
        return isinstance(tower, QuickShotTower)

    def get_range(self):
        return self.size*3

    def produce_tower(self):
        image = self.get_init_image()
        money = self.get_money()
        attack_range = self.get_range()
        tower = QuickShotTower(image, attack_range, self.level_moneys, self.level_times)
        return tower


class RangeTowerFactory(TowerFactory):

    def __init__(self, size, level_moneys, level_times):
        TowerFactory.__init__(self, size, level_moneys, level_times)

    def get_init_image(self):
        image = pygame.Surface((self.size-1, self.size-1), pygame.SRCALPHA)
        x, y = image.get_rect().center
        pygame.draw.circle(image, GREEN, (x, y), 11, 0)
        pygame.draw.circle(image, BLACK, (x, y), 11, 1)
        pygame.draw.circle(image, BLACK, (x, y), 7, 1)
        pygame.draw.circle(image, BLACK, (x, y), 4, 1)
        return image

    def get_range(self):
        return self.size*3

    def is_mine(self, tower):
        return isinstance(tower, RangeTower)

    def produce_tower(self):
        image = self.get_init_image()
        money = self.get_money()
        attack_range = self.get_range()
        tower = RangeTower(image, attack_range, self.level_moneys, self.level_times)
        return tower


class TrapTowerFactory(TowerFactory):

    def __init__(self, size, level_moneys, level_times):
        TowerFactory.__init__(self, size, level_moneys, level_times)

    def get_init_image(self):
        image = pygame.Surface((self.size-1, self.size-1), pygame.SRCALPHA)
        rect = image.get_rect()
        rect.topleft = (rect.width//4+2, rect.height//4+2)
        rect.width = rect.width//2 - 4
        rect.height = rect.height//2 - 4
        pygame.draw.rect(image, (127, 0, 255), rect)
        pygame.draw.rect(image, BLACK, rect, 1)
        return image

    def get_range(self):
        return int(self.size*1.5)

    def is_mine(self, tower):
        return isinstance(tower, TrapTower)

    def produce_tower(self):
        image = self.get_init_image()
        money = self.get_money()
        attack_range = self.get_range()
        tower = TrapTower(image, attack_range, self.level_moneys, self.level_times)
        return tower


class MapCell(object):

    def __init__(self):
        self._blocking = False
        self.tower = None

    @property
    def blocking(self):
        return self._blocking

    def block(self):
        self._blocking = True
    
    def unblock(self):
        self._blocking = False

    def set_tower(self, tower):
        self.tower = tower


class GameMap(object):
    
    def __init__(self, cols, rows):
        self.cells = [
            [MapCell() for _ in range(cols)] for _ in range(rows)
        ]
        self.cols = cols
        self.rows = rows

    def get_cell(self, col, row):
        return self.cells[col][row]


class Direction(object):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3


class Guider(object):

    DIRECTIONS = [
        Direction.LEFT,
        Direction.RIGHT,
        Direction.UP,
        Direction.DOWN,
    ]

    DIRECTION_VECTORS = {
        Direction.LEFT: (+1, 0),
        Direction.RIGHT: (-1, 0),
        Direction.UP: (0, +1),
        Direction.DOWN: (0, -1),
    }

    class Cell(object):

        def __init__(self):
            self._locking = False
            self._binding = False
            self.directions = []

        def add_direction(self, direction):
            if not direction in self.directions:
                self.directions.append(direction)

        def lock(self):
            self._locking = True

        def unlock(self):
            self._locking = False

        def bind(self):
            self._binding = True

        def unbind(self):
            self._binding = False

        def clear(self):
            self.unlock()
            self.unbind()
            self.directions = []

        @property
        def locking(self):
            return self._locking

        @property
        def binding(self):
            return self._binding

        def direction_count(self):
            return len(self.directions)

    def __init__(self, map, destinations):
        self.destinations = list(destinations)
        self.map = map
        self.cells = [[Guider.Cell() for _ in range(map.cols)] for _ in range(map.rows)]

    def _set_initial_destination(self):
        for col, row in self.destinations:
            cell = self.cells[col][row]
            if col == 0:
                cell.add_direction(Direction.LEFT)
            elif col == self.map.cols - 1:
                cell.add_direction(Direction.RIGHT)
            elif row == 0:
                cell.add_direction(Direction.UP)
            elif row == self.map.rows - 1:
                cell.add_direction(Direction.DOWN)
            else:
                raise ValueError('Invalid destinations')
            self.cells[col][row].lock()

    def draw_floating(self, surface):
        # empty on purpose
        pass

    def guide(self):
        self.clear()
        self._set_initial_destination()
        # breadth first search
        queue = collections.deque(self.destinations)
        queue_size = len(self.destinations)
        while queue_size > 0:
            queue_size -= 1
            curr_col, curr_row = queue.popleft()
            self.cells[curr_col][curr_row].lock()
            for d in Guider.DIRECTIONS:
                delta_c, delta_r = Guider.DIRECTION_VECTORS[d]
                col = curr_col + delta_c
                row = curr_row + delta_r
                if not (0 <= col < self.map.cols and 0 <= row < self.map.rows):
                    continue
                guider_cell = self.cells[col][row]
                map_cell = self.map.get_cell(col, row)
                if not (guider_cell.locking or map_cell.blocking):
                    guider_cell.add_direction(d)
                    if not guider_cell.binding:
                        queue_size += 1
                        queue.append((col, row))
                        guider_cell.bind()
    
    def get_cell(self, col, row):
        return self.cells[col][row]

    def clear(self):
        for col in range(self.map.cols):
            for row in range(self.map.rows):
                self.cells[col][row].clear()


class TowerList(pygame.sprite.Group):

    def __init__(self, *towers):
        pygame.sprite.Group.__init__(self, *towers)

    def towers(self):
        return self.sprites()

    def remove_all(self):
        self.remove(*self.sprites())


class Game(object):

    class Status:
        PLAYING = 0
        PAUSE = 1
        PREPAREING = 2
        FINISHING = 3

    CELL_SIZE = 32
    MAP_COLS = 18
    MAP_ROWS = 18
    TEXT_MENU_WIDTH = CELL_SIZE * 7
    CELLS_WIDTH = CELL_SIZE * MAP_COLS
    CELLS_HEIGHT = CELL_SIZE * MAP_ROWS
    SCREEN_WIDTH = CELLS_WIDTH + TEXT_MENU_WIDTH
    SCREEN_HEIGHT = CELLS_HEIGHT

    BIRTHPLACES = [
        (0, MAP_ROWS//2-1),
        (0, MAP_ROWS//2),
        (MAP_COLS//2-1, 0),
        (MAP_COLS//2, 0)
    ]

    DESTINATIONS = [
        (MAP_COLS-1, MAP_ROWS//2-1),
        (MAP_COLS-1, MAP_ROWS//2),
        (MAP_COLS//2-1, MAP_ROWS-1),
        (MAP_COLS//2, MAP_ROWS-1)
    ]

    def __init__(self):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((Game.SCREEN_WIDTH, Game.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.channels = 2
        self.max_progress = 1000
        self.map = GameMap(Game.MAP_COLS, Game.MAP_ROWS)
        self.clip_painter = ClipPainter()
        self.money_font = pygame.font.SysFont(pygame.font.get_default_font(), 20, True, False)

        self.monster_factory = MonsterFactory(Game.CELL_SIZE)
        self.monster_lists = [
            MonsterList(), 
            MonsterList(),
        ]

        self.guiders = [
            Guider(self.map, Game.DESTINATIONS[:2]),
            Guider(self.map, Game.DESTINATIONS[2:]),
        ]

        self.tower_factories = [
            MultiShotTowerFactory(
                Game.CELL_SIZE, [5, 16, 81, 256, 625, 1296], [0, 40, 80, 120, 160, 260]),
            QuickShotTowerFactory(
                Game.CELL_SIZE, [10, 32, 162, 512, 1250, 2592], [0, 80, 120, 160, 200, 300]),
            RangeTowerFactory(
                Game.CELL_SIZE, [50, 160, 810, 2560, 6250, 12960], [0, 120, 160, 200, 240, 340]),
            TrapTowerFactory(
                Game.CELL_SIZE, [5000, 10000, 20000], [0, 300, 500]),
        ]
        self.tower_lists = [TowerList() for _ in range(4)]

        self.event_handlers = {}
        self.init_event_handlers()
        self.messager = self.init_messager()
        self.cursor_surfs = self.init_cursor_surfs()
        self.init_toolbox()
        self.start_new_game()

    def guide(self):
        for guider in self.guiders:
            guider.guide()

    def start_new_game(self):
        self._life = 10
        self.money = 160
        self.progress = 0
        self.killed = 0

        self.status = Game.Status.PREPAREING
        self.focus_index = 1
        self.cursor_index = 0
        self.cursor_pos = (0, 0)
        self.init_map()
        self.guide()
        for monster_list in self.monster_lists:
            monster_list.remove_all()
        for tower_list in self.tower_lists:
            tower_list.remove_all()
        self.monster_factory.reset()
        self.text_menus = [
            "sell",
            "pause",
            "restart",
        ]
        self.send_message("click to build", "enter to start")

    def init_cursor_surfs(self):
        cursor_surfs = []
        size = Game.CELL_SIZE
        half_size = Game.CELL_SIZE//2
        for factory in self.tower_factories:
            attack_range = factory.get_range()
            surf = pygame.Surface((attack_range*2, attack_range*2), pygame.SRCALPHA)
            rect = surf.get_rect()
            x, y = rect.center
            pygame.draw.circle(surf, (255, 255, 255, 128), (x, y), attack_range, 0)
            pygame.draw.circle(surf, WHITE, (x, y), attack_range, 1)
            pygame.draw.rect(surf, WHITE, (x-half_size, y-half_size, size+1, size+1), 1)
            cursor_surfs.append(surf)
        font = pygame.font.SysFont(pygame.font.get_default_font(), 25, True, True)
        cursor_surfs.append(font.render('$', False, (255, 255, 0)))
        cursor_surfs.append(font.render('level up', False, (255, 128, 0)))  
        return cursor_surfs

    def finish_game(self, is_win):
        if is_win:
            self.send_message('player win', 'enter to restart')
        else:
            self.send_message('player lost', 'enter to restart')
        self.status = Game.Status.FINISHING

    def get_life(self):
        return self._life

    def set_life(self, value):
        self._life = value
        if self._life <= 0:
            self.finish_game(False)
    life = property(get_life, set_life)

    def is_border(self, col, row):
        return (col == 0 or col == Game.MAP_COLS-1) or (row == 0 or row == Game.MAP_ROWS-1)

    def is_wall(self, col, row):
        if self.is_border(col, row):
            return not (col, row) in (Game.BIRTHPLACES + Game.DESTINATIONS)
        return False

    def is_editable(self, col, row):
        return 1 <= col < Game.MAP_COLS-1 and 1 <= row < Game.MAP_ROWS-1

    def add_money_clip(self, col, row, money):
        text = str(money)
        color = RED
        if money > 0:
            text = '+' + text
            color = (255, 255, 0)
        x = (col-0.5) * Game.CELL_SIZE 
        y = row * Game.CELL_SIZE
        y -= self.money_font.get_height()
        dy = -Game.CELL_SIZE/FPS / 2
        clip = TextClip(self.money_font, (x, y), FPS*1.5, (0, dy), text, color)
        self.clip_painter.add_clip(clip)
        return clip

    def add_progress_clip(self, col, row, life_frames):
        x = col * Game.CELL_SIZE
        y = row * Game.CELL_SIZE
        clip = ProgressClip(Game.CELL_SIZE, (x, y), life_frames, RED)
        self.clip_painter.add_clip(clip)
        return clip

    def add_handler(self, event_id, event_handler):
        if self.event_handlers.get(event_id) is not None:
            raise ValueError('event id duplicates')
        self.event_handlers[event_id] = event_handler

    def add_time_handler(self, milliseconds, handler):
        event_id = get_userevent_id()
        self.add_handler(event_id, handler)
        pygame.time.set_timer(event_id, milliseconds)

    def draw_toolbox(self):
        self.screen.fill(BLACK, (Game.CELLS_WIDTH, 0, Game.TEXT_MENU_WIDTH, Game.CELLS_HEIGHT))
        width = Game.CELLS_WIDTH
        size = Game.CELL_SIZE
        # draw title
        for i, surf in enumerate(self.toolbox_title_surfs):
            self.screen.blit(surf, (width + 10 + size*(i+1), (size - surf.get_height())//2))
        # draw toolbox
        for i, factory in enumerate(self.tower_factories):
            image = self.towers_images[i]
            self.screen.blit(image, (width, size*(i+1)))
            for j, level_money in enumerate(factory.level_moneys):
                self._draw_toolbox_money(level_money, width+size*(j+1), size*(i+1))
        # draw text menu
        x = width + Game.TEXT_MENU_WIDTH//2
        y = size*5 + size//2
        for text in self.text_menus:
            draw_text(text, self.screen, (255, 128, 0), self.text_menu_font, (x, y))
            y += size
        # draw focus item
        y = size * self.focus_index
        pygame.draw.rect(self.screen, WHITE, (width+1, y, Game.TEXT_MENU_WIDTH, size), 1)
        # draw level up tip
        if self.cursor_index == len(self.tower_factories) + 1:
            col, row = self.cursor_pos
            tower = self.map.get_cell(col, row).tower
            if tower is None or tower.level >= tower.top_level:
                return
            for i, factory in enumerate(self.tower_factories):
                if not factory.is_mine(tower):
                    continue
                x = width + (tower.level+2)*size
                y = (i+1) * size
                pygame.draw.rect(self.screen, WHITE, (x, y, size, size), 1)
                break
            

    def _draw_toolbox_money(self, money, x, y):
        color = GREEN
        if money > self.money:
            color = RED
        draw_text(str(money), self.screen, color, 
                  self.toolbox_money_font, (x+Game.CELL_SIZE//2, y+Game.CELL_SIZE//2))

    def draw_tower(self):
        for tower_list in self.tower_lists:
            tower_list.draw(self.screen)

    def draw_tower_floating(self):
        for tower_list in self.tower_lists:
            for tower in tower_list:
                tower.draw_floating(self.screen)

    def _do_nothing(self):
        # empty on purpose
        pass

    def draw_cursor(self):
        # empty on purpose
        pass

    def draw(self):
        self.draw_background()
        self.draw_caption()
        self.draw_tower()
        self.draw_monster()
        self.draw_tower_floating()
        self.clip_painter.draw(self.screen)
        self.draw_message()
        self.draw_cursor()

    def run(self):
        self.handle_events()
        self.draw_toolbox()
        if self.status != Game.Status.PAUSE:
            self.run_monster()
            self.run_tower()
            self.draw()
        pygame.display.update()
        self.clock.tick(FPS)

    def is_monster_enter_enough(self, monster, direction):
        x, y = monster.pos
        enter_length = -1
        if direction == Direction.LEFT:
            enter_length = Game.CELL_SIZE - x % Game.CELL_SIZE
        elif direction == Direction.RIGHT:
            enter_length = x % Game.CELL_SIZE
        elif direction == Direction.UP:
            enter_length = Game.CELL_SIZE - y % Game.CELL_SIZE
        elif direction == Direction.DOWN:
            enter_length = y % Game.CELL_SIZE
        else:
            raise ValueError('Invalid direction')
        return enter_length >= monster.radius

    def is_blocking(self):
        for channel in range(self.channels):
            guider = self.guiders[channel]
            monster_list = self.monster_lists[channel]
            for col, row in Game.BIRTHPLACES:
                guider_cell = guider.get_cell(col, row)
                if guider_cell.direction_count() == 0:
                    return True
            for monster in monster_list.monsters():
                x, y = monster.pos
                col, row = int(x//Game.CELL_SIZE), int(y//Game.CELL_SIZE)
                if col >= Game.MAP_COLS or row >= Game.MAP_ROWS:
                    continue
                guider_cell  = guider.get_cell(col, row)
                if guider_cell.direction_count() == 0:
                    return True
        return False

    def run_monster(self):
        for channel in range(self.channels):
            monster_list = self.monster_lists[channel]
            guider = self.guiders[channel]
            for m in monster_list:
                x, y = m.pos
                col = int(x // Game.CELL_SIZE)
                row = int(y // Game.CELL_SIZE)
                # check if monster enter a new map cell
                if self.is_monster_enter_enough(m, m.direction):
                    if not m.direction in guider.cells[col][row].directions:
                        m.direction = random.choice(guider.cells[col][row].directions)
                # monster walk
                m.walk()
                # check if monster arrive its destination
                if col >= Game.MAP_COLS or row >= Game.MAP_ROWS:
                    self.life -= 1
                    m.remove(*m.groups())
                    if self.life <= 0:
                        self.finish_game(False)
                # check if monster die
                elif m.life <= 0:
                    money = m.get_money()
                    self.add_money_clip(col+1, row+1, money)
                    self.killed += 1
                    self.money += money
                    m.remove(*m.groups())


    def run_tower(self):
        for tower_list in self.tower_lists:
            for tower in tower_list:
                tower.run(self)

    def handle_events(self):
        for event in pygame.event.get():
            event_handler = self.event_handlers.get(event.type)
            if event_handler is not None:
                event_handler(event)

    def draw_background(self):
        self.draw_border()
        self.draw_birthplace_and_destination()
        self.draw_cells()
        draw_grid(self.screen, BLACK, Game.MAP_COLS, Game.MAP_ROWS, Game.CELL_SIZE)

    def draw_monster(self):
        for monster_list in self.monster_lists:
            monster_list.draw(self.screen)

    def send_message(self, *messages):
        self.is_draw_message = True
        self.messager.add_message(*messages)

    def draw_message(self):
        if self.is_draw_message:
            is_message_faded = not self.messager.draw(self.screen)
            self.is_draw_message = is_message_faded

    def draw_caption(self):
        progress = min(self.progress, self.max_progress)
        pygame.display.set_caption(
            "Tower Defense 2015 [Life: {}] [Money: {}] [Killed: {}] [progress: {}/{}]".format(
                self.life, self.money, self.killed, progress, self.max_progress))

    def get_rect(self, col, row, c_factor=1, r_factor=1):
        return (col*Game.CELL_SIZE, row*Game.CELL_SIZE,
                Game.CELL_SIZE*c_factor, Game.CELL_SIZE*r_factor)

    def init_messager(self):
        messager_font = pygame.font.SysFont(pygame.font.get_default_font(), 65, True)
        messager_pos = [Game.CELLS_WIDTH//2, Game.CELLS_HEIGHT//2]
        self.is_draw_message = False
        return Messager(messager_font, messager_pos, FPS)

    def draw_cells(self):
        w = (Game.MAP_COLS-2) * Game.CELL_SIZE
        h = (Game.MAP_ROWS-2) * Game.CELL_SIZE
        self.screen.fill((250, 197, 21), (Game.CELL_SIZE, Game.CELL_SIZE, w, h))

    def draw_border(self):
        s = Game.CELL_SIZE
        w, h = Game.CELLS_WIDTH, Game.CELLS_HEIGHT
        c, r = Game.MAP_COLS-1, Game.MAP_ROWS-1
        for rect in [(0, 0, s, h), (0, 0, w, s),
                     (c*s, 0, s, h), (0, r*s, w, s)]:
            self.screen.fill((204, 0, 0), rect)

    def draw_birthplace_and_destination(self):
        for c, r in (Game.BIRTHPLACES + Game.DESTINATIONS):
            self.screen.fill((0, 204, 102), self.get_rect(c, r))

    def init_event_handlers(self):
        self.add_handler(pygame.QUIT, self.quit_handler)
        self.add_handler(pygame.KEYDOWN, self.keydown_handler)
        self.add_handler(pygame.MOUSEBUTTONDOWN, self.mousedown_handler)
        self.add_handler(pygame.MOUSEMOTION, self.mousemotion_handler)
        self.add_time_handler(1000, self.produce_monster)
        self.add_time_handler(1000, self.refresh_progress)

    def _draw_toolbox_cursor(self, row):
        def draw():
            rect = (Game.CELLS_WIDTH, row*Game.CELL_SIZE,
                    Game.TEXT_MENU_WIDTH, Game.CELL_SIZE)
            pygame.draw.rect(self.screen, (255, 128, 0), rect, 1)
        return draw

    def _draw_game_area_cursor(self, col, row):
        def draw():
            x = (col+0.5)*Game.CELL_SIZE
            y = (row+0.5)*Game.CELL_SIZE
            cursor_surf = self.cursor_surfs[self.cursor_index]
            x -= cursor_surf.get_width()//2
            y -= cursor_surf.get_height()//2
            self.screen.blit(cursor_surf, (x, y))
        return draw

    def update_cursor(self, cursor_col, cursor_row):
        col, row = cursor_col, cursor_row
        # mouse cursor on game area
        if col < Game.MAP_COLS:
            if self.is_border(col, row):
                return
            cell = self.map.get_cell(col, row)
            self.cursor_index = self.focus_index - 1
            self.cursor_pos = (col, row)
            if cell.tower is not None:
                # cursor of "sell":
                if self.focus_index == len(self.tower_factories) + 1:
                    self.text_menus[0] = 'sell for ${}'.format(cell.tower.get_sell_money())
                # cursor of "level up":
                else:
                    self.cursor_index = len(self.tower_factories) + 1
            # set draw cursor function
            self.draw_cursor = self._draw_game_area_cursor(col, row)

        # mouse cursor on toolbox area
        else:
            if 0 < row <= len(self.tower_factories) + len(self.text_menus):
                self.draw_cursor = self._draw_toolbox_cursor(row)

    def mousemotion_handler(self, event):
        x, y = event.pos
        col = x // Game.CELL_SIZE
        row = y // Game.CELL_SIZE
        self.draw_cursor = self._do_nothing
        self.text_menus[0] = 'sell'
        self.update_cursor(col, row)

    def quit_handler(self, event):
        pygame.quit()
        sys.exit()

    def get_random_birthplace(self, channel):
        if channel == 0:
            x = -Game.CELL_SIZE
            y = (Game.MAP_ROWS//2 - 1) * Game.CELL_SIZE + random.randint(0, Game.CELL_SIZE)
        elif channel == 1:
            x = (Game.MAP_COLS//2 - 1) * Game.CELL_SIZE + random.randint(0, Game.CELL_SIZE)
            y = -Game.CELL_SIZE
        else:
            raise ValueError('Invalid channel: {}'.format(channel))
        return (x, y)

    def produce_monster(self, event):
        if self.status == Game.Status.PLAYING and self.progress < self.max_progress:
            channel = random.randint(0, 1)
            x, y = self.get_random_birthplace(channel)
            monster = self.monster_factory.produce_monster((x, y))
            if channel == 0:
                monster.set_direction(Direction.RIGHT)
            elif channel == 1:
                monster.set_direction(Direction.DOWN)
            self.monster_lists[channel].add(monster)
    
    def keydown_handler(self, event):
        if event.key != pygame.K_RETURN:
            return
        if self.status == Game.Status.FINISHING:
            self.start_new_game()
        elif self.status == Game.Status.PREPAREING:
            self.status = Game.Status.PLAYING

    def mousedown_handler(self, event):
        x, y = event.pos
        col, row = x//Game.CELL_SIZE, y//Game.CELL_SIZE

        # mouse click on game area
        if col < Game.MAP_COLS:
            if self.status == Game.Status.PAUSE:
                return
            cell = self.map.get_cell(col, row)
            # case 1: sell tower
            if self.focus_index == len(self.tower_factories) + 1:
                self.sell_tower(col, row)
            # case 2: upgrade tower
            elif cell.tower is not None:
                self.upgrade_tower(col, row)
            # case 3: build tower
            elif 0 < self.focus_index <= len(self.tower_factories):
                self.build_tower(col, row, self.focus_index-1)
        # mouse click on toolbox
        else:
            if 0 < row <= len(self.tower_factories) + 1:
                self.focus_index = row
            # case 4: pause
            if row == len(self.tower_factories) + 2:
                if self.status != Game.Status.PAUSE:
                    self._old_status = self.status
                    self.status = Game.Status.PAUSE
                    self.text_menus[1] = "continue"
                else:
                    self.status = self._old_status
                    self.text_menus[1] = "pause"
            # case 5: restart
            elif row == len(self.tower_factories) + 3:
                self.start_new_game()

        self.update_cursor(col, row)

    def is_cell_blockable(self, col, row):
        cell = self.map.get_cell(col, row)
        cell.block()
        self.guide()
        if self.is_blocking():
            cell.unblock()
            self.guide()
            return False
        cell.unblock()
        return True

    def sell_tower(self, col, row):
        cell = self.map.get_cell(col, row)
        tower = cell.tower
        if tower is None:
            self.send_message("nothing to sell")
            return
        money = tower.get_sell_money()
        tower.remove(*tower.groups())
        if tower.level_up_progress is not None:
            self.clip_painter.remove_clip(tower.level_up_progress)
        cell.set_tower(None)
        cell.unblock()
        self.money += money
        self.add_money_clip(col+1, row+1, money)
        self.guide()

    def upgrade_tower(self, col, row):
        tower = self.map.get_cell(col, row).tower
        if tower.level == tower.top_level:
            self.send_message("top level")
            return
        if tower.updating:
            self.send_message("updating")
            return
        money = tower.get_level_up_money()
        if self.money < money:
            self.send_message("no enough $")
            return

        self.money -= money
        self.add_money_clip(col+1, row+1, -money)
        progress = self.add_progress_clip(col, row, tower.get_level_up_time())
        tower.level_up(progress)

    def build_tower(self, col, row, factory_index):
        factory = self.tower_factories[factory_index]

        if self.money < factory.get_money():
            self.send_message("no enough $")
            return
        if self.is_border(col, row):
            self.send_message("forbidden")
            return
        if not self.is_cell_blockable(col, row):
            self.send_message("blocking")
            return

        tower = factory.produce_tower()
        tower.pos = (col*Game.CELL_SIZE+1, row*Game.CELL_SIZE+1)
        self.tower_lists[factory_index].add(tower)
        self.map.get_cell(col, row).set_tower(tower)
        self.map.get_cell(col, row).block()
        self.money -= factory.get_money()
        self.add_money_clip(col+1, row+1, -factory.get_money())

    def alive_monster_count(self):
        n = 0
        for channel in range(self.channels):
            n += len(self.monster_lists[channel])
        return n

    def refresh_progress(self, event):
        if self.status == Game.Status.PLAYING:
            self.progress += 1
            if self.progress >= self.max_progress and self.alive_monster_count() == 0:
                self.finish_game(True)


    def init_map(self):
        for col in range(Game.MAP_COLS):
            for row in range(Game.MAP_ROWS):
                cell = self.map.get_cell(col, row)
                cell.set_tower(None)
                cell.unblock()
                if self.is_wall(col, row):
                    cell.block()

    def init_toolbox(self):
        # title
        self.toolbox_title_surfs = []
        font = pygame.font.SysFont(pygame.font.get_default_font(), Game.CELL_SIZE, True)
        for i in range(6):
            surf = font.render(str(i), False, (255, 128, 0))
            self.toolbox_title_surfs.append(surf)
        # tower image
        self.towers_images = [tower.get_init_image() for tower in self.tower_factories]
        # tower level up money
        self.toolbox_money_font = pygame.font.Font(pygame.font.get_default_font(), 10)
        # text_menu
        self.text_menu_font = pygame.font.SysFont(
            pygame.font.get_default_font(), Game.CELL_SIZE, True, True)


if __name__ == '__main__':
    game = Game()
    while True:
        game.run()
