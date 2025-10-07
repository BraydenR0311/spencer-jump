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
DIFFICULTY_MULTIPLIER = 1.1
DIFFICULTY_INTERVAL = 3


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
    FLIP_SECS = 0.3

    JUMP_SOUNDS = [load_sound("") for sound in ()]

    def __init__(self, dest, *groups):
        super().__init__(*groups)
        self.image, _ = load_image("spence.png", scale=0.2)
        self.orig_image = self.image

        self.image = pg.transform.rotate(self.image, 10)
        self.rect = self.image.get_rect()
        self.rect.midbottom = dest

        self.velocity = pg.Vector2(0, 0)
        self.position = pg.Vector2(self.rect.midbottom)
        self.on_ground = True
        self.air_time = 0

        self.flip_timer = 0

    def update(self, delta=None, **kwargs):
        if self.on_ground:
            if self.flip_timer > Spencer.FLIP_SECS:
                self.flip_timer = 0
                self.image = pg.transform.flip(self.image, flip_x=True, flip_y=False)
        if delta is not None:
            self.flip_timer += delta
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

    def emote(self):
        emotes = (self.peace,)
        random.choice(emotes)()

    def peace(self):
        Peace(self, all_sprites)


class Peace(pg.sprite.Sprite):
    IMAGE, _ = load_image("peace.png", scale=0.06)
    LIFETIME = 0.5

    def __init__(self, target, *groups):
        super().__init__(*groups)
        self.image = pg.transform.rotate(Peace.IMAGE, 15)
        self.target = target
        self.rect = self.image.get_rect(midright=self.target.rect.midleft)
        self.age = 0
        peace_sound.play()

    def update(self, delta, *args, **kwargs):
        self.rect.midright = self.target.rect.midleft
        self.rect.x += 60
        self.rect.y -= 30
        self.age += delta
        if self.age > Peace.LIFETIME:
            self.kill()


class Ground(pg.sprite.Sprite):
    IMAGE, _ = load_image("ground.png", scale=0.2)

    distance_since_cactus = 0

    def __init__(self, *groups, **kwargs):
        super().__init__(*groups)
        self.image = Ground.IMAGE
        self.rect = self.image.get_rect(**kwargs)

    def update(self, delta=None, **kwargs):
        if delta is not None:
            distance = speed * delta
            Ground.distance_since_cactus += distance
            self.rect.move_ip(distance, 0)


class Cactus(pg.sprite.Sprite):
    BEFORE_ALLOWABLE_SPAWN = 100
    AFTER_ALLOWABLE_SPAWN = 500
    IMAGE_RECT_TUPLES = [
        load_image(fp.name, scale=0.2) for fp in IMAGE_DIR.glob("cactus*.png")
    ]
    spawn_chance = 0.25

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image, _ = random.choice(Cactus.IMAGE_RECT_TUPLES)
        self.rect = self.image.get_rect()
        self.rect.left = screen.get_rect().right
        Ground.distance_since_cactus = 0
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
peace_sound = load_sound("peace.mp3")
speed = INITIAL_SPEED


difficulty_timer = 0
score = Score(all_sprites)


def play_song():
    song = random.choice(list(SOUND_DIR.glob("song*")))
    pg.mixer.music.load(song)
    pg.mixer.music.set_volume(0.7)
    pg.mixer.music.play(-1)


play_song()

while running:
    delta = clock.tick(FPS) / 1000
    screen.blit(background)

    for event in pg.event.get():
        if event.type == pg.QUIT or (
            event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
        ):
            running = False

    keys = pg.key.get_pressed()

    if keys[pg.K_SPACE]:
        spencer.jump()

    if spencer.on_ground:
        if keys[pg.K_d]:
            spencer.move("right")
        if keys[pg.K_a]:
            spencer.move("left")

    # TODO: change to time not distance?
    if random.random() < (Cactus.spawn_chance * delta) and not (
        Cactus.BEFORE_ALLOWABLE_SPAWN
        < -Ground.distance_since_cactus
        < Cactus.AFTER_ALLOWABLE_SPAWN
    ):
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

    if spencer.rect.collideobjects(cactus_group.sprites()) and spencer.alive():
        thunder_sound.play()
        spencer.kill()
        speed = 0
        Explosion(spencer, all_sprites)

    if cactus_group:
        cactus = cactus_group.sprites()[0]
        if spencer.rect.center >= cactus.rect.center and not cactus.passed:
            cactus.passed = True
            score.increase(1)
            if random.random() < 1.0:
                spencer.emote()
            if not score.score % DIFFICULTY_INTERVAL:
                speed *= DIFFICULTY_MULTIPLIER
                Cactus.spawn_chance *= DIFFICULTY_MULTIPLIER

    all_sprites.update(delta=delta)

    all_sprites.draw(screen)
    pg.display.flip()


pg.quit()
