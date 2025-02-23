

## 配置环境：

python  3.12.9 MySQL  5.7.42  JQuery--3.7.0

## 项目远程克隆

在你需要的目录下执行

```
git clone https://github.com/duasong111/JobSubmissionPlatform.git
```

## 安装依赖

```
进入项目文件夹
cd  JobSubmissionPlatform
```

```
使用`pip`安装所需模块
pip install -r requirements.txt
```

## 运行程序

- ######  数据库迁移命令 python manage.py makemigrations 

- ###### 执行数据库迁移文件 python manage.py migrate 

- ###### 运行项目 python manage.py runserver 

- ###### 指定端口运行项目 python manage.py runserver 8080 

- ###### 指定端口IP运行项目 python manage.py runserver 0.0.0.0:8080     

- ###### 创建超级用户 python manage.py createsuperuser 

## 

##### 功能详情说明

![Image](https://github.com/user-attachments/assets/a1a70e8e-298e-4340-af89-d8d9cf9749e3)

**登录要求**

| 请求方式 | 参数   | 说明         | 是否必须 |
| -------- | ------ | ------------ | -------- |
| **POST** | 用户名 | 学号         | 是       |
|          | 密码   | 教务系统密码 | 是       |

**成功后主页面显示**

![Image](https://github.com/user-attachments/assets/7d773011-7f14-413a-ac08-626a8b9b42b1)

| 状态码 | 返回状态 | 说明 | 备注 |
| :----: | -------- | ---- | ---- |
|  200   | 返回成功 | 成功 | 无   |

**学生页面展示**

![Image](https://github.com/user-attachments/assets/401781d8-b604-4b5c-9cc1-64a7ce04b97f)
**社团活动展示**

![Image](https://github.com/user-attachments/assets/6e3714da-b706-4961-8dd4-9c5ba68a4252)
