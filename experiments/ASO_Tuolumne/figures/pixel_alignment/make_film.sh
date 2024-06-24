FILES="$@"

for f in $FILES
do
  montage -font 'Courier' -pointsize 35 -label ${f:0:8} ${f} -geometry +0-0 -background Gold ${f}_annotated.jpg
done

outdir=$(dirname $(echo ${FILES} | awk '{print $1}'))

ffmpeg -framerate 3 -pattern_type glob -i $outdir/'*annotated.jpg' -vf format=yuv420p -c:v libx264 -s 1280x960 $outdir/out.mp4
