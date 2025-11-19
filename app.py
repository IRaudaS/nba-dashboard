import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Nacho's NBA Hub", layout="wide", page_icon="🏀")

# CSS
st.markdown("""
<style>
    .stMetric { text-align: center; }
    div[data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
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

@st.cache_data(ttl=600)
def get_latest_game_stats(team_id):
    """
    Busca el último juego JUGADO y devuelve las stats.
    """
    try:
        # 1. Buscar historial
        gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
        games = gamefinder.get_data_frames()[0]
        
        # --- CORRECCIÓN IMPORTANTE ---
        # Filtramos juegos que no tienen puntos (PTS es NaN o None)
        # Esto evita que agarre juegos programados a futuro
        games = games.dropna(subset=['PTS'])
        
        if games.empty:
            return None, "No se encontraron juegos recientes."
            
        # Ordenar por fecha
        games = games.sort_values('GAME_DATE', ascending=False)
        
        # Tomamos el último juego VÁLIDO
        last_game = games.iloc[0]
        game_id = last_game['GAME_ID']
        game_date = last_game['GAME_DATE']
        matchup = last_game['MATCHUP']
        wl = last_game['WL']
        
        # 2. Obtener el Box Score
        box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        players_stats = box.player_stats.get_data_frame()
        
        if players_stats.empty:
            return None, "Datos del juego aún no disponibles."

        # 3. Filtrar equipo y limpiar
        my_team_stats = players_stats[players_stats['TEAM_ID'] == team_id].copy()
        
        if my_team_stats.empty:
            return None, "No hay stats de jugadores para este equipo."

        display_df = my_team_stats[['PLAYER_NAME', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'MIN']]
        
        cols = ['PTS', 'REB', 'AST', 'STL', 'BLK']
        display_df[cols] = display_df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
        
        # Ordenar por Puntos
        display_df = display_df.sort_values(by='PTS', ascending=False).reset_index(drop=True)
        
        return display_df, f"{matchup} ({game_date}) - Resultado: {wl}"

    except Exception as e:
        return None, f"Error procesando datos: {e}"

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Estadísticas Recientes", "📺 Marcador en Vivo"])

# --- PESTAÑA 1 ---
with tab1:
    st.header("Rendimiento del Último Juego")
    col_bos, col_gsw = st.columns(2)

    # Variables para guardar los DataFrames
    df_bos = None
    df_gsw = None

    # --- COLUMNA CELTICS ---
    with col_bos:
        st.image(f"https://cdn.nba.com/logos/nba/{CELTICS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: green;'>Boston Celtics</div>", unsafe_allow_html=True)
        
        with st.spinner("Cargando Boston..."):
            df_bos, context_bos = get_latest_game_stats(CELTICS_ID)
            st.info(f"📅 {context_bos}")
            if df_bos is not None and not df_bos.empty:
                st.dataframe(df_bos, hide_index=True, use_container_width=True)

    # --- COLUMNA WARRIORS ---
    with col_gsw:
        st.image(f"https://cdn.nba.com/logos/nba/{WARRIORS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: #FFC72C;'>Golden State Warriors</div>", unsafe_allow_html=True)
        
        with st.spinner("Cargando Golden State..."):
            df_gsw, context_gsw = get_latest_game_stats(WARRIORS_ID)
            st.info(f"📅 {context_gsw}")
            if df_gsw is not None and not df_gsw.empty:
                st.dataframe(df_gsw, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown("### 🏆 Líderes de Puntos")
    
    # --- CORRECCIÓN IMPORTANTE: CHECK DE SEGURIDAD ---
    # Solo intentamos buscar al líder si las tablas NO están vacías
    if (df_bos is not None and not df_bos.empty) and (df_gsw is not None and not df_gsw.empty):
        try:
            top_bos = df_bos.iloc[0]
            top_gsw = df_gsw.iloc[0]
            
            c1, c2 = st.columns(2)
            c1.metric(f"Mejor Celtic ({top_bos['PLAYER_NAME']})", f"{top_bos['PTS']} Pts")
            c2.metric(f"Mejor Warrior ({top_gsw['PLAYER_NAME']})", f"{top_gsw['PTS']} Pts")
        except Exception as e:
            st.warning("No se pudieron calcular los líderes comparativos.")
    else:
        st.write("Esperando datos completos para mostrar el duelo de líderes.")

# --- PESTAÑA 2 ---
with tab2:
    st.header("Pizarra en Vivo")
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()
    found = False
    
    for game in games:
        h_id = game['homeTeam']['teamId']
        a_id = game['awayTeam']['teamId']
        if h_id in [CELTICS_ID, WARRIORS_ID] or a_id in [CELTICS_ID, WARRIORS_ID]:
            found = True
            c1, c2, c3 = st.columns([1,0.5,1])
            c1.metric(game['homeTeam']['teamTricode'], game['homeTeam']['score'])
            c2.write(f"VS\n{game['gameStatusText']}")
            c3.metric(game['awayTeam']['teamTricode'], game['awayTeam']['score'])
            st.divider()
            
    if not found:
        st.info("No hay juegos activos en este momento.")
