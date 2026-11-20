# 2026_03_01
# Interactive program to solicit selection of an image from a directory of images.  Selection is made
# by index.  This index value is transmitted by network to a selected controller for one or more projectors.
# Program cycles:  identify a projector controller to communicate with followed by identification of an image index
# to send.
# It's assumed that this software and software for projector controllers are working from directories with
# same contents.


import socket
import time
import os

# These socket setups should be modified to match intended operating environments.  Each socket is assumed to
# be for the network address of a processor receiving commands (indices) from this program to use for displaying
# selected images.
Controller01_ADDR = ('192.168.3.103', 12345)
Controller01_REMOTE = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

Controller02_ADDR = ('192.168.3.107', 12345)
Controller02_REMOTE = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

Controller03_ADDR = ('192.168.3.108', 12345)
#Controller03_ADDR = ('127.0.0.1', 12345)  # useful for testing on same computer as manager
Controller03_REMOTE = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

Controllers = [[Controller01_REMOTE, Controller01_ADDR],[Controller02_REMOTE,Controller02_ADDR],\
               [Controller03_REMOTE,Controller03_ADDR]]

# Path values in this list should be modified to represent where images are stored locally for the
# three different projector controllers.
pathPrefixes = ['./ImagesController01/',\
                './ImagesController02/',\
                './ImagesController03/']

while True:
    # Ask user for projector controller ID
    c='a'
    while not(c.isnumeric() and 1 <= int(c) <= 3):
        c=input('\n\nChoose a Controller, 1-3: ')

    imagesList = os.listdir(pathPrefixes[int(c)-1])  ## get latest copy of directory --could be changing
    imagesList.sort()
    # Print list of images with index for user
    for i in range(len(imagesList)):
        print(str(i) + ':   ' + str(imagesList[i]))
    # get user selection of image by index.
    index=input('\nSelect an image by index: ')
    if index.isnumeric() and ((0 <= int(index) < len(imagesList)) or int(index) == 9999):
        try:
            Controllers[int(c)-1][0].sendto(bytes(index.encode("utf-8")), Controllers[int(c)-1][1])  # Send
            if int(index) != 9999:
                print('\nSent Controller ' + str(c) + ':  ' + str(imagesList[int(index)]))
        except:
            print('\nFailed to send Controller ' + c + ':  ' + str(imagesList[int(index)]))

        
    
