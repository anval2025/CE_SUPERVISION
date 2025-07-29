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

    st.markdown("<h1 style='color:black;'>Disponibilidad de equipo</h1>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if 'mostrar_listado' not in st.session_state:
        st.session_state['mostrar_listado'] = None
    if 'mostrar_grafico' not in st.session_state:
        st.session_state['mostrar_grafico'] = False
    if 'mostrar_grafico_gruas' not in st.session_state:
        st.session_state['mostrar_grafico_gruas'] = False

    c.execute("SELECT DISTINCT location FROM equipos")
    ubicaciones = [row[0] for row in c.fetchall()]

    # Botones principales
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📊 Mostrar gráficos generales"):
            st.session_state['mostrar_grafico'] = True
            st.session_state['mostrar_grafico_gruas'] = False
            st.session_state['mostrar_listado'] = None
    with col2:
        if st.button("🚛 Mostrar gráficos de grúas móviles para llenos"):
            st.session_state['mostrar_grafico_gruas'] = True
            st.session_state['mostrar_grafico'] = False
            st.session_state['mostrar_listado'] = None

    # Mostrar gráficos generales
    if st.session_state['mostrar_grafico']:
        tipo_equipo = st.selectbox("Seleccionar tipo de equipo", ["Todos"] + list(set(row[0] for row in c.execute("SELECT tipo_equipo FROM equipos"))))
        st.markdown("### 📈 Gráficos por ubicación")
        for ubicacion in ubicaciones:
            if tipo_equipo != "Todos":
                c.execute("""
                    SELECT tipo_equipo,
                        SUM(CASE WHEN status = 'DISPONIBLE' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'NO DISPONIBLE' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'NO DISPONIBLE ALTA INVERSION' THEN 1 ELSE 0 END)
                    FROM equipos
                    WHERE location = ? AND tipo_equipo = ?
                    GROUP BY tipo_equipo
                """, (ubicacion, tipo_equipo))
            else:
                c.execute("""
                    SELECT tipo_equipo,
                        SUM(CASE WHEN status = 'DISPONIBLE' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'NO DISPONIBLE' THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'NO DISPONIBLE ALTA INVERSION' THEN 1 ELSE 0 END)
                    FROM equipos
                    WHERE location = ?
                    GROUP BY tipo_equipo
                """, (ubicacion,))
            rows = c.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=["Tipo", "Disponibles", "No disponibles", "Alta inversión"])
                fig = go.Figure()
                fig.add_bar(x=df["Tipo"], y=df["Disponibles"], name="Disponibles", marker_color="blue")
                fig.add_bar(x=df["Tipo"], y=df["No disponibles"], name="No disponibles", marker_color="gray")
                fig.add_bar(x=df["Tipo"], y=df["Alta inversión"], name="Alta inversión", marker_color="black")
                fig.update_layout(barmode='group', title=f"Ubicación: {ubicacion}")
                st.plotly_chart(fig, use_container_width=True)
        if st.button("❌ Cerrar gráficos"):
            st.session_state['mostrar_grafico'] = False

    # Mostrar gráficos grúa móviles con texto central del total disponible/total
    elif st.session_state['mostrar_grafico_gruas']:
        st.markdown("### 🚛 Gráficos de GRUA MOVIL MANIPULADOR PARA LLENOS")
        for ubicacion in ubicaciones:
            c.execute("""
                SELECT 
                    SUM(CASE WHEN status = 'DISPONIBLE' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'NO DISPONIBLE' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN status = 'NO DISPONIBLE ALTA INVERSION' THEN 1 ELSE 0 END)
                FROM equipos
                WHERE tipo_equipo = 'GRUA MOVIL MANIPULADOR PARA LLENOS' AND location = ?
            """, (ubicacion,))
            resultado = c.fetchone()
            if resultado and any(resultado):
                disponibles, no_disp, no_disp_ai = resultado
                total = disponibles + no_disp + no_disp_ai
                porcentaje = round((disponibles / total) * 100, 1) if total else 0
                fig = go.Figure(data=[go.Pie(
                    labels=['DISPONIBLE', 'NO DISPONIBLE', 'ALTA INVERSIÓN'],
                    values=[disponibles, no_disp, no_disp_ai],
                    marker=dict(colors=["blue", "gray", "black"]),
                    hole=0.5,
                    textinfo='label+percent'
                )])
                fig.update_layout(
                    title=f"{ubicacion} - {porcentaje}% DISPONIBLE",
                    showlegend=True,
                    annotations=[dict(
                        text=f"{disponibles} de {total}",
                        x=0.5,
                        y=0.5,
                        font_size=20,
                        showarrow=False
                    )]
                )
                st.plotly_chart(fig, use_container_width=True)
        if st.button("❌ Cerrar gráficos"):
            st.session_state['mostrar_grafico_gruas'] = False

    # Mostrar tablas y botones
    elif not st.session_state['mostrar_grafico'] and not st.session_state['mostrar_grafico_gruas']:
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
