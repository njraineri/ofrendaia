import sqlite3
import os

DATABASE_FILE = 'ofrendas.db'

def get_db():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Para acceder a las columnas por nombre
    # Habilitar claves foráneas (importante para la integridad referencial)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Inicializa la base de datos si no existe."""
    print("--- Iniciando init_db() ---") # Mensaje de depuración
    if not os.path.exists(DATABASE_FILE):
        print(f"Archivo DB no encontrado: {DATABASE_FILE}. Creando base de datos inicial...") # Mensaje de depuración
        conn = get_db()
        cursor = conn.cursor()
        try:
            print("Intentando crear tabla leaders...") # Mensaje de depuración
            cursor.execute('''
                CREATE TABLE leaders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    direccion TEXT,
                    dia TEXT,
                    hora TEXT
                )
            ''')
            print("Tabla leaders creada con éxito.") # Mensaje de depuración
            print("Intentando crear tabla offerings...") # Mensaje de depuración
            cursor.execute('''
                CREATE TABLE offerings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL, -- Formato YYYY-MM-DD
                    leader_id INTEGER NOT NULL,
                    FOREIGN KEY (leader_id) REFERENCES leaders (id) ON DELETE CASCADE
                )
            ''')
            print("Tabla offerings creada con éxito.") # Mensaje de depuración
            conn.commit()
            print("Cambios de creación de tablas confirmados.") # Mensaje de depuración
        except Exception as e:
            print(f"ERROR durante la creación de tablas: {e}") # Mensaje de depuración con error
            conn.rollback()
        finally:
            conn.close()
            print("Conexión cerrada después de init_db().") # Mensaje de depuración
        print("Base de datos creada (si no existía).") # Mensaje de depuración
    else:
        print(f"Archivo DB encontrado: {DATABASE_FILE}.") # Mensaje de depuración
        # Asegurarse de que las claves foráneas estén habilitadas al inicio
        conn = get_db()
        conn.execute("PRAGMA foreign_keys = ON")
        # --- VERIFICAR Y AÑADIR COLUMNAS SI FALTAN ---
        # Este bloque intenta actualizar la tabla leaders si le faltan las columnas
        # Puede ser útil si tienes una DB vieja.
        try:
            cursor = conn.cursor()
            # Intenta seleccionar las nuevas columnas para ver si existen
            cursor.execute("SELECT direccion, dia, hora FROM leaders LIMIT 0") # Usar LIMIT 0 es más eficiente
            print("Columnas direccion, dia, hora ya existen.") # Mensaje de depuración
        except sqlite3.OperationalError as e:
            print(f"OperacionalError al verificar columnas ({e}). Intentando añadir columnas...") # Mensaje de depuración
            try:
                conn.execute("ALTER TABLE leaders ADD COLUMN direccion TEXT")
                conn.execute("ALTER TABLE leaders ADD COLUMN dia TEXT")
                conn.execute("ALTER TABLE leaders ADD COLUMN hora TEXT")
                conn.commit()
                print("Columnas añadidas a la tabla leaders con éxito.") # Mensaje de depuración
            except Exception as add_col_e:
                print(f"Error **grave** al intentar añadir columnas con ALTER TABLE: {add_col_e}") # Mensaje de depuración
                print("Puede que la base de datos esté corrupta o la tabla leaders no exista en absoluto.") # Mensaje de depuración
        except Exception as other_e:
             print(f"Otro error inesperado al verificar/añadir columnas: {other_e}") # Mensaje de depuración
        finally:
             conn.close()
             print("Verificación/adición de columnas finalizada.") # Mensaje de depuración

    print("--- Fin de init_db() ---") # Mensaje de depuración


# --- Funciones para Líderes ---

