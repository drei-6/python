# render.txt
"""
type = emulator ; the video of the emulator
type = rectangle, x = 0, y = 0, width = MAX_WIDTH, height = MAX_HEIGHT ; background
"""

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
    CHIP8_STACK_DEPTH = 16
    CHIP8_REGISTER_COUNT = 16
    CHIP8_ENTRY_POINT_ADDRESS = 0x200
    CHIP8_FONTSET_ADDRESS = 0x50

class Button:
    is_down = False
    was_down = False # @NOTE: Updated by the caller

class Mouse:
    x = 0
    y = 0
    left_button = Button()
    middle_button = Button()
    right_button = Button()

class Keyboard:
    pass

class Input:
    mouse = Mouse()
    keyboard = Keyboard()

class GUI:
    pass

class Render:
    video = 0
    input = 0
    font = 0

    def __init__(self, video: pygame.Surface, input: Input, font: pygame.font.Font):
        self.video = video
        self.input = input
        self.font = font

class Chip8:
    memory = [0] * 4096
    video = [0] * (64 * 32)
    pc = 0
    i = 0
    stack = [0] * Global.CHIP8_STACK_DEPTH
    delay_timer = 0
    sound_timer = 0
    register = [0] * Global.CHIP8_REGISTER_COUNT
    opcode = 0

class Emulator:
    fps = 0.0
    is_debugging = False
    chip8 = Chip8()

def log(string: str, *args: tuple):
    print(string % args)

def rectangle_to_pygame_rect(rectangle: Rectangle):
    result = (rectangle.x, rectangle.y, rectangle.width, rectangle.height)
    return result

def rgba_to_pygame_rgba(rgba: RGBA):
    result = (int(rgba.r * 255.0), int(rgba.g * 255.0), int(rgba.b * 255.0), int((1.0 - rgba.a) * 255.0))
    return result

def draw_rectangle(video: pygame.Surface, rectangle: Rectangle, rgba: RGBA):
    rectangle = rectangle_to_pygame_rect(rectangle)
    rgba = rgba_to_pygame_rgba(rgba)
    pygame.draw.rect(video, rgba, rectangle)

def draw_character(video: pygame.Surface, font: pygame.font.Font, c: str, x: int, y: int, is_anti_alising: bool, text_rgba: RGBA, background_rgba: RGBA):
    result = 0

    text_rgba = rgba_to_pygame_rgba(text_rgba)
    background_rgba = rgba_to_pygame_rgba(background_rgba)
    surface_foreground = font.render(c, is_anti_alising, text_rgba)
    foreground_dimension = (surface_foreground.get_width(), surface_foreground.get_height())
    surface_background = pygame.Surface(foreground_dimension)
    surface_background.fill(background_rgba)
    surface_background.set_alpha(background_rgba[3])
    video.blit(surface_background, (x, y))
    video.blit(surface_foreground, (x, y))

    result = surface_background.get_rect().width
    return result

def draw_text(video: pygame.Surface, font: pygame.font.Font, text: str, x: int, y: int, is_anti_alising: bool, text_rgba: RGBA, background_rgba: RGBA):
    for c in text:
        if c == '\n':
            x = 0
            y += font.get_height()
            continue
        x += draw_character(video, font, c, x, y, is_anti_alising, text_rgba, background_rgba)

def draw_button(render: Render, x: int, y: int, text: str):
    draw_rectangle(render.video, Rectangle(x, y, 100, 100), RGBA(1.0, 1.0, 1.0, 0.0))

def draw_menu():
    pass

def draw_menubar():
    pass

def draw_gui(render: Render, gui: GUI):
    draw_button(render, 0, 0, "Hello, world!!!")

def update_gui(video: pygame.Surface, input: Input, font: pygame.font.Font, gui: GUI):
    pass

def emulator_initialize():
    result = Emulator()
    result.fps = Global.CHIP8_VIDEO_REFRESH_RATE

    return result

def chip8_initialize(chip8: Chip8):
    fontset = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,
        0x20, 0x60, 0x20, 0x20, 0x70,
        0xF0, 0x10, 0xF0, 0x80, 0xF0,
        0xF0, 0x10, 0xF0, 0x10, 0xF0,
        0x90, 0x90, 0xF0, 0x10, 0x10,
        0xF0, 0x80, 0xF0, 0x10, 0xF0,
        0xF0, 0x80, 0xF0, 0x90, 0xF0,
        0xF0, 0x10, 0x20, 0x40, 0x40,
        0xF0, 0x90, 0xF0, 0x90, 0xF0,
        0xF0, 0x90, 0xF0, 0x10, 0xF0,
        0xF0, 0x90, 0xF0, 0x90, 0x90,
        0xE0, 0x90, 0xE0, 0x90, 0xE0,
        0xF0, 0x80, 0x80, 0x80, 0xF0,
        0xE0, 0x90, 0x90, 0x90, 0xE0,
        0xF0, 0x80, 0xF0, 0x80, 0xF0,
        0xF0, 0x80, 0xF0, 0x80, 0x80 
    ]

    for i in range(len(fontset)):
        chip8.memory[Global.CHIP8_FONTSET_ADDRESS + i] = fontset[i]

def chip8_load_rom(chip8: Chip8, file_name: str):
    result = False

    file = open(file_name, 'rb')
    buffer = file.read()
    file.close()

    buffer_length = len(buffer)

    if buffer_length > (len(chip8.memory) - Global.CHIP8_ENTRY_POINT_ADDRESS):
        log("ROM size is too big: %u", buffer_length)
        return result

    for i in range(buffer_length):
        chip8.memory[Global.CHIP8_ENTRY_POINT_ADDRESS + i] = buffer[i]

    buffer = []

    return True

def chip8_cycle(chip8: Chip8):
    # Fetch
    # Decode and execute
    # delay timer
    # sound timer
    pass

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

    pygame.display.set_caption("Emulator")    
    emulator = emulator_initialize()
    
    chip8_initialize(emulator.chip8)
    chip8_load_rom(emulator.chip8, "tetris.rom")

    input = Input()
    render = Render(video, input, font)
    gui = GUI()
    is_running = True
    last_counter = time.perf_counter_ns()
    
    while is_running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif (event.type == pygame.KEYDOWN) or (event.type == pygame.KEYUP):
                is_down = event.type == pygame.KEYDOWN
            elif (event.type == pygame.MOUSEBUTTONDOWN) or (event.type == pygame.MOUSEBUTTONUP):
                is_down = event.type == pygame.MOUSEBUTTONDOWN
                mouse = input.mouse

                match event.button:
                    case 1:
                        mouse.left_button.is_down = is_down
                    case 2:
                        mouse.middle_button.is_down = is_down
                    case 3:
                        mouse.right_button.is_down = is_down
                    case _:
                        pass

        if not is_running:
            break

        # Update GUI
        update_gui(video, input, font, gui)
        
        # Draw
        video.fill((0, 0, 0))

        # Draw GUI
        draw_gui(render, gui)

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