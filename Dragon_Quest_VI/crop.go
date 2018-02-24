package main

import (
    "image"
    "gocv.io/x/gocv"
)

func main() {
    //ref: //<https://answers.unity.com/questions/1374912/how-to-crop-image-using-opencv.html>
    //need template matching: rect := image.Rect(0, 1730, 1440, 2225)
    rect := image.Rect(0, 77, 1440, 144)
    src := gocv.IMRead("crop.png", gocv.IMReadUnchanged)
    //Find this function in core.go in gocv
    dst := src.Region(rect)
    gocv.IMWrite("./result.png", dst)
}
