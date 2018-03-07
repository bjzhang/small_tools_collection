
package main

import (
    "fmt"
    "gocv.io/x/gocv"
    "image"
    "log"
    "os"
    "strconv"
)

//drawProjection() {
//    mat := gocv.NewMatWithSize(100, 100, gocv.MatTypeCV16S)
//    for i:= 0; i< 100; i++ {
//        mat.SetShortAt(50, i, 255)
//    }
//    gocv.IMWrite("./test.png", mat)
//}

func proj(binary gocv.Mat, rootName string) {
    projection := make([]int, binary.Cols())
    fmt.Printf("Row<%v>, Col<%v>\n", binary.Rows(), binary.Cols())
    for i := 0; i < binary.Rows(); i++ {
        for j := 0; j < binary.Cols(); j++ {
            point := binary.GetUCharAt(i, j)
            if point == -1 {
                projection[j]++
            }
        }
    }
    projection_mat := gocv.NewMatWithSize(binary.Rows(), binary.Cols(), gocv.MatTypeCV16S)
    for i := 0; i < binary.Cols(); i++ {
        for j := 0; j < projection[i]; j++ {
            projection_mat.SetShortAt(j, i, 255)
        }
    }
    gocv.IMWrite("./projection_mat_" + rootName + ".png", projection_mat)
    fontMin := 30
    skipMax := fontMin
    for i := 0; i < binary.Cols(); i++ {
    //for i := 724; i < 892; i++ {
        start := i
        j := i
        skip := 0
        projection_count := 0
        for ; j < binary.Cols(); j++ {
        //for ; j < 892; j++ {
            if projection[j] > 0 {
                projection_count++
                skip = 0
            } else if projection[j] == 0 && projection_count != 0 && skip < skipMax {
                skip++
            } else {
                break
            }
        }
        end := j
        if projection_count > fontMin {
            i = end
            fmt.Printf("%v, %v, %v, %v\n", start, 0, end, binary.Rows())
            rect := image.Rect(start, 0, end, binary.Rows())
            //Find this function in core.go in gocv
            dst := binary.Region(rect)
            filename := rootName + "_result_" + strconv.Itoa(start) + "_" + strconv.Itoa(end) + ".png"
            gocv.IMWrite(filename, dst)
        }
    }
}

func main() {
    mat := gocv.IMRead(os.Args[1], gocv.IMReadUnchanged)
    if mat.Empty() {
        log.Fatal("Invalid file name")
    }
    gray := gocv.NewMat()
    defer gray.Close()
    gocv.CvtColor(mat, gray, gocv.ColorBGRToGray)
    binary := gocv.NewMat()
    defer binary.Close()
    gocv.Threshold(gray, binary, 120, 255, gocv.ThresholdBinary)
    gocv.IMWrite("binary.png", binary)
    fmt.Printf("%v, %v\n", mat.Rows(), mat.Cols())
    projection := make([]int, mat.Rows())
    for i := 0; i < mat.Rows(); i++ {
        for j := 0; j < mat.Cols(); j++ {
            point := binary.GetUCharAt(i, j)
            if point == -1 {
                projection[i]++
            }
        }
//        fmt.Printf("%v\n", projection[i])
    }
    projection_mat := gocv.NewMatWithSize(mat.Rows(), mat.Cols(), gocv.MatTypeCV16S)
    for i := 0; i < mat.Rows(); i++ {
        if i < 10 {
            fmt.Println(projection[i])
        }
        for j := 0; j < projection[i]; j++ {
            projection_mat.SetShortAt(i, j, 255)
        }
    }
    gocv.IMWrite("./projection_mat.png", projection_mat)

    fontMinHeight := 30
    projectionMin := 10
    projectionMargin := fontMinHeight / 2
    skipMax := 10
    for i := 0; i < mat.Rows() - fontMinHeight; i++ {
        cont := 0
        skip := 0
        for j := i; j < i + fontMinHeight; j++ {
            if projection[j] > projectionMin {
                cont++
            } else if skip < skipMax {
                cont++
                skip++
            }
        }
        if cont < fontMinHeight {
            projection[i] = 0
        }
    }
    projection_mat_final := gocv.NewMatWithSize(mat.Rows(), mat.Cols(), gocv.MatTypeCV16S)
    for i := 0; i < mat.Rows(); i++ {
        for j := 0; j < projection[i]; j++ {
            if projection[i] >= projectionMin  {
                projection_mat_final.SetShortAt(i, j, 255)
            }
        }
    }
    gocv.IMWrite("./projection_mat_final.png", projection_mat_final)
    prevEnd := 0
    for i := 0; i < mat.Rows(); i++ {
        start := i
        skip := 0
        j := i
        for ; j < mat.Rows(); j++ {
            if projection[j] >= projectionMin {
                continue
            } else if skip < skipMax {
                skip++
                continue
            } else {
                break
            }
        }
        end := j
//        fmt.Printf("start: %v, end: %v\n", start, end)
        if end - start > fontMinHeight {
            i = j
            fmt.Printf("previous end is %v\n", prevEnd)
            start = start - projectionMargin
            if start < 0 {
                start = 0
            }
            if start < prevEnd {
                start = prevEnd
            }
            end = end + projectionMargin
            if end > mat.Rows() {
                end = mat.Rows()
            }
            prevEnd = end
            fmt.Printf("%v, %v, %v, %v\n", 0, start, mat.Cols(), end)
            rect := image.Rect(0, start, mat.Cols(), end)
            //Find this function in core.go in gocv
            dst := binary.Region(rect)
            filename := "result_" + strconv.Itoa(start) + "_" + strconv.Itoa(end) + ".png"
            proj(dst, filename)
            gocv.IMWrite(filename, dst)
        }
    }
}
