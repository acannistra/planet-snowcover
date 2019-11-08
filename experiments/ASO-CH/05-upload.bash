DIRS=$(ls /tmp/ | grep "201705")

for d in $DIRS; do 
    aws s3 cp --recursive --profile esip /tmp/$d s3://planet-snowcover-predictions/$d 
done
