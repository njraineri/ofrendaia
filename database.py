import psycopg2
import psycopg2.extras
import os

# URL de la base de datos PostgreSQL en Render (ajustala si es necesario)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ofrendaia_user:ZGuO8iA1RnGYVOqe0AEisCSOY83dpEmi@dpg-d0c0g2ruibrs73dnfrg0-a/ofrendaia")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def init_db():
    print("--- Iniciando init_db() con PostgreSQL ---")
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaders (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                direccion TEXT,
                dia TEXT,
                hora TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offerings (
                id SERIAL PRIMARY KEY,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                leader_id INTEGER NOT NULL,
                FOREIGN KEY (leader_id) REFERENCES leaders (id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        print("Tablas creadas o ya existentes.")
    except Exception as e:
        print(f"Error en init_db: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def add_leader(name, direccion=None, dia=None, hora=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO leaders (name, direccion, dia, hora)
            VALUES (%s, %s, %s, %s)
        """, (name, direccion, dia, hora))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    except Exception as e:
        print(f"Error al agregar líder: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_leader(leader_id, new_name, new_direccion=None, new_dia=None, new_hora=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM leaders WHERE name = %s AND id != %s", (new_name, leader_id))
        if cursor.fetchone():
            return False
        cursor.execute("""
            UPDATE leaders
            SET name = %s, direccion = %s, dia = %s, hora = %s
            WHERE id = %s
        """, (new_name, new_direccion, new_dia, new_hora, leader_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al actualizar líder: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def delete_leader(leader_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM leaders WHERE id = %s", (leader_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar líder: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_all_leaders(search_term=None):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT id, name, direccion, dia, hora FROM leaders"
    params = []
    if search_term:
        query += " WHERE name ILIKE %s"
        params.append(f'%{search_term}%')
    query += " ORDER BY name ASC"
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_leader_by_id(leader_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, name, direccion, dia, hora FROM leaders WHERE id = %s", (leader_id,))
    leader = cursor.fetchone()
    cursor.close()
    conn.close()
    return leader

def add_offering(amount, date, leader_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO offerings (amount, date, leader_id)
            VALUES (%s, %s, %s)
        """, (amount, date, leader_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al agregar ofrenda: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_offerings_history(start_date=None, end_date=None, leader_id=None):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = """
        SELECT o.id, o.amount, o.date, l.name as leader_name, o.leader_id
        FROM offerings o
        JOIN leaders l ON o.leader_id = l.id
    """
    filters = []
    params = []
    if start_date:
        filters.append("o.date >= %s")
        params.append(start_date)
    if end_date:
        filters.append("o.date <= %s")
        params.append(end_date)
    if leader_id and leader_id != 'all':
        try:
            lid = int(leader_id)
            filters.append("o.leader_id = %s")
            params.append(lid)
        except ValueError:
            print(f"ID de líder inválido: {leader_id}")
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY o.date DESC, l.name ASC"
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
