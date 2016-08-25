# 新浪微博爬虫部署
## 项目地址
```
/home/app/weibo_new
```
## 依赖安装
```
sudo yum install pip
pip install selenium,requests,lxml
```
## 使用
使用之前需要在mysql建表：
```
CREATE DATABASE IF NOT EXISTS weibo DEFAULT CHARSET utf8 COLLATE utf8_general_ci;
create table weibos(
   Publish_Time VARCHAR(40) ,
   weibo_URL VARCHAR(100) NOT NULL ,
   Sina_Weibo_ID VARCHAR(100) NOT NULL,
   weibo_Text text NOT NULL,
   Pic_URL_List text,
   Publisher_Name VARCHAR(50) ,
   Publisher_Main_URL VARCHAR(100) ,
   Collect_Time DATE,
   Recommend_Number INT,
   Comment_Number INT,
   Like_Number INT,
   PRIMARY KEY ( Sina_Weibo_ID )
);
create table comments(
   Sina_Weibo_ID VARCHAR(100) NOT NULL,
   weibo_URL VARCHAR(100) NOT NULL ,
   comment_id VARCHAR(100) NOT NULL,
   Commenter_Main_URL VARCHAR(100) ,
   Commenter_Name VARCHAR(50) ,
   Comment_date DATE,
   Comment_Text text NOT NULL,
   PRIMARY KEY ( comment_id )
);
```
另外需要Firefox火狐浏览器。
### 使用：
首先在crawl_weibo.py中，修改WEIBO_USER变量，修改成登陆用的新浪通行证的用户名。注意这里是你登录新浪通行证之后的页面会显示的你的名称，不是id。用来判断是否登录成功。如果这里没有改好，登录很可能会失败。

另外将MAIN_URLS数组里的链接，更改为目标主页的链接。注意这里的链接是主页链接。

接着运行程序：
```
python crawl_weibo.py
```
然后在命令行，根据提示输入新浪通行证的账号和密码，如下：
```
input weibo username:18801095156
Password:
```
爬取的微博保存在csv_weibo目录下，微博的评论保存在csv_comment下。同时，数据库也会保存相应内容。
