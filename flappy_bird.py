import pygame
import random
import neat

pygame.init()

# Parameters Input
# DRAW_LINES = bool(input("Do you want to show reference lines?(y/n) [Default: y] ") == "y") or True
# SCORE_THRESHOLD = int(input("At what score to stop running? [Default: 100] ") or 100)
# MAX_GEN = int(input("What is the maximum generation? [Default: 20] ") or 20)
DRAW_LINES = True
SCORE_THRESHOLD = 100
MAX_GEN = 20

# Game Variables
WIN_WIDTH = 400
WIN_HEIGHT = 640
GEN = -1

# Load Images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load("imgs/bird1.png")),
             pygame.transform.scale2x(pygame.image.load("imgs/bird2.png")),
             pygame.transform.scale2x(pygame.image.load("imgs/bird3.png"))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load("imgs/pipe.png"))
BASE_IMG = pygame.transform.scale2x(pygame.image.load("imgs/base.png"))
BG_IMG = pygame.transform.scale2x(pygame.image.load("imgs/bg.png"))
STAT_FONT = pygame.font.SysFont("comicsans", 30)


# Bird Class
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    # Function to make the bird jump
    def jump(self):
        self.vel = -8.4
        self.tick_count = 0
        self.height = self.y

    # Function to implement gravity
    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.2 * self.tick_count ** 2
        if d >= 12:
            d = 12
        if d < 0:
            d -= 1.6
        self.y += d

        if d < 0 or self.y < self.height + 40:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    # Function to get the mask
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

    # Function to draw and animate the bird
    def draw(self, window):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center)
        window.blit(rotated_img, new_rect.topleft)


# Pipe Class
class Pipe:
    GAP = 160
    VEL = 4

    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    # Function to determine the top and bottom location
    def set_height(self):
        self.height = random.randrange(40, 360)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # Function to move the pipe
    def move(self):
        self.x -= self.VEL

    # Function to detect collision
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        return False

    # Function to draw the pipe
    def draw(self, window):
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


# Base Class
class Base:
    VEL = 4
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, window):
        window.blit(self.IMG, (self.x1, self.y))
        window.blit(self.IMG, (self.x2, self.y))


# Function to draw components on game window
def draw_window(window, birds, pipes, base, score, gen, pipe_ind):
    window.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(window)

    text = STAT_FONT.render(f"Score: {score}", True, (255, 255, 255))
    window.blit(text, (WIN_WIDTH - 8 - text.get_width(), 8))

    text = STAT_FONT.render(f"Gen: {gen}", True, (255, 255, 255))
    window.blit(text, (8, 8))

    text = STAT_FONT.render(f"Alive: {len(birds)}", True, (255, 255, 255))
    window.blit(text, (8, 48))

    base.draw(window)

    for bird in birds:
        if DRAW_LINES:
            try:
                pygame.draw.line(window, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(window, (255, 0, 0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        bird.draw(window)

    pygame.display.update()


# Neuro-evolution Evaluation Function
def eval(genomes, config):
    global GEN
    GEN += 1

    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(184, 280))
        g.fitness = 0
        ge.append(g)

    base = Base(584)
    pipes = [Pipe(480)]

    score = 0

    window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird Neuro-Evolution")
    clock = pygame.time.Clock()

    # Game loop
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            running = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            # Neural Network Inputs
            # output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height),
            #                            abs(bird.y - pipes[pipe_ind].bottom)))
            output = nets[x].activate((bird.y, pipes[pipe_ind].x,
                                       abs(bird.y - pipes[pipe_ind].height),
                                       abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()

        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(480))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 584 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        draw_window(window, birds, pipes, base, score, GEN, pipe_ind)

        if score >= SCORE_THRESHOLD and pipes[0].x <= -10:
            break


# NEAT Config Function
def run(config_path):
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval, MAX_GEN)
    print('\nBest genome:\n{!s}'.format(winner))


# Main Function
if __name__ == "__main__":
    config_path = "config-neat.txt"
    run(config_path)
