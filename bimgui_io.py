class BImGui_IO:
    def __init__(self):
        self._key_down_prev = {}
        self._key_down = {}
        self.mouse_down = {
            'LEFTMOUSE': False,
            'RIGHTMOUSE': False,
            'MIDDLEMOUSE': False
        }
        self.mouse_clicked = {
            'LEFTMOUSE': False,
            'RIGHTMOUSE': False,
            'MIDDLEMOUSE': False
        }
        self.__timer_since_release = {
            'LEFTMOUSE': 0,
            'RIGHTMOUSE': 0,
            'MIDDLEMOUSE': 0
        }

        self.alt = False
        self.shift = False
        self.ctrl = False
        self.mouse_pos = []

        self.__mouse_buttons = ['MIDDLEMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE']
        self.__mouse_types = ['MOUSEMOVE', 'MIDDLEMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE']
        self.__ignored = ['NONE',
            'TIMER', 'TIMER0', 'TIMER1', 'TIMER2', 'TIMER_JOBS', 'TIMER_AUTOSAFE'
            'WINDOW_DEACTIVATE',
            'BUTTON4MOUSE', 'BUTTON5MOUSE', 'BUTTON6MOUSE', 'BUTTON7MOUSE',
            'PEN', 'ERASER',
            'INBETWEEN_MOUSEMOVE', 'TRACKPADPAN', 'TRACKPADZOOM', 'MOUSEROTATE',
            'EVT_TWEAK_L', 'EVT_TWEAK_R', 'EVT_TWEAK_M',
            'LEFT_CTRL', 'LEFT_ALT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY', 'GRLESS',
            'LINE_FEED', 'WINDOW_DEACTIVATE' ]

    def handle_input(self, event):
        self.ctrl = event.ctrl
        self.alt = event.alt
        self.shift = event.shift

        self.mouse_pos = [event.mouse_x, event.mouse_y]
        if event.type.startswith("TIMER"):
            for button in self.__mouse_buttons:
                if self.mouse_clicked[button] == True and self.__timer_since_release[button] == 1:
                    self.mouse_clicked[button] = False
                self.__timer_since_release[button] += 1

        if event.type in self.__ignored:
            return
        if event.type in self.__mouse_types:
            self.mouse_clicked['MIDDLEMOUSE'] = False 
            self.mouse_clicked['LEFTMOUSE'] = False
            self.mouse_clicked['RIGHTMOUSE'] = False
            if event.type != 'MOUSEMOVE':
                if event.value == 'PRESS':
                    self.mouse_down[event.type] = True
                elif event.value == 'RELEASE':
                    self.mouse_down[event.type] = False
                    self.mouse_clicked[event.type] = True
                    self.__timer_since_release[event.type] = 0
        else:
            # print(event.type, event.value)
            if event.value == 'PRESS':
                if not event.type in self._key_down or not self._key_down[event.type]:
                    print("Key {} down".format(event.type))
                self._key_down[event.type] = True
            elif event.value == 'RELEASE' and event.type in self._key_down and self._key_down[event.type]:
                print("Key {} was released".format(event.type))
                self._key_down[event.type] = False
            else:
              print(event.type, event.value)

    def is_key_down(self, key):
        return key in self._key_down and self._key_down[key]
