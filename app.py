import streamlit as st
import pandas as pd
from datetime import datetime
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Nacho's NBA Hub", layout="wide", page_icon="🏀")

# Estilos CSS para darle colores de equipos
st.markdown("""
<style>
    .celtics { color: #007A33; font-weight: bold; }
    .warriors { color: #FFC72C; font-weight: bold; }
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏀 Centro de Mando: Celtics vs Warriors")
st.markdown("Bienvenido al cuartel general de la familia.")

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📅 Juego del Día", "⚔️ Duelo de Hermanos"])

# --- PESTAÑA 1: JUEGO DEL DÍA ---
with tab1:
    st.header("¿Juegan hoy?")
    
    # Obtener datos en vivo
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        
        # IDs de los equipos
        TEAMS = {
            1610612738: {"name": "Boston Celtics", "logo": "🍀", "style": "celtics"},
            1610612744: {"name": "Golden State Warriors", "logo": "🌉", "style": "warriors"}
        }
        
        found_game = False
        
        if not games:
            st.info("No hay juegos programados en la NBA para hoy.")
        else:
            for game in games:
                home_id = game['homeTeam']['teamId']
                away_id = game['awayTeam']['teamId']
                
                # Si juega alguno de los nuestros
                if home_id in TEAMS or away_id in TEAMS:
                    found_game = True
                    
                    # Datos del partido
                    home_team = game['homeTeam']
                    away_team = game['awayTeam']
                    status = game['gameStatusText']
                    
                    # Diseño de tarjeta de partido
                    col_home, col_vs, col_away = st.columns([2, 1, 2])
                    
                    with col_home:
                        st.markdown(f"### {home_team['teamTricode']}")
                        st.metric("Puntos", home_team['score'])
                        
                    with col_vs:
                        st.markdown("## VS")
                        st.caption(status)
                        
                    with col_away:
                        st.markdown(f"### {away_team['teamTricode']}")
                        st.metric("Puntos", away_team['score'])
                        
                    st.divider()

            if not found_game:
                st.success("✅ Hoy hay descanso. Ni Celtics ni Warriors juegan hoy.")
                
    except Exception as e:
        st.error(f"No se pudo conectar con la NBA: {e}")

# --- PESTAÑA 2: DUELO DE ESTRELLAS ---
with tab2:
    st.header("Comparador de Leyendas")
    st.write("Elige a tu jugador para ver quién manda.")
    
    col_a, col_b = st.columns(2)
    
    # Listas predefinidas para facilitar la búsqueda
    celtics_stars = ["Jayson Tatum", "Jaylen Brown", "Jrue Holiday"]
    warriors_stars = ["Stephen Curry", "Draymond Green", "Andrew Wiggins"]
    
    with col_a:
        st.markdown('<p class="celtics">🍀 Elige Celtic</p>', unsafe_allow_html=True)
        p1_name = st.selectbox("Jugador BOS", celtics_stars, index=0)
        
    with col_b:
        st.markdown('<p class="warriors">🌉 Elige Warrior</p>', unsafe_allow_html=True)
        p2_name = st.selectbox("Jugador GSW", warriors_stars, index=0)

    if st.button("¡Analizar Stats!"):
        with st.spinner('Buscando en los archivos de la NBA...'):
            # Función auxiliar para buscar ID y stats
            def get_player_stats(name):
                nba_players = players.get_players()
                player_dict = [p for p in nba_players if p['full_name'] == name][0]
                career = playercareerstats.PlayerCareerStats(player_id=player_dict['id'])
                df = career.get_data_frames()[0]
                return df

            # Obtener datos
            df1 = get_player_stats(p1_name)
            df2 = get_player_stats(p2_name)
            
            # Calcular promedios de carrera
            st.subheader("Promedios de Carrera (Toda la vida)")
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            # Puntos
            diff_pts = round(df1['PTS'].mean() - df2['PTS'].mean(), 1)
            metric_col1.metric(f"Puntos p/j ({p1_name})", round(df1['PTS'].mean(), 1), delta=diff_pts)
            metric_col1.metric(f"Puntos p/j ({p2_name})", round(df2['PTS'].mean(), 1))
            
            # Asistencias
            metric_col2.metric(f"Asistencias ({p1_name})", round(df1['AST'].mean(), 1))
            metric_col2.metric(f"Asistencias ({p2_name})", round(df2['AST'].mean(), 1))

            # Triples Totales (El dato Warriors)
            total_3pm_1 = df1['FG3M'].sum()
            total_3pm_2 = df2['FG3M'].sum()
            metric_col3.metric("Triples Totales de Carrera", f"{total_3pm_1} vs {total_3pm_2}")
            
            if total_3pm_2 > total_3pm_1:
                st.caption(f"🎯 {p2_name} gana en triples (como era de esperarse en GSW).")
            else:
                st.caption(f"🎯 {p1_name} lleva la delantera en triples.")
