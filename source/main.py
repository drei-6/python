import time
import pygame

class Global:
    CHIP8_MEMORY_SIZE = 4096
    CHIP8_REGISTER_COUNT = 16
    CHIP8_STACK_SIZE = 16
    CHIP8_KEYPAD_COUNT = 16
    CHIP8_START_ADDRESS = 0x200
    CHIP8_FONTSET_ADDRESS = 0x50
    CHIP8_VIDEO_WIDTH = 64
    CHIP8_VIDEO_HEIGHT = 32
    CHIP8_SPRITE_WIDTH = 8
    CHIP8_SPRITE_HEIGHT = 15
    CHIP8_FONTSET_WIDTH = 8
    CHIP8_FONTSET_HEIGHT = 5
    
class Chip8:
    memory = [0] * Global.CHIP8_MEMORY_SIZE
    register = [0] * Global.CHIP8_REGISTER_COUNT
    i = 0
    delay_timer = 0
    sound_timer = 0
    pc = 0
    sp = 0
    stack = [0] * Global.CHIP8_STACK_SIZE
    keyboard = [False] * Global.CHIP8_KEYPAD_COUNT
    video = [0] * (64 * 32)
    opcode = 0

def log(string: str, *arguments: tuple):
    print(string % arguments)

def initialize():
    result = Chip8()

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
        result.memory[Global.CHIP8_FONTSET_ADDRESS + i] = fontset[i]

    result.pc = Global.CHIP8_START_ADDRESS

    return result

def load_rom(chip8: Chip8, file_name: str):
    file = open(file_name, 'rb')
    buffer = file.read()
    file.close()

    for i in range(len(buffer)):
        chip8.memory[Global.CHIP8_START_ADDRESS + i] = buffer[i]

    buffer = []

def _00ee(chip8: Chip8):
    chip8.pc = chip8.stack[chip8.sp]
    chip8.sp -= 1

def _1nnn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF
    chip8.pc = nnn

def _2nnn(chip8: Chip8):
    # @TODO: check if the address is withing bounds
    chip8.sp += 1
    chip8.stack[chip8.sp] = chip8.pc
    address = chip8.opcode & 0x0FFF
    chip8.pc = address

def _3xkk(chip8: Chip8):
    x = (chip8.opcode >> 8) & 0x000F
    kk = chip8.opcode & 0x00FF

    if chip8.register[x] == kk:
        chip8.opcode += 2

def _6xkk(chip8: Chip8):
    kk = chip8.opcode & 0x00FF
    x = (chip8.opcode >> 8) & 0x000F
    assert((x >= 0) and (x < Global.CHIP8_REGISTER_COUNT))
    chip8.register[x] = kk

def _7xkk(chip8: Chip8):
    kk = chip8.opcode & 0x00FF
    x = (chip8.opcode >> 8) & 0x000F
    assert((x >= 0) and (x < Global.CHIP8_REGISTER_COUNT))
    chip8.register[x] += kk

def annn(chip8: Chip8):
    nnn = chip8.opcode & 0x0FFF
    chip8.i = nnn

def dxyn(chip8: Chip8):
    # @TODO: fix this
    address = chip8.i
    height = chip8.opcode & 0x000F
    register_x = (chip8.opcode >> 8) & 0x000F
    assert((register_x >= 0) and (register_x < Global.CHIP8_REGISTER_COUNT))
    register_y = (chip8.opcode >> 4) & 0x000F
    assert((register_y >= 0) and (register_y < Global.CHIP8_REGISTER_COUNT))
    x = chip8.register[register_x] % Global.CHIP8_SPRITE_WIDTH
    y = chip8.register[register_y] % Global.CHIP8_SPRITE_HEIGHT

    for i in range(height):
        byte = chip8.memory[address + i]
        for j in range(Global.CHIP8_SPRITE_WIDTH):
            # 1 0 0 0 0 0 0 0
            bit = (byte >> (7 - j)) & 1
            new_x = (x + j) # % Global.CHIP8_VIDEO_WIDTH
            new_y = (y + i) # % Global.CHIP8_VIDEO_HEIGHT
            position = (new_y * Global.CHIP8_VIDEO_WIDTH) + new_x
            chip8.video[position] ^= bit
            chip8.register[0xF] = 1 if chip8.video[position] == 0 else 0

    return

def chip8_cycle(chip8: Chip8):
    result = False

    # Fetch opcode
    chip8.opcode = (chip8.memory[chip8.pc] << 8) | chip8.memory[chip8.pc + 1]

    # Increment PC by 2
    chip8.pc += 2

    # decode and execute
    opcode = ((chip8.opcode & 0xF000) >> 12)

    if chip8.opcode == 0x00E0:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif chip8.opcode == 0x00EE:
        _00ee(chip8)
    elif opcode == 0X0:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0x1:
        _1nnn(chip8)
    elif opcode == 0x2:
        _2nnn(chip8)
    elif opcode == 0x3:
        _3xkk(chip8)
    elif opcode == 0x4:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0x5:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0x6:
        _6xkk(chip8)
    elif opcode == 0x7:
        _7xkk(chip8)
    elif opcode == 0x8:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0x9:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0xA:
        annn(chip8)
    elif opcode == 0xB:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0xC:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0xD:
        dxyn(chip8)
    elif opcode == 0xE:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    elif opcode == 0xF:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
    else:
        print("Invalid instruction: ", hex(chip8.opcode))
        return result
        
    # if delay timer is greater than 0 decrement by 1
    if chip8.delay_timer > 0:
        chip8.delay_timer -= 1

    # if sound timer is greater than 0 decrement by 1
    if chip8.sound_timer > 0:
        chip8.sound_timer -= 1

    return True

def main():
    result = 1

    pygame.init()
    window_width = 1280
    window_height = 720
    display = pygame.display.set_mode((window_width, window_height))
    
    chip8 = initialize()
    load_rom(chip8, "tetris.rom")

    is_running = True
    fps = 60.0
    inverse_fps = 1.0 / fps
    last_counter = time.perf_counter_ns()    

    while is_running:
        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

        if not is_running:
            break

        # 1 chip 8 cycle
        if not chip8_cycle(chip8):
            break
        

        # draw time!
        display.fill((255, 0, 0))
        pixel_size = 8

        for y in range(Global.CHIP8_VIDEO_HEIGHT):
            for x in range(Global.CHIP8_VIDEO_WIDTH):
                pixel = chip8.video[(y * Global.CHIP8_VIDEO_WIDTH) + x]

                if pixel == 0:
                    pygame.draw.rect(display, (0, 0, 0), pygame.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size))
                elif pixel == 1:
                    pygame.draw.rect(display, (255, 255, 255), pygame.Rect(x * pixel_size, y * pixel_size, pixel_size, pixel_size))
                else:
                    assert("Video value is invalid!")

        # Timer
        work_counter = time.perf_counter_ns()
        while work_counter < inverse_fps:
            work_counter = time.perf_counter_ns()
        end_counter = time.perf_counter_ns()

        # Update screen
        pygame.display.flip()

        last_counter = end_counter

    pygame.quit()

    return 0

if __name__ == "__main__":
    exit(main())