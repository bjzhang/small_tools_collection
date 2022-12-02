set flash_sz_idx 0
if { $argc >= $flash_sz_idx + 1 } {
        set flash_sz [lindex $argv $flash_sz_idx]
} else {
        set flash_sz 64
}

if {[info exists flash_sz] } {
        puts "flash size: $flash_sz MB"
}
