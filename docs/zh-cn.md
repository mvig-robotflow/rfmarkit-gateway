# markit-gateway

## 简介

`markit-gateway` 被设计用于接收多个传感器发送的数据流。其本质是利用python多进程的TCP服务器。

## 安装

```shell
git clone https://github.com/mvig-robotflow/rfmarkit-gateway
cd rfimu-interface/markit_gateway
python setup.py develop
```
## 如何使用

`markit-gateway` 依赖默认为`imu_config.yaml`的配置文件来工作。需要先生成该配置文件，然后再运行`markit-gateway`。`markit-gateway`提供`configure`命令来生成配置文件。


## 配置

打开终端，键入

```shell
python -m markit_gateway configure
```
程序将启动交互式界面配置各项参数，默认如下

```yaml
imu:
  api_port: 18889
  base_dir: ./imu_data
  data_addr: 0.0.0.0
  data_port: 18888
  debug: false
  enable_gui: false
  imu_addresses: []
  imu_port: 18888
  n_procs: 4
  render_packet: true
  tcp_buff_sz: 1024
  update_interval_s: 0.1
```

通过修改imu_addresses，可以使用CIDR格式支持目标IMU网络，例如

```yaml
imu:
  api_port: 18889
  base_dir: ./imu_data
  data_addr: 0.0.0.0
  data_port: 18888
  debug: false
  enable_gui: false
  imu_addresses: ["10.233.233.0/24"]
  imu_port: 18888
  n_procs: 4
  render_packet: true
  tcp_buff_sz: 1024
  update_interval_s: 0.1
```

您也可以通过`--input`和`--output`参数指定配置文件输入路径和输出路径。若输入路径被指定，configure脚本会读取该路径下的YAML文件，更新其中的imu字段。


## 启动

使用

```shell
python -m markit_gateway [-h] [-P] [--easy] [--config CONFIG]
```

或者

```shell
python -m markit_gateway serve [--config CONFIG]
```

启动，或者用`--port`选项指定端口。
> (将来也许会改变) 传感器默认会与服务器的`18888`端口通信。

TCP Brocker 启动的时，会弹出提示符，键入`?`可以得到帮助：

```text
[22:14:39] using ./imu_data as storage backend                                                                                                                                                                                                                                                                 cli.py:38
Welcome to the Inertial Measurement Unit Data collecting system.   Type help or ? to list commands.

(imu) ?

Documented commands (type help <topic>):
========================================
control  easy_setup  help  portal  quit  start

(imu)

- start: 启动服务器，在命令行终端中
- easy_setup: 启动一个简单的交互式终端
- portal: 启动一个API服务器，接受遥控
- control: 启动一个交互式终端，用于控制IMU
- quit: 退出
```


输入`start`然后回车即可开始检测。这时候启动传感器，传感器的IP地址会出现在屏幕上。

```text
(imu) start
Starting measurement, tag=imu_mem_2022-12-01_221636
Press [enter] to stop measurement
INFO:tcp_listen_task:binding address 0.0.0.0:18888
INFO:tcp_listen_task:new client 10.233.233.4:61920
```

使用 `nc -u <IP> 18888` 命令可以连接上传感器，这时候可以发送`ping`命令测试传感器是否在线，在线的话，传感器会恢复OK. 输入`start`可以启动测量

```bash
nc -u 10.52.24.251 18888
ping
OK

start
OK
```

## 控制

新建一个新的终端窗口，再次运行

```bash
python -m markit_gateway
```

输入`control/c`然后回车即可开始控制。

```text
Welcome to Inertial Measurement Unit control system

 IMUs:

[]
Commands:
    > ping
    > restart|shutdown
    > update
    > imu_cali_[reset|acc|mag]
    > start|stop
    > imu_[enable|disable|status|imm|setup|scale|debug]
    > id
    > ver
    > time
    > blink_[set|get|start|stop|off]
    > self_test
    > always_on
    > varget|varset
    > probe* - probe client in a subnet
    > quit* - quit this tool


Online clients [0] :
set()
>

```

控制台将会试图批量操控所有的IMU并且收集IMU返回的信息（如果有的话)

支持的命令（待更新）：

- restart 模块重启
- ping 测试连通性
- sleep 轻度睡眠
- shutdown 深度睡眠（关机）
- update 更新固件
- cali_reset 重设校准信息
- cali_acc 校准加速度
- cali_mag 校准磁力计
- start 开始发送记录
- stop 停止发送记录
- ...

## 使用流程

1. `python main.py` -> `start` 启动一个**实验记录器**
2. 激活传感器
3. `python main.py` -> `control` 启动**控制器**
4. **控制器**: `start`
5. **控制器**: `stop`
6. **实验记录器**: `Ctrl-C`中断
7. **实验记录器**: 输入实验记录
8. 下一次实验
