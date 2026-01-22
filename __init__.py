from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# ---------- Fonctions utilitaires BDD ----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Routes principales ----------

@app.route("/")
def home():
    """
    Page d'accueil : lien vers la liste et vers l'ajout de tâches
    """
    return render_template("home.html")


@app.route("/tasks")
def list_tasks():
    """
    Afficher toutes les tâches
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY completed, due_date IS NULL, due_date")
    tasks = cur.fetchall()
    conn.close()
    return render_template("tasks.html", tasks=tasks)


@app.route("/tasks/add", methods=["GET", "POST"])
def add_task():
    """
    Ajouter une tâche (GET = formulaire, POST = traitement)
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date") or None  # peut être vide

        if title:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tasks (title, description, due_date, completed) VALUES (?, ?, ?, ?)",
                (title, description, due_date, 0),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("list_tasks"))
        # si pas de titre, on réaffiche le formulaire avec un message simple
        error = "Le titre est obligatoire."
        return render_template("add_task.html", error=error)

    return render_template("add_task.html")


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    """
    Supprimer une tâche
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("list_tasks"))


@app.route("/tasks/<int:task_id>/done", methods=["POST"])
def mark_task_done(task_id):
    """
    Marquer une tâche comme terminée
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("list_tasks"))


# ---------- Route de debug (optionnelle) ----------

@app.route("/debug/tasks")
def debug_tasks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    tasks = cur.fetchall()
    conn.close()
    return "<br>".join(
        [f"{t['id']} - {t['title']} - terminé={t['completed']}" for t in tasks]
    )


# ---------- Lancement local ----------

if __name__ == "__main__":
    app.run(debug=True)
