创建项目过程的主要步骤：

建虚拟环境： python -m venv venv

激活虚拟环境： .\venv\Scripts\activate

安装： pip install python-dotenv


添加配置文件： .flaskenv

FLASK_ENV=development
FLASK_APP=app.py

安装： pip install flask-sqlalchemy

安装： pip install flask-login

执行编写好的命令，初始化数据库： flask forge

启动运行： flask run


---

使用Python下的 pip 包管理工具，来生成 requirements.txt 文件，命令如下：
pip freeze > D:\pycharm\requirements.txt

---

使用 requirements.txt 安装当前项目所有的依赖模块

pip install -r requirements.txt