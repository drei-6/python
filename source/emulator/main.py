import time
import pygame

# Attempt number 3.
# http://devernay.free.fr/hacks/chip8/C8TECH10.HTM

# 0x000-0x1FF is writable by the interpreter but only readable by the programs.
# Most programs start location is at 0x200, but some are at 0x600 (ETI 660 computer).
# 0x200-0xFFF program / data space. And maybe 0x600-0xFFF for ETI 660 computer?
# There are 16 general purpose 8-bit registers referred to V0-VF.
# The 16-bit register I is used commonly to store memory address (low 12-bits).
# VF should NOT be used by any program because its used by some instructions.
# Delay_timer/sound_timer are 8-bit registers that are decremented if > 0 at 60hz.
# PC is a 16-bit register that holds the address of current instruction.
# SP is 8-bit and its a pointer to the topmost level of the stack.
# The stack is an array of 16 16-bit values. Holds the return address for PC (depth 16).
# Keypad is 1,2,3,C/4,5,6,D/7,8,9,E/A,0,B,F (4x4).
# Display is monochrome with resolution of 64x32 pixels.
# ETI 660 had 64x48 and 64x64 modes. Super Chip 48 added 128x64 pixel mode.
# Chip 8 sprite of height up to 15 bytes and fixed width of 8 (bits?).
# Fontset is 8x5 pixels. This fontset should be store at 0x000-0x1FF
# Sound timer if > 0 decremets at 60 hz and will make only one tone.
# Chip 8 has 36 instructions. Super Chip-48 has 46.
# Instruction are 2-bytes and are most-signifcant-byte first.
# The first by of each instruction should be located at an even address.
# if a program includes sprite data it should be padded... by 2 maybe?

# Rectangle
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

# RGBA
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

# define some globals
class Global:
    EMULATOR_INVALID_MODE = 0
    EMULATOR_CHIP8_MODE = 1
    CHIP8_MONITOR_REFRESH_RATE = 60.0
    CHIP8_RAM_SIZE = 4096
    CHIP8_REGISTER_COUNT = 16
    CHIP8_STACK_DEPTH = 16
    CHIP8_KEY_COUNT = 16
    CHIP8_DISPLAY_WIDTH = 64
    CHIP8_DISPLAY_HEIGHT = 32
    CHIP8_FONT_WIDTH = 8
    CHIP8_FONT_HEIGHT = 5
    CHIP8_SPRITE_WIDTH = 8
    CHIP8_ENTRY_POINT_ADDRESS = 0x200
    CHIP8_FONTSET_ADDRESS = 0x50 # not on the "specification"
    
# chip 8 state
class Chip8:
    ram = [0] * Global.CHIP8_RAM_SIZE # ram
    register = [0] * Global.CHIP8_REGISTER_COUNT # register
    index = 0 # index
    delay_timer = 0 # delay timer
    sound_timer = 0 # sound timer
    program_counter = 0 # program counter
    stack_pointer = 0 # stack pointer
    stack = [0] * Global.CHIP8_STACK_DEPTH # stack
    keypad = [0] * Global.CHIP8_KEY_COUNT # keypad
    display = [0] * (Global.CHIP8_DISPLAY_WIDTH * Global.CHIP8_DISPLAY_HEIGHT) # display
    opcode = 0 # current opcode being executed

class Debugger:
    is_debugging = False
    line = 0
    instruction = {}

# emulator state
class Emulator:
    debugger = Debugger()
    fps = 0.0
    mode = 0
    chip8 = Chip8()

# log function
def log(string: str, *args: tuple):
    print(string % args)

# convert rectangle to pygame rectangle
def rectangle_to_pygame_rect(rectangle: Rectangle):
    result = pygame.Rect(rectangle.x, rectangle.y, rectangle.width, rectangle.height)
    return result

# convert rgba to pygame rgba
def rgba_to_pygame_rgba(rgba: RGBA):
    result = (int(rgba.r * 255.0), int(rgba.g * 255.0), int(rgba.b * 255.0), int((1.0 - rgba.a) * 255.0))
    return result

# draw rectangle
def draw_rectangle(display: pygame.Surface, rectangle: Rectangle, rgba: RGBA):
    rectangle = rectangle_to_pygame_rect(rectangle)
    rgba = rgba_to_pygame_rgba(rgba)
    rectangle_surface = pygame.Surface((rectangle.width, rectangle.height))
    rectangle_surface.set_alpha(rgba[3])
    rectangle_surface.fill(rgba)
    display.blit(rectangle_surface, (rectangle.left, rectangle.top))

