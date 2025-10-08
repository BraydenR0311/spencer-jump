import pygame as pg
from pathlib import Path
import random
import math

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


def load_image(name, scale=1.0):
    fullname = IMAGE_DIR / name
    image = pg.image.load(fullname).convert_alpha()

    image = pg.transform.scale_by(image, scale)

    return image


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

    JUMP_SOUNDS = {fp.stem: load_sound(fp.name) for fp in SOUND_DIR.glob("jump*")}
    flint_sound = load_sound("flint.opus")

    IMAGES = {
        fp.stem: load_image(fp.name, scale=0.2) for fp in IMAGE_DIR.glob("spence*.png")
    }

    def __init__(self, dest, *groups):
        super().__init__(*groups)
        self.image = Spencer.IMAGES["spence1"]
        self.orig_image = self.image

        self.rotate_factor = 10
        self.image = pg.transform.rotate(self.orig_image, self.rotate_factor)
        self.rect = self.image.get_rect()
        self.rect.inflate_ip(-30, -30)
        self.rect.midbottom = dest

        self.velocity = pg.Vector2(0, 0)
        self.position = pg.Vector2(self.rect.midbottom)

        self.on_ground = True
        self.fast_falling = False

        self.air_time = 0
        self.flip_timer = 0

    def update(self, delta=None, **kwargs):
        if self.on_ground:
            self.fast_falling = False
            if self.flip_timer > Spencer.FLIP_SECS:
                self.flip_timer = 0
                self.rotate_factor = -self.rotate_factor
                self.image = pg.transform.rotate(self.orig_image, self.rotate_factor)
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

        self.velocity.x *= Spencer.FRICTION
        self.position += self.velocity * delta
        self.rect.midbottom = self.position
        if self.rect.left <= screen.get_rect().left:
            self.velocity.x = 0
        self.rect.clamp_ip(screen.get_rect())

    def jump(self):
        emotes = (self.legs_together, self.hot_hairy, self.sneeze, self.nether)
        if self.on_ground and random.random() < 0.3:
            random.choice(emotes)()

        if self.air_time <= self.MAX_AIR_TIME:
            self.velocity.y = Spencer.JUMP_VELOCITY
            self.on_ground = False

    def legs_together(self):
        self.image = self.IMAGES["spence2"]

    def hot_hairy(self):
        self.JUMP_SOUNDS["jump1"].play()

    def sneeze(self):
        self.JUMP_SOUNDS["jump2"].play()

    def nether(self):
        self.JUMP_SOUNDS["jump3"].play()

    def move(self, direction):
        if direction == "right":
            self.velocity.x += Spencer.ACCEL * delta
        if direction == "left":
            self.velocity.x -= Spencer.ACCEL * delta
        if direction == "down":
            if not self.on_ground:
                self.velocity.y += 10000 * delta
                if not self.fast_falling:
                    self.fast_falling = True
                    FastFall(self, all_sprites)

    def emote(self):
        emotes = (self.peace, self.pika)
        random.choice(emotes)()

    def peace(self):
        Peace(self, all_sprites)
        ChadFace(self, all_sprites)

    def pika(self):
        PikaFace(self, all_sprites)
        Spencer.flint_sound.play()

    def animate(self):
        pass


class Peace(pg.sprite.Sprite):
    IMAGE = load_image("peace.png", scale=0.06)
    LIFETIME = 0.5

    def __init__(self, target, *groups):
        super().__init__(*groups)
        self.image = pg.transform.flip(Peace.IMAGE, flip_x=True, flip_y=False)
        self.image = pg.transform.rotate(self.image, -20)
        self.target = target
        self.rect = self.image.get_rect(midleft=self.target.rect.midright)
        self.age = 0
        peace_sound.play()

    def update(self, delta, *args, **kwargs):
        self.rect.midleft = self.target.rect.midright
        self.rect.move_ip(-30, -30)

        self.age += delta
        if self.age > Peace.LIFETIME:
            self.kill()


