# PyBoids

An implementation of the Boids algorithm ([Craig Reynolds, 1986](http://www.red3d.com/cwr/boids/)) in Python using [Pygame](https://www.pygame.org/).

## About

Boids ("Bird-oids") are an example of complex behavior from simple rules. The Boids have three basic rules:
1. Separation - Boids steer to avoid collisions
2. Cohesion - Boids steer towards the center of a nearby flock
3. Alignment - Boids attempt to match the velocity of flockmates

From these three simple rules, we can observe complex herding behavior.

I've added two additional rules, just for fun:
1. Focus - Boids steer towards focal points (mouse cursor)
2. Jitter - Boids have a small chance to randomly turn a small amount

## To run

`python3 boids.py [number of boids to spawn]`

Of course, you need Python and Pygame installed :)

## Why?

Over a year ago I attempted to implement Boids in Rust using the Amethyst game engine. I was mostly successful, but that engine has since been discontinued. I wanted to experiment more with Boids so I assembled this in Python.

### References:

- [Boids](http://www.red3d.com/cwr/boids/)
- [Boids Pseudocode](http://www.kfish.org/boids/pseudocode.html)
- [Boids Algorithm Demonstration](https://eater.net/boids)
- [Pygame Object Oriented Tutorial](http://pygametutorials.wikidot.com/tutorials-basic)
