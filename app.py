from flask import Flask, render_template, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms.fields import StringField, FloatField, IntegerField, SubmitField
from wtforms import PasswordField, BooleanField
import sqlite3

app = Flask(__name__)
# Задаем секретный ключ для защиты форм
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Создаем класс формы для ввода данных о продаже
class SaleForm(FlaskForm):
    # Определяем поля формы с помощью классов полей ввода
    # и набора валидаторов
    name = StringField('Name', validators=[DataRequired()])
    amount = IntegerField('amount', validators=[DataRequired()])
    weight = FloatField('weight', validators=[DataRequired()])
    price = FloatField('Pric', validators=[DataRequired()])
    discount = FloatField('discount', default=0.0)
    manager = StringField('Manager', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Save')

# Функция для создания таблицы в базе данных
def create_table():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    # Определяем структуру таблицы sales
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            weight REAL NOT NULL,
            price REAL NOT NULL,
            discount REAL DEFAULT 0.0,
            final_price REAL NOT NULL,
            manager TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Основной маршрут приложения
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SaleForm()
    if request.method == "POST":
        # Если пользователь отправил форму, проверяем его логин и пароль
        if form.username.data == 'manager' and form.password.data == 'password':
            # Если введены правильные данные, перенаправляем на страницу менеджера
            return redirect(url_for('manager'))
        elif form.username.data == 'admin' and form.password.data == 'password':
            # Если введены правильные данные, перенаправляем на страницу администратора
            return redirect(url_for('admin'))
        else:
            # Если данные введены неправильно, выводим сообщение об ошибке
            flash('Неверно введен логин или пароль')
    # Отображаем страницу ввода данных о продаже
    return render_template('index.html', form=form)

create_table()


@app.route('/manager/sales', methods=['GET', 'POST'])
def manager():
    # создаем экземпляр формы продажи
    form = SaleForm()
    if request.method == "POST":
        # сохраняем данные в базе данных
        conn = sqlite3.connect('sales.db') # устанавливаем соединение с базой данных
        c = conn.cursor() # создаем курсор для работы с базой данных
        c.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                weight REAL NOT NULL,
                price REAL NOT NULL,
                discount REAL DEFAULT 0.0,
                final_price REAL NOT NULL,
                manager TEXT NOT NULL
            )
        ''') # создаем таблицу sales, если она еще не создана
        discount = form.discount.data if form.discount.data is not None else 0.0 # получаем значение скидки из формы или устанавливаем значение по умолчанию
        final_price = form.price.data * form.amount.data * (1 - (discount or 0.0) / 100) # вычисляем итоговую цену продажи

        values = (
            form.name.data,
            form.amount.data,
            form.weight.data,
            form.price.data,
            form.discount.data,
            final_price,
            form.manager.data
        ) # упаковываем данные в кортеж
        c.execute(
            'INSERT INTO sales (name, amount, weight, price, discount, final_price, manager) VALUES (?, ?, ?, ?, ?, ?, ?)',
            values) # вставляем данные в таблицу sales
        conn.commit() # сохраняем изменения в базе данных
        conn.close() # закрываем соединение с базой данных
        flash('Продажа успешно добавлена') # выводим сообщение об успешном добавлении продажи
        return redirect(url_for('manager')) # перенаправляем пользователя на страницу с формой продажи
    else:
        return render_template('manager.html', form=form) # отображаем страницу с формой продажи

@app.route('/admin')
def admin():
    conn = sqlite3.connect('sales.db') # устанавливаем соединение с базой данных
    c = conn.cursor() # создаем курсор для работы с базой данных
    c.execute('SELECT * FROM sales') # получаем все записи из таблицы sales
    sales = c.fetchall() # извлекаем все записи из курсора
    conn.close() # закрываем соединение с базой данных
    return render_template('admin.html', sales=sales) # отображаем страницу с данными о продажах

@app.route('/logout')
def logout():
    return redirect(url_for('index')) # перенаправляем пользователя на главную страницу


def get_sale(id):
    # устанавливаем соединение с базой данных
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()

    # выполняем запрос к базе данных на выборку продажи с указанным id
    c.execute('SELECT * FROM sales WHERE id=?', (id,))
    sale = c.fetchone()

    # закрываем соединение с базой данных
    conn.close()

    # возвращаем выбранную продажу
    return sale


@app.route('/edit_sale/<int:id>', methods=['GET', 'POST'])
def edit_sale(id):
    # создаём экземпляр формы для редактирования продажи
    form = SaleForm()

    # устанавливаем соединение с базой данных
    conn = sqlite3.connect('sales.db')

    # выполняем запрос к базе данных на выборку продажи с указанным id
    sale = conn.execute('SELECT * FROM sales WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        # получаем данные из формы редактирования продажи
        name = request.form['name']
        amount = float(request.form['amount']) if request.form['amount'] else 0.0
        weight = float(request.form['weight']) if request.form['weight'] else None
        price = float(request.form['price']) if request.form['price'] else 0.0
        discount = float(request.form['discount']) if request.form['discount'] else 0.0
        manager = request.form['manager']

        # Вычисляем final_price с учётом discount
        final_price = amount * price * (1 - discount / 100)

        # Обновляем данные в базе данных
        update_sale(name, amount, weight, price, discount, manager, final_price, id)

        # закрываем соединение с базой данных
        conn.close()

        # перенаправляем пользователя на страницу администратора
        return redirect(url_for('admin'))

    else:
        # заполняем форму данными из базы данных
        form.name.data = sale[1]
        form.amount.data = sale[2]
        form.weight.data = sale[3]
        form.price.data = sale[4]
        form.discount.data = sale[5]
        form.manager.data = sale[7]

        # закрываем соединение с базой данных
        conn.close()

        # отображаем страницу редактирования продажи с заполненной формой
        return render_template('edit_sale.html', form=form, sale=sale)


# Объявляем функцию update_sale, которая будет обновлять запись в базе данных
def update_sale(name, amount, weight, price, discount, manager, final_price, id):
    # Создаем соединение с базой данных
    conn = sqlite3.connect('sales.db')
    # Создаем курсор для выполнения операций с базой данных
    c = conn.cursor()

    # Обрабатываем случай, когда discount = None, и заменяем его на 0.0
    if discount is None:
        discount = 0.0

    # Создаем кортеж с данными, которые нужно обновить в базе данных
    values = (name, amount, weight, price, discount, final_price, manager, id)
    # Создаем SQL-запрос на обновление записи в базе данных
    sql = '''UPDATE sales SET name=?, amount=?, weight=?, price=?, discount=?, final_price=?, manager=? WHERE id=?'''
    # Выполняем SQL-запрос с помощью курсора и передаем ему кортеж с данными
    c.execute(sql, values)
    # Применяем изменения в базе данных
    conn.commit()
    # Закрываем соединение с базой данных
    conn.close()


# Если файл запускается как скрипт, то запускаем встроенный веб-сервер Flask
if __name__ == '__main__':
    app.run(debug=True, port=5000)

