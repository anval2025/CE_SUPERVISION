import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from pages.form_equipo import agregar_equipo
from pages.edit_equipo import editar_equipo
from pages.historial_equipo import historial_equipo

DB = "data/plantlist.db"

def admin_dashboard():
    st.title("Panel Administrador")

    # Inicializar variable para controlar qué mostrar
    if 'admin_panel' not in st.session_state:
        st.session_state['admin_panel'] = None

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Agregar equipo"):
            st.session_state['admin_panel'] = 'agregar'

    with col2:
        if st.button("Editar equipo"):
            st.session_state['admin_panel'] = 'editar'

    with col3:
        if st.button("Historial equipo"):
            st.session_state['admin_panel'] = 'historial'

    with col4:
        if st.button("Ver todos los equipos"):
            st.session_state['admin_panel'] = 'todos'

    st.markdown("---")  # Separador

    # Mostrar el panel correspondiente en la parte de abajo
    if st.session_state['admin_panel'] == 'agregar':
        agregar_equipo()
    elif st.session_state['admin_panel'] == 'editar':
        editar_equipo()
    elif st.session_state['admin_panel'] == 'historial':
        historial_equipo()
    elif st.session_state['admin_panel'] == 'todos':
        mostrar_todos_equipos()

def mostrar_todos_equipos():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM equipos", conn)
    conn.close()

    st.subheader("Tabla completa de equipos")
    st.dataframe(df)

    # Opción para descargar la tabla completa en Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Equipos_Completos")
    data = output.getvalue()

    st.download_button(
        label="Descargar tabla completa en Excel",
        data=data,
        file_name="equipos_completos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
