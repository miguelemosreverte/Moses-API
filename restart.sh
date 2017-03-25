sudo docker build . -t moses-api
sudo docker stop $(sudo docker ps -q)
sudo docker run -p 5000:5000 -t moses-api

