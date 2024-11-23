# ComfyMSS

## 安装
目前仅能作为dlc在[MSST-WebUI整合包](https://github.com/SUC-DriverOld/MSST-WebUI)使用。``git clone``对应分支最新代码或参考以下方法安装。

将release中最新版的可执行文件放在项目根目录运行。无需额外安装依赖。
若出现bug，可尝试从源码运行。

**[NOTICE]**
如果你使用的是自己配置的环境**且**需要使用**日语**的界面，为确保翻译支持的完整性，请在项目的根目录打开终端并运行：
```
python ./ComfyUI/DownloadManager/fix_JP.py -a fix
```

如果运行了上述操作后出现错误，请在项目的根目录打开终端并运行：
```
python ./ComfyUI/DownloadManager/fix_JP.py -a restore
```
这样会将其恢复到原始状态，代价是有一些组件的文本可能是没有翻译的英文。
如有任何问题，请提交issue。


## 使用

### 模型安装页面

本页面的主要部分是一个树形结构，用于选择要下载的模型。当用户选中某一模型时，页面上半部分会显示模型的名称，以供用户快速了解已经选择的模型。
如果想要取消某选择，除了取消勾选叶节点的复选框外，可以直接点击上半部分对应模型右侧的删除图标，达到同样的效果。
**[INFO]** 当代表模型类别的四个节点被选中时，其下的所有树节点也会被选中，此时即为下载该类的所有模型。（虽然通常并不推荐这么做）

选择完要下载的模型后，下载的实现有两种方式：
1. 直接下载：
> 点击**下载模型**按钮
> 底层实现为```requests.get(url, stream=True)```
> 单线程单进程

2. 发送到Aria2下载
> 点击**发送到Aria2**按钮
> 底层实现为将所有要下载的url发送到本地的Aria2 RPC端口
> 可自定义本地的Aria2 RPC端口密钥。
> 需要自行开启Aria2，如果不知道这是什么，可以[bing一下](https://cn.bing.com/search?q=aria2+rpc&qs=n&form=QBRE&sp=-1&lq=0&pq=aria2+rpc&sc=10-9&sk=&cvid=8B1B8ED0D20C47DB80BE562A95B66FBA&ghsh=0&ghacc=0&ghpl=)或者使用方法1下载
> 多线程多进程

