<p align="center">
<h2>实时现场服务排班</h2>

![screenshot](./doc/kandbox_planner_20200505.jpg)

</p>

---
<p align="center">
中文 | <a href="./README.md"> English </a>
</p>


## 在线Demo演示系统
> 这个在线demo系统里面用伦敦的样例数据做排班和展示:

+ 地址: [https://planner.kandbox.com](https://planner.kandbox.com)
+ 用户名: demo
+ 密码: Demo1234


系统特性
-----
👍 基于echarts的，能同时显示在途时间的Gantt/Timeline图，

:point_right: 基于Gym的强化学习环境 

:point_right: 当前在线demo里面使用了一个手工(Heurisitc)的agent，同时实现了基于RLLib的ppo的小agent，效果还不好。 

如何本地安装
-----
推荐使用[docker-compose](https://docs.docker.com/compose/install/)来安装。如果要本地无docker安装，参考[get_started_locally](./doc/get_started_locally.md)。

1. 我安装的环境是 Ubuntu Linux 1804和 Macos，根据操作系统指导安装好docker和docker-compose。
2. 克隆本代码库后，到src目录执行下面命令，可以启动服务:
    ```shell
    cd src
    docker-compose -f prod.yml build
    docker-compose -f prod.yml up
    ```
3. 执行下面命令创建超级用户:

    ```shell
    cd src
    docker-compose -f prod.yml  run backend python manage.py createsuperuser
    ```

4. 从浏览器打开 http://localhost:8000. 可以用超级用户创建其他用户.

5. (可选) 可以执行伦敦的样例数据导入和排班作为单元测试。下面的<your_access_token>可以从界面上的Access Toke中获取:

    ```shell
    docker-compose -f prod.yml  run backend python kandbox_planner/fsm_adapter/toy_generator/london_service_generator.py 	<your_access_token>
    ```

# 关键词

实时现场服务，排班， Reinforcement Learning, Field Service Scheduling, Dispatching, Planning, AI, Optimization


# 技术栈
Frontend UI: [Django](https://www.djangoproject.com/) | [Django-SimpleUI](https://github.com/newpanjing/simpleui/blob/master/doc/en/README_en.md)

Backend Algorithm Platform: [Gym](https://github.com/openai/gym) | [RLLib  for RL](https://docs.ray.io/en/latest/rllib.html) | [Ortools  for Optimization](https://github.com/google/or-tools)

Python为主，浏览器的展现用JS.


# TODO
- Improve London area dispatching quality
- Create usage documents


# Known Issues
