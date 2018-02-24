
//reference <https://golang.org/pkg/bufio/#Scanner> for how to use scanner.
//reference <https://stackoverflow.com/a/16615559/5230736> for how to open file
// and pass file to Scanner. It is because File implements Read method.
// refernce the following link for more information:
// <https://medium.com/@matryer/golang-advent-calendar-day-seventeen-io-reader-in-depth-6f744bb4320b>
// Scanner will raise error if the characters exceed 65535:
// 2018/02/24 15:13:01 bufio.Scanner: token too long
// exit status 1

package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
)

func main() {
    file, err := os.Open("sample.txt")
    if err != nil {
        log.Fatal(err)
    }
    defer file.Close()

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        fmt.Println(scanner.Text())
    }
    if err := scanner.Err(); err != nil {
        log.Fatal(err)
    }
}

