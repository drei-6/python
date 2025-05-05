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

# define some globals
class Global:
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
    CHIP8_FONTSET_ADDRESS = 0x50 # not on the specification
    
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

# emulator state
class Emulator:
    fps = 0.0
    chip8 = Chip8()

# log function
def log(string: str, *args: tuple):
    print(string % args)

# write to ram
def chip8_write_to_ram(chip8: Chip8, index: int, value: int):
    assert((index >= 0) and (index < Global.CHIP8_RAM_SIZE))
    chip8.ram[index] = value

# set program counter
def chip8_set_program_counter(chip8: Chip8, value: int):
    assert((value >= Global.CHIP8_ENTRY_POINT_ADDRESS) and (value < Global.CHIP8_RAM_SIZE))
    chip8.program_counter = value

# read to ram
def chip8_read_from_ram(chip8: Chip8, index: int):
    assert((index >= 0) and (index < Global.CHIP8_RAM_SIZE))
    result = chip8.ram[index]
    return result

# get program counter
def chip8_get_program_counter(chip8: Chip8):
    assert((chip8.program_counter >= Global.CHIP8_ENTRY_POINT_ADDRESS) and (chip8.program_counter < Global.CHIP8_RAM_SIZE))
    result = chip8.program_counter
    return result

# set opcode
def chip8_set_opcode(chip8: Chip8, value: int):
    assert((value >= 0) and (value <= 0xFFFF))
    chip8.opcode = value

# get opcode
def chip8_get_opcode(chip8: Chip8):
    assert((chip8.opcode >= 0) and (chip8.opcode <= 0xFFFF))
    result = chip8.opcode
    return result

# set delay timer
def chip8_set_delay_timer(chip8: Chip8, value: int):
    assert((value >= 0) and (value <= 60))
    chip8.delay_timer = value

# set sound timer
def chip8_set_sound_timer(chip8: Chip8, value: int):
    assert((value >= 0) and (value <= 60))
    chip8.sound_timer = value

# get delay timer
def chip8_get_delay_timer(chip8: Chip8):
    assert((chip8.delay_timer >= 0) and (chip8.delay_timer <= 60))
    result = chip8.delay_timer
    return result

# get sound timer
def chip8_get_sound_timer(chip8: Chip8):
    assert((chip8.sound_timer >= 0) and (chip8.sound_timer <= 60))
    result = chip8.sound_timer
    return result

def chip8_set_index(chip8: Chip8, value: int):
    assert((value >= 0) and (value < Global.CHIP8_RAM_SIZE))
    chip8.index = value

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
        chip8_write_to_ram(chip8, Global.CHIP8_FONTSET_ADDRESS + i, font[i])

    chip8_set_program_counter(chip8, Global.CHIP8_ENTRY_POINT_ADDRESS)

# load chip 8 rom
def chip8_load_rom(chip8: Chip8, file_name: str):
    # read file contents to buffer
    file = open(file_name, 'rb')
    buffer = file.read()
    file.close()

    # copy buffer to ram starting at the address x
    for i in range(len(buffer)):
        chip8_write_to_ram(chip8, Global.CHIP8_ENTRY_POINT_ADDRESS + i, buffer[i])

    # release memory?
    buffer = []

def annn(chip8: Chip8):
    nnn = chip8_get_opcode(chip8) & 0x0FFF
    chip8_set_index(chip8, nnn)

# decode and execute
def chip8_decode_and_execute(chip8: Chip8):
    result = False

    opcode = chip8_get_opcode(chip8)
    opcoden4 = (opcode >> 12) & 0x000F

    if opcoden4 == 0x0A:
        annn(chip8)
    else:
        return result

    return True

def chip8_cycle(chip8: Chip8):
    result = False

    # fetch instruction
    program_counter = chip8_get_program_counter(chip8)
    byte0 = chip8_read_from_ram(chip8, program_counter)
    byte1 = chip8_read_from_ram(chip8, program_counter + 1)
    chip8_set_opcode(chip8, (byte0 << 8) | byte1)

    # advance program counter by 2
    chip8_set_program_counter(chip8, program_counter + 2)

    # decode and execute
    if(chip8_decode_and_execute(chip8)):
        pass
    else:
        log("Invalid instruction: 0x%X", chip8_get_opcode(chip8))
        return result

    # delay timer
    delay_timer = chip8_get_delay_timer(chip8)
    if delay_timer > 0:
        chip8_set_delay_timer(chip8, delay_timer - 1)
    
    # sound timer
    sound_timer = chip8_get_sound_timer(chip8)
    if sound_timer > 0:
        chip8_set_delay_timer(chip8, sound_timer - 1)

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

    return result

# emulate one cycle
def emulator_cycle(emulator: Emulator):
    result = chip8_cycle(emulator.chip8)
    return result

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

        # @TODO: draw emulator video
        
        # clear screen to black
        display.fill((0, 0, 0))

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