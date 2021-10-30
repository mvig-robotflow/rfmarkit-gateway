# 如何使用 TCP Broker

## 简介

TCP Brocker 被设计用于接收多个传感器发送的数据流。其本质是利用python多进程的TCP服务器。

## 启动

使用

```bash
python main.py 
```
启动，或者用`--port`选项指定端口。
> (将来也许会改变) 传感器默认会与服务器的`18888`端口通信。

TCP Brocker 启动的时，会弹出选项：

```text
Welcome to Inertial Measurement Unit Data collecting system 

 Usage: 
    > start [measurement_name]    - start measurement
    > control    - begin control program
    > quit    - quit program
> 

```

输入`start/s`然后回车即可开始检测。这时候启动传感器，传感器的IP地址会出现在屏幕上。

```
Starting measurement: imu_mem_2021-10-29_212204
INFO:root:Binding address 0.0.0.0:18888
INFO:root:New client 10.52.24.251:58921
INFO:root:New client 10.52.24.132:58812
INFO:root:New client 10.52.24.187:59615
```

使用 `nc -u <IP> 18888` 命令可以连接上传感器，这时候可以发送`ping`命令测试传感器是否在线，在线的话，传感器会恢复OK.
输入`start`可以启动测量

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
python main.py
```

输入`control/c`然后回车即可开始控制。

```text
Welcome to Inertial Measurement Unit Data collecting system 

 Usage: 
    > start [measurement_name]    - start measurement
    > control    - begin control program
    > quit    - quit program
> c
Input subnet of IMUs, e.g. 10.52.24.0
> 10.52.24.0
INFO:root:Wrong input, use default value(10.52.24.0)
Welcome to Inertial Measurement Unit control system 

Sending to [10, 52, 24, 0]
Commands: 
    > restart
    > ping
    > sleep
    > shutdown
    > update
    > cali_reset
    > cali_acc
    > cali_mag
    > start
    > stop

>
```

脚本要求输入形如`10.52.24.0`的网段，将会把命令通过UDP协议发送到该网段的广播地址`10.52.24.255`上

```text
> start
INFO:root:Sending b'start' to 10.52.24.255:18888
WARNING:root:Socket timeout
INFO:root:
```

并且收集IMU返回的信息（如果有的话)

支持的命令：
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

## 使用

1. `python main.py` -> `start` 启动一个**实验记录器**
2. 激活传感器
3. `python main.py` -> `control` 启动**控制器**
4. **控制器**: `start`
5. **控制器**: `stop`
6. **实验记录器**: `Ctrl-C`中断
7. **实验记录器**: 输入实验记录
8. 下一次实验


## 校准（只需执行一次）


> 紫叶的传感器IP地址都在`10.52.24.0/24`网段

