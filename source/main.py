import time
import pygame

class Rectangle:
    x = 0
    y = 0
    width = 0
    height = 0

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

class RGBA:
    r = 0.0
    g = 0.0
    b = 0.0
    a = 0.0

    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

class Global:
    CHIP8_VIDEO_REFRESH_RATE = 60.0

class Emulator:
    fps = 0.0

def log(string: str, *args: tuple):
    print(string % args)

def rectangle_to_pygame_rect(rectangle: Rectangle):
    result = (rectangle.x, rectangle.y, rectangle.width, rectangle.height)
    return result

def rgba_to_pygame_rgba(rgba: RGBA):
    result = (int(rgba.r * 255.0), int(rgba.g * 255.0), int(rgba.b * 255.0), int(rgba.a * 255.0))
    return result

def draw_rectangle(video: pygame.Surface, rectangle: Rectangle, rgba: RGBA):
    rectangle = rectangle_to_pygame_rect(rectangle)
    rgba = rgba_to_pygame_rgba(rgba)
    pygame.draw.rect(video, rgba, rectangle)

def draw_character(video: pygame.Surface, font: pygame.font.Font, c: str, x: int, y: int, is_anti_alising: bool, text_rgba: RGBA):
    result = 0

    text_rgba = rgba_to_pygame_rgba(text_rgba)
    surface = font.render(c, is_anti_alising, text_rgba)
    video.blit(surface, (x, y))

    result = surface.get_rect().width
    return result

def draw_text(video: pygame.Surface, font: pygame.font.Font, text: str, x: int, y: int, is_anti_alising: bool, text_rgba: RGBA):
    for c in text:
        if c == '\n':
            x = 0
            y += font.get_height()
            continue
        x += draw_character(video, font, c, x, y, is_anti_alising, text_rgba)

def emulator_initialize():
    result = Emulator()
    result.fps = Global.CHIP8_VIDEO_REFRESH_RATE

    return result

def main():
    result = 1

    module_failed_count = pygame.init()[1]

    if module_failed_count > 0:
        log("pygame.init() failed with %d module(s)", module_failed_count)
        return result
    
    window_width = 1280
    window_height = 720
    video = pygame.display.set_mode((window_width, window_height))

    if video is None:
        log("pygame.display.set_mode() failed")
        pygame.quit()
        return result
    
    font = pygame.font.Font(None, 32)

    if font is None:
        log("pygame.font.Font failed()")
        pygame.quit()
        return result
    
    text = font.render("Hello, world!", True, (0, 0, 255))

    pygame.display.set_caption("Emulator")
    
    emulator = emulator_initialize()
    is_running = True
    last_counter = time.perf_counter_ns()
    
    while is_running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

        if not is_running:
            break
        
        # Draw
        video.fill((0, 0, 0))
        draw_rectangle(video, Rectangle(0, 0, 100, 100), RGBA(1.0, 0.0, 0.0, 0.0))
        draw_text(video, font, "Hello, world!\n  Hello, world!\n    Hello, world!", 0, 0, True, RGBA(1.0, 1.0, 1.0, 0.0))

        # Timer
        work_counter = time.perf_counter_ns()
        while work_counter < (1.0 / emulator.fps):
            work_counter = time.perf_counter_ns()
        end_counter = time.perf_counter_ns()

        # Swap buffers/presentation
        pygame.display.flip()

        last_counter = end_counter

    pygame.quit()

    return 0

if __name__ == "__main__":
    exit(main())