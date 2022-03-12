import ctypes

SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)

# Just some Win32 API flex, ignore that since I'm not getting good results with it ...


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def setqwerty():
    global key_y
    global key_z
    key_y = 0x15
    key_z = 0x2C


def setqwertz():
    global key_y
    global key_z
    key_y = 0x2C
    key_z = 0x15


# OKAY I'm a looser, but this works so good
from pynput.keyboard import Key, Controller

# This file is still very messy from the win32 api bare interface and some better keycode tests...

keyboard = Controller()

# Key Codes, legacy.
KC = {
    'A': 16,
    'Z': 17,
    'E': 18,
    'R': 19,
    'T': 20,
    'Y': 21,
    'U': 22,
    'I': 23,
    'O': 24,
    'P': 25,

    'Q': 30,
    'S': 31,
    'D': 32,
    'F': 33,

    'G': 34,
    'H': 35,
    'J': 36,
    'K': 37,
    'L': 38,

    'W': 44,
    'X': 45,
    'C': 46,
    'V': 47,
    'B': 48,
    'N': 49,
    ',': 50,
}

SPECIALS = {
    'UP': Key.up,
    'DOWN': Key.down,
}


def press(code):
    """
    Press the key, with the given keyCode
    """
    global _keys_memo

    if code == "":
        return

    # Take a deep breath, then take a look at
    # https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes

    # OKAY IT DOES NOT WORK ON MY COMPUTER
    # here's my keycodes:

    if code in SPECIALS:
        code = SPECIALS[code]
    else:
        code = code.lower()
    # defaults to shift key
    # key = 0x10
    #
    # if code in KC:
    #     key = KC[code]
    # else:
    #     print(f"Key error : \"{code}\"")

    # PressKey(key)
    # ReleaseKey(key)

    try:
        keyboard.press(code)
        # keyboard.release(code.lower())
    except:
        print(f'Key printing error : {code}')


def release(code):
    """
    Release the key, with the given keyCode
    """
    global _keys_memo
    if code == "":
        return

    # if code in KC:
    #     key = KC[code]
    # else:
    #     print(f"Key error : \"{code}\"")

    if code in SPECIALS:
        code = SPECIALS[code]
    else:
        code = code.lower()

    try:
        keyboard.release(code)
    except:
        print(f'Key release error : {code}')
