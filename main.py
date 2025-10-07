import pygame as pg
from pathlib import Path
import random

pg.init()

FPS = 60
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
IMAGE_DIR = Path("assets/images")
SOUND_DIR = Path("assets/sounds")
GRAVITY = 2000
INITIAL_SPEED = -400
INCREASE_FACTOR = 1.1
DIFFICULTY_INTERVAL = 5


clock = pg.Clock()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def load_image(name, scale=1.0, **kwargs):
    fullname = IMAGE_DIR / name
    image = pg.image.load(fullname).convert_alpha()

    image = pg.transform.scale_by(image, scale)

    return image, image.get_rect(**kwargs)


def load_sound(name):
    class NoneSound:
        def play(self):
            pass

    if not pg.mixer.get_init():
        return NoneSound()

    fullname = SOUND_DIR / name
    sound = pg.mixer.Sound(fullname)

    return sound


class Spencer(pg.sprite.Sprite):
    JUMP_VELOCITY = -700
    MAX_AIR_TIME = 0.2
    ACCEL = 2000
    FRICTION = 0.9

    def __init__(self, dest, *groups):
        super().__init__(*groups)
        self.image, self.rect = load_image("spence.png", scale=0.2)
        self.rect.midbottom = dest

        self.velocity = pg.Vector2(0, 0)
        self.position = pg.Vector2(self.rect.midbottom)
        self.on_ground = True
        self.air_time = 0

    def update(self, delta=None, **kwargs):
        if delta is not None:
            if not self.on_ground:
                self.velocity.y += GRAVITY * delta
                self.air_time += delta
            else:
                self.air_time = 0

            if self.rect.collideobjects(ground_group.sprites()):
                self.on_ground = True
                self.position.y = ground_group.sprites()[0].rect.top
                self.velocity.y = 0

        self.velocity.x *= 0.9
        self.position += self.velocity * delta
        self.rect.midbottom = self.position
        if self.rect.left <= screen.get_rect().left:
            self.velocity.x = 0
        self.rect.clamp_ip(screen.get_rect())

    def jump(self):
        if self.air_time <= self.MAX_AIR_TIME:
            self.velocity.y = Spencer.JUMP_VELOCITY
            self.on_ground = False

    def move(self, direction):
        if direction == "right":
            self.velocity.x += Spencer.ACCEL * delta
        if direction == "left":
            self.velocity.x -= Spencer.ACCEL * delta


print(pg.Vector2(1, 2) * 5)


class Ground(pg.sprite.Sprite):
    IMAGE, _ = load_image("ground.png", scale=0.2)

    def __init__(self, *groups, **kwargs):
        super().__init__(*groups)
        self.image = Ground.IMAGE
        self.rect = self.image.get_rect(**kwargs)

    def update(self, delta=None, **kwargs):
        if delta is not None:
            self.rect.move_ip(speed * delta, 0)


class Cactus(pg.sprite.Sprite):
    IMAGE_RECT_TUPLES = [
        load_image(fp.name, scale=0.2) for fp in IMAGE_DIR.glob("cactus*.png")
    ]
    spawn_chance = 0.25

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image, _ = random.choice(Cactus.IMAGE_RECT_TUPLES)
        self.rect = self.image.get_rect()
        self.rect.left = screen.get_rect().right
        self.passed = False

    def update(self, delta=None, **kwargs):
        if delta is not None:
            self.rect.move_ip(speed * delta, 0)
            self.rect.bottom = ground_group.sprites()[0].rect.top

        if self.rect.right <= screen.get_rect().left:
            self.kill()


class Explosion(pg.sprite.Sprite):
    IMAGE, _ = load_image("explosion.png", scale=0.2)

    def __init__(self, target, *groups):
        super().__init__(*groups)
        self.image = Explosion.IMAGE
        self.rect = self.image.get_rect(center=target.rect.center)

    def update(self, *args, **kwargs):
        pass


class Score(pg.sprite.Sprite):
    """to keep track of the score."""

    def __init__(self, *groups):
        super().__init__(*groups)
        self.font = pg.Font(None, 100)
        self.font.set_italic(True)
        self.color = "white"
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", False, "black")
        self.update()

    def update(self, *args, **kwargs):
        self.rect = self.image.get_rect(topright=screen.get_rect().topright)

    def increase(self, amount):
        self.score += amount
        self.image = self.font.render(f"Score: {self.score}", False, "black")


all_sprites = pg.sprite.Group()
ground_group = pg.sprite.Group()
cactus_group = pg.sprite.Group()

background = pg.Surface(screen.get_size()).convert()
background.fill((170, 238, 187))

running = True

spencer = Spencer((75, 400), all_sprites)

thunder_sound = load_sound("thunder.mp3")
speed = INITIAL_SPEED

difficulty_timer = 0
score = Score(all_sprites)


while running:
    delta = clock.tick(FPS) / 1000
    screen.blit(background)

    for event in pg.event.get():
        if event.type == pg.QUIT or (
            event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
        ):
            running = False

    keys = pg.key.get_pressed()

    difficulty_timer += delta
    if difficulty_timer > DIFFICULTY_INTERVAL:
        difficulty_timer = 0
        speed *= INCREASE_FACTOR
        Cactus.spawn_chance *= INCREASE_FACTOR
        print(Cactus.spawn_chance)

    if keys[pg.K_SPACE]:
        spencer.jump()

    if spencer.on_ground:
        if keys[pg.K_d]:
            spencer.move("right")
        if keys[pg.K_a]:
            spencer.move("left")

    if random.random() < (Cactus.spawn_chance * delta):
        Cactus(all_sprites, cactus_group)

    if not ground_group:
        Ground(all_sprites, ground_group, bottomleft=screen.get_rect().bottomleft)

    if (
        ground_group.sprites()[0].rect.right <= screen.get_rect().right + 20
        and len(ground_group) < 2
    ):
        Ground(all_sprites, ground_group, bottomleft=screen.get_rect().bottomright)

    if (
        ground_group.sprites()[0].rect.right <= screen.get_rect().left
        and len(ground_group) > 1
    ):
        ground_group.sprites()[0].kill()

    if spencer.rect.collideobjects(cactus_group.sprites()):
        thunder_sound.play()
        spencer.kill()
        Explosion(spencer, all_sprites)

        running = False

    if cactus_group:
        cactus = cactus_group.sprites()[0]
        if spencer.rect.center >= cactus.rect.center and not cactus.passed:
            cactus.passed = True
            score.increase(1)

    all_sprites.update(delta=delta, ground_group=ground_group)

    all_sprites.draw(screen)
    pg.display.flip()

pg.time.wait(1000)
pg.quit()
