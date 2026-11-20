
#  Written by Paul Reynolds  2025 12 23
# I realized the pix values needed to be normalized to 255.  I hadn't been doing that.  It's only needed if a != 1.0.
# I've removed "a" from the computation of pix because nolmalization turned out to be nothing more then multiplying
# pix by 1/a.  Since there is an "a" term in Bourke's original formula, multiplyuing by 1/a was a waste of time.
# So I removed the "a" from the formula for pix, which guarantees that in all cases 0 <= pix <== 255.
# I'm now confused by Bourke's introduction of "a" in the first place.
# If Bourke's formula should instead be (a*2*x) ^ p  rather than a* (2*x)^p then normalization involving something
# other than "a" would be required.
### On further inquiry I find "a" to be practically useless.  If it's greater tahn one then then a blend has to be scaled by
### 1/a.  That's a worthless revrsal of multiplying by a.  If "a" is put inside exponentiation then when scaling by the
### largest value produced you get the same curve as if "a" were one.

### Best values for "a", "p" and gamma hover around, 1.0, 0.41 and 1.0.  Some image blended come out a little too light and
### others come out a little too dark, necessitating some small increment explorations.


import cv2
import numpy as np
from PIL import Image
import math
import os
import shutil

def adjust_gamma(image, gamma=1.0):
    """Applies gamma correction to an image."""
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)



######################################### Empty target directory #################################


outputPath = "/home/paul/Desktop/ModelTrains/Projection/AllImages/03_blendedImages/Proj03/"
try:
    shutil.rmtree(outputPath)
    print(f"Directory '{outputPath}' and all its contents deleted.")
except FileNotFoundError:
    print(f"Directory '{outputPath}' not found, skipping deletion.")
except Exception as e:
    print(f"Error deleting directory: {e}")
try:
    os.makedirs(outputPath) # Use os.makedirs() to handle potential parent directory creation if needed
    print(f"Directory '{outputPath}' recreated.")
except FileExistsError:
    print(f"Directory '{outputPath}' already exists after deletion attempt.")
except Exception as e:
    print(f"Error creating directory: {e}")

###################################### Main loop to make belnded inmages from source images ####################

lista = [1.0]
listp = [0.35, 0.38, 0.41, 0.45]  # 0.41 isnt bad either.  Its a tossup
listg = [1.0]  #  Most settings need a little gamma boost
    
