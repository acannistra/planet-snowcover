FILES=$(aws s3 ls --profile esip  s3://planet-snowcover-imagery | grep "201705" | cut -b 32-)

for file in $FILES; do
    cd ~/planet-snowcover/model/robosat_pink/ ; ./rsp predict --create_tif --checkpoint s3://planet-snowcover-models/USCATE-20180528-copy-08-22/checkpoint-00050-of-00050.pth --aws_profile esip --config /home/ubuntu/planet-snowcover/experiments/ASO-CH-train1-5-17.toml s3://planet-snowcover-imagery/${file} /tmp/${file}
done;
