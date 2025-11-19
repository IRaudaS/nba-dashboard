import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2
from nba_api.stats.static import players, teams

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Nacho's NBA Hub", layout="wide", page_icon="🏀")

# CSS: Ajustes para que las tablas se vean compactas y bonitas
st.markdown("""
<style>
    .stMetric { text-align: center; }
    div[data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    .vs-text { font-size: 24px; font-weight: bold; text-align: center; padding-top: 20px; }
    .team-header { text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🏀 Centro de Mando: Celtics vs Warriors")

if st.button("🔄 Actualizar Estadísticas"):
    st.rerun()

# IDs de Equipos
CELTICS_ID = 1610612738
WARRIORS_ID = 1610612744

# --- FUNCIONES DE INTELIGENCIA DE DATOS ---

@st.cache_data(ttl=600) # Guardamos en caché por 10 mins para no saturar
def get_latest_game_stats(team_id):
    """
    Busca el último juego (o el actual) y devuelve las stats de los jugadores.
    """
    # 1. Buscar en el historial de juegos del equipo
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    games = gamefinder.get_data_frames()[0]
    
    # Ordenar por fecha para asegurar el último
    games = games.sort_values('GAME_DATE', ascending=False)
    
    if games.empty:
        return None, "No hay datos recientes"
        
    # Tomamos el juego más reciente (fila 0)
    last_game = games.iloc[0]
    game_id = last_game['GAME_ID']
    game_date = last_game['GAME_DATE']
    matchup = last_game['MATCHUP']
    wl = last_game['WL'] # W = Ganaron, L = Perdieron
    
    # 2. Obtener el Box Score (Detalle de jugadores) de ese juego
    box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    players_stats = box.player_stats.get_data_frame()
    
    # 3. Filtrar solo los jugadores de NUESTRO equipo (porque el boxscore trae a los dos)
    my_team_stats = players_stats[players_stats['TEAM_ID'] == team_id].copy()
    
    # 4. Limpiar y seleccionar columnas clave para tus hijos
    # PLAYER_NAME, PTS, REB, AST, STL (Robos), BLK (Bloqueos)
    display_df = my_team_stats[['PLAYER_NAME', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'MIN']]
    
    # Convertir a números para que se vea bien
    cols = ['PTS', 'REB', 'AST', 'STL', 'BLK']
    display_df[cols] = display_df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
    
    # Ordenar por Puntos (para ver a los líderes arriba)
    display_df = display_df.sort_values(by='PTS', ascending=False).reset_index(drop=True)
    
    return display_df, f"{matchup} ({game_date}) - Resultado: {wl}"

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Estadísticas Recientes (Comparativo)", "📺 Marcador en Vivo"])

# --- PESTAÑA 1: COMPARATIVO DE EQUIPOS (LO QUE PIDIÓ TU HIJO MAYOR) ---
with tab1:
    st.header("Rendimiento del Último Juego")
    st.caption("Aquí mostramos el último partido que jugaron, sea hoy o hace días.")

    col_bos, col_gsw = st.columns(2)

    # --- COLUMNA CELTICS ---
    with col_bos:
        st.image(f"https://cdn.nba.com/logos/nba/{CELTICS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: green;'>Boston Celtics</div>", unsafe_allow_html=True)
        
        with st.spinner("Cargando datos de Boston..."):
            df_bos, context_bos = get_latest_game_stats(CELTICS_ID)
            st.info(f"📅 {context_bos}")
            if df_bos is not None:
                # Mostramos la tabla pero ocultamos el índice feo de pandas
                st.dataframe(df_bos, hide_index=True, use_container_width=True)

    # --- COLUMNA WARRIORS ---
    with col_gsw:
        st.image(f"https://cdn.nba.com/logos/nba/{WARRIORS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: #FFC72C;'>Golden State Warriors</div>", unsafe_allow_html=True)
        
        with st.spinner("Cargando datos de Golden State..."):
            df_gsw, context_gsw = get_latest_game_stats(WARRIORS_ID)
            st.info(f"📅 {context_gsw}")
            if df_gsw is not None:
                st.dataframe(df_gsw, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("### 🏆 Líderes de Puntos")
    # Pequeño insight rápido
    if df_bos is not None and df_gsw is not None:
        top_bos = df_bos.iloc[0]
        top_gsw = df_gsw.iloc[0]
        
        c1, c2 = st.columns(2)
        c1.metric(f"Mejor Celtic ({top_bos['PLAYER_NAME']})", f"{top_bos['PTS']} Pts")
        c2.metric(f"Mejor Warrior ({top_gsw['PLAYER_NAME']})", f"{top_gsw['PTS']} Pts")

# --- PESTAÑA 2: MARCADOR EN VIVO (SIMPLE) ---
with tab2:
    # Reutilizamos la lógica simple para ver si hay juego HOY
    st.header("¿Hay acción ahora mismo?")
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()
    found = False
    
    for game in games:
        h_id = game['homeTeam']['teamId']
        a_id = game['awayTeam']['teamId']
        if h_id in [CELTICS_ID, WARRIORS_ID] or a_id in [CELTICS_ID, WARRIORS_ID]:
            found = True
            # Renderizado simple del juego
            c1, c2, c3 = st.columns([1,0.5,1])
            c1.metric(game['homeTeam']['teamTricode'], game['homeTeam']['score'])
            c2.write(f"VS\n{game['gameStatusText']}")
            c3.metric(game['awayTeam']['teamTricode'], game['awayTeam']['score'])
            st.divider()
            
    if not found:
        st.write("No hay juegos en vivo de tus equipos en este momento. Revisa la pestaña de Estadísticas Recientes.")