for j in range(len(lista)):  #  number of parameter studies to conduct
    for jj in range(len(listp)):
        for jjj in range(len(listg)):
            a = lista[j]
            p = listp[jj]
            gamma_value = listg[jjj]
            
            ##################################################### Make Blend mask ######################

            # Create 1280x1080 blank mask (all white initially) with 3 channels (BGR) and 8-bit unsigned integers
            # Shape is (height, width, channels)
            # Then apply Paul Bourke approach to create actual mask
            # The ratio of initial image width to total blend mask width is 4.5
            mask = np.zeros((1080, 1280, 3), np.uint8)
            mask[:, :, :] = 255  #  255 makes it white
            blendWidth = 1280  #  two times the width of an overlapped region
            halfBlendWidth = int(blendWidth/2)
            MAXPix = 0
            # Build the mask using a and p as parameters
            for x in range(halfBlendWidth):
                xNormal = x/blendWidth
                pix = int((math.pow((2*xNormal), p) * 255))
                if pix > MAXPix:  MAXPix = pix
 #               if pix > 230: pix = pix - int((pix - 230) / 5.0)
                if pix > 255: pix = 255
                color = (pix, pix, pix) 
                thickness = 1
                cv2.line(mask, (halfBlendWidth-x, 0), (halfBlendWidth-x, 1080), color, thickness)
                cv2.line(mask, (halfBlendWidth+x, 0), (halfBlendWidth+x, 1080), color, thickness)    
                mask_float = mask.astype(np.float32)  # For use when doing multiply blend
            print("MAXPix is: " + str(MAXPix) + "__" + f"{a:.2f}" +"_" + f"{p:.2f}" +"_" + f"{gamma_value:.2f}" )



            splitPoint = 1920  #  four projectors
            inputPath = "/home/paul/Desktop/ModelTrains/Projection/AllImages/02_croppedResizedimages/"
            imagesList = os.listdir(inputPath)  ## get latest copy of directory --could be changing
            imagesList.sort()

            for ii in range(len(imagesList)):
                file = imagesList[ii]
                if file[0:7] != "keepers":
                    print("Just read: " + imagesList[ii]) 
                    baseImage = cv2.imread(inputPath + file)  #  a 5760 by 1080 image

                    ####################################### Extract and Concatenate #######################

                    ## Make appended_image a 7680x1080 image with three embedded overlapped panels
                    appended_image = cv2.hconcat([baseImage[0 : 1080, 0 : 1920], baseImage[0 : 1080, 1280 : 3200]])
                    appended_image = cv2.hconcat([appended_image, baseImage[0 : 1080, 2560 : 4480]])
                    appended_image = cv2.hconcat([appended_image, baseImage[0 : 1080, 3840 : 5760]])

                    ######################################### Blend in mask ###############################

                    segments = 3  # number of overlapped blended regions to produce
                    for k in range(segments):
                        ROI = appended_image[0:1080, k*1920+1280:k*1920+2560]
                        floatROI = ROI.astype(np.float32)
                        #Blend overlapped region with mask
                        resultFloat = cv2.multiply(floatROI  , mask_float, scale=1/255.0)
                        # Convert the blended result back to 8-bit unsigned integer
                        eightBit = cv2.convertScaleAbs(resultFloat)
                        #Do gamma correction
                        corrected_roi = adjust_gamma(eightBit, gamma=gamma_value)
                        #Restore into chosen section in appended_image
                        appended_image[0:1080, k*1920+1280:k*1920+2560] = corrected_roi
                    # The image is currently 7680 x 1080.  Remove second half of width and attach
                    #it under the first half, making a 4k image:  3840x2160
                    
                    displayImage = cv2.vconcat ([appended_image[0:1080, 0:3840],\
                                                appended_image[0:1080, 3840:7680]])

                    displayImage = cv2.cvtColor(displayImage, cv2.COLOR_BGR2RGB) # BGR -> RGB

    ##                text = str(a) +"_" + f"{p:.2f}" +"_" + str(gamma_value )
    ##                cv2.putText(appended_image, text, (3300, 1900), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,0,0), 2, cv2.LINE_AA)

                    displayImage_rgb = Image.fromarray(displayImage, 'RGB') # 'RGB' for color

                    displayImage_rgb.save(outputPath + file[:file.find("-")] +\
                         "__" + str(a) +"_" + f"{p:.2f}" +"_" + str(gamma_value ) + "_blended.jpg")




























############################################### Blend two halves --addWeighted ##########################

### Ensure images have the same dimensions if blending directly
### (or define a region of interest for blending)
### Example: Resize img2 to match img1
### img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
##
### Define alpha weights
##alpha = 0.5 # Weight for img1
##beta = 1.0 - alpha # Weight for img2
##
### Perform linear blending
##blended_img = cv2.addWeighted(img1, alpha, img2, beta, 0.0)
##
##cv2.imshow('Linear Blended Image', blended_img)
##cv2.waitKey(0)
##cv2.destroyAllWindows()






############################################### Blend two halves --multiply ##########################

##
### Ensure images have the same dimensions and number of channels
##if img1.shape != img2.shape:
##    print("Error: Images must have the same dimensions and number of channels.")
##else:
##    # Perform image multiplication
##    # The result will be saturated (values capped at 255 for uint8 images)
##    result_img = cv2.multiply(img1, img2, scale=1/255.0) # Scale is important for normalization
##
##    # Display the original and resulting images
##    cv2.imshow('Image 1', img1)
##    cv2.imshow('Image 2', img2)
##    cv2.imshow('Multiplied Image', result_img)
##
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()




###================================================================
###append

##
### Horizontally concatenate the images
##appended_image_horizontal = cv2.hconcat([img1, img2])

##
##


