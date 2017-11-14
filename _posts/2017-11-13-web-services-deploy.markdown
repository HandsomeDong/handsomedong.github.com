---
layout: post
title:  "django-channel Web服务布署文档!"
date:   2017-11-13
categories: Django
---
 
> web服务部署分为三步：
1. 运行channel backend（redis）
2. 运行worker servers（django）
3. 运行interface servers（Daphne）

**这里因为workers和interface servers都有重启监控的要求，为了方便管理，我们决定用docker来部署网站。**

## 安装环境
 操作系统版本：CentOS Linux release 7.1 64位
 
## 安装步骤

### 第一步：安装docker
1.以root或相同权限登入centos系统，运行以下代码添加yum仓库：
```shell
$ tee /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/7/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF
```
2.安装docker，注意这里安装的是docker-engine，之前使用的是yum install docker，但是在之后的版本docker进行了修改，安装方式有所不同。docker在1.12后的版本将swarm加入到docker核心内容，我们需要使用到这一功能，因此我们必须安装1.12或以后的版本。
```shell
yum install docker-engine
```

3.启动docker服务
```shell
systemctl enable docker.service
systemctl start docker
```
4.运行示例程序
```shell
docker run --rm hello-world
```
运行成功输出 Hello from Docker！说明安装成功。

### 第二步：运行channel backend（Redis）
1.下载redis的docker镜像，tag加上alpine版本，这个版本使用的是alpine linux，更加精简，体积更小。运行：
```shell
docker pull redis:alpine
```
2.运行redis
```shell
docker run --name channel-backend -d redis:alpine
```
3.尝试连接redis
```shell
docker run -it --link channel-backend:redis --rm redis:alpine redis-cli -h redis -p 6379
```
出现redis的命令行说明安装成功，可以输入redis指令尝试操作一下redis。

4.查看网络情况
```shell
docker network inspect bridge
```
一个container启动时会被自动连接到一个本地网络里面，查看对应的redis的ip地址，记录下来。


### 第三步：运行worker server（Django）
1.首先运行起来我们django需要用到的数据库mysql。
直接运行mysql的docker镜像
```shell
docker run --name django-backend -e MYSQL_ROOT_PASSWORD=password -d mysql
```
这里MYSQL_ROOT_PASSWORD指定root密码。
它向外暴露3306端口，其他启动的容器只要连接到这个容器就可以了

2.查看网络情况
```shell
docker network inspect bridge
```
查看对应的mysql的ip地址，记录下来。

3.创建数据库
首先连接数据库，这里容器ip要根据上面的来
```shell
docker run -it --link django-backend:mysql --rm mysql sh -c 'exec mysql -h 172.17.0.6 -P 3306 -uroot -p '
```
连接上后可以看到是一个新的数据库，我们需要在里面创建一个名为‘user_strategy_seller’的schema，这是我们的django所用的数据的名字。
运行:
```sql
create schema user_strategy_seller；
```
运行show databases;可以看到是否创建成功。
具体的表现在不用添加，后面会用django自带的工具生成。

4.配置django

从远程仓库registry.domain.com获取web_worker镜像，远程仓库配置方法在大鱼下的配置文档中有介绍。
docker pull registry.domain.com/web_worker
然后用相关参数启动容器即可：
docker run -d registry.domain.com/web_worker -r 'redis_IP' -m 'mysql_IP'
由于worker的特性，一般为一个核分配一到两个worker的数量比较合适，也就是说要根据需要运行多次以上指令。



### 第四步：运行interface server（Daphne）
同样的，从远程仓库获得daphne镜像
docker pull registry.domain.com/daphne
运行指令：
docker run -d -p 80:80 registry.domain.com/daphne -r 'redis_IP'
这里由于端口占用的关系，这个指令只能运行一次，否则会因为端口冲突启动失败。

***至此单点web服务的部署就完成了，后面将会介绍在集群上部署服务的方法。***

## 附：镜像制作：

### 制作worker server Django 镜像

registry.domain.com/miniconda3是一个已经预先安装好miniconda的centos系统，由于django环境配置比较复杂，因此就不直接写出dockerfile，而是采取先进入镜像手动安装配置环境，再commit产生基础环境镜像，然后用dockerfile配置CMD的方式来创建。

#### 第一步：安装基础运行环境

1.运行基础镜像
docker run -it registry.domain.com/miniconda3 /bin/bash

2.创建名为django的虚拟环境
conda create -n django biopython

3.在虚拟环境下安装项目运行需要的包
yum install mysql-devel 
pip install:
mysqlclient django channels django-bootstrap-form itsdangerous djangocaptcha decorator pandas asgi_redis gevent ujson zmq 
这是我在部署时需要安装的包，如果在尝试运行的时候还是提示有缺少的包就再安装上去就可以了。

另外需要注意的是哪个djangocaptcha是django的验证码插件，它是一个有点问题的插件，它使用python 2.7的语法，但是在3.5版本中没有修改过来。我们需要修复一下。
安装好之后找到安装目录下的djangocaptcha代码：
/root/miniconda3/envs/django/lib/python3.5/site-packages/DjangoCaptcha/\__init__.py
将前面的 import StringIO改成
import io
在下面的代码中找到buf = StringIO.StringIO()改成buf = IO.BytesIO()之后就可以正常工作了。


用pypi的源下载可能速度较慢，可以配置国内的源，在后面加上 -i https://pypi.tuna.tsinghua.edu.cn/simple 使用清华的镜像。


