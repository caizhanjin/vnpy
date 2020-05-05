# onui linux服务器 指南
## 配置环境
1、系统：centos远端服务器
2、python环境搭建
``` 
# 下载安装anaconda
wget -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-5.2.0-Linux-x86_64.sh
sh Anaconda3-5.2.0-Linux-x86_64.sh  # 基本一路默认，除了，

出现下面语句时，可以选中不安装 no
Do you wish to proceed with the installation of Microsoft VSCode? [yes|no]

source .bashrc  # 使配置立即生效

# 创建vnpy专用环境
conda create -n vnpy python=3.7
source activate vnpy  # 进入vnpy环境
```
3、上传项目代码，推荐使用pycharm的远程功能