###================================================================
###extract
##
##import cv2
##
### Load the image
##img = cv2.imread('your_image.jpg')
##
### Define the coordinates for the Region of Interest (ROI)
### y_start, y_end: row indices (height)
### x_start, x_end: column indices (width)
##x_start, y_start = 100, 50  # Top-left corner (x, y)
##width, height = 200, 150    # Width and height of the ROI
##
##cropped_img = img[y_start : y_start + height, x_start : x_start + width]
##
### Display the original and cropped images
##cv2.imshow('Original Image', img)
##cv2.imshow('Cropped Image', cropped_img)
##cv2.waitKey(0)
##cv2.destroyAllWindows()
##
##
##
##
###================================================================
###blend  addweighted with gamma
##
##    # Ensure images have the same dimensions if blending directly
##    # (or define a region of interest for blending)
##    # Example: Resize img2 to match img1
##    # img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
##
##    # Define alpha weights
##    alpha = 0.5 # Weight for img1
##    beta = 1.0 - alpha # Weight for img2
##
##    # Perform linear blending
##    blended_img = cv2.addWeighted(img1, alpha, img2, beta, 0.0)
##
##    cv2.imshow('Linear Blended Image', blended_img)
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()



### ==============================================================
#Another blending - bitwise
##    import cv2
##    import numpy as np
##
##    img1 = cv2.imread('background.jpg')
##    img2 = cv2.imread('foreground.png', cv2.IMREAD_UNCHANGED) # Load with alpha channel
##
##    # Create a mask from the alpha channel of the foreground image
##    mask = img2[:, :, 3] 
##    img2_rgb = img2[:, :, :3] # Extract RGB channels
##
##    # Resize foreground image and mask to match background if needed
##    # img2_rgb = cv2.resize(img2_rgb, (img1.shape[1], img1.shape[0]))
##    # mask = cv2.resize(mask, (img1.shape[1], img1.shape[0]))
##
##    # Invert the mask for the background
##    mask_inv = cv2.bitwise_not(mask)
##
##    # Black out the area of the foreground in the background
##    background_masked = cv2.bitwise_and(img1, img1, mask=mask_inv)
##
##    # Take only the foreground region from the foreground image
##    foreground_masked = cv2.bitwise_and(img2_rgb, img2_rgb, mask=mask)
##
##    # Combine the masked images
##    blended_image = cv2.add(background_masked, foreground_masked)
##
##    cv2.imshow('Blended Image', blended_image)
##    cv2.waitKey(0)
##    cv2.destroyAllWindows()




###=======================================================================
#alpha channel blending
# For images with an alpha channel (like PNGs), you can directly use the alpha channel for transparency
# when overlaying. This often involves creating a mask from the alpha channel and applying it.
#Libraries like cvzone simplify this process.


##import cv2
##import cvzone # You might need to install cvzone: pip install cvzone
##
### Load background and foreground PNG with alpha channel
##background_img = cv2.imread("background.jpg")
##foreground_img_alpha = cv2.imread("foreground.png", cv2.IMREAD_UNCHANGED)
##
### Define position for overlay
##pos = (100, 50)
##
### Overlay using cvzone.overlayPNG
##overlayed_img = cvzone.overlayPNG(background_img, foreground_img_alpha, pos)
##
##cv2.imshow("Overlayed PNG", overlayed_img)
##cv2.waitKey(0)
##cv2.destroyAllWindows()


##########################################################################################
##cv2 multiply example
##import cv2
##import numpy as np
##
### Load two images (ensure they have the same dimensions and type)
##img1 = cv2.imread('image1.png', cv2.IMREAD_GRAYSCALE)
##img2 = cv2.imread('image2.png', cv2.IMREAD_GRAYSCALE)
##
##        # Convert images to float32 to avoid saturation if necessary
##        img1_float = img1.astype(np.float32)
##        img2_float = img2.astype(np.float32)
##
##        # Perform element-wise multiplication
##        # Optional: Add a scale factor (e.g., 0.5)
##        result_float = cv2.multiply(img1_float, img2_float, scale=1/255.0) 
##        # The scale of 1/255.0 is often used when multiplying two 8-bit images 
##        # to normalize the result before converting back to 8-bit, preventing overflow.
##
##        # Convert the result back to 8-bit unsigned integer for display
##        result_8bit = cv2.convertScaleAbs(result_float) 
##        # Or, if no scaling was used and you expect values within 0-255:
##        # result_8bit = cv2.multiply(img1, img2) 
##




### =============================================================
#Pyramids
# This method is more complex and involves multiple steps of building and collapsing pyramids.
# Refer to OpenCV documentation or tutorials on "Image Pyramid Blending" for a detailed implementation.


















