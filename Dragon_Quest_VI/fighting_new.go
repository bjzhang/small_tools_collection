
package main

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
type button struct {
    name string
    pos position
    action func
}

type senario struct {
    name string
    buttonSlice []button
}

/*
 * Take snapshot in order to analysis it
 */
func snapshot()(pic string, err error) {

}

/*
 * Get the senario from the picture.
 */
func getSenario(pic string)(current senario, err error) {

}

func main() {
    while {
        var prev senario
        pic, err := snapshot()
        cur, err = getSenario(pic)
        err = process(cur, prev)
        prev = cur
    }
}