# draw character
def draw_character(display: pygame.Surface, font: pygame.font.Font, x: int, y: int, character: str, is_antialiasing: bool, foreground_rgba: RGBA, background_rgba: RGBA):
    #@TODO: Check for failure with pygame
    result = 0
    foreground_rgba = rgba_to_pygame_rgba(foreground_rgba)
    background_rgba = rgba_to_pygame_rgba(background_rgba)
    character_surface = font.render(character, is_antialiasing, foreground_rgba, None)
    background_alpha = background_rgba[3]
    background_surface = pygame.Surface(character_surface.get_size())
    background_surface.set_alpha(background_alpha)
    background_surface.fill(background_rgba)
    display.blit(background_surface, (x, y))
    display.blit(character_surface, (x, y))

    result = character_surface.get_size()
    return result

# draw text
def draw_text(display: pygame.Surface, font: pygame.font.Font, x: int, y: int, text: str, is_antialiasing: bool, foreground_rgba: RGBA, background_rgba: RGBA):
    for c in text:
        if c == '\n':
            x = 0
            y += font.get_height()
            continue

        dimension = draw_character(display, font, x, y, c, is_antialiasing, foreground_rgba, background_rgba)
        x += dimension[0]

def chip8_initialize(chip8: Chip8):
    # this is the font 8x5
    font = [
        0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
        0x20, 0x60, 0x20, 0x20, 0x70, # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
        0x90, 0x90, 0xF0, 0x10, 0x10, # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
        0xF0, 0x10, 0x20, 0x40, 0x40, # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90, # A
        0xF0, 0x90, 0xE0, 0x90, 0xE0, # B
        0xF0, 0x80, 0x80, 0x80, 0xF0, # C
        0xE0, 0x80, 0x90, 0x90, 0xE0, # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
        0xF0, 0x80, 0xF0, 0x80, 0x80, # F
    ]

    # write the font to memory at location x
    for i in range(len(font)):

        chip8.ram[Global.CHIP8_FONTSET_ADDRESS + i] = font[i]

    # set the program_counter
    chip8.program_counter = Global.CHIP8_ENTRY_POINT_ADDRESS

# load chip 8 rom
def chip8_load_rom(chip8: Chip8, file_name: str):
    # read file contents to buffer
    file = open(file_name, 'rb')
    buffer = file.read()
    file.close()

    # copy buffer to ram starting at the address x
    for i in range(len(buffer)):
        chip8.ram[Global.CHIP8_ENTRY_POINT_ADDRESS + i] = buffer[i]

    # release memory?
    buffer = []

# RET
def chip8_00EE(chip8: Chip8):
    chip8.program_counter = chip8.stack[chip8.stack_pointer] # set program_counter to the address at top of the stack
    chip8.stack_pointer -= 1 # decrement the stack pointer

# LD I, addr
def chip8_annn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF
    chip8.index = nnn

# CALL addr
def chip8_2nnn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF # isolate nnn
    chip8.stack_pointer += 1 # increment stack pointer
    chip8.stack[chip8.stack_pointer] = chip8.program_counter # set top of the stack to program counter
    chip8.program_counter = nnn # set program counter to nnn

# LD Vx, byte
def chip8_6xkk(chip8: Chip8):
    kk = chip8.opcode & 0x00FF # isolate kk
    x = (chip8.opcode >> 8) & 0x000F # isolate x
    chip8.register[x] = kk # set register 'x' to 'kk'

# ADD Vx, byte
def chip8_7xkk(chip8: Chip8):
    kk = chip8.opcode & 0x00FF # isolate 'kk'
    x = (chip8.opcode >> 8) & 0x000F # isolate 'x'
    chip8.register[x] += kk # add 'kk' to register 'x'

def chip8_dxyn(chip8: Chip8):
    n = chip8.opcode & 0x000F # isolate 'n'
    index_x = (chip8.opcode >> 8) & 0x000F # isolate 'x'
    index_y = (chip8.opcode >> 4) & 0x000F # isolate 'y'
    x = chip8.register[index_x]
    y = chip8.register[index_y]

# fetch the opcode
def chip8_fetch(chip8: Chip8):
    assert(chip8.program_counter < Global.CHIP8_RAM_SIZE)

    result = (chip8.ram[chip8.program_counter] << 8) | (chip8.ram[chip8.program_counter + 1])
    chip8.program_counter += 2

    return result

