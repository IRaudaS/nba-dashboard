import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Nacho's NBA Hub", layout="wide", page_icon="🏀")

st.markdown("""
<style>
    .stMetric { text-align: center; }
    div[data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    .team-header { text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
    .live-indicator { color: red; font-weight: bold; animation: blink 2s infinite; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

st.title("🏀 Centro de Mando: Celtics vs Warriors")

if st.button("🔄 Actualizar Estadísticas"):
    st.rerun()

# IDs
CELTICS_ID = 1610612738
WARRIORS_ID = 1610612744

# --- INTELIGENCIA DE DATOS MEJORADA ---

def get_game_data(team_id):
    """
    Estrategia Híbrida:
    1. Busca si hay juego EN VIVO hoy en el Scoreboard.
    2. Si no, busca el último juego TERMINADO en el historial.
    """
    game_id = None
    game_status = ""
    is_live = False
    
    # PASO 1: Buscar en el Scoreboard (En vivo hoy)
    try:
        board = scoreboard.ScoreBoard()
        games_today = board.games.get_dict()
        
        for game in games_today:
            if game['homeTeam']['teamId'] == team_id or game['awayTeam']['teamId'] == team_id:
                game_id = game['gameId']
                game_status = f"🔴 EN VIVO: {game['gameStatusText']}"
                is_live = True
                break
    except:
        pass # Si falla el scoreboard, seguimos al historial

    # PASO 2: Si no encontramos juego en vivo, vamos al historial
    if not game_id:
        try:
            gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
            games = gamefinder.get_data_frames()[0]
            games = games.dropna(subset=['PTS']).sort_values('GAME_DATE', ascending=False)
            
            if not games.empty:
                last_game = games.iloc[0]
                game_id = last_game['GAME_ID']
                game_status = f"Finalizado ({last_game['GAME_DATE']}) - {last_game['MATCHUP']}"
            else:
                return None, "Sin datos recientes"
        except:
            return None, "Error buscando historial"

    # PASO 3: Teniendo el ID (sea vivo o pasado), sacamos el Box Score
    try:
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        players_stats = box.player_stats.get_data_frame()
        
        if players_stats.empty:
            return None, "El juego comenzó pero aún no hay stats de jugadores."
            
        my_team_stats = players_stats[players_stats['TEAM_ID'] == team_id].copy()
        
        # Limpieza visual
        display_df = my_team_stats[['PLAYER_NAME', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'MIN']]
        cols = ['PTS', 'REB', 'AST', 'STL', 'BLK']
        display_df[cols] = display_df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
        display_df = display_df.sort_values(by='PTS', ascending=False).reset_index(drop=True)
        
        return display_df, game_status
        
    except Exception as e:
        return None, f"Error al procesar datos: {e}"

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Estadísticas (Vivo/Reciente)", "📺 Marcador Visual"])

# --- PESTAÑA 1: ESTADÍSTICAS ---
with tab1:
    st.header("Rendimiento de Jugadores")
    st.caption("Muestra estadísticas en tiempo real si están jugando, o del último partido si descansan.")
    
    col_bos, col_gsw = st.columns(2)
    
    # --- CELTICS ---
    with col_bos:
        st.image(f"https://cdn.nba.com/logos/nba/{CELTICS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: green;'>Boston Celtics</div>", unsafe_allow_html=True)
        
        df_bos, status_bos = get_game_data(CELTICS_ID)
        if "EN VIVO" in status_bos:
            st.markdown(f"<p class='live-indicator'>{status_bos}</p>", unsafe_allow_html=True)
        else:
            st.info(status_bos)
            
        if df_bos is not None:
            st.dataframe(df_bos, hide_index=True, use_container_width=True)

    # --- WARRIORS ---
    with col_gsw:
        st.image(f"https://cdn.nba.com/logos/nba/{WARRIORS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: #FFC72C;'>Golden State Warriors</div>", unsafe_allow_html=True)
        
        df_gsw, status_gsw = get_game_data(WARRIORS_ID)
        if "EN VIVO" in status_gsw:
            st.markdown(f"<p class='live-indicator'>{status_gsw}</p>", unsafe_allow_html=True)
        else:
            st.info(status_gsw)
            
        if df_gsw is not None:
            st.dataframe(df_gsw, hide_index=True, use_container_width=True)

# --- PESTAÑA 2: MARCADOR CON LOGOS ---
with tab2:
    st.header("Pizarra en Vivo")
    
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        found = False
        
        for game in games:
            h_id = game['homeTeam']['teamId']
            a_id = game['awayTeam']['teamId']
            
            # Filtrar solo nuestros equipos
            if h_id in [CELTICS_ID, WARRIORS_ID] or a_id in [CELTICS_ID, WARRIORS_ID]:
                found = True
                
                # Datos
                h_team = game['homeTeam']
                a_team = game['awayTeam']
                
                # Logos
                h_logo = f"https://cdn.nba.com/logos/nba/{h_id}/primary/L/logo.svg"
                a_logo = f"https://cdn.nba.com/logos/nba/{a_id}/primary/L/logo.svg"
                
                st.markdown("---")
                c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
                
                with c1:
                    st.image(h_logo, width=80)
                    st.markdown(f"<h4 style='text-align: center;'>{h_team['teamTricode']}</h4>", unsafe_allow_html=True)
                with c2:
                    st.metric("Local", h_team['score'])
                with c3:
                    st.markdown(f"<div class='vs-text'>{game['gameStatusText']}</div>", unsafe_allow_html=True)
                with c4:
                    st.metric("Visita", a_team['score'])
                with c5:
                    st.image(a_logo, width=80)
                    st.markdown(f"<h4 style='text-align: center;'>{a_team['teamTricode']}</h4>", unsafe_allow_html=True)
                st.markdown("---")
        
        if not found:
