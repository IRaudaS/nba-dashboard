import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Nacho's NBA Hub", layout="wide", page_icon="🏀")

# CSS para centrar imágenes y mejorar métricas
st.markdown("""
<style>
    .stMetric { text-align: center; }
    div[data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    .vs-text { font-size: 30px; font-weight: bold; text-align: center; padding-top: 25px; }
</style>
""", unsafe_allow_html=True)

st.title("🏀 Centro de Mando: Celtics vs Warriors")

# Botón de actualización manual (La forma segura de ver datos en vivo)
if st.button("🔄 Actualizar Datos en Vivo"):
    st.rerun()

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📺 Marcador en Vivo", "⚖️ Duelo de Estrellas"])

# --- PESTAÑA 1: JUEGO DEL DÍA ---
with tab1:
    st.header("Pizarra de Juegos")
    
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        
        # IDs de los equipos clave
        MY_TEAMS = [1610612738, 1610612744] # Celtics, Warriors
        
        found_game = False
        
        if not games:
            st.info("😴 No hay juegos programados en la NBA para hoy.")
        else:
            for game in games:
                home_id = game['homeTeam']['teamId']
                away_id = game['awayTeam']['teamId']
                
                # Filtrar: Mostramos el juego SI es Celtics o Warriors. 
                # (Si quieres ver TODOS los juegos, borra la linea del 'if')
                if home_id in MY_TEAMS or away_id in MY_TEAMS:
                    found_game = True
                    
                    # Datos
                    h_team = game['homeTeam']
                    a_team = game['awayTeam']
                    status = game['gameStatusText']
                    
                    # URLs de Logos
                    h_logo = f"https://cdn.nba.com/logos/nba/{home_id}/primary/L/logo.svg"
                    a_logo = f"https://cdn.nba.com/logos/nba/{away_id}/primary/L/logo.svg"
                    
                    # --- DISEÑO DEL MARCADOR VISUAL ---
                    with st.container():
                        st.markdown("---")
                        # 5 columnas: Logo L | Pts L | VS | Pts V | Logo V
                        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
                        
                        with c1:
                            st.image(h_logo, width=100)
                            st.markdown(f"<h3 style='text-align: center;'>{h_team['teamTricode']}</h3>", unsafe_allow_html=True)
                        
                        with c2:
                            st.metric("Local", h_team['score'])
                            
                        with c3:
                            st.markdown(f"<div class='vs-text'>{status}</div>", unsafe_allow_html=True)
                            
                        with c4:
                            st.metric("Visita", a_team['score'])
                            
                        with c5:
                            st.image(a_logo, width=100)
                            st.markdown(f"<h3 style='text-align: center;'>{a_team['teamTricode']}</h3>", unsafe_allow_html=True)
                        st.markdown("---")

            if not found_game:
                st.success("✅ Hoy hay descanso. Ni Celtics ni Warriors juegan hoy.")
                st.caption("Revisa mañana para más acción.")
                
    except Exception as e:
        st.error(f"Error conectando con la NBA: {e}")

# --- PESTAÑA 2: DUELO DE ESTRELLAS CON FOTOS ---
with tab2:
    st.header("Comparador Visual")
    
    col_select_a, col_select_b = st.columns(2)
    
    celtics_roster = ["Jayson Tatum", "Jaylen Brown", "Jrue Holiday", "Derrick White", "Kristaps Porzingis"]
    warriors_roster = ["Stephen Curry", "Draymond Green", "Andrew Wiggins", "Jonathan Kuminga", "Buddy Hield"]
    
    with col_select_a:
        p1_name = st.selectbox("Jugador Celtics 🍀", celtics_roster, index=0)
    with col_select_b:
        p2_name = st.selectbox("Jugador Warriors 🌉", warriors_roster, index=0)

    if st.button("⚔️ ¡Comparar!"):
        # Función para obtener datos y FOTO
        def get_player_data(name):
            nba_players = players.get_players()
            player_info = [p for p in nba_players if p['full_name'] == name][0]
            p_id = player_info['id']
            
            # Stats
            career = playercareerstats.PlayerCareerStats(player_id=p_id)
            df = career.get_data_frames()[0]
            
            # Foto URL
            img_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p_id}.png"
            
            return df, img_url

        # Cargando...
        with st.spinner('Analizando biométricos...'):
            df1, img1 = get_player_data(p1_name)
            df2, img2 = get_player_data(p2_name)
            
            # --- VISUALIZACIÓN CARA A CARA ---
            col_p1, col_stats, col_p2 = st.columns([1, 2, 1])
            
            with col_p1:
                st.image(img1, use_column_width=True)
                st.markdown(f"<h3 style='text-align: center; color: green;'>{p1_name}</h3>", unsafe_allow_html=True)

            with col_p2:
                st.image(img2, use_column_width=True)
                st.markdown(f"<h3 style='text-align: center; color: gold;'>{p2_name}</h3>", unsafe_allow_html=True)
                
            with col_stats:
                st.markdown("### Stats de Carrera")
                
                # Puntos
                diff = round(df1['PTS'].mean() - df2['PTS'].mean(), 1)
                st.metric("Puntos por Juego (PPG)", f"{round(df1['PTS'].mean(), 1)} vs {round(df2['PTS'].mean(), 1)}", delta=diff)
                
                # Asistencias
                diff_ast = round(df1['AST'].mean() - df2['AST'].mean(), 1)
                st.metric("Asistencias (APG)", f"{round(df1['AST'].mean(), 1)} vs {round(df2['AST'].mean(), 1)}", delta=diff_ast)
                
                # Partidos Jugados
                st.metric("Experiencia (Juegos)", f"{df1['GP'].count()} vs {df2['GP'].count()}")
