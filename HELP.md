In order to make changes and get them updated inside the docker container, follow the following steps:

sudo docker build . -t moses-api
sudo docker run -p 5000:5000 -t moses-api

