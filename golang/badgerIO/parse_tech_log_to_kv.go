
// Reference <https://gobyexample.com/command-line-arguments> for how to get
// arguments.
package main

import (
    "bufio"
    "fmt"
    "os"
    "log"
    "regexp"
    "strings"

    kvwrapper "./kvwrapper"
)

func parse_markdown(markdown string, badger string) {

    file, err := os.Open(markdown)
    if err != nil {
        log.Fatal(err)
    }
    defer file.Close()

    scanner := bufio.NewScanner(file)
    var prevLine string
    var state string
    state = "unknown"
    var key string
    var value string
    for scanner.Scan() {
        line := scanner.Text()
        matched, err := regexp.MatchString("^=+", line)
        if err != nil {
            log.Fatal(err)
        }
        if (matched) {
            fmt.Println("end get value. output previous key-value:")
            fmt.Println("key: " + key)
            fmt.Println("value: ")
            fmt.Println(value)
            kvwrapper.WriteKV(key, value)
            key = ""
            value = ""
            fmt.Println("Found Key")
            key = prevLine
            state = "getValue"
        } else {
            if strings.Compare(state, "getValue") == 0 {
                matched, err := regexp.MatchString("^=+", prevLine)
                if err != nil {
                    log.Fatal(err)
                }
                if !matched {
                    value += prevLine + "\n"
                }
            }
        }
        prevLine = line
    }
    fmt.Println("EOF. output previous key-value:")
    value += prevLine + "\n"
    fmt.Println("key: " + key)
    fmt.Println("value: ")
    fmt.Println(value)
    kvwrapper.WriteKV(key, value)
    if err := scanner.Err(); err != nil {
        log.Fatal(err)
    }
}

func main() {
    if (len(os.Args) < 3) {
        log.Fatal("Usage: " + os.Args[0] + " /path/to/markdown /path/to/badgerIO")
    }
    markdown := os.Args[1]
    if _, err := os.Stat(markdown); os.IsNotExist(err) {
        log.Fatal("file<" + markdown + "> is not exist")
    }
    fi, err := os.Lstat(markdown)
    if err != nil {
        log.Fatal(err)
    }
    if (!fi.Mode().IsRegular()) {
        fmt.Println("file<" + markdown + "> is not regular file")
    }
    badger := os.Args[2]
    parse_markdown(markdown, badger)
}

