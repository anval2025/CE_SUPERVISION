import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
import plotly.graph_objects as go

DB = "data/plantlist.db"

def invitado_dashboard():
    with st.sidebar:
        st.markdown("### 👤 Usuario: " + st.session_state.get('usuario', 'Invitado'))
        if st.button("🔒 Cerrar sesión"):
            st.session_state['logged_in'] = False
            st.session_state['usuario'] = ''
            st.experimental_rerun()

    st.title("Disponibilidad de equipo")
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Estado global
    if 'mostrar_listado' not in st.session_state:
        st.session_state['mostrar_listado'] = None
    if 'mostrar_grafico' not in st.session_state:
        st.session_state['mostrar_grafico'] = False

    # Botón para mostrar gráficos
    if not st.session_state['mostrar_grafico']:
        if st.button("📊 Mostrar gráficos"):
            st.session_state['mostrar_grafico'] = True
            st.rerun()

    # Si mostrar_grafico está activado, mostramos filtros y gráfico
    if st.session_state['mostrar_grafico']:
        # Filtro por ubicación
        c.execute("SELECT DISTINCT location FROM equipos")
        ubicaciones = [row[0] for row in c.fetchall()]
        ubicacion_seleccionada = st.selectbox("Seleccionar ubicación", ubicaciones)

        # Filtro por tipo de equipo
        c.execute("SELECT DISTINCT tipo_equipo FROM equipos WHERE location = ?", (ubicacion_seleccionada,))
        tipos_equipo = ["TODOS"] + [row[0] for row in c.fetchall()]
        tipo_seleccionado = st.selectbox("Seleccionar tipo de equipo", tipos_equipo)

        col_filtros = st.columns([1, 1])
        with col_filtros[0]:
            if st.button("🔄 Actualizar gráfico"):
                pass  # solo se refresca automáticamente

        with col_filtros[1]:
            if st.button("❌ Cerrar gráfico"):
                st.session_state['mostrar_grafico'] = False
                st.rerun()

        mostrar_grafico(conn, ubicacion_seleccionada, tipo_seleccionado)
        conn.close()
        return

    # Mostrar tablas por ubicación
    c.execute("SELECT DISTINCT location FROM equipos")
    ubicaciones = [row[0] for row in c.fetchall()]

    for ubicacion in ubicaciones:
        st.subheader(f"Ubicación: {ubicacion}")

        c.execute("""
            SELECT tipo_equipo,
                SUM(CASE WHEN status = 'DISPONIBLE' THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN status = 'NO DISPONIBLE' THEN 1 ELSE 0 END) as no_disponibles,
                SUM(CASE WHEN status = 'NO DISPONIBLE ALTA INVERSION' THEN 1 ELSE 0 END) as no_disponibles_inversion
            FROM equipos
            WHERE location = ?
            GROUP BY tipo_equipo
        """, (ubicacion,))
        rows = c.fetchall()

        df = pd.DataFrame(rows, columns=["Tipo Equipo", "Disponibles", "No Disponibles", "No Disponibles Alta Inversión"])
        st.dataframe(df)

        cols = st.columns(len(rows))
        for i, row in enumerate(rows[::-1]):
            tipo_equipo = row[0]
            with cols[i]:
                if st.button(tipo_equipo, key=f"{ubicacion}_{tipo_equipo}"):
                    st.session_state['mostrar_listado'] = (tipo_equipo, ubicacion)

        if st.session_state['mostrar_listado'] and st.session_state['mostrar_listado'][1] == ubicacion:
            tipo, ubi = st.session_state['mostrar_listado']
            st.markdown("---")
            st.subheader(f"Listado de Equipos - {tipo} en {ubi}")
            mostrar_equipos(conn, tipo, ubi)
            if st.button("Cerrar listado", key=f"cerrar_{ubicacion}"):
                st.session_state['mostrar_listado'] = None
                st.experimental_rerun()

    conn.close()

def mostrar_equipos(conn, tipo_equipo, ubicacion):
    c = conn.cursor()
    c.execute("""
        SELECT tipo_equipo, equipo, capacidad, status
        FROM equipos
        WHERE tipo_equipo = ? AND location = ?
    """, (tipo_equipo, ubicacion))
    rows = c.fetchall()

    if not rows:
        st.info("No hay equipos para mostrar.")
        return

    df = pd.DataFrame(rows, columns=["Tipo de Equipo", "Equipo", "Capacidad (SWL)", "Status"])
    st.dataframe(df, use_container_width=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Equipos")
    data = output.getvalue()

    st.download_button(
        "📥 Descargar listado en Excel",
        data=data,
        file_name=f"equipos_{tipo_equipo}_{ubicacion}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def mostrar_grafico(conn, ubicacion, tipo_equipo):
    c = conn.cursor()

    if tipo_equipo == "TODOS":
        c.execute("""
            SELECT tipo_equipo,
                SUM(CASE WHEN status = 'DISPONIBLE' THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN status = 'NO DISPONIBLE' THEN 1 ELSE 0 END) as no_disponibles,
                SUM(CASE WHEN status = 'NO DISPONIBLE ALTA INVERSION' THEN 1 ELSE 0 END) as no_disponibles_inversion
            FROM equipos
            WHERE location = ?
            GROUP BY tipo_equipo
        """, (ubicacion,))
    else:
        c.execute("""
            SELECT tipo_equipo,
                SUM(CASE WHEN status = 'DISPONIBLE' THEN 1 ELSE 0 END) as disponibles,
                SUM(CASE WHEN status = 'NO DISPONIBLE' THEN 1 ELSE 0 END) as no_disponibles,
                SUM(CASE WHEN status = 'NO DISPONIBLE ALTA INVERSION' THEN 1 ELSE 0 END) as no_disponibles_inversion
            FROM equipos
            WHERE location = ? AND tipo_equipo = ?
            GROUP BY tipo_equipo
        """, (ubicacion, tipo_equipo))

    data = c.fetchall()

    if not data:
        st.warning("No hay datos para mostrar.")
        return

    tipos = [d[0] for d in data]
    disponibles = [d[1] for d in data]
    no_disponibles = [d[2] for d in data]
    alta_inversion = [d[3] for d in data]

    fig = go.Figure(data=[
        go.Bar(name='Disponible', x=tipos, y=disponibles,
               marker_color='lightblue', text=disponibles, textposition='auto'),
        go.Bar(name='No disponible', x=tipos, y=no_disponibles,
               marker_color='gray', text=no_disponibles, textposition='auto'),
        go.Bar(name='No disponible alta inversión', x=tipos, y=alta_inversion,
               marker_color='black', text=alta_inversion, textposition='auto'),
    ])

    fig.update_layout(
        barmode='group',
        title=f'Disponibilidad en {ubicacion}' if tipo_equipo == "TODOS" else f'Disponibilidad de {tipo_equipo} en {ubicacion}',
        xaxis_title='Tipo de equipo',
        yaxis_title='Cantidad',
        plot_bgcolor='white'
    )

    st.plotly_chart(fig, use_container_width=True)
