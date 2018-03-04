
package main

import (
    "bufio"
    "errors"
    "fmt"
    "gocv.io/x/gocv"
    "image"
    "log"
    "os/exec"
    "strconv"
    "strings"
)

/*
 * Position in the screen.
 */
type position struct {
    x int
    y int
}

/*
 * The button which could pressed
 */
type button map[string](position)

type scenario map[string](button)

var scenarios = scenario{
    "startFighting": {
        "fighting": {-1, -1},
        "escaping": {-1, -1},
    },
    "exitFighting": button{
        "exiting": {-1, -1},
    },
}

/*
 * Take snapshot in order to analysis it
 * Call adb commmand and store picture to file. Return the path of the file
 */
func snapshot()(pic string, err error) {
    fmt.Println("snapshot")
    cmd := exec.Command("/usr/local/bin/adb", "shell", "screencap", "-p", "/storage/sdcard0/bamvor/dq6.png")
    err = cmd.Run()
    if err != nil {
        fmt.Println("Command finished with error: %v", err)
        return "", err
    }
    cmd = exec.Command("adb", "pull", "/storage/sdcard0/bamvor/dq6.png")
    err = cmd.Run()
    if err != nil {
        fmt.Println("Command finished with error: %v", err)
        return "", err
    }
    cmd = exec.Command("adb", "shell", "rm", "/storage/sdcard0/bamvor/dq6.png")
    err = cmd.Run()
    if err != nil {
        fmt.Println("Command finished with error: %v", err)
        return "", err
    }
    return "dq6.png", nil
}

// rectangle := tryToGetMainDialog()
// crop(rectangle)
func tryToGetMainDialog(pic string) ([]int) {
	cmd := exec.Command("./detect_shapes.py", "--image", pic)
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}
	if err := cmd.Start(); err != nil {
		log.Fatal(err)
	}
	reader := bufio.NewReader(stdout)
	line, _, _ := reader.ReadLine()
	if err := cmd.Wait(); err != nil {
		log.Fatal(err)
	}
    if len(line) == 0 {
        log.Fatal(errors.New("line is empty"))
    }
	strs := strings.Split(string(line), ", ")
	array := make([]int, 4)
	for i := range array {
		array[i], _ = strconv.Atoi(strs[i])
	}
	return array
}

func crop(pic string, pos []int) gocv.Mat{
    //ref: //<https://answers.unity.com/questions/1374912/how-to-crop-image-using-opencv.html>
    //need template matching: rect := image.Rect(0, 1730, 1440, 2225)
    rect := image.Rect(pos[0], pos[1], pos[2], pos[3])
    src := gocv.IMRead(pic, gocv.IMReadUnchanged)
    //Find this function in core.go in gocv
    dst := src.Region(rect)
    gocv.IMWrite("./crop_result.png", dst)
    return src.Region(rect)
}

func locateFont(mat gocv.Mat) []string {
    files := make([]string,0)
    gray := gocv.NewMat()
    defer gray.Close()
    gocv.CvtColor(mat, gray, gocv.ColorBGRToGray)
    binary := gocv.NewMat()
    defer binary.Close()
    gocv.Threshold(gray, binary, 150, 255, gocv.ThresholdBinary)
    gocv.IMWrite("binary.png", binary)
//    fmt.Printf("%v, %v\n", mat.Rows(), mat.Cols())
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
        for j := 0; j < projection[i]; j++ {
            projection_mat.SetShortAt(i, j, 255)
        }
    }
    gocv.IMWrite("./projection_mat.png", projection_mat)

    fontMinHeight := 30
    projectionMin := 10
    projectionMargin := fontMinHeight
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
//            fmt.Printf("previous end is %v\n", prevEnd)
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
//            fmt.Printf("%v, %v, %v, %v\n", 0, start, mat.Cols(), end)
            rect := image.Rect(0, start, mat.Cols(), end)
            //Find this function in core.go in gocv
            dst := mat.Region(rect)
            filename := "result_" + strconv.Itoa(start) + "_" + strconv.Itoa(end) + ".png"
            files = append(files, filename)
            gocv.IMWrite(filename, dst)
        }
    }
    return files
}

func getText(file string) string {
	cmd := exec.Command("tesseract", file, "stdout", "-l", "chi_sim", "--psm", "7")
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		log.Fatal(err)
	}
	if err := cmd.Start(); err != nil {
		log.Fatal(err)
	}
	reader := bufio.NewReader(stdout)
    var lines string
    for true {
        line, err := reader.ReadString('\n')
        lines += line
        if err != nil {
            break
        }
    }
	if err := cmd.Wait(); err != nil {
		log.Fatal(err)
	}
    return lines
}

/*
 * Get the scenario from the picture.
 * Get the current scenario from the picture and save the button position to
 * such scenario
 */
func getScenario(pic string)(name string, err error) {
    fmt.Println("getScenario: ", pic)
    pos := tryToGetMainDialog(pic)
    dialog := crop(pic, pos)
    files := locateFont(dialog)
    for _, value := range files {
        fmt.Println(getText(value))
    }
    name = "startFighting"
    switch name {
    case "startFighting":
        scenarios[name]["fighting"] = position{0, 1}
        scenarios[name]["escaping"] = position{0, 2}
    case "exitFighting":
        scenarios[name]["exiting"] = position{1, 1}
    }
    return name, nil
}

/*
 * Do the process according to the previous and current scenario
 */
func process(current string, previous string)(err error) {
    fmt.Println("process: ", current, previous)
    click(scenarios[current]["fighting"])
    return nil
}

func click(pos position) {
    fmt.Println("Click: ", pos)
}

func printScenario(s scenario) {
    fmt.Printf("%v\n", s)
}

func printScenarioByName(name string) {
    fmt.Println(scenarios[name])
}

//printScenarios(scenario)
func printScenarios(ss scenario) {
    for key, value := range ss {
        fmt.Printf("%v: %v\n", key, value)
    }
}

//printPos("startFighting", "fighting")
func printPos(scnr string, bttn string) {
    fmt.Printf("%v: %v: %v\n", scnr, bttn, scenarios[scnr][bttn])
}

func main() {
    var prev string = ""

    for true {
        printScenarios(scenarios)
        pic, err := snapshot()
        if err != nil {
            panic(err)
        }
        cur, err := getScenario(pic)
        if err != nil {
            panic(err)
        }
        err = process(cur, prev)
        if err != nil {
            panic(err)
        }
        prev = cur
        break
    }
}

