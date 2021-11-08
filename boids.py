import pygame
from pygame.locals import *
from random import random, randrange, uniform
import math
import sys

BOID_SIZE = BOID_W, BOID_H = 50, 35
WINDOW_SIZE = WINDOW_W, WINDOW_H = 1600, 900
BOID_ICON = pygame.transform.smoothscale(pygame.image.load("boid.png"), BOID_SIZE)
BOID_ICONS = {angle % 360: pygame.transform.rotate(BOID_ICON, -angle) for angle in range(360)}
DEFAULT_NUM = 50

# Boid related constants
MAX_SPEED = 4
MIN_SPEED = 2
FOV = 75
COHESION_STRENGTH = 0.00025
SEPARATION_STRENGTH = 0.005
ALIGNMENT_STRENGTH = 0.05
FOCUS_STRENGTH = 0.0005
JITTER_STRENGTH = 0.5

class Application:
    def __init__(self, args):
        """
        Constructs an Application instance

        Parameters
        ----------
            args : list
                Command line arguments supplied when the application was launched
        """
        self.running = True
        self.sceen = None
        self.size = self.weight, self.height = WINDOW_SIZE
        self.screen = pygame.display.set_mode(self.size)
        self.color = "lightblue"
        self.num = int(args[1]) if len(args) > 1 else DEFAULT_NUM


    def init(self):
        """
        Initializes the Application.

        Creates a Pygame window, colors the background, and spawns a flock of Boids.
        """
        pygame.init()
        self.screen = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.screen.fill(self.color)
        self.running = True

        self.flock = Flock(self.num)


    def handle_event(self, event):
        """
        Handles a Pygame event.

        Parameters
        ----------
            event : pygame.event.Event
                The event being handleded.
        """
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

    def loop(self):
        """
        Executes a single loop in the Application's cycle.

        In this case, it just tells the flock of boids to cycle once
        """
        self.flock.cycle()


    def render(self):
        """
        Render all contents to screen.
        """

        # Reset screen
        self.screen.fill(self.color)

        # Render each boid
        for boid in self.flock.boids:
            self.screen.blit(boid.icon, boid.rect)

        # Update screen
        pygame.display.update()

    def cleanup(self):
        """
        Clean up the Application before exiting.
        """
        pygame.quit()

    def execute(self):
        """
        Execute the Application.

        This function is the "game loop" that controls the logical flow of events.
        """
        print("Application Start")
        self.init()

        while(self.running):
            for event in pygame.event.get():
                self.handle_event(event)

            self.loop()

            self.render()

        self.cleanup()
        print("Application Exit")

class Boid:
    """
    A single Boid that exhibits herd-like behavior when in a flock of other Boids.

    Attributes
    ----------
        angle : float
            The angle which the Boid is facing
        icon : pygame.Surface
            Renderable icon of this Boid
        rect : pygame.Rect
            Rectangular area of the Boid's icon
        pos : Position
            Position of the Boid
        vel : Position
            Velocity of the Boid
        fov : int
            Field of view, or sight distance of the Boid
        divergence_chance : float
            Chance for the Boid to exhibit divergent behavior
        max_speed : int
            Maximum speed
        min_speed : int
            Minimum speed
        bounds : Position
            Maximum bounds the Boid is allowed to travel
        min_dist : float
            Minimum distance preferred between Boids

    Methods
    -------
        update() : None
            Updates the relevant fields of the Boid, based on its velocity
        limit_speed() : None
            Limits the speed of the Boid, based on its min and max speed fields
        avoid_walls() : None
            Causes the Boid to turn to avoid walls
        in_sight(other) : bool
            Determines if another Boid is in sight of the current Boid
        too_close(other) : bool
            Determines if another Boid is too close to the current Boid
    """
    def __init__(self, pos, bounds = None):
        """
        Initializes the Boid.

        Parameters
        ----------
            pos : Position
                Position of the Boid
            bounds : Position
                Maximum bounds the Boid is allowed to travel
        """
        if type(pos) is tuple:
            pos = Position(pos)
        if type(bounds) is tuple:
            bounds = Position(bounds)

        self.angle = randrange(0, 360)
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
        """
        Updates the position and angle of the Boid, based on its velocity.
        """
        self.limit_speed()
        self.avoid_walls()

        self.angle = round(self.vel.angle(degrees=True)) % 360

        self.pos = (self.pos + self.vel) % self.bounds

        # Rotate the boid's icon
        old_center = self.rect.center
        self.icon = BOID_ICONS[self.angle]
        self.rect = self.icon.get_rect()
        self.rect.center = self.pos.as_tuple()


    def limit_speed(self):
        """
        Limits the speed of the Boid, based on its min and max speed fields.
        """
        speed = self.vel.magnitude()

        if speed > self.max_speed:
            self.vel = (self.vel / speed) * self.min_speed

        if speed < self.min_speed:
            self.vel = (self.vel / speed) * self.max_speed


    def avoid_walls(self):
        """
        Steers the Boid to avoid collision with walls
        """
        turn = 0.5
        margin = 50

        if self.pos.x < margin:
            self.vel.x += turn

        if self.pos.x > self.bounds.x - margin:
            self.vel.x -= turn

        if self.pos.y < margin:
            self.vel.y += turn

        if self.pos.y > self.bounds.y - margin:
            self.vel.y -= turn

    def in_sight(self, other):
        """
        Determines if `other` is within sight of the current Boid.

        Parameters
        ----------
            other : Boid
                The other Boid being checked

        Returns
        -------
            true if the other Boid is within sight
        """
        return self.pos.dist(other.pos) < self.fov

    def too_close(self, other):
        """
        Determines if `other` is too close to the current Boid.

        Parameters
        ----------
            other : Boid
                The other Boid being checked

        Returns
        -------
            true if the other Boid is too close
        """
        return self.pos.dist(other.pos) < self.min_dist

