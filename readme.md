# YTFlex

[![Docker Hub](https://img.shields.io/badge/Docker%20Hub%20Repository-%230db7ed.svg?logo=docker&logoColor=white)](https://hub.docker.com/r/kirellkekw/ytflex)

[![Pylint](https://github.com/kirellkekw/YTFlex/actions/workflows/pylint.yml/badge.svg)](https://github.com/pylint-dev/pylint)
[![Build, Push and Deploy](https://github.com/kirellkekw/YTFlex/actions/workflows/deploy_to_server.yml/badge.svg)](https://github.com/kirellkekw/YTFlex/actions/workflows/deploy_to_server.yml)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Deployment ready, easy to use and fast YouTube downloader API written in Python with CDN and reverse proxy setup guide.
 
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](<https://www.python.org/>)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](<https://www.docker.com/>)
[![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)](<https://www.nginx.com/>)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](<https://fastapi.tiangolo.com/>)
[![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](<https://www.linux.org/>)
[![Nix](https://img.shields.io/badge/NIX-5277C3.svg?style=for-the-badge&logo=NixOS&logoColor=white)](<https://nixos.org/>)

# 1- Installing the requirements

This guide assumes you have a Linux machine with root access, a public IP address, or a domain name, and the required storage space for the downloaded files.

## 1.1- Download the dependencies

* Docker
* Nginx

For detailed instructions on how to install those, please refer to the following links:

* [Docker Install Guide](https://docs.docker.com/engine/install/)
* [Nginx Install Guide](https://www.nginx.com/resources/wiki/start/topics/tutorials/install/)

# 2- Setting up the API server with Docker

* This guide has been tested on NixOS with distro specific commands on both Docker and Podman OCI runtimes, but it has been written with the assumption that you are using Docker on a Debian based distro. If you are using a different distro, you might need to change the commands accordingly.

## 2.1- Clone the repository(and change directory to it)

```bash
git clone https://github.com/kirellkekw/YTFlex.git
cd YTFlex
```

## 2.2- Edit the configuration file

* Open the `config.yaml` file and change the settings according to your needs with your favorite text editor.

* Here's a quick explanation of what each setting does:

| Setting | Description | Type |
| --- | --- | --- |
| `res_list` | A list of resolutions API can attempt to download. | `list[int]` |
| `root_path` | Reverse proxied path to the API. | `str` |
| `max_file_size` | The maximum file size in megabytes the API can download. | `int` |
| `port` | The port the API server will listen on. | `int` |
| `ip_or_domain` | The address API will use to create a CDN link. If you pass this value in docker run command, config.yaml value will be ignored. | `str` |
| `max_file_age` | Maximum age of a file in seconds before it gets deleted. | `int` |
| `show_yt_dlp_output` | Decides if yt_dlp output is printed to the console or not. | `bool` |
| `allowed_domains` | A list of allowed domains for CORS requests. | `list[str]` |

## 2.3- Edit the docker-compose file

* Open `docker-compose.yml` and change the values of `volumes` to the path you want to attach to the container. You can also change the port the container will listen on, but you should also change the Nginx configuration file accordingly.

## 2.4- Build the Docker image

```bash
sudo docker build -t ytflex .
```

## 2.5- Run the image with docker-compose

```bash
sudo docker-compose up -d
```

* You can later stop and remove the container with the following commands:

```bash
sudo docker stop ytflex
sudo docker remove ytflex
```

* Or you can change directory to the cloned repository and run the following command to stop the container:

```bash
sudo docker-compose down
```

# 3- Running the CDN server with Nginx

## 3.1- Create new location blocks in your Nginx configuration file, usually located at `/etc/nginx/nginx.conf`

```nginx
# use your favorite text editor add the following server blocks to your nginx.conf as you see fit
server {
  # other server blocks and listen directives

  location /ytflex/ {
    proxy_pass http://127.0.0.1:2002/; # remember to change the port if you have changed it in the docker-compose file
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;  
  }
  location /ytflex-cdn/ {
    alias /app/ytflex/downloads/; # change this to your download path attached to the container, or leave as is if you're using the default path
    add_header Content-Disposition 'attachment'; # forces browser to download the file instead of playing it
  }
}

```

## 3.2- Restart Nginx

* The way you restart Nginx depends on your distro, but in a Debian based distro, you can restart Nginx with the following command:

```bash
sudo systemctl restart nginx
```

## 3.3- Test the server

Try to access the following URL in your browser:

`http://localhost/ytflex/root`

If you get a JSON response with the following content, then you are good to go!

```json
{"message": "Hello World"}
```

# 4- TODO

***(in no particular order)***

* [x] Add support for multiple file resolutions
* [x] Add option to limit the file size of the downloaded files
* [x] Add support for Docker for easier deployment
* [x] Add support for Nginx for reverse proxying and CDN
* [x] Add CDN support
* [x] Write a proper readme(ironic, isn't it?)
* [x] Add option to purge files after a certain amount of time
* [x] Add option to download mp3 files(this is actually easier than video files ~~,but i haven't gotten around to it yet~~)
* [x] Handle multiple file links more gracefully
* [x] Add graceful error handling for invalid links
* [x] Open source the project
* [x] Restructure the backend to be more modular
* [x] Add option to download playlists
* [x] Allow passing video or playlist id's as a parameter instead of a link
* [x] Anonymize the file access links
* [ ] Add a frontend
* [ ] Create a special message if:
  * [x] The file is not available for download, or if the link is invalid
  * [ ] If the file is already downloaded and not expired
  * [ ] The file is too large
  * [ ] The file is too long
  * [ ] The file is not available in the requested resolution
* [ ] Add support to sqlite database for:
  * [ ] Logging downloads
  * [ ] Logging errors
  * [ ] Logging file purges
  * [ ] Adding API key support for uncapped file size and higher resolution
  * [ ] Adding option to choose when a file will be purged to user
  * [ ] Adding a mechanism to limit the number of concurrent downloads per IP to prevent abuse
