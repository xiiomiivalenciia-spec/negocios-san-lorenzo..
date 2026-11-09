
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from io import BytesIO

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Negocios San Lorenzo",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "base_datos_san_lorenzo_2026 (1)(1).xlsx"
DB_PATH = BASE_DIR / "negocios_san_lorenzo.db"

# =========================================================
# ESTILOS ORIGINALES
# =========================================================

st.markdown("""
<style>
.stApp {
    background-color: #f5f8f7;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b5d3b, #087f5b);
}

[data-testid="stSidebar"] * {
    color: white;
}

.titulo {
    text-align: center;
    color: #087f5b;
    font-size: 38px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitulo {
    text-align: center;
    color: #555;
    font-size: 17px;
    margin-bottom: 30px;
}

.login-card {
    background: white;
    padding: 35px;
    border-radius: 18px;
    box-shadow: 0px 5px 20px rgba(0,0,0,0.08);
    max-width: 550px;
    margin: auto;
}

h2, h3 {
    color: #087f5b;
}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    border: none;
    background-color: #087f5b;
    color: white;
    font-weight: bold;
    padding: 10px;
}

.stButton > button:hover {
    background-color: #f2c300;
    color: #173f35;
}

[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.07);
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
}

.footer {
    text-align: center;
    color: #777;
    font-size: 13px;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# BASE DE DATOS EXCEL
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

EXCEL_PATH = BASE_DIR / "base_datos_san_lorenzo_2026 (1).xlsx"

@st.cache_data
def cargar_datos():

    if not EXCEL_PATH.exists():
        st.error("No se encontró el archivo Excel de la base de datos.")
        st.write("Ruta donde se está buscando:")
        st.code(str(EXCEL_PATH))

        st.write("Archivos Excel encontrados en la carpeta:")
        st.write([archivo.name for archivo in BASE_DIR.glob("*.xlsx")])

        st.stop()

    return {
        "negocios": pd.read_excel(EXCEL_PATH, sheet_name="Negocios"),
        "clientes": pd.read_excel(EXCEL_PATH, sheet_name="Clientes"),
        "productos": pd.read_excel(EXCEL_PATH, sheet_name="Productos"),
        "ventas": pd.read_excel(EXCEL_PATH, sheet_name="Ventas"),
        "detalle": pd.read_excel(EXCEL_PATH, sheet_name="Detalle_Ventas")
    }


datos = cargar_datos()

productos_df = datos["productos"].copy()
clientes_base = datos["clientes"].copy()
ventas_base = datos["ventas"].copy()
detalle_base = datos["detalle"].copy()
negocios_df = datos["negocios"].copy()

# =========================================================
# BASE DE DATOS PARA GUARDAR CLIENTES Y VENTAS NUEVAS
# =========================================================

def conectar_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def inicializar_db():

    with conectar_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS clientes_nuevos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                contacto TEXT,
                direccion TEXT,
                correo TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ventas_nuevas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                cliente TEXT,
                producto TEXT,
                cantidad INTEGER,
                precio REAL,
                total REAL
            )
        """)


inicializar_db()


# =========================================================
# FUNCIONES DE CLIENTES
# =========================================================

def obtener_clientes():

    base = clientes_base[["ClienteID", "NombreCliente"]].copy()

    base.columns = ["ID", "Nombre"]

    with conectar_db() as conn:

        nuevos = pd.read_sql_query(
            "SELECT id, nombre FROM clientes_nuevos",
            conn
        )

    if not nuevos.empty:

        nuevos.columns = ["ID", "Nombre"]

        base = pd.concat(
            [base, nuevos],
            ignore_index=True
        )

    base["Nombre"] = base["Nombre"].fillna("").astype(str)

    return base.drop_duplicates(
        subset=["Nombre"]
    ).sort_values("Nombre")


def obtener_ventas_nuevas():

    with conectar_db() as conn:

        return pd.read_sql_query(
            "SELECT * FROM ventas_nuevas",
            conn
        )


# =========================================================
# PREPARACIÓN DE VENTAS ORIGINALES
# =========================================================

detalle_completo = detalle_base.merge(
    productos_df[["ProductoID", "Producto"]],
    on="ProductoID",
    how="left"
)

ventas_completas = detalle_completo.merge(
    ventas_base[["VentaID", "Fecha", "ClienteID", "NegocioID"]],
    on="VentaID",
    how="left"
)

