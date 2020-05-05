<p align="center">
Reinforcement Learning for Real Time Field Service Scheduling, Dispatching, Planning

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
1. Prepare linux or macos with docker, docker-compose. This is how to install [docker-compose] (https://docs.docker.com/compose/install/)
2. Run this commond in src folder:
    ```shell
    docker-compose -f local.yml build
    docker-compose -f local.yml up
    ```
3. Open browser and visit http://localhost:8000

# Keywords

Reinforcement Learning, Field Service Scheduling, Dispatching, Planningnd, AI, Optimization

Architecture
-----
![System_Architecture](./doc/architecture.jpg)



# Technology Stack
[Django] (https://www.djangoproject.com/) | [Django-SimpleUI] (https://github.com/newpanjing/simpleui)

[Gym] (https://github.com/openai/gym) | [RLLib  for RL] (https://docs.ray.io/en/latest/rllib.html) | [Ortools  for Optimization] (https://github.com/google/or-tools)





# TODO
- Deploy a demo
- Create usage documents


# Known Issues
