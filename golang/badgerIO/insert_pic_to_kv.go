package main

import (
    "bufio"
    "encoding/base64"
    "fmt"
    "log"
    "math/rand"
    "os"
    "path"

    kvwrapper "./kvwrapper"
)

/*
How to use
// Embed into an html without PNG file
img2html := "<html><body><img src=\"data:image/png;base64," + imgBase64Str + "\" /></body></html>"
w.Write([]byte(fmt.Sprintf(img2html)))
 */
func insert_pic_to_kv(kv kvwrapper.KeyvalueStore, picture string) {
    file, err := os.Open(picture)
    if err != nil {
        log.Fatal(err)
    }
    defer file.Close()

    fileInfo, err := file.Stat()
    if err != nil {
        log.Fatal(err)
    }
    var size int64 = fileInfo.Size()
    buffer := make([]byte, size)

    fileReader := bufio.NewReader(file)
    fileReader.Read(buffer)

    imageBase64Str := base64.StdEncoding.EncodeToString(buffer)

    key := "images_" + string(rand.Int31n(1000)) + "_" + path.Base(picture)
    fmt.Println("key: " + key)
    kv.WriteKV(key, imageBase64Str)
}

func main() {
    if (len(os.Args) < 3) {
        log.Fatal("Usage: " + os.Args[0] + " /path/to/badgerIO /path/to/image1 /path/to/image2")
    }
    var kv kvwrapper.KeyvalueStore
    kv.OpenKV(os.Args[1])
    defer kv.CloseKV()
    kv.SetCompact(true)
    for true {
        for i := 2; i < len(os.Args); i++ {
            fmt.Println("insert picture: ", os.Args[i])
            insert_pic_to_kv(kv, os.Args[i])
        }
    }
}
