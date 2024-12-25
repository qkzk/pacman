import os
from random import choice

import pgzrun

import pgzrun
from pgzero import music, clock
from pgzero.actor import Actor
from pgzero.keyboard import Keyboard
from pgzero.screen import Screen
from pygame import Rect

from world import WORLD

screen: Screen
keyboard: Keyboard

os.environ["SDL_VIDEO_CENTERED"] = "1"

TITLE = "PACMAN"
WIDTH = 1600
HEIGHT = 800
TILE = 40

WORLD_WIDTH = WIDTH // TILE
WORLD_HEIGHT = HEIGHT // TILE

DEBUG = True


class Colors:
    BACKGROUND = "#555555"
    WALL = "#3333FF"
    BALL = "#DD22FF"
    PACMAN = "#FFDD22"
    PHANTOMS = (
        "#4466AA",
        "#AA2288",
        "#DD4422",
        "#22DDAA",
    )
    WHITE = "#FFFFFF"
    BLACK = "#000000"


class Movable:
    DIRECTIONS = {
        "up": (0, -1),
        "down": (0, 1),
        "left": (-1, 0),
        "right": (1, 0),
    }

    def __init__(self, x: int, y: int):
        self.rect: Rect = Rect((x, y, TILE, TILE))

    def move(self, direction: str, walls: list[Rect]) -> bool:
        vx, vy = self.DIRECTIONS.get(direction, (0, 0))
        if vx == 0 and vy == 0:
            return False

        for speed in range(SPEED, 0, -1):
            r = self.rect.move(vx * SPEED, vy * speed)
            if not any(wall.colliderect(r) for wall in walls):
                self.rect.x += vx * speed
                self.rect.y += vy * speed
                return True

        return False