4.配置运行worker
这里配置运行主要是为了测试镜像是否可用，找到django项目下的StrategySeller文件夹，里面有django的配置文件。为了方便配置，我们将setting里的一部分提取到了config.py中。其内容如下：
```python
# -*- coding: utf-8 -*-

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("localhost", 6379)],
        },
        "ROUTING": "StrategySeller.routing.channel_routing",
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'user_strategy_seller',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

DEBUG = True

```

分别配置django后台和channel后台以及debug模式。
这里我们直接将参数用编辑器修改，后面在使用时可以直接自己编写并加载上去。主要涉及mysql和redis参数，建议自己先按照前面布署的步骤先运行起来mysql和redis，记下ip等等填入。
配置好之后在项目根目录在虚拟环境下运行
```python
python manage.py runworker
```
如果没有报错说明运行成功，这个worker是没有输出信息的，所以等待一会如果没有报错误就可以认为是安装成功了。

5.运行asgi服务器Daphne
daphne作为channel的依赖已经被安装了，所以这里直接在项目根目录下运行就可以了。
```python
daphne -b 0.0.0.0 -p 80 StrategySeller.asgi:channel_layer
```
输出开始信息代表运行成功。

6.退出容器，将目前的容器提交为镜像，名为django：
```shell 
docker commit containerid django
```

#### 第二步：配置启动脚本

目前配置已经完成，我们的服务运行需要的包和软件已经都安装完毕，现在要考虑的是如何配置启动脚本可以方便后面的部署和拓展。

目前的worker运行需要配置一下几项：
1. django后台mysql参数
2. channel后台redis参数

asgi服务运行需要配置  ：
1. channel后台redis参数

配置方案有三种：1.写在image里面，启动不需要指定，但是不方便修改。2.写在配置文件里，启动方便，但是使用时必须有配置文件。3.放在启动命令里面，启动时候必须指定这些参数。

我们的布署环境将由docker的swarm完成，它可以自动均衡负载，自动重启。是在多个服务器上运行的，所以方法1和2都不可取。因此配置方案还是决定将这些参数放在启动脚本里面，也就是说要求必须在run的时候指定这些参数。

首先启动刚才制作的django镜像，在root文件夹下创建一个新的启动脚本run_django.sh，运行它就可以配置并且启动我们的worker，内容如下：
```shell
#! /bin/bash

cd /root/StrageySeller

while getopts "m:r:d" opt
do
        case $opt in
                r ) sed -i  "/hosts/c\           'hosts'\: \[\('${OPTARG}'\, 6379\)\]," StrategySeller/config.py;;
                m ) sed -i  "/HOST/c\            'HOST': '${OPTARG}'," StrategySeller/config.py;;
                d ) sed -i  "/DEBUG/c\ DEBUG = True'," StrategySeller/config.py;;
                ? ) echo "argument error"
                    exit 1;;
        esac
done

/root/miniconda3/envs/django/bin/python  manage.py runworker
```
这个脚本有三个选项，-m -r -d前两个可以指定mysql和redis的地址，端口和用户名等信息都是相同的，只有ip可以指定。-d选项可以将debug改成true，设置为debug模式。
保存后退出容器，然后执行commit指令将容器提交为镜像：
```shell 
docker commit containerid web_worker
```
这里镜像名字为web_worker，和下面的dockerfile对应就可以了。

下一步为容器配置启动脚本：
新建并进入一个目录，新建一个文件Dockerfile，输入以下内容：
FROM web_worker
WORKDIR StrageySeller
ENTRYPOINT /root/run_django.sh
CMD ["-m", "172.17.0.6", "-r", "172.17.0.4"]

这里的ＣＭＤ是启动默认参数，在命令行中写的参数可以覆盖ＣＭＤ命令。
然后回到Dockerfile目录运行
docker build .
成功后将镜像tag修改为registry.domain.com/webworker
然后使用push将这个镜像推送到远程仓库。
需要使用时只要使用docker run指令就可以启动一个worker在后面可以使用-m和-r来修改后端数据库地址。

配置daphne
前面提到daphne可以直接在django的容器中运行，因此我们仍然从django开始，从django启动一个容器，在root文件夹下新建启动脚本run_aphne.sh，内容如下:
```shell
#! /bin/bash

cd /root/StrageySeller

while getopts "r:" opt
do
        case $opt in
                r ) sed -i  "/hosts/c\           'hosts'\: \[\('${OPTARG}'\, 6379\)\]," StrategySeller/config.py;;
                ? ) echo "argument error"
                    exit 1;;
        esac
done

/root/miniconda3/envs/django/bin/daphne -b 0.0.0.0 -p 80 StrategySeller.asgi:channel_layer
```

用法和之前相同，只是去掉了Daphne不使用的mysql和debug配置，仅仅保留了redis的配置。
同样的，退出并提交镜像为daphne

新建并进入一个目录，新建一个文件Dockerfile，输入以下内容：
FROM daphne
MAINTAINER LSD "646970309@qq.com"
WORKDIR StrageySeller
ENTRYPOINT /root/run_daphne.sh
CMD ["-r", "172.17.0.4"]

然后运行docker build .
将得到的镜像改名为registry.domain.com/daphne，推送到远程仓库。
启动时要映射80接口以方便web访问，启动指令为：
docker run -p 80:80 registry.domain.com/daphne -r 'redis_IP'
当然，也可以根据需要映射到其它的端口。