def add_leader(name, direccion=None, dia=None, hora=None):
    """Agrega un nuevo líder a la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO leaders (name, direccion, dia, hora) VALUES (?, ?, ?, ?)",
                       (name, direccion, dia, hora))
        conn.commit()
        return True # Indicamos éxito (líder agregado)
    except sqlite3.IntegrityError:
        # Ocurre si el nombre del líder ya existe (debido a UNIQUE NOT NULL)
        return False # Indicamos fallo (líder ya existe)
    except Exception as e:
        print(f"Error al agregar líder: {e}")
        conn.rollback() # Revertir cambios si hay un error
        return False
    finally:
        conn.close()

def update_leader(leader_id, new_name, new_direccion=None, new_dia=None, new_hora=None):
    """Actualiza un líder existente."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Primero, verifica si ya existe otro líder con el nuevo nombre (si el nombre cambia)
        cursor.execute("SELECT id FROM leaders WHERE name = ? AND id != ?", (new_name, leader_id))
        if cursor.fetchone() is not None:
            return False # Ya existe otro líder con ese nombre

        cursor.execute("""
            UPDATE leaders
            SET name = ?, direccion = ?, dia = ?, hora = ?
            WHERE id = ?
        """, (new_name, new_direccion, new_dia, new_hora, leader_id))
        conn.commit()
        # Verifica si se actualizó alguna fila (el líder con ese ID existía)
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al actualizar líder: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_leader(leader_id):
    """Elimina un líder y sus ofrendas asociadas (ON DELETE CASCADE en la tabla offerings)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM leaders WHERE id = ?", (leader_id,))
        conn.commit()
        # rowcount > 0 indica que se eliminó al menos un líder con ese ID
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar líder: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_all_leaders(search_term=None):
    """Obtiene todos los líderes, opcionalmente filtrados por nombre."""
    print("DEBUG: Ejecutando get_all_leaders()") # Mensaje de depuración
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT id, name, direccion, dia, hora FROM leaders" # Aseguramos que seleccionamos los nuevos campos
    params = []
    if search_term:
        query += " WHERE name LIKE ?"
        params.append('%' + search_term + '%')
    query += " ORDER BY name ASC"

    # Debug: Imprimir la consulta y los parámetros (descomentar para depuración)
    # print("SQL Query:", query)
    # print("Parameters:", params)

    try:
        cursor.execute(query, params)
        leaders = cursor.fetchall()
        print(f"DEBUG: get_all_leaders() recuperó {len(leaders)} líderes.") # Mensaje de depuración
        return leaders
    except sqlite3.OperationalError as e:
        print(f"ERROR en get_all_leaders() (OperationalError): {e}") # Mensaje de depuración
        print("Esto generalmente significa que la tabla 'leaders' no existe.") # Mensaje de depuración
        raise e # Re-lanzar el error para que se vea en la traza principal
    except Exception as e:
        print(f"ERROR inesperado en get_all_leaders(): {e}") # Mensaje de depuración
        raise e # Re-lanzar otros errores
    finally:
        conn.close()
        print("DEBUG: Conexión cerrada después de get_all_leaders().") # Mensaje de depuración


def get_leader_by_id(leader_id):
    """Obtiene un líder por su ID."""
    conn = get_db()
    cursor = conn.cursor()
    # Aseguramos que seleccionamos los nuevos campos
    cursor.execute("SELECT id, name, direccion, dia, hora FROM leaders WHERE id = ?", (leader_id,))
    leader = cursor.fetchone()
    conn.close()
    return leader

# --- Funciones para Ofrendas ---

def add_offering(amount, date, leader_id):
    """Agrega una nueva ofrenda a la base de datos."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO offerings (amount, date, leader_id) VALUES (?, ?, ?)",
                       (amount, date, leader_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al agregar ofrenda: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_offerings_history(start_date=None, end_date=None, leader_id=None):
    """Obtiene el historial de ofrendas, con filtros opcionales."""
    print("DEBUG: Ejecutando get_offerings_history()") # Mensaje de depuración
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT o.id, o.amount, o.date, l.name as leader_name, o.leader_id
        FROM offerings o
        JOIN leaders l ON o.leader_id = l.id
    """
    filters = []
    params = []

    if start_date:
        filters.append("o.date >= ?")
        params.append(start_date)
    if end_date:
        filters.append("o.date <= ?")
        params.append(end_date)
    # Filtro por líder específico
    if leader_id and leader_id != 'all': # 'all' significa sin filtro de líder
         try:
             lid = int(leader_id) # Asegurarse que es un entero válido
             filters.append("o.leader_id = ?")
             params.append(lid)
         except ValueError:
             print(f"ID de líder inválido recibido en get_offerings_history: {leader_id}") # Mensaje de depuración
             # Si el ID del líder es inválido, no aplicamos el filtro y posiblemente retornamos una lista vacía más adelante
             pass # Continuamos sin añadir este filtro si el ID es inválido


    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += " ORDER BY o.date DESC, l.name ASC" # Ordenar por fecha descendente y luego por nombre de líder

    # Debug: Imprimir la consulta y los parámetros (descomentar para depuración)
    # print("SQL Query:", query)
    # print("Parameters:", params)

    try:
        cursor.execute(query, params)
        history = cursor.fetchall()
        print(f"DEBUG: get_offerings_history() recuperó {len(history)} ofrendas.") # Mensaje de depuración
        return history
    except sqlite3.OperationalError as e:
        print(f"ERROR en get_offerings_history() (OperationalError): {e}") # Mensaje de depuración
        print("Esto puede significar que la tabla 'offerings' o 'leaders' no existe o hay un problema con el JOIN.") # Mensaje de depuración
        raise e # Re-lanzar el error
    except Exception as e:
        print(f"ERROR inesperado en get_offerings_history(): {e}") # Mensaje de depuración
        raise e # Re-lanzar otros errores
    finally:
        conn.close()
        print("DEBUG: Conexión cerrada después de get_offerings_history().") # Mensaje de depuración


def update_offering(offering_id, amount, date, leader_id):
    """Actualiza una ofrenda existente."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE offerings
            SET amount = ?, date = ?, leader_id = ?
            WHERE id = ?
        """, (amount, date, leader_id, offering_id))
        conn.commit()
        # rowcount > 0 indica que se actualizó al menos una ofrenda con ese ID
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al actualizar ofrenda {offering_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_offering(offering_id):
    """Elimina una ofrenda por su ID."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM offerings WHERE id = ?", (offering_id,))
        conn.commit()
        # rowcount > 0 indica que se eliminó al menos una ofrenda con ese ID
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error al eliminar ofrenda {offering_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_offering_by_id(offering_id):
    """Obtiene una ofrenda por su ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, date, leader_id FROM offerings WHERE id = ?", (offering_id,))
    offering = cursor.fetchone()
    conn.close()
    return offering

# --- Inicialización de la base de datos ---
# Intentar inicializar la DB al inicio del script.
# Esto asegura que init_db se ejecuta cuando se importa database.py
try:
    print("DEBUG: Intentando llamar a init_db() al importar database.py")
    init_db()
    print("DEBUG: Llamada a init_db() al importar finalizada.")
except Exception as e:
    print(f"DEBUG: ERROR llamando a init_db() al importar: {e}")