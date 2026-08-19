import os
from dotenv import load_dotenv
import pandas as pd 
import numpy as np 
from psycopg2 import OperationalError
from sqlalchemy import create_engine, text

load_dotenv()

df = pd.read_csv('ventas_colombia.csv')

df['Fecha'] = df['Fecha'].fillna('01-01-1900')


df['Fecha'] = pd.to_datetime(
    df['Fecha'].str.replace(r'^(\d{2})/(\d{2})/(\d{4})$', r'\3-\2-\1', regex=True),
    format='mixed',
    errors='coerce'
).fillna(pd.Timestamp('1900-01-01'))


df['Producto'] = df['Producto'].astype(str).str.strip().str.capitalize()
df['Categoria'] = df['Categoria'].astype(str).str.strip().str.capitalize()

df['ID_Cliente'] = df['ID_Cliente'].astype(str).str.strip().str.capitalize()


df['Precio_Unitario'] = pd.to_numeric(df['Precio_Unitario'], errors='coerce').astype(float)
df['Monto_Total'] = pd.to_numeric(df['Monto_Total'], errors='coerce').astype(float)
df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(pd.Int64Dtype())


df['Categoria'] = df['Categoria'].fillna('Categoria desconocida')

df['Metodo_Pago'] = df['Metodo_Pago'].fillna('Metodo de pago desconocido')
df['Ciudad'] = df['Ciudad'].fillna('Ciudad desconocido')

df['Monto_Total'] = df['Monto_Total'].fillna(0)
df['Precio_Unitario'] = df['Precio_Unitario'].fillna(0)

df['Cantidad'] = df['Cantidad'].abs()
df['Precio_Unitario'] = df['Precio_Unitario'].abs()

df['Monto_Total'] = df['Cantidad'] * df['Precio_Unitario']

duplicados = df['ID_Venta'].duplicated().sum()

df = df.drop_duplicates(subset=['ID_Venta'], keep='first').reset_index(drop=True)

df.to_csv('ventas_limpias.csv', index=False, encoding='utf-8-sig')



# # Lectura de las variables de entorno
# USER = os.getenv("DB_USER")
# PASSWORD = os.getenv("DB_PASSWORD")
# HOST = os.getenv("DB_HOST", "localhost")  
# PORT = os.getenv("DB_PORT", "5432")
# DB_NAME = os.getenv("DB_NAME")

# # Construcción de la URL de conexión
# DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

# # Creación y verificación del motor de base de datos
# try:
#     engine = create_engine(DATABASE_URL)
#     with engine.connect() as connection:
#         connection.execute(text("SELECT 1"))
#     print(f" Conexión exitosa a '{DB_NAME}' en {HOST}:{PORT}\n")
# except OperationalError as e:
#     print(f" Error de credenciales o red al conectar a PostgreSQL: {e}\n")
# except Exception as e:
#     print(f" Error inesperado: {e}\n")


# Cliente = (
#     df[
#         ["ID_Cliente", "nombre", "tipo_campana"]
#     ].drop_duplicates()
#     .reset_index(drop=True)
# )

# canales = df[["canal"]].drop_duplicates().reset_index(drop=True)
# canales.insert(0, "id_canal", range(1, len(canales) + 1))


# productos = (
#     df[["producto_promocionado"]].drop_duplicates().reset_index(drop=True)
# )
# productos.insert(0, "id_producto", range(1, len(productos) + 1))

# marketing_resultados = df.merge(canales, on="canal")
# marketing_resultados = marketing_resultados.merge(productos, on="producto_promocionado")

# # Seleccionamos las métricas, la fecha de registro y las Claves Foráneas (FKs)
# marketing_resultados = marketing_resultados[
#     [
#         "id_campana_registro",
#         "id_canal",
#         "id_producto",
#         "impresiones",
#         "clics",
#         "conversiones",
#         "costo_mxn",
#         "ingresos_generados_mxn",
#     ]
# ]

# #conectamos a postgress sql

# campanas.to_sql("campanas", engine, if_exists="replace", index=False)
# canales.to_sql("canal", engine, if_exists="replace", index=False)
# productos.to_sql("producto_promocionado", engine, if_exists="replace", index=False)
# marketing_resultados.to_sql("marketing_resultados", engine, if_exists="replace", index=False)


# # Ejecutar comandos SQL para inyectar PKs y FKs que DBeaver pueda leer
# with engine.connect() as conn:
#     # Definir Claves Primarias (PK)
#     conn.execute(text("ALTER TABLE campanas ADD PRIMARY KEY (id_campana_registro);"))
#     conn.execute(text("ALTER TABLE canal ADD PRIMARY KEY (id_canal);"))
#     conn.execute(text("ALTER TABLE producto_promocionado ADD PRIMARY KEY (id_producto);"))

# # Definir Claves Foráneas (FK)
#     conn.execute(text("ALTER TABLE marketing_resultados ADD CONSTRAINT fk_campanas FOREIGN KEY (id_campana_registro) REFERENCES campanas(id_campana_registro);"))
#     conn.execute(text("ALTER TABLE marketing_resultados ADD CONSTRAINT fk_canal FOREIGN KEY (id_canal) REFERENCES canal(id_canal);"))
#     conn.execute(text("ALTER TABLE marketing_resultados ADD CONSTRAINT fk_producto_promocionado FOREIGN KEY (id_producto) REFERENCES producto_promocionado(id_producto);"))
#     conn.commit()