import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, db_host, db_port, db_user, db_pass, db_name):
        try:
            self.connection = mysql.connector.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                passwd=db_pass,
                database=db_name
            )
            if self.connection.is_connected():
                print("Conexión a la base de datos establecida.")
        except Error as e:
            print("Error al conectar a MySQL", e)

    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print("Conexión a la base de datos cerrada.")

    def execute_query(self, query, data):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, data)
            self.connection.commit()
            print(cursor.rowcount, "registro insertado.")
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")

    def insert_user_log(self, data):
        print("Insertando registro en user_log...")
        query = """
        INSERT INTO user_log (user_id, username, command_time, date, command)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.execute_query(query, data)

    def insert_status(self, data):
        print("Actualizando estado del servicio status...")
        query = """
        INSERT INTO service_status (service_name, version, log_level, status, models_info)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        service_name = VALUES(service_name),
        version = VALUES(version),
        log_level = VALUES(log_level),
        status = VALUES(status),
        models_info = VALUES(models_info)
        """
        self.execute_query(query, data)

    def insert_sentiment(self, data):
        print("Insertando registro en sentiment...")
        query = """
        INSERT INTO sentiment (user_id, texto_analizado, label, score, fecha_hora, tiempo_ejecucion, modelos, longitud_texto, uso_memoria, uso_cpu)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, data)

    def insert_analysis(self, data):
        print("Insertando registro en analysis...")
        query = """
        INSERT INTO analysis (user_id, texto_analizado, pos_tags_resumen, pos_tags_conteo, ner_resumen, ner_conteo, sentimiento_label, sentimiento_score, fecha_hora, tiempo_ejecucion, modelos, longitud_texto, uso_memoria, uso_cpu)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_query(query, data)

    def get_user_ids(self):
        print("Obteniendo user_ids...")
        query = "SELECT DISTINCT user_id FROM user_log"
        user_ids = set()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                user_ids = {row[0] for row in result}
        except Error as e:
            print(f"Error al obtener los user_ids: {e}")
        return user_ids

    def get_status(self):
        query = "SELECT * FROM service_status LIMIT 1"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchone()
        except Error as e:
            print(f"Error al obtener el estado del servicio: {e}")
            return None

