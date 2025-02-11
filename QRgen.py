 
from flask import Flask, render_template_string, request, send_file
import qrcode
import json
import io
from datetime import datetime, timedelta
app = Flask(__name__)


html_page = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>QR Генератор</title>
    <!-- Подключаем Bootstrap 5 из CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Дополнительные стили для улучшения дизайна -->
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 800px;
        }
        .card {
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .card-body {
            padding: 20px;
        }
        .form-control {
            border-radius: 10px;
        }
        .btn-primary {
            border-radius: 10px;
        }
        .qr-result {
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <!-- Навигационная панель -->
    <nav class="navbar navbar-expand-lg navbar-light bg-light shadow-sm">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">QR Генератор</a>
        </div>
    </nav>

    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-md-8 col-lg-6">
                <h1 class="text-center mb-4">Форма для ввода данных о продукте</h1>

                <form method="POST" action="/" class="card p-4 shadow-sm">
                    <div class="mb-3">
                        <label for="product_type" class="form-label">1) Тип продукта</label>
    <select class="form-control" id="product_type" name="product_type" required>
        <option value="" disabled selected>Выберите категорию</option>
        <option value="молочка">Молочка</option>
        <option value="соусы">Соусы</option>
        <option value="мясо">Мясо</option>
        <option value="овощи">Овощи</option>
        <option value="хлеб">Хлеб</option>
        <option value="фрукты">Фрукты</option>
        <option value="напитки">Напитки</option>
        <option value="яйца">Яйца</option>
        <option value="сыры">Сыры</option>
        <option value="масло">Масло</option>
        <option value="рыба">Рыба</option>
        <option value="курица">Курица</option>
    </select>
                    </div>

                    <div class="mb-3">
                        <label for="product_name" class="form-label">2) Имя продукта</label>
                        <input type="text" class="form-control" id="product_name" name="product_name"
                               placeholder="Название (например, 'Молоко 'Домик в деревне'')" required>
                    </div>

                    <div class="mb-3">
                        <label for="production_time" class="form-label">3) Время производства</label>
                        <input type="text" class="form-control" id="production_time" name="production_time"
                               placeholder="Формат: ГГГГ-ММ-ДД Ч:М" required>
                    </div>

                    <div class="mb-3">
                        <label for="expiration_date" class="form-label">
                            4) День истечения срока годности (ГГГГ-ММ-ДД)
                            или "через X дней Y часов"
                        </label>
                        <input type="text" class="form-control" id="expiration_date" name="expiration_date"
                               placeholder="Например, 2025-02-15 или через 10 дней 3 часа" required>
                    </div>

                    <div class="mb-3">
                        <label for="quantity_items" class="form-label">5) Количество штук</label>
                        <input type="number" class="form-control" id="quantity_items" name="quantity_items"
                               value="1" required>
                    </div>

                    <div class="mb-3">
                        <label for="quantity_mass" class="form-label">6) Сколько мл или г</label>
                        <input type="text" class="form-control" id="quantity_mass" name="quantity_mass"
                               placeholder="Например, '500 мл' или '200 г'" required>
                    </div>

                    <div class="mb-3">
                        <label for="kbzhu" class="form-label">
                            7) КБЖУ (калории, белки, жиры, углеводы)
                        </label>
                        <input type="text" class="form-control" id="kbzhu" name="kbzhu"
                               placeholder="Например, '200 ккал, Б=10, Ж=5, У=30'" required>
                    </div>

                    <div class="mb-3">
                        <label for="allergens" class="form-label">8) Аллергены (через запятую)</label>
                        <input type="text" class="form-control" id="allergens" name="allergens"
                               placeholder="Например, орехи, лактоза">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Сгенерировать QR</button>
                </form>

                {% if qr_generated %}
                <div class="qr-result card text-center mt-5 shadow-sm">
                    <div class="card-body">
                        <h2 class="card-title">Результат</h2>
                        <img src="{{ url_for('qr_code') }}" class="img-fluid" alt="qr code">
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Подключаем Bootstrap JS (не обязательно, если не нужны интерактивные компоненты) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    qr_generated = False
    if request.method == "POST":
        product_type = request.form.get("product_type", "")
        product_name = request.form.get("product_name", "")
        production_time = request.form.get("production_time", "")
        expiration_date_input = request.form.get("expiration_date", "")
        quantity_items = request.form.get("quantity_items", "0")
        quantity_mass = request.form.get("quantity_mass", "")
        kbzhu = request.form.get("kbzhu", "")
        allergens = request.form.get("allergens", "")


        try:
            production_dt = datetime.strptime(production_time, "%Y-%m-%d %H:%M")
        except ValueError:
            production_dt = datetime.now()


        expiration_date_str = ""
        if expiration_date_input.lower().startswith("через"):
            parts = expiration_date_input.lower().replace("через", "").split()
            days, hours = 0, 0
            if "дней" in parts:
                idx_days = parts.index("дней")
                if idx_days > 0:
                    days = int(parts[idx_days - 1])
            if "часов" in parts:
                idx_hours = parts.index("часов")
                if idx_hours > 0:
                    hours = int(parts[idx_hours - 1])
            expiration_dt = production_dt + timedelta(days=days, hours=hours)
            expiration_date_str = expiration_dt.strftime("%Y-%m-%d")
        else:
            expiration_date_str = expiration_date_input


        measurement_type = "вес" if "г" in quantity_mass.lower() or "кг" in quantity_mass.lower() else "объем"


        data_json = {
            "name": product_name,
            "type": product_type,
            "production_date": production_dt.strftime("%Y-%m-%d"),
            "expiration_date": expiration_date_str,
            "quantity": int(quantity_items),
            "measurement_unit": quantity_mass,
            "measurement_type": measurement_type,
            "nutritional_value": kbzhu,
            "allergens": allergens
        }


        app.config['QR_DATA_JSON'] = json.dumps(data_json, ensure_ascii=False)


        app.config['QR_DATA'] = data_json
        qr_generated = True

    return render_template_string(html_page, qr_generated=qr_generated)


@app.route("/qr_code")
def qr_code():
    data_json = app.config.get('QR_DATA', {})
    qr_data = json.dumps(data_json, ensure_ascii=False)


    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5, border=1
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


if __name__ == "__main__":
    app.run(debug=True)
