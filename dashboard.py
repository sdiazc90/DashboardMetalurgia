import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    /* Quitar márgenes/padding innecesarios y permitir ancho completo */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
        max-width: none;
    }
    .stApp {
        background-color: white;
    }
    /* Selectboxes con fondo pastel */
    [data-baseweb="select"] > div {
        background-color: #fff9e3 !important;
        border-radius: 10px !important;
    }
    /* Que los contenedores gráficos ocupen más altura relativa */
    .element-container {
        padding: 0.25rem 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)



# Carga de datos
df = pd.read_csv('LOGISTICA.csv', sep=';')

# Elimina cualquier columna que contenga 'index' en su nombre
cols_to_drop = [col for col in df.columns if 'index' in col.lower()]
df = df.drop(columns=cols_to_drop)

# Conversión de fechas
df['INICIO DESCARGA'] = pd.to_datetime(df['INICIO DESCARGA'], dayfirst=True, errors='coerce')
df['FIN DESCARGA'] = pd.to_datetime(df['FIN DESCARGA'], dayfirst=True, errors='coerce')
df['SALIDA DEL PROVEEDOR'] = pd.to_datetime(df['SALIDA DEL PROVEEDOR'], dayfirst=True, errors='coerce')
df['LLEGADA A FÁBRICA'] = pd.to_datetime(df['LLEGADA A FÁBRICA'], dayfirst=True, errors='coerce')

# Elimina toda la fila de Antonio Medina
df = df[df['SUPERVISOR'] != 'Antonio Medina']
df = df[df['TIPO_ACERO'] != 'ACERO INOX']

# Variables temporales
df['TIEMPO_DESCARGA_MIN'] = (df['FIN DESCARGA'] - df['INICIO DESCARGA']).dt.total_seconds() / 60
df['TIEMPO_VIAJE_MIN'] = (df['LLEGADA A FÁBRICA'] - df['SALIDA DEL PROVEEDOR']).dt.total_seconds() / 60
df['TIEMPO_ESPERA_MIN'] = (df['INICIO DESCARGA'] - df['LLEGADA A FÁBRICA']).dt.total_seconds() / 60

st.markdown(
    '<h1 style="text-align: center; color: #1a3c1a;">Monitoreo de Transporte y Fallas – Industria Metalúrgica</h1>',
    unsafe_allow_html=True
)
st.markdown(
    '<h3 style="text-align: center; color: white;">Sergio Diaz Colina</h3>',
    unsafe_allow_html=True
)

# Asegura que no haya NaN y todo sea string para los filtros
df['LINEA'] = df['LINEA'].fillna('Línea B').astype(str)
df['SUPERVISOR'] = df['SUPERVISOR'].fillna('Sin dato').astype(str)
df['TIPO_ACERO'] = df['TIPO_ACERO'].fillna('Sin dato').astype(str)
df['TRANSPORTE'] = df['TRANSPORTE'].fillna('Sin dato').astype(str)

# Filtros interactivos
col1, col2, col3, col4 = st.columns(4)
with col1:
    linea = st.selectbox("Selecciona Línea", options=['Todas'] + sorted(df['LINEA'].unique().tolist()))
with col2:
    supervisor = st.selectbox("Selecciona Supervisor", options=['Todos'] + sorted(df['SUPERVISOR'].unique().tolist()))
with col3:
    tipo_acero = st.selectbox("Selecciona Tipo de Acero", options=['Todos'] + sorted(df['TIPO_ACERO'].unique().tolist()))
with col4:
    transporte = st.selectbox("Selecciona Transporte", options=['Todos'] + sorted(df['TRANSPORTE'].unique().tolist()))

df_filtrado = df.copy()
if linea != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['LINEA'] == linea]
if supervisor != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['SUPERVISOR'] == supervisor]
if tipo_acero != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['TIPO_ACERO'] == tipo_acero]
if transporte != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['TRANSPORTE'] == transporte]

