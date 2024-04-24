import sqlite3


class Database:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            "tg_id INTEGER, "
                            "name TEXT,"
                            "address TEXT,"
                            "city TEXT,"
                            "country TEXT,"
                            "phone TEXT,"
                            "email TEXT,"
                            "shipping_type TEXT"
                            ")"
                            )
        self.cursor.execute("CREATE TABLE IF NOT EXISTS orders("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            "tg_id INTEGER,"
                            "type TEXT,"
                            "size TEXT,"
                            "color TEXT"
                            ")"
                            )
        self.cursor.execute("CREATE TABLE IF NOT EXISTS front_print("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            "tg_id INTEGER,"
                            "position_x INTEGER,"
                            "position_y INTEGER,"
                            "width INTEGER,"
                            "height INTEGER,"
                            "bg_deleted BOOLEAN,"
                            "angle INTEGER"
                            ")"
                            )
        self.cursor.execute("CREATE TABLE IF NOT EXISTS back_print("
                            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            "tg_id INTEGER,"
                            "position_x INTEGER,"
                            "position_y INTEGER,"
                            "width INTEGER,"
                            "height INTEGER,"
                            "bg_deleted BOOLEAN,"
                            "angle INTEGER"
                            ")"
                            )
        self.conn.commit()

    def close(self):
        self.conn.close()
