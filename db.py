import sqlite3
conn = sqlite3.connect('payments.db')
cursor = conn.cursor()



def initialize_db():
    try:
        conn = sqlite3.connect('payments.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                number TEXT,
                serial_key TEXT,
                pin TEXT,
                max_allowed_checks INTEGER DEFAULT 3
            )
        ''')

        conn.commit()
        conn.close()

        # app.logger.info('Database initialized successfully')
    except Exception as e:
        # app.logger.error('Error initializing database: %s', e)
        raise
    
    
def get_column_index(db_name, table_name, column_name):

    conn = sqlite3.connect(f'{db_name}.db')
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    
    for index, column in enumerate(columns):
        if column[1] == column_name:
            return index
    
    raise ValueError(f"Column '{column_name}' not found in table '{table_name}'")
    
