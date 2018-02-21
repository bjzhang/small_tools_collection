package main

import (
    "bytes"
    "image"
    "fmt"
	"os/exec"
    "gocv.io/x/gocv"
)

func test_and_start_fighting() {
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
		fmt.Println("It is not fighting senario.")
	} else {
		cmd := exec.Command("adb", "shell", "input", "tap", "130", "1800")
		fmt.Println("Running adb input tap and waiting for it to finish...")
		err := cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		cmd = exec.Command("adb", "shell", "input", "tap", "130", "1800")
		fmt.Println("Running adb input tap and waiting for it to finish...")
		err = cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		cmd = exec.Command("adb", "shell", "input", "tap", "130", "1800")
		fmt.Println("Running adb input tap and waiting for it to finish...")
		err = cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
	}
}

func test_and_exit_fighting() {
	src := gocv.IMRead("dq6.png", gocv.IMReadUnchanged)
	//ref: //<https://answers.unity.com/questions/1374912/how-to-crop-image-using-opencv.html>
    rect := image.Rect(0, 2150, 1440, 2200)
	//Find this function in core.go in gocv
	dst := src.Region(rect)
	golden := gocv.IMRead("golden_exit_fighting.png", gocv.IMReadUnchanged)
	dst_bytes := dst.ToBytes()
	golden_bytes := golden.ToBytes()
	ret := bytes.Compare(dst_bytes, golden_bytes)
//	fmt.Println("bytes compare result: %v", ret)
	if ret != 0 {
		fmt.Println("It is not exit fighting senario.")
	} else {
		cmd := exec.Command("adb", "shell", "input", "tap", "750", "1200")
		fmt.Println("Running adb input tap and waiting for it to finish...")
		err := cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		cmd = exec.Command("adb", "shell", "input", "tap", "130", "1800")
		fmt.Println("Running adb input tap and waiting for it to finish...")
		err = cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
		cmd = exec.Command("adb", "shell", "input", "tap", "130", "1800")
		fmt.Println("Running adb input tap and waiting for it to finish...")
		err = cmd.Run()
		if err != nil {
			fmt.Println("Command finished with error: %v", err)
			return
		}
	}
}

func main() {
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
		test_and_start_fighting()
		test_and_exit_fighting()
    }
}
