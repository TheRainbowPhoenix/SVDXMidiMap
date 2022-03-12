import queue
import sys
import threading
import tkinter as tk

# Using PyGame for midi is quite efficient !
import pygame.midi

# Custom key wrapper for windows
import winkeys


# My MIDI devices I tested on. AIR is the best to play the game !
class MIDIDevices:
    AXIOM_MINI = 'axiom'
    OXYGEN = 'oxygen'
    AIR = 'DJ Control Air'


class KeyMap:
    """
    ASCII ART TIME :D


    # KShoot config :

     Z / E           O / P
      ( )             ( )

    [ S ] [ D ] [ K ] [ L ]
       [ C ]      [ N ]


    # Axiom config :

    [ 40 ] [ 41 ] [ 42 ] [ 43 ]
    [    ] [ 37 ] [ 38 ] [    ]


    # DJ Air config:

    [  1 ] [  2 ]   [ 23 ] [ 24 ]
    [  3 ] [  4 ]   [ 25 ] [ 26 ]
    < 15 > < 16 >   < 37 > < 38 >
                  ^ 51
                  v 52

     ,-48-,  |  [48] |   ,-49-,
    | (22 | 54  [46] 59 | (44 |
    `----`   |  [45] |  `----`

    Spin velocity:
    <- 127  1 ->
    """

    # - Wait, it's all dict ? - Always has been
    _map = {
        40: 'S',
        41: 'D',
        42: 'K',
        43: 'L',
        37: 'C',
        38: 'N',
    }

    _map_usc_axiom_mini = {
        23: '1',
        40: 'D',
        41: 'F',
        42: 'J',
        43: 'K',
        37: 'C',
        38: ',',
    }

    _map_usc_oxygen = {
        117: 'A',
        50: 'D',
        45: 'F',
        51: 'J',
        49: 'K',
        38: 'C',
        42: ',',
    }

    _map_usc_air = {
        # Binary
        45: 'A',
        # Analog
        1: 'D',
        2: 'F',
        3: 'D',
        4: 'F',
        23: 'J',
        24: 'K',
        25: 'J',
        26: 'K',
        # Binary
        15: 'C',
        16: 'C',
        22: 'C',
        37: ',',
        38: ',',
        44: ',',
        # Special
        51: 'UP',
        52: 'DOWN'
    }

    _map_usc_air_spin = {
        48: {
            127: 'Z',
            1: 'E'
        },
        49: {
            127: 'O',
            1: 'P'
        }
    }

    # _map_your_custom_device_here = { midi_keycode: 'Letter_to_send' }

    # Reference to the current device, used as a lock
    current_device = None
    # Map the midi codes to your device
    current_map = _map_usc_air
    # Map the Jog Spin
    current_spin_map = _map_usc_air_spin

    @classmethod
    def map_device(cls, name: str) -> None:
        """
        Load the keymap. Harcoded because I don't need much customization for now.
        """
        if name == MIDIDevices.AIR:
            KeyMap.current_device = MIDIDevices.AIR
            KeyMap.current_map = KeyMap._map_usc_air
            KeyMap.current_spin_map = KeyMap._map_usc_air_spin
        # if name == MIDIDevices.YOUR_CUSTOM: ...

    @classmethod
    def map(cls, key) -> str:
        """
        Simply an easy way to lookup for keymap
        """
        if key in KeyMap.current_map:
            return KeyMap.current_map[key]
        else:
            return ''

    @classmethod
    def map_spin(cls, key, velocity) -> str:
        """
        Get the key for a spin. No types hint cause PyGame don't like it (for now) :/
        """
        if KeyMap.current_device == MIDIDevices.AIR:
            if key in KeyMap.current_spin_map:
                act = KeyMap.current_spin_map[key]
                if velocity in act:
                    return act[velocity]
        return ""


    # Hardware specific behaviour: binary mode button (all or nothing)
    _binary_air = [
        13, 14, 15, 16, 17, 18, 19, 20, 21, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 50, 51, 52, 54, 55,
        56
    ]

    # Jog reference
    # _spin_air = [
    #     48, 49
    # ]

    @classmethod
    def is_binary(cls, key_code: int) -> bool:
        """
        return if button in mapping is binary (ToutOuRien), false if analog
        :param key_code: device keycode
        :return: true if binary, false if analog
        """
        if KeyMap.current_device == MIDIDevices.AIR:
            return key_code in KeyMap._binary_air
        # TODO
        return False

    @classmethod
    def is_spin(cls, key_code: int) -> bool:
        """
        Return true if input is infinite spin, EG jogs
        :param key_code: device keycode
        :return:
        """
        if KeyMap.current_device == MIDIDevices.AIR:
            return key_code in KeyMap.current_spin_map
        # TODO
        return False


