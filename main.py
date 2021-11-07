import pygame
from pygame.locals import *
from random import random, randrange, uniform
import math
import sys

BOID_SIZE = BOID_W, BOID_H = 50, 35
WINDOW_SIZE = WINDOW_W, WINDOW_H = 1600, 900
BOID_ICON = pygame.transform.smoothscale(pygame.image.load("boid.png"), BOID_SIZE)
MIN_DEGREES, MAX_DEGREES = 0, 360
BOID_ICONS = {angle % MAX_DEGREES: pygame.transform.rotate(BOID_ICON, -angle) for angle in range(MAX_DEGREES)}
DEFAULT_NUM = 25

# Boid related constants
MAX_SPEED = 3
MIN_SPEED = 1
FOV = 75
COHESION_STRENGTH = 0.00025
SEPARATION_STRENGTH = 0.005
ALIGNMENT_STRENGTH = 0.05
FOCUS_STRENGTH = 0.0005
JITTER_STRENGTH = 0.5

class App:
    def __init__(self, args):
        self.running = True
        self.sceen = None
        self.size = self.weight, self.height = WINDOW_SIZE
        self.screen = pygame.display.set_mode(self.size)
        self.color = "lightblue"
        self.num = int(args[1]) if len(args) > 1 else DEFAULT_NUM


    def on_init(self):
        print("Begin App")
        pygame.init()
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.screen.fill(self.color)
        self.running = True

        self.flock = Flock(self.num)


    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.flock.spawn(event.pos, WINDOW_SIZE)
        elif event.type == pygame.MOUSEMOTION:
            self.flock.focal_point = Position(event.pos)
        elif event.type == pygame.WINDOWLEAVE:
            self.flock.focal_point = None
        else:
            pass
            #print(event)

    def on_loop(self):
        self.flock.cycle()


    def on_render(self):
        self.screen.fill(self.color)

        for boid in self.flock.boids:
            self.screen.blit(boid.icon, boid.rect)

        pygame.display.flip()
        pygame.display.update()

    def on_cleanup(self):
        print("Game End")
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self.running = False

        while(self.running):
            for event in pygame.event.get():
                self.on_event(event)

            self.on_loop()

            self.on_render()

        self.on_cleanup()

class Boid:
    def __init__(self, pos, bounds = None):
        if type(pos) is tuple:
            pos = Position(pos)
        if type(bounds) is tuple:
            bounds = Position(bounds)

        self.angle = randrange(MIN_DEGREES, MAX_DEGREES)
        self.icon = BOID_ICONS[self.angle]
        self.rect = self.icon.get_rect()
        self.rect.center = pos.as_tuple()

        self.pos = pos
        self.vel = Position()
        self.fov = FOV
        self.divergence_chance = 0.01
        self.max_speed = MAX_SPEED
        self.min_speed = MIN_SPEED
        self.bounds = bounds
        self.min_dist = self.fov / 2

    def update(self):
        self.limit_speed()
        self.avoid_walls()

        self.angle = round(self.vel.angle(degrees=True)) % MAX_DEGREES

        self.pos = (self.pos + self.vel) % self.bounds

        # Rotate the boid's icon
        old_center = self.rect.center
        self.icon = BOID_ICONS[self.angle]
        self.rect = self.icon.get_rect()
        self.rect.center = self.pos.as_tuple()


    def limit_speed(self):
        speed = self.vel.magnitude()

        if speed > self.max_speed:
            self.vel = (self.vel / speed) * self.min_speed

        if speed < self.min_speed:
            self.vel = (self.vel / speed) * self.max_speed


    def avoid_walls(self):
        turn = 0.5
        margin = 100

        if self.pos.x < margin:
            self.vel.x += turn

        if self.pos.x > self.bounds.x - margin:
            self.vel.x -= turn

        if self.pos.y < margin:
            self.vel.y += turn

        if self.pos.y > self.bounds.y - margin:
            self.vel.y -= turn

