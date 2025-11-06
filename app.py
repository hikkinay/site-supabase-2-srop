from flask import Flask, render_template, request, redirect, url_for, flash, session
from supabase import create_client, Client

# ---- Supabase ----
SUPABASE_URL = "https://nvvnnmcoyopyjwhdbpkr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im52dm5ubWNveW9weWp3aGRicGtyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIzNzA2OTIsImV4cCI6MjA3Nzk0NjY5Mn0.4s0YucPF25sQKjUBjVK0KWF6T4qz5soAva1LKdGkgZE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = "your_flask_secret_key"


# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            # Проверяем username
            existing_user = supabase.table("users").select("*").eq("username", username).execute()

            if existing_user.data:
                flash("Пользователь с таким именем уже существует")
                return redirect(url_for('register'))

            # Создаем пользователя в Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            # Добавляем в таблицу users с тем же ID
            if auth_response.user:
                supabase.table("users").insert({
                    "id": auth_response.user.id,
                    "email": email,
                    "username": username,
                    "is_admin": False  # По умолчанию обычный пользователь
                }).execute()

                flash("Регистрация успешна, войдите в систему")
                return redirect(url_for('login'))
            else:
                flash("Ошибка при регистрации")
                return redirect(url_for('register'))

        except Exception as e:
            err_msg = str(e)
            if "23505" in err_msg or "duplicate key" in err_msg:
                if "username" in err_msg:
                    flash("Пользователь с таким именем уже существует")
                elif "email" in err_msg:
                    flash("Пользователь с таким email уже существует")
                else:
                    flash("Пользователь уже существует")
            elif "User already registered" in err_msg:
                flash("Пользователь с таким email уже зарегистрирован")
            else:
                flash(f"Ошибка при регистрации: {err_msg}")
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            auth = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if auth.user is None:
                flash("Неверный логин или пароль")
                return redirect(url_for('login'))

            # Сохраняем данные пользователя
            session['user'] = {
                "id": auth.user.id,
                "email": email,
                "access_token": auth.session.access_token
            }

            return redirect(url_for('dashboard'))

        except Exception as e:
            err_msg = str(e)
            if "Email not confirmed" in err_msg:
                flash("Ваш email ещё не подтверждён. Проверьте почту.")
            elif "Invalid login credentials" in err_msg:
                flash("Неверный логин или пароль")
            else:
                flash(f"Ошибка: {err_msg}")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']['id']

    try:
        # Получаем данные пользователя
        user_data = supabase.table("users").select("*").eq("id", user_id).single().execute().data

        print(f"Текущий пользователь: {user_data}")

        # Получаем задачи пользователя
        tasks = supabase.table("tasks").select("*").eq("user_id", user_id).execute().data

        if user_data['is_admin']:  # ИЗМЕНЕНО: проверяем is_admin вместо role
            # Админ видит всех пользователей и их задачи
            all_users = supabase.table("users").select("*").execute().data
            all_tasks = supabase.table("tasks").select("*").execute().data

            # Группируем задачи по пользователям
            users_with_tasks = []
            for user in all_users:
                user_tasks = [task for task in all_tasks if task['user_id'] == user['id']]
                users_with_tasks.append({
                    'id': user['id'],
                    'email': user['email'],
                    'username': user['username'],
                    'is_admin': user['is_admin'],  # ИЗМЕНЕНО
                    'tasks': user_tasks
                })

            # Свои задачи админа
            my_tasks = [task for task in all_tasks if task['user_id'] == user_id]

            return render_template("dashboard.html",
                                   current_user=user_data,
                                   my_tasks=my_tasks,
                                   users_with_tasks=users_with_tasks,
                                   is_admin=True)  # ИЗМЕНЕНО
        else:
            # Обычный пользователь видит только свои задачи
            return render_template("dashboard.html",
                                   current_user=user_data,
                                   tasks=tasks,
                                   is_admin=False)  # ИЗМЕНЕНО
    except Exception as e:
        flash(f"Ошибка при загрузке данных: {str(e)}")
        print(f"ОШИБКА dashboard: {e}")
        return redirect(url_for('login'))


@app.route('/task/add', methods=['POST'])
def add_task():
    if 'user' not in session:
        return redirect(url_for('login'))

    title = request.form['title']
    user_id = session['user']['id']

    try:
        supabase.table("tasks").insert({"title": title, "user_id": user_id}).execute()
        flash("Задача добавлена")
    except Exception as e:
        flash(f"Ошибка при добавлении задачи: {str(e)}")

    return redirect(url_for('dashboard'))


@app.route('/task/delete/<uuid:id>')
def delete_task(id):
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']['id']

    try:
        user_data = supabase.table("users").select("*").eq("id", user_id).single().execute().data
        task_data = supabase.table("tasks").select("*").eq("id", str(id)).single().execute().data

        # Проверяем права: админ может удалять все, пользователь - только свои
        if not user_data['is_admin'] and task_data['user_id'] != user_id:  # ИЗМЕНЕНО
            flash("Нельзя удалять чужие задачи!")
            return redirect(url_for('dashboard'))

        supabase.table("tasks").delete().eq("id", str(id)).execute()
        flash("Задача удалена")
    except Exception as e:
        flash(f"Ошибка при удалении задачи: {str(e)}")

    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    flash("Вы вышли из системы")
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)