total_trucks = len(df_filtrado)
# Cantidad de fallas: si es numérico sumás, si no contás no nulos
if pd.api.types.is_numeric_dtype(df_filtrado['FALLAS']):
    total_failures = df_filtrado['FALLAS'].sum()
    avg_failures = df_filtrado['FALLAS'].mean()
else:
    total_failures = df_filtrado['FALLAS'].notna().sum()
    avg_failures = None

failure_rate = (total_failures / total_trucks * 100) if total_trucks else 0

# Métricas principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("Cantidad Total de Camiones", len(df_filtrado))
col2.metric("Cantidad de Fallas", df_filtrado['FALLAS'].notna().sum())
col3.metric("Fallas / Camiones", f"{failure_rate:.1f} %")
col4.metric("Peso Neto Total", f"{df_filtrado['PESO NETO'].sum():,.0f}")


col5, col6, col7, col8 = st.columns(4)
col6.metric("Promedio en Espera (min)", f"{df_filtrado['TIEMPO_ESPERA_MIN'].mean():.1f}")
col7.metric("Promedio de Descarga (min)", f"{df_filtrado['TIEMPO_DESCARGA_MIN'].mean():.1f}")
col5.metric("Promedio en Viaje (min)", f"{df_filtrado['TIEMPO_VIAJE_MIN'].mean():.1f}")
col8.metric("Promedio en Temperatura C°", f"{df_filtrado['TEMPERATURA'].mean():.1f}")
# Prepara datos para gráficos
df_filtrado['DIA'] = df_filtrado['SALIDA DEL PROVEEDOR'].dt.date
conteo = df_filtrado.groupby('DIA').size().reset_index(name='Cantidad de Camiones')
conteo = conteo.sort_values('DIA')

conteo_turno = df_filtrado['TURNO'].value_counts().reset_index()
conteo_turno.columns = ['TURNO', 'Cantidad de Camiones']

fallas_tipo = df_filtrado['FALLAS'].value_counts().reset_index()
fallas_tipo.columns = ['Tipo de Falla', 'Cantidad de Fallas']
fallas_tipo = fallas_tipo[fallas_tipo['Tipo de Falla'].notna() & (fallas_tipo['Tipo de Falla'] != '')]

fallas_transporte = df_filtrado[df_filtrado['FALLAS'].notna()]
treemap_data = fallas_transporte['TRANSPORTE'].value_counts().reset_index()
treemap_data.columns = ['Transporte', 'Cantidad de Fallas']

# --- Presentación de gráficos en dos columnas por fila ---
col_graf1, col_graf2 = st.columns(2)
with col_graf1:
    st.subheader("Cantidad de Camiones por Día")
    st.line_chart(conteo.set_index('DIA')['Cantidad de Camiones'])

with col_graf2:
    st.subheader("Cantidad de Camiones por Turno")
    fig = px.pie(
        conteo_turno,
        names='TURNO',
        values='Cantidad de Camiones',
        hole=0.5,
        title=""
    )
    st.plotly_chart(fig, use_container_width=True)

col_graf3, col_graf4 = st.columns(2)
with col_graf3:
    st.subheader("Embudo: Cantidad de Fallas por Tipo")
    if not fallas_tipo.empty:
        fig_funnel = px.funnel(
            fallas_tipo,
            x='Cantidad de Fallas',
            y='Tipo de Falla',
            title=""
        )
        st.plotly_chart(fig_funnel, use_container_width=True)
    else:
        st.info("No hay datos de fallas para mostrar el embudo.")

with col_graf4:
    st.subheader("Treemap: Cantidad de Fallas por Transporte")
    if not treemap_data.empty:
        fig_treemap = px.treemap(
            treemap_data,
            path=['Transporte'],
            values='Cantidad de Fallas',
            title=""
        )
        st.plotly_chart(fig_treemap, use_container_width=True)
    else:
        st.info("No hay datos de fallas para mostrar el treemap.")

st.subheader("Datos Filtrados")
st.dataframe(df_filtrado, hide_index=True)