class ChadFace(pg.sprite.Sprite):
    IMAGE = load_image("chadface.PNG", scale=0.07)
    LIFETIME = 0.5

    def __init__(self, target, *groups):
        super().__init__(*groups)
        self.image = pg.transform.rotate(ChadFace.IMAGE, 15)
        self.target = target
        self.rect = self.image.get_rect(midtop=self.target.rect.midtop)
        self.age = 0

    def update(self, delta, *args, **kwargs):
        self.rect.midtop = self.target.rect.midtop
        self.rect.move_ip(0, -10)

        self.age += delta
        if self.age > ChadFace.LIFETIME:
            self.kill()


class PikaFace(pg.sprite.Sprite):
    IMAGE = load_image("pika.png", scale=0.07)
    LIFETIME = 0.5

    def __init__(self, target, *groups):
        super().__init__(*groups)
        self.image = pg.transform.rotate(PikaFace.IMAGE, 15)
        self.target = target
        self.rect = self.image.get_rect(midtop=self.target.rect.midtop)
        self.age = 0

    def update(self, delta, *args, **kwargs):
        self.rect.midtop = self.target.rect.midtop
        self.rect.move_ip(30, -10)

        self.age += delta
        if self.age > PikaFace.LIFETIME:
            self.kill()


class FastFall(pg.sprite.Sprite):
    IMAGE = load_image("fastfall.png", scale=0.04)
    LIFETIME = 0.07

    def __init__(self, target, *groups):
        super().__init__(*groups)
        self.image = pg.transform.rotate(FastFall.IMAGE, 15)
        self.target = target
        self.rect = self.image.get_rect(bottomright=self.target.rect.topleft)
        self.age = 0

    def update(self, delta, *args, **kwargs):
        self.rect.bottomright = self.target.rect.topleft
        self.rect.move_ip(40, 0)

        self.age += delta
        if self.age > FastFall.LIFETIME:
            self.kill()


class Ground(pg.sprite.Sprite):
    IMAGE = load_image("tile.png", scale=1)

    def __init__(self, *groups, **kwargs):
        super().__init__(*groups)
        self.image = Ground.IMAGE
        self.rect = self.image.get_rect(**kwargs)

    def update(self, delta=None, **kwargs):
        if delta is not None:
            distance = speed * delta
            self.rect.move_ip(distance, 0)


class Cactus(pg.sprite.Sprite):
    BEFORE_ALLOWABLE_SPAWN = 100
    AFTER_ALLOWABLE_SPAWN = 500
    MAX_DISTANCE_SINCE_SPAWN = 1500
    IMAGES = [load_image(fp.name, scale=0.2) for fp in IMAGE_DIR.glob("cactus*.png")]
    spawn_chance = 0.0
    distance_since_spawn = 0.0

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = random.choice(Cactus.IMAGES)
        self.rect = self.image.get_rect()
        self.rect.left = screen.get_rect().right
        self.rect.inflate_ip(-10, -10)
        Cactus.distance_since_spawn = 0
        self.passed = False

    def update(self, delta=None, **kwargs):
        if delta is not None:
            self.rect.move_ip(speed * delta, 0)
            self.rect.bottom = ground_group.sprites()[0].rect.top

        if self.rect.right <= screen.get_rect().left:
            self.kill()


class Explosion(pg.sprite.Sprite):
    IMAGE = load_image("explosion.png", scale=0.2)

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


LAO_CLICKED = pg.event.custom_type()
lao_event = pg.event.Event(LAO_CLICKED)


class Lao(pg.sprite.Sprite):
    IMAGE = load_image("lao.png", scale=0.1)

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = Lao.IMAGE
        self.rect = self.image.get_rect()
        self.position = pg.Vector2(screen.get_rect().right, 50)
        self.rect.topleft = self.position
        self.sin = 0

    def update(self, delta, *args, **kwargs):
        self.sin += delta
        if delta is not None:
            distance = speed * delta
            self.rect.move_ip(distance, math.sin(self.sin * 10) * 5)

        pos = pg.mouse.get_pos()
        click, _, _ = pg.mouse.get_pressed()
        if self.rect.collidepoint(pos) and click:
            pg.event.post(lao_event)
            self.kill()