ventas_completas["Total"] = pd.to_numeric(
    ventas_completas["Subtotal"],
    errors="coerce"
).fillna(0)


# =========================================================
# LOGO
# =========================================================

col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])

with col_logo2:

    if (BASE_DIR / "logo.png").exists():

        st.image("logo.png", width=180)


# =========================================================
# TÍTULO
# =========================================================

st.markdown(
    '<div class="titulo">Negocios San Lorenzo</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitulo">Sistema de Inteligencia de Negocios</div>',
    unsafe_allow_html=True
)


# =========================================================
# MENÚ LATERAL
# =========================================================

st.sidebar.markdown("## 🏪 Negocios San Lorenzo")

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Menú principal",
    [
        "🏠 Inicio",
        "👥 Clientes",
        "🛒 Ventas",
        "📊 Dashboard",
        "📑 Reportes"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    "**Conectando comercios,**  \n"
    "**impulsando el desarrollo local.**"
)


# =========================================================
# INICIO
# =========================================================

if menu == "🏠 Inicio":

    st.markdown(
        '<div class="login-card">',
        unsafe_allow_html=True
    )

    st.markdown(
        "<h2 style='text-align:center;'>👋 Bienvenido</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#666;'>"
        "Ingresa al sistema para gestionar y analizar "
        "la información de los negocios."
        "</p>",
        unsafe_allow_html=True
    )

    usuario = st.text_input(
        "👤 Usuario",
        placeholder="Escribe tu usuario"
    )

    contraseña = st.text_input(
        "🔒 Contraseña",
        type="password",
        placeholder="Escribe tu contraseña"
    )

    if st.button("🚀 Iniciar sesión"):

        if usuario and contraseña:

            st.success(f"¡Bienvenido, {usuario}!")

        else:

            st.warning(
                "Por favor, completa el usuario y la contraseña."
            )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# CLIENTES
# =========================================================

elif menu == "👥 Clientes":

    st.header("👥 Registro de clientes")

    st.write(
        "Registra la información de los clientes de los negocios locales."
    )

    col1, col2 = st.columns(2)

    with col1:

        nombre = st.text_input(
            "Nombre del cliente",
            placeholder="Ejemplo: Juan Pérez"
        )

        contacto = st.text_input(
            "📱 Contacto",
            placeholder="Ejemplo: 0987654321"
        )

    with col2:

        direccion = st.text_input(
            "📍 Dirección",
            placeholder="Ejemplo: San Lorenzo"
        )

        correo = st.text_input(
            "✉️ Correo electrónico",
            placeholder="correo@ejemplo.com"
        )

    if st.button("💾 Guardar cliente"):

        if nombre.strip() and contacto.strip() and direccion.strip():

            clientes_existentes = obtener_clientes()

            existe = clientes_existentes["Nombre"].str.casefold().eq(
                nombre.strip().casefold()
            ).any()

            if existe:

                st.warning("⚠️ Este cliente ya está registrado.")

            else:

                with conectar_db() as conn:

                    conn.execute(
                        """
                        INSERT INTO clientes_nuevos
                        (nombre, contacto, direccion, correo)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            nombre.strip(),
                            contacto.strip(),
                            direccion.strip(),
                            correo.strip()
                        )
                    )

                st.success(
                    "✅ Cliente registrado correctamente."
                )

                st.rerun()

        else:

            st.warning(
                "⚠️ Completa los campos principales."
            )

    # BUSCAR CLIENTES

    st.markdown("---")

    st.subheader("🔎 Buscar cliente registrado")

    busqueda_cliente = st.text_input(
        "Nombre del cliente",
        placeholder="Escribe el nombre para buscar..."
    )

    todos_clientes = obtener_clientes()

    if busqueda_cliente.strip():

        encontrados = todos_clientes[
            todos_clientes["Nombre"].str.contains(
                busqueda_cliente,
                case=False,
                na=False
            )
        ]

        if not encontrados.empty:

            st.dataframe(
                encontrados,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No se encontraron clientes.")


# =========================================================
# VENTAS
# =========================================================

elif menu == "🛒 Ventas":

    st.header("🛒 Registro de ventas")

    col1, col2 = st.columns(2)

    # PRODUCTOS DE LA BASE DE DATOS

    lista_productos = sorted(
        productos_df["Producto"].dropna().astype(str).unique().tolist()
    )

    with col1:

        busqueda_producto = st.text_input(
            "📦 Producto",
            placeholder="Escribe el nombre del producto..."
        )

        productos_filtrados = [
            p for p in lista_productos
            if busqueda_producto.strip().casefold() in p.casefold()
        ]

        producto = st.selectbox(
            "Seleccionar producto",
            options=productos_filtrados,
            index=None,
            placeholder="Busca y selecciona un producto"
        )

        cantidad = st.number_input(
            "🔢 Cantidad",
            min_value=1,
            value=1
        )

    with col2:

        precio_sugerido = 0.0

        if producto:

            fila = productos_df[
                productos_df["Producto"] == producto
            ]

            if not fila.empty:

                precio_sugerido = float(
                    fila.iloc[0]["PrecioBase"]
                )

        precio = st.number_input(
            "💵 Precio unitario",
            min_value=0.0,
            value=precio_sugerido,
            step=0.50,
            key=f"precio_{producto}"
        )

        fecha = st.date_input(
            "📅 Fecha de venta",
            min_value=pd.Timestamp("2026-01-01").date(),
            max_value=pd.Timestamp("2026-12-31").date()
        )

    # SELECCIÓN DEL CLIENTE

    clientes_disponibles = obtener_clientes()["Nombre"].tolist()

    cliente = st.selectbox(
        "👥 Cliente",
        options=clientes_disponibles,
        index=None,
        placeholder="Escribe para buscar un cliente"
    )

    total = cantidad * precio

    st.info(
        f"💰 Total de la venta: **${total:,.2f}**"
    )

    if st.button("💾 Guardar venta"):

        if producto and precio > 0:

            with conectar_db() as conn:

                conn.execute(
                    """
                    INSERT INTO ventas_nuevas
                    (fecha, cliente, producto, cantidad, precio, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fecha.isoformat(),
                        cliente or "",
                        producto,
                        int(cantidad),
                        float(precio),
                        float(total)
                    )
                )

            st.success(
                "✅ Venta registrada correctamente."
            )

            st.rerun()

        else:

            st.warning(
                "⚠️ Busca un producto y verifica el precio."
            )


