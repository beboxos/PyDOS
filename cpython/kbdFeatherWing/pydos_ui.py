from bbq10keyboard import BBQ10Keyboard, STATE_PRESS, STATE_RELEASE, STATE_LONG_PRESS
import board

import adafruit_ili9341
import digitalio
import displayio



class PyDOS_UI:

    def __init__(self):
        # Release any resources currently in use for the displays
        displayio.release_displays()

        tft_cs = board.D9
        tft_dc = board.D10
        display_bus = displayio.FourWire(board.SPI(), command=tft_dc, chip_select=tft_cs)
        display = adafruit_ili9341.ILI9341(display_bus, width=320, height=240)

        self.__kbd = BBQ10Keyboard(board.I2C())

        self.__contrl_seq = []

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
        while loop:
            if k != None:
               if k[0] == STATE_RELEASE:
                    if k[1] != '\n':
                        if k[1] == '\x08': # Backspace
                            if len(input_text) > 0:
                                input_text = input_text[:-1]
                                print(k[1]+" "+k[1],end="")
                        elif k[1] == '\x60': # change speaker symbol to equal sign
                            input_text += "="
                            print("=",end="")
                        else: # Anything else, we add to the text field
                            input_text += k[1]
                            print(k[1],end="")
                    else:
                        print()
                        loop = False

            if loop:
                k = self.__kbd.key

        return input_text