class Phantom(Movable):
    def __init__(self, x: int, y: int, color: str):
        self.color = color
        self.rect = Rect(x, y, TILE, TILE)
        self.direction = "right"

        clock.schedule_interval(self.choice_direction, 2.0)

    def choice_direction(self):
        self.direction = choice(("up", "left", "down", "right"))

    def draw(self):
        if DEBUG:
            screen.draw.filled_rect(self.rect, "VIOLET")
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2, self.rect.y + TILE // 2 - 10), 8, self.color
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2, self.rect.y + TILE // 2 + 6), 14, self.color
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 - 10, self.rect.y + TILE // 2 - 10),
            4,
            Colors.WHITE,
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 + 10, self.rect.y + TILE // 2 - 10),
            4,
            Colors.WHITE,
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 - 10, self.rect.y + TILE // 2 - 10),
            2,
            Colors.BLACK,
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 + 10, self.rect.y + TILE // 2 - 10),
            2,
            Colors.BLACK,
        )

    def tile(self) -> tuple[int, int]:
        return (self.rect.x + TILE // 2) // TILE, (self.rect.y + TILE // 2) // TILE


SPEED = 4


class Pacman(Movable):
    def __init__(self, x: int, y: int):
        self.rect: Rect = Rect((x + 2, y + 2, TILE - 4, TILE - 4))
        self.lives = 3
        self.invicible = False

    def draw(self):
        if DEBUG:
            screen.draw.filled_rect(self.rect, "BROWN")
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 - 2, self.rect.y + TILE // 2 - 2),
            18,
            Colors.PACMAN if not self.invicible else Colors.BLACK,
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 + 10, self.rect.y + TILE // 2 - 5), 7, Colors.WHITE
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 + 10, self.rect.y + TILE // 2 - 5), 3, Colors.BLACK
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 - 10, self.rect.y + TILE // 2 - 5), 7, Colors.WHITE
        )
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2 - 10, self.rect.y + TILE // 2 - 5), 3, Colors.BLACK
        )
        screen.draw.filled_rect(
            Rect(self.rect.x + TILE // 2 - 6, self.rect.y + TILE // 2 + 6, 12, 3),
            Colors.BLACK,
        )

    def tile(self) -> tuple[int, int]:
        return (self.rect.x + TILE // 2) // TILE, (self.rect.y + TILE // 2) // TILE

    def end_invicibility(self):
        self.invicible = False

    def hit(self, phantoms: list[Phantom]) -> bool:
        if self.invicible:
            return False
        for phantom in phantoms:
            if self.rect.colliderect(phantom.rect):
                self.lives -= 1
                self.invicible = True
                clock.schedule(self.end_invicibility, 5.0)
                return True
        return False


CELLS: dict[str, int] = {
    " ": 0,
    "w": 1,
    "b": 2,
}


def parse_world(world: str) -> list[list[int]]:
    world = world.strip()
    return [[CELLS[char] for char in line] for line in world.splitlines()]


class Game:
    WALL: int = 1
    VOID: int = 0
    BALL: int = 2

    def __init__(self):
        self.pacman: Pacman
        self.phantoms: list[Phantom]
        self.world: list[list[int]]
        self.walls: list[Rect]
        self.score: int
        self.goal: int
        self.is_playing = False
        self.is_started = False
        self.is_won = False

        clock.schedule(self.reset, 2.0)

    def reset(self):
        self.pacman: Pacman = Pacman(TILE * 30, TILE * 18)
        self.phantoms: list[Phantom] = [
            Phantom(5 * TILE, 2 * TILE, Colors.PHANTOMS[0]),
            Phantom(5 * TILE, 4 * TILE, Colors.PHANTOMS[1]),
            Phantom(5 * TILE, 6 * TILE, Colors.PHANTOMS[2]),
            Phantom(5 * TILE, 11 * TILE, Colors.PHANTOMS[3]),
        ]
        self.world = parse_world(WORLD)
        self.walls = [
            Rect(TILE * i, TILE * j, TILE, TILE)
            for j, row in enumerate(self.world)
            for i, cell in enumerate(row)
            if cell == self.WALL
        ]
        self.goal = sum(
            (sum(1 for cell in row if cell == self.BALL) for row in self.world)
        )
        self.score = 0
        self.is_playing = True
        self.is_started = True
        self.is_won = False

    def read_keys(self) -> str | None:
        if keyboard.up:
            return "up"
        if keyboard.down:
            return "down"
        if keyboard.left:
            return "left"
        if keyboard.right:
            return "right"

    def eat(self, tile_x: int, tile_y: int):
        if self.world[tile_y][tile_x] == self.BALL:
            self.world[tile_y][tile_x] = self.VOID
            self.score += 1

    def game_over(self):
        if self.score == self.goal:
            self.is_won = True
            self.is_playing = False
        if self.pacman.lives == 0:
            self.is_playing = False

    def update(self):
        direction = self.read_keys()
        if direction is not None:
            self.pacman.move(direction, self.walls)
        self.eat(*self.pacman.tile())
        self.game_over()
        if not self.is_playing:
            clock.schedule(self.reset, 2.0)
        self.pacman.hit(self.phantoms)
        for phantom in self.phantoms:
            while not phantom.move(phantom.direction, self.walls):
                phantom.choice_direction()

    def draw_splash(self):
        text: str
        if not self.is_started:
            text = "PACMAN"
        elif self.is_won:
            text = "VICTORY"
        else:
            text = "GAME OVER"
        screen.draw.text(text, center=(WIDTH / 2, HEIGHT / 2), **text_attr())

    def draw(self):
        if not self.is_playing:
            self.draw_splash()
            return
        for j, line in enumerate(self.world):
            for i, block in enumerate(line):
                if block == self.WALL:
                    screen.draw.filled_rect(
                        Rect(i * TILE, j * TILE, TILE, TILE), Colors.WALL
                    )
                elif block == self.BALL:
                    screen.draw.filled_circle(
                        (i * TILE + TILE // 2, j * TILE + TILE // 2),
                        TILE // 5,
                        Colors.BALL,
                    )
        for phantom in self.phantoms:
            phantom.draw()
        self.pacman.draw()
        screen.draw.text(str(self.score), topleft=(TILE, 5), **text_attr())
        screen.draw.text(str(self.pacman.lives), midtop=(WIDTH // 2, 5), **text_attr())
        if DEBUG:
            screen.draw.text(str(self.goal), topleft=(WIDTH // 2, 5), **text_attr())
            screen.draw.text(
                f"tile: {self.pacman.tile()}", topleft=(3 * WIDTH / 4, 5), **text_attr()
            )


def text_attr() -> dict:
    return {
        "fontsize": 50,
        "color": "WHITE",
        "ocolor": "BLACK",
        "owidth": 0.5,
    }


def update():
    check_quit()
    if game.is_playing:
        game.update()


def draw():
    screen.fill(Colors.BACKGROUND)
    game.draw()


def check_quit():
    if keyboard.ESCAPE:
        exit()


game = Game()
music.play("celeste")

pgzrun.go()