class Flock:
    def __init__(self, size):
        self.MAX_CAPACITY = 100
        self.boids = []
        self.size = 0
        self.focal_point = None

        for i in range(size):
            x = randrange(BOID_W, WINDOW_W - BOID_W)
            y = randrange(BOID_H, WINDOW_H - BOID_H)
            pos = Position(x, y)
            self.spawn(pos, Position(WINDOW_SIZE))


    def spawn(self, pos, bounds = None):
        if self.size < self.MAX_CAPACITY:
            self.boids.append(Boid(pos, bounds))
            self.size += 1
        else:
            print(f"Maximum Capacity ({self.MAX_CAPACITY}) reached!")

    def cycle(self):
        for boid in self.boids:
            sep = self.separation(boid)
            coh = self.cohesion(boid)
            ali = self.alignment(boid)
            foc = self.focus(boid)
            jit = self.jitter(boid)

            boid.vel += (sep * SEPARATION_STRENGTH) + (coh * COHESION_STRENGTH) + (ali * ALIGNMENT_STRENGTH) + (foc * FOCUS_STRENGTH) + (jit * JITTER_STRENGTH)

            boid.update()

    def focus(self, boid):
        pos = Position()
        if self.focal_point:

            pos = self.focal_point - boid.pos

        return pos

    def jitter(self, boid):
        vx = vy = 0

        if random() < boid.divergence_chance:
            vx += uniform(-boid.vel.y, boid.vel.y)
            vy += uniform(-boid.vel.x, boid.vel.x)

        return Position(vx, vy)


    def separation(self, boid):
        pos = Position()
        neighbors = 0

        for other in self.boids:
            if boid is not other:
                if self.distance(boid, other) < boid.min_dist:
                    pos += boid.pos - other.pos
                    neighbors += 1

        if neighbors > 0:
            pos /= neighbors

        return pos

    def cohesion(self, boid):
        pos = Position()
        neighbors = 0

        for other in self.boids:
            if boid is not other:
                if self.distance(boid, other) < boid.fov:
                    pos += other.pos
                    neighbors += 1

        if neighbors > 0:
            pos /= neighbors

        pos -= boid.pos

        return pos

    def alignment(self, boid):
        vel = Position()
        neighbors = 0
        for other in self.boids:
            if boid is not other:
                if self.distance(boid, other) < boid.fov:
                    vel += other.vel
                    neighbors += 1

        if neighbors > 0:
            vel /= neighbors

        vel -= boid.vel
        return vel

    def distance(self, boid1, boid2):
        return boid1.pos.dist(boid2.pos)

class Position:
    def __init__(self, x = 0, y = 0):
        if type(x) is tuple:
            y = x[1]
            x = x[0]

        self.x, self.y = x, y

    def __add__(self, other):
        if type(other) is Position:
            return Position(self.x + other.x, self.y + other.y)
        elif type(other) is tuple:
            return Position(self.x + other[0], self.y + other[1])
        elif type(other) is int or type(other) is float:
            return Position(self.x + other, self.y + other)

    def __sub__(self, other):
        if type(other) is Position:
            return Position(self.x - other.x, self.y - other.y)
        elif type(other) is tuple:
            return Position(self.x - other[0], self.y - other[1])
        elif type(other) is int or type(other) is float:
            return Position(self.x - other, self.y - other)

    def __mul__(self, other):
        if type(other) is Position:
            return Position(self.x * other.x, self.y * other.y)
        elif type(other) is tuple:
            return Position(self.x * other[0], self.y * other[1])
        elif type(other) is int or type(other) is float:
            return Position(self.x * other, self.y * other)

    def __truediv__(self, other):
        if type(other) is Position:
            return Position(self.x / other.x, self.y / other.y)
        elif type(other) is tuple:
            return Position(self.x / other[0], self.y / other[1])
        elif type(other) is int or type(other) is float:
            return Position(self.x / other, self.y / other)

    def __floordiv__(self, other):
        if type(other) is Position:
            return Position(self.x // other.x, self.y // other.y)
        elif type(other) is tuple:
            return Position(self.x // other[0], self.y // other[1])
        elif type(other) is int or type(other) is float:
            return Position(self.x // other, self.y // other)

    def __mod__(self, other):
        if type(other) is Position:
            return Position(self.x % other.x, self.y % other.y)
        elif type(other) is tuple:
            return Position(self.x % other[0], self.y % other[1])
        elif type(other) is int or type(other) is float:
            return Position(self.x % other, self.y % other)

    def __str__(self):
        return f"({self.x}, {self.y})"

    def dist(self, other):
        if type(other) is Position:
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        elif type(other) is tuple:
            return math.sqrt((self.x - other[0])**2 + (self.y - other[1])**2)

    def angle(self, other = None, degrees = False):
        if other:
            if type(other) is Position:
                angle = math.atan2(other.y - self.y, other.x - self.x)
                return math.degrees(angle) if degrees else angle

            elif type(other) is tuple:
                angle = math.atan2(other[1] - self.y, other[0] - self.x)
                return math.degrees(angle) if degrees else angle
        else:
            angle = math.atan2(self.y, self.x)
            return math.degrees(angle) if degrees else angle

    def as_tuple(self):
        return self.x, self.y

    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

if __name__ == "__main__" :

    theApp = App(sys.argv)
    theApp.on_execute()
