
while true; do
    rm crop*.png
    bash ./snapshot.sh
    python ./detect_color.py --image dq6.png
    python ./detect_shapes.py --image images.png
    for s in `ls crop*.png`; do
        rm result_*.png
        ./locate_the_font $s
        for f in `ls result_*png_*.png`; do
            tesseract $f stdout -l chi_sim --psm 7
        done
    done
done
