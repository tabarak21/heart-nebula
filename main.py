
import math
import random
import sys

import numpy as np
import pygame


pygame.init()

# =========================================================
# Window
# =========================================================

WIDTH = 1280
HEIGHT = 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Heart Nebula Composition 3D")

clock = pygame.time.Clock()

BACKGROUND = (2, 1, 5)

# =========================================================
# 3D stars
# =========================================================

STAR_COUNT = 1100
SPACE_X = 17.0
SPACE_Y = 9.5
MIN_Z = 0.75
MAX_Z = 32.0
FOCAL_LENGTH = 520.0

BASE_FORWARD_SPEED = 0.020
ZOOM_STEP = 0.060
ZOOM_FRICTION = 0.925

MAX_FORWARD_IMPULSE = 0.34
MAX_BACKWARD_IMPULSE = -0.16

STAR_COLORS = [
    (255, 255, 255),
    (238, 241, 255),
    (255, 228, 235),
    (255, 200, 218),
    (210, 220, 255),
]


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


# =========================================================
# Noise
# =========================================================

def value_noise(width, height, cell_size, seed):
    rng = np.random.default_rng(seed)

    grid_w = max(2, width // cell_size + 3)
    grid_h = max(2, height // cell_size + 3)

    small_values = rng.random((grid_w, grid_h)).astype(np.float32)

    small_surface = pygame.Surface((grid_w, grid_h))
    small_rgb = np.repeat(
        (small_values[:, :, None] * 255).astype(np.uint8),
        3,
        axis=2,
    )

    pygame.surfarray.blit_array(small_surface, small_rgb)

    smooth = pygame.transform.smoothscale(
        small_surface,
        (width, height),
    )

    return (
        pygame.surfarray.array3d(smooth)[:, :, 0]
        .astype(np.float32)
        / 255.0
    )


def fractal_noise(width, height, seed):
    result = np.zeros((width, height), dtype=np.float32)

    amplitudes = [1.0, 0.56, 0.31, 0.18, 0.10, 0.06]
    cell_sizes = [260, 150, 84, 44, 24, 12]

    total = 0.0

    for index, (amplitude, cell_size) in enumerate(
        zip(amplitudes, cell_sizes)
    ):
        result += (
            value_noise(
                width,
                height,
                cell_size,
                seed + index * 137,
            )
            * amplitude
        )

        total += amplitude

    result /= total

    return np.clip(result, 0.0, 1.0)


# =========================================================
# Heart-nebula composition mask
# =========================================================

def soft_ellipse_field(
    width,
    height,
    center_x,
    center_y,
    radius_x,
    radius_y,
    rotation_degrees,
):
    x = np.arange(width, dtype=np.float32)[:, None]
    y = np.arange(height, dtype=np.float32)[None, :]

    dx = x - center_x
    dy = y - center_y

    angle = math.radians(rotation_degrees)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    rx = dx * cos_a + dy * sin_a
    ry = -dx * sin_a + dy * cos_a

    distance = (
        (rx / radius_x) ** 2
        + (ry / radius_y) ** 2
    )

    return np.exp(-distance * 2.15)


def create_composition_mask(width, height):
    """
    Creates two irregular gas lobes and a lower tail.
    The result only suggests a heart; it does not draw a heart outline.
    """
    left_lobe = soft_ellipse_field(
        width,
        height,
        width * 0.40,
        height * 0.43,
        width * 0.25,
        height * 0.27,
        -18,
    )

    right_lobe = soft_ellipse_field(
        width,
        height,
        width * 0.61,
        height * 0.40,
        width * 0.22,
        height * 0.31,
        17,
    )

    lower_bridge = soft_ellipse_field(
        width,
        height,
        width * 0.52,
        height * 0.61,
        width * 0.30,
        height * 0.18,
        4,
    )

    lower_tail = soft_ellipse_field(
        width,
        height,
        width * 0.67,
        height * 0.73,
        width * 0.22,
        height * 0.12,
        18,
    )

    mask = (
        left_lobe * 0.95
        + right_lobe * 1.0
        + lower_bridge * 0.70
        + lower_tail * 0.48
    )

    # Central dark cavity that creates the heart-like suggestion.
    cavity = soft_ellipse_field(
        width,
        height,
        width * 0.51,
        height * 0.48,
        width * 0.13,
        height * 0.20,
        0,
    )

    mask -= cavity * 0.68

    return np.clip(mask, 0.0, 1.0)


# =========================================================
# Nebula generation
# =========================================================

def create_heart_nebula_composition():
    width = WIDTH + 360
    height = HEIGHT + 260

    composition = create_composition_mask(width, height)

    gas_noise = fractal_noise(width, height, 11)
    edge_noise = fractal_noise(width, height, 43)
    filament_noise = fractal_noise(width, height, 97)
    dust_noise = fractal_noise(width, height, 211)

    # Irregular gas distribution
    gas = np.clip(
        composition
        * (
            0.20
            + np.clip((gas_noise - 0.28) * 1.65, 0.0, 1.0)
        ),
        0.0,
        1.0,
    )

    # Bright, thin emission filaments
    filaments = np.clip(
        (filament_noise - 0.58) * 5.2,
        0.0,
        1.0,
    ) * gas

    # Broken perimeter detail
    edge_detail = np.clip(
        (edge_noise - 0.44) * 2.3,
        0.0,
        1.0,
    ) * composition

    # Dark dust inside the cloud
    dust = np.clip(
        (dust_noise - 0.50) * 3.8,
        0.0,
        1.0,
    ) * composition

    output = pygame.Surface((width, height), pygame.SRCALPHA)

    rgb = pygame.surfarray.pixels3d(output)
    alpha = pygame.surfarray.pixels_alpha(output)

    # Deep crimson base
    red = 28 + gas * 185
    green = 2 + gas * 25
    blue = 10 + gas * 35

    # Red-pink outer detail
    red += edge_detail * 55
    green += edge_detail * 16
    blue += edge_detail * 30

    # Rose emission filaments
    red += filaments * 85
    green += filaments * 70
    blue += filaments * 92

    # Sparse pale hot gas
    hot = np.clip(
        (filament_noise - 0.74) * 7.5,
        0.0,
        1.0,
    ) * composition

    red += hot * 65
    green += hot * 105
    blue += hot * 125

    # Dust darkening
    red *= 1.0 - dust * 0.80
    green *= 1.0 - dust * 0.88
    blue *= 1.0 - dust * 0.84

    rgb[:, :, 0] = np.clip(red, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(green, 0, 255).astype(np.uint8)
    rgb[:, :, 2] = np.clip(blue, 0, 255).astype(np.uint8)

    alpha_values = (
        gas * 185
        + filaments * 55
        + edge_detail * 22
        - dust * 42
    )

    alpha[:, :] = np.clip(alpha_values, 0, 225).astype(np.uint8)

    del rgb
    del alpha

    # Embedded stars
    embedded = pygame.Surface((width, height), pygame.SRCALPHA)
    rng = random.Random(88)

    for _ in range(7600):
        x = rng.randrange(width)
        y = rng.randrange(height)

        density = float(composition[x, y])

        if rng.random() > density * 0.78:
            continue

        color = rng.choice([
            (255, 236, 242, rng.randint(30, 115)),
            (255, 205, 220, rng.randint(25, 95)),
            (222, 230, 255, rng.randint(20, 80)),
        ])

        radius = 1 if rng.random() < 0.987 else 2

        pygame.draw.circle(
            embedded,
            color,
            (x, y),
            radius,
        )

    output.blit(
        embedded,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    output.set_alpha(220)

    return output



def create_background_dust():
    """
    Very subtle large-scale dark cosmic dust.
    It adds depth without becoming a visible coloured cloud.
    """
    width = WIDTH + 260
    height = HEIGHT + 200

    layer = pygame.Surface((width, height), pygame.SRCALPHA)

    noise_a = fractal_noise(width, height, 307)
    noise_b = fractal_noise(width, height, 401)

    density = np.clip(
        (noise_a * 0.68 + noise_b * 0.32 - 0.43) * 1.75,
        0.0,
        1.0,
    )

    rgb = pygame.surfarray.pixels3d(layer)
    alpha = pygame.surfarray.pixels_alpha(layer)

    # Nearly black, slightly warm/red-violet dust.
    rgb[:, :, 0] = np.clip(6 + density * 12, 0, 255).astype(np.uint8)
    rgb[:, :, 1] = np.clip(3 + density * 5, 0, 255).astype(np.uint8)
    rgb[:, :, 2] = np.clip(9 + density * 15, 0, 255).astype(np.uint8)

    alpha[:, :] = np.clip(density * 52, 0, 58).astype(np.uint8)

    del rgb
    del alpha

    return layer


# =========================================================
# Foreground 3D stars
# =========================================================


class Ripple:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        self.radius = 8.0
        self.speed = 4.1
        self.alpha = 145.0
        self.max_radius = 230.0
        self.dead = False

    def update(self):
        self.radius += self.speed
        self.alpha -= 2.7

        if (
            self.alpha <= 0
            or self.radius >= self.max_radius
        ):
            self.dead = True

    def influence(self, x, y, layer):
        dx = x - self.x
        dy = y - self.y

        distance = math.hypot(dx, dy)

        if distance <= 0:
            return 0.0, 0.0

        wave_width = 26.0
        distance_from_wave = abs(distance - self.radius)

        if distance_from_wave > wave_width:
            return 0.0, 0.0

        strength = 1.0 - distance_from_wave / wave_width

        if layer == "far":
            layer_force = 0.55
        elif layer == "mid":
            layer_force = 1.0
        else:
            layer_force = 1.55

        force = strength * 2.8 * layer_force

        return (
            dx / distance * force,
            dy / distance * force,
        )

    def draw(self, surface):
        if self.dead:
            return

        size = int(self.radius * 2 + 40)

        layer = pygame.Surface(
            (size, size),
            pygame.SRCALPHA,
        )

        center = size // 2
        alpha = max(0, int(self.alpha))

        pygame.draw.ellipse(
            layer,
            (205, 225, 255, alpha),
            (
                center - self.radius,
                center - self.radius * 0.72,
                self.radius * 2,
                self.radius * 1.44,
            ),
            1,
        )

        pygame.draw.ellipse(
            layer,
            (255, 255, 255, int(alpha * 0.22)),
            (
                center - self.radius - 5,
                center - self.radius * 0.72 - 4,
                self.radius * 2 + 10,
                self.radius * 1.44 + 8,
            ),
            1,
        )

        surface.blit(
            layer,
            (
                int(self.x - center),
                int(self.y - center),
            ),
        )


class Star:
    def __init__(self):
        self.reset()

    def reset(self, z=None):
        self.x = random.uniform(-SPACE_X, SPACE_X)
        self.y = random.uniform(-SPACE_Y, SPACE_Y)

        self.z = (
            random.uniform(MIN_Z, MAX_Z)
            if z is None
            else z
        )

        chance = random.random()

        if chance < 0.965:
            self.base_size = random.uniform(0.22, 0.46)
        elif chance < 0.997:
            self.base_size = random.uniform(0.48, 0.74)
        else:
            self.base_size = random.uniform(0.76, 0.92)

        self.color = random.choice(STAR_COLORS)

        brightness_roll = random.random()

        if brightness_roll < 0.80:
            self.base_brightness = random.randint(55, 125)
            self.twinkle_amount = random.randint(2, 10)
        elif brightness_roll < 0.98:
            self.base_brightness = random.randint(126, 190)
            self.twinkle_amount = random.randint(5, 16)
        else:
            self.base_brightness = random.randint(205, 245)
            self.twinkle_amount = random.randint(8, 22)

        self.twinkle_speed = random.uniform(0.16, 0.72)
        self.phase = random.uniform(0, math.tau)
        # Depth grouping:
        # far stars move with the nebula,
        # middle stars move moderately,
        # near stars create foreground parallax.
        depth_roll = random.random()

        if depth_roll < 0.48:
            self.layer = "far"
            self.parallax = 0.18
        elif depth_roll < 0.87:
            self.layer = "mid"
            self.parallax = 0.52
        else:
            self.layer = "near"
            self.parallax = 1.0

        self.ripple_offset_x = 0.0
        self.ripple_offset_y = 0.0

        self.previous_screen_position = None

    def move_in_depth(self, speed):
        self.z -= speed

        if self.z < MIN_Z:
            self.reset(MAX_Z)
        elif self.z > MAX_Z:
            self.reset(MIN_Z + 0.45)

    def apply_ripples(self, ripples, screen_x, screen_y):
        force_x = 0.0
        force_y = 0.0

        for ripple in ripples:
            fx, fy = ripple.influence(
                screen_x,
                screen_y,
                self.layer,
            )

            force_x += fx
            force_y += fy

        self.ripple_offset_x += force_x
        self.ripple_offset_y += force_y

        self.ripple_offset_x *= 0.88
        self.ripple_offset_y *= 0.88

        return (
            self.ripple_offset_x,
            self.ripple_offset_y,
        )

    def project(self, camera_x, camera_y, time_seconds, ripples):
        adjusted_x = (
            self.x
            - camera_x
            * self.parallax
            * (self.z / MAX_Z)
        )

        adjusted_y = (
            self.y
            - camera_y
            * self.parallax
            * (self.z / MAX_Z)
        )

        if self.z <= 0.1:
            return None

        scale = FOCAL_LENGTH / self.z

        screen_x = WIDTH / 2 + adjusted_x * scale
        screen_y = HEIGHT / 2 + adjusted_y * scale

        ripple_x, ripple_y = self.apply_ripples(
            ripples,
            screen_x,
            screen_y,
        )

        screen_x += ripple_x
        screen_y += ripple_y

        if (
            screen_x < -40
            or screen_x > WIDTH + 40
            or screen_y < -40
            or screen_y > HEIGHT + 40
        ):
            return None

        depth = 1.0 - self.z / MAX_Z

        twinkle = math.sin(
            time_seconds * self.twinkle_speed + self.phase
        )

        brightness = int(
            self.base_brightness + twinkle * self.twinkle_amount
        )

        if self.layer == "far":
            brightness *= 0.72
        elif self.layer == "near":
            brightness *= 1.08

        brightness = clamp(int(brightness), 42, 255)

        color = tuple(
            min(255, int(channel * brightness / 255))
            for channel in self.color
        )

        radius = self.base_size * scale * 0.018

        if self.layer == "far":
            radius *= 0.72
        elif self.layer == "near":
            radius *= 1.16

        radius = clamp(radius, 0.28, 1.65)

        return (
            screen_x,
            screen_y,
            radius,
            color,
            depth,
        )


def draw_star(
    star_surface,
    bloom_source,
    star,
    projected,
    speed,
):
    x, y, radius, color, depth = projected

    px = int(x)
    py = int(y)

    if (
        star.previous_screen_position is not None
        and abs(speed) > 0.11
    ):
        previous_x, previous_y = star.previous_screen_position

        pygame.draw.line(
            star_surface,
            (
                int(color[0] * 0.15),
                int(color[1] * 0.15),
                int(color[2] * 0.15),
            ),
            (int(previous_x), int(previous_y)),
            (px, py),
            1,
        )

    star.previous_screen_position = (x, y)

    if not (0 <= px < WIDTH and 0 <= py < HEIGHT):
        return

    if radius < 0.72:
        star_surface.set_at((px, py), color)
    else:
        pygame.draw.circle(
            star_surface,
            color,
            (px, py),
            1,
        )

    if star.base_brightness >= 145:
        if star.layer == "far":
            glow_radius = 1
            glow_alpha = 22
        elif star.layer == "mid":
            glow_radius = 2
            glow_alpha = 34
        else:
            glow_radius = 2
            glow_alpha = 48

        glow_alpha += int(depth * 18)

        pygame.draw.circle(
            bloom_source,
            (
                color[0],
                color[1],
                color[2],
                min(90, glow_alpha),
            ),
            (px, py),
            glow_radius,
        )

    if star.base_brightness > 205 and radius > 0.92:
        pygame.draw.circle(
            bloom_source,
            (
                color[0],
                color[1],
                color[2],
                72,
            ),
            (px, py),
            3,
        )

    if (
        star.base_brightness > 232
        and radius > 1.15
        and star.layer == "near"
    ):
        flare = pygame.Surface((14, 14), pygame.SRCALPHA)
        c = 7

        pygame.draw.line(
            flare,
            (*color, 46),
            (c - 3, c),
            (c + 3, c),
            1,
        )

        pygame.draw.line(
            flare,
            (*color, 46),
            (c, c - 3),
            (c, c + 3),
            1,
        )

        star_surface.blit(
            flare,
            (px - c, py - c),
        )


# =========================================================
# Scene
# =========================================================

random.seed(7)

print("Generating realistic heart-nebula composition...")

heart_nebula = create_heart_nebula_composition()
background_dust = create_background_dust()

print("Nebula ready.")

stars = [Star() for _ in range(STAR_COUNT)]

zoom_impulse = 0.0

camera_x = 0.0
camera_y = 0.0
target_camera_x = 0.0
target_camera_y = 0.0

ripples = []

nebula_ripple_x = 0.0
nebula_ripple_y = 0.0

pygame.mouse.set_visible(False)

far_star_surface = pygame.Surface(
    (WIDTH, HEIGHT),
    pygame.SRCALPHA,
)

mid_star_surface = pygame.Surface(
    (WIDTH, HEIGHT),
    pygame.SRCALPHA,
)

near_star_surface = pygame.Surface(
    (WIDTH, HEIGHT),
    pygame.SRCALPHA,
)

bloom_source = pygame.Surface(
    (WIDTH, HEIGHT),
    pygame.SRCALPHA,
)

running = True

while running:
    time_seconds = pygame.time.get_ticks() / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                zoom_impulse = 0.0

        elif event.type == pygame.MOUSEWHEEL:
            zoom_impulse += event.y * ZOOM_STEP

            zoom_impulse = clamp(
                zoom_impulse,
                MAX_BACKWARD_IMPULSE,
                MAX_FORWARD_IMPULSE,
            )

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                click_x, click_y = pygame.mouse.get_pos()
                ripples.append(Ripple(click_x, click_y))

    camera_speed = BASE_FORWARD_SPEED + zoom_impulse

    zoom_impulse *= ZOOM_FRICTION

    if abs(zoom_impulse) < 0.0005:
        zoom_impulse = 0.0

    mouse_x, mouse_y = pygame.mouse.get_pos()

    normalized_x = (
        mouse_x - WIDTH / 2
    ) / (WIDTH / 2)

    normalized_y = (
        mouse_y - HEIGHT / 2
    ) / (HEIGHT / 2)

    target_camera_x = normalized_x * 1.35
    target_camera_y = normalized_y * 0.78

    camera_x += (
        target_camera_x - camera_x
    ) * 0.045

    camera_y += (
        target_camera_y - camera_y
    ) * 0.045

    for ripple in ripples:
        ripple.update()

    ripples = [
        ripple
        for ripple in ripples
        if not ripple.dead
    ]

    screen.fill(BACKGROUND)

    dust_x = int(-130 - camera_x * 2.8)
    dust_y = int(-100 - camera_y * 1.8)

    screen.blit(
        background_dust,
        (dust_x, dust_y),
    )

    # Nebula moves slowly because it is far away.
    # The nebula and far stars now share nearly the same depth motion.
    nebula_x = int(-180 - camera_x * 7.8)
    nebula_y = int(-130 - camera_y * 4.8)

    target_nebula_ripple_x = 0.0
    target_nebula_ripple_y = 0.0

    for ripple in ripples:
        dx = WIDTH / 2 - ripple.x
        dy = HEIGHT / 2 - ripple.y
        distance = math.hypot(dx, dy)

        if distance > 0:
            proximity = max(
                0.0,
                1.0 - distance / 520.0,
            )

            pulse = max(
                0.0,
                1.0 - ripple.radius / ripple.max_radius,
            )

            target_nebula_ripple_x += (
                dx / distance
                * proximity
                * pulse
                * 2.4
            )

            target_nebula_ripple_y += (
                dy / distance
                * proximity
                * pulse
                * 1.7
            )

    nebula_ripple_x += (
        target_nebula_ripple_x
        - nebula_ripple_x
    ) * 0.12

    nebula_ripple_y += (
        target_nebula_ripple_y
        - nebula_ripple_y
    ) * 0.12

    screen.blit(
        heart_nebula,
        (
            nebula_x + int(nebula_ripple_x),
            nebula_y + int(nebula_ripple_y),
        ),
    )

    projected_stars = []

    for star in stars:
        star.move_in_depth(camera_speed)

        projected = star.project(
            camera_x,
            camera_y,
            time_seconds,
            ripples,
        )

        if projected is not None:
            projected_stars.append(
                (star.z, star, projected)
            )

    projected_stars.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    far_star_surface.fill((0, 0, 0, 0))
    mid_star_surface.fill((0, 0, 0, 0))
    near_star_surface.fill((0, 0, 0, 0))
    bloom_source.fill((0, 0, 0, 0))

    for _, star, projected in projected_stars:
        if star.layer == "far":
            target_surface = far_star_surface
        elif star.layer == "mid":
            target_surface = mid_star_surface
        else:
            target_surface = near_star_surface

        draw_star(
            target_surface,
            bloom_source,
            star,
            projected,
            camera_speed,
        )

    # Far stars are blended close to the nebula, so they feel embedded in it.
    screen.blit(
        far_star_surface,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    # Mid-space stars sit between the nebula and the foreground.
    screen.blit(
        mid_star_surface,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    # True soft bloom for only the strongest stars.
    bloom_small = pygame.transform.smoothscale(
        bloom_source,
        (WIDTH // 10, HEIGHT // 10),
    )

    bloom_soft = pygame.transform.smoothscale(
        bloom_small,
        (WIDTH, HEIGHT),
    )

    bloom_soft.set_alpha(185)

    screen.blit(
        bloom_soft,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    # Gravitational ripples are drawn softly inside the scene.
    for ripple in ripples:
        ripple.draw(screen)

    # Near stars are rendered last to create foreground depth.
    screen.blit(
        near_star_surface,
        (0, 0),
        special_flags=pygame.BLEND_RGBA_ADD,
    )

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
