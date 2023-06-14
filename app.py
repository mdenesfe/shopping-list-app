from flask import Flask, render_template, request, redirect, url_for, flash
from peewee import *
from flask_login import LoginManager, login_user, logout_user, current_user, UserMixin
from flask import abort

app = Flask(__name__)
db = SqliteDatabase('shopping-list.db')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel, UserMixin):
    username = CharField(unique=True)
    password = CharField()

class ShoppingItem(BaseModel):
    name = CharField()
    quantity = IntegerField()
    notes = TextField()
    user = ForeignKeyField(User, backref='shopping_items')

@login_manager.user_loader
def load_user(user_id):
    return User.get_or_none(User.id == user_id)

@app.route('/')
def home():
    if current_user.is_authenticated:
        shopping_items = ShoppingItem.select().where(ShoppingItem.user == current_user.id)
        return render_template('home.html', shopping_items=shopping_items)
    else:
        return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if current_user.is_authenticated:
        if request.method == 'POST':
            item = ShoppingItem(
                name=request.form['name'],
                quantity=request.form['quantity'],
                notes=request.form['notes'],
                user=current_user.id
            )
            item.save()
            flash('Item added!')
            return redirect(url_for('home'))
        return render_template('add.html')
    else:
        return redirect(url_for('login'))

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if current_user.is_authenticated:
        item = ShoppingItem.get_or_none((ShoppingItem.id == item_id) & (ShoppingItem.user == current_user.id))
        if item:
            if request.method == 'POST':
                item.name = request.form['name']
                item.quantity = request.form['quantity']
                item.notes = request.form['notes']
                item.save()
                flash('Item updated!')
                return redirect(url_for('home'))
            return render_template('edit.html', item=item)
        else:
            abort(404)
    else:
        return redirect(url_for('login'))

@app.route('/delete/<int:item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    if current_user.is_authenticated:
        item = ShoppingItem.get_or_none((ShoppingItem.id == item_id) & (ShoppingItem.user == current_user.id))
        if item:
            if request.method == 'POST':
                item.delete_instance()
                flash('Item deleted!')
                return redirect(url_for('home'))
            return render_template('delete.html', item=item)
        else:
            abort(404)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        user = User.get_or_none(User.username == request.form['username'])
        if user and user.password == request.form['password']:
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            user = User.create(
                username=request.form['username'],
                password=request.form['password']
            )
            flash('User created!')
            return redirect(url_for('login'))
        except IntegrityError:
            flash('Username already exists')
    return render_template('register.html')

if __name__ == '__main__':
    db.connect()
    db.create_tables([User, ShoppingItem], safe=True)
    app.secret_key = 'secret'
    app.run(debug=True)
