import click
import os
import sys

from flask import Flask, render_template
from flask import request, url_for, redirect, flash
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'   # windows 下的 sqlite连接前缀
else:
    prefix = 'sqlite:////'   # Linux  或 macOS 下的 sqlite连接前缀

app = Flask(__name__)  # flask 实例

# 数据库连接字符串
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + \
    os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'

db = SQLAlchemy(app)
login_manager = LoginManager(app)

login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    '''
    用户模型类， 
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))           # 用户显示名称，可以在 settings 中修改
    username = db.Column(db.String(20))       # 用户登录名，不能更改
    password_hash = db.Column(db.String(128)) # 用户登录密码加密后的hash值

    def set_password(self, password):   # 密码加密
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):  # 验证密码
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))    # 电影标题
    year = db.Column(db.String(4))      # 电影发行年份


@app.route('/', methods=['GET', 'POST'])
def index():  # put application's code here
    '''
    HTTP 的 GET 方法: 查询电影 
    HTTP 的 POST 方法: 添加电影
    '''
    if request.method == 'POST':
        # 用户是否已登录
        if not current_user.is_authenticated:
            flash('匿名用户不能添加数据')
            return redirect(url_for('index'))
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('无效的输入')
            return redirect(url_for('index'))

        # 实例化电影数据
        movie = Movie(title=title, year=year)
        db.session.add(movie)  # 添加数据
        db.session.commit()    # 提交会话
        flash('添加成功')
        return redirect(url_for('index'))

    movies = Movie.query.all()   # 查询所有电影
    return render_template('index.html', title="Home",  movies=movies)


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
    '''
    HTTP 的 GET 方法: 显示待修改的电影 
    HTTP 的 POST 方法: 接收修改后的数据实现电影修改
    '''
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('无效的输入')
            return redirect(url_for('edit', movie_id=movie_id))
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('修改成功')
        return redirect(url_for('index'))

    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
    '''   
    HTTP 的 POST 方法: 接收要电影的ID，实现删除
    '''
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('删除成功')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    '''
    HTTP 的 GET 方法: 显示登录界面
    HTTP 的 POST 方法: 接收用户名和密码实现登录
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('无效的输入')
            return redirect(url_for('login'))
        # user = User.query.first()
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('无效的用户名或密码')
            return redirect(url_for('login'))
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('登录成功')
            return redirect(url_for('index'))
        flash('无效的用户名或密码')
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    '''
    HTTP 的 GET 方法: 显示注册新用户界面
    HTTP 的 POST 方法: 接收用户名和密码实现注册
    '''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('用户名或密码不能为空')
            return redirect(url_for('signup'))

        user = User.query.filter_by(username=username).first()

        if user is not None:
            flash('用户名已经存在')
            return redirect(url_for('signup'))
        else:
            click.echo('Creating user...')
            user = User(username=username, name=username)
            user.set_password(password)  # 密码加密
            db.session.add(user)
            db.session.commit()
            flash('用户注册成功')
            return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    '''
    注销用户
    '''
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    '''
    HTTP 的 GET 方法: 显示用户名修改界面
    HTTP 的 POST 方法: 接收新用户名，实现修改
    '''
    if request.method == 'POST':
        name = request.form.get('name')
        if not name or len(name) > 20:
            flash('Goodbye.')
            return redirect(url_for('settings'))
        current_user.name = name
        db.session.commit()
        flash('用户名修改成功')
        return redirect(url_for('index'))

    return render_template('settings.html')


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


@app.errorhandler(404)
def page_not_found(e):
    user = User.query.first()
    return render_template('404.html', user=user)


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    '''
    删除数据库，然后按新的class重建
    '''
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login')
def admin(username, password):
    ''''
    命令方式添加用于登录的用户名和密码（这个功能和注册功能相同）
    '''
    db.create_all()
    # user = User.query.first()
    user = User.query.filter_by(username=username).first()

    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name=username)
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('Done.')


@app.cli.command()
def forge():
    '''
    初始化数据，并添加数据
    '''
    db.create_all()
    # 全局的两个变量移动到这个函数内
    name = 'Grey Li'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly',
         'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep',
         'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done.')


@app.context_processor
def inject_user():
    '''
    模板数据上下文, 用于传递所有模板都使用的公共数据
    '''
    user = User.query.first()
    return dict(user=user)


if __name__ == '__main__':
    app.run()
