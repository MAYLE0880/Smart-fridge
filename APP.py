
from flask import Flask, render_template, redirect, url_for, request, jsonify
import pymysql
import datetime
import json

DB_CONFIG = {
    "host": "194.87.243.9",
    "user": "pedr",
    "password": "15421542",
    "database": "fridge_management",
    "charset": "utf8mb4"
}

app = Flask(__name__)


def days_until_expiration(expiration_date):
    """
    Вычисляет, сколько дней осталось до истечения срока годности
    от сегодняшнего дня.
    """
    if not expiration_date:
        return None


    if isinstance(expiration_date, datetime.date):
        exp_date = expiration_date
    else:
        exp_date = datetime.datetime.strptime(expiration_date, "%Y-%m-%d").date()

    today = datetime.date.today()
    return (exp_date - today).days


def get_all_products():
    """
    Получает все продукты из таблицы products в БД.
    Возвращает список словарей, где каждый словарь — одна строка из БД.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM products;")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return products
    except pymysql.MySQLError as err:
        print("Ошибка MySQL:", err)
        return []


def get_products_by_category(category_name):
    """
    Получает продукты из таблицы products по категории (product_type).
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM products WHERE product_type = %s;"
        cursor.execute(sql, (category_name,))
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return products
    except pymysql.MySQLError as err:
        print("Ошибка MySQL:", err)
        return []


@app.route("/")
def index():
    """
    Главная страница с кнопкой «Открыть холодильник».
    """
    return render_template("index.html")


@app.route("/open_fridge")
def open_fridge():
    """
    При нажатии на кнопку «Открыть холодильник» выводим
    весь список продуктов с группировкой по категориям.
    """
    products = get_all_products()


    for product in products:
        product["days_left"] = days_until_expiration(product["expiration_date"])


    categories_dict = {}
    for p in products:
        cat = p["product_type"] or "Без категории"
        if cat not in categories_dict:
            categories_dict[cat] = []
        categories_dict[cat].append(p)


    return render_template("fridge.html", categories=categories_dict)


@app.route("/category/<category_name>")
def show_category(category_name):
    """
    Переход по ссылке на конкретную категорию.
    Выводит продукты, у которых product_type = category_name.
    """
    products = get_products_by_category(category_name)


    for product in products:
        product["days_left"] = days_until_expiration(product["expiration_date"])

    return render_template("category.html", category=category_name, products=products)


@app.route("/update_product/<int:product_id>", methods=["POST"])
def update_product(product_id):
    """
    Обновляет количество продукта в базе данных.
    """
    try:
        new_quantity = int(request.form.get("quantity", 0))
        if new_quantity < 0:
            return "Ошибка: Количество не может быть отрицательным.", 400

        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = "UPDATE products SET quantity = %s WHERE id = %s;"
        cursor.execute(sql, (new_quantity, product_id))
        conn.commit()
        cursor.close()
        conn.close()

        return "Продукт успешно обновлен.", 200
    except Exception as e:
        print("Ошибка:", e)
        return "Ошибка при обновлении продукта.", 500


@app.route("/delete_product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    """
    Удаляет продукт из базы данных.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = "DELETE FROM products WHERE id = %s;"
        cursor.execute(sql, (product_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return "Продукт успешно удален.", 200
    except Exception as e:
        print("Ошибка:", e)
        return "Ошибка при удалении продукта.", 500


@app.route("/close_fridge")
def close_fridge():
    """
    Закрытие холодильника (просто возвращаемся на главную).
    """
    return redirect(url_for("index"))


if __name__ == "__main__":

    app.run(debug=True)