all_sprites = pg.sprite.Group()
ground_group = pg.sprite.Group()
cactus_group = pg.sprite.Group()

background = pg.Surface(screen.get_size()).convert()
background.fill((170, 238, 187))

running = True

spencer = Spencer((75, 400), all_sprites)

thunder_sound = load_sound("thunder.mp3")
peace_sound = load_sound("peace.mp3")
freddy_sound = load_sound("freddy.opus")
coin_sound = load_sound("coin.mp3")
speed = INITIAL_SPEED


difficulty_timer = 0
score = Score(all_sprites)


def play_song():
    song = random.choice(list(SOUND_DIR.glob("song*")))
    pg.mixer.music.load(song)
    pg.mixer.music.set_volume(0.7)
    pg.mixer.music.play(-1)


def game_over():
    def freddy():
        class GoodBye(pg.sprite.Sprite):
            def __init__(self, *groups):
                super().__init__(*groups)
                self.image = load_image("babySpence.JPG")
                self.image = pg.transform.scale(self.image, screen.get_size())
                self.rect = self.image.get_rect()

        GoodBye(all_sprites)
        freddy_sound.play()

    def explosion():
        Explosion(spencer, all_sprites)
        thunder_sound.play()

    choices = (explosion, freddy)
    weights = (0.9, 0.1)
    global speed
    spencer.kill()
    pg.mixer.music.stop()
    speed = 0
    random.choices(choices, weights=weights, k=1)[0]()


def move_ground():
    if not ground_group:
        Ground(all_sprites, ground_group, bottomleft=screen.get_rect().bottomleft)
    if ground_group.sprites()[-1].rect.right <= screen.get_rect().right + 20:
        Ground(
            all_sprites,
            ground_group,
            bottomleft=ground_group.sprites()[-1].rect.bottomright,
        )
    if (
        ground_group.sprites()[0].rect.right <= screen.get_rect().left
        and len(ground_group) > 1
    ):
        ground_group.sprites()[0].kill()


play_song()
last_score = 0
while running:
    delta = clock.tick(FPS) / 1000
    screen.blit(background)

    for event in pg.event.get():
        if event.type == pg.QUIT or (
            event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
        ):
            running = False
        if event.type == LAO_CLICKED:
            coin_sound.play()
            score.increase(2)

    keys = pg.key.get_pressed()

    if keys[pg.K_SPACE]:
        spencer.jump()

    if spencer.on_ground:
        if keys[pg.K_d]:
            spencer.move("right")
        if keys[pg.K_a]:
            spencer.move("left")
    if keys[pg.K_s]:
        spencer.move("down")

    move_ground()

    Cactus.distance_since_spawn += speed * delta
    # TODO: change to time not distance?
    if -Cactus.distance_since_spawn > Cactus.MAX_DISTANCE_SINCE_SPAWN:
        Cactus(all_sprites, cactus_group)
    if random.random() < (Cactus.spawn_chance * delta) and not (
        Cactus.BEFORE_ALLOWABLE_SPAWN
        < -Cactus.distance_since_spawn
        < Cactus.AFTER_ALLOWABLE_SPAWN
    ):
        Cactus(all_sprites, cactus_group)

    if spencer.rect.collideobjects(cactus_group.sprites()) and spencer.alive():
        game_over()

    if cactus_group:
        cactus = cactus_group.sprites()[0]
        if spencer.rect.left >= cactus.rect.centerx and not cactus.passed:
            cactus.passed = True
            score.increase(1)
            if random.random() < 0.3:
                spencer.emote()
            if score.score - last_score >= 3:
                print("inc")
                last_score = score.score
                speed *= DIFFICULTY_MULTIPLIER
                Cactus.spawn_chance *= DIFFICULTY_MULTIPLIER

    if random.random() < 0.10 * delta:
        Lao(all_sprites)

    all_sprites.update(delta=delta)

    all_sprites.draw(screen)
    pg.display.flip()


pg.quit()
