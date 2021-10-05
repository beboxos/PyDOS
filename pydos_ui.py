"""
    Terminal abstraction layer for Keboard FeatherWing by @Arturo182 and @solderparty

    Adds the following keyboard functionality

        Pressing Alt-$ (Speaker) returns an equal sign (=)
        Holding down a key for 2 seconds will either shift the character or return the Alt key
        Pressing Alt-Enter will toggle between Shift and Alt when holding a key for 2 seconds
        Pressing Alt-Space will enable Caps Lock or Alt Lock depending on the Alt-Enter toggle state
        Using a shift key when Caps Lock is on returns the lower case character
        Pressing the Microphone symbol returns a left bracket ([)
        Using the 2 second Shift or Shift Lock on the Microphone Symbol returns a right bracket (])
        Using the 2 second Shift or Shift Lock on the dollar sign ($) returns the percent symbal (%)
        Pressing the F3 key will return the last entered line
        Pressing the F2 and then pressing a key will return the last entered line up to the first instance of that key

"""

from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_RELEASE, STATE_LONG_PRESS
import board

import adafruit_ili9341
import digitalio
import displayio


class PyDOS_UI:

    __SHIFT = 1
    __ALT = 2

    def __init__(self):
        # Release any resources currently in use for the displays
        displayio.release_displays()

        tft_cs = board.D9
        tft_dc = board.D10
        display_bus = displayio.FourWire(board.SPI(), command=tft_dc, chip_select=tft_cs)
        display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

        self.__kbd = BBQ10Keyboard(board.I2C())

        self.__contrl_seq = []

        self.__shift_Lock = False
        self.__shift_Mode = self.__SHIFT # Default Cap lock/Long Press mode

        self.__lastCmdLine = ""

    def __process_key(self,key,time_Param):
        # Modified the pressed key value per translation table or
        # held key modifications (shift for 3 seconds, alt for 6 seconds)

        altChars = {'q':'#', 'w':'1', 'e':'2', 'r':'3', 't':'(', 'y':')', 'u':'_', 'i':'-', 'o':'+', 'p':'@',
                    'a':'*', 's':'4', 'd':'5', 'f':'6', 'g':'/', 'h':':', 'j':';', 'k':"'", 'l':'"',
                    'z':'7', 'x':'8', 'c':'9', 'v':'?', 'b':'!', 'n':',', 'm':'.', '$':'=', '~':'0'}

        if time_Param == None and not self.__shift_Lock:
            if key == '\x60': # change speaker symbol to equal sign
                retVal = '='
            elif key == '~': # change microphone symbol to left bracket
                retVal = '['
            else:
                retVal = key
        elif self.__shift_Mode == self.__SHIFT:
            if key == '~':
                retVal = ']'
            elif key == '$':
                retVal = '%'
            else:
                if key != key.upper():
                    retVal = key.upper()
                else:
                    retVal = key.lower()
            print(retVal+'\x08',end="")
        elif self.__shift_Mode == self.__ALT:
            retVal = altChars.get(key,key)
            print(retVal+'\x08',end="")

        return retVal

    def read_keyboard(self,num):
        # Does the same function as sys.stdin.read(num)
        # Reads num characters from keyboard and returns
        # This is a blocking read, ie the program will wait for the input
        input_text = ""

        while self.__kbd.key_count == 0 and len(self.__contrl_seq) == 0:
            pass

        while num > 0:
            if len(self.__contrl_seq) > 0:
                input_text += self.__contrl_seq.pop(0)
                num -= 1
            else:
                k = self.__kbd.key
                if k != None:
                    if k[0] == STATE_RELEASE:
                        if k[1] == '\x01':   # Up Arrow - emulate terminal behavior
                            self.__contrl_seq = ['\x5b','\x41']
                            input_text += '\x1b'
                            num -= 1
                        elif k[1] == '\x02': # Down Arrow - emulate terminal behavior
                            self.__contrl_seq = ['\x5b','\x42']
                            input_text += '\x1b'
                            num -= 1
                        else:
                            input_text += k[1]
                            num -= 1

        return input_text

    def input_keyboard(self,disp_text):
        # Does the same function as input(disp_text)
        # displays the "disp_text" prompt and waits for keyboard input
        # This is a blocking read, ie the program will wait for input
        # a carriage return is required for the input to be processed
        input_text = ""

        # There seems to be an initial timing issue so running this
        # extra key_count seems to avoid random startup crashes
        try:
            self.__kbd.key_count
        except:
            print("Trouble on startup, waiting a bit",end="")
            for i in range(100000):
                if i % 10000 == 0:
                    print (".",end="")
            print()

        if disp_text != None:
            print(disp_text,end='')

        while self.__kbd.key_count == 0:
            pass

        k = self.__kbd.key
        loop = True
        time_Param = None
        while loop:
            if k != None:
                if k[0] == STATE_RELEASE:
                    if k[1] not in  '\n\x07\x11':
                        if k[1] == '\x08': # Backspace
                            if len(input_text) > 0:
                                input_text = input_text[:-1]
                                print(k[1]+" "+k[1],end="")
                        elif k[1] == '\x09': # Alt-Space toggles the Shift/Alt lock on or off
                            self.__shift_Lock = not self.__shift_Lock
                        elif k[1] == '\x7c': # Alt-Enter toggles between Shift & Alt for long press
                            if self.__shift_Mode == self.__SHIFT:
                                self.__shift_Mode = self.__ALT
                            else:
                                self.__shift_Mode = self.__SHIFT
                        else: # Anything else, we add to the text field
                            retKey = self.__process_key(k[1],time_Param)
                            input_text += retKey
                            time_Param = None
                            print(retKey,end="")
                    elif k[1] == '\x07': # F3 pressed
                        print(self.__lastCmdLine[len(input_text):],end="")
                        input_text += self.__lastCmdLine[len(input_text):]
                    elif k[1] == '\x11': # F2 Pressed
                        searchLoc = self.__lastCmdLine[len(input_text):].find(self.read_keyboard(1))
                        if searchLoc >= 0:
                            print(self.__lastCmdLine[len(input_text):len(input_text)+searchLoc],end="")
                            input_text += self.__lastCmdLine[len(input_text):len(input_text)+searchLoc]
                    else: # Enter pressed
                        print()
                        self.__lastCmdLine = input_text
                        loop = False
                elif k[0] == STATE_LONG_PRESS:
                    if k[1] not in '\x08\x09\x7c':
                        time_Param = STATE_LONG_PRESS
                        self.__process_key(k[1],time_Param)

            if loop:
                k = self.__kbd.key

        return input_text