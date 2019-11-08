FILES=$(aws s3 ls --profile esip --recursive s3://planet-snowcover-imagery/planet-orders | sed -n  "/201705.*SR_clip.tif/p" | cut -b 32-)

for f in $FILES; do 
    aws s3 cp --profile esip s3://planet-snowcover-imagery/$f /tmp 
done
