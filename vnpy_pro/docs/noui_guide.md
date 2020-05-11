# onui linux服务器 指南
## 配置环境
1、系统：ubuntu远端服务器

2、python环境搭建
``` 
# 下载安装anaconda
wget -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-5.2.0-Linux-x86_64.sh
sh Anaconda3-5.2.0-Linux-x86_64.sh  

# 基本一路默认，除了，出现下面语句时，是否安装VSCode，选不安装 no
Do you wish to proceed with the installation of Microsoft VSCode? [yes|no]

source .bashrc  # 使配置立即生效

# 创建vnpy专用环境
conda create -n vnpy python=3.7
source activate vnpy  # 进入vnpy环境
```
3、上传项目代码，推荐使用pycharm的远程功能

4、安装依赖包
``` 
sudo apt-get update

# 安装gcc编译器，用于编译C++类接口文件
sudo apt-get  install  build-essential

# 安装postgresql-devel
apt search postgresql-server-dev 
sudo apt-get install postgresql-server-dev
sudo apt-get install postgresql

# 安装talib
conda install -chttps://conda.anaconda.org/quantopian ta-lib

# 如果requirements.txt存在wmi，需先删除，该包是在win底下使用的
# 然后在项目根目录下编译安装vnpy和依赖包。
# 如果失败，多跑几次
pip install .

# 编译结束后，前往删除多转移的包即可
# 如果遇到字体编码问题，跑下面命令：
locale-gen zh_CN.GB18030

# 后面就是缺啥安装啥
```
5、系统后台运行
``` 
# run_noui.py为提前写好的运维脚本，脚本控制台数据内容会输出到当前目录下nohup.out
nohup python run_noui.py & 
# 查看进程
ps -aux | grep "run_noui.py"
# 杀死进程
kill [进程号]
```

-----------------------
记录一下：talib安装方法
``` 
# 安装talib 
sudo chmod -R 777 anaconda3
conda install -chttps://conda.anaconda.org/quantopian ta-lib

# 附：以下是编译安装
wget https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz
# 解压ta-lib
tar -xzvf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make & make install
# 最后安装Ta-Lib
pip install TA-Lib
```
