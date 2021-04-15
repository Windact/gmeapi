# gmeapi
REST API for the GME powerplant-coding-challenge
For more details, refer to https://github.com/gem-spaas/powerplant-coding-challenge
---
# About the packages files and folders
The package contains :
- an ```api```  folder where you can find a productionplan.py that contains the class that process the post request, logs info and errors; an 'utils.py' file where the algorithm that find the adequate powerplant combination is located and a logs folder where 'productionplan.log' contains info logs and error logs and 'productionplanRuntimeError.log' contains RunTimeError logs.
- This 'README.md' file
- A 'Dockerfile'
- A 'requirements.txt' file that contains all the dependancies for this api to run in a python3 environement

---
# How to compile and lauch this application
There is two ways:
# Without Docker
- Create a python3 virtual environement with the help of the 'requirements.txt' file
- Run the api using this command : 'python run.py'. (Here we assume your terminal is open in the root folder of this package)
- The application runs on http://0.0.0.0:8888/
- As requiered port 8888 is exposed and the exposed endpoint for the POST request is '/productionplan'. It's therefore accecible at : http://0.0.0.0:8888/productionplan

# Deploy with docker
The root directory of this package contains a Dockerfile. This file is use to build a docker image for our api.
# Overview of the Dockerfile
- The 'FROM alpine:latest' command tells docker where we want to get our base docker image and which version. Here it's the latest available one.
- 'RUN apk add --no-cache python3-dev' and 'RUN apk add py3-pip' are use to download and install python3 then pip3 in our docker image
- The 'WORKDIR /app' commands copy all files and folders in DockerFile directory to an 'app' directory in our docker image. That way we are moving our gmeapi package into the docker image
- The 'RUN pip3 --no-cache-dir install -r requirements.txt' use pip3, the package manager of python to install all the dependencies in the 'requirements.txt' file for our application to run.
- The 'EXPOSE 8888' command expose the port 8888. This must be the same as the one for the flask application.
- 'ENTRYPOINT ["python3"]' and 'CMD ["run.py"]' so that they the command 'python3 run.py' is run when we run the docker as a container.
# Deploying the gmeapi with docker
- Build your docker image with the help of the Dockerfile : 'docker build -t <imageName:version> dockerFilePath'
- Run your docker container in daemon mode with ports exposed: 'docker run -it -d -p <outsidePort>:<dockerInsidePort> <imageName:version>'
# Example:
- Build docker image with your Dockerfile in your current directory : 'docker build -t gmeapi:latest .'
- run your docker container with the out side port as 5005. ( The inside port must stay as the one given in the dockerfile): 'docker run -p 5005:8888 gmeapi'
- Send your POST request to the api to : http://0.0.0.0:5005/productionplan

# Usefull docker commands:
- List all running container : 'docker ps'
- List all containers : 'docker ps -a'
- List all docker images : 'docker images'

Check https://docs.docker.com/ for more information about docker and docker commands.
