## 配置环境：

python  3.12.9 MySQL  5.7.42

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

登录说明

请求数据格式

| 请求方式 | 参数     | 说明         | 是否必须 |
| -------- | -------- | ------------ | -------- |
| **POST** | username | 学号         | 是       |
|          | password | 教务系统密码 | 是       |





| 状态码 | 返回状态 | 说明 | 备注 |
| ------ | -------- | ---- | ---- |
| 200    | 返回成功 | 成功 | 无   |

## 功能说明

##### 接口显示详情





##### 展示学生作业状态

##### 展示教师状态

### 页面展示显示