class Flock:
    """
    Represents a flock of Boids.

    Handles all calculations and movements of Boids within the flock.

    Attributes
    ----------
        max_size : int
            Maximum number of Boids allowed in the flock (for performance reasons)
        boids : list
            List of all Boids in the flock
        size : int
            Number of Boids in the flock
        focal_point : Position
            Point of focus for all Boids in the flock

    Methods
    -------
        spawn(pos, bounds) : None
            Spawns a Boid in the flock
        cycle() : None
            Applies all Boid rules to the entire flock
    """
    def __init__(self, size, max_size = 100):
        self.max_size = max_size
        self.boids = []
        self.size = 0
        self.focal_point = None

        for i in range(size):
            x = randrange(BOID_W, WINDOW_W - BOID_W)
            y = randrange(BOID_H, WINDOW_H - BOID_H)
            pos = Position(x, y)
            self.spawn(pos, Position(WINDOW_SIZE))


    def spawn(self, pos, bounds = None):
        if self.size < self.max_size:
            self.boids.append(Boid(pos, bounds))
            self.size += 1
        else:
            print(f"Maximum Capacity ({self.max_size}) reached!")

    def cycle(self):
        for boid in self.boids:
            separation = Position()
            cohesion = Position()
            alignment = Position()
            focus = Position()
            jitter = Position()

            in_sight = 0
            too_close = 0

            for other in self.boids:
                if boid is not other:
                    if boid.too_close(other):
                        separation += boid.pos - other.pos
                        too_close += 1

                    if boid.in_sight(other):
                        cohesion += other.pos
                        alignment += other.vel
                        in_sight += 1

            if too_close > 0:
                separation /= too_close

            if in_sight > 0:
                cohesion /= in_sight
                alignment /= in_sight

            cohesion -= boid.pos
            alignment -= boid.vel

            if self.focal_point:
                focus = self.focal_point - boid.pos

            if random() < boid.divergence_chance:
                jitter.x = uniform(-boid.vel.y, boid.vel.y)
                jitter.y = uniform(-boid.vel.x, boid.vel.x)


            boid.vel += (separation * SEPARATION_STRENGTH) \
                + (cohesion * COHESION_STRENGTH) \
                + (alignment * ALIGNMENT_STRENGTH) \
                + (focus * FOCUS_STRENGTH) \
                + (jitter * JITTER_STRENGTH)

            boid.update()

class Position:
    """
    A single coordinate on a 2-dimensional plane.

    Attributes
    ----------
        x : float
            The x coordinate
        y : float
            The y coordinate

    Methods
    -------
        dist(other) : float
            Calculates the distance between this Point and another.
        angle(other, degrees) : float
            Calculates the angle between this Position and another.
        as_tuple() : tuple
            Returns this Position as a tuple.
        magnitude() : float
            Calculates the magnitude of the Position.
    """
    def __init__(self, x = 0, y = 0):
        """
        Initializes this Position.

        Parameters
        ----------
            x : float
                The x coordinate
            y : float
                The y coordinate
        """
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
            return Position(self.x / other, self.y / other) if other != 0 else Position()

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
        """
        Calculates the distance between this Point and another.

        Parameters
        ----------
            other : Position
                The other Position to calculate distance between

        Returns
        -------
            The distance between `self` and `other`
        """
        if type(other) is Position:
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        elif type(other) is tuple:
            return math.sqrt((self.x - other[0])**2 + (self.y - other[1])**2)

    def angle(self, other = None, degrees = False):
        """
        Calculates the angle between this Position and another.

        Parameters
        ----------
            other (optional) : Position
                The other Position to use to calculate the angle between
            degrees (optional) : bool
                Whether to calculate the angle in degrees

        Returns
        -------
            The angle between `self` and `other`
        """
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
        """
        Returns this Position as a tuple.

        Returns
        -------
            This Position in tuple format
        """
        return self.x, self.y

    def magnitude(self):
        """
        Calculates the magnitude of the Position.

        Returns
        -------
            The magnitude of this Position
        """
        return math.sqrt(self.x**2 + self.y**2)


if __name__ == "__main__" :
    boids = Application(sys.argv)
    boids.execute()
