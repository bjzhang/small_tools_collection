
package main

import (
    "fmt"
    "gocv.io/x/gocv"
    "image"
    "log"
    "strconv"
)

//drawProjection() {
//    mat := gocv.NewMatWithSize(100, 100, gocv.MatTypeCV16S)
//    for i:= 0; i< 100; i++ {
//        mat.SetShortAt(50, i, 255)
//    }
//    gocv.IMWrite("./test.png", mat)
//}

func main() {
    mat := gocv.IMRead("./thresh.png", gocv.IMReadUnchanged)
    if mat.Empty() {
        log.Fatal("Invalid file name")
    }
    fmt.Printf("%v, %v\n", mat.Rows(), mat.Cols())
    projection := make([]int, mat.Rows())
    for i := 0; i < mat.Rows(); i++ {
        for j := 0; j < mat.Cols(); j++ {
            point := mat.GetUCharAt(i, j)
//            if point != 0 {
//                fmt.Printf("%v\n", point)
//            }
            if point == -1 {
                projection[i]++
            }
        }
//        fmt.Printf("%v\n", projection[i])
    }
    projection_mat := gocv.NewMatWithSize(mat.Rows(), mat.Cols(), gocv.MatTypeCV16S)
    for i := 0; i < mat.Rows(); i++ {
        for j := 0; j < projection[i]; j++ {
            projection_mat.SetShortAt(i, j, 255)
        }
    }
    gocv.IMWrite("./projection_mat.png", projection_mat)

    fontMinHeight:= 5
    for i := 0; i < mat.Rows() - fontMinHeight; i++ {
        cont := 0
        for j := i; j < i + fontMinHeight; j++ {
            if projection[j] > 3 {
                cont++
            }
        }
        if cont < fontMinHeight {
            projection[i] = 0
        }
    }
    projection_mat_final := gocv.NewMatWithSize(mat.Rows(), mat.Cols(), gocv.MatTypeCV16S)
    for i := 0; i < mat.Rows(); i++ {
        for j := 0; j < projection[i]; j++ {
            if projection[i] > 5 {
                projection_mat_final.SetShortAt(i, j, 255)
            }
        }
    }
    gocv.IMWrite("./projection_mat_final.png", projection_mat_final)
    for i := 0; i < mat.Rows(); i++ {
        start := i
        j := i
        for ; j < mat.Rows(); j++ {
            if projection[j] < 5 {
                break
 //           } else {
 //               fmt.Printf("%v: %v\n", j, projection[j])
            }
        }
        end := j
//        fmt.Printf("start: %v, end: %v\n", start, end)
        if end - start > fontMinHeight {
            i = j
            fmt.Printf("%v, %v, %v, %v\n", start, 0, end, mat.Cols())
            rect := image.Rect(0, start, mat.Cols(), end)
            //Find this function in core.go in gocv
            dst := mat.Region(rect)
            filename := "result_" + strconv.Itoa(start) + "_" + strconv.Itoa(end) + ".png"
            gocv.IMWrite(filename, dst)
        }
    }
}
