d=./data/my_first_pwnie;
echo "Building $d"
image_name=$(jq -r .container_image < "$d"/challenge.json)
sudo docker build -t "$image_name" "$d"
echo "Starting $d"
image_name=$(jq -r .container_image < "$d"/challenge.json)
port=$(jq -r .internal_port < "$d"/challenge.json)
docker run -d --rm -p $port:$port --name "$image_name" "$image_name"