# decode and execute
def chip8_decode_and_execute(chip8: Chip8):
    assert(chip8.opcode < 0xFFFF)

    result = False
    opcoden4 = (chip8.opcode >> 12) & 0x000F

    if chip8.opcode == 0xEE:
        chip8_00EE(chip8)
    elif opcoden4 == 0x0A:
        chip8_annn(chip8)
    elif opcoden4 == 0x02:
        chip8_2nnn(chip8)
    elif opcoden4 == 0x06:
        chip8_6xkk(chip8)
    elif opcoden4 == 0x07:
        chip8_7xkk(chip8)
    else:
        return result

    return True

def chip8_cycle(chip8: Chip8, debugger: Debugger):
    result = False

    # fetch the opcode
    chip8.opcode = chip8_fetch(chip8)

    # decode and execute
    if not chip8_decode_and_execute(chip8):
        log("Invalid instruction: 0x%X", chip8.opcode)
        return result

    # delay timer
    if chip8.delay_timer > 0:
        chip8.delay_timer -= 1
    
    # sound timer
    if chip8.sound_timer > 0:
        chip8.sound_timer -= 1

    debugger.is_debugging = True

    return True
    
# load emulator rom
def emulator_load_rom(emulator: Emulator, file_name: str):
    result = False

    chip8_load_rom(emulator.chip8, file_name)

    return True

# initialize emulator
def emulator_initialize():
    result = Emulator()
    
    chip8_initialize(result.chip8)
    result.fps = Global.CHIP8_MONITOR_REFRESH_RATE
    result.mode = Global.EMULATOR_CHIP8_MODE

    debugger = result.debugger
    debugger.is_debugging = False
    debugger.instruction = {
        "": "",
        "Annn": "LD I, %s",
    }

    return result

# emulate one cycle
def emulator_cycle(emulator: Emulator):
    result = chip8_cycle(emulator.chip8, emulator.debugger)
    return result

# chip 8 opcode to string
def chip8_opcode_to_string(chip8:Chip8, debugger: Debugger):
    result = ""

    # decode
    opcode_high_upper_nibble = (chip8.opcode >> 12) & 0x000F
    instruction_name = ""

    if opcode_high_upper_nibble == 0:
        if (chip8.opcode & 0x00FF) == 0xE0:
            result = "00E0"
        elif (chip8.opcode & 0x00FF) == 0xEE:
            result = "00EE"
        else:
            result = "0nnn"
    elif opcode_high_upper_nibble == 0x0A:
        result = debugger.instruction["Annn"] % hex(chip8.opcode & 0x0FFF)
    else:
        pass # @TODO: Report it?

    return result

# draw debugger
def emulator_draw_debugger(emulator: Emulator, display: pygame.Surface, font: pygame.font.Font):
    display_width = display.get_width()
    display_height = display.get_height()

    # draw background
    draw_rectangle(display, Rectangle(display_width // 2, 0, display_width // 2, display_height), RGBA(1.0, 0.0, 0.0, 0.8))

    # opcode to string
    instruction = chip8_opcode_to_string(emulator.chip8, emulator.debugger)

    # draw instructions
    draw_text(display, font, 0, 0, instruction, True, RGBA(1.0, 0.0, 0.0, 0.0), RGBA(0.0, 0.0, 0.0, 1.0))

# emulator draw
def emulator_draw(emulator: Emulator, display: pygame.Surface, font: pygame.font.Font):
    if emulator.debugger.is_debugging:
        emulator_draw_debugger(emulator, display, font)

# entry point
def main():
    result = 1

    # initialize pygame
    failed_modules_count = pygame.init()[1]

    if failed_modules_count > 0:
        log("pygame.init() failed with %u module(s)", failed_modules_count)
        return result

    # create a display
    display_width = 1280
    display_height = 720
    display = pygame.display.set_mode((display_width, display_height))

    if display is None:
        log("pygame.display.set_mode() failed")
        pygame.quit()
        return result
    
    # initialize emulator
    emulator = emulator_initialize()
    font = pygame.font.Font(None, 32)

    # load rom
    if not emulator_load_rom(emulator, "tetris.ch8"):
        pygame.quit()
        return result
    
    # main loop
    is_running = True

    # timer
    last_counter = time.perf_counter_ns()
    while is_running:
        # event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
        
        if not is_running:
            break

        # emulator cycle
        if not emulator_cycle(emulator):
            break   
        
        # clear screen to black
        display.fill((0, 0, 0))

        # draw emulator video
        emulator_draw(emulator, display, font)

        # timer
        work_counter = time.perf_counter_ns()
        while work_counter < (1.0 / emulator.fps):
            work_counter = time.perf_counter_ns()
        end_counter = time.perf_counter_ns()

        # flip display
        pygame.display.flip()
        
        # timer
        last_counter = end_counter
    

    # finalize pygame
    pygame.quit()

    return 0

if __name__ == "__main__":
    exit(main())