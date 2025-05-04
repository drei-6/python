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
    CHIP8_SPRITE_WIDTH = 8
    CHIP8_VIDEO_WIDTH = 64
    CHIP8_VIDEO_HEIGHT = 32
    CHIP8_MEMORY_SIZE = 4096

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
    memory = [0] * Global.CHIP8_MEMORY_SIZE
    video = [0] * (Global.CHIP8_VIDEO_WIDTH * Global.CHIP8_VIDEO_HEIGHT)
    pc = 0
    i = 0
    stack = [0] * Global.CHIP8_STACK_DEPTH
    sp = 0
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

    chip8.pc = Global.CHIP8_ENTRY_POINT_ADDRESS

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

def chip8_get_register(chip8: Chip8, index: int):
    assert((index >= 0) and (index < Global.CHIP8_REGISTER_COUNT))
    result = chip8.register[index]
    return result

def chip8_set_register(chip8: Chip8, index: int, value: int):
    assert((index >= 0) and (index < Global.CHIP8_REGISTER_COUNT))
    chip8.register[index] = value

def _00EE(chip8: Chip8):
    chip8.pc = chip8.stack[chip8.sp]
    chip8.sp -= 1

def _1nnn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF
    chip8.pc = nnn

def _2nnn(chip8: Chip8):
    chip8.sp += 1
    chip8.stack[chip8.sp] = chip8.pc
    nnn = chip8.opcode & 0x0FFF
    chip8.pc = nnn

def _3xnn(chip8: Chip8):
    nn = chip8.opcode & 0x00FF
    x = (chip8.opcode >> 8) & 0x000F
    vx = chip8_get_register(chip8, x)
    
    if vx == nn:
        chip8.pc += 2

def _6xnn(chip8: Chip8):
    nn = chip8.opcode & 0x00FF
    x = (chip8.opcode >> 8) & 0xF
    chip8_set_register(chip8, x, nn)

def _7xnn(chip8: Chip8):
    nn = chip8.opcode & 0x00FF
    x = (chip8.opcode >> 8) & 0xF
    chip8_set_register(chip8, x, nn)

def annn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF
    chip8.i = nnn

def bnnn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF
    v0 = chip8_get_register(chip8, 0)
    chip8.pc = nnn + v0

def dxyn(chip8: Chip8):
    sprite_height = chip8.opcode & 0x000F
    x = (chip8.opcode >> 8) & 0x000F
    y = (chip8.opcode >> 4) & 0x000F
    x = chip8_get_register(chip8, x)
    y = chip8_get_register(chip8, y)

    for i in range(sprite_height):
        byte = chip8.memory[chip8.i]
        for j in range(Global.CHIP8_SPRITE_WIDTH):
            pixel = byte >> (7 - j) & 1
            video_index = ((y + i) * Global.CHIP8_VIDEO_WIDTH) + (x + j)
            previous_pixel = chip8.video[video_index]
            chip8.video[video_index] ^= pixel

            if (previous_pixel == 1) and (chip8.video[video_index] == 0):
                chip8_set_register(chip8, 0xF, 1)
            else:
                chip8_set_register(chip8, 0xF, 0)

def chip8_cycle(chip8: Chip8):
    result = False

    # Fetch (big endian)
    chip8.opcode = (chip8.memory[chip8.pc] << 8) | chip8.memory[chip8.pc + 1]

    chip8.pc += 2

    # Decode and execute
    opcode = (chip8.opcode >> 12) & 0x000F

    if chip8.opcode == 0xEE:
        _00EE(chip8)
    elif opcode == 0x01:
        _1nnn(chip8)
    elif opcode == 0x02:
        _2nnn(chip8)
    elif opcode == 0x03:
        _3xnn(chip8)
    elif opcode == 0x06:
        _6xnn(chip8)
    elif opcode == 0x07:
        _7xnn(chip8)
    elif opcode == 0x0A:
        annn(chip8)
    elif opcode == 0x0B:
        bnnn(chip8)
    elif opcode == 0x0D:
        dxyn(chip8)
    else:
        log("Invalid instruction: %X", chip8.opcode)
        return result

    # delay timer
    if chip8.delay_timer > 0:
        chip8.delay_timer -= 1

    # sound timer
    if chip8.sound_timer > 0:
        chip8.sound_timer -= 1

    return True

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

        if not chip8_cycle(emulator.chip8):
            break
        
        # Draw
        video.fill((0, 0, 0))

        pixel_size = 16 # experiment

        for y in range(Global.CHIP8_VIDEO_HEIGHT):
            for x in range(Global.CHIP8_VIDEO_WIDTH):
                if emulator.chip8.video[(y * Global.CHIP8_VIDEO_WIDTH) + x] != 0:
                    draw_rectangle(video, Rectangle(x * pixel_size, y * pixel_size, pixel_size, pixel_size), RGBA(1.0, 1.0, 1.0, 0.0))

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