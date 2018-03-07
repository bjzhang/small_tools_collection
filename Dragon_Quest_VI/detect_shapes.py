#!/usr/bin/env python
# reference from:
# https://www.pyimagesearch.com/2016/02/08/opencv-shape-detection/
# USAGE
# python detect_shapes.py --image shapes_and_colors.png

# import the necessary packages
import argparse
import imutils
import cv2
import numpy
import math

def detectSharp(c):
    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    if len(approx) == 4:
        return "rectangle"
    else:
        return "unknown"

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

linesP = cv2.HoughLinesP(thresh, 1, numpy.pi / 180, 50, None, 50, 10)

if linesP is not None:
    for i in range(0, len(linesP)):
        l = linesP[i][0]
#        print ('distance: ' + str(distance))
        l = l.astype("float")
        l *= ratio
        l = l.astype("int")
        a = numpy.array([l[0], l[1]])
        b = numpy.array([l[2], l[3]])
        distance = numpy.linalg.norm(a - b)
        if distance > 120:
            cv2.line(image, (l[0], l[1]), (l[2], l[3]), (0,0,0), 15, cv2.LINE_AA)

# loop over the contours
for c in cnts:
	shape = detectSharp(c)
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
            if proportion > 200000:
                print(str(min_point[0][0]) + ", " +  str(min_point[0][1]) + ", " + str(max_point[0][0]) + ", " + str(max_point[0][1]))
                crop = image[min_point[0][1]: max_point[0][1], min_point[0][0]: max_point[0][0]]
                cv2.imwrite("crop_" + str(min_point[0][1]) + "_" + str(max_point[0][0]) + ".png" , crop)