# =========================================================
# DASHBOARD
# =========================================================

elif menu == "📊 Dashboard":

    st.header("📊 Dashboard de ventas")

    st.write(
        "Visualización de los principales indicadores "
        "de los emprendimientos comerciales analizados."
    )

    st.caption(
        "Período de análisis: 1 de enero al 30 de junio de 2026"
    )

    ventas_nuevas = obtener_ventas_nuevas()

    total_original = ventas_completas["Total"].sum()

    total_nuevo = (
        ventas_nuevas["total"].sum()
        if not ventas_nuevas.empty else 0
    )

    # MÉTRICAS

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "💰 Total ventas",
        f"${total_original + total_nuevo:,.2f}"
    )

    col2.metric(
        "👥 Clientes activos",
        f"{ventas_base['ClienteID'].nunique():,}"
    )

    col3.metric(
        "🏪 Negocios registrados",
        f"{negocios_df['NegocioID'].nunique():,}"
    )

    col4.metric(
        "📦 Productos registrados",
        f"{len(productos_df):,}"
    )

    st.markdown("---")

    # GRÁFICOS

    col1, col2 = st.columns(2)

    ventas_por_producto = (
        ventas_completas.groupby("Producto")["Total"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    ventas_por_producto.columns = [
        "Producto", "Ventas"
    ]

    if not ventas_nuevas.empty:

        nuevos_productos = (
            ventas_nuevas.groupby("producto")["total"]
            .sum()
            .reset_index()
        )

        nuevos_productos.columns = [
            "Producto", "Ventas"
        ]

        ventas_por_producto = pd.concat(
            [ventas_por_producto, nuevos_productos],
            ignore_index=True
        )

        ventas_por_producto = (
            ventas_por_producto.groupby(
                "Producto", as_index=False
            )["Ventas"]
            .sum()
            .sort_values("Ventas", ascending=False)
            .head(10)
        )

    with col1:

        st.subheader("🛒 Ventas por producto")

        st.bar_chart(
            ventas_por_producto.set_index("Producto")
        )

    with col2:

        st.subheader("📈 Ventas mensuales")

        datos_mensuales = ventas_completas.copy()

        datos_mensuales["Fecha"] = pd.to_datetime(
            datos_mensuales["Fecha"],
            errors="coerce"
        )

        mensual = datos_mensuales.groupby(
            datos_mensuales["Fecha"].dt.to_period("M")
        )["Total"].sum()

        mensual.index = mensual.index.astype(str)

        if not ventas_nuevas.empty:

            nuevas = ventas_nuevas.copy()

            nuevas["fecha"] = pd.to_datetime(
                nuevas["fecha"],
                errors="coerce"
            )

            mensual_nueva = nuevas.groupby(
                nuevas["fecha"].dt.to_period("M")
            )["total"].sum()

            mensual_nueva.index = mensual_nueva.index.astype(str)

            mensual = mensual.add(
                mensual_nueva,
                fill_value=0
            )

        st.line_chart(mensual)

    # RESUMEN COMPLETO DE PRODUCTOS

    st.markdown("---")

    st.subheader("📦 Resumen de productos")

    buscar_producto = st.text_input(
        "🔎 Buscar producto",
        placeholder="Escribe el nombre del producto que deseas encontrar..."
    )

    resumen_productos = productos_df[
        ["ProductoID", "Producto", "CategoriaID", "PrecioBase"]
    ].copy()

    resumen_productos.columns = [
        "Código",
        "Producto",
        "Categoría",
        "Precio base"
    ]

    if buscar_producto.strip():

        resumen_productos = resumen_productos[
            resumen_productos["Producto"].str.contains(
                buscar_producto.strip(),
                case=False,
                na=False
            )
        ]

    st.caption(
        f"Productos encontrados: {len(resumen_productos)} de {len(productos_df)}"
    )

    if not resumen_productos.empty:

        st.dataframe(
            resumen_productos,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No se encontraron productos con ese nombre.")

    # MAPA

    st.subheader("📍 Ubicación de negocios")

    mapa = pd.DataFrame({
        "lat": [
            1.285,
            1.290,
            1.280,
            1.295
        ],
        "lon": [
            -78.835,
            -78.830,
            -78.840,
            -78.825
        ]
    })

    st.map(mapa)


# =========================================================
# REPORTES
# =========================================================

elif menu == "📑 Reportes":

    st.header("📑 Reportes de ventas")

    reporte = ventas_completas[
        [
            "Fecha",
            "NegocioID",
            "ClienteID",
            "Producto",
            "Cantidad",
            "PrecioUnitario",
            "Subtotal"
        ]
    ].copy()

    reporte.columns = [
        "Fecha",
        "Negocio",
        "Cliente",
        "Producto",
        "Cantidad",
        "Precio unitario",
        "Precio total"
    ]

    ventas_nuevas = obtener_ventas_nuevas()

    if not ventas_nuevas.empty:

        nuevas = ventas_nuevas.rename(
            columns={
                "fecha": "Fecha",
                "cliente": "Cliente",
                "producto": "Producto",
                "cantidad": "Cantidad",
                "precio": "Precio unitario",
                "total": "Precio total"
            }
        )

        nuevas["Negocio"] = "Registro manual"

        nuevas = nuevas[
            [
                "Fecha",
                "Negocio",
                "Cliente",
                "Producto",
                "Cantidad",
                "Precio unitario",
                "Precio total"
            ]
        ]

        reporte = pd.concat(
            [reporte, nuevas],
            ignore_index=True
        )

    st.dataframe(
        reporte,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    total_reporte = pd.to_numeric(
        reporte["Precio total"],
        errors="coerce"
    ).fillna(0).sum()

    st.metric(
        "💰 Total de ventas registradas en el reporte",
        f"${total_reporte:,.2f}"
    )

    # DESCARGAR EXCEL

    archivo_excel = BytesIO()

    with pd.ExcelWriter(
        archivo_excel,
        engine="openpyxl"
    ) as writer:

        reporte.to_excel(
            writer,
            sheet_name="Reporte de ventas",
            index=False
        )

        obtener_clientes().to_excel(
            writer,
            sheet_name="Clientes",
            index=False
        )

        productos_df.to_excel(
            writer,
            sheet_name="Productos",
            index=False
        )

    archivo_excel.seek(0)

    st.download_button(
        label="⬇️ Descargar reporte en Excel",
        data=archivo_excel.getvalue(),
        file_name="reporte_negocios_san_lorenzo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =========================================================
# PIE DE PÁGINA
# =========================================================

st.markdown(
    """
    <div class="footer">
        Negocios San Lorenzo © 2026<br>
        Sistema de Inteligencia de Negocios
    </div>
    """,
    unsafe_allow_html=True
)
