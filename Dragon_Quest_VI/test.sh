
rm result_*
go run fighting.go
go run locate_the_font.go
for f in `ls result_*`; do
    tesseract $f stdout -l chi_sim --psm 11
    #tesseract $f stdout -l chi_sim --psm 7
    #tesseract $f stdout -l chi_sim
done
