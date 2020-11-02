import pygame
import neat
import time
import os
import random
import pickle
pygame.font.init()

os.environ['SDL_VIDEO_WINDOW_POS'] = "200, 30"  #starting location of window
WIN_WIDTH = 450
WIN_HEIGHT = 700

STAT_FONT = pygame.font.SysFont('comicsans', 30)
GAME_OVER_FONT = pygame.font.Font(r'C:\Users\3558\Desktop\Projects\Flappy Bird AI\game_over.ttf', 100)

# BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
#              pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
#              pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]

BIRD_IMGS = [pygame.image.load(os.path.join("imgs", "bird1.png")),
             pygame.image.load(os.path.join("imgs", "bird2.png")),
             pygame.image.load(os.path.join("imgs", "bird3.png"))]
BIRD_IMGS = [pygame.transform.scale(img, (int(1.5*img.get_size()[0]), int(1.5*img.get_size()[1]))) for img in BIRD_IMGS]
PIPE_IMG = pygame.image.load(os.path.join("imgs", "pipe.png"))
PIPE_IMG = pygame.transform.scale(PIPE_IMG, (int(1.3*PIPE_IMG.get_size()[0]), int(1.3*PIPE_IMG.get_size()[1])))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "bg.png")), (WIN_WIDTH, WIN_HEIGHT+200))

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5        #when jump happens, to move up negative velocity
        self.tick_count = 0    
        self.height = self.y

    def move(self):
        self.tick_count = self.tick_count + 1
        d = self.vel*self.tick_count + 1.5*self.tick_count**2   #calculate displacement

        if d>=16:       #to fix the displacement amount, no acceleration over this
            d = 16
        if d<0:         #if it is going up, fine tune it
            d = d - 2
        
        self.y = self.y + d    #move as per calculation, up or down

        #if we are moving up then tilt the bird to predetermined max value,
        #allows to avoid bird getting tilted weirdly
        if d<0 or self.y<self.height+50:
            if self.tilt<self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        #if we are moving down then slowly tilt till 90 deg down using
        #predetermined rotation velocity
        else:
            if self.tilt> -90:
                self.tilt = self.tilt - self.ROT_VEL
    
    def draw(self, win):
        self.img_count = self.img_count + 1     #helps determine which image to show (flapping)
                                                #based on time passed (wing- up, levelled, down)

        if self.img_count<self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count<self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count<self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count<self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        if self.tilt<=-80:  #if tilt is a lot downwards then no point in flapping
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2
        
        #rotate image from center w.r.t. to tilt
        rotated_image = pygame.transform.rotate(self.img, self.tilt)    #rotates from top-left corner
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)    #handles our center issue for rotation
        win.blit(rotated_image, new_rect.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 150   #vertical gap
    VEL = 5     

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 400)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x = self.x - self.VEL  #move left
    
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) #returns None if no collision
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True
        
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 = self.x1 - self.VEL    #move left with velocity
        self.x2 = self.x2 - self.VEL

        #bring image behind the other as soon as it gets out of window
        if self.x1 + self.WIDTH<0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH<0:
            self.x2 = self.x1 + self.WIDTH
    
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0, 0))    #blit draws the images on window
    
    for pipe in pipes:
        pipe.draw(win)          #call to draw all the pipes

    text = STAT_FONT.render("Score: "+str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH-10-text.get_width(), 10))

    base.draw(win)              #call to draw the bases

    for bird in birds:
        bird.draw(win)              #call to the draw of Bird class

    pygame.display.update()     #refresh what is shown

def main(config_path, save_path):
    nets = []
    ge = []
    birds = []

    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    with open(save_path, "rb") as f:
        genome = pickle.load(f)

    genomes = [(1, genome)]

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(200, 270))    #bird obj
        ge.append(g)

    base = Base(630)
    pipes = [Pipe(500)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  #window obj
    run = True  #while loop fuel
    clock = pygame.time.Clock()     #game clock
    score = 0       #game score
    
    while run:
        clock.tick(30)  #every iteration passes 30 ticks
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                text = GAME_OVER_FONT.render("Game Over", 1, (0, 0, 0))
                win.blit(text, (int(WIN_WIDTH/4+20), int(WIN_HEIGHT/2-50)))
                pygame.display.update()
                time.sleep(1)
                pygame.quit()
                quit()
        
        pipe_ind = 0
        if len(birds)>0:
            if len(pipes)>1 and birds[0].x>pipes[0].x+pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0]>0.5:
                bird.jump()
        #bird.move()
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    text = GAME_OVER_FONT.render("Game Over", 1, (0, 0, 0))
                    win.blit(text, (int(WIN_WIDTH/4+20), int(WIN_HEIGHT/2-50)))
                    pygame.display.update()
                    time.sleep(1)                    
                    pygame.quit()
                    quit()

                if not pipe.passed and pipe.x<bird.x:       #if pipe has been passed by bird
                    pipe.passed = True
                    add_pipe = True
            
            if pipe.x + pipe.PIPE_TOP.get_width()<0:    #if pipe is out of window
                rem.append(pipe)

            pipe.move()
            
        if add_pipe:                                #if a pipe has been passed create a new pipe and increment score
            score = score+1
            pipes.append(Pipe(500))
            
        for r in rem:
            pipes.remove(r)
        
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height()>=630 or bird.y<0:
                text = GAME_OVER_FONT.render("Game Over", 1, (0, 0, 0))
                win.blit(text, (int(WIN_WIDTH/4+20), int(WIN_HEIGHT/2-50)))
                pygame.display.update()
                time.sleep(1)
                pygame.quit()
                quit()

        base.move()
        draw_window(win, birds, pipes, base, score)
  
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    save_path = os.path.join(local_dir, "winner.pickle")
    main(config_path, save_path)