class MidiMap:
    """
    Class to wrap midi device and events
    """
    def __init__(self):
        # Storing the event and reading it between threads
        self._queue = queue.Queue()

        # Device references in GUI
        self.devicelist = []
        self.selected_device = None

        # TK GUI
        self.root = None
        self._init_tk()

        self._flag_key = {}

    def worker(self):
        """
        Midi Thread - Basically very messy. Feel free to rewrite it for your device if needed.
        """
        _keys_memo = []
        while True:
            items = self._queue.get()
            for item in items:

                channel = item[0][0]  # Implementation specific behaviour for Axiom - Note: must be 144 for CH1
                key_code = item[0][1]
                velocity = item[0][2]
                timing = item[1]

                # Useful for Axiom when midi got messy, reset the key states
                # Note: Kids, don't play SVDX with a midi piano PLEASE
                #  - No I'm deadly serious, don't !

                # RiP PANIC MODE - 2021 - 2021
                # if key_code == 118:
                #     for k in self._flag_key:
                #         self._flag_key[k] = False

                # Ignored midi keycode, got them really noisy for AIR
                if key_code in [53, 63]:
                    continue

                # Debug use : print key in console. Useful for mapping too
                print(f"Got key : {repr(item)}")

                # Map the actual key
                key_map = KeyMap.map(key_code)

                # Flag test, useful with keyboard when midi infos are messy
                # if key_map in self._flag_key:
                #     self._flag_key[key_map] = not self._flag_key[key_map]
                # else:
                #     self._flag_key[key_map] = True

                # if self._flag_key[key_map]:

                # Real mapping here ! Midi controller AIR specific
                if KeyMap.current_device == MIDIDevices.AIR:
                    print(f"MAP OF {key_map}")

                    # Binary button are all (127) or nothing (0)
                    if KeyMap.is_binary(key_code):
                        if velocity == 127:
                            winkeys.press(key_map)
                        else:
                            winkeys.release(key_map)

                    # Jog spin are clockwise (1) or counter-clockwise (127)
                    elif KeyMap.is_spin(key_code):
                        """
                        Key mapped in SVDX and midi velocity :
                        
                        Z / E           O / P
                        
                        <- 127  1 ->
                        """
                        # Debug, because I got case where no spin where detected...
                        print(f'is_spin')
                        key_map = KeyMap.map_spin(key_code, velocity)
                        if key_map != '':
                            # More debug !
                            print(f'Spin {key_map}')
                            # Do the actual keypress here
                            winkeys.press(key_map)
                            winkeys.release(key_map)

                    # At this point it should be a simple button press
                    else:
                        # Velocity == 0 => release
                        if velocity == 0 and key_map in _keys_memo:
                            # Debug trace in console
                            print(f'release {key_map}')
                            # Remove from memo of pressed keys, and do it
                            _keys_memo.remove(key_map)
                            winkeys.release(key_map)
                        # Velocity > 0 => press
                        elif velocity > 0 and key_map not in _keys_memo:
                            # Debug trace in console
                            print(f'press {key_map}')
                            # Add to memo of pressed keys, and do it
                            _keys_memo.append(key_map)
                            winkeys.press(key_map)

                # MIDI keyboard mapping - You're crazy if you use that !
                if KeyMap.current_device == MIDIDevices.OXYGEN:
                    # Oxygen midi specific mapping
                    if channel == 153:

                        print(f"MAP OF {key_map}")
                        winkeys.press(key_map)
                    elif channel == 137:
                        winkeys.release(key_map)

                    elif channel == 176:
                        winkeys.press(key_map)
                        winkeys.release(key_map)

                # keypress.keys(str(item))
            self._queue.task_done()

    def _init_tk(self):
        """
        Small window to select the device and start/stop mapping
        """
        self.root = tk.Tk()
        self.root.geometry('350x90')
        self.root.resizable(0, 0)
        self.root.title("MidiMap")
        self.root.poll = True

    def start(self):
        """
        Start the thread and launch GUI
        """
        self._t = threading.Thread(target=self.worker)
        self._t.daemon = True
        self._t.start()

        self.refresh_devices()

        self.setup_ui()

        self.root.mainloop()

    def refresh_devices(self):
        """
        refresh midi devices
        """
        for dev in range(0, pygame.midi.get_count()):
            if pygame.midi.get_device_info(dev)[2] == 1:
                # Can be bugged on some device and causes crash. It didn't happen to me so far ...
                self.devicelist.append(f"{dev}- {pygame.midi.get_device_info(dev)[1].decode()}")
                print(pygame.midi.get_device_info(dev))
                KeyMap.map_device(pygame.midi.get_device_info(dev)[1].decode())

        # TODO: keep the program alive if no device
        if not self.devicelist:
            print("No devices !!")
            # noDevices()
            self.quit_program()

    # Main midi loop
    def midiloop(self):
        if self.root.poll:
            keys = []
            if self.inp.poll():
                raw_key = self.inp.read(1000)
                self._queue.put(raw_key)

            pygame.time.wait(1)
            self.root.after(0, self.midiloop)
        else:
            return

    # UI Methods
    def enable_button(self, dev):
        self.start_button.config(state='normal')
        self.selected_device = dev[0]

    def quit_program(self):
        pygame.quit()
        sys.exit()

    def callback(self):
        self.msg_output_label.config(text="Running...")
        self.start_button.config(state='disabled')
        self.dev_drop.config(state='disabled')
        # self.azerty_button.config(state='disabled')

        self.root.update()

        print("Device: " + self.selected_device)
        self.inp = pygame.midi.Input(int(self.selected_device))
        self.midiloop()

    def setup_ui(self):
        self.devices = tk.StringVar(self.root)
        self.devices.set('SELECT A MIDI DEVICE')

        self.dev_drop = tk.OptionMenu(self.root, self.devices, *self.devicelist, command=self.enable_button)
        self.dev_drop.config(width=20)
        self.dev_drop.grid(row=0, column=0, sticky="W")

        self.quit_button = tk.Button(self.root, text=" QUIT ", command=self.quit_program)
        self.quit_button.grid(row=1, column=1, sticky="E")

        self.start_button = tk.Button(self.root, text="START", state='disabled', command=self.callback)
        self.start_button.grid(row=0, column=1, sticky="E")

        self.msg_output_label = tk.Label(self.root, text="Select Keyboard and hit Start", anchor="w")
        self.msg_output_label.grid(row=3, column=0, sticky="W")


if __name__ == '__main__':
    pygame.init()
    pygame.midi.init()

    midiMap = MidiMap()
    midiMap.start()
