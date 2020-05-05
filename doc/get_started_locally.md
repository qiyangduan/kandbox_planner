<p align="center">
<h3>How to install kandobx planner locally</h3>

---
<p align="center">
<a href="./get_started_locally_cn.md">中文</a> | English
</p>
---


Get Started with Docker-compose
-----
I always recommend using docker (compose, kubernetes) for installing this planner. 

1. Prepare linux or macos with docker, docker-compose. This is how to install [docker-compose] (https://docs.docker.com/compose/install/)
2. Run this commond in {KPlanner_HOME}/src folder:
    ```shell
    cd src
    docker-compose -f local.yml build
    docker-compose -f local.yml up
    ```
3. Open browser and visit http://localhost:8000


Get Started from Local Installation
-----
If you want to install from scratch for finer control or learning how it works, you can follow this path.

# Prerequisites 
## OS and Environements
I tested it on Ubuntu 18.04 and MacOS, Python 3.7 (Anaconda distribution also works).

## Mapping Service
For demo or testing purpose, you can use free routing service from: https://router.project-osrm.org/route/v1

To change it to another routing service, change configuration from this location: src/backend/static/vendor/leaflet-routing-machine/leaflet-routing-machine.js

# Steps
## Install and configure Postgresql database.
## Install required python libraries
As required by file: src/backend/requirements.txt


