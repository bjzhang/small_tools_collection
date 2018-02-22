# reference from:
# https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/
# USAGE
# python detect_shapes.py --image shapes_and_colors.png

# import the necessary packages
from pyimagesearch.shapedetector import ShapeDetector
import argparse
import imutils
import cv2
import numpy
import math

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
	help="path to the input image")
args = vars(ap.parse_args())

# load the image and resize it to a smaller factor so that
# the shapes can be approximated better
image = cv2.imread(args["image"])
resized = imutils.resize(image, width=300)
ratio = image.shape[0] / float(resized.shape[0])

# convert the resized image to grayscale, blur it slightly,
# and threshold it
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
cv2.imwrite("thresh.png", thresh)

# find contours in the thresholded image and initialize the
# shape detector
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
	cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]
sd = ShapeDetector()

# loop over the contours
for c in cnts:
	shape = sd.detect(c)
        if shape == "rectangle":
            # multiply the contour (x, y)-coordinates by the resize ratio,
            # then draw the contours and the name of the shape on the image
            c = c.astype("float")
            c *= ratio
            c = c.astype("int")
#            cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
#            cv2.putText(image, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
#                    0.5, (255, 255, 255), 2)

            count = 0
            zero = numpy.array([0, 0])
            min_distance = numpy.linalg.norm(c[0] - zero)
            max_distance = min_distance
            min_point = c[0]
            max_point = min_point
            while count < c.size / 2:
                distance = numpy.linalg.norm(c[count] - zero)
                if min_distance > distance:
                    min_distance = distance
                    min_point = c[count]
                if max_distance < distance:
                    max_distance = distance
                    max_point = c[count]

                count += 1

            proportion = math.fabs(max_point[0][0] - min_point[0][0]) * math.fabs(max_point[0][1] - min_point[0][1])
            if proportion > 100000:
                print(proportion)

