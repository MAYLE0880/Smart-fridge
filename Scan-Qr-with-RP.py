import cv2
import json
import pymysql
from pyzbar import pyzbar
import datetime
from playsound import playsound
import time


DB_CONFIG = {
    "host": "194.87.243.9",
    "user": "lev",
    "password": "15421542",
    "database": "fridge_management",
    "charset": "utf8mb4"
}

def days_until_expiration(expiration_date):
    """
    Вычисляет, сколько дней осталось до истечения срока годности.
    """
    if isinstance(expiration_date, datetime.datetime):
        expiration_date = expiration_date.date()
    elif isinstance(expiration_date, datetime.date):
        expiration_date = expiration_date.strftime("%Y-%m-%d")
    elif not expiration_date:
        return None

    today = datetime.date.today()
    exp_date = datetime.datetime.strptime(expiration_date, "%Y-%m-%d").date()
    return (exp_date - today).days

def check_product_in_db(product_name):
    """
    Проверяет, есть ли продукт в базе данных.
    Возвращает данные продукта в виде словаря, если найден, иначе None.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = "SELECT * FROM products WHERE product_name = %s LIMIT 1;"
        cursor.execute(sql, (product_name,))
        product = cursor.fetchone()

        cursor.close()
        conn.close()
        return product
    except pymysql.MySQLError as err:
        print("Ошибка MySQL:", err)
        return None

def delete_product_from_db(product_name):
    """
    Удаляет продукт из базы данных.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = "DELETE FROM products WHERE product_name = %s;"
        cursor.execute(sql, (product_name,))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Продукт '{product_name}' удалён из базы данных.")
    except pymysql.MySQLError as err:
        print("Ошибка MySQL:", err)

def insert_product(product_info):
    """
    Вставляет данные о продукте в таблицу products с помощью pymysql.
    """
    product_name = product_info.get("name")


    existing_product = check_product_in_db(product_name)
    if existing_product:
        print(f"\nПродукт '{product_name}' уже существует в базе данных!")
        choice = input("Выберите действие: Посмотреть данные (1) или Удалить (2): ")

        if choice == "1":
            days_left = days_until_expiration(existing_product["expiration_date"])
            print("\n📋 **Данные о продукте:**")
            print(f"- Название: {existing_product['product_name']}")
            print(f"- Тип: {existing_product['product_type']}")
            print(f"- Дней до истечения: {days_left if days_left is not None else 'Неизвестно'}")
            print(f"- Аллергены: {existing_product['allergens'] if existing_product['allergens'] else 'Нет'}")
        elif choice == "2":
            delete_product_from_db(product_name)
        return


    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        sql = """
        INSERT INTO products (
            product_name,
            product_type,
            production_date,
            expiration_date,
            quantity,
            measurement_unit,
            measurement_type,
            nutritional_value,
            allergens
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (
            product_info.get("name"),
            product_info.get("type"),
            product_info.get("production_date"),
            product_info.get("expiration_date"),
            product_info.get("quantity"),
            product_info.get("measurement_unit"),
            product_info.get("measurement_type"),
            product_info.get("nutritional_value"),
            product_info.get("allergens")
        )
        cursor.execute(sql, values)
        conn.commit()
        print(f"✅ Продукт '{product_name}' добавлен в базу.")
        playsound(r'C:\Users\exam\Downloads\puk.mp3')  # Воспроизведение звука
        time.sleep(2.5)
    except pymysql.MySQLError as err:
        print("Ошибка MySQL:", err)
    finally:
        cursor.close()
        conn.close()


def scan_qr_and_save():
    """
    Считывает изображение с камеры в реальном времени,
    распознаёт QR-код, парсит как JSON и добавляет в БД.
    Для завершения нажмите 'q' в окне просмотра.
    """
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Не удалось открыть камеру.")
        return

    print("Сканирование запущено. Наведите камеру на QR-код. Для выхода нажмите 'q'.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Не удалось считать кадр с камеры.")
            break

        decoded_objects = pyzbar.decode(frame)
        for obj in decoded_objects:
            qr_data = obj.data.decode('utf-8', errors='replace')
            print("QR-код найден:", qr_data)

            try:
                product_info = json.loads(qr_data)
                insert_product(product_info)
            except json.JSONDecodeError:
                print("Ошибка: данные в QR не являются валидным JSON.")


        cv2.imshow("QR Scanner", frame)


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    scan_qr_and_save()

if __name__ == "__main__":
    main()
