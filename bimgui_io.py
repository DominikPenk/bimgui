"""
This module implements the Keyobard and Mouse input handling in the class 'BImGuiIO'
"""

class BImGuiIO:
    """
    Class to handle keyboard and mous input
    """
    def __init__(self):
        self.__current_listener = 0
        self.__next_listener_id = 0
        self.__listener_states = dict()

        self._key_down_prev = {}
        self._key_down = {}

        self.mouse_down = {
            'LEFTMOUSE': False,
            'RIGHTMOUSE': False,
            'MIDDLEMOUSE': False
        }

        self.alt = False
        self.shift = False
        self.ctrl = False
        self.mouse_pos = []

        self.__mouse_buttons = ['MIDDLEMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE']
        self.__mouse_types = ['MOUSEMOVE', 'MIDDLEMOUSE', 'LEFTMOUSE', 'RIGHTMOUSE']
        self.__ignored = [
            'NONE',
            'TIMER', 'TIMER0', 'TIMER1', 'TIMER2', 'TIMER_JOBS', 'TIMER_AUTOSAFE'
            'WINDOW_DEACTIVATE',
            'BUTTON4MOUSE', 'BUTTON5MOUSE', 'BUTTON6MOUSE', 'BUTTON7MOUSE',
            'PEN', 'ERASER',
            'INBETWEEN_MOUSEMOVE', 'TRACKPADPAN', 'TRACKPADZOOM', 'MOUSEROTATE',
            'EVT_TWEAK_L', 'EVT_TWEAK_R', 'EVT_TWEAK_M',
            'LEFT_CTRL', 'LEFT_ALT', 'RIGHT_ALT', 'RIGHT_CTRL', 'RIGHT_SHIFT', 'OSKEY', 'GRLESS',
            'LINE_FEED', 'WINDOW_DEACTIVATE']

    def handle_input(self, event):
        """
        This will handle an input event and update the internal io state
        """
        self.ctrl = event.ctrl
        self.alt = event.alt
        self.shift = event.shift

        self.mouse_pos = [event.mouse_x, event.mouse_y]

        if event.type in self.__ignored:
            return
        if event.type in self.__mouse_types:
            if event.type != 'MOUSEMOVE':
                if event.value == 'PRESS':
                    self.mouse_down[event.type] = True
                elif event.value == 'RELEASE':
                    self.mouse_down[event.type] = False
                    # Signal all listeners
                    for _, listener_state in self.__listener_states.items():
                        listener_state[event.type] = True
        else:
            if event.value == 'PRESS':
                if not event.type in self._key_down or not self._key_down[event.type]:
                    self._key_down[event.type] = True
            elif event.value == 'RELEASE':
                self._key_down[event.type] = False
                # Signal all listeners
                for _, listener_state in self.__listener_states.items():
                    listener_state[event.type] = True
            else:
                print(event.type, event.value)

    def is_key_down(self, key):
        """
        Returns true if the given key is currently down
        """
        return self._key_down.get(key, False)

    def register_listener(self):
        """
        Registers a new listener and returns its key
        """
        self.__listener_states[self.__next_listener_id] = {}
        tmp = self.__next_listener_id
        self.__next_listener_id += 1
        return tmp

    def unregister_listener(self, key):
        """
        Remove a listener
        """
        self.__listener_states.pop(key, None)

    def set_current_listener(self, index):
        """
        Set the current listener by index
        """
        #pylint: disable=line-too-long
        assert isinstance(index, int), "Tried to set listener but did not get an integer"
        self.__current_listener = index

    def signal_processed(self, index=None):
        """
        Signals that the listener given by index processed the io state.
        If no index is given the current listener is used as index
        """
        index = index if index is not None else self.__current_listener
        self.__listener_states[index] = {}

    @property
    def mouse_clicked(self):
        """
        Returns a dict which stores for each mouse button if it was released in the last frame
        """
        return {
            'LEFTMOUSE': not self.mouse_down['LEFTMOUSE'] and
                         self.just_released('LEFTMOUSE'),
            'RIGHTMOUSE': not self.mouse_down['RIGHTMOUSE'] and
                          self.just_released('RIGHTMOUSE'),
            'MIDDLEMOUSE': not self.mouse_down['MIDDLEMOUSE'] and
                           self.just_released('MIDDLEMOUSE'),
        }

    def just_released(self, key):
        """
        Returns true if the key 'key' was released in the last call to the listener
        """
        return self.__listener_states[self.__current_listener].get(key, False)
