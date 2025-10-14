# train_offline.py
import os
import time
import pickle
import argparse

# Run pygame headless
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402
import neat    # noqa: E402

# Use your existing physics – no rendering done here
from ..core.bird import Bird
from ..core.pipe import Pipe

WIN_WIDTH = 1000
WIN_HEIGHT = 1000
FPS = 240               # fast sim
MAX_FRAMES_PER_RUN = 60 * 120  # ~120s at 60fps-equivalent per genome (safety stop)

def eval_genome(genome, config):
    """
    Evaluate a single genome. Fitness:
      +1 per frame survived, +50 per pipe passed.
    """
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    bird = Bird(280, 250, "ai")
    pipes = [Pipe(WIN_WIDTH + 20)]
    passed = set()
    frames = 0

    while True:
        frames += 1
        bird.move()

        add_pipe = False
        rem = []

        for p in pipes:
            p.move()
            if p.collide(bird):
                return max(0.0, genome.fitness)

            if p not in passed and p.x < bird.x:
                passed.add(p)
                add_pipe = True

            if p.x + p.PIPE_TOP.get_width() < 0:
                rem.append(p)
                passed.discard(p)

        if add_pipe:
            pipes.append(Pipe(WIN_WIDTH + 20))
            genome.fitness += 50.0

        for r in rem:
            pipes.remove(r)

        # out of bounds ends
        if bird.y + bird.img.get_height() - 10 >= WIN_HEIGHT or bird.y < -50:
            return max(0.0, genome.fitness)

        # choose relevant pipe
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # NN acts
        output = net.activate((
            bird.y,
            abs(bird.y - pipes[pipe_ind].height),
            abs(bird.y - pipes[pipe_ind].bottom)
        ))
        if output[0] > 0.5:
            bird.jump()

        genome.fitness += 1.0  # survive bonus

        if frames >= MAX_FRAMES_PER_RUN:
            return genome.fitness

def eval_genomes(genomes, config):
    for _, g in genomes:
        g.fitness = 0.0
        eval_genome(g, config)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to NEAT config (e.g., config-feedforwardEasy.txt)")
    parser.add_argument("--generations", type=int, default=60, help="Number of generations to run")
    parser.add_argument("--out", required=True, help="Output winner filename (e.g., winner_EASY.pkl)")
    args = parser.parse_args()

    pygame.init()

    config = neat.config.Config(
        neat.DefaultGenome, neat.DefaultReproduction,
        neat.DefaultSpeciesSet, neat.DefaultStagnation,
        args.config
    )

    p = neat.Population(config)
    # Console logs
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    print(f"[TRAIN] Generations={args.generations}  Config={os.path.basename(args.config)}")
    t0 = time.time()
    winner = p.run(eval_genomes, args.generations)
    print(f"[TRAIN] Done in {time.time()-t0:.1f}s. Saving to {args.out}")

    with open(args.out, "wb") as f:
        pickle.dump(winner, f)
    print("[TRAIN] Saved:", args.out)

if __name__ == "__main__":
    main()
