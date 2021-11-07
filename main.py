import pygame
from pygame.locals import *
from random import randint, random, randrange, uniform
from time import sleep
import math
import sys

BOID_SIZE = BOID_W, BOID_H = 50, 35
WINDOW_SIZE = WINDOW_W, WINDOW_H = 1600, 900
BOID_ICON = pygame.transform.smoothscale(pygame.image.load("boid.png"), BOID_SIZE)
MIN_DEGREES, MAX_DEGREES = 0, 360
BOID_ICONS = {angle % MAX_DEGREES: pygame.transform.rotate(BOID_ICON, -angle) for angle in range(MAX_DEGREES)}
PI_180 = math.pi / 180
DEFAULT_NUM = 25

# Boid related constants
MAX_SPEED = 3
MIN_SPEED = 1
WALL_AVOID = 0.5
FOV = 75
COHESION_FACTOR = 0.00025
SEPARATION_FACTOR = 0.005
ALIGNMENT_FACTOR = 0.05

class App:
    def __init__(self, num=None):
        self.running = True
        self.sceen = None
        self.size = self.weight, self.height = WINDOW_SIZE
        self.screen = pygame.display.set_mode(self.size)
        self.color = "white"
        self.num = num


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
            self.flock.focal_point = event.pos
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
            #self.screen.blit(boid.text.image, boid.rect.move(-BOID_W / 2, BOID_H * 1.5))

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
        self.angle = randrange(MIN_DEGREES, MAX_DEGREES)
        self.icon = BOID_ICONS[self.angle]
        self.rect = self.icon.get_rect()
        self.rect.center = self.x , self.y = pos
        self.vx = random() * MAX_SPEED - MAX_SPEED
        self.vy = random() * MAX_SPEED - MAX_SPEED
        self.fov = FOV
        self.divergence_chance = 0.01
        self.max_speed = MAX_SPEED
        self.min_speed = MIN_SPEED
        self.bounds = bounds
        self.min_dist = self.fov / 2

    def update(self):
        self.limit_speed()
        self.avoid_walls()

        self.angle = round(math.degrees(math.atan2(self.vy, self.vx))) % MAX_DEGREES

        self.x = (self.x + self.vx) % self.bounds[0]
        self.y = (self.y + self.vy) % self.bounds[1]

        # Rotate the boid
        old_center = self.rect.center
        self.icon = BOID_ICONS[self.angle]
        self.rect = self.icon.get_rect()
        self.rect.center = self.x, self.y

    def limit_speed(self):
        speed = abs(self.vx) + abs(self.vy)

        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.min_speed

        if speed < self.min_speed:
            self.vx = (self.vx / speed) * self.min_speed
            self.vy = (self.vy / speed) * self.max_speed


    def avoid_walls(self):
        turn = WALL_AVOID
        margin = 100

        if self.x < margin:
            self.vx += turn

        if self.x > self.bounds[0] - margin:
            self.vx -= turn

        if self.y < margin:
            self.vy += turn

        if self.y > self.bounds[1] - margin:
            self.vy -= turn


class Flock:
    def __init__(self, size):
        self.MAX_CAPACITY = 100
        self.boids = []
        self.size = 0
        self.focal_point = None
        self.separation_const = SEPARATION_FACTOR
        self.cohesion_const = COHESION_FACTOR
        self.alignment_const = ALIGNMENT_FACTOR

        for i in range(size):
            x = randint(BOID_W, WINDOW_W - BOID_W)
            y = randint(BOID_H, WINDOW_H - BOID_H)
            self.spawn((x, y), WINDOW_SIZE)


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

            boid.vx += sep[0] + coh[0] + ali[0] + foc[0] + jit[0]
            boid.vy += sep[1] + coh[1] + ali[1] + foc[1] + jit[1]

            boid.update()

    def focus(self, boid):
        if self.focal_point:
            focus_const = 0.0025
            x = self.focal_point[0] - boid.x
            y = self.focal_point[1] - boid.y

            return (x * focus_const, y * focus_const)
        else:
            return 0, 0

    def jitter(self, boid):
        vx = vy = 0
        if random() < boid.divergence_chance:
            vx += uniform(-boid.vy, boid.vy)
            vy += uniform(-boid.vx, boid.vx)

        return (vx, vy)


    def separation(self, boid):
        x = y = 0
        neighbors = 0
        for other in self.boids:
            if boid is not other:
                if self.distance(boid, other) < boid.min_dist:
                    x += boid.x - other.x
                    y += boid.y - other.y
                    neighbors += 1

        if neighbors > 0:
            x = x / neighbors
            y = y / neighbors

        return (x * self.separation_const, y * self.separation_const)

    def cohesion(self, boid):
        x = y = 0
        neighbors = 0

        for other in self.boids:
            if boid is not other:
                if self.distance(boid, other) < boid.fov:
                    x += other.x
                    y += other.y
                    neighbors += 1

        if neighbors > 0:
            x = x / neighbors
            y = y / neighbors

        x -= boid.x
        y -= boid.y

        return (x * self.cohesion_const, y * self.cohesion_const)

    def alignment(self, boid):
        vx = vy = 0
        neighbors = 0
        for other in self.boids:
            if boid is not other:
                if self.distance(boid, other) < boid.fov:
                    vx += other.vx
                    vy += other.vy
                    neighbors += 1

        if neighbors > 0:
            vx = vx / neighbors
            vy = vy / neighbors

        vx -= boid.vx
        vy -= boid.vy

        return (vx * self.alignment_const, vy * self.alignment_const)

    def distance(self, boid1, boid2):
        return math.sqrt((boid1.x - boid2.x)**2 + (boid1.y - boid2.y)**2)


class Text(pygame.sprite.Sprite):
    def __init__(self, text, width, height):
        # Call the parent class (Sprite) constructor  
        pygame.sprite.Sprite.__init__(self)

        self.font = pygame.font.SysFont("Arial", 12)
        self.textSurf = self.font.render(text, 1, "white")
        self.image = pygame.Surface((width, height))
        self.image.set_alpha(255)
        W = self.textSurf.get_width()
        H = self.textSurf.get_height()
        self.image.blit(self.textSurf, [width/2 - W/2, height/2 - H/2])

if __name__ == "__main__" :
    size = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_NUM

    theApp = App(size)

    theApp.on_execute()
