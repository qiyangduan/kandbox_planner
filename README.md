<p align="center">
<h3>Reinforcement Learning for Real Time Field Service Planning</h3>

![screenshot](./doc/kandbox_planner_20200505.jpg)

</p>

---
<p align="center">
<a href="./README.md">中文</a> | English
</p>


## Online Demo
> This is a demo to dispatch services in London area (TO be done).  

+ Address：[https://planner.kandbox.com](https://planner.kandbox.com)
+ username：demo
+ password：Demo1234


Features
-----
👍 Timeline Chart with travel time

:point_right: Reinforcement Learning Environment per standard of Gym

:point_right: Heurisitc Agent for the Environment 

Get Started
-----
It is recommended to use docker version. For more details about installation, click [get_started_locallys](./doc/get_started_locally.md).

1. Prepare linux or macos with docker, docker-compose. This is how to install [docker-compose](https://docs.docker.com/compose/install/)
2. Run this commond in {KPlanner_HOME}/src folder:
    ```shell
    cd src
    docker-compose -f prod.yml build
    docker-compose -f prod.yml up
    ```
3. Open a browser and visit http://localhost:8000

# Keywords

Reinforcement Learning, Field Service Scheduling, Dispatching, Planning, AI, Optimization

Architecture
-----
![System_Architecture](./doc/architecture.jpg)



# Technology Stack
[Django](https://www.djangoproject.com/) | [Django-SimpleUI](https://github.com/newpanjing/simpleui)

[Gym](https://github.com/openai/gym) | [RLLib  for RL](https://docs.ray.io/en/latest/rllib.html) | [Ortools  for Optimization](https://github.com/google/or-tools)





# TODO
- Deploy a demo
- Create usage documents


# Known Issues
