KEY=$AWS_ACCESS_KEY_ID
SECRET=$AWS_SECRET_ACCESS_KEY
PROFILE="esip"

printf "[profile $PROFILE]\nregion = us-west-2 "> ./deployment/environment/aws_config
printf "[$PROFILE]\naws_access_key_id=$KEY\naws_secret_access_key=$SECRET" > ./deployment/environment/aws_creds
