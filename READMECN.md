# 一个用来备份QQ空间动态的小东西

能把那些你看得见的好友动态，包括里面的图片和视频，存到你自己的电脑上。

> **如何工作：** 像你用浏览器浏览QQ空间，然后这个项目顺手帮你记录了下来。

---

## 使用

### 第一步: 创建和进入环境  

```bash
# 创建环境
python -m venv venv

# 进入环境
# Windows 上
venv\Scripts\activate
# Mac 或者 Linux 上
source venv/bin/activate
```

### 第二步: 安装依赖

```Bash
pip install -r requirements.txt
```

### 第三步：运行程序

```Bash
python main.py
```
运行后内容会在在 resource/result/ 文件夹里（可修改config.ini更改位置）。

### 第四步：生成能看的网页

```Bash
python report.py
```
它会自动用浏览器打开一个网页，以后想看随时都能点开。
## 说在最后

### 项目由来
Inspired by 之前一个已删库的项目（把里面的ConfigUtil、LoginUtil、RequestUtil和ToolsUtil抄了一下..）.
这个项目使用了emotion_cgi_msglist_v6接口，就是模仿浏览qq空间网页，然后把看到的内容如说说文字，图片和视频等抄下来放在一个文件夹里。当然还有生成一个简陋的html页面方便查看。它能获取的都是你能看到，所以只是帮你快速看看你好友的动态而已。

### 免责声明
本项目仅供学习和技术交流使用，请勿用于非法用途或商业目的。
所有数据版权归原作者及腾讯公司所有。如有侵权，我会马上删除。