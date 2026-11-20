# 2026_03_01

# PURPOSE: to receive commands over a network connection comprising a single integer for selecting an image to display
# from a local "./ImagesController0X" directory (1 <= X <= 3).  Integer 9999 commands shutting down.

# Assume:
#   Directory of 4k images
#   Local file named "Iam" containing single integer identifying this software's ID
#   Available network for receiving integers identifying index of next image to project

# Output one 4k image at a time based on receipt of index specifying which image to project
#
# This software currently runs on an Ubuntu based miniPC.  With small mods it has run on a
# Raspberry Pi 4 running Raspberry Pi O.S. RPi was found to run too slow (5 seconds to display selected 4k image)
# With some mods this software could run on any computer that supports Python using ImageTK.

# This software is set up to serve any of three different instances of projectors, depending on the
# value found in Iam.txt" file.  This value is assigned to variable myID.

# Check for active DISPLAY environment variable supports this code being started on boot-up.
#  Sometimes DISPLAY is not ready yet when this code is first started up.

# Note: Settled on using ImageTk after encountering failures with VLC and OpenCV for doing the displays.  Ran into
# runtime issues regarding libraries and segmentation faults.  Also, couldn't get decent full screen display
# working with either.


import os
import sys
import socket
import threading
import time

DEBUG = False
stopProgram = threading.Event()  #  Set when 9999 is received on input
inBound = ''  # buffer for incoming index values selecting which image to display

myID = 3      # Default for identifier expected to be in local file Iam.txt.

# Value of myID determines source directory for images to be projected.
pathPrefixes=['/home/paul/Desktop/executeMe/ImagesController01/',\
              '/home/paul/Desktop/executeMe/ImagesController02/',\
              '/home/paul/Desktop/executeMe/ImagesController03/']

# Separate thread that listens for inputs on UDP socket "receiveSocket".  Any values received
# are appended to string variable "inbound".  Assumption is that "inBound" contents are processed elsewhere
# in separate thread.
# This thread is a standard producer in a producer/consumer scenario.
class ListenToMaster(threading.Thread):
    def run(Self):
        global inBound, receiveSocket, event, stopProgram, DEBUG
        if DEBUG: print('Master UDP listening thread started.')
        receiveSocket.settimeout(6)
        masterInput = ''
        while not stopProgram.is_set():
            try:
                masterInput, address = receiveSocket.recvfrom(4096)  # Try to read from master
                masterInput = masterInput.decode("utf-8").lstrip().rstrip('\n\r')
                if len(masterInput) > 0 and DEBUG:
                   print('\nListener received >' + masterInput + "<", flush = True)
            except:
                pass
            #  Only accept numeric inputs
            if len(masterInput) >0 and masterInput.isnumeric():
                # Separate inputs by "#" in case multiple arrive in quick succession
                inBound += masterInput + "#"
                if DEBUG:
                    print('\ninBound set to >' + inBound + "<", flush = True)
                masterInput = ''
        print("Master terminating")

# Continuous looping process that checks object "inBound" for new requests.
# Requests are integers meant to represent index of image to display.
# Display uses a TK label to display selected image.
# Process terminates if event variable "stopProgram" is set or input "9999" is received.
def updateImage():
    global inBound, stopProgram, DEBUG, label, myID
#    print("In updateImage")
    if not stopProgram.is_set():
        if inBound:  # Request to display an image has arrived
            # Refresh and sort directory of images.  Allows for dynamic updating of
            # contents of image directory.
            imageNamesList = os.listdir(pathPrefixes[myID-1])
            imageNamesList.sort()
            # Pick off first request and its trailing "#" from inBound, preserving other requests for later.
            # There's a possible race condition with the setting of inBound in the ListenToMaster thread
            # that I'm ignoring because it's of little consequence if it occurs.  A lock or event variable
            # could be used to prevent the race condition.

            commandString = inBound.partition("#")[0]
            inBound = inBound.partition("#")[2]
            if commandString and commandString.isnumeric():
                index = int(commandString)
                if index >=0 and index < len(imageNamesList):
                    newImage = Image.open(pathPrefixes[myID-1] + imageNamesList[index])
                    photo = ImageTk.PhotoImage(newImage)
                    image_label.configure(image = photo)
                    image_label.image = photo
                else:
                    if index == 9999:
                        stopProgram.set()
                        root.destroy()
        root.after(500, updateImage)
    else:
        print("UpdateImage is stopped")


def wait_for_display(timeout=30):
#   Waits for the $DISPLAY environment variable to be set.
    start_time = time.time()
    while not os.environ.get("DISPLAY"):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for $DISPLAY variable to be set after {timeout} seconds")
        if DEBUG:
            print("Waiting for $DISPLAY environment variable...", file=sys.stderr)
        time.sleep(1) # Wait for 1 second before checking again  
#    print(f"$DISPLAY is set to: {os.environ['DISPLAY']}")




if __name__ == '__main__':
    
    try:
        wait_for_display(timeout=90)
        # If DISPLAY variable is found to be set then proceed with setting up foundation
        # for displaying requested images.
        import tkinter as tk
        from tkinter import *
        import tkinter.font as font
        from PIL import ImageTk, Image, ImageOps
    except TimeoutError as e:
        print(e)
        sys.exit(1)
    
    try:
        # Set up a UDP socket for receiving image display requests
        localReceive = ('', 12345)
        receiveSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiveSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  ## Drop socekt quickly 
        receiveSocket.bind(localReceive)
    except:
        with open("/home/paul/Desktop/executeMe/errorlog.txt", "w") as errorLog:
            errorLog.write("Failed to open socket")
        print("Cant open socket")
        sys.exit()

    masterLISTEN = ListenToMaster()  
    masterLISTEN.start()  #Start up thread listening for display requests
    root = tk.Tk()
    # We're working with 4k images
    screen_width=3840
    screen_height=2160
    # Operations to keep display manager well behaved
#    root.wm_overrideredirect(True)
    root.attributes('-fullscreen', True)
    root.bind('<Escape>', lambda e: root.destroy())
    inBound = ''
    # Get myID, to determine which directory to pull images from
    try: 
        with open('/home/paul/Desktop/executeMe/Iam', 'r') as IamMe:
            myID = int(IamMe.read())
    except:
        print('I have no identity')
        sys.exit()
    # Initially set display to black
    fileToOpen = pathPrefixes[myID-1] + 'Black_3840_2160_blended.jpg'
    pil_image = Image.open(fileToOpen)
    pil_image=pil_image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(pil_image)
    # Uses a TK label to display the 4k image.
    image_label = tk.Label(root, image = photo, bg='black')
    image_label.pack(fill=tk.BOTH, expand=True)
    image_label.image = photo
    updateImage()
    try:
        root.mainloop()
    except:
        root.destroy()
        sys.exit()
    masterLISTEN.join()
    receiveSocket.close()
    sys.exit()


