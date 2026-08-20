import os
from dotenv import load_dotenv
import pandas as pd 
import numpy as np 
from psycopg2 import OperationalError
from sqlalchemy import create_engine, text

load_dotenv()

df = pd.read_csv('ventas_colombia.csv')



# Limpieza de fecha
df['Fecha'] = df['Fecha'].fillna('1900-01-01')


df['Fecha'] = pd.to_datetime(
    df['Fecha'].str.replace(r'^(\d{2})/(\d{2})/(\d{4})$', r'\3-\2-\1', regex=True),
    format='mixed',
    errors='coerce'
).fillna(pd.Timestamp('1900-01-01'))

# convertir a string y capitalizar los nombres de las columnas

df['Producto'] = df['Producto'].astype(str).str.strip().str.capitalize()
df['Categoria'] = df['Categoria'].astype(str).str.strip().str.capitalize()

df['ID_Cliente'] = df['ID_Cliente'].astype(str).str.strip().str.capitalize()


df['Precio_Unitario'] = pd.to_numeric(df['Precio_Unitario'], errors='coerce').astype(float)
df['Monto_Total'] = pd.to_numeric(df['Monto_Total'], errors='coerce').astype(float)
df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(pd.Int64Dtype())

# Limpieza de datos faltantes y duplicados basando en datos relacionales en ID_Metodo_Pago y ID_Categoria, reemplazando valores desconocidos con None y luego rellenando hacia adelante y hacia atrás.
df['Metodo_Pago'] = df['Metodo_Pago'].replace('Metodo de pago desconocido', None)
df['Metodo_Pago'] = df.groupby('ID_Metodo_Pago')['Metodo_Pago'].transform(lambda x: x.ffill().bfill())


df['Categoria'] = df['Categoria'] .replace ('Categoria desconocida', None)
df['Categoria'] = df.groupby('ID_Categoria')['Categoria'].transform(lambda x: x.ffill().bfill())

df['Categoria'] = df['Categoria'].fillna('Categoria desconocida')


df['Metodo_Pago'] = df['Metodo_Pago']. fillna('Metodo de pago desconocido')

df['Ciudad'] = df['Ciudad'].fillna('Ciudad desconocido')

df['Monto_Total'] = df['Monto_Total'].fillna(0)
df['Precio_Unitario'] = df['Precio_Unitario'].fillna(0)

df['Cantidad'] = df['Cantidad'].abs()
df['Precio_Unitario'] = df['Precio_Unitario'].abs()

df['Monto_Total'] = df['Cantidad'] * df['Precio_Unitario']

print(df.info())

df = df.drop_duplicates(subset=['ID_Venta'], keep='first').reset_index(drop=True)

df.columns = df.columns.str.lower()


df.to_csv('ventas_limpias.csv', index=False, encoding='utf-8-sig')

# Lectura de las variables de entorno
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")  
PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

# Construcción de la URL de conexión
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

# Creación y verificación del motor de base de datos
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print(f" Conexión exitosa a '{DB_NAME}' en {HOST}:{PORT}\n")
except OperationalError as e:
    print(f" Error de credenciales o red al conectar a PostgreSQL: {e}\n")
except Exception as e:
    print(f" Error inesperado: {e}\n")


clientes = (
    df[["id_cliente", "nombre_cliente", "ciudad"]]
    .drop_duplicates(subset=["id_cliente"], keep="first")
    .reset_index(drop=True)
)

categorias = (
    df[["id_categoria", "categoria"]].drop_duplicates().reset_index(drop=True)
)

productos = (
    df[["id_producto", "producto", "id_categoria"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

metodos_pago = (
    df[["id_metodo_pago", "metodo_pago"]].drop_duplicates().reset_index(drop=True)
)

# TABLA DE HECHOS 

ventas = df[
    [
        "id_venta",
        "fecha",
        "id_cliente",
        "id_producto",
        "id_metodo_pago",
        "cantidad",
        "precio_unitario",
        "monto_total",
    ]
].drop_duplicates()

#  CONEXIÓN Y CARGA A POSTGRESQL (Reemplazar 'engine' por tu conexión activa)

clientes.to_sql("clientes", engine, if_exists="replace", index=False)
categorias.to_sql("categorias", engine, if_exists="replace", index=False)
productos.to_sql("productos", engine, if_exists="replace", index=False)
metodos_pago.to_sql("metodos_pago", engine, if_exists="replace", index=False)
ventas.to_sql("ventas", engine, if_exists="replace", index=False)


with engine.connect() as conn:
    conn.execute(text("ALTER TABLE clientes ADD PRIMARY KEY (id_cliente);"))
    conn.execute(text("ALTER TABLE categorias ADD PRIMARY KEY (id_categoria);"))
    conn.execute(text("ALTER TABLE productos ADD PRIMARY KEY (id_producto);"))
    conn.execute(
        text("ALTER TABLE metodos_pago ADD PRIMARY KEY (id_metodo_pago);")
    )
    conn.execute(text("ALTER TABLE ventas ADD PRIMARY KEY (id_venta);"))

    # Definir Claves Foráneas (FK) entre entidades
    conn.execute(
        text(
            "ALTER TABLE productos ADD CONSTRAINT fk_categoria FOREIGN KEY"
            " (id_categoria) REFERENCES categorias(id_categoria);"
        )
    )

    # Definir Claves Foráneas (FK) hacia la tabla de hechos
    conn.execute(
        text(
            "ALTER TABLE ventas ADD CONSTRAINT fk_cliente FOREIGN KEY"
            " (id_cliente) REFERENCES clientes(id_cliente);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE ventas ADD CONSTRAINT fk_producto FOREIGN KEY"
            " (id_producto) REFERENCES productos(id_producto);"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE ventas ADD CONSTRAINT fk_metodo_pago FOREIGN KEY"
            " (id_metodo_pago) REFERENCES metodos_pago(id_metodo_pago);"
        )
    )

    conn.commit()