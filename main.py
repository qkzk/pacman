import os
from dataclasses import dataclass
from math import ceil, floor

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


class Phantom:
    def __init__(self, x: int, y: int, color: str):
        self.color = color
        self.rect = Rect(x, y, TILE, TILE)

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


class Pacman:
    def __init__(self, x: int, y: int):
        self.rect: Rect = Rect((x, y, TILE, TILE))

    def draw(self):
        if DEBUG:
            screen.draw.filled_rect(self.rect, "BROWN")
        screen.draw.filled_circle(
            (self.rect.x + TILE // 2, self.rect.y + TILE // 2), 15, Colors.PACMAN
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
    SPEED: int = 2

    def __init__(self):
        self.pacman: Pacman
        self.phantoms: list[Phantom]
        self.world: list[list[int]]
        self.score: int
        self.goal: int
        self.is_playing = False
        self.is_started = False

        clock.schedule(self.reset, 2.0)

    def reset(self):
        self.pacman: Pacman = Pacman(TILE * 30, TILE * 17)
        self.phantoms: list[Phantom] = [
            Phantom(5 * TILE, 2 * TILE, Colors.PHANTOMS[0]),
            Phantom(5 * TILE, 4 * TILE, Colors.PHANTOMS[1]),
            Phantom(5 * TILE, 6 * TILE, Colors.PHANTOMS[2]),
            Phantom(5 * TILE, 8 * TILE, Colors.PHANTOMS[3]),
        ]
        self.world: list[list[int]] = parse_world(WORLD)
        self.goal = sum(
            (sum(1 for cell in row if cell == self.BALL) for row in self.world)
        )
        self.score = 0
        self.is_playing = True
        self.is_started = True

    def read_keys(self) -> dict:
        return {
            "up": keyboard.up,
            "down": keyboard.down,
            "left": keyboard.left,
            "right": keyboard.right,
        }

    def eat(self, tile_x: int, tile_y: int):
        if self.world[tile_y][tile_x] == self.BALL:
            self.world[tile_y][tile_x] = self.VOID
            self.score += 1

    def game_over(self) -> bool:
        return self.score == self.goal

    def update(self):
        keys = self.read_keys()
        tile_x, tile_y = self.pacman.tile()
        self.eat(tile_x, tile_y)
        if self.game_over():
            clock.schedule(self.reset, 2.0)
            self.is_playing = False
        if (
            keys["up"]
            and self.pacman.rect.y > TILE
            and self.world[(self.pacman.rect.y - self.SPEED) // TILE][
                self.pacman.rect.x // TILE
            ]
            != self.WALL
        ):
            self.pacman.rect.y -= self.SPEED
        elif (
            keys["down"]
            and self.pacman.rect.y < HEIGHT - 2 * TILE
            and self.world[(self.pacman.rect.y + self.SPEED) // TILE + 1][
                self.pacman.rect.x // TILE
            ]
            != self.WALL
        ):
            self.pacman.rect.y += self.SPEED
        if (
            keys["left"]
            and self.pacman.rect.x > TILE
            and self.world[self.pacman.rect.y // TILE][
                (self.pacman.rect.x - self.SPEED) // TILE
            ]
            != self.WALL
        ):
            self.pacman.rect.x -= self.SPEED
        elif (
            keys["right"]
            and self.pacman.rect.x < WIDTH - 2 * TILE
            and self.world[self.pacman.rect.y // TILE][
                (self.pacman.rect.x + self.SPEED) // TILE + 1
            ]
            != self.WALL
        ):
            self.pacman.rect.x += self.SPEED

    def draw_splash(self):
        screen.draw.text(
            "GAME OVER" if self.is_started else "PACMAN",
            center=(WIDTH / 2, HEIGHT / 2),
            **text_attr(),
        )

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

pgzrun.go()
