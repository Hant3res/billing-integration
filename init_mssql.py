import pyodbc
import time

print("Waiting for SQL Server to be ready...")
time.sleep(10)

conn_str = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;UID=sa;PWD=YourStrongPass123;TrustServerCertificate=yes"

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Создание базы данных
    cursor.execute("CREATE DATABASE billing_db")
    print("Database 'billing_db' created")
    
    conn.close()
    
    # Подключение к новой БД
    conn2 = pyodbc.connect(conn_str + ";DATABASE=billing_db")
    cursor2 = conn2.cursor()
    
    # Таблица tariffs
    cursor2.execute('''
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tariffs' AND xtype='U')
    CREATE TABLE tariffs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        price FLOAT NOT NULL,
        currency NVARCHAR(3) DEFAULT 'RUB',
        stock INT DEFAULT 10
    )
    ''')
    
    # Таблица invoices
    cursor2.execute('''
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='invoices' AND xtype='U')
    CREATE TABLE invoices (
        id INT IDENTITY(1,1) PRIMARY KEY,
        client_id INT NOT NULL,
        tariff_ids NVARCHAR(500) NOT NULL,
        total_amount FLOAT NOT NULL,
        currency NVARCHAR(3) DEFAULT 'RUB',
        status NVARCHAR(20) DEFAULT 'pending',
        created_at NVARCHAR(50)
    )
    ''')
    
    # Таблица payments
    cursor2.execute('''
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='payments' AND xtype='U')
    CREATE TABLE payments (
        id INT IDENTITY(1,1) PRIMARY KEY,
        invoice_id INT NOT NULL,
        amount FLOAT NOT NULL,
        payment_method NVARCHAR(50) DEFAULT 'card',
        status NVARCHAR(20) DEFAULT 'pending',
        transaction_id NVARCHAR(100) NOT NULL
    )
    ''')
    
    # Тестовые тарифы
    cursor2.execute("DELETE FROM tariffs")
    cursor2.execute("INSERT INTO tariffs (name, price, stock) VALUES ('Hosting Basic', 500, 5)")
    cursor2.execute("INSERT INTO tariffs (name, price, stock) VALUES ('Hosting Pro', 1500, 3)")
    cursor2.execute("INSERT INTO tariffs (name, price, stock) VALUES ('Extra Disk 10GB', 300, 0)")
    cursor2.execute("INSERT INTO tariffs (name, price, stock) VALUES ('SSL Certificate', 1000, 10)")
    conn2.commit()
    
    print("Tables created and test data inserted")
    conn2.close()
    
except Exception as e:
    print(f"Error: {e}")
