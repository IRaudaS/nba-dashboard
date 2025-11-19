import streamlit as st
import pandas as pd
from nba_api.live.nba.endpoints import scoreboard, boxscore
from nba_api.stats.endpoints import leaguegamefinder, boxscoretraditionalv2

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Nacho's NBA Hub", layout="wide", page_icon="🏀")

st.markdown("""
<style>
    .stMetric { text-align: center; }
    div[data-testid="stImage"] { display: block; margin-left: auto; margin-right: auto; }
    .team-header { text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
    .live-indicator { color: red; font-weight: bold; animation: blink 2s infinite; text-align: center; }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

st.title("🏀 Centro de Mando: Celtics vs Warriors")

if st.button("🔄 Actualizar Estadísticas"):
    st.rerun()

# IDs
CELTICS_ID = 1610612738
WARRIORS_ID = 1610612744

# --- NUEVA LÓGICA DE PARSEO EN VIVO ---
def process_live_json(players_list):
    """Convierte el JSON complejo de la API Live en un DataFrame simple"""
    data = []
    for p in players_list:
        # Solo procesamos si el jugador ha jugado (tiene segundos en cancha)
        # o si tiene estadísticas activas
        stats = p.get('statistics', {})
        mins = stats.get('minutes', 'PT00M00.00S')
        
        if mins != 'PT00M00.00S': # Formato ISO 8601 de duración
            data.append({
                'PLAYER_NAME': p.get('nameI', 'Desconocido'), # nameI suele ser Inicial + Apellido
                'PTS': stats.get('points', 0),
                'REB': stats.get('reboundsTotal', 0),
                'AST': stats.get('assists', 0),
                'STL': stats.get('steals', 0),
                'BLK': stats.get('blocks', 0)
            })
            
    if not data:
        return pd.DataFrame()
        
    df = pd.DataFrame(data)
    # Ordenar por puntos
    return df.sort_values(by='PTS', ascending=False).reset_index(drop=True)

def get_game_data(team_id):
    game_id = None
    game_status = ""
    
    # 1. INTENTO EN VIVO (PRIORIDAD MÁXIMA)
    try:
        board = scoreboard.ScoreBoard()
        games_today = board.games.get_dict()
        
        for game in games_today:
            h_id = game['homeTeam']['teamId']
            a_id = game['awayTeam']['teamId']
            
            if h_id == team_id or a_id == team_id:
                game_id = game['gameId']
                game_status = f"🔴 EN VIVO: {game['gameStatusText']}"
                
                # --- AQUÍ ESTÁ EL CAMBIO MÁGICO ---
                # Usamos el endpoint LIVE BOXSCORE
                box = boxscore.BoxScore(game_id=game_id)
                data = box.get_dict()
                
                # Identificar si somos Home o Away para sacar los jugadores correctos
                if h_id == team_id:
                    players_list = data['game']['homeTeam']['players']
                else:
                    players_list = data['game']['awayTeam']['players']
                
                df = process_live_json(players_list)
                
                if df.empty:
                    return None, "Juego activo, pero datos vacíos (Tiempo fuera o inicio)."
                
                return df, game_status
                
    except Exception as e:
        pass # Si falla el live, caemos calladitos al histórico

    # 2. INTENTO HISTÓRICO (SI NO HAY VIVO)
    try:
        gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
        games = gamefinder.get_data_frames()[0]
        games = games.dropna(subset=['PTS']).sort_values('GAME_DATE', ascending=False)
        
        if not games.empty:
            last_game = games.iloc[0]
            game_id = last_game['GAME_ID']
            game_status = f"Finalizado ({last_game['GAME_DATE']}) - {last_game['MATCHUP']}"
            
            # Endpoint Tradicional (Mejor para juegos pasados)
            box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            players_stats = box.player_stats.get_data_frame()
            my_team_stats = players_stats[players_stats['TEAM_ID'] == team_id].copy()
            
            display_df = my_team_stats[['PLAYER_NAME', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
            cols = ['PTS', 'REB', 'AST', 'STL', 'BLK']
            display_df[cols] = display_df[cols].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            display_df = display_df.sort_values(by='PTS', ascending=False).reset_index(drop=True)
            
            return display_df, game_status
    except:
        return None, "Error buscando datos."

    return None, "Sin datos recientes"

# --- PESTAÑAS ---
tab1, tab2 = st.tabs(["📊 Estadísticas", "📺 Marcador"])

# --- PESTAÑA 1 ---
with tab1:
    col_bos, col_gsw = st.columns(2)
    
    # CELTICS
    with col_bos:
        st.image(f"https://cdn.nba.com/logos/nba/{CELTICS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: green;'>Boston Celtics</div>", unsafe_allow_html=True)
        df, status = get_game_data(CELTICS_ID)
        if "EN VIVO" in status:
            st.markdown(f"<p class='live-indicator'>{status}</p>", unsafe_allow_html=True)
        else:
            st.info(status)
        if df is not None:
            st.dataframe(df, hide_index=True, use_container_width=True)

    # WARRIORS
    with col_gsw:
        st.image(f"https://cdn.nba.com/logos/nba/{WARRIORS_ID}/primary/L/logo.svg", width=80)
        st.markdown("<div class='team-header' style='color: #FFC72C;'>Golden State Warriors</div>", unsafe_allow_html=True)
        df, status = get_game_data(WARRIORS_ID)
        if "EN VIVO" in status:
            st.markdown(f"<p class='live-indicator'>{status}</p>", unsafe_allow_html=True)
        else:
            st.info(status)
        if df is not None:
            st.dataframe(df, hide_index=True, use_container_width=True)

# --- PESTAÑA 2 ---
with tab2:
    # Código del marcador (igual que antes)
    try:
        board = scoreboard.ScoreBoard()
        games = board.games.get_dict()
        found = False
        for game in games:
            h_id = game['homeTeam']['teamId']
            a_id = game['awayTeam']['teamId']
            if h_id in [CELTICS_ID, WARRIORS_ID] or a_id in [CELTICS_ID, WARRIORS_ID]:
                found = True
                st.markdown("---")
                c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
                with c1:
                    st.image(f"https://cdn.nba.com/logos/nba/{h_id}/primary/L/logo.svg", width=70)
                    st.metric("Local", game['homeTeam']['score'])
                with c3:
                    st.markdown(f"<div class='vs-text'>{game['gameStatusText']}</div>", unsafe_allow_html=True)
                with c5:
                    st.metric("Visita", game['awayTeam']['score'])
                    st.image(f"https://cdn.nba.com/logos/nba/{a_id}/primary/L/logo.svg", width=70)
                st.markdown("---")
        if not found:
            st.write("No hay juegos activos.")
    except:
        st.error("Error en marcador.")
