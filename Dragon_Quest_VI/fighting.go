package main

import (
	"bufio"
	"bytes"
	"fmt"
	"image"
	"log"
	"os/exec"
	"strconv"
	"strings"

    "gocv.io/x/gocv"
)

func click(x, y int) bool {
	cmd := exec.Command("adb", "shell", "input", "tap", strconv.Itoa(x), strconv.Itoa(y))
	//fmt.Println("Running adb input tap and waiting for it to finish...")
	err := cmd.Run()
	if err != nil {
		fmt.Println("Command finished with error: %v", err)
		return false
	}
	return true
}

// rectangle := try_to_get_main_dialog()
// crop(rectangle)
func try_to_get_main_dialog() ([]int) {
	cmd := exec.Command("./detect_shapes.py", "--image", "dq6.png")
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
	strs := strings.Split(string(line), ", ")
	array := make([]int, 4)
	for i := range array {
		array[i], _ = strconv.Atoi(strs[i])
	}
	return array
}

func test_and_start_fighting() bool {
	var result bool

	src := gocv.IMRead("dq6.png", gocv.IMReadUnchanged)
	//ref: //<https://answers.unity.com/questions/1374912/how-to-crop-image-using-opencv.html>
	//need template matching: rect := image.Rect(0, 1730, 1440, 2225)
	rect := image.Rect(0, 1860, 1440, 2225)
	//Find this function in core.go in gocv
	dst := src.Region(rect)
	golden := gocv.IMRead("golden_fighting.png", gocv.IMReadUnchanged)
	dst_bytes := dst.ToBytes()
	golden_bytes := golden.ToBytes()
	ret := bytes.Compare(dst_bytes, golden_bytes)
//	fmt.Println("bytes compare result: %v", ret)
	if ret != 0 {
		return false
	}

	fmt.Println("In fighting senario.")
	result = click(130, 1800)
	if !result {
		return result
	}
	result = click(130, 1800)
	if !result {
		return result
	}
	result = click(130, 1800)
	if !result {
		return result
	}
	return true
}

func test_and_check_fighting_result() bool {
	var result bool

	src := gocv.IMRead("dq6.png", gocv.IMReadUnchanged)
	//ref: //<https://answers.unity.com/questions/1374912/how-to-crop-image-using-opencv.html>
    rect := image.Rect(0, 2150, 1440, 2200)
	//Find this function in core.go in gocv
	dst := src.Region(rect)
	golden := gocv.IMRead("golden_check_fighting_result.png", gocv.IMReadUnchanged)
	dst_bytes := dst.ToBytes()
	golden_bytes := golden.ToBytes()
	ret := bytes.Compare(dst_bytes, golden_bytes)
	//fmt.Println("bytes compare result: %v", ret)
	if ret != 0 {
		return false
	}
	fmt.Println("In check fighting result senario.")
	result = click(750, 1200)
	if !result {
		return result
	}
	return true
}

func test_and_walking() bool {
	src := gocv.IMRead("dq6.png", gocv.IMReadUnchanged)
	//ref: //<https://answers.unity.com/questions/1374912/how-to-crop-image-using-opencv.html>
    rect := image.Rect(67, 1489, 214, 1601)
	//Find this function in core.go in gocv
	dst := src.Region(rect)
    gocv.IMWrite("./dst.png", dst)
	golden := gocv.IMRead("golden_main_menu.png", gocv.IMReadUnchanged)
    gocv.IMWrite("./golden.png", golden)
	cmd := exec.Command("diff", "dst.png", "golden.png")
	//fmt.Println("Running diff and waiting for it to finish...")
	err := cmd.Run()
	if err != nil {
		return false
	}
	fmt.Println("In non-fight senario.")
	cmd = exec.Command("adb", "shell", "input", "swipe", "900", "2020", "900", "2020", "1000")
	//fmt.Println("Running adb input tap and waiting for it to finish...")
	err = cmd.Run()
	if err != nil {
		fmt.Println("Command finished with error: %v", err)
		return false
	}
	cmd = exec.Command("adb", "shell", "input", "swipe", "1300", "2020", "1300", "2020", "1000")
	//fmt.Println("Running adb input tap and waiting for it to finish...")
	err = cmd.Run()
	if err != nil {
		fmt.Println("Command finished with error: %v", err)
		return false
	}
	return true
}

func idle_click() {
	_ = click(720, 1280)
	fmt.Println("Do idle click")
}

func crop(rectangle []int) {
    rect := image.Rect(rectangle[0], rectangle[1], rectangle[2],  rectangle[3])
    src := gocv.IMRead("dq6.png", gocv.IMReadUnchanged)
    //Find this function in core.go in gocv
    dst := src.Region(rect)
    gocv.IMWrite("./result.png", dst)
}

func ocr_main_dialog() {
    src := gocv.IMRead("dq6.png", gocv.IMReadUnchanged)
	rectangle := try_to_get_main_dialog()
    rect := image.Rect(rectangle[0], rectangle[1], rectangle[2],  rectangle[3])
    mainDialog := src.Region(rect)
    gocv.IMWrite("./crop.png", mainDialog)
}

func main() {

	var result bool
	var false_count int

    for {
		cmd := exec.Command("/usr/local/bin/adb", "shell", "screencap", "-p", "/storage/sdcard0/bamvor/dq6.png")
//		fmt.Println("Running screen capture command and waiting for it to finish...")
		err := cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		cmd = exec.Command("adb", "pull", "/storage/sdcard0/bamvor/dq6.png")
//		fmt.Println("Running pull and waiting for it to finish...")
		err = cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		cmd = exec.Command("adb", "shell", "rm", "/storage/sdcard0/bamvor/dq6.png")
//		fmt.Println("Running rm and waiting for it to finish...")
		err = cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		ocr_main_dialog()
		return
		result = test_and_start_fighting()
		result = result || test_and_check_fighting_result()
		result = result || test_and_walking()
		if !result {
			false_count += 1
//			fmt.Println("false_count %v", false_count)
		}
		if false_count % 30 == 0 {
			idle_click()
		}
    }
}
