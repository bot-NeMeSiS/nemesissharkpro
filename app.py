
import os
import time
import json
import re
import sqlite3
import hashlib
import urllib.request
import urllib.parse
import requests
try:
    from pywebpush import webpush, WebPushException
except Exception:
    webpush = None
    class WebPushException(Exception):
        pass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, render_template, request, redirect, session, jsonify, send_from_directory, Response

APP_VERSION = "NeMeSiS_SHARK_PRO_V59_0_BACKEND_SPLIT_SECURITY_PRO"
APP_NAME = "NeMeSiS SHARK PRO"


PLAN_AI_LIMITS = {
    "FREE": 0,
    "PRO": 15,
    "ELITE": 100,
    "ADMIN": 9999,
}

def get_ai_limit(plan):
    return PLAN_AI_LIMITS.get((plan or "FREE").upper(), 0)



app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nemesis-change-this-secret")
MADRID_TZ = ZoneInfo("Europe/Madrid")

def madrid_now():
    return datetime.now(MADRID_TZ)

def madrid_date_today():
    return madrid_now().date()


def madrid_iso_now():
    return madrid_now().replace(microsecond=0).isoformat()


def add_months_madrid(months=1):
    """Suma meses sin depender de librerías externas."""
    base = madrid_now().replace(microsecond=0)
    months = int(months or 1)
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    days = [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day = min(base.day, days[month-1])
    return base.replace(year=year, month=month, day=day).isoformat()


def days_until_iso(iso_value):
    if not iso_value:
        return None
    try:
        txt = str(iso_value).replace('Z', '+00:00')
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MADRID_TZ)
        delta = dt.astimezone(MADRID_TZ) - madrid_now()
        return max(0, delta.days + (1 if delta.seconds > 0 else 0))
    except Exception:
        return None


DB_PATH = os.environ.get("DB_PATH", "/data/database.db").strip() or "/data/database.db"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin").strip() or "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234").strip() or "1234"

# V36.0: Professional Platform Layer — app instalable + alertas preparadas.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
ENABLE_PRO_ALERTS = os.environ.get("ENABLE_PRO_ALERTS", "false").lower() == "true"
TELEGRAM_ALERT_MIN_SCORE = int(os.environ.get("TELEGRAM_ALERT_MIN_SCORE", "68") or 68)
TELEGRAM_ODDS_ALERT_MIN_SCORE = int(os.environ.get("TELEGRAM_ODDS_ALERT_MIN_SCORE", "68") or 68)
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")
TELEGRAM_GROUP_URL = os.environ.get("TELEGRAM_GROUP_URL", "").strip()
# V46.0: Telegram full automation por membresía. Canales separados opcionales; canal único como fallback.
TELEGRAM_FREE_CHAT_ID = os.environ.get("TELEGRAM_FREE_CHAT_ID", "").strip()
TELEGRAM_PRO_CHAT_ID = os.environ.get("TELEGRAM_PRO_CHAT_ID", "").strip()
TELEGRAM_ELITE_CHAT_ID = os.environ.get("TELEGRAM_ELITE_CHAT_ID", "").strip()
TELEGRAM_FREE_GROUP_URL = os.environ.get("TELEGRAM_FREE_GROUP_URL", TELEGRAM_GROUP_URL).strip()
TELEGRAM_PRO_GROUP_URL = os.environ.get("TELEGRAM_PRO_GROUP_URL", TELEGRAM_GROUP_URL).strip()
TELEGRAM_ELITE_GROUP_URL = os.environ.get("TELEGRAM_ELITE_GROUP_URL", TELEGRAM_GROUP_URL).strip()
TELEGRAM_AUTO_ALERT_ENGINE = os.environ.get("TELEGRAM_AUTO_ALERT_ENGINE", "true").lower() == "true"
TELEGRAM_AUTO_ALERT_MAX_PER_RUN = int(os.environ.get("TELEGRAM_AUTO_ALERT_MAX_PER_RUN", "3") or 3)
TELEGRAM_ALERT_ONLY_PREMIUM = os.environ.get("TELEGRAM_ALERT_ONLY_PREMIUM", "false").lower() == "true"
TELEGRAM_ALERT_NEW_PICKS = os.environ.get("TELEGRAM_ALERT_NEW_PICKS", "true").lower() == "true"
TELEGRAM_ALERT_RESULTS = os.environ.get("TELEGRAM_ALERT_RESULTS", "true").lower() == "true"
TELEGRAM_SEND_ON_ADMIN_CREATE = os.environ.get("TELEGRAM_SEND_ON_ADMIN_CREATE", "true").lower() == "true"
TELEGRAM_SEND_TO_CONNECTED_USERS = os.environ.get("TELEGRAM_SEND_TO_CONNECTED_USERS", "true").lower() == "true"
TELEGRAM_SEND_TO_PLAN_CHANNELS = os.environ.get("TELEGRAM_SEND_TO_PLAN_CHANNELS", "true").lower() == "true"
TELEGRAM_TEST_CHAT_ID = os.environ.get("TELEGRAM_TEST_CHAT_ID", "").strip()

# V47.0: SHARK Quality Control — evita spam, repetidos y señales flojas antes de avisar al cliente.
SHARK_MIN_SCORE = int(os.environ.get("SHARK_MIN_SCORE", os.environ.get("TELEGRAM_ALERT_MIN_SCORE", "70")) or 70)
MIN_ALLOWED_ODDS = float(os.environ.get("MIN_ALLOWED_ODDS", "1.40") or 1.40)
MAX_ALLOWED_ODDS = float(os.environ.get("MAX_ALLOWED_ODDS", "4.50") or 4.50)
MAX_ALERTS_PER_HOUR = int(os.environ.get("MAX_ALERTS_PER_HOUR", "6") or 6)
TELEGRAM_QUIET_HOURS = os.environ.get("TELEGRAM_QUIET_HOURS", "true").lower() == "true"
TELEGRAM_QUIET_START = int(os.environ.get("TELEGRAM_QUIET_START", "1") or 1)
TELEGRAM_QUIET_END = int(os.environ.get("TELEGRAM_QUIET_END", "8") or 8)
TELEGRAM_BLOCK_DUPLICATE_MATCHES = os.environ.get("TELEGRAM_BLOCK_DUPLICATE_MATCHES", "true").lower() == "true"
TELEGRAM_QUALITY_MODE = os.environ.get("TELEGRAM_QUALITY_MODE", "strict").strip().lower() or "strict"
# V44.0: experiencia live + autocierre seguro.
AUTO_RESULT_SETTLEMENT = os.environ.get("AUTO_RESULT_SETTLEMENT", "true").lower() == "true"
LIVE_PRO_MODE = os.environ.get("LIVE_PRO_MODE", "true").lower() == "true"
PWA_OFFLINE_MESSAGE = "NeMeSiS SHARK PRO está sin conexión. Vuelve a abrir cuando tengas internet para actualizar cuotas y picks reales."

# V50.0: Push Notifications preparadas para app instalada/navegador.
# Para activar push real: genera claves VAPID y ponlas en Render.
ENABLE_PUSH_NOTIFICATIONS = os.environ.get("ENABLE_PUSH_NOTIFICATIONS", "true").lower() == "true"
PUSH_VAPID_PUBLIC_KEY = os.environ.get("PUSH_VAPID_PUBLIC_KEY", "").strip()
PUSH_VAPID_PRIVATE_KEY = os.environ.get("PUSH_VAPID_PRIVATE_KEY", "").strip()
PUSH_VAPID_SUBJECT = os.environ.get("PUSH_VAPID_SUBJECT", "mailto:soporte@nemesis-shark.local").strip() or "mailto:soporte@nemesis-shark.local"
PUSH_SEND_ON_NEW_PICK = os.environ.get("PUSH_SEND_ON_NEW_PICK", "true").lower() == "true"
PUSH_SEND_ON_RESULTS = os.environ.get("PUSH_SEND_ON_RESULTS", "true").lower() == "true"
PUSH_MIN_SCORE = int(os.environ.get("PUSH_MIN_SCORE", os.environ.get("SHARK_MIN_SCORE", "70")) or 70)
PUSH_MAX_DAILY_PER_USER = int(os.environ.get("PUSH_MAX_DAILY_PER_USER", "8") or 8)

# V51.0: Performance + Stability Engine
# El objetivo es que las visitas de clientes NO disparen trabajo pesado ni tumben Render.
PERFORMANCE_SAFE_MODE = os.environ.get("PERFORMANCE_SAFE_MODE", "true").lower() == "true"
PUBLIC_LIVE_REFRESH_COOLDOWN_SECONDS = int(os.environ.get("PUBLIC_LIVE_REFRESH_COOLDOWN_SECONDS", "600") or 600)
ADMIN_REFRESH_COOLDOWN_SECONDS = int(os.environ.get("ADMIN_REFRESH_COOLDOWN_SECONDS", "180") or 180)
TELEGRAM_AUTO_SEND_DURING_REFRESH = os.environ.get("TELEGRAM_AUTO_SEND_DURING_REFRESH", "false").lower() == "true"
MAX_SPORTS_PER_REFRESH = int(os.environ.get("MAX_SPORTS_PER_REFRESH", "6") or 6)
HTTP_TIMEOUT_SECONDS = int(os.environ.get("HTTP_TIMEOUT_SECONDS", "7") or 7)
BACKGROUND_JOBS_ENABLED = os.environ.get("BACKGROUND_JOBS_ENABLED", "false").lower() == "true"

# V54.0: Stability Hardening — evita workers colgados por refrescos concurrentes o tablas gigantes.
STABILITY_HARD_MODE = os.environ.get("STABILITY_HARD_MODE", "true").lower() == "true"
API_REFRESH_LOCK_SECONDS = int(os.environ.get("API_REFRESH_LOCK_SECONDS", "240") or 240)
DB_BUSY_TIMEOUT_MS = int(os.environ.get("DB_BUSY_TIMEOUT_MS", "8000") or 8000)
DB_ENABLE_WAL = os.environ.get("DB_ENABLE_WAL", "true").lower() == "true"
PRUNE_LOGS_ON_STARTUP = os.environ.get("PRUNE_LOGS_ON_STARTUP", "true").lower() == "true"
MAX_ALERT_LOG_ROWS = int(os.environ.get("MAX_ALERT_LOG_ROWS", "800") or 800)
MAX_API_USAGE_LOG_ROWS = int(os.environ.get("MAX_API_USAGE_LOG_ROWS", "1200") or 1200)
CLIENT_API_MAX_ROWS = int(os.environ.get("CLIENT_API_MAX_ROWS", "24") or 24)
LIVE_SNAPSHOT_LIMIT = int(os.environ.get("LIVE_SNAPSHOT_LIMIT", "8") or 8)
PUBLIC_ENDPOINT_TIMEOUT_GUARD = os.environ.get("PUBLIC_ENDPOINT_TIMEOUT_GUARD", "true").lower() == "true"

# V31.7: motor principal SOLO The Odds API. API-Football queda desactivado por defecto
# para evitar pantallas vacías cuando no tienes cuenta/clave API-SPORTS.
def current_football_season():
    now = datetime.utcnow()
    return str(now.year - 1 if now.month < 7 else now.year)

# Live / Odds manager real-only. Si existe ODDS_API_KEY, carga eventos reales próximos y cuotas.
THESPORTSDB_KEY = os.environ.get("THESPORTSDB_KEY", "").strip()
ODDS_API_KEY = (os.environ.get("ODDS_API_KEY") or os.environ.get("THE_ODDS_API_KEY") or "").strip()
# V35.0: proveedor opcional para clasificaciones y escudos reales.
# The Odds API da cuotas/partidos, pero no clasificaciones ni logos oficiales.
# FOOTBALL_DATA_KEY permite activar tablas tipo Flashscore sin romper la app si falta la clave.
FOOTBALL_DATA_KEY = (os.environ.get("FOOTBALL_DATA_KEY") or os.environ.get("FOOTBALLDATA_KEY") or "").strip()
LOCAL_TEAM_LOGOS_DIR = os.environ.get("LOCAL_TEAM_LOGOS_DIR", "static/team_logos").strip() or "static/team_logos"
ENABLE_STANDINGS = os.environ.get("ENABLE_STANDINGS", "true").lower() == "true"
STANDINGS_CACHE_MINUTES = int(os.environ.get("STANDINGS_CACHE_MINUTES", "720") or 720)
STANDINGS_COMPETITIONS = [
    {"code":"PD", "name":"LaLiga", "country":"España", "tier":"TOP", "filter":"liga"},
    {"code":"PL", "name":"Premier League", "country":"Inglaterra", "tier":"TOP", "filter":"premier"},
    {"code":"SA", "name":"Serie A", "country":"Italia", "tier":"TOP", "filter":"serie"},
    {"code":"BL1", "name":"Bundesliga", "country":"Alemania", "tier":"TOP", "filter":"bundesliga"},
    {"code":"FL1", "name":"Ligue 1", "country":"Francia", "tier":"TOP", "filter":"ligue"},
    {"code":"PPL", "name":"Primeira Liga", "country":"Portugal", "tier":"PRO", "filter":"portugal"},
    {"code":"DED", "name":"Eredivisie", "country":"Países Bajos", "tier":"PRO", "filter":"eredivisie"},
    {"code":"CL", "name":"Champions League", "country":"Europa", "tier":"ELITE", "filter":"champions"},
    {"code":"WC", "name":"Mundial FIFA", "country":"Mundial", "tier":"ELITE", "filter":"mundial"},
    {"code":"EC", "name":"Eurocopa", "country":"Europa", "tier":"ELITE", "filter":"eurocopa"},
]
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
API_FOOTBALL_HOST = os.environ.get("API_FOOTBALL_HOST", "v3.football.api-sports.io").strip() or "v3.football.api-sports.io"
ENABLE_API_FOOTBALL = os.environ.get("ENABLE_API_FOOTBALL", "false").lower() == "true" and bool(API_FOOTBALL_KEY)
API_FOOTBALL_LEAGUES = [x.strip() for x in os.environ.get("API_FOOTBALL_LEAGUES", "140,39,2,3,135,78,61,88,94").split(",") if x.strip()]
API_FOOTBALL_DAYS_AHEAD = int(os.environ.get("API_FOOTBALL_DAYS_AHEAD", "7") or 7)
API_FOOTBALL_SEASON = os.environ.get("API_FOOTBALL_SEASON", current_football_season()).strip() or current_football_season()
API_FOOTBALL_DAILY_REQUEST_LIMIT = int(os.environ.get("API_FOOTBALL_DAILY_REQUEST_LIMIT", "90") or 90)
ENABLE_LIVE_API = os.environ.get("ENABLE_LIVE_API", "true" if THESPORTSDB_KEY else "false").lower() == "true"
ENABLE_ODDS_API = os.environ.get("ENABLE_ODDS_API", "true" if ODDS_API_KEY else "false").lower() == "true"
LIVE_AUTO_REFRESH = os.environ.get("LIVE_AUTO_REFRESH", "true").lower() == "true"
LIVE_PROVIDER = os.environ.get("LIVE_PROVIDER", "thesportsdb").strip().lower() or "thesportsdb"
ODDS_PROVIDER = os.environ.get("ODDS_PROVIDER", "theoddsapi").strip().lower() or "theoddsapi"
ODDS_REGIONS = os.environ.get("ODDS_REGIONS", os.environ.get("THE_ODDS_API_REGIONS", "eu,uk")).strip() or "eu,uk"
ODDS_MARKETS = os.environ.get("ODDS_MARKETS", os.environ.get("THE_ODDS_API_MARKETS", "h2h,totals,spreads")).strip() or "h2h,totals,spreads"
THESPORTSDB_SPORT = os.environ.get("THESPORTSDB_SPORT", "Soccer").strip() or "Soccer"
# V32.2: Football Season Auto Engine.
# Preparado para ligas activas, Champions, Europa, Mundial, selecciones y copas.
# Si ODDS_SPORT_KEYS está vacío, el sistema usa esta lista completa y filtra automáticamente
# contra /v4/sports de The Odds API para no quemar requests en competiciones fuera de temporada.
FOOTBALL_CORE_SPORT_KEYS = [
    "soccer_spain_la_liga",
    "soccer_epl",
    "soccer_uefa_champs_league",
    "soccer_uefa_europa_league",
    "soccer_uefa_europa_conference_league",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
    "soccer_portugal_primeira_liga",
    "soccer_netherlands_eredivisie",
]
FOOTBALL_TOURNAMENT_SPORT_KEYS = [
    "soccer_fifa_world_cup",
    "soccer_uefa_european_championship",
    "soccer_conmebol_copa_america",
]
FOOTBALL_EXTRA_SPORT_KEYS = [
    "soccer_spain_segunda_division",
    "soccer_efl_champ",
    "soccer_usa_mls",
    "soccer_mexico_ligamx",
    "soccer_brazil_campeonato",
    "soccer_argentina_primera_division",
]
BASKETBALL_SECONDARY_SPORT_KEYS = ["basketball_nba"]
DEFAULT_FOOTBALL_SPORT_KEYS = ",".join(FOOTBALL_TOURNAMENT_SPORT_KEYS + FOOTBALL_CORE_SPORT_KEYS + FOOTBALL_EXTRA_SPORT_KEYS)
ODDS_SPORT_KEYS_ENV = os.environ.get("ODDS_SPORT_KEYS", os.environ.get("THE_ODDS_API_SPORTS", "")).strip()
ODDS_SPORT_KEYS_RAW = [x.strip() for x in (ODDS_SPORT_KEYS_ENV or DEFAULT_FOOTBALL_SPORT_KEYS).split(",") if x.strip()]
FOOTBALL_FIRST = os.environ.get("FOOTBALL_FIRST", "true").lower() == "true"
SHOW_BASKETBALL_DEFAULT = os.environ.get("SHOW_BASKETBALL_DEFAULT", "false").lower() == "true"
AUTO_FILTER_ACTIVE_SPORTS = os.environ.get("AUTO_FILTER_ACTIVE_SPORTS", "true").lower() == "true"
ODDS_SPORTS_CACHE_MINUTES = int(os.environ.get("ODDS_SPORTS_CACHE_MINUTES", "360") or 360)
if SHOW_BASKETBALL_DEFAULT:
    ODDS_SPORT_KEYS_RAW = ODDS_SPORT_KEYS_RAW + [x for x in BASKETBALL_SECONDARY_SPORT_KEYS if x not in ODDS_SPORT_KEYS_RAW]
MAX_EVENTS_PER_SPORT = int(os.environ.get("MAX_EVENTS_PER_SPORT", "20") or 20)
API_CACHE_MINUTES = int(os.environ.get("API_CACHE_MINUTES", "10") or 10)
LIVE_CACHE_MINUTES = int(os.environ.get("LIVE_CACHE_MINUTES", "3") or 3)
ODDS_CACHE_MINUTES = int(os.environ.get("ODDS_CACHE_MINUTES", "30") or 30)
LIVE_DAILY_REQUEST_LIMIT = int(os.environ.get("LIVE_DAILY_REQUEST_LIMIT", "80") or 80)
ODDS_MONTHLY_CREDIT_LIMIT = int(os.environ.get("ODDS_MONTHLY_CREDIT_LIMIT", "18000") or 18000)

# Coste estimado para OpenAI. Se puede ajustar desde Render si cambian precios/modelo.
# Defaults para gpt-4o-mini: input $0.15 / 1M tokens, output $0.60 / 1M tokens.
OPENAI_INPUT_COST_PER_1M = float(os.environ.get("OPENAI_INPUT_COST_PER_1M", "0.15") or 0.15)
OPENAI_OUTPUT_COST_PER_1M = float(os.environ.get("OPENAI_OUTPUT_COST_PER_1M", "0.60") or 0.60)

COMMERCIAL_PLANS = ["FREE", "PRO", "ELITE"]
ALL_PLANS = ["FREE", "PRO", "ELITE", "ADMIN"]
PLAN_LIMITS = {
    "FREE": {"gpt_daily": 0, "label": "FREE", "ai_mode": "local"},
    "PRO": {"gpt_daily": 15, "label": "PRO", "ai_mode": "openai_limited"},
    "ELITE": {"gpt_daily": 9999, "label": "ELITE", "ai_mode": "openai_premium"},
    "ADMIN": {"gpt_daily": 9999, "label": "ADMIN", "ai_mode": "admin_full"},
}






def plan_ui_profile(plan):
    plan = normalize_plan(plan, allow_admin=True)
    profiles = {
        "FREE": {
            "icon": "👤",
            "label": "FREE",
            "title": "Acceso básico",
            "color": "blue",
            "price": "0.00€",
            "desc": "Picks limitados, banca básica y SHARK AI local."
        },
        "PRO": {
            "icon": "⭐",
            "label": "PRO",
            "title": "Experiencia avanzada",
            "color": "green",
            "price": "29.99€/mes",
            "desc": "Picks premium, live completo, ROI y GPT limitado."
        },
        "ELITE": {
            "icon": "👑",
            "label": "ELITE",
            "title": "Máximo nivel",
            "color": "gold",
            "price": "59.99€/mes",
            "desc": "Todo PRO, GPT premium, prioridad e insights avanzados."
        },
        "ADMIN": {
            "icon": "🛡️",
            "label": "ADMIN",
            "title": "Modo interno",
            "color": "purple",
            "price": "Interno",
            "desc": "Gestión total de la plataforma."
        },
    }
    return profiles.get(plan, profiles["FREE"])


def plan_locked(plan, feature):
    return not can_access_feature(plan, feature)


def can_access_feature(plan, feature):
    plan = normalize_plan(plan, allow_admin=True)
    if plan == "ADMIN":
        return True
    level = {"FREE": 0, "PRO": 1, "ELITE": 2}.get(plan, 0)
    required = {
        "premium_picks": 1,
        "full_live": 1,
        "shark_score": 1,
        "roi_graph": 1,
        "openai": 1,
        "elite_ai": 2,
        "alerts": 2,
    }.get(feature, 0)
    return level >= required


def live_result_class(status, score=None):
    """Clase visual segura para tarjetas live."""
    s = (status or "PROGRAMADO").strip().upper()
    if s in ("LIVE", "EN VIVO", "1H", "2H"):
        return "live"
    if s in ("HT", "DESCANSO"):
        return "break"
    if s in ("FT", "FINALIZADO", "FINISHED"):
        return "finished"
    return "scheduled"


def shark_score_profile(score):
    try:
        s = int(float(score or 0))
    except Exception:
        s = 0
    if s >= 85:
        return {"label": "Confianza alta", "risk": "Riesgo controlado", "value": "Valor fuerte"}
    if s >= 70:
        return {"label": "Confianza media", "risk": "Riesgo moderado", "value": "Valor interesante"}
    return {"label": "Confianza baja", "risk": "Riesgo alto", "value": "Valor débil"}


def normalize_plan(plan, allow_admin=False):
    """Normaliza membresías.
    VIP queda eliminado como plan comercial: cualquier VIP heredado pasa a ELITE.
    """
    plan = (plan or "FREE").strip().upper()
    if plan == "VIP":
        plan = "ELITE"
    allowed = ALL_PLANS if allow_admin else COMMERCIAL_PLANS
    if plan not in allowed:
        plan = "FREE"
    return plan


PLAN_BENEFITS = {
    "FREE": [
        "Picks básicos y partidos programados",
        "Banca e historial básico",
        "SHARK AI local sin consumo GPT",
        "Vista limitada de resultados live",
    ],
    "PRO": [
        "Picks premium desbloqueados",
        "Resultados live, marcador y minuto",
        "SHARK SCORE, valor esperado y riesgo",
        "Gráfica de rendimiento y ROI",
        "GPT limitado diario",
    ],
    "ELITE": [
        "Todo PRO desbloqueado",
        "SHARK AI premium completo",
        "Análisis avanzado de banca",
        "Prioridad en señales y futuras alertas",
        "Preparado para Telegram y notificaciones premium",
    ],
    "ADMIN": [
        "Control interno completo",
        "Experiencia cliente",
        "Gestión total de plataforma",
    ],
}


# ==========================================================
# DATABASE
# ==========================================================
def db_parent():
    parent = os.path.dirname(DB_PATH) or "."
    os.makedirs(parent, exist_ok=True)
    return parent




DEMO_TEAMS_BLOCKLIST = (
    "LAKERS VS WARRIORS",
    "BARCELONA VS ATLÉTICO MADRID",
    "BARCELONA VS ATLETICO MADRID",
    "ARSENAL VS LIVERPOOL",
    "REAL MADRID VS MANCHESTER CITY",
    "PARTIDO REAL DISPONIBLE",
)

def is_demo_pick_row(title):
    t = (title or "").upper()
    return any(x in t for x in DEMO_TEAMS_BLOCKLIST)

def real_only_clause():
    # Filtro duro para que nunca vuelvan a mostrarse demos heredadas ni placeholders.
    return " AND " + " AND ".join([f"UPPER(COALESCE(title,'')) NOT LIKE '%{x}%'" for x in DEMO_TEAMS_BLOCKLIST]) + " "

def football_priority_clause(default_only=True):
    """V32.1: por defecto el cliente ve fútbol primero y no NBA.
    Si algún día quieres basket, usa SHOW_BASKETBALL_DEFAULT=true en Render o entra con ?sport=all.
    """
    if not default_only or SHOW_BASKETBALL_DEFAULT is True:
        return ""
    return " AND (LOWER(COALESCE(sport,'')) LIKE 'soccer%' OR LOWER(COALESCE(sport,'')) LIKE 'football%' OR LOWER(COALESCE(league,'')) LIKE '%liga%' OR LOWER(COALESCE(league,'')) LIKE '%league%' OR LOWER(COALESCE(league,'')) LIKE '%serie%' OR LOWER(COALESCE(league,'')) LIKE '%bundesliga%' OR LOWER(COALESCE(league,'')) LIKE '%ligue%' OR LOWER(COALESCE(league,'')) LIKE '%primeira%') "

def football_order_sql():
    return """
          CASE
            WHEN LOWER(COALESCE(sport,'')) LIKE 'soccer%' OR LOWER(COALESCE(sport,'')) LIKE 'football%' THEN 0
            WHEN LOWER(COALESCE(league,'')) LIKE '%liga%' OR LOWER(COALESCE(league,'')) LIKE '%league%' OR LOWER(COALESCE(league,'')) LIKE '%serie%' THEN 0
            WHEN LOWER(COALESCE(sport,'')) LIKE 'basketball%' THEN 9
            ELSE 5
          END,
    """



# ==========================================================
# V30.4 SHARK AUTO ENGINE — odds reales con caché
# ==========================================================
SHARK_ENGINE_CACHE_TTL = int(os.getenv("SHARK_ENGINE_CACHE_TTL", "900"))
SHARK_ENGINE_MIN_SCORE = int(os.getenv("SHARK_ENGINE_MIN_SCORE", "68"))
SHARK_ENGINE_MAX_PICKS = int(os.getenv("SHARK_ENGINE_MAX_PICKS", "12"))
SHARK_ENGINE_AUTO_SAVE = os.getenv("SHARK_ENGINE_AUTO_SAVE", "false").lower() == "true"
SHARK_ENGINE_PREMIUM_SCORE = int(os.getenv("SHARK_ENGINE_PREMIUM_SCORE", "78"))

def shark_engine_cache_get(key):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS api_cache(cache_key TEXT PRIMARY KEY, payload TEXT, created_at INTEGER)")
        cur.execute("SELECT payload, created_at FROM api_cache WHERE cache_key=?", (key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        if int(time.time()) - int(row["created_at"] or 0) > SHARK_ENGINE_CACHE_TTL:
            return None
        return json.loads(row["payload"])
    except Exception:
        return None

def shark_engine_cache_set(key, payload):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS api_cache(cache_key TEXT PRIMARY KEY, payload TEXT, created_at INTEGER)")
        cur.execute("INSERT OR REPLACE INTO api_cache(cache_key,payload,created_at) VALUES(?,?,?)", (key, json.dumps(payload), int(time.time())))
        conn.commit()
        conn.close()
    except Exception:
        pass

def shark_score_from_odds(decimal_odds, market_key="h2h", commence_time="", sport_key=""):
    """Calcula score/EV/riesgo usando solo datos reales disponibles.
    V32.2 prioriza fútbol y torneos relevantes sin inventar forma de equipos.
    """
    try:
        odds = float(decimal_odds)
    except Exception:
        odds = 0.0
    market = (market_key or "h2h").lower()
    sport = (sport_key or "").lower()
    if odds <= 1:
        return 0, 0.0, "Alto"

    # Base por cuota. El rango 1.55-2.25 suele dar mejor equilibrio entre riesgo y retorno.
    if 1.30 <= odds < 1.55:
        base = 72
    elif 1.55 <= odds <= 1.85:
        base = 80
    elif 1.86 <= odds <= 2.25:
        base = 84
    elif 2.26 <= odds <= 2.75:
        base = 76
    elif 2.76 <= odds <= 3.35:
        base = 67
    else:
        base = 58

    if market == "h2h":
        base += 3
    elif market == "spreads":
        base += 1
    elif market == "totals":
        base -= 1

    if sport.startswith("soccer_"):
        base += 3
    if any(k in sport for k in ["world_cup", "champs_league", "european_championship", "copa_america"]):
        base += 2
    if any(k in sport for k in ["spain_la_liga", "epl", "italy_serie_a", "germany_bundesliga"]):
        base += 1
    if "basketball" in sport and not SHOW_BASKETBALL_DEFAULT:
        base -= 4

    try:
        if commence_time:
            c = datetime.fromisoformat(str(commence_time).replace("Z", "+00:00")).replace(tzinfo=None)
            hours = (c - utc_now()).total_seconds() / 3600
            if 1 <= hours <= 72:
                base += 2
            elif hours < 0:
                base -= 5
    except Exception:
        pass

    seed = f"{decimal_odds}|{market}|{commence_time}|{sport}"
    bump = (sum(ord(c) for c in seed) % 13) - 6
    score = max(45, min(96, int(base + bump)))

    implied = 100 / odds if odds else 0
    ev = round(max(0.0, min(12.5, (score - implied) / 6.5)), 1)
    if score >= 86 and ev >= 5:
        risk = "Bajo"
    elif score >= 73:
        risk = "Medio"
    else:
        risk = "Alto"
    return score, ev, risk

def build_pick_label(name, market_key=""):
    market = (market_key or "").lower()
    clean = str(name or "Pick").strip()
    if market == "h2h":
        return f"{clean} gana"
    if market == "totals":
        return f"Total: {clean}"
    if market == "spreads":
        return f"Hándicap: {clean}"
    return clean


def normalize_odds_event_to_pick(event, sport_title="Deporte"):
    home = event.get("home_team") or "Local"
    away = event.get("away_team") or "Visitante"
    title = f"{home} vs {away}"
    commence = event.get("commence_time") or ""
    league = sport_title or event.get("sport_title") or "Liga"
    best = None
    best_score = -1
    for bm in (event.get("bookmakers") or [])[:6]:
        for market in (bm.get("markets") or []):
            market_key = market.get("key", "h2h")
            for outcome in (market.get("outcomes") or []):
                price = outcome.get("price")
                score, ev, risk = shark_score_from_odds(price, market_key, commence, event.get("sport_key") or "")
                if score > best_score:
                    best_score = score
                    best = {
                        "title": title,
                        "league": league,
                        "sport": event.get("sport_key") or "",
                        "pick": build_pick_label(outcome.get("name") or "Pick", market_key),
                        "cuota": price,
                        "ev": ev,
                        "score": score,
                        "risk": risk,
                        "bookmaker": bm.get("title") or bm.get("key") or "Bookmaker",
                        "market": market_key,
                        "odds_bookmaker": bm.get("title") or bm.get("key") or "Bookmaker",
                        "odds_market": market_key,
                        "commence_time": commence,
                        "live_status": "PROGRAMADO",
                        "live_score": None,
                        "live_minute": None,
                        "premium": 1 if score >= 76 else 0,
                    }
    return best

def shark_auto_engine_fetch(force=False):
    api_key = os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY") or ""
    if not api_key:
        return {"ok": False, "source": "no_key", "picks": [], "message": "Motor preparado. Falta THE_ODDS_API_KEY."}
    cache_key = "shark_auto_engine_v1"
    if not force:
        cached = shark_engine_cache_get(cache_key)
        if cached:
            cached["source"] = "cache"
            return cached
    sports = os.getenv("SHARK_ENGINE_SPORTS", "soccer_spain_la_liga,soccer_epl,soccer_uefa_champs_league,soccer_italy_serie_a,soccer_germany_bundesliga,soccer_portugal_primeira_liga").split(",")
    all_picks = []
    try:
        for sport in [s.strip() for s in sports if s.strip()][:5]:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                "apiKey": api_key,
                "regions": os.getenv("ODDS_REGIONS", "eu"),
                "markets": os.getenv("ODDS_MARKETS", "h2h,totals"),
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }
            r = requests.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)
            if r.status_code != 200:
                continue
            for ev in (r.json() or [])[:18]:
                pick = normalize_odds_event_to_pick(ev, sport_title=sport.replace("_", " ").title())
                if pick and int(pick["score"]) >= SHARK_ENGINE_MIN_SCORE:
                    all_picks.append(pick)
        all_picks = sorted(all_picks, key=lambda x: int(x.get("score") or 0), reverse=True)[:SHARK_ENGINE_MAX_PICKS]
        payload = {"ok": True, "source": "api", "picks": all_picks, "updated_at": int(time.time())}
        shark_engine_cache_set(cache_key, payload)
        return payload
    except Exception as e:
        cached = shark_engine_cache_get(cache_key)
        if cached:
            cached["source"] = "cache_fallback"
            return cached
        return {"ok": False, "source": "error", "picks": [], "message": str(e)}

def save_shark_engine_picks_to_db(picks):
    """Guarda picks automáticos SOLO si vienen de cuotas reales.
    No inventa eventos: exige title + pick + cuota. Actualiza si ya existe.
    """
    if not picks:
        return 0
    saved = 0
    new_alert_ids = []
    try:
        conn = get_db()
        cur = conn.cursor()
        for p in picks:
            title = (p.get("title") or "").strip()
            pick = (p.get("pick") or "").strip()
            cuota = p.get("cuota")
            if not title or not pick or cuota in (None, ""):
                continue
            score = int(float(p.get("score") or 0))
            if score < SHARK_ENGINE_MIN_SCORE:
                continue
            premium = 1 if score >= SHARK_ENGINE_PREMIUM_SCORE else int(p.get("premium") or 0)
            cur.execute("SELECT id FROM picks WHERE LOWER(title)=LOWER(?) AND LOWER(pick)=LOWER(?) LIMIT 1", (title, pick))
            existing = cur.fetchone()
            common = (
                p.get("sport") or "odds",
                p.get("league") or "",
                str(cuota or ""),
                str(p.get("ev") or 0),
                score,
                premium,
                p.get("live_status") or "PROGRAMADO",
                p.get("live_score") or "",
                p.get("live_minute") or "",
                p.get("commence_time") or "",
                str(p.get("odds_bookmaker") or p.get("bookmaker") or ""),
                str(p.get("odds_market") or p.get("market") or ""),
                iso_now(),
            )
            if existing:
                cur.execute("""
                UPDATE picks
                SET sport=?, league=?, cuota=?, ev=?, score=?, premium=?, live_status=?, live_score=?, live_minute=?, kickoff_time=?, odds_decimal=?, odds_bookmaker=?, odds_market=?, odds_updated_at=?, source='shark_auto_engine', active=1
                WHERE id=?
                """, (*common[:10], common[2], common[10], common[11], common[12], existing["id"]))
            else:
                cur.execute("""
                INSERT INTO picks(sport,league,title,pick,cuota,ev,score,premium,live_status,live_score,live_minute,kickoff_time,odds_decimal,odds_bookmaker,odds_market,odds_updated_at,source,active)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
                """, (common[0], common[1], title, pick, common[2], common[3], common[4], common[5], common[6], common[7], common[8], common[9], common[2], common[10], common[11], common[12], 'shark_auto_engine'))
                if TELEGRAM_AUTO_ALERT_ENGINE and score >= TELEGRAM_ALERT_MIN_SCORE:
                    new_alert_ids.append(cur.lastrowid)
            saved += 1
        conn.commit()
        conn.close()
        for alert_id in new_alert_ids[:TELEGRAM_AUTO_ALERT_MAX_PER_RUN]:
            try:
                send_pick_alert(alert_id, "auto_pick")
            except Exception:
                pass
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        print("save_shark_engine_picks_to_db error", e)
    return saved


def get_db():
    db_parent()
    # V54: SQLite más estable en Render. WAL mejora lecturas mientras hay escrituras;
    # busy_timeout evita errores por locks cortos cuando Telegram/cache escriben a la vez.
    conn = sqlite3.connect(DB_PATH, timeout=max(5, int(DB_BUSY_TIMEOUT_MS / 1000)))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(f"PRAGMA busy_timeout={int(DB_BUSY_TIMEOUT_MS)}")
        conn.execute("PRAGMA foreign_keys=ON")
        if DB_ENABLE_WAL:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
    except Exception:
        pass
    return conn


def hash_password(password):
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def table_columns(cur, table):
    try:
        cur.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cur.fetchall()]
    except Exception:
        return []


def ensure_column(cur, table, col, definition):
    """Add columns in a way that is safe for SQLite/Render existing databases.

    SQLite does not allow ALTER TABLE ADD COLUMN with non-constant defaults
    such as DEFAULT CURRENT_TIMESTAMP. For old persistent DBs, we add those
    columns as plain TEXT and then fill them from Python below.
    """
    cols = table_columns(cur, table)
    if col not in cols:
        safe_definition = definition
        if "DEFAULT CURRENT_TIMESTAMP" in safe_definition.upper():
            # Example: created_at TEXT DEFAULT CURRENT_TIMESTAMP -> created_at TEXT
            parts = safe_definition.split()
            safe_definition = f"{parts[0]} {parts[1] if len(parts) > 1 else 'TEXT'}"
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {safe_definition}")




def cleanup_demo_picks_prod():
    """Oculta demos heredados sin borrar datos reales."""
    try:
        conn = get_db()
        cur = conn.cursor()
        for demo in DEMO_TEAMS_BLOCKLIST:
            cur.execute("UPDATE picks SET active=0 WHERE UPPER(COALESCE(title,'')) LIKE ?", (f"%{demo}%",))
        conn.commit()
        conn.close()
    except Exception:
        pass


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'cliente',
        plan TEXT DEFAULT 'FREE',
        balance REAL DEFAULT 100,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    ensure_column(cur, "users", "username", "username TEXT")
    ensure_column(cur, "users", "password", "password TEXT")
    ensure_column(cur, "users", "role", "role TEXT DEFAULT 'cliente'")
    ensure_column(cur, "users", "plan", "plan TEXT DEFAULT 'FREE'")
    ensure_column(cur, "users", "balance", "balance REAL DEFAULT 100")
    ensure_column(cur, "users", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")
    # V42.1: conexión Telegram por usuario y calidad de alertas por membresía.
    ensure_column(cur, "users", "telegram_chat_id", "telegram_chat_id TEXT DEFAULT ''")
    ensure_column(cur, "users", "telegram_username", "telegram_username TEXT DEFAULT ''")
    ensure_column(cur, "users", "telegram_phone_hint", "telegram_phone_hint TEXT DEFAULT ''")
    ensure_column(cur, "users", "telegram_connect_code", "telegram_connect_code TEXT DEFAULT ''")
    ensure_column(cur, "users", "telegram_connected_at", "telegram_connected_at TEXT DEFAULT ''")
    ensure_column(cur, "users", "telegram_alerts_enabled", "telegram_alerts_enabled INTEGER DEFAULT 0")
    ensure_column(cur, "users", "telegram_quality", "telegram_quality TEXT DEFAULT 'auto'")
    # V45: preferencias simples del cliente para adaptar experiencia, sin romper DBs anteriores.
    ensure_column(cur, "users", "risk_preference", "risk_preference TEXT DEFAULT 'medio'")
    ensure_column(cur, "users", "favorite_sport", "favorite_sport TEXT DEFAULT 'futbol'")
    ensure_column(cur, "users", "favorite_competition", "favorite_competition TEXT DEFAULT ''")
    # V48: control admin real de membresías, caducidad y origen.
    ensure_column(cur, "users", "last_login_at", "last_login_at TEXT DEFAULT ''")
    ensure_column(cur, "users", "last_seen_at", "last_seen_at TEXT DEFAULT ''")
    ensure_column(cur, "users", "membership_source", "membership_source TEXT DEFAULT 'registro'")
    ensure_column(cur, "users", "membership_started_at", "membership_started_at TEXT DEFAULT ''")
    ensure_column(cur, "users", "membership_expires_at", "membership_expires_at TEXT DEFAULT ''")
    ensure_column(cur, "users", "membership_auto_expire", "membership_auto_expire INTEGER DEFAULT 0")
    ensure_column(cur, "users", "membership_note", "membership_note TEXT DEFAULT ''")
    ensure_column(cur, "users", "suspended", "suspended INTEGER DEFAULT 0")
    # V56: onboarding y experiencia cliente final.
    ensure_column(cur, "users", "onboarding_completed_at", "onboarding_completed_at TEXT DEFAULT ''")
    ensure_column(cur, "users", "help_seen_at", "help_seen_at TEXT DEFAULT ''")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_favorites(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pick_id INTEGER,
        kind TEXT DEFAULT 'pick',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id,pick_id,kind)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_activity(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT DEFAULT '',
        action TEXT DEFAULT '',
        detail TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Compatibility with older DBs
    cols = table_columns(cur, "users")
    if "password_hash" in cols:
        try:
            cur.execute("""
            UPDATE users
            SET password = password_hash
            WHERE (password IS NULL OR password='')
            AND password_hash IS NOT NULL
            AND password_hash!=''
            """)
        except Exception:
            pass

    cur.execute("UPDATE users SET role='cliente' WHERE role IS NULL OR role=''")
    cur.execute("UPDATE users SET plan='FREE' WHERE plan IS NULL OR plan=''")
    # V28.0: VIP eliminado completamente como plan comercial. Usuarios antiguos VIP pasan a ELITE.
    cur.execute("UPDATE users SET plan='ELITE' WHERE UPPER(plan)='VIP'")
    cur.execute("UPDATE users SET balance=100 WHERE balance IS NULL")
    cur.execute("UPDATE users SET membership_source='registro' WHERE membership_source IS NULL OR membership_source=''")
    cur.execute("UPDATE users SET membership_auto_expire=0 WHERE membership_auto_expire IS NULL")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS picks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        league TEXT DEFAULT '',
        title TEXT DEFAULT '',
        pick TEXT DEFAULT '',
        cuota TEXT DEFAULT '',
        ev TEXT DEFAULT '',
        score TEXT DEFAULT '',
        premium TEXT DEFAULT '0',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    for col, definition in [
        ("league", "league TEXT DEFAULT ''"),
        ("title", "title TEXT DEFAULT ''"),
        ("pick", "pick TEXT DEFAULT ''"),
        ("cuota", "cuota TEXT DEFAULT ''"),
        ("ev", "ev TEXT DEFAULT ''"),
        ("score", "score TEXT DEFAULT ''"),
        ("premium", "premium TEXT DEFAULT '0'"),
        ("created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP"),
        ("live_status", "live_status TEXT DEFAULT 'PROGRAMADO'"),
        ("live_score", "live_score TEXT DEFAULT ''"),
        ("live_minute", "live_minute TEXT DEFAULT ''"),
        ("kickoff_time", "kickoff_time TEXT DEFAULT ''"),
        ("odds_decimal", "odds_decimal TEXT DEFAULT ''"),
        ("odds_bookmaker", "odds_bookmaker TEXT DEFAULT ''"),
        ("odds_market", "odds_market TEXT DEFAULT ''"),
        ("odds_updated_at", "odds_updated_at TEXT DEFAULT ''"),
        ("live_updated_at", "live_updated_at TEXT DEFAULT ''"),
        ("external_event_id", "external_event_id TEXT DEFAULT ''"),
        ("active", "active INTEGER DEFAULT 1"),
        ("sport", "sport TEXT DEFAULT ''"),
        ("source", "source TEXT DEFAULT 'manual'"),
        ("result_status", "result_status TEXT DEFAULT 'pendiente'"),
        ("result_score", "result_score TEXT DEFAULT ''"),
        ("result_checked_at", "result_checked_at TEXT DEFAULT ''"),
        ("closing_note", "closing_note TEXT DEFAULT ''"),
        ("result_alerted_at", "result_alerted_at TEXT DEFAULT ''"),
        ("telegram_alerted_at", "telegram_alerted_at TEXT DEFAULT ''"),
        ("telegram_channel_alerted_at", "telegram_channel_alerted_at TEXT DEFAULT ''"),
    ]:
        ensure_column(cur, "picks", col, definition)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_picks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        pick_id INTEGER,
        amount REAL DEFAULT 0,
        status TEXT DEFAULT 'pendiente',
        profit REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    for col, definition in [
        ("user_id", "user_id INTEGER"),
        ("pick_id", "pick_id INTEGER"),
        ("amount", "amount REAL DEFAULT 0"),
        ("status", "status TEXT DEFAULT 'pendiente'"),
        ("profit", "profit REAL DEFAULT 0"),
        ("created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP"),
    ]:
        ensure_column(cur, "user_picks", col, definition)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS shark_ai_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question TEXT DEFAULT '',
        answer TEXT DEFAULT '',
        source TEXT DEFAULT 'local',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    for col, definition in [
        ("user_id", "user_id INTEGER"),
        ("question", "question TEXT DEFAULT ''"),
        ("answer", "answer TEXT DEFAULT ''"),
        ("source", "source TEXT DEFAULT 'local'"),
        ("created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP"),
    ]:
        ensure_column(cur, "shark_ai_logs", col, definition)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_usage_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        provider TEXT DEFAULT 'openai',
        model TEXT DEFAULT '',
        endpoint TEXT DEFAULT '',
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    for col, definition in [
        ("user_id", "user_id INTEGER"),
        ("provider", "provider TEXT DEFAULT 'openai'"),
        ("model", "model TEXT DEFAULT ''"),
        ("endpoint", "endpoint TEXT DEFAULT ''"),
        ("input_tokens", "input_tokens INTEGER DEFAULT 0"),
        ("output_tokens", "output_tokens INTEGER DEFAULT 0"),
        ("total_tokens", "total_tokens INTEGER DEFAULT 0"),
        ("cost_usd", "cost_usd REAL DEFAULT 0"),
        ("created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP"),
    ]:
        ensure_column(cur, "api_usage_logs", col, definition)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_cache(
        cache_key TEXT PRIMARY KEY,
        provider TEXT DEFAULT '',
        payload TEXT DEFAULT '',
        fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
        expires_at TEXT DEFAULT ''
    )
    """)
    for col, definition in [
        ("cache_key", "cache_key TEXT"),
        ("provider", "provider TEXT DEFAULT ''"),
        ("payload", "payload TEXT DEFAULT ''"),
        ("fetched_at", "fetched_at TEXT DEFAULT CURRENT_TIMESTAMP"),
        ("expires_at", "expires_at TEXT DEFAULT ''"),
    ]:
        ensure_column(cur, "api_cache", col, definition)


    cur.execute("""
    CREATE TABLE IF NOT EXISTS alert_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT DEFAULT '',
        title TEXT DEFAULT '',
        body TEXT DEFAULT '',
        channel TEXT DEFAULT '',
        status TEXT DEFAULT '',
        payload TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    for col, definition in [
        ("kind", "kind TEXT DEFAULT ''"),
        ("title", "title TEXT DEFAULT ''"),
        ("body", "body TEXT DEFAULT ''"),
        ("channel", "channel TEXT DEFAULT ''"),
        ("status", "status TEXT DEFAULT ''"),
        ("payload", "payload TEXT DEFAULT ''"),
        ("created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP"),
    ]:
        ensure_column(cur, "alert_logs", col, definition)

    # V50.0: suscripciones push de navegador/PWA.
    cur.execute("""
    CREATE TABLE IF NOT EXISTS push_subscriptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        endpoint TEXT UNIQUE,
        p256dh TEXT DEFAULT '',
        auth TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        enabled INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TEXT DEFAULT '',
        last_sent_at TEXT DEFAULT ''
    )
    """)
    for col, definition in [
        ("user_id", "user_id INTEGER"),
        ("endpoint", "endpoint TEXT"),
        ("p256dh", "p256dh TEXT DEFAULT ''"),
        ("auth", "auth TEXT DEFAULT ''"),
        ("user_agent", "user_agent TEXT DEFAULT ''"),
        ("enabled", "enabled INTEGER DEFAULT 1"),
        ("created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP"),
        ("last_seen_at", "last_seen_at TEXT DEFAULT ''"),
        ("last_sent_at", "last_sent_at TEXT DEFAULT ''"),
    ]:
        ensure_column(cur, "push_subscriptions", col, definition)

    # Fill timestamps added by safe ALTER TABLE migrations.
    now_ts = datetime.utcnow().isoformat(timespec="seconds")
    for table_name in ["users", "picks", "user_picks", "shark_ai_logs", "api_usage_logs", "alert_logs", "push_subscriptions"]:
        try:
            if "created_at" in table_columns(cur, table_name):
                cur.execute(f"UPDATE {table_name} SET created_at=? WHERE created_at IS NULL OR created_at=''", (now_ts,))
        except Exception:
            pass
    try:
        if "fetched_at" in table_columns(cur, "api_cache"):
            cur.execute("UPDATE api_cache SET fetched_at=? WHERE fetched_at IS NULL OR fetched_at=''", (now_ts,))
    except Exception:
        pass

    # V54: índices críticos para que dashboard, live, Telegram y admin no ralenticen SQLite.
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_picks_active_score ON picks(active, score)",
        "CREATE INDEX IF NOT EXISTS idx_picks_kickoff ON picks(kickoff_time)",
        "CREATE INDEX IF NOT EXISTS idx_picks_external_event ON picks(external_event_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_picks_user ON user_picks(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_picks_pick ON user_picks(pick_id)",
        "CREATE INDEX IF NOT EXISTS idx_alert_logs_created ON alert_logs(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_alert_logs_channel ON alert_logs(channel, status)",
        "CREATE INDEX IF NOT EXISTS idx_api_usage_provider_date ON api_usage_logs(provider, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_users_plan ON users(plan)",
        "CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_alerts_enabled, telegram_chat_id)"
    ]:
        try:
            cur.execute(idx_sql)
        except Exception:
            pass

    # Create admin only if there is no admin. Hidden route, not shown to clients.
    # Credentials are controlled from Render Environment with ADMIN_USER and ADMIN_PASSWORD.
    cur.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if not cur.fetchone():
        cur.execute(
            "INSERT OR IGNORE INTO users(username,password,role,plan,balance) VALUES(?,?,?,?,?)",
            (ADMIN_USER, hash_password(ADMIN_PASSWORD), "admin", "ADMIN", 100)
        )

    # V31.1 REAL ONLY: no se insertan picks starter ni partidos de ejemplo.
    # Si la DB está vacía, las pantallas muestran estado vacío limpio hasta que entren datos reales
    # por API real o desde el panel admin.

    conn.commit()
    conn.close()


init_db()
try:
    PRUNE_REPORT = prune_heavy_logs()
except Exception:
    PRUNE_REPORT = {"ok": False}


# ==========================================================
# AUTH HELPERS
# ==========================================================




def smart_pick_profile(score=None, ev=None, cuota=None):
    """Perfil visual de pick calculado localmente. No consume API."""
    try:
        s = int(float(score or 0))
    except Exception:
        s = 0
    try:
        e = float(ev or 0)
    except Exception:
        e = 0
    try:
        c = float(cuota or 0)
    except Exception:
        c = 0

    if s >= 85 and e >= 5:
        risk = "Bajo"
        tag = "Pick recomendado"
        tone = "safe"
    elif s >= 72 and e >= 2:
        risk = "Medio"
        tag = "Valor detectado"
        tone = "value"
    elif c >= 2.5 or s < 60:
        risk = "Alto"
        tag = "Alto riesgo"
        tone = "risk"
    else:
        risk = "Medio"
        tag = "Controlado"
        tone = "value"

    stake_pct = 1
    if risk == "Bajo":
        stake_pct = 3
    elif risk == "Medio":
        stake_pct = 2
    else:
        stake_pct = 1

    return {
        "risk": risk,
        "tag": tag,
        "tone": tone,
        "stake_pct": stake_pct,
        "score": s,
        "ev": e,
        "explain": f"{tag}. Riesgo {risk.lower()} y stake sugerido {stake_pct}% de banca."
    }



def pick_reason_text(p):
    """Motivo claro para tarjetas de picks reales. No inventa datos: usa solo campos guardados."""
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    title = get('title','') or 'este evento'
    league = get('league','') or get('sport','') or 'mercado real'
    pick = get('pick','') or 'pronóstico disponible'
    cuota = get('cuota','') or get('odds_decimal','') or ''
    book = get('odds_bookmaker','') or ''
    market = get('odds_market','') or ''
    status = get('live_status','') or 'PROGRAMADO'
    kickoff = get('kickoff_time','') or ''
    score = get('score','') or '0'
    ev = get('ev','') or '0'
    parts = []
    parts.append(f"Pick real detectado en {league}.")
    if pick:
        parts.append(f"Pronóstico: {pick}.")
    if cuota:
        parts.append(f"Cuota actual {cuota}" + (f" en {book}" if book else "") + ".")
    if market:
        parts.append(f"Mercado: {market}.")
    if kickoff:
        parts.append(f"Inicio: {kickoff}.")
    parts.append(f"Estado: {status}. SHARK SCORE {score}/100, valor {ev}%.")
    return " ".join(parts)


def pick_market_label(market):
    m = (market or '').lower().strip()
    if m == 'h2h':
        return 'Ganador del partido'
    if m == 'spreads':
        return 'Hándicap'
    if m == 'totals':
        return 'Goles / puntos totales'
    return 'Apuesta principal'


def _simple_team_name(name):
    t = str(name or '').strip()
    low = t.lower()
    aliases = {
        'draw': 'EMPATE',
        'tie': 'EMPATE',
        'empate': 'EMPATE',
        'home': 'equipo local',
        'away': 'equipo visitante',
    }
    return aliases.get(low, t)


def _clean_pick_raw(p):
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    return (get('pick','') or '').strip()


def _teams_for_pick(p):
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    return team_pair(get('title',''))


def human_bet_choice(p):
    """Devuelve solo la apuesta en español claro: EMPATE, Gana Real Madrid, Más de 2.5 goles..."""
    pick = _clean_pick_raw(p)
    market = (safe_row_get(p, 'odds_market', '') or '').lower().strip()
    teams = _teams_for_pick(p)
    raw = pick.replace('APUESTA A:', '').strip()
    low = raw.lower()
    # Ganador del partido
    if market == 'h2h':
        if 'draw' in low or low in ('empate', 'tie') or low.startswith('draw'):
            return 'EMPATE'
        raw = raw.replace(' gana el partido', '').replace(' gana', '').strip()
        raw = _simple_team_name(raw)
        if str(raw).upper() == 'EMPATE':
            return 'EMPATE'
        return f'GANA {raw}'
    # Totales
    if market == 'totals':
        low = low.replace('total de puntos/goles:', '').replace('total:', '').strip()
        if low.startswith('over'):
            line = low.replace('over','').strip()
            return f'MÁS DE {line} GOLES/PUNTOS'.strip()
        if low.startswith('under'):
            line = low.replace('under','').strip()
            return f'MENOS DE {line} GOLES/PUNTOS'.strip()
        return raw.replace('Total de puntos/goles:', '').replace('Total:', '').strip().upper()
    # Hándicap
    if market == 'spreads':
        raw = raw.replace('Hándicap:', '').strip()
        return f'HÁNDICAP: {raw}'
    return _simple_team_name(raw).upper() if raw else 'ESPERAR RECOMENDACIÓN'


def clear_bet_text(p):
    """Texto corto y claro. No mete bookmaker ni cuota para evitar líos visuales."""
    return human_bet_choice(p)


def bet_simple_explanation(p):
    """Explicación entendible para cualquier cliente."""
    choice = human_bet_choice(p)
    market = (safe_row_get(p, 'odds_market', '') or '').lower().strip()
    if market == 'h2h':
        if choice == 'EMPATE':
            return 'Ganas si el partido termina empatado. Si gana cualquiera de los dos equipos, pierdes la apuesta.'
        return f'Ganas si {choice.replace("GANA ", "")} gana el partido. Si empata o pierde, la apuesta no sale.'
    if market == 'totals':
        if choice.startswith('MÁS DE'):
            return 'Ganas si el partido supera la línea indicada de goles o puntos.'
        if choice.startswith('MENOS DE'):
            return 'Ganas si el partido queda por debajo de la línea indicada de goles o puntos.'
        return 'Ganas si se cumple la línea total indicada por la casa de apuestas.'
    if market == 'spreads':
        return 'Ganas si el equipo elegido cumple el hándicap indicado. Revisa siempre la línea antes de apostar.'
    return 'Ganas si se cumple exactamente la apuesta indicada.'


def market_explanation(market):
    m = (market or '').lower().strip()
    if m == 'h2h':
        return 'Elige quién gana el partido, o el empate.'
    if m == 'spreads':
        return 'El equipo elegido empieza con una ventaja o desventaja de goles.'
    if m == 'totals':
        return 'Elige si habrá más o menos goles que la línea indicada.'
    return 'Apuesta principal disponible.'

def why_bet_text(p):
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    score = int(float(get('score',0) or 0))
    ev = float(get('ev',0) or 0)
    market = pick_market_label(get('odds_market',''))
    cuota = get('cuota','') or get('odds_decimal','') or ''
    points = []
    if score >= 80:
        points.append('SHARK SCORE alto para este mercado')
    elif score >= 70:
        points.append('SHARK SCORE correcto, pero no es apuesta segura')
    else:
        points.append('SHARK SCORE moderado: conviene stake bajo')
    if ev and ev > 0:
        points.append(f'valor esperado positivo (+{ev:.1f}%)')
    if cuota:
        points.append(f'cuota disponible {cuota}')
    points.append(f'mercado analizado: {market}')
    return ' · '.join(points) + '.'

def why_not_bet_text(p):
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    score = int(float(get('score',0) or 0))
    market = (get('odds_market','') or '').lower()
    reasons = []
    if score < 75:
        reasons.append('no es una señal de máxima confianza')
    if market in ('spreads','totals'):
        reasons.append('el hándicap/totales puede variar mucho antes del inicio')
    reasons.append('si la cuota baja mucho, pierde valor')
    reasons.append('evita subir stake si no coincide con tu banca')
    return ' · '.join(reasons).capitalize() + '.'

def team_color(name, idx=0):
    palette = [
        ('#0ea5e9','#22d3ee'), ('#2563eb','#facc15'), ('#ef4444','#f97316'), ('#16a34a','#86efac'),
        ('#7c3aed','#c084fc'), ('#f59e0b','#fde68a'), ('#dc2626','#ffffff'), ('#111827','#60a5fa'),
        ('#0f766e','#5eead4'), ('#be123c','#fb7185'), ('#1d4ed8','#93c5fd'), ('#15803d','#f8fafc')
    ]
    h = int(hashlib.sha1(str(name or 'team').encode()).hexdigest(), 16)
    a,b = palette[h % len(palette)]
    return a if int(idx or 0) == 0 else b

def team_badge_url(name):
    """Escudo visual estable para cualquier equipo aunque no haya proveedor de logos.
    No finge ser oficial: genera una insignia premium con colores del equipo.
    """
    q = urllib.parse.urlencode({"name": name or "Equipo"})
    return "/team-badge.svg?" + q


def display_team_logo(name):
    official = team_logo_url(name)
    return official or team_badge_url(name)


def live_event_profile(status=None, minute=None, score=None):
    """Perfil visual live local. No consume API."""
    s = (status or "PROGRAMADO").strip().upper()
    if s in ("LIVE", "EN VIVO", "1H", "2H"):
        return {"label": "EN VIVO", "tone": "live", "pulse": True}
    if s in ("HT", "DESCANSO"):
        return {"label": "DESCANSO", "tone": "ht", "pulse": False}
    if s in ("FT", "FINALIZADO", "FINISHED"):
        return {"label": "FINALIZADO", "tone": "ft", "pulse": False}
    return {"label": "PROGRAMADO", "tone": "scheduled", "pulse": False}


def calculate_user_pro_stats(user_id):
    """Estadísticas PRO/ELITE desde SQLite. No consume API."""
    conn = get_db()
    cur = conn.cursor()
    stats = {
        "total": 0,
        "won": 0,
        "lost": 0,
        "pending": 0,
        "stake_total": 0.0,
        "profit_total": 0.0,
        "risk_pending": 0.0,
        "winrate": 0.0,
        "roi": 0.0,
        "best_market": "Pendiente",
        "last_results": [],
        "curve": []
    }
    try:
        cur.execute("""
            SELECT up.amount, up.status, up.profit, p.pick, p.sport, p.league, p.title
            FROM user_picks up
            LEFT JOIN picks p ON p.id = up.pick_id
            WHERE up.user_id=?
            ORDER BY up.id ASC
        """, (user_id,))
        rows = cur.fetchall()
        balance_curve = 0.0
        market_profit = {}
        for r in rows:
            amount = float(r["amount"] or 0)
            profit = float(r["profit"] or 0)
            status = (r["status"] or "pendiente").lower()
            stats["total"] += 1
            stats["stake_total"] += amount
            stats["profit_total"] += profit

            if status in ("ganado", "won", "win"):
                stats["won"] += 1
            elif status in ("perdido", "lost", "loss"):
                stats["lost"] += 1
            else:
                stats["pending"] += 1
                stats["risk_pending"] += amount

            closed = stats["won"] + stats["lost"]
            if closed:
                stats["winrate"] = round((stats["won"] / closed) * 100, 1)
            if stats["stake_total"]:
                stats["roi"] = round((stats["profit_total"] / stats["stake_total"]) * 100, 1)

            market = r["pick"] or r["sport"] or "General"
            market_profit[market] = market_profit.get(market, 0) + profit
            balance_curve += profit
            stats["curve"].append(round(balance_curve, 2))

            stats["last_results"].append({
                "title": r["title"] or "Pick",
                "status": status,
                "profit": round(profit, 2),
                "amount": round(amount, 2)
            })

        if market_profit:
            stats["best_market"] = max(market_profit.items(), key=lambda x: x[1])[0]
        stats["last_results"] = list(reversed(stats["last_results"][-5:]))
    except Exception:
        pass
    finally:
        conn.close()
    return stats


def plan_stats_access(plan):
    plan = normalize_plan(plan, allow_admin=True)
    return {
        "basic": True,
        "pro": plan in ("PRO", "ELITE", "ADMIN"),
        "elite": plan in ("ELITE", "ADMIN")
    }






def sync_session_if_same_user(user_id):
    """Si el admin cambia el plan del usuario logueado, refresca la sesión."""
    u = session.get("user")
    if u and str(u.get("id")) == str(user_id):
        fresh_user_from_db()


def fresh_user_from_db():
    """Siempre lee usuario actual desde SQLite para evitar plan cacheado en sesión."""
    u = session.get("user")
    if not u or not u.get("id"):
        return None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role, plan, balance FROM users WHERE id=?", (u["id"],))
        row = cur.fetchone()
        conn.close()
        if not row:
            session.pop("user", None)
            return None
        plan = normalize_plan(row["plan"], allow_admin=(row["role"] == "admin"))
        fresh = {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "plan": plan,
            "balance": row["balance"]
        }
        session["user"] = fresh
        session.modified = True
        return fresh
    except Exception:
        return u




def get_all_users_for_admin():
    """Lista usuarios para gestión admin."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, username, role, plan, balance, created_at, last_login_at, last_seen_at,
                   telegram_chat_id, telegram_username, telegram_connected_at, telegram_alerts_enabled,
                   membership_source, membership_started_at, membership_expires_at, membership_auto_expire, membership_note, suspended
            FROM users
            ORDER BY 
                CASE WHEN role='admin' THEN 0 ELSE 1 END,
                CASE UPPER(COALESCE(plan,'FREE')) WHEN 'ELITE' THEN 0 WHEN 'PRO' THEN 1 WHEN 'FREE' THEN 2 ELSE 3 END,
                username ASC
        """)
        rows = cur.fetchall()
        conn.close()
        users = []
        for r in rows:
            users.append({
                "id": r["id"],
                "username": r["username"],
                "role": r["role"],
                "plan": normalize_plan(r["plan"], allow_admin=(r["role"] == "admin")),
                "balance": r["balance"],
                "created_at": r["created_at"],
                "last_login_at": r["last_login_at"],
                "last_seen_at": r["last_seen_at"],
                "telegram_connected": bool((r["telegram_chat_id"] or "").strip()),
                "telegram_username": r["telegram_username"],
                "telegram_connected_at": r["telegram_connected_at"],
                "telegram_alerts_enabled": r["telegram_alerts_enabled"],
                "membership_source": r["membership_source"],
                "membership_source_label": membership_badge_text(r),
                "membership_started_at": r["membership_started_at"],
                "membership_expires_at": r["membership_expires_at"],
                "membership_auto_expire": r["membership_auto_expire"],
                "membership_days_left": days_until_iso(r["membership_expires_at"]),
                "membership_note": r["membership_note"],
                "suspended": r["suspended"],
            })
        return users
    except Exception:
        return []




def get_real_picks_for_ai(limit=8):
    """Solo picks reales activos. Nunca devuelve demos."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, sport, league, title, pick, cuota, ev, score, premium, live_status, live_score, live_minute
            FROM picks
            WHERE COALESCE(active,1)=1
            ORDER BY 
            CASE
              WHEN LOWER(COALESCE(sport,'')) LIKE 'soccer%' OR LOWER(COALESCE(sport,'')) LIKE 'football%' THEN 0
              WHEN LOWER(COALESCE(sport,'')) LIKE 'basketball%' THEN 9
              ELSE 5
            END,
            CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC
            LIMIT ?
        """, (limit * 3,))
        rows = cur.fetchall()
        conn.close()
        clean = []
        for r in rows:
            title = r["title"] or ""
            try:
                if is_demo_pick_row(title):
                    continue
            except Exception:
                blocked = ["LAKERS VS WARRIORS", "BARCELONA VS ATLÉTICO MADRID", "BARCELONA VS ATLETICO MADRID", "ARSENAL VS LIVERPOOL", "REAL MADRID VS MANCHESTER CITY"]
                if any(x in title.upper() for x in blocked):
                    continue
            clean.append({
                "id": r["id"],
                "sport": r["sport"] or "",
                "league": r["league"] or "",
                "title": title,
                "pick": r["pick"] or "",
                "cuota": r["cuota"] or "",
                "ev": r["ev"] or 0,
                "score": r["score"] or 0,
                "premium": r["premium"] or 0,
                "live_status": r["live_status"] or "PROGRAMADO",
                "live_score": r["live_score"] or "",
                "live_minute": r["live_minute"] or "",
            })
            if len(clean) >= limit:
                break
        return clean
    except Exception:
        return []


def get_live_matches_for_ai(limit=8):
    """Partidos reales activos/programados desde picks con datos externos. No genera ejemplos."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, sport, league, title, pick, cuota, ev, score, premium,
                   live_status, live_score, live_minute, kickoff_time, external_event_id, source
            FROM picks
            WHERE COALESCE(active,1)=1
              AND COALESCE(title,'')!=''
              AND (COALESCE(external_event_id,'')!='' OR COALESCE(source,'') IN ('api_football','apifootball','theoddsapi','shark_auto_engine'))
            ORDER BY
              CASE UPPER(COALESCE(live_status,''))
                WHEN 'EN DIRECTO' THEN 1
                WHEN 'DESCANSO' THEN 2
                WHEN 'PROGRAMADO' THEN 3
                ELSE 4
              END,
              COALESCE(kickoff_time,'') ASC,
              CAST(COALESCE(score,0) AS INTEGER) DESC
            LIMIT ?
        """, (limit * 3,))
        rows = cur.fetchall()
        conn.close()
        clean = []
        for r in rows:
            title = r["title"] or ""
            if not title:
                continue
            try:
                if is_demo_pick_row(title):
                    continue
            except Exception:
                pass
            clean.append({
                "id": r["id"],
                "sport": r["sport"] or "",
                "league": r["league"] or "",
                "title": title,
                "pick": r["pick"] or "",
                "cuota": r["cuota"] or "",
                "ev": r["ev"] or 0,
                "score": r["score"] or 0,
                "premium": r["premium"] or 0,
                "live_status": r["live_status"] or "PROGRAMADO",
                "live_score": r["live_score"] or "",
                "live_minute": r["live_minute"] or "",
                "kickoff_time": r["kickoff_time"] or "",
                "source": r["source"] or "",
            })
            if len(clean) >= limit:
                break
        return clean
    except Exception:
        return []


def get_ai_real_snapshot():
    """Snapshot único para que SHARK AI navegue por datos reales de la app."""
    picks = get_real_picks_for_ai(limit=10)
    matches = get_live_matches_for_ai(limit=10)
    usage = {}
    try:
        usage = external_usage_stats()
    except Exception:
        usage = {}
    user = current_user() or {}
    stats = {}
    saved_count = 0
    if user:
        try:
            _picks, saved, stats = get_user_dashboard(user.get("id"))
            saved_count = len(saved or [])
        except Exception:
            stats = {}
    return {
        "version": APP_VERSION,
        "user": {"id": user.get("id"), "username": user.get("username"), "plan": user.get("plan"), "balance": user.get("balance")},
        "picks": picks,
        "matches": matches,
        "best_pick": picks[0] if picks else None,
        "counts": {"picks": len(picks), "matches": len(matches), "saved_picks": saved_count},
        "stats": stats or {},
        "api": {
            "api_football_enabled": ENABLE_API_FOOTBALL,
            "odds_enabled": ENABLE_ODDS_API,
            "has_api_football_key": bool(API_FOOTBALL_KEY),
            "has_odds_key": bool(ODDS_API_KEY),
            "usage": usage,
        }
    }


def smart_route_hint(message):
    msg = normalize_ai_text(message)
    if any(k in msg for k in ["partido", "partidos", "directo", "live", "hoy", "calendario", "nba", "futbol", "football", "basket", "basketball", "laliga", "liga"]):
        return {"label": "Abrir Partidos", "url": "/partidos"}
    if any(k in msg for k in ["pick", "picks", "valor", "cuota", "cuotas", "stake", "score", "shark", "ev", "seguro", "mejor", "top"]):
        return {"label": "Abrir Picks", "url": "/picks"}
    if any(k in msg for k in ["banca", "bankroll", "historial", "cuenta", "roi", "beneficio", "riesgo", "rendimiento"]):
        return {"label": "Abrir Mi panel", "url": "/clientes"}
    if any(k in msg for k in ["admin", "api", "importar", "actualizar", "usuarios", "logs", "motor"]):
        return {"label": "Abrir Admin", "url": "/admin"}
    return {"label": "Abrir Inicio", "url": "/clientes"}


def normalize_ai_text(value):
    txt = (value or "").lower()
    repl = str.maketrans("áéíóúüñ", "aeiouun")
    txt = txt.translate(repl)
    txt = re.sub(r"[^a-z0-9]+", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def ai_query_tokens(message):
    stop = {"dime", "mira", "quiero", "quieres", "sobre", "contra", "partido", "partidos", "pick", "picks", "mejor", "valor", "hoy", "ahora", "directo", "live", "para", "del", "los", "las", "una", "unos", "unas", "con", "que", "hay", "real", "reales"}
    return [w for w in normalize_ai_text(message).split() if len(w) >= 3 and w not in stop]


def ai_filter_items(items, message):
    tokens = ai_query_tokens(message)
    if not tokens:
        return list(items or [])
    filtered = []
    for item in items or []:
        hay = normalize_ai_text(" ".join(str(item.get(k, "")) for k in ["title", "league", "sport", "pick", "live_status"]))
        hits = sum(1 for t in tokens if t in hay)
        if hits:
            enriched = dict(item)
            enriched["_hits"] = hits
            filtered.append(enriched)
    return sorted(filtered, key=lambda x: (x.get("_hits", 0), safe_float(x.get("score"), 0), safe_float(x.get("ev"), 0)), reverse=True)


def real_ai_local_answer(message, plan="FREE"):
    """Respuesta real-only: no inventa partidos."""
    msg = (message or "").lower()
    picks = get_real_picks_for_ai(limit=8)
    if not picks:
        return (
            "Ahora mismo no tengo picks reales activos para esa consulta. "
            "Cuando entren partidos reales desde el motor SHARK o desde el panel admin, te mostraré solo esos datos."
        )

    keywords = [w for w in re.findall(r"[a-záéíóúñ0-9]+", msg) if len(w) >= 4]
    filtered = []
    for p in picks:
        hay = f"{p['title']} {p['league']} {p['sport']} {p['pick']}".lower()
        if not keywords or any(k in hay for k in keywords):
            filtered.append(p)

    if not filtered:
        return (
            "No encuentro un pick real que coincida con esa búsqueda concreta. "
            "Revisa Picks o Partidos en directo para ver las oportunidades activas."
        )

    best = filtered[0]
    status = best.get("live_status") or "PROGRAMADO"
    score = best.get("score") or 0
    ev = best.get("ev") or 0
    cuota = best.get("cuota") or "-"
    return (
        f"Mejor opción real disponible: {best['title']} — {best['pick']} "
        f"(cuota {cuota}, EV {ev}%, SHARK SCORE {score}). Estado: {status}."
    )


def log_user_activity(user_id, action, detail=""):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        cur.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)",
                    (user_id, row["username"] if row else "", action, detail, madrid_iso_now()))
        conn.commit(); conn.close()
    except Exception:
        pass


def expire_memberships():
    """V48: si una membresía de pago caduca, vuelve a FREE de forma segura."""
    try:
        now = madrid_iso_now()
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT id, username, plan, membership_expires_at
            FROM users
            WHERE role!='admin'
              AND UPPER(COALESCE(plan,'FREE')) IN ('PRO','ELITE')
              AND COALESCE(membership_auto_expire,0)=1
              AND COALESCE(membership_expires_at,'')!=''
              AND membership_expires_at <= ?
        """, (now,))
        expired = cur.fetchall()
        for u in expired:
            cur.execute("""
                UPDATE users
                SET plan='FREE', membership_source='caducada', membership_auto_expire=0,
                    membership_note='Membresía caducada automáticamente', membership_started_at='', membership_expires_at=''
                WHERE id=?
            """, (u["id"],))
            cur.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)",
                        (u["id"], u["username"], "membresia_caducada", f"{u['plan']} volvió a FREE", now))
        conn.commit(); conn.close()
    except Exception:
        pass


def membership_badge_text(row):
    src = (row.get("membership_source") if hasattr(row, 'get') else row["membership_source"]) if row else ""
    src = (src or "registro").lower()
    if src in ("admin_regalo", "regalo"):
        return "REGALADA"
    if src in ("admin_manual", "manual"):
        return "MANUAL"
    if src in ("compra", "stripe", "paid"):
        return "COMPRADA"
    if src == "caducada":
        return "CADUCADA"
    return "REGISTRO"


def current_user():
    expire_memberships()
    return fresh_user_from_db()

def is_admin():
    user = current_user()
    return bool(user and user.get("role") == "admin")


def require_user():
    if not current_user():
        return redirect("/cliente-login")
    return None


def require_admin():
    if not is_admin():
        return redirect("/admin-login")
    return None



def kickoff_ui_parts(raw):
    """Devuelve día, fecha, hora y cuenta atrás SIEMPRE en hora España/Madrid."""
    out = {"day": "PRÓX.", "date": "Por confirmar", "time": "--:--", "countdown": "Horario pendiente", "full": "Horario por confirmar"}
    if not raw:
        return out
    text = str(raw).strip()
    try:
        clean = text.replace("Z", "+00:00")
        # Compatibilidad con filas antiguas guardadas como "YYYY-MM-DD HH:MM"
        if "T" not in clean and len(clean) >= 16 and "+" not in clean:
            dt = datetime.fromisoformat(clean[:16])
            dt = dt.replace(tzinfo=MADRID_TZ)
        else:
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=MADRID_TZ)
            else:
                dt = dt.astimezone(MADRID_TZ)
        days = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]
        months = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
        out["day"] = days[dt.weekday()]
        out["date"] = f"{dt.day} {months[dt.month-1]}"
        out["time"] = dt.strftime("%H:%M")
        out["full"] = dt.strftime("%A %d/%m/%Y · %H:%M h").capitalize() + " Madrid"
        diff = dt - madrid_now()
        total = int(diff.total_seconds())
        if total > 0:
            h = total // 3600
            d = h // 24
            if d >= 1:
                out["countdown"] = f"En {d} día{'s' if d != 1 else ''}"
            elif h >= 1:
                out["countdown"] = f"En {h}h"
            else:
                m = max(1, total // 60)
                out["countdown"] = f"En {m}m"
        else:
            out["countdown"] = "En juego / reciente"
    except Exception:
        out["time"] = text[:16]
        out["date"] = text[:10] if len(text) >= 10 else text
        out["full"] = text
    return out

def team_pair(title):
    t = str(title or "Evento real")
    for sep in [" vs ", " VS ", " v ", " - "]:
        if sep in t:
            a,b = t.split(sep,1)
            return {"home": a.strip(), "away": b.strip()}
    return {"home": t.strip(), "away": "Rival por confirmar"}

def competition_badge(league, sport=None):
    txt = (league or sport or "Fútbol").lower()
    if "world" in txt or "mundial" in txt or "fifa" in txt: return "🌍 Mundial"
    if "champ" in txt: return "🏆 Champions"
    if "premier" in txt or "epl" in txt: return "🏴 Premier"
    if "liga" in txt or "spain" in txt: return "🇪🇸 LaLiga"
    if "serie" in txt: return "🇮🇹 Serie A"
    if "bundes" in txt: return "🇩🇪 Bundesliga"
    if "ligue" in txt or "france" in txt: return "🇫🇷 Ligue 1"
    if "nba" in txt or "basket" in txt: return "🏀 NBA"
    return "⚽ Fútbol"



def team_initials(name):
    """Iniciales visuales para escudos generados cuando la API no trae logos oficiales."""
    words = [w for w in re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 ]", " ", str(name or "")).split() if w]
    ignore = {"fc", "cf", "club", "de", "the", "and", "city"}
    clean = [w for w in words if w.lower() not in ignore]
    if not clean:
        clean = words or ["N"]
    if len(clean) == 1:
        return clean[0][:3].upper()
    return (clean[0][0] + clean[1][0]).upper()


def league_filter_label(value):
    v = (value or "").lower()
    if not v or v == "all": return "Todas"
    labels = {
        "world": "Mundial", "mundial": "Mundial", "champions": "Champions", "europa": "Europa League",
        "laliga": "LaLiga", "liga": "LaLiga", "premier": "Premier", "epl": "Premier League",
        "serie": "Serie A", "bundesliga": "Bundesliga", "ligue": "Ligue 1", "portugal": "Portugal",
    }
    for k, label in labels.items():
        if k in v: return label
    return value.title()


def ui_date_links(base_path, q='', league=''):
    today = madrid_date_today()
    items = [
        ("all", "Todos"),
        ("today", "Hoy"),
        ("tomorrow", "Mañana"),
        ("dayafter", "Pasado"),
        ("week", "7 días"),
    ]
    out = []
    for key, label in items:
        args = []
        if key != "all": args.append("date="+key)
        if q: args.append("q="+urllib.parse.quote(q))
        if league: args.append("league="+urllib.parse.quote(league))
        out.append({"key":key,"label":label,"href":base_path + ("?"+"&".join(args) if args else "")})
    return out


def match_time_status(p):
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    live_status = (get('live_status','') or 'PROGRAMADO').upper()
    score = get('live_score','') or ''
    minute = get('live_minute','') or ''
    if live_status in ('EN DIRECTO','LIVE','1H','2H'):
        return {"label":"EN VIVO", "detail": (minute or "Live"), "score": score, "tone":"live"}
    if live_status in ('FINALIZADO','FT','FINISHED'):
        return {"label":"FINAL", "detail":"Resultado", "score": score, "tone":"final"}
    return {"label":"PROGRAMADO", "detail":"Próximo", "score": score, "tone":"scheduled"}


# ==========================================================
# V33.0 SHARK PROFESSIONAL EXPERIENCE HELPERS
# ==========================================================
def safe_row_get(row, key, default=None):
    try:
        return row.get(key, default)
    except Exception:
        try:
            return row[key]
        except Exception:
            return default


def parse_match_score(score_text):
    """Devuelve goles/puntos local/visitante si el marcador es legible."""
    text = str(score_text or "").strip()
    if not text:
        return None
    m = re.search(r"(\d+)\s*[-:]\s*(\d+)", text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def pick_winner_side(p):
    pick = normalize_ai_text(safe_row_get(p, "pick", ""))
    teams = team_pair(safe_row_get(p, "title", ""))
    home = normalize_ai_text(teams.get("home"))
    away = normalize_ai_text(teams.get("away"))
    if home and home in pick:
        return "home"
    if away and away in pick:
        return "away"
    return None


def professional_insight(p):
    """Bloques explicativos profesionales usando solo datos disponibles en DB, sin jerga técnica."""
    score = int(float(safe_row_get(p, "score", 0) or 0))
    ev = float(safe_row_get(p, "ev", 0) or 0)
    cuota = safe_row_get(p, "cuota", "") or safe_row_get(p, "odds_decimal", "") or "-"
    market = safe_row_get(p, "odds_market", "") or "h2h"
    bookmaker = safe_row_get(p, "odds_bookmaker", "") or "Casa disponible"
    sp = smart_pick_profile(score, ev, cuota)
    choice = human_bet_choice(p)
    conf = "alta" if score >= 84 else ("media" if score >= 70 else "moderada")
    trend = "valor fuerte" if ev >= 6 else ("valor interesante" if ev >= 2 else "valor ajustado")
    if score >= 84:
        headline = f"SHARK ve buena entrada en {choice}: cuota, riesgo y valor están alineados."
    elif score >= 72:
        headline = f"{choice} tiene valor, pero conviene entrar con stake controlado."
    else:
        headline = f"{choice} es una señal arriesgada: solo stake bajo si decides entrar."
    return {
        "confidence": conf.capitalize(),
        "trend": trend.capitalize(),
        "headline": headline,
        "stake_pct": sp.get("stake_pct", 1),
        "risk": sp.get("risk", "Medio"),
        "market_label": pick_market_label(market),
        "bookmaker": bookmaker,
        "cuota": cuota,
        "choice": choice,
        "bullets_for": [
            f"Confianza SHARK {conf} ({score}/100).",
            f"Cuota {cuota} con {trend} según el motor SHARK.",
            f"Apuesta fácil de entender: {bet_simple_explanation(p)}",
        ],
        "bullets_against": [
            "La cuota puede cambiar antes del inicio.",
            "No es una apuesta segura: usa siempre stake responsable.",
            "Si no entiendes el mercado o cambia la línea, mejor no entrar.",
        ],
    }

def stake_recommendation_eur(p, balance=None):
    try:
        bal = float(balance or 0)
    except Exception:
        bal = 0
    prof = professional_insight(p)
    pct = float(prof.get("stake_pct") or 1)
    amount = round(max(0, bal * pct / 100), 2)
    return {"pct": pct, "amount": amount, "label": f"{pct:.0f}% de banca"}


def match_timeline(p):
    kt = kickoff_ui_parts(safe_row_get(p, "kickoff_time", ""))
    livep = match_time_status(p)
    return [
        {"label": "Apuesta recomendada", "text": human_bet_choice(p)},
        {"label": "Inicio del partido", "text": kt.get("full", "Horario por confirmar")},
        {"label": "Estado", "text": livep.get("label", "PROGRAMADO")},
        {"label": "Confianza SHARK", "text": f"{safe_row_get(p, 'score', 0)}/100 · stake responsable"},
    ]

def auto_settle_finished_user_picks():
    """Cierra picks H2H si existe marcador final guardado. Seguro: si no hay datos suficientes, no toca nada."""
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT up.id AS up_id, up.amount, p.title, p.pick, p.odds_market, p.cuota, p.live_status, p.live_score
            FROM user_picks up
            JOIN picks p ON p.id = up.pick_id
            WHERE LOWER(COALESCE(up.status,'pendiente'))='pendiente'
              AND UPPER(COALESCE(p.live_status,'')) IN ('FINALIZADO','FT','FINISHED')
              AND LOWER(COALESCE(p.odds_market,'h2h'))='h2h'
              AND COALESCE(p.live_score,'')!=''
        """)
        rows = cur.fetchall(); changed = 0
        for r in rows:
            parsed = parse_match_score(r["live_score"])
            side = pick_winner_side(r)
            if not parsed or not side:
                continue
            home_goals, away_goals = parsed
            won = (side == "home" and home_goals > away_goals) or (side == "away" and away_goals > home_goals)
            draw = home_goals == away_goals
            amount = float(r["amount"] or 0)
            try: cuota = float(r["cuota"] or 0)
            except Exception: cuota = 0
            if draw:
                status, profit = "void", 0.0
            elif won:
                status, profit = "ganado", round(amount * max(cuota - 1, 0), 2)
            else:
                status, profit = "perdido", round(-amount, 2)
            cur.execute("UPDATE user_picks SET status=?, profit=? WHERE id=?", (status, profit, r["up_id"]))
            changed += 1
        if changed:
            cur.execute("""
                UPDATE picks
                SET result_status=CASE WHEN COALESCE(result_status,'pendiente')='pendiente' THEN 'cerrado_auto' ELSE result_status END,
                    result_checked_at=?
                WHERE UPPER(COALESCE(live_status,'')) IN ('FINALIZADO','FT','FINISHED')
            """, (iso_now(),))
        conn.commit(); conn.close()
        return changed
    except Exception:
        try: conn.close()
        except Exception: pass
        return 0


def live_results_snapshot(limit=8):
    """Resumen ligero para cliente: directos, próximos y resultados pendientes/recientes."""
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT * FROM picks
            WHERE COALESCE(active,1)=1
            """ + real_only_clause() + football_priority_clause(default_only=True) + """
            ORDER BY
              CASE UPPER(COALESCE(live_status,''))
                WHEN 'EN DIRECTO' THEN 0 WHEN 'LIVE' THEN 0 WHEN 'DESCANSO' THEN 1
                WHEN 'FINALIZADO' THEN 2 WHEN 'FT' THEN 2 WHEN 'FINISHED' THEN 2
                WHEN 'PROGRAMADO' THEN 3 ELSE 4 END,
              CASE WHEN COALESCE(kickoff_time,'')='' THEN 1 ELSE 0 END,
              kickoff_time ASC, CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall(); conn.close()
        live=[]; upcoming=[]; finished=[]
        for r in rows:
            st=(safe_row_get(r,'live_status','') or '').upper()
            item={
                'id': safe_row_get(r,'id'),
                'title': safe_row_get(r,'title','Partido'),
                'league': safe_row_get(r,'league','Fútbol'),
                'status': match_time_status(r),
                'time': kickoff_ui_parts(safe_row_get(r,'kickoff_time','')),
                'bet': clear_bet_text(r),
                'score': safe_row_get(r,'score',0),
                'result': pick_result_badge(r),
            }
            if st in ('EN DIRECTO','LIVE','1H','2H','DESCANSO'): live.append(item)
            elif st in ('FINALIZADO','FT','FINISHED'): finished.append(item)
            else: upcoming.append(item)
        return {'live':live[:4], 'upcoming':upcoming[:4], 'finished':finished[:4], 'total':len(rows)}
    except Exception:
        return {'live':[], 'upcoming':[], 'finished':[], 'total':0}


def auto_settle_and_notify_finished_picks():
    """Autocierre seguro de resultados H2H con marcador final. No inventa resultados."""
    if not AUTO_RESULT_SETTLEMENT:
        return {'changed': 0, 'notified': 0}
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute("""
            SELECT p.id AS pick_id, p.title, p.pick, p.odds_market, p.cuota, p.live_status, p.live_score, p.result_alerted_at,
                   up.id AS up_id, up.amount
            FROM user_picks up
            JOIN picks p ON p.id=up.pick_id
            WHERE LOWER(COALESCE(up.status,'pendiente'))='pendiente'
              AND UPPER(COALESCE(p.live_status,'')) IN ('FINALIZADO','FT','FINISHED')
              AND LOWER(COALESCE(p.odds_market,'h2h'))='h2h'
              AND COALESCE(p.live_score,'')!=''
        """)
        rows=cur.fetchall(); changed=0; affected_pick_ids=set(); notify_pick_ids=[]
        for r in rows:
            parsed=parse_match_score(r['live_score'])
            side=pick_winner_side(r)
            if not parsed or not side:
                continue
            home_goals, away_goals = parsed
            won = (side == 'home' and home_goals > away_goals) or (side == 'away' and away_goals > home_goals)
            draw = home_goals == away_goals
            try: amount=float(r['amount'] or 0)
            except Exception: amount=0.0
            try: cuota=float(str(r['cuota'] or 0).replace(',', '.'))
            except Exception: cuota=0.0
            if draw:
                status, profit = 'void', 0.0
            elif won:
                status, profit = 'ganado', round(amount * max(cuota - 1, 0), 2)
            else:
                status, profit = 'perdido', round(-amount, 2)
            cur.execute('UPDATE user_picks SET status=?, profit=? WHERE id=?', (status, profit, r['up_id']))
            cur.execute("""
                UPDATE picks SET result_status=?, result_score=?, result_checked_at=?,
                    closing_note=CASE WHEN COALESCE(closing_note,'')='' THEN 'Cerrado automáticamente por marcador final.' ELSE closing_note END
                WHERE id=?
            """, (status, r['live_score'], iso_now(), r['pick_id']))
            changed += 1; affected_pick_ids.add(r['pick_id'])
            if not (r['result_alerted_at'] or '').strip():
                notify_pick_ids.append((r['pick_id'], status, r['live_score']))
        for pid in affected_pick_ids:
            cur.execute('UPDATE picks SET result_checked_at=? WHERE id=?', (iso_now(), pid))
        conn.commit(); conn.close()
        notified=0
        seen=set()
        for pid,status,score in notify_pick_ids:
            if pid in seen: continue
            seen.add(pid)
            try:
                send_result_alert(pid, status, score)
                if PUSH_SEND_ON_RESULTS:
                    try:
                        pick_row = fetch_pick_by_id(pid)
                        estado = 'ganado' if str(status).lower() == 'ganado' else ('perdido' if str(status).lower() == 'perdido' else 'nulo')
                        send_push_to_connected_users('Resultado SHARK', f'Pick {estado}: {safe_row_get(pick_row, "title", "Partido")} · Marcador {score}', f'/partido/{pid}', min_plan='FREE', kind='push_result')
                    except Exception:
                        pass
                conn=get_db(); cur=conn.cursor(); cur.execute('UPDATE picks SET result_alerted_at=? WHERE id=?', (iso_now(), pid)); conn.commit(); conn.close()
                notified += 1
            except Exception:
                pass
        return {'changed': changed, 'notified': notified}
    except Exception:
        try: conn.close()
        except Exception: pass
        return {'changed': 0, 'notified': 0}


# ==========================================================
# V34.0 REAL DATA + ROI SYSTEM HELPERS
# ==========================================================
def normalize_status(status):
    st = (status or "pendiente").strip().lower()
    aliases = {
        "win": "ganado", "won": "ganado", "acertado": "ganado",
        "loss": "perdido", "lost": "perdido", "fallado": "perdido",
        "void": "void", "nulo": "void", "cancelado": "void",
        "pending": "pendiente", "abierto": "pendiente"
    }
    return aliases.get(st, st if st in ("ganado", "perdido", "void", "pendiente") else "pendiente")


def status_label_es(status):
    st = normalize_status(status)
    return {"ganado": "Ganado", "perdido": "Perdido", "void": "Nulo", "pendiente": "Pendiente"}.get(st, "Pendiente")


def compute_profit_from_status(amount, cuota, status):
    try: amount = float(amount or 0)
    except Exception: amount = 0.0
    try: cuota = float(str(cuota or 0).replace(',', '.'))
    except Exception: cuota = 0.0
    st = normalize_status(status)
    if st == "ganado":
        return round(amount * max(cuota - 1, 0), 2)
    if st == "perdido":
        return round(-amount, 2)
    return 0.0


def settle_pick_for_all_users(pick_id, status, result_score="", note=""):
    """Cierra el pick para todos los usuarios que lo guardaron. Seguro y reversible desde admin."""
    st = normalize_status(status)
    now = iso_now()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, cuota, odds_decimal FROM picks WHERE id=?", (pick_id,))
    p = cur.fetchone()
    if not p:
        conn.close(); return {"ok": False, "updated": 0}
    cuota = p["cuota"] or p["odds_decimal"] or 0
    cur.execute("""
        UPDATE picks
        SET result_status=?, result_score=?, result_checked_at=?, closing_note=?,
            live_status=CASE WHEN ? IN ('ganado','perdido','void') THEN 'FINALIZADO' ELSE live_status END,
            live_score=CASE WHEN ?!='' THEN ? ELSE live_score END
        WHERE id=?
    """, (st, result_score, now, note, st, result_score, result_score, pick_id))
    cur.execute("SELECT id, amount FROM user_picks WHERE pick_id=?", (pick_id,))
    rows = cur.fetchall(); updated = 0
    for r in rows:
        profit = compute_profit_from_status(r["amount"], cuota, st)
        cur.execute("UPDATE user_picks SET status=?, profit=? WHERE id=?", (st, profit, r["id"]))
        updated += 1
    conn.commit(); conn.close()
    return {"ok": True, "updated": updated, "status": st}


def enhanced_roi_summary(user_id):
    """Resumen profesional del usuario: rendimiento real, pendientes y desglose por liga/mercado."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT up.amount, up.status, up.profit, up.created_at,
               p.title, p.league, p.sport, p.odds_market, p.cuota, p.score, p.ev, p.kickoff_time
        FROM user_picks up
        LEFT JOIN picks p ON p.id = up.pick_id
        WHERE up.user_id=?
        ORDER BY up.id ASC
    """, (user_id,))
    rows = cur.fetchall(); conn.close()
    total_stake = closed_stake = pending_stake = profit = 0.0
    won = lost = void = pending = 0
    by_league = {}; by_market = {}; curve = []
    cumulative = 0.0
    last_closed = []
    for r in rows:
        amount = float(r["amount"] or 0)
        st = normalize_status(r["status"])
        pr = float(r["profit"] or 0)
        total_stake += amount
        if st == "pendiente":
            pending += 1; pending_stake += amount
        else:
            closed_stake += amount; profit += pr; cumulative += pr
            if st == "ganado": won += 1
            elif st == "perdido": lost += 1
            elif st == "void": void += 1
            key_league = r["league"] or r["sport"] or "General"
            key_market = pick_market_label(r["odds_market"] or "")
            for bucket, key in [(by_league, key_league), (by_market, key_market)]:
                bucket.setdefault(key, {"stake":0.0,"profit":0.0,"won":0,"lost":0,"total":0})
                bucket[key]["stake"] += amount
                bucket[key]["profit"] += pr
                bucket[key]["total"] += 1
                if st == "ganado": bucket[key]["won"] += 1
                if st == "perdido": bucket[key]["lost"] += 1
            last_closed.append({"title": r["title"] or "Pick", "status": st, "profit": round(pr,2), "amount": round(amount,2), "league": key_league})
        curve.append({"n": len(curve)+1, "profit": round(cumulative,2), "status": st})
    closed = won + lost
    roi = round((profit / closed_stake) * 100, 1) if closed_stake else 0.0
    winrate = round((won / closed) * 100, 1) if closed else 0.0
    def top_items(bucket):
        out=[]
        for k,v in bucket.items():
            stake=v["stake"] or 0
            item=dict(v); item["name"]=k; item["roi"]=round((v["profit"]/stake)*100,1) if stake else 0.0; item["profit"]=round(v["profit"],2); item["stake"]=round(stake,2)
            out.append(item)
        return sorted(out, key=lambda x: x["profit"], reverse=True)[:5]
    return {
        "total_picks": len(rows), "won": won, "lost": lost, "void": void, "pending": pending,
        "closed": closed + void, "winrate": winrate, "roi": roi,
        "total_stake": round(total_stake,2), "closed_stake": round(closed_stake,2),
        "pending_stake": round(pending_stake,2), "profit": round(profit,2),
        "curve": curve[-30:], "last_closed": list(reversed(last_closed[-6:])),
        "by_league": top_items(by_league), "by_market": top_items(by_market),
        "status_text": "Rentabilidad positiva" if profit > 0 else ("En seguimiento" if len(rows) else "Sin historial todavía")
    }


def pick_result_badge(p):
    st = normalize_status(safe_row_get(p, "result_status", "pendiente"))
    if st == "pendiente":
        live = (safe_row_get(p, "live_status", "") or "").upper()
        if live in ("FINALIZADO", "FT", "FINISHED"):
            return {"label": "Final pendiente de cerrar", "tone": "pending"}
    return {"label": status_label_es(st), "tone": st}



def user_trust_profile(user_id):
    """Perfil de confianza V45: racha, mejores ligas/mercados y recomendación simple."""
    summary = enhanced_roi_summary(user_id)
    curve = summary.get("curve") or []
    # Racha final sobre cerrados
    streak_status = "Sin racha"
    streak_count = 0
    for item in reversed(curve):
        st = normalize_status(item.get("status"))
        if st not in ("ganado", "perdido"):
            continue
        label = "ganando" if st == "ganado" else "perdiendo"
        if streak_count == 0:
            streak_status = label
            streak_count = 1
        elif streak_status == label:
            streak_count += 1
        else:
            break
    if streak_count == 0:
        streak_text = "Aún no hay racha cerrada"
    elif streak_status == "ganando":
        streak_text = f"{streak_count} pick{'s' if streak_count != 1 else ''} ganado{'s' if streak_count != 1 else ''} seguido{'s' if streak_count != 1 else ''}"
    else:
        streak_text = f"{streak_count} pick{'s' if streak_count != 1 else ''} perdido{'s' if streak_count != 1 else ''} seguido{'s' if streak_count != 1 else ''}"
    best_league = (summary.get("by_league") or [{}])[0].get("name", "Sin datos") if summary.get("by_league") else "Sin datos"
    best_market = (summary.get("by_market") or [{}])[0].get("name", "Sin datos") if summary.get("by_market") else "Sin datos"
    trust = 50
    trust += min(20, max(0, float(summary.get("roi") or 0)))
    trust += min(15, max(0, (float(summary.get("winrate") or 0) - 45) / 2))
    trust += 8 if summary.get("total_picks", 0) >= 10 else 0
    trust -= 8 if streak_status == "perdiendo" and streak_count >= 2 else 0
    trust = int(max(1, min(99, round(trust))))
    if trust >= 80:
        trust_label = "Confianza alta"
    elif trust >= 62:
        trust_label = "Confianza media"
    else:
        trust_label = "En construcción"
    return {
        "trust": trust,
        "trust_label": trust_label,
        "streak": streak_text,
        "best_league": best_league,
        "best_market": best_market,
        "advice": roi_advice(summary),
        "summary": summary,
    }


def pick_trust_score(p):
    """Lectura clara de confianza para cada pick, pensada para clientes."""
    sp = smart_pick_profile(safe_row_get(p, "score", 70), safe_row_get(p, "ev", 0), safe_row_get(p, "cuota", None) or safe_row_get(p, "odds_decimal", None))
    score = int(sp.get("score", 70) or 70)
    ev = safe_float(safe_row_get(p, "ev", 0), 0)
    odds = safe_float(safe_row_get(p, "cuota", None) or safe_row_get(p, "odds_decimal", None), 1.8)
    trust = score
    if ev > 4:
        trust += 4
    if odds > 2.75:
        trust -= 8
    if odds < 1.35:
        trust -= 4
    trust = int(max(1, min(99, trust)))
    if trust >= 82:
        label = "Entrar ahora"
        why = "La señal tiene buena confianza y el riesgo está controlado."
        avoid = "No entres si la cuota baja mucho antes de apostar."
        tone = "high"
    elif trust >= 68:
        label = "Entrar con calma"
        why = "Tiene valor, pero conviene usar stake moderado."
        avoid = "No entres si buscas una apuesta muy segura."
        tone = "mid"
    else:
        label = "Esperar o stake bajo"
        why = "La señal es más agresiva y puede moverse bastante."
        avoid = "No entres fuerte; úsala solo si aceptas riesgo alto."
        tone = "low"
    return {"score": trust, "label": label, "why": why, "avoid": avoid, "tone": tone}



def user_favorite_ids(user_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT pick_id FROM user_favorites WHERE user_id=?", (user_id,))
        ids = {int(r[0]) for r in cur.fetchall()}
        conn.close()
        return ids
    except Exception:
        return set()

def client_quality_empty_state(kind="picks"):
    if kind == "partidos":
        return {
            "title": "No hay partidos con ese filtro",
            "text": "Cuando The Odds API abra mercado para esos partidos, aparecerán aquí automáticamente.",
            "action": "Ver próximos 7 días",
            "href": "/partidos?date=week",
        }
    if kind == "favoritos":
        return {
            "title": "Aún no tienes favoritos",
            "text": "Marca partidos o picks importantes para encontrarlos rápido desde tu panel.",
            "action": "Explorar picks",
            "href": "/picks",
        }
    return {
        "title": "No hay señales activas ahora",
        "text": "SHARK prefiere esperar antes que mostrar apuestas sin valor. Revisa próximos días o vuelve más tarde.",
        "action": "Ver próximos partidos",
        "href": "/partidos?date=week",
    }

def client_next_step(user):
    if not user:
        return {"title":"Crea tu cuenta", "text":"Accede a picks, banca y alertas.", "href":"/registro", "cta":"Registrarme"}
    if not safe_row_get(user, "onboarding_completed_at", ""):
        return {"title":"Configura tu perfil", "text":"Elige riesgo, ligas favoritas y activa alertas para que SHARK se adapte a ti.", "href":"/onboarding", "cta":"Empezar"}
    if not safe_row_get(user, "telegram_chat_id", ""):
        return {"title":"Conecta Telegram", "text":"Recibe señales importantes sin entrar cada vez en la app.", "href":"/alertas", "cta":"Conectar"}
    return {"title":"Listo para operar", "text":"Tu cuenta ya tiene perfil y alertas. Revisa las mejores señales de hoy.", "href":"/picks?date=today", "cta":"Ver picks"}

def roi_advice(summary):
    roi = float(summary.get("roi") or 0)
    pending = float(summary.get("pending_stake") or 0)
    if summary.get("total_picks",0) < 3:
        return "Guarda y cierra más picks para construir una muestra real."
    if roi > 8:
        return "Buen rendimiento: mantén stake estable y evita sobreexponerte."
    if roi >= 0:
        return "Rendimiento controlado: prioriza picks con score alto y EV positivo."
    if pending > 0:
        return "Hay riesgo abierto: espera resultados antes de subir stake."
    return "Reduce stake y filtra mejor por ligas/mercados rentables."

@app.context_processor
def inject_globals():
    return {
        "APP_NAME": APP_NAME,
        "APP_VERSION": APP_VERSION,
        "current_user": current_user(),
        "is_admin": is_admin(),
        "PLAN_BENEFITS": PLAN_BENEFITS,
        "COMMERCIAL_PLANS": COMMERCIAL_PLANS,
        "live_result_class": live_result_class,
        "shark_score_profile": shark_score_profile,
        "can_access_feature": can_access_feature,
        "calculate_user_pro_stats": calculate_user_pro_stats,
        "plan_stats_access": plan_stats_access,
        "smart_pick_profile": smart_pick_profile,
        "live_event_profile": live_event_profile,
        "pick_reason_text": pick_reason_text,
        "pick_market_label": pick_market_label,
        "plan_ui_profile": plan_ui_profile,
        "current_user_fresh": fresh_user_from_db,
        "plan_locked": plan_locked,
        "kickoff_ui_parts": kickoff_ui_parts,
        "team_pair": team_pair,
        "competition_badge": competition_badge,
        "team_initials": team_initials,
        "league_filter_label": league_filter_label,
        "ui_date_links": ui_date_links,
        "match_time_status": match_time_status,
        "professional_insight": professional_insight,
        "stake_recommendation_eur": stake_recommendation_eur,
        "match_timeline": match_timeline,
        "market_explanation": market_explanation,
        "bet_simple_explanation": bet_simple_explanation,
        "human_bet_choice": human_bet_choice,
        "clear_bet_text": clear_bet_text,
        "why_bet_text": why_bet_text,
        "why_not_bet_text": why_not_bet_text,
        "team_color": team_color,
        "enhanced_roi_summary": enhanced_roi_summary,
        "status_label_es": status_label_es,
        "pick_result_badge": pick_result_badge,
        "roi_advice": roi_advice,
        "team_logo_url": team_logo_url,
        "team_badge_url": team_badge_url,
        "display_team_logo": display_team_logo,
        "get_competition_context": get_competition_context,
        "standings_status": standings_status,
        "get_standings_groups": get_standings_groups,
        "user_favorite_ids": user_favorite_ids,
        "client_quality_empty_state": client_quality_empty_state,
        "client_next_step": client_next_step,
        "platform_health_summary": platform_health_summary,
        "user_trust_profile": user_trust_profile,
        "pick_trust_score": pick_trust_score,
    }


# ==========================================================
# PUBLIC ROUTES
# ==========================================================

# ==========================================================
# V36 PROFESSIONAL PLATFORM HELPERS
# ==========================================================
def platform_health_summary():
    """Resumen seguro para dashboard/admin sin hacer llamadas externas."""
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM picks WHERE active=1 " + real_only_clause())
        active_picks = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM picks WHERE active=1 AND UPPER(COALESCE(live_status,'')) IN ('LIVE','EN VIVO','EN DIRECTO','1H','2H')")
        live_now = cur.fetchone()[0]
        cur.execute("SELECT MAX(created_at) FROM picks WHERE active=1")
        last_pick = cur.fetchone()[0] or ""
        cur.execute("SELECT COUNT(*) FROM alert_logs WHERE date(created_at)=date('now')")
        alerts_today = cur.fetchone()[0]
        conn.close()
    except Exception:
        active_picks, live_now, last_pick, alerts_today = 0, 0, "", 0
    return {
        "version": APP_VERSION,
        "odds_api": bool(ODDS_API_KEY) and ENABLE_ODDS_API,
        "standings": bool(FOOTBALL_DATA_KEY) and ENABLE_STANDINGS,
        "alerts": ENABLE_PRO_ALERTS and (bool(TELEGRAM_BOT_TOKEN and (TELEGRAM_CHAT_ID or TELEGRAM_FREE_CHAT_ID or TELEGRAM_PRO_CHAT_ID or TELEGRAM_ELITE_CHAT_ID)) or bool(DISCORD_WEBHOOK_URL)),
        "active_picks": active_picks,
        "live_now": live_now,
        "last_pick": last_pick,
        "alerts_today": alerts_today,
    }


def log_alert(kind, title, body, channel, status, payload=None):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""INSERT INTO alert_logs(kind,title,body,channel,status,payload,created_at)
                       VALUES(?,?,?,?,?,?,?)""", (kind, title, body, channel, status, json.dumps(payload or {}, ensure_ascii=False), datetime.utcnow().isoformat(timespec="seconds")))
        conn.commit(); conn.close()
    except Exception:
        pass


def send_platform_alert(kind, title, body):
    """Alertas preparadas para Telegram/Discord. No bloquea la app si fallan."""
    results = []
    if not ENABLE_PRO_ALERTS:
        log_alert(kind, title, body, "system", "disabled", {})
        return {"ok": False, "reason": "alerts_disabled", "results": results}
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"🦈 <b>{title}</b>\n\n{body}",
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            r = requests.post(url, json=payload, timeout=5)
            status = "ok" if r.ok else f"error_{r.status_code}"
            log_alert(kind, title, body, "telegram", status, {"status_code": r.status_code, "response": (r.text or "")[:300]})
            results.append({"channel": "telegram", "status": status})
        except Exception as e:
            log_alert(kind, title, body, "telegram", "error", {"error": str(e)[:200]})
            results.append({"channel": "telegram", "status": "error"})
    if DISCORD_WEBHOOK_URL:
        try:
            r = requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🦈 **{title}**\n{body}"}, timeout=5)
            status = "ok" if r.ok else f"error_{r.status_code}"
            log_alert(kind, title, body, "discord", status, {"status_code": r.status_code})
            results.append({"channel": "discord", "status": status})
        except Exception as e:
            log_alert(kind, title, body, "discord", "error", {"error": str(e)[:200]})
            results.append({"channel": "discord", "status": "error"})
    if not results:
        log_alert(kind, title, body, "system", "no_channel", {})
    return {"ok": any(x.get("status") == "ok" for x in results), "results": results}


def telegram_ready():
    return bool(ENABLE_PRO_ALERTS and TELEGRAM_BOT_TOKEN and (TELEGRAM_CHAT_ID or TELEGRAM_FREE_CHAT_ID or TELEGRAM_PRO_CHAT_ID or TELEGRAM_ELITE_CHAT_ID))


def telegram_private_ready():
    return bool(ENABLE_PRO_ALERTS and TELEGRAM_BOT_TOKEN)


def telegram_config_status():
    """Estado legible de Telegram para admin. No expone tokens al cliente."""
    channel_ids = {
        "general": bool(TELEGRAM_CHAT_ID),
        "free": bool(TELEGRAM_FREE_CHAT_ID),
        "pro": bool(TELEGRAM_PRO_CHAT_ID),
        "elite": bool(TELEGRAM_ELITE_CHAT_ID),
    }
    return {
        "enabled": bool(ENABLE_PRO_ALERTS),
        "bot_token": bool(TELEGRAM_BOT_TOKEN),
        "bot_username": bool(TELEGRAM_BOT_USERNAME),
        "any_channel": any(channel_ids.values()),
        "channels": channel_ids,
        "group_url": bool(TELEGRAM_GROUP_URL or TELEGRAM_FREE_GROUP_URL or TELEGRAM_PRO_GROUP_URL or TELEGRAM_ELITE_GROUP_URL),
        "auto_engine": bool(TELEGRAM_AUTO_ALERT_ENGINE),
        "new_picks": bool(TELEGRAM_ALERT_NEW_PICKS),
        "results": bool(TELEGRAM_ALERT_RESULTS),
        "plan_channels": bool(TELEGRAM_SEND_TO_PLAN_CHANNELS),
        "connected_users": bool(TELEGRAM_SEND_TO_CONNECTED_USERS),
        "min_score": TELEGRAM_ALERT_MIN_SCORE,
    }


def telegram_channel_chat_id(plan):
    """Canal de envío según membresía. Permite canal único o canales separados."""
    plan = normalize_plan(plan, allow_admin=True)
    if plan == "ELITE":
        return TELEGRAM_ELITE_CHAT_ID or TELEGRAM_PRO_CHAT_ID or TELEGRAM_CHAT_ID
    if plan == "PRO":
        return TELEGRAM_PRO_CHAT_ID or TELEGRAM_CHAT_ID
    if plan == "FREE":
        return TELEGRAM_FREE_CHAT_ID or TELEGRAM_CHAT_ID
    return TELEGRAM_CHAT_ID or TELEGRAM_ELITE_CHAT_ID or TELEGRAM_PRO_CHAT_ID or TELEGRAM_FREE_CHAT_ID


def telegram_plan_group_url(plan):
    plan = normalize_plan(plan, allow_admin=True)
    if plan == "ELITE":
        return TELEGRAM_ELITE_GROUP_URL or TELEGRAM_PRO_GROUP_URL or TELEGRAM_GROUP_URL
    if plan == "PRO":
        return TELEGRAM_PRO_GROUP_URL or TELEGRAM_GROUP_URL
    if plan == "FREE":
        return TELEGRAM_FREE_GROUP_URL or TELEGRAM_GROUP_URL
    return TELEGRAM_GROUP_URL


def send_telegram_message(chat_id, body, kind="telegram", title="Mensaje SHARK", payload=None):
    if not ENABLE_PRO_ALERTS or not TELEGRAM_BOT_TOKEN or not chat_id:
        log_alert(kind, title, body, "telegram", "disabled_or_missing_chat", payload or {})
        return {"ok": False, "reason": "telegram_not_ready"}
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": body,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=5)
        status = "ok" if r.ok else f"error_{r.status_code}"
        log_alert(kind, title, body, "telegram", status, {"chat_id": str(chat_id), "status_code": r.status_code, "response": (r.text or "")[:300], **(payload or {})})
        return {"ok": r.ok, "status": status}
    except Exception as e:
        log_alert(kind, title, body, "telegram", "error", {"chat_id": str(chat_id), "error": str(e)[:200], **(payload or {})})
        return {"ok": False, "status": "error"}


def mark_pick_telegram_alerted(pick_id, field="telegram_alerted_at"):
    try:
        if field not in ("telegram_alerted_at", "telegram_channel_alerted_at"):
            field = "telegram_alerted_at"
        conn = get_db(); cur = conn.cursor()
        cur.execute(f"UPDATE picks SET {field}=? WHERE id=?", (iso_now(), pick_id))
        conn.commit(); conn.close()
    except Exception:
        pass


def user_full_from_db(user_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = cur.fetchone(); conn.close()
        return row
    except Exception:
        return None


def telegram_plan_policy(plan):
    """Qué calidad recibe cada membresía. Lenguaje claro, sin jerga técnica."""
    plan = normalize_plan(plan, allow_admin=True)
    policies = {
        "FREE": {
            "label": "FREE",
            "min_score": 82,
            "max_daily": 1,
            "detail": "básica",
            "description": "Recibe avisos generales y una señal destacada cuando haya mucho valor.",
            "markets": "solo señales muy claras",
            "show_stake": False,
            "show_ev": False,
            "show_full_reason": False,
        },
        "PRO": {
            "label": "PRO",
            "min_score": 75,
            "max_daily": 4,
            "detail": "premium",
            "description": "Recibe señales premium con cuota, riesgo, explicación sencilla y stake recomendado.",
            "markets": "fútbol, competiciones principales y mejores cuotas",
            "show_stake": True,
            "show_ev": True,
            "show_full_reason": True,
        },
        "ELITE": {
            "label": "ELITE",
            "min_score": 68,
            "max_daily": 12,
            "detail": "máxima",
            "description": "Recibe prioridad, más señales, análisis completo, señales live y mayor profundidad SHARK.",
            "markets": "todo PRO + señales live, value y oportunidades avanzadas",
            "show_stake": True,
            "show_ev": True,
            "show_full_reason": True,
        },
        "ADMIN": {
            "label": "ADMIN",
            "min_score": 0,
            "max_daily": 99,
            "detail": "interna",
            "description": "Pruebas internas.",
            "markets": "todo",
            "show_stake": True,
            "show_ev": True,
            "show_full_reason": True,
        },
    }
    return policies.get(plan, policies["FREE"])


def user_alerts_sent_today(user_id):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM alert_logs
            WHERE kind='user_pick' AND channel='telegram_private'
            AND json_extract(payload, '$.user_id')=?
            AND date(created_at)=date('now')
        """, (int(user_id),))
        n = cur.fetchone()[0]
        conn.close(); return int(n or 0)
    except Exception:
        return 0


def pick_score_value(p):
    try: return int(float(safe_row_get(p, "score", 0) or 0))
    except Exception: return 0


def should_send_pick_to_user(p, user_row):
    plan = normalize_plan(safe_row_get(user_row, "plan", "FREE"), allow_admin=True)
    policy = telegram_plan_policy(plan)
    if int(safe_row_get(user_row, "telegram_alerts_enabled", 0) or 0) != 1:
        return False, "El usuario no tiene activadas las alertas."
    if not safe_row_get(user_row, "telegram_chat_id", ""):
        return False, "El usuario no ha conectado Telegram."
    if pick_score_value(p) < int(policy["min_score"]):
        return False, "La señal no supera la calidad mínima de su plan."
    if user_alerts_sent_today(safe_row_get(user_row, "id", 0)) >= int(policy["max_daily"]):
        return False, "Límite diario del plan alcanzado."
    return True, "ok"


def build_member_pick_message(p, user_row):
    plan = normalize_plan(safe_row_get(user_row, "plan", "FREE"), allow_admin=True)
    policy = telegram_plan_policy(plan)
    title = safe_row_get(p, "title", "Partido") or "Partido"
    league = safe_row_get(p, "league", "Fútbol") or "Fútbol"
    choice = clear_bet_text(p)
    explanation = bet_simple_explanation(p)
    cuota = safe_row_get(p, "cuota", "-") or "-"
    score = pick_score_value(p)
    ev = safe_row_get(p, "ev", "0") or "0"
    kickoff = safe_row_get(p, "kickoff_time", "Horario pendiente") or "Horario pendiente"
    bookmaker = safe_row_get(p, "odds_bookmaker", "Casa disponible") or "Casa disponible"
    prof = professional_insight(p)
    risk = prof.get("risk", "Medio")
    stake = prof.get("stake_pct", 1)
    msg = [
        f"🦈 <b>Señal {policy['label']} para ti</b>",
        f"⚽ <b>{_html_escape(title)}</b>",
        f"🏆 {_html_escape(league)}",
        f"🕒 {_html_escape(kickoff)} hora España",
        "",
        f"✅ <b>Apuesta: {_html_escape(choice)}</b>",
        f"👶 <b>Qué significa:</b> {_html_escape(explanation)}",
        "",
        f"💰 Cuota: <b>{_html_escape(cuota)}</b> · {_html_escape(bookmaker)}",
        f"🦈 Confianza SHARK: <b>{score}/100</b>",
        f"⚠️ Riesgo: <b>{_html_escape(risk)}</b>",
    ]
    if policy.get("show_ev"):
        msg.append(f"📈 Valor estimado: <b>{_html_escape(ev)}%</b>")
    if policy.get("show_stake"):
        msg.append(f"🎯 Stake sugerido: <b>{stake}% de banca</b>")
    else:
        msg.append("🎯 Stake sugerido: apuesta pequeña y responsable")
    if policy.get("show_full_reason"):
        reasons = professional_reasons(p) if 'professional_reasons' in globals() else []
        if reasons:
            msg += ["", "📌 <b>Por qué SHARK la ve interesante:</b>"] + [f"• {_html_escape(r)}" for r in reasons[:3]]
    msg += ["", "Recuerda: apuesta solo si lo entiendes claro y respeta tu banca."]
    return "\n".join(msg)


def build_channel_pick_message(p, plan="PRO"):
    """Mensaje público/privado para canal según plan. Evita jerga y muestra calidad según membresía."""
    plan = normalize_plan(plan, allow_admin=True)
    policy = telegram_plan_policy(plan)
    title = safe_row_get(p, "title", "Partido") or "Partido"
    league = safe_row_get(p, "league", "Fútbol") or "Fútbol"
    choice = clear_bet_text(p)
    explanation = bet_simple_explanation(p)
    cuota = safe_row_get(p, "cuota", "-") or safe_row_get(p, "odds_decimal", "-") or "-"
    kickoff = kickoff_ui_parts(safe_row_get(p, "kickoff_time", "")).get("full") or safe_row_get(p, "kickoff_time", "Horario pendiente") or "Horario pendiente"
    score = pick_score_value(p)
    prof = professional_insight(p)
    risk = prof.get("risk", "Medio")
    stake = prof.get("stake_pct", 1)
    header = "🟦 SEÑAL FREE" if plan == "FREE" else ("⭐ SEÑAL PRO" if plan == "PRO" else "👑 TOP SHARK ELITE")
    lines = [
        f"{header}",
        f"⚽ <b>{_html_escape(title)}</b>",
        f"🏆 {_html_escape(league)}",
        f"🕒 {_html_escape(kickoff)} · hora España/Madrid",
        "",
        f"✅ <b>Apuesta: {_html_escape(choice)}</b>",
        f"👶 {_html_escape(explanation)}",
        "",
        f"💰 Cuota: <b>{_html_escape(cuota)}</b>",
        f"🦈 Confianza SHARK: <b>{score}/100</b>",
        f"⚠️ Riesgo: <b>{_html_escape(risk)}</b>",
    ]
    if policy.get("show_stake"):
        lines.append(f"🎯 Stake: <b>{stake}% de banca</b>")
    else:
        lines.append("🎯 Stake: pequeño y responsable")
    if policy.get("show_full_reason"):
        reasons = professional_reasons(p) if 'professional_reasons' in globals() else []
        if reasons:
            lines += ["", "📌 <b>Por qué SHARK la destaca:</b>"] + [f"• {_html_escape(r)}" for r in reasons[:3]]
    if plan == "FREE":
        lines += ["", "🔒 En PRO/ELITE verás stake, motivos completos y señales prioritarias."]
    lines += ["", "Juego responsable. Si no lo ves claro, no entres."]
    return "\n".join(lines)


def send_pick_to_plan_channels(pick_id):
    """Envía al canal correcto según calidad de señal. No duplica si no hay chats configurados."""
    if not TELEGRAM_SEND_TO_PLAN_CHANNELS:
        return {"ok": False, "reason": "plan_channels_disabled", "sent": 0}
    p = fetch_pick_by_id(pick_id)
    if not p:
        return {"ok": False, "reason": "pick_not_found", "sent": 0}
    score = pick_score_value(p)
    targets = []
    # FREE solo señales muy fuertes y captación. PRO señales premium. ELITE todo lo potente.
    if score >= telegram_plan_policy("FREE")["min_score"]:
        targets.append("FREE")
    if score >= telegram_plan_policy("PRO")["min_score"]:
        targets.append("PRO")
    if score >= telegram_plan_policy("ELITE")["min_score"]:
        targets.append("ELITE")
    # Evita mandar tres veces al mismo chat si se usa canal único.
    used = set(); sent = 0; results = []
    for plan in targets:
        chat_id = telegram_channel_chat_id(plan)
        if not chat_id or chat_id in used:
            continue
        used.add(chat_id)
        body = build_channel_pick_message(p, plan)
        res = send_telegram_message(chat_id, body, kind="channel_pick", title=f"Señal {plan}", payload={"pick_id": pick_id, "plan": plan})
        results.append({"plan": plan, **res})
        if res.get("ok"):
            sent += 1
    if sent:
        mark_pick_telegram_alerted(pick_id, "telegram_channel_alerted_at")
    return {"ok": sent > 0, "sent": sent, "results": results}


def send_private_telegram(chat_id, title, body, payload=None):
    if not telegram_private_ready() or not chat_id:
        return {"ok": False, "reason": "telegram_private_not_ready"}
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": f"{body}", "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=5)
        status = "ok" if r.ok else f"error_{r.status_code}"
        log_alert("user_pick", title, body, "telegram_private", status, payload or {"chat_id": str(chat_id)})
        return {"ok": r.ok, "status": status}
    except Exception as e:
        log_alert("user_pick", title, body, "telegram_private", "error", {"error": str(e)[:200], **(payload or {})})
        return {"ok": False, "status": "error"}


def send_pick_to_connected_users(pick_id):
    """Envía señales adaptadas por membresía a usuarios conectados a Telegram."""
    if not TELEGRAM_SEND_TO_CONNECTED_USERS:
        return {"ok": False, "reason": "connected_users_disabled", "sent": 0}
    if not ENABLE_PRO_ALERTS or not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "reason": "alerts_disabled_or_bot_missing", "sent": 0}
    p = fetch_pick_by_id(pick_id)
    if not p:
        return {"ok": False, "reason": "pick_not_found", "sent": 0}
    sent = 0
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT * FROM users
            WHERE role='cliente' AND telegram_alerts_enabled=1
            AND telegram_chat_id IS NOT NULL AND telegram_chat_id!=''
        """)
        users = cur.fetchall(); conn.close()
    except Exception:
        users = []
    for u in users:
        allowed, reason = should_send_pick_to_user(p, u)
        if not allowed:
            continue
        body = build_member_pick_message(p, u)
        res = send_private_telegram(safe_row_get(u, "telegram_chat_id", ""), "Señal personalizada", body, {"user_id": safe_row_get(u, "id"), "pick_id": pick_id, "plan": safe_row_get(u, "plan")})
        if res.get("ok"):
            sent += 1
    return {"ok": True, "sent": sent}


def make_telegram_connect_code(user_id):
    raw = f"NS{user_id}{int(time.time())}"
    code = hashlib.sha1(raw.encode()).hexdigest()[:8].upper()
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET telegram_connect_code=? WHERE id=?", (code, user_id))
        conn.commit(); conn.close()
    except Exception:
        pass
    return code


def bot_start_link(code):
    if TELEGRAM_BOT_USERNAME:
        return f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={code}"
    return ""


def try_link_telegram_from_updates(user_id):
    """Busca /start CODIGO en getUpdates. Útil sin webhook para que el cliente conecte fácil."""
    user = user_full_from_db(user_id)
    code = safe_row_get(user, "telegram_connect_code", "") if user else ""
    if not TELEGRAM_BOT_TOKEN or not code:
        return False, "Falta bot o código."
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        r = requests.get(url, timeout=5)
        data = r.json() if r.ok else {}
        for item in data.get("result", [])[-80:]:
            msg = item.get("message") or item.get("edited_message") or {}
            text = (msg.get("text") or "").strip()
            if code in text:
                chat = msg.get("chat") or {}
                from_user = msg.get("from") or {}
                chat_id = str(chat.get("id") or "")
                username = from_user.get("username") or chat.get("username") or ""
                if chat_id:
                    conn = get_db(); cur = conn.cursor()
                    cur.execute("""
                        UPDATE users SET telegram_chat_id=?, telegram_username=?, telegram_alerts_enabled=1,
                        telegram_connected_at=?, telegram_connect_code=''
                        WHERE id=?
                    """, (chat_id, username, datetime.utcnow().isoformat(timespec="seconds"), user_id))
                    conn.commit(); conn.close()
                    return True, "Telegram conectado correctamente."
        return False, "Todavía no vemos tu mensaje al bot. Abre el bot y pulsa Iniciar."
    except Exception as e:
        return False, "No se pudo comprobar Telegram ahora."


def _html_escape(value):
    return (str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;"))


def build_pick_alert_message(p, prefix="Nueva señal SHARK"):
    """Mensaje claro para Telegram. Nada de jerga API ni mercados técnicos."""
    try:
        get = p.get
    except Exception:
        get = lambda k, d=None: p[k] if k in p.keys() else d
    title = get("title", "Partido") or "Partido"
    league = get("league", "") or "Fútbol"
    choice = clear_bet_text(p)
    explanation = bet_simple_explanation(p)
    cuota = get("cuota", "") or get("odds_decimal", "") or "-"
    score = get("score", "") or "-"
    ev = get("ev", "") or "0"
    kickoff = get("kickoff_time", "") or "Horario pendiente"
    bookmaker = get("odds_bookmaker", "") or "Casa disponible"
    prof = professional_insight(p)
    risk = prof.get("risk", "Medio")
    stake = prof.get("stake_pct", 1)
    lines = [
        f"⚽ <b>{_html_escape(title)}</b>",
        f"🏆 {_html_escape(league)}",
        f"🕒 {_html_escape(kickoff)} hora España",
        "",
        f"✅ <b>Apuesta recomendada: {_html_escape(choice)}</b>",
        f"📌 {_html_escape(explanation)}",
        "",
        f"💰 Cuota: <b>{_html_escape(cuota)}</b> · {_html_escape(bookmaker)}",
        f"🦈 Confianza SHARK: <b>{_html_escape(score)}/100</b>",
        f"📈 Valor estimado: <b>{_html_escape(ev)}%</b>",
        f"⚠️ Riesgo: <b>{_html_escape(risk)}</b>",
        f"🎯 Stake sugerido: <b>{stake}% de banca</b>",
        "",
        "Juego responsable: no subas stake si no entiendes la apuesta.",
    ]
    return "\n".join(lines)



def quality_control_status():
    """Resumen admin de filtros SHARK sin enseñar tokens ni datos sensibles."""
    return {
        "min_score": SHARK_MIN_SCORE,
        "min_odds": MIN_ALLOWED_ODDS,
        "max_odds": MAX_ALLOWED_ODDS,
        "max_alerts_hour": MAX_ALERTS_PER_HOUR,
        "quiet_hours": TELEGRAM_QUIET_HOURS,
        "quiet_start": TELEGRAM_QUIET_START,
        "quiet_end": TELEGRAM_QUIET_END,
        "duplicate_matches": TELEGRAM_BLOCK_DUPLICATE_MATCHES,
        "mode": TELEGRAM_QUALITY_MODE,
    }


def telegram_alerts_sent_last_hour():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM alert_logs
            WHERE channel IN ('telegram','telegram_private')
            AND status='ok'
            AND datetime(created_at) >= datetime('now','-1 hour')
        """)
        n = int(cur.fetchone()[0] or 0)
        conn.close()
        return n
    except Exception:
        return 0


def telegram_is_quiet_now():
    if not TELEGRAM_QUIET_HOURS:
        return False
    try:
        h = int(madrid_now().hour)
        start = int(TELEGRAM_QUIET_START)
        end = int(TELEGRAM_QUIET_END)
        if start == end:
            return False
        if start < end:
            return start <= h < end
        return h >= start or h < end
    except Exception:
        return False


def pick_odds_float(p):
    raw = safe_row_get(p, "cuota", "") or safe_row_get(p, "odds_decimal", "") or 0
    try:
        return float(str(raw).replace(",", "."))
    except Exception:
        return 0.0


def pick_duplicate_alerted_recently(p, hours=12):
    """Evita repetir el mismo partido/mercado en Telegram durante unas horas."""
    if not TELEGRAM_BLOCK_DUPLICATE_MATCHES:
        return False
    try:
        title = (safe_row_get(p, "title", "") or "").strip().lower()
        pick = (safe_row_get(p, "pick", "") or "").strip().lower()
        if not title:
            return False
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM alert_logs
            WHERE channel IN ('telegram','telegram_private')
            AND status='ok'
            AND LOWER(COALESCE(title,'')) LIKE ?
            AND datetime(created_at) >= datetime('now', ?)
        """, (f"%{title[:40]}%", f"-{int(hours)} hours"))
        count = int(cur.fetchone()[0] or 0)
        conn.close()
        return count > 0
    except Exception:
        return False


def quality_rejection_reason(p, min_score=None, force=False):
    if force:
        return ""
    try:
        score = int(float(safe_row_get(p, "score", 0) or 0))
    except Exception:
        score = 0
    threshold = max(int(SHARK_MIN_SCORE), int(min_score if min_score is not None else TELEGRAM_ALERT_MIN_SCORE))
    if score < threshold:
        return f"Confianza baja ({score}/100). Mínimo actual: {threshold}/100."
    odds = pick_odds_float(p)
    if odds and odds < float(MIN_ALLOWED_ODDS):
        return f"Cuota demasiado baja ({odds})."
    if odds and odds > float(MAX_ALLOWED_ODDS):
        return f"Cuota demasiado alta/riesgosa ({odds})."
    if telegram_is_quiet_now():
        return "Horario silencioso activado."
    if telegram_alerts_sent_last_hour() >= int(MAX_ALERTS_PER_HOUR):
        return "Límite de alertas por hora alcanzado."
    if pick_duplicate_alerted_recently(p):
        return "Partido o señal ya avisada recientemente."
    if TELEGRAM_ALERT_ONLY_PREMIUM and str(safe_row_get(p, "premium", "0")) != "1":
        return "Solo se permiten señales premium."
    return ""

def should_alert_pick(p, min_score=None):
    return quality_rejection_reason(p, min_score=min_score) == ""


def fetch_pick_by_id(pick_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM picks WHERE id=?", (pick_id,))
    row = cur.fetchone(); conn.close()
    return row


def telegram_recent_auto_alert_count(minutes=30):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM alert_logs
            WHERE kind='odds_auto_pick' AND status='ok'
            AND datetime(created_at) >= datetime('now', ?)
        """, (f"-{int(minutes)} minutes",))
        n = int(cur.fetchone()[0] or 0)
        conn.close()
        return n
    except Exception:
        return 0


def send_pick_alert(pick_id, kind="new_pick", min_score=None, force=False):
    if not TELEGRAM_ALERT_NEW_PICKS and kind in ("new_pick", "odds_auto_pick"):
        return {"ok": False, "reason": "new_pick_alerts_disabled"}
    p = fetch_pick_by_id(pick_id)
    if not p:
        return {"ok": False, "reason": "pick_not_found"}
    reject_reason = quality_rejection_reason(p, min_score=min_score, force=force)
    if reject_reason:
        log_alert(kind, "Señal no enviada", reject_reason, "system", "filtered", {"pick_id": pick_id, "min_score": min_score or TELEGRAM_ALERT_MIN_SCORE})
        return {"ok": False, "reason": "filtered", "detail": reject_reason}
    title = "Nueva señal SHARK" if kind == "new_pick" else "Señal SHARK"
    # Canal general si está configurado + canales por membresía + mensajes privados conectados.
    platform_result = send_platform_alert(kind, title, build_pick_alert_message(p)) if TELEGRAM_CHAT_ID or DISCORD_WEBHOOK_URL else {"ok": False, "reason": "no_general_channel"}
    channel_result = send_pick_to_plan_channels(pick_id)
    user_result = send_pick_to_connected_users(pick_id)
    platform_result["channels_by_plan"] = channel_result
    platform_result["personalized"] = user_result
    try:
        platform_result["push"] = send_pick_push_notifications(pick_id)
    except Exception as _push_error:
        platform_result["push"] = {"ok": False, "reason": "push_error"}
    if channel_result.get("ok") or user_result.get("sent", 0) > 0:
        mark_pick_telegram_alerted(pick_id, "telegram_alerted_at")
    return platform_result


def send_pending_telegram_signals(limit=None):
    """Envía al canal Telegram las mejores señales reales que aún no se han avisado.
    Pensado para picks importados desde The Odds API, no solo picks creados a mano.
    """
    if not telegram_ready() or not TELEGRAM_AUTO_ALERT_ENGINE or not TELEGRAM_ALERT_NEW_PICKS:
        return {"ok": False, "reason": "telegram_not_ready_or_disabled", "sent": 0}
    limit = int(limit or TELEGRAM_AUTO_ALERT_MAX_PER_RUN or 3)
    already = telegram_recent_auto_alert_count(30)
    remaining = max(0, limit - already)
    if remaining <= 0:
        return {"ok": False, "reason": "recent_limit_reached", "sent": 0}
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT id FROM picks
            WHERE active=1
            AND COALESCE(telegram_channel_alerted_at,'')=''
            AND CAST(COALESCE(score,0) AS INTEGER) >= ?
            ORDER BY CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC
            LIMIT ?
        """, (int(TELEGRAM_ODDS_ALERT_MIN_SCORE), int(remaining)))
        ids = [int(r[0]) for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        return {"ok": False, "reason": f"db_error:{str(e)[:80]}", "sent": 0}
    sent = 0; results = []
    for pid in ids:
        res = send_pick_alert(pid, kind="odds_auto_pick", min_score=TELEGRAM_ODDS_ALERT_MIN_SCORE)
        results.append({"pick_id": pid, **(res or {})})
        if res and res.get("ok"):
            sent += 1
            mark_pick_telegram_alerted(pid, "telegram_channel_alerted_at")
    return {"ok": sent > 0, "sent": sent, "results": results}


def build_result_message(p, status, result_score="", plan="PRO"):
    label = status_label_es(status).upper()
    icon = "✅" if status == "ganado" else ("❌" if status == "perdido" else "➖")
    title = safe_row_get(p, "title", "Partido") or "Partido"
    choice = clear_bet_text(p)
    cuota = safe_row_get(p, "cuota", "-") or "-"
    plan = normalize_plan(plan, allow_admin=True)
    lines = [
        f"{icon} <b>Resultado SHARK {plan}</b>",
        f"⚽ <b>{_html_escape(title)}</b>",
        f"✅ Apuesta: <b>{_html_escape(choice)}</b>",
        f"💰 Cuota: <b>{_html_escape(cuota)}</b>",
        "",
        f"{icon} Estado: <b>{_html_escape(label)}</b>",
    ]
    if result_score:
        lines.append(f"📊 Marcador final: <b>{_html_escape(result_score)}</b>")
    if status == "ganado":
        lines.append("Buen cierre. Mantén disciplina y no subas el stake por emoción.")
    elif status == "perdido":
        lines.append("Rojo controlado. Lo importante es seguir la gestión de banca.")
    else:
        lines.append("Apuesta anulada. No cuenta como ganada ni perdida.")
    return "\n".join(lines)


def send_result_to_plan_channels(pick_id, status, result_score=""):
    if not TELEGRAM_SEND_TO_PLAN_CHANNELS:
        return {"ok": False, "reason": "plan_channels_disabled", "sent": 0}
    p = fetch_pick_by_id(pick_id)
    if not p:
        return {"ok": False, "reason": "pick_not_found", "sent": 0}
    used = set(); sent = 0; results = []
    for plan in ["FREE", "PRO", "ELITE"]:
        chat_id = telegram_channel_chat_id(plan)
        if not chat_id or chat_id in used:
            continue
        used.add(chat_id)
        body = build_result_message(p, status, result_score, plan)
        res = send_telegram_message(chat_id, body, kind="channel_result", title=f"Resultado {plan}", payload={"pick_id": pick_id, "plan": plan, "status": status})
        results.append({"plan": plan, **res})
        if res.get("ok"):
            sent += 1
    return {"ok": sent > 0, "sent": sent, "results": results}


def send_result_to_connected_users(pick_id, status, result_score=""):
    if not TELEGRAM_SEND_TO_CONNECTED_USERS or not ENABLE_PRO_ALERTS or not TELEGRAM_BOT_TOKEN:
        return {"ok": False, "reason": "disabled", "sent": 0}
    p = fetch_pick_by_id(pick_id)
    if not p:
        return {"ok": False, "reason": "pick_not_found", "sent": 0}
    sent = 0
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT * FROM users
            WHERE role='cliente' AND telegram_alerts_enabled=1
            AND telegram_chat_id IS NOT NULL AND telegram_chat_id!=''
        """)
        users = cur.fetchall(); conn.close()
    except Exception:
        users = []
    for u in users:
        body = build_result_message(p, status, result_score, safe_row_get(u, "plan", "FREE"))
        res = send_private_telegram(safe_row_get(u, "telegram_chat_id", ""), "Resultado de señal", body, {"user_id": safe_row_get(u, "id"), "pick_id": pick_id, "plan": safe_row_get(u, "plan"), "status": status})
        if res.get("ok"):
            sent += 1
    return {"ok": True, "sent": sent}


def send_result_alert(pick_id, status, result_score=""):
    if not TELEGRAM_ALERT_RESULTS:
        return {"ok": False, "reason": "result_alerts_disabled"}
    p = fetch_pick_by_id(pick_id)
    if not p:
        return {"ok": False, "reason": "pick_not_found"}
    body = build_result_message(p, status, result_score, "PRO")
    platform = send_platform_alert("result", "Resultado de señal SHARK", body) if TELEGRAM_CHAT_ID or DISCORD_WEBHOOK_URL else {"ok": False, "reason": "no_general_channel"}
    channel_result = send_result_to_plan_channels(pick_id, status, result_score)
    user_result = send_result_to_connected_users(pick_id, status, result_score)
    platform["channels_by_plan"] = channel_result
    platform["personalized"] = user_result
    return platform

@app.route("/")
def home():
    return render_template("index.html", commercial_plans=COMMERCIAL_PLANS)


@app.route("/version")
def version():
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "db_path": DB_PATH,
        "openai_enabled": bool(OPENAI_API_KEY),
        "ai_access": ai_access_for_current_user(),
        "openai_model": OPENAI_MODEL
    })


@app.route("/storage-check-v2")
@app.route("/storage-check")
def storage_check():
    parent = db_parent()
    writable = False
    error = ""
    try:
        test = os.path.join(parent, ".nemesis_write_test")
        with open(test, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test)
        writable = True
    except Exception as e:
        error = str(e)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM picks")
    picks = cur.fetchone()[0]
    conn.close()

    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "db_path": DB_PATH,
        "expected": "/data/database.db",
        "persistence": "OK" if DB_PATH == "/data/database.db" and writable else "CHECK",
        "parent_writable": writable,
        "users": users,
        "picks": picks,
        "error": error
    })


@app.route("/db-check")
def db_check():
    conn = get_db()
    cur = conn.cursor()
    users_cols = table_columns(cur, "users")
    picks_cols = table_columns(cur, "picks")
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    admins = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM picks")
    picks = cur.fetchone()[0]
    conn.close()
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "users_columns": users_cols,
        "picks_columns": picks_cols,
        "users": users,
        "admins": admins,
        "picks": picks
    })



@app.route("/manifest.json")
def manifest():
    return send_from_directory(app.root_path, "manifest.json", mimetype="application/manifest+json")


@app.route("/service-worker.js")
def service_worker():
    return send_from_directory(app.root_path, "service-worker.js", mimetype="application/javascript")

# ==========================================================
# CLIENT AUTH
# ==========================================================
@app.route("/registro", methods=["GET", "POST"])
def registro():
    error = None
    success = None
    selected_plan = normalize_plan(request.form.get("plan") or request.args.get("plan") or "FREE", allow_admin=False)

    plan_copy = {
        "FREE": {
            "title": "Cuenta FREE",
            "desc": "Entrada gratuita: picks básicos, banca e IA local.",
            "cta": "Crear cuenta FREE"
        },
        "PRO": {
            "title": "Cuenta PRO",
            "desc": "Plan principal: picks premium, métricas completas y GPT limitado diario.",
            "cta": "Crear cuenta PRO"
        },
        "ELITE": {
            "title": "Cuenta ELITE",
            "desc": "Nivel máximo: todo PRO, SHARK AI premium y prioridad en señales.",
            "cta": "Crear cuenta ELITE"
        },
    }

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        selected_plan = normalize_plan(request.form.get("plan") or selected_plan, allow_admin=False)

        if len(username) < 3:
            error = "El usuario debe tener al menos 3 caracteres."
        elif len(password) < 4:
            error = "La contraseña debe tener al menos 4 caracteres."
        else:
            try:
                conn = get_db()
                cur = conn.cursor()
                now_iso = madrid_iso_now()
                expires = add_months_madrid(1) if selected_plan in ("PRO", "ELITE") else ""
                source = "registro"
                cur.execute(
                    "INSERT INTO users(username,password,role,plan,balance,membership_source,membership_started_at,membership_expires_at,membership_auto_expire) VALUES(?,?,?,?,?,?,?,?,?)",
                    (username, hash_password(password), "cliente", selected_plan, 100, source, now_iso if selected_plan in ("PRO","ELITE") else "", expires, 1 if selected_plan in ("PRO","ELITE") else 0)
                )
                user_id = cur.lastrowid
                conn.commit()
                conn.close()

                # Alta directa: el usuario entra a su dashboard con el plan elegido en la tarjeta.
                session.clear()
                session["user"] = {
                    "id": user_id,
                    "username": username,
                    "role": "cliente",
                    "plan": selected_plan,
                    "balance": 100
                }
                session.modified = True
                return redirect(f"/clientes?welcome={selected_plan}")
            except sqlite3.IntegrityError:
                error = "Ese usuario ya existe. Prueba a iniciar sesión."
            except Exception:
                error = "No se pudo crear la cuenta."

    return render_template(
        "registro.html",
        error=error,
        success=success,
        selected_plan=selected_plan,
        plan_info=plan_copy.get(selected_plan, plan_copy["FREE"])
    )


@app.route("/cliente-login", methods=["GET", "POST"])
def cliente_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=? AND role!='admin'",
            (username, hash_password(password))
        )
        user = cur.fetchone()
        conn.close()

        if user:
            try:
                conn2 = get_db(); cur2 = conn2.cursor()
                cur2.execute("UPDATE users SET last_login_at=?, last_seen_at=? WHERE id=?", (madrid_iso_now(), madrid_iso_now(), user["id"]))
                cur2.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)", (user["id"], user["username"], "login", "Inicio de sesión cliente", madrid_iso_now()))
                conn2.commit(); conn2.close()
            except Exception:
                pass
            session.clear()
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "plan": user["plan"],
                "balance": user["balance"]
            }
            return redirect("/clientes")

        error = "Usuario o contraseña incorrectos."

    return render_template("login_cliente.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ==========================================================
# CLIENT AREA
# ==========================================================
def get_user_dashboard(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM picks
        WHERE COALESCE(active,1)=1
        """ + real_only_clause() + football_priority_clause(default_only=True) + """
        ORDER BY
        """ + football_order_sql() + """
        CASE UPPER(COALESCE(live_status,''))
          WHEN 'EN DIRECTO' THEN 0
          WHEN 'LIVE' THEN 0
          WHEN 'PROGRAMADO' THEN 1
          ELSE 2
        END,
        CASE WHEN COALESCE(kickoff_time,'')='' THEN 1 ELSE 0 END,
        kickoff_time ASC,
        CAST(COALESCE(score,0) AS INTEGER) DESC,
        id DESC
        LIMIT 12
    """)
    picks = cur.fetchall()
    cur.execute("""
    SELECT up.*, p.league, p.title, p.pick, p.cuota, p.ev, p.score, p.premium
    FROM user_picks up
    LEFT JOIN picks p ON p.id = up.pick_id
    WHERE up.user_id=?
    ORDER BY up.id DESC
    LIMIT 50
    """, (user_id,))
    saved = cur.fetchall()
    conn.close()

    total_saved = len(saved)
    total_staked = sum(float(r["amount"] or 0) for r in saved)
    pending_risk = sum(float(r["amount"] or 0) for r in saved if (r["status"] or "pendiente").lower() == "pendiente")
    settled_stake = sum(float(r["amount"] or 0) for r in saved if (r["status"] or "pendiente").lower() != "pendiente")
    total_profit = sum(float(r["profit"] or 0) for r in saved if (r["status"] or "pendiente").lower() != "pendiente")
    roi = (total_profit / settled_stake * 100) if settled_stake > 0 else 0
    stats = {
        "total_saved": total_saved,
        "total_staked": total_staked,
        "pending_risk": pending_risk,
        "settled_stake": settled_stake,
        "total_profit": total_profit,
        "roi": roi,
    }
    return picks, saved, stats


@app.route("/clientes")
@app.route("/dashboard")
def clientes():
    auto_refresh_real_live_data(force=False)
    auto_settle_and_notify_finished_picks()
    gate = require_user()
    if gate:
        return gate

    user = current_user()
    picks, saved, stats = get_user_dashboard(user["id"])
    roi_summary = enhanced_roi_summary(user["id"])
    favorites = user_favorite_ids(user["id"])
    return render_template("cliente.html", user=user, picks=picks, saved=saved, stats=stats, roi_summary=roi_summary, sport_status=get_sport_watchlist_status(force=False), live_snapshot=live_results_snapshot(), favorite_ids=favorites, next_step=client_next_step(user))


@app.route("/cliente/bankroll", methods=["POST"])
def update_bankroll():
    gate = require_user()
    if gate:
        return gate

    raw = (request.form.get("balance") or request.form.get("bankroll") or request.form.get("banca") or "100")
    try:
        # Admite formato europeo: 1.000,50 € o 1000,50
        cleaned = str(raw).replace("€", "").replace(" ", "").strip()
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", ".")
        balance = round(float(cleaned), 2)
        if balance < 0:
            balance = 0
    except Exception:
        balance = 100.00

    user = current_user()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance=? WHERE id=?", (balance, user["id"]))
    conn.commit()
    conn.close()

    # Refresca sesión inmediatamente para que al volver al dashboard se vea actualizado.
    session["user"] = dict(user)
    session["user"]["balance"] = balance
    session.modified = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"ok": True, "balance": balance, "currency": "EUR", "symbol": "€"})

    return redirect("/clientes?bankroll=updated")



@app.route("/cliente/preferencias", methods=["POST"])
def update_client_preferences():
    gate = require_user()
    if gate:
        return gate
    user = current_user()
    risk = (request.form.get("risk_preference") or "medio").strip().lower()
    sport = (request.form.get("favorite_sport") or "futbol").strip().lower()
    comp = (request.form.get("favorite_competition") or "").strip()[:80]
    if risk not in ("conservador", "medio", "agresivo"):
        risk = "medio"
    if sport not in ("futbol", "basket", "todos"):
        sport = "futbol"
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET risk_preference=?, favorite_sport=?, favorite_competition=? WHERE id=?", (risk, sport, comp, user["id"]))
    conn.commit(); conn.close()
    return redirect("/clientes#perfil")

@app.route("/guardar-pick/<int:pick_id>", methods=["POST"])
def guardar_pick(pick_id):
    gate = require_user()
    if gate:
        return gate

    user = current_user()
    plan = normalize_plan(user.get("plan"), allow_admin=(user.get("role") == "admin"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT premium FROM picks WHERE id=?", (pick_id,))
    pick_row = cur.fetchone()
    if not pick_row:
        conn.close()
        return redirect("/clientes?save_error=missing")
    if str(pick_row["premium"]) == "1" and plan == "FREE":
        conn.close()
        return redirect("/clientes?upgrade=PRO")

    try:
        amount = float(str(request.form.get("amount", "0")).replace(",", "."))
    except Exception:
        amount = 0
    if amount < 0:
        amount = 0

    cur.execute("INSERT INTO user_picks(user_id,pick_id,amount,status,profit) VALUES(?,?,?,?,?)",
                (user["id"], pick_id, amount, "pendiente", 0))
    conn.commit()
    conn.close()
    return redirect("/clientes?saved=1")


@app.route("/cliente/pick/<int:saved_id>/delete", methods=["POST"])
def cliente_pick_delete(saved_id):
    gate = require_user()
    if gate:
        return gate

    user = current_user()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM user_picks WHERE id=? AND user_id=?", (saved_id, user["id"]))
    conn.commit()
    conn.close()
    return redirect("/clientes")


@app.route("/api/cliente-stats")
def api_cliente_stats():
    gate = require_user()
    if gate:
        return jsonify({"ok": False, "error": "login_required"}), 401

    user = current_user()
    picks, saved, stats = get_user_dashboard(user["id"])
    return jsonify({
        "ok": True,
        "user": {"username": user["username"], "plan": user["plan"], "balance": user["balance"]},
        "stats": stats,
        "saved_picks": [dict(r) for r in saved[:20]],
    })


# ==========================================================
# PICKS / PARTIDOS
# ==========================================================
@app.route("/api/cliente-performance")
def api_cliente_performance():
    gate = require_user()
    if gate:
        return jsonify({"ok": False, "error": "login_required"}), 401

    user = current_user()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT created_at, amount, status, profit
    FROM user_picks
    WHERE user_id=?
    ORDER BY id ASC
    """, (user["id"],))
    rows = cur.fetchall()
    conn.close()

    cumulative = 0.0
    points = []
    for idx, r in enumerate(rows, start=1):
        status = (r["status"] or "pendiente").lower()
        if status != "pendiente":
            cumulative += float(r["profit"] or 0)
        points.append({
            "n": idx,
            "date": r["created_at"],
            "profit": round(cumulative, 2),
            "stake": float(r["amount"] or 0),
            "status": status
        })

    return jsonify({"ok": True, "currency": "EUR", "points": points})


@app.route("/api/roi-summary")
def api_roi_summary():
    auto_settle_and_notify_finished_picks()
    gate = require_user()
    if gate:
        return jsonify({"ok": False, "error": "login_required"}), 401
    user = current_user()
    summary = enhanced_roi_summary(user["id"])
    summary["advice"] = roi_advice(summary)
    trust = user_trust_profile(user["id"])
    return jsonify({"ok": True, "currency": "EUR", "summary": summary, "trust": trust})


@app.route("/api/live-results")
def api_live_results():
    if not current_user():
        return jsonify({"ok": False, "error": "login_required"}), 401
    auto_refresh_real_live_data(force=False)
    result = auto_settle_and_notify_finished_picks()
    return jsonify({"ok": True, "settlement": result, "snapshot": live_results_snapshot(limit=12)})

@app.route("/picks")
def picks():
    auto_refresh_real_live_data(force=False)
    q = request.args.get("q", "").strip().lower()
    sport_filter = request.args.get("sport", "football").strip().lower()
    date_filter = request.args.get("date", "").strip().lower()
    league_filter = request.args.get("league", "").strip().lower()
    conn = get_db()
    cur = conn.cursor()
    where = " WHERE active=1 " + real_only_clause()
    params = []
    if sport_filter not in ("all", "todos") and not any(x in q for x in ["nba", "basket", "basketball"]):
        where += football_priority_clause(default_only=True)
    if q:
        where += " AND (LOWER(title) LIKE ? OR LOWER(league) LIKE ? OR LOWER(pick) LIKE ? OR LOWER(sport) LIKE ?)"
        like = f"%{q}%"; params += [like, like, like, like]
    if league_filter:
        where += " AND (LOWER(league) LIKE ? OR LOWER(sport) LIKE ?)"
        like = f"%{league_filter}%"; params += [like, like]
    if date_filter:
        today = madrid_date_today()
        if date_filter == "today":
            where += " AND substr(COALESCE(kickoff_time,''),1,10)=?"; params.append(today.isoformat())
        elif date_filter == "tomorrow":
            where += " AND substr(COALESCE(kickoff_time,''),1,10)=?"; params.append((today + timedelta(days=1)).isoformat())
        elif date_filter in ("dayafter", "pasado"):
            where += " AND substr(COALESCE(kickoff_time,''),1,10)=?"; params.append((today + timedelta(days=2)).isoformat())
        elif date_filter in ("week", "7d"):
            where += " AND substr(COALESCE(kickoff_time,''),1,10) BETWEEN ? AND ?"; params += [today.isoformat(), (today + timedelta(days=7)).isoformat()]
    sql = "SELECT * FROM picks " + where + " ORDER BY " + football_order_sql() + " CASE UPPER(COALESCE(live_status,'')) WHEN 'EN DIRECTO' THEN 0 WHEN 'LIVE' THEN 0 WHEN 'PROGRAMADO' THEN 1 ELSE 2 END, CASE WHEN COALESCE(kickoff_time,'')='' THEN 1 ELSE 0 END, kickoff_time ASC, CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC LIMIT 120"
    cur.execute(sql, params)
    picks = cur.fetchall(); conn.close()
    if not picks and ODDS_API_KEY:
        auto_refresh_real_live_data(force=True)
        conn=get_db(); cur=conn.cursor(); cur.execute(sql, params); picks=cur.fetchall(); conn.close()
    return render_template("picks.html", picks=picks, q=q, sport_filter=sport_filter, date_filter=date_filter, league_filter=league_filter)



@app.route("/clasificaciones")
def clasificaciones():
    if not current_user():
        return redirect("/cliente-login")
    force = request.args.get("refresh") == "1" and is_admin()
    refresh_status = refresh_football_standings(force=force) if (force or (ENABLE_STANDINGS and FOOTBALL_DATA_KEY and not standings_available())) else {"ok": True, "cached": True}
    q = request.args.get("q", "").strip().lower()
    groups = get_standings_groups(q)
    return render_template("clasificaciones.html", groups=groups, q=q, refresh_status=refresh_status, standings_status=standings_status())

@app.route("/api/standings")
def api_standings():
    if not current_user():
        return jsonify({"ok": False, "error": "login_required"}), 401
    force = request.args.get("refresh") == "1" and is_admin()
    refresh_status = refresh_football_standings(force=force) if force else {"ok": True, "cached": True}
    q = request.args.get("q", "").strip().lower()
    return jsonify({"ok": True, "status": standings_status(), "refresh": refresh_status, "groups": get_standings_groups(q)})

@app.route("/partidos")
def partidos():
    refresh_status = auto_refresh_real_live_data(force=False)
    q = request.args.get("q", "").strip().lower()
    date_filter = request.args.get("date", "").strip().lower()
    league_filter = request.args.get("league", "").strip().lower()
    sport_filter = request.args.get("sport", "football").strip().lower()
    conn = get_db(); cur = conn.cursor()
    base_where = """
        WHERE COALESCE(active,1)=1
          AND COALESCE(title,'')!=''
    """ + real_only_clause()
    params = []
    if sport_filter not in ("all", "todos") and not any(x in q for x in ["nba", "basket", "basketball"]):
        base_where += football_priority_clause(default_only=True)
    if q:
        base_where += """
          AND (LOWER(title) LIKE ? OR LOWER(league) LIKE ? OR LOWER(pick) LIKE ? OR LOWER(sport) LIKE ? OR LOWER(live_status) LIKE ?)
        """
        like = f"%{q}%"; params += [like, like, like, like, like]
    if league_filter:
        base_where += " AND (LOWER(league) LIKE ? OR LOWER(sport) LIKE ?)"
        like = f"%{league_filter}%"; params += [like, like]
    if date_filter:
        today = madrid_date_today()
        if date_filter == "today":
            base_where += " AND substr(COALESCE(kickoff_time,''),1,10)=?"; params.append(today.isoformat())
        elif date_filter == "tomorrow":
            base_where += " AND substr(COALESCE(kickoff_time,''),1,10)=?"; params.append((today + timedelta(days=1)).isoformat())
        elif date_filter in ("dayafter", "pasado"):
            base_where += " AND substr(COALESCE(kickoff_time,''),1,10)=?"; params.append((today + timedelta(days=2)).isoformat())
        elif date_filter in ("week", "7d"):
            base_where += " AND substr(COALESCE(kickoff_time,''),1,10) BETWEEN ? AND ?"; params += [today.isoformat(), (today + timedelta(days=7)).isoformat()]
    sql = """
        SELECT * FROM picks
    """ + base_where + """
        ORDER BY
""" + football_order_sql() + """
          CASE UPPER(COALESCE(live_status,''))
            WHEN 'EN DIRECTO' THEN 0
            WHEN 'LIVE' THEN 0
            WHEN 'DESCANSO' THEN 1
            WHEN 'PROGRAMADO' THEN 2
            ELSE 3
          END,
          CASE WHEN COALESCE(kickoff_time,'')='' THEN 1 ELSE 0 END,
          kickoff_time ASC,
          id DESC
        LIMIT 120
    """
    cur.execute(sql, params); picks = cur.fetchall(); conn.close()
    if not picks and ODDS_API_KEY:
        refresh_status = auto_refresh_real_live_data(force=True)
        conn=get_db(); cur=conn.cursor(); cur.execute(sql, params); picks=cur.fetchall(); conn.close()
    return render_template("partidos.html", picks=picks, q=q, sport_filter=sport_filter, date_filter=date_filter, league_filter=league_filter, refresh_status=refresh_status)



@app.route("/partido/<int:pick_id>")
def partido_detalle(pick_id):
    err = require_user()
    if err:
        return err
    auto_refresh_real_live_data(force=False)
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM picks WHERE id=? AND active=1 " + real_only_clause(), (pick_id,))
    pick = cur.fetchone()
    conn.close()
    if not pick:
        return render_template("error.html", error="Partido no disponible o mercado cerrado."), 404
    return render_template("partido_detalle.html", p=pick)

# ==========================================================
# HIDDEN ADMIN
# ==========================================================
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        # Admin oculto: acceso por usuario + contraseña.
        # En producción se configura desde Render Environment:
        # ADMIN_USER y ADMIN_PASSWORD.
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        password_hash = hash_password(password)

        user = None

        # Modo recomendado: credenciales desde variables de entorno.
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND role='admin' LIMIT 1", (ADMIN_USER,))
            user = cur.fetchone()
            if not user:
                cur.execute(
                    "INSERT OR IGNORE INTO users(username,password,role,plan,balance) VALUES(?,?,?,?,?)",
                    (ADMIN_USER, password_hash, "admin", "ADMIN", 100)
                )
                conn.commit()
                cur.execute("SELECT * FROM users WHERE username=? AND role='admin' LIMIT 1", (ADMIN_USER,))
                user = cur.fetchone()
            conn.close()

        # Compatibilidad: si ya existía un admin en SQLite, también permite usuario + contraseña del admin guardado.
        if not user:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM users WHERE username=? AND password=? AND role='admin' LIMIT 1",
                (username, password_hash)
            )
            user = cur.fetchone()
            conn.close()

        if user:
            try:
                conn2 = get_db(); cur2 = conn2.cursor()
                cur2.execute("UPDATE users SET last_login_at=?, last_seen_at=? WHERE id=?", (madrid_iso_now(), madrid_iso_now(), user["id"]))
                cur2.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)", (user["id"], user["username"], "login", "Inicio de sesión cliente", madrid_iso_now()))
                conn2.commit(); conn2.close()
            except Exception:
                pass
            session.clear()
            session["user"] = {
                "id": user["id"],
                "username": user["username"],
                "role": "admin",
                "plan": user["plan"],
                "balance": user["balance"]
            }
            return redirect("/admin")

        error = "Usuario o contraseña interna incorrectos."

    return render_template("login_admin.html", error=error)


def estimate_openai_cost(input_tokens, output_tokens):
    try:
        input_cost = (int(input_tokens or 0) / 1000000) * OPENAI_INPUT_COST_PER_1M
        output_cost = (int(output_tokens or 0) / 1000000) * OPENAI_OUTPUT_COST_PER_1M
        return round(input_cost + output_cost, 8)
    except Exception:
        return 0


def log_api_usage(model, endpoint, input_tokens, output_tokens, total_tokens):
    try:
        user = current_user() or {}
        cost = estimate_openai_cost(input_tokens, output_tokens)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO api_usage_logs(user_id,provider,model,endpoint,input_tokens,output_tokens,total_tokens,cost_usd)
        VALUES(?,?,?,?,?,?,?,?)
        """, (user.get("id"), "openai", model or OPENAI_MODEL, endpoint or "chat", int(input_tokens or 0), int(output_tokens or 0), int(total_tokens or 0), cost))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_api_spend_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT
      COALESCE(SUM(cost_usd),0) AS month_cost,
      COALESCE(SUM(total_tokens),0) AS month_tokens,
      COUNT(*) AS month_calls
    FROM api_usage_logs
    WHERE provider='openai' AND strftime('%Y-%m', created_at)=strftime('%Y-%m','now')
    """)
    month = cur.fetchone()
    cur.execute("""
    SELECT
      COALESCE(SUM(cost_usd),0) AS today_cost,
      COALESCE(SUM(total_tokens),0) AS today_tokens,
      COUNT(*) AS today_calls
    FROM api_usage_logs
    WHERE provider='openai' AND date(created_at)=date('now')
    """)
    today = cur.fetchone()
    cur.execute("""
    SELECT model, COUNT(*) AS calls, COALESCE(SUM(cost_usd),0) AS cost, COALESCE(SUM(total_tokens),0) AS tokens
    FROM api_usage_logs
    WHERE provider='openai' AND strftime('%Y-%m', created_at)=strftime('%Y-%m','now')
    GROUP BY model
    ORDER BY cost DESC
    LIMIT 5
    """)
    by_model = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT created_at,cost_usd,total_tokens,model,endpoint FROM api_usage_logs WHERE provider='openai' ORDER BY id DESC LIMIT 5")
    recent = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "configured": bool(OPENAI_API_KEY),
        "model": OPENAI_MODEL,
        "currency": "USD",
        "month_cost": float(month["month_cost"] or 0),
        "month_tokens": int(month["month_tokens"] or 0),
        "month_calls": int(month["month_calls"] or 0),
        "today_cost": float(today["today_cost"] or 0),
        "today_tokens": int(today["today_tokens"] or 0),
        "today_calls": int(today["today_calls"] or 0),
        "input_cost_per_1m": OPENAI_INPUT_COST_PER_1M,
        "output_cost_per_1m": OPENAI_OUTPUT_COST_PER_1M,
        "by_model": by_model,
        "recent": recent,
        "note": "Estimación en tiempo real basada en tokens consumidos por esta app."
    }




# ==========================================================
# LIVE + ODDS MANAGER
# ==========================================================
def env_bool(value):
    return str(value or "").lower() in ["1", "true", "yes", "on"]


def utc_now():
    return datetime.utcnow()


def iso_now():
    return utc_now().strftime("%Y-%m-%d %H:%M:%S")


def cache_get(cache_key):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT payload, expires_at FROM api_cache WHERE cache_key=?", (cache_key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        expires_at = row["expires_at"] or ""
        if expires_at:
            try:
                if datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S") < utc_now():
                    return None
            except Exception:
                return None
        return json.loads(row["payload"] or "{}")
    except Exception:
        return None


def cache_set(cache_key, provider, payload, ttl_minutes):
    try:
        fetched_at = iso_now()
        expires_at = (utc_now() + timedelta(minutes=int(ttl_minutes or API_CACHE_MINUTES))).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        INSERT OR REPLACE INTO api_cache(cache_key,provider,payload,fetched_at,expires_at)
        VALUES(?,?,?,?,?)
        """, (cache_key, provider, json.dumps(payload, ensure_ascii=False), fetched_at, expires_at))
        conn.commit()
        conn.close()
    except Exception:
        pass



def cache_age_seconds(cache_key):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT fetched_at FROM api_cache WHERE cache_key=?", (cache_key,))
        row = cur.fetchone(); conn.close()
        if not row or not row["fetched_at"]:
            return None
        return max(0, int((utc_now() - datetime.strptime(row["fetched_at"], "%Y-%m-%d %H:%M:%S")).total_seconds()))
    except Exception:
        return None

def cache_is_fresh(cache_key, max_age_seconds):
    age = cache_age_seconds(cache_key)
    return age is not None and age < int(max_age_seconds or 0)


def stability_acquire_lock(lock_key, ttl_seconds=None):
    """Candado simple en SQLite para evitar refrescos simultáneos que provoquen timeout."""
    ttl_seconds = int(ttl_seconds or API_REFRESH_LOCK_SECONDS)
    now = int(time.time())
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS api_locks(lock_key TEXT PRIMARY KEY, locked_at INTEGER DEFAULT 0, owner TEXT DEFAULT '')")
        cur.execute("SELECT locked_at FROM api_locks WHERE lock_key=?", (lock_key,))
        row = cur.fetchone()
        if row and now - int(row["locked_at"] or 0) < ttl_seconds:
            conn.close()
            return False
        cur.execute("INSERT OR REPLACE INTO api_locks(lock_key,locked_at,owner) VALUES(?,?,?)", (lock_key, now, APP_VERSION))
        conn.commit(); conn.close()
        return True
    except Exception:
        return True


def stability_release_lock(lock_key):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("DELETE FROM api_locks WHERE lock_key=?", (lock_key,))
        conn.commit(); conn.close()
    except Exception:
        pass


def prune_heavy_logs():
    """Evita que SQLite crezca demasiado y ralentice Render."""
    if not PRUNE_LOGS_ON_STARTUP:
        return {"ok": True, "skipped": True}
    report = {"ok": True, "alert_logs_deleted": 0, "api_logs_deleted": 0}
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("DELETE FROM alert_logs WHERE id NOT IN (SELECT id FROM alert_logs ORDER BY id DESC LIMIT ?)", (int(MAX_ALERT_LOG_ROWS),))
        report["alert_logs_deleted"] = cur.rowcount if cur.rowcount is not None else 0
        cur.execute("DELETE FROM api_usage_logs WHERE id NOT IN (SELECT id FROM api_usage_logs ORDER BY id DESC LIMIT ?)", (int(MAX_API_USAGE_LOG_ROWS),))
        report["api_logs_deleted"] = cur.rowcount if cur.rowcount is not None else 0
        conn.commit(); conn.close()
    except Exception as e:
        report = {"ok": False, "error": str(e)[:160]}
    return report


def stability_counts():
    out = {}
    try:
        conn=get_db(); cur=conn.cursor()
        for table in ["users", "picks", "user_picks", "alert_logs", "api_usage_logs", "api_cache", "push_subscriptions"]:
            try:
                cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
                out[table] = int(cur.fetchone()["c"] or 0)
            except Exception:
                out[table] = None
        conn.close()
    except Exception:
        pass
    return out

def light_live_snapshot():
    """Snapshot barato para clientes. Solo lee DB, no consulta APIs externas."""
    try:
        return live_results_snapshot(limit=max(3, int(LIVE_SNAPSHOT_LIMIT or 8)))
    except Exception:
        return {"live": [], "upcoming": [], "finished": [], "total": 0}

def log_external_api(provider, endpoint, units=1, meta=""):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO api_usage_logs(user_id,provider,model,endpoint,input_tokens,output_tokens,total_tokens,cost_usd)
        VALUES(?,?,?,?,?,?,?,?)
        """, (None, provider, meta[:120], endpoint[:250], 0, 0, int(units or 1), float(units or 1)))
        conn.commit()
        conn.close()
    except Exception:
        pass


def external_usage_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT provider, COUNT(*) AS calls, COALESCE(SUM(total_tokens),0) AS units
    FROM api_usage_logs
    WHERE provider IN ('thesportsdb','theoddsapi','apifootball') AND date(created_at)=date('now')
    GROUP BY provider
    """)
    today = {r["provider"]: {"calls": int(r["calls"] or 0), "units": int(r["units"] or 0)} for r in cur.fetchall()}
    cur.execute("""
    SELECT provider, COUNT(*) AS calls, COALESCE(SUM(total_tokens),0) AS units
    FROM api_usage_logs
    WHERE provider IN ('thesportsdb','theoddsapi','apifootball') AND strftime('%Y-%m', created_at)=strftime('%Y-%m','now')
    GROUP BY provider
    """)
    month = {r["provider"]: {"calls": int(r["calls"] or 0), "units": int(r["units"] or 0)} for r in cur.fetchall()}
    cur.execute("SELECT cache_key,provider,fetched_at,expires_at FROM api_cache ORDER BY fetched_at DESC LIMIT 8")
    cache_rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"today": today, "month": month, "cache": cache_rows}


def api_limits_ok(provider):
    stats = external_usage_stats()
    if provider == "thesportsdb":
        used = stats["today"].get("thesportsdb", {}).get("units", 0)
        return used < LIVE_DAILY_REQUEST_LIMIT
    if provider == "theoddsapi":
        used = stats["month"].get("theoddsapi", {}).get("units", 0)
        return used < ODDS_MONTHLY_CREDIT_LIMIT
    if provider == "apifootball":
        used = stats["today"].get("apifootball", {}).get("units", 0)
        return used < API_FOOTBALL_DAILY_REQUEST_LIMIT
    return True


def http_json(url, headers=None, timeout=None):
    timeout = int(timeout or HTTP_TIMEOUT_SECONDS)
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw or "{}"), dict(resp.headers)


def odds_sport_label(key):
    labels = {
        "soccer_fifa_world_cup": "Mundial FIFA",
        "soccer_uefa_european_championship": "Eurocopa",
        "soccer_conmebol_copa_america": "Copa América",
        "soccer_uefa_champs_league": "Champions League",
        "soccer_uefa_europa_league": "Europa League",
        "soccer_uefa_europa_conference_league": "Conference League",
        "soccer_spain_la_liga": "LaLiga",
        "soccer_epl": "Premier League",
        "soccer_italy_serie_a": "Serie A",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_portugal_primeira_liga": "Primeira Liga",
        "soccer_netherlands_eredivisie": "Eredivisie",
        "soccer_spain_segunda_division": "LaLiga Hypermotion",
        "soccer_efl_champ": "Championship",
        "soccer_usa_mls": "MLS",
        "soccer_mexico_ligamx": "Liga MX",
        "soccer_brazil_campeonato": "Brasileirão",
        "soccer_argentina_primera_division": "Argentina Primera",
        "basketball_nba": "NBA",
    }
    return labels.get(key, (key or "").replace("soccer_", "").replace("basketball_", "").replace("_", " ").title())


def sport_is_football(key):
    return str(key or "").startswith("soccer_")


def get_available_odds_sports(force=False):
    """Devuelve deportes activos de The Odds API.
    Esto prepara ligas y torneos para cuando empiecen: si The Odds API los activa,
    la app los mete automáticamente sin tocar código ni Render.
    """
    if not ODDS_API_KEY or not ENABLE_ODDS_API or not AUTO_FILTER_ACTIVE_SPORTS:
        return None
    cache_key = "theoddsapi:sports:active"
    cached = None if force else cache_get(cache_key)
    if cached and isinstance(cached.get("sports"), list):
        return cached.get("sports")
    try:
        url = f"https://api.the-odds-api.com/v4/sports/?apiKey={urllib.parse.quote(ODDS_API_KEY)}"
        data, headers = http_json(url, timeout=10)
        sports = data if isinstance(data, list) else []
        log_external_api("theoddsapi", "/v4/sports", 1, "active_sports")
        cache_set(cache_key, "theoddsapi", {"sports": sports}, ODDS_SPORTS_CACHE_MINUTES)
        return sports
    except Exception:
        return None


def get_active_odds_sport_keys(force=False):
    requested = list(dict.fromkeys([x for x in ODDS_SPORT_KEYS_RAW if x]))
    if SHOW_BASKETBALL_DEFAULT:
        requested += [x for x in BASKETBALL_SECONDARY_SPORT_KEYS if x not in requested]
    if FOOTBALL_FIRST:
        requested = sorted(requested, key=lambda k: (0 if sport_is_football(k) else 1, requested.index(k)))

    active_sports = get_available_odds_sports(force=force)
    if active_sports is None:
        return requested
    active_keys = {str(s.get("key") or "") for s in active_sports if s.get("active", True)}
    filtered = [k for k in requested if k in active_keys]
    # Si la API no devuelve alguna competición por estar fuera de temporada, queda en vigilancia
    # y se activará sola cuando aparezca en /v4/sports.
    return filtered or requested[:8]


def get_sport_watchlist_status(force=False):
    requested = list(dict.fromkeys([x for x in ODDS_SPORT_KEYS_RAW if x]))
    active_sports = get_available_odds_sports(force=force)
    active_keys = {str(s.get("key") or "") for s in active_sports} if active_sports else set()
    active = [k for k in requested if not active_keys or k in active_keys]
    waiting = [k for k in requested if active_keys and k not in active_keys]
    return {
        "active": [{"key": k, "label": odds_sport_label(k)} for k in active],
        "waiting": [{"key": k, "label": odds_sport_label(k)} for k in waiting],
        "football_first": FOOTBALL_FIRST,
        "auto_filter": AUTO_FILTER_ACTIVE_SPORTS,
        "basketball_default": SHOW_BASKETBALL_DEFAULT,
    }


def normalize_team_name(name):
    return (name or "").lower().replace("fc", "").replace("cf", "").replace("club", "").strip()


def split_match_title(title):
    title = title or ""
    for sep in [" vs ", " VS ", " v ", " - "]:
        if sep in title:
            a, b = title.split(sep, 1)
            return a.strip(), b.strip()
    return title.strip(), ""


def find_matching_pick(home, away):
    home_n = normalize_team_name(home)
    away_n = normalize_team_name(away)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id,title FROM picks")
    rows = cur.fetchall()
    conn.close()
    best = None
    for r in rows:
        title_n = normalize_team_name(r["title"])
        if home_n and away_n and home_n in title_n and away_n in title_n:
            best = r["id"]
            break
        if home_n and home_n in title_n:
            best = r["id"]
    return best


def refresh_thesportsdb_live(force=False):
    if not ENABLE_LIVE_API:
        return {"ok": False, "reason": "ENABLE_LIVE_API=false", "updated": 0}
    if not api_limits_ok("thesportsdb"):
        return {"ok": False, "reason": "daily_limit_reached", "updated": 0}
    cache_key = f"live:{LIVE_PROVIDER}:{THESPORTSDB_SPORT}"
    cached = None if force else cache_get(cache_key)
    if cached:
        return {"ok": True, "cached": True, "updated": 0, "events": len(cached.get("events") or [])}

    # TheSportsDB v2 livescore endpoint. API key is optional for free/premium depending on account.
    sport_url = urllib.parse.quote(THESPORTSDB_SPORT)
    url = f"https://www.thesportsdb.com/api/v2/json/livescore/{sport_url}"
    headers = {}
    if THESPORTSDB_KEY:
        headers["X-API-KEY"] = THESPORTSDB_KEY
    data, _headers = http_json(url, headers=headers)
    log_external_api("thesportsdb", "/api/v2/json/livescore", 1, THESPORTSDB_SPORT)
    cache_set(cache_key, "thesportsdb", data, LIVE_CACHE_MINUTES)

    events = data.get("events") or data.get("livescores") or data.get("event") or []
    if isinstance(events, dict):
        events = [events]
    updated = 0
    conn = get_db()
    cur = conn.cursor()
    for ev in events:
        home = ev.get("strHomeTeam") or ev.get("homeTeam") or ev.get("strHome") or ""
        away = ev.get("strAwayTeam") or ev.get("awayTeam") or ev.get("strAway") or ""
        pick_id = find_matching_pick(home, away)
        if not pick_id:
            continue
        home_score = ev.get("intHomeScore") or ev.get("homeScore") or ev.get("intHome") or ""
        away_score = ev.get("intAwayScore") or ev.get("awayScore") or ev.get("intAway") or ""
        minute = ev.get("strProgress") or ev.get("strStatus") or ev.get("intMinute") or ev.get("strTime") or ""
        status_raw = str(ev.get("strStatus") or ev.get("status") or minute or "EN DIRECTO").upper()
        if "FT" in status_raw or "FIN" in status_raw or "MATCH FINISHED" in status_raw:
            live_status = "FINALIZADO"
        elif "HT" in status_raw or "HALF" in status_raw:
            live_status = "DESCANSO"
        else:
            live_status = "EN DIRECTO"
        score = f"{home_score} - {away_score}" if str(home_score) != "" and str(away_score) != "" else ""
        cur.execute("""
        UPDATE picks SET live_status=?, live_score=?, live_minute=?, live_updated_at=?, external_event_id=?
        WHERE id=?
        """, (live_status, score, str(minute), iso_now(), str(ev.get("idEvent") or ev.get("idLiveScore") or ""), pick_id))
        updated += cur.rowcount
    conn.commit()
    conn.close()
    return {"ok": True, "cached": False, "updated": updated, "events": len(events)}


def best_odds_from_event(event):
    """Elige la mejor oportunidad por perfil SHARK, no simplemente la cuota más alta."""
    best = None
    best_rank = -999
    bookmakers = event.get("bookmakers") or []
    commence = event.get("commence_time") or ""
    sport_key = event.get("sport_key") or ""
    for book in bookmakers[:6]:
        for market in book.get("markets") or []:
            mkey = market.get("key")
            if mkey not in ["h2h", "totals", "spreads"]:
                continue
            for outcome in market.get("outcomes") or []:
                price = outcome.get("price")
                try:
                    price_f = float(price)
                except Exception:
                    continue
                score, ev, risk = shark_score_from_odds(price_f, mkey, commence, sport_key)
                # Prioriza score/EV, penaliza cuotas demasiado locas para que no todo sea alto riesgo.
                rank = score + (ev * 2) - (8 if price_f >= 3.8 else 0)
                if rank > best_rank:
                    best_rank = rank
                    best = {
                        "price": price_f,
                        "bookmaker": book.get("title") or book.get("key") or "Bookmaker",
                        "market": mkey,
                        "name": outcome.get("name") or "",
                        "score": score,
                        "ev": ev,
                        "risk": risk,
                    }
    return best

def pick_exists_for_event(event_id, title):
    conn = get_db()
    cur = conn.cursor()
    if event_id:
        cur.execute("SELECT id FROM picks WHERE external_event_id=? LIMIT 1", (str(event_id),))
        row = cur.fetchone()
        if row:
            conn.close()
            return row["id"]
    cur.execute("SELECT id FROM picks WHERE LOWER(title)=LOWER(?) LIMIT 1", (title or "",))
    row = cur.fetchone()
    conn.close()
    return row["id"] if row else None


def create_or_update_pick_from_odds_event(ev, sport_key=""):
    """Crea o actualiza picks reales desde The Odds API.
    Mantiene historial y no genera partidos falsos.
    """
    home = ev.get("home_team") or ""
    away = ev.get("away_team") or ""
    if not home or not away:
        return 0

    title = f"{home} vs {away}"
    event_id = str(ev.get("id") or "")
    league = ev.get("sport_title") or sport_key or "Evento real"
    odds = best_odds_from_event(ev)

    pick_text = "Mercado principal disponible"
    cuota = ""
    bookmaker = ""
    market = ""
    score_val = 68
    ev_val = "0"

    if odds:
        name = odds.get("name") or ""
        market = odds.get("market") or ""
        cuota = str(odds.get("price") or "")
        bookmaker = odds.get("bookmaker") or ""
        score_val = int(odds.get("score") or 68)
        ev_val = str(odds.get("ev") or 0)
        if market == "h2h" and name:
            pick_text = f"{name} gana"
        elif market == "totals" and name:
            pick_text = f"Total de puntos/goles: {name}"
        elif market == "spreads" and name:
            pick_text = f"Hándicap: {name}"

    premium_val = "1" if score_val >= SHARK_ENGINE_PREMIUM_SCORE else "0"
    commence = (ev.get("commence_time") or "")
    existing_id = pick_exists_for_event(event_id, title)

    conn = get_db()
    cur = conn.cursor()
    if existing_id:
        cur.execute("""
        UPDATE picks
        SET league=?, title=?, pick=COALESCE(NULLIF(pick,''), ?), cuota=COALESCE(NULLIF(cuota,''), ?), ev=?, score=?, premium=?, odds_decimal=?, odds_bookmaker=?, odds_market=?, odds_updated_at=?, kickoff_time=?, external_event_id=COALESCE(NULLIF(external_event_id,''), ?), source='theoddsapi', active=1, live_status=COALESCE(NULLIF(live_status,''),'PROGRAMADO')
        WHERE id=?
        """, (
            league, title, pick_text, cuota, ev_val, str(score_val), premium_val,
            cuota, bookmaker, market, iso_now(), commence, event_id, existing_id
        ))
    else:
        cur.execute("""
        INSERT INTO picks(league,title,pick,cuota,ev,score,premium,live_status,live_score,live_minute,kickoff_time,odds_decimal,odds_bookmaker,odds_market,odds_updated_at,external_event_id,sport,source,active)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
        """, (
            league, title, pick_text, cuota, ev_val, str(score_val), premium_val, "PROGRAMADO", "", "", commence,
            cuota, bookmaker, market, iso_now(), event_id, sport_key, "theoddsapi"
        ))
        new_pick_id = cur.lastrowid
    conn.commit()
    conn.close()
    # V46.1: si el pick nace desde The Odds API también puede avisar Telegram.
    # Límite suave para no llenar el canal con decenas de mensajes en un refresh.
    try:
        if (TELEGRAM_AUTO_SEND_DURING_REFRESH or not PERFORMANCE_SAFE_MODE) and not existing_id and TELEGRAM_AUTO_ALERT_ENGINE and TELEGRAM_ALERT_NEW_PICKS and int(score_val or 0) >= TELEGRAM_ODDS_ALERT_MIN_SCORE:
            if telegram_recent_auto_alert_count(30) < int(TELEGRAM_AUTO_ALERT_MAX_PER_RUN or 3):
                send_pick_alert(new_pick_id, "odds_auto_pick", min_score=TELEGRAM_ODDS_ALERT_MIN_SCORE)
    except Exception:
        pass
    return 1

def hide_demo_picks_when_real_data_exists():
    """Evita que salgan demos tipo Lakers/Warriors cuando ya hay partidos reales con external_event_id.
    No elimina picks guardados por usuarios.
    """
    demo_titles = [
        "partido real disponible",
        "partido real disponible",
        "partido real disponible",
        "partido real disponible",
    ]
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM picks WHERE external_event_id IS NOT NULL AND external_event_id!=''")
        real_count = int(cur.fetchone()[0] or 0)
        if real_count <= 0:
            conn.close()
            return 0
        qmarks = ",".join(["?"] * len(demo_titles))
        cur.execute(f"""
        DELETE FROM picks
        WHERE title IN ({qmarks})
        AND (external_event_id IS NULL OR external_event_id='')
        AND id NOT IN (SELECT DISTINCT pick_id FROM user_picks WHERE pick_id IS NOT NULL)
        """, demo_titles)
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception:
        return 0


def auto_refresh_real_live_data(force=False, public=False):
    """Refresh estable V54.
    - Cliente/public: respuesta rápida desde DB/cache, sin llamar APIs externas.
    - Admin/force: refresca proveedores con cooldown, lock y límites.
    """
    if public and PERFORMANCE_SAFE_MODE and not force:
        return {"ok": True, "safe_mode": True, "cached": True, "snapshot": light_live_snapshot(), "reason": "client_safe_snapshot"}
    if not LIVE_AUTO_REFRESH and not force:
        return {"ok": False, "reason": "LIVE_AUTO_REFRESH=false"}
    refresh_cache_key = "perf:admin_refresh_guard" if force else "perf:auto_refresh_guard"
    cooldown = ADMIN_REFRESH_COOLDOWN_SECONDS if force else PUBLIC_LIVE_REFRESH_COOLDOWN_SECONDS
    if PERFORMANCE_SAFE_MODE and not force and cache_is_fresh(refresh_cache_key, cooldown):
        return {"ok": True, "cached": True, "snapshot": light_live_snapshot(), "reason": "refresh_cooldown"}
    lock_key = "refresh:admin" if force else "refresh:auto"
    if STABILITY_HARD_MODE and not stability_acquire_lock(lock_key, API_REFRESH_LOCK_SECONDS):
        return {"ok": True, "locked": True, "cached": True, "snapshot": light_live_snapshot(), "reason": "refresh_already_running"}
    cache_set(refresh_cache_key, "perf", {"started_at": iso_now()}, max(1, int(cooldown/60)))
    result = {"ok": True, "live": None, "odds": None, "api_football_live": None, "api_football_upcoming": None, "demo_hidden": 0}
    if ENABLE_API_FOOTBALL and API_FOOTBALL_KEY and not PERFORMANCE_SAFE_MODE:
        try:
            result["api_football_live"] = refresh_api_football_live(force=force)
        except Exception as e:
            result["api_football_live"] = {"ok": False, "reason": str(e)}
        try:
            result["api_football_upcoming"] = refresh_api_football_upcoming(force=force)
        except Exception as e:
            result["api_football_upcoming"] = {"ok": False, "reason": str(e)}
    if ENABLE_ODDS_API and ODDS_API_KEY:
        try:
            result["odds"] = refresh_theoddsapi(force=force, notify=bool(force or TELEGRAM_AUTO_SEND_DURING_REFRESH))
        except Exception as e:
            result["odds"] = {"ok": False, "reason": str(e)}
    if ENABLE_LIVE_API and not PERFORMANCE_SAFE_MODE:
        try:
            result["live"] = refresh_thesportsdb_live(force=force)
        except Exception as e:
            result["live"] = {"ok": False, "reason": str(e)}
    if SHARK_ENGINE_AUTO_SAVE and ENABLE_ODDS_API and ODDS_API_KEY and not PERFORMANCE_SAFE_MODE:
        try:
            engine = shark_auto_engine_fetch(force=force)
            result["shark_engine"] = {"ok": engine.get("ok"), "detected": len(engine.get("picks") or []), "saved": save_shark_engine_picks_to_db(engine.get("picks") or [])}
        except Exception as e:
            result["shark_engine"] = {"ok": False, "reason": str(e)}
    result["demo_hidden"] = hide_demo_picks_when_real_data_exists()
    result["snapshot"] = light_live_snapshot()
    if STABILITY_HARD_MODE:
        stability_release_lock(lock_key)
    return result


def api_football_headers():
    return {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": API_FOOTBALL_KEY,
    }


def api_football_get(path, params=None):
    query = urllib.parse.urlencode(params or {})
    url = f"https://{API_FOOTBALL_HOST}{path}"
    if query:
        url += "?" + query
    data, headers = http_json(url, headers=api_football_headers(), timeout=14)
    log_external_api("apifootball", path, 1, query[:120])
    return data or {}, headers


def normalize_api_football_fixture(item):
    fixture = item.get("fixture") or {}
    league = item.get("league") or {}
    teams = item.get("teams") or {}
    goals = item.get("goals") or {}
    status = fixture.get("status") or {}
    home = (teams.get("home") or {}).get("name") or ""
    away = (teams.get("away") or {}).get("name") or ""
    elapsed = status.get("elapsed")
    short_status = (status.get("short") or "").upper()
    status_map = {
        "NS": "PROGRAMADO", "TBD": "PROGRAMADO",
        "1H": "EN DIRECTO", "2H": "EN DIRECTO", "ET": "EN DIRECTO", "BT": "EN DIRECTO", "P": "EN DIRECTO",
        "HT": "DESCANSO", "FT": "FINALIZADO", "AET": "FINALIZADO", "PEN": "FINALIZADO",
        "SUSP": "SUSPENDIDO", "PST": "SUSPENDIDO", "CANC": "SUSPENDIDO", "ABD": "SUSPENDIDO",
    }
    live_status = status_map.get(short_status, status.get("long") or "PROGRAMADO")
    score = ""
    if goals.get("home") is not None or goals.get("away") is not None:
        score = f"{goals.get('home') if goals.get('home') is not None else 0} - {goals.get('away') if goals.get('away') is not None else 0}"
    minute = f"{elapsed}'" if elapsed else ""
    kickoff = (fixture.get("date") or "")[:16].replace("T", " ")
    return {
        "event_id": str(fixture.get("id") or ""),
        "league": league.get("name") or "Fútbol",
        "sport": "football",
        "title": f"{home} vs {away}".strip(" vs "),
        "home": home,
        "away": away,
        "live_status": live_status,
        "live_score": score,
        "live_minute": minute,
        "kickoff_time": kickoff,
        "source": "api_football",
    }


def upsert_real_match_event(match, create_if_missing=True):
    if not match.get("event_id") or not match.get("title"):
        return 0
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM picks WHERE external_event_id=? LIMIT 1", (match["event_id"],))
    row = cur.fetchone()
    if row:
        cur.execute("""
        UPDATE picks
        SET league=?, title=?, sport=?, live_status=?, live_score=?, live_minute=?, kickoff_time=?, live_updated_at=?, source=?, active=1
        WHERE id=?
        """, (match["league"], match["title"], match["sport"], match["live_status"], match["live_score"], match["live_minute"], match["kickoff_time"], iso_now(), match["source"], row["id"]))
        changed = cur.rowcount
    elif create_if_missing:
        cur.execute("""
        INSERT INTO picks(league,title,pick,cuota,ev,score,premium,live_status,live_score,live_minute,kickoff_time,external_event_id,sport,source,active)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
        """, (match["league"], match["title"], "Pendiente de valor SHARK", "", "", "0", "0", match["live_status"], match["live_score"], match["live_minute"], match["kickoff_time"], match["event_id"], match["sport"], match["source"]))
        changed = 1
    else:
        changed = 0
    conn.commit()
    conn.close()
    return changed


def refresh_api_football_live(force=False):
    if not ENABLE_API_FOOTBALL:
        return {"ok": False, "reason": "ENABLE_API_FOOTBALL=false", "updated": 0}
    if not API_FOOTBALL_KEY:
        return {"ok": False, "reason": "missing_API_FOOTBALL_KEY", "updated": 0}
    if not api_limits_ok("apifootball"):
        return {"ok": False, "reason": "daily_limit_reached", "updated": 0}
    cache_key = "apifootball:fixtures:live"
    cached = None if force else cache_get(cache_key)
    if cached:
        return {"ok": True, "cached": True, "updated": 0, "events": len(cached.get("response") or [])}
    data, _headers = api_football_get("/fixtures", {"live": "all"})
    cache_set(cache_key, "apifootball", data, LIVE_CACHE_MINUTES)
    updated = 0
    for item in data.get("response") or []:
        updated += upsert_real_match_event(normalize_api_football_fixture(item), create_if_missing=True)
    return {"ok": True, "cached": False, "updated": updated, "events": len(data.get("response") or [])}


def refresh_api_football_upcoming(force=False):
    """Carga partidos reales de los próximos días, no solo live.
    V31.5: usa calendario por fecha para que el cliente vea tarjetas de próximos días.
    """
    if not ENABLE_API_FOOTBALL:
        return {"ok": False, "reason": "ENABLE_API_FOOTBALL=false", "updated": 0}
    if not API_FOOTBALL_KEY:
        return {"ok": False, "reason": "missing_API_FOOTBALL_KEY", "updated": 0}
    if not api_limits_ok("apifootball"):
        return {"ok": False, "reason": "daily_limit_reached", "updated": 0}

    total_updated = 0
    total_events = 0
    results = []
    today_dt = utc_now()
    days = max(1, min(API_FOOTBALL_DAYS_AHEAD, 10))

    for league_id in API_FOOTBALL_LEAGUES[:9]:
        league_updated = 0
        league_events = 0
        for offset in range(days):
            day = (today_dt + timedelta(days=offset)).strftime("%Y-%m-%d")
            cache_key = f"apifootball:fixtures:{league_id}:{API_FOOTBALL_SEASON}:{day}"
            cached = None if force else cache_get(cache_key)
            if cached:
                events = len(cached.get("response") or [])
                league_events += events
                total_events += events
                continue

            params = {"league": league_id, "season": API_FOOTBALL_SEASON, "date": day}
            data, _headers = api_football_get("/fixtures", params)
            cache_set(cache_key, "apifootball", data, ODDS_CACHE_MINUTES)
            events = len(data.get("response") or [])
            league_events += events
            total_events += events
            for item in data.get("response") or []:
                league_updated += upsert_real_match_event(normalize_api_football_fixture(item), create_if_missing=True)

        # Fallback por liga: si el calendario por fecha viene vacío, pide próximos 15.
        if league_events == 0:
            cache_key = f"apifootball:fixtures_next:{league_id}:{API_FOOTBALL_SEASON}"
            cached = None if force else cache_get(cache_key)
            if cached:
                data = cached
            else:
                data, _headers = api_football_get("/fixtures", {"league": league_id, "season": API_FOOTBALL_SEASON, "next": 15})
                cache_set(cache_key, "apifootball", data, ODDS_CACHE_MINUTES)
            events = len(data.get("response") or [])
            league_events += events
            total_events += events
            for item in data.get("response") or []:
                league_updated += upsert_real_match_event(normalize_api_football_fixture(item), create_if_missing=True)

        total_updated += league_updated
        results.append({"league": league_id, "events": league_events, "updated": league_updated})

    return {"ok": True, "updated": total_updated, "events": total_events, "days_ahead": days, "season": API_FOOTBALL_SEASON, "leagues": results}

def refresh_theoddsapi(force=False, notify=True):
    if not ENABLE_ODDS_API:
        return {"ok": False, "reason": "ENABLE_ODDS_API=false", "updated": 0}
    if not ODDS_API_KEY:
        return {"ok": False, "reason": "missing_ODDS_API_KEY", "updated": 0}
    if not api_limits_ok("theoddsapi"):
        return {"ok": False, "reason": "monthly_credit_limit_reached", "updated": 0}

    total_updated = 0
    results = []
    for sport_key in get_active_odds_sport_keys(force=force)[:max(1, int(MAX_SPORTS_PER_REFRESH or 6))]:
        if not api_limits_ok("theoddsapi"):
            break
        cache_key = f"odds:{sport_key}"
        cached = None if force else cache_get(cache_key)
        if cached:
            payload = cached
            events = (payload.get("events") or [])[:MAX_EVENTS_PER_SPORT]
            conn = get_db()
            cur = conn.cursor()
            updated = 0
            for ev in events:
                try:
                    updated += int(create_or_update_pick_from_odds_event(ev, sport_key))
                except Exception:
                    pass
            conn.commit()
            conn.close()
            total_updated += updated
            results.append({"sport": sport_key, "cached": True, "events": len(events), "updated": updated})
            continue
        url = (
            f"https://api.the-odds-api.com/v4/sports/{urllib.parse.quote(sport_key)}/odds"
            f"?apiKey={urllib.parse.quote(ODDS_API_KEY)}&regions={urllib.parse.quote(ODDS_REGIONS)}&markets={urllib.parse.quote(ODDS_MARKETS)}&oddsFormat=decimal"
        )
        data, headers = http_json(url)
        if isinstance(data, list):
            payload = {"events": data}
        else:
            payload = data or {"events": []}
        remaining = headers.get("x-requests-remaining") or headers.get("X-Requests-Remaining") or ""
        used = headers.get("x-requests-used") or headers.get("X-Requests-Used") or ""
        log_external_api("theoddsapi", f"/v4/sports/{sport_key}/odds", 1, f"remaining:{remaining} used:{used}")
        cache_set(cache_key, "theoddsapi", payload, ODDS_CACHE_MINUTES)

        events = (payload.get("events") or [])[:MAX_EVENTS_PER_SPORT]
        conn = get_db()
        cur = conn.cursor()
        updated = 0
        for ev in events:
            home = ev.get("home_team") or ""
            away = ev.get("away_team") or ""
            pick_id = find_matching_pick(home, away)
            odds = best_odds_from_event(ev)
            if pick_id and odds:
                cur.execute("""
                UPDATE picks SET odds_decimal=?, odds_bookmaker=?, odds_market=?, odds_updated_at=?, external_event_id=COALESCE(NULLIF(external_event_id,''), ?)
                WHERE id=?
                """, (str(odds["price"]), odds["bookmaker"], odds["market"], iso_now(), str(ev.get("id") or ""), pick_id))
                updated += cur.rowcount
            else:
                try:
                    updated += int(create_or_update_pick_from_odds_event(ev, sport_key))
                except Exception:
                    pass
        conn.commit()
        conn.close()
        total_updated += updated
        results.append({"sport": sport_key, "cached": False, "events": len(events), "updated": updated, "remaining": remaining})
    telegram_batch = send_pending_telegram_signals() if (notify and TELEGRAM_AUTO_ALERT_ENGINE) else {"ok": False, "reason": "notify_disabled_for_refresh", "sent": 0}
    return {"ok": True, "updated": total_updated, "sports": results, "telegram": telegram_batch}



def normalize_team_key(name):
    txt = (name or "").lower()
    txt = txt.replace("fc", "").replace("cf", "").replace("club", "")
    txt = re.sub(r"[^a-z0-9áéíóúñü]+", " ", txt).strip()
    return txt


def football_data_get(path):
    if not FOOTBALL_DATA_KEY:
        return None, {}
    url = "https://api.football-data.org/v4" + path
    return http_json(url, headers={"X-Auth-Token": FOOTBALL_DATA_KEY}, timeout=HTTP_TIMEOUT_SECONDS)


def refresh_football_standings(force=False):
    """V35.0: Clasificaciones reales tipo Flashscore.
    Usa Football-Data.org si hay FOOTBALL_DATA_KEY. Si no hay clave, no rompe la app.
    """
    if not ENABLE_STANDINGS:
        return {"ok": False, "reason": "ENABLE_STANDINGS=false", "updated": 0}
    if not FOOTBALL_DATA_KEY:
        return {"ok": False, "reason": "missing_FOOTBALL_DATA_KEY", "updated": 0}
    results=[]; total=0
    conn=get_db(); cur=conn.cursor()
    for comp in STANDINGS_COMPETITIONS:
        code=comp["code"]
        cache_key=f"standings:{code}"
        payload=None if force else cache_get(cache_key)
        cached=bool(payload)
        if not payload:
            try:
                payload, headers = football_data_get(f"/competitions/{urllib.parse.quote(code)}/standings")
                if payload:
                    cache_set(cache_key, "football-data", payload, STANDINGS_CACHE_MINUTES)
                    log_external_api("football-data", f"/competitions/{code}/standings", 1, "standings")
            except Exception as e:
                results.append({"competition": code, "ok": False, "reason": str(e)[:120]})
                continue
        if not payload or payload.get("errorCode"):
            results.append({"competition": code, "ok": False, "reason": (payload or {}).get("message", "empty")[:120] if isinstance(payload, dict) else "empty"})
            continue
        standings=payload.get("standings") or []
        table=[]
        for st in standings:
            if (st.get("type") or "TOTAL").upper() == "TOTAL":
                table=st.get("table") or []
                break
        if not table and standings:
            table=standings[0].get("table") or []
        season=(payload.get("season") or {}).get("startDate", "")[:4] or current_football_season()
        cur.execute("DELETE FROM league_standings WHERE competition_code=?", (code,))
        count=0
        for row in table:
            team=row.get("team") or {}
            cur.execute("""
            INSERT INTO league_standings(competition_code,competition_name,country,season,position,team_name,crest_url,played,won,draw,lost,goals_for,goals_against,goal_difference,points,form,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                code, comp["name"], comp["country"], str(season), int(row.get("position") or 0),
                team.get("name") or team.get("shortName") or "", team.get("crest") or "",
                int(row.get("playedGames") or 0), int(row.get("won") or 0), int(row.get("draw") or 0), int(row.get("lost") or 0),
                int(row.get("goalsFor") or 0), int(row.get("goalsAgainst") or 0), int(row.get("goalDifference") or 0), int(row.get("points") or 0),
                row.get("form") or "", iso_now()
            ))
            count+=1
        total += count
        results.append({"competition": code, "name": comp["name"], "cached": cached, "teams": count, "ok": True})
    conn.commit(); conn.close()
    return {"ok": True, "updated": total, "competitions": results, "provider": "football-data"}


def standings_available():
    conn=get_db(); cur=conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) AS c FROM league_standings")
        c=int(cur.fetchone()["c"] or 0)
    except Exception:
        c=0
    conn.close()
    return c


def get_standings_groups(filter_key=""):
    filter_key=(filter_key or "").strip().lower()
    params=[]
    where="WHERE 1=1"
    if filter_key and filter_key not in ("all", "todos"):
        where += " AND (LOWER(competition_name) LIKE ? OR LOWER(country) LIKE ? OR LOWER(competition_code) LIKE ?)"
        like=f"%{filter_key}%"; params=[like,like,like]
    conn=get_db(); cur=conn.cursor()
    try:
        cur.execute("""
        SELECT * FROM league_standings
        """ + where + """
        ORDER BY
          CASE competition_code WHEN 'PD' THEN 1 WHEN 'PL' THEN 2 WHEN 'CL' THEN 3 WHEN 'SA' THEN 4 WHEN 'BL1' THEN 5 WHEN 'FL1' THEN 6 ELSE 20 END,
          position ASC
        """, params)
        rows=[dict(r) for r in cur.fetchall()]
    except Exception:
        rows=[]
    conn.close()
    groups=[]
    by={}
    for r in rows:
        key=r.get("competition_code") or r.get("competition_name") or "Liga"
        if key not in by:
            by[key]={"code": key, "name": r.get("competition_name") or key, "country": r.get("country") or "", "updated_at": r.get("updated_at") or "", "rows": []}
            groups.append(by[key])
        by[key]["rows"].append(r)
    return groups


def team_logo_url(name):
    key=normalize_team_key(name)
    if not key:
        return ""
    # 1) Logos locales manuales: static/team_logos/<nombre_normalizado>.svg/png/webp
    # Puedes añadir escudos propios sin tocar código. Ej: static/team_logos/real_madrid.png
    try:
        base_dir = os.path.join(app.root_path, LOCAL_TEAM_LOGOS_DIR)
        static_prefix = "/" + LOCAL_TEAM_LOGOS_DIR.strip("/")
        for ext in ("svg", "png", "webp", "jpg", "jpeg"):
            candidate = os.path.join(base_dir, f"{key}.{ext}")
            if os.path.exists(candidate):
                return f"{static_prefix}/{key}.{ext}"
    except Exception:
        pass
    # 2) Logos oficiales si existe proveedor de clasificación.
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute("SELECT team_name, crest_url FROM league_standings WHERE COALESCE(crest_url,'')!=''")
        rows=cur.fetchall(); conn.close()
        best=""
        for r in rows:
            tk=normalize_team_key(r["team_name"])
            if tk and (tk == key or tk in key or key in tk):
                best=r["crest_url"]; break
        return best or ""
    except Exception:
        return ""


def get_competition_context(limit=8):
    """Ranking profesional de competiciones con mercados reales abiertos.
    No sustituye una clasificación oficial; sirve como contexto cuando no hay FOOTBALL_DATA_KEY.
    """
    conn=get_db(); cur=conn.cursor()
    try:
        cur.execute("""
        SELECT league, sport, COUNT(*) AS matches,
               AVG(CAST(COALESCE(NULLIF(score,''),'0') AS REAL)) AS avg_score,
               MAX(CAST(COALESCE(NULLIF(ev,''),'0') AS REAL)) AS best_ev,
               MIN(NULLIF(kickoff_time,'')) AS next_kickoff
        FROM picks
        WHERE active=1 AND COALESCE(title,'')!='' AND (COALESCE(sport,'') LIKE '%soccer%' OR LOWER(COALESCE(league,'')) LIKE '%liga%' OR LOWER(COALESCE(league,'')) LIKE '%league%' OR LOWER(COALESCE(league,'')) LIKE '%cup%')
        GROUP BY COALESCE(NULLIF(league,''), sport)
        ORDER BY matches DESC, avg_score DESC
        LIMIT ?
        """, (int(limit),))
        rows=[dict(r) for r in cur.fetchall()]
    except Exception:
        rows=[]
    conn.close()
    for r in rows:
        r['name']=r.get('league') or r.get('sport') or 'Fútbol'
        r['avg_score']=round(float(r.get('avg_score') or 0),1)
        r['best_ev']=round(float(r.get('best_ev') or 0),1)
        r['next_label']=kickoff_ui_parts(r.get('next_kickoff')).get('full') if r.get('next_kickoff') else 'Próximamente'
    return rows

def standings_status():
    return {
        "enabled": ENABLE_STANDINGS,
        "has_key": bool(FOOTBALL_DATA_KEY),
        "rows": standings_available(),
        "provider": "Football-Data.org",
        "cache_minutes": STANDINGS_CACHE_MINUTES,
    }

def live_odds_manager_status():
    usage = external_usage_stats()
    return {
        "enabled": {"live": ENABLE_LIVE_API, "odds": ENABLE_ODDS_API, "api_football": False, "auto_refresh": LIVE_AUTO_REFRESH},
        "providers": {"live": LIVE_PROVIDER, "odds": ODDS_PROVIDER, "api_football": "desactivado"},
        "keys": {"thesportsdb": bool(THESPORTSDB_KEY), "theoddsapi": bool(ODDS_API_KEY), "api_football": False},
        "limits": {"live_daily": LIVE_DAILY_REQUEST_LIMIT, "odds_monthly": ODDS_MONTHLY_CREDIT_LIMIT, "api_football_daily": 0},
        "cache_minutes": {"live": LIVE_CACHE_MINUTES, "odds": ODDS_CACHE_MINUTES, "general": API_CACHE_MINUTES},
        "usage": usage,
        "sport": THESPORTSDB_SPORT,
        "odds_sports": get_active_odds_sport_keys(force=False),
        "sport_watchlist": get_sport_watchlist_status(force=False),
    }


@app.route("/team-badge.svg")
def team_badge_svg():
    name = (request.args.get("name") or "Equipo").strip()[:42]
    initials = team_initials(name) or "NS"
    c1 = team_color(name, 0)
    c2 = team_color(name, 1)
    safe_name = re.sub(r"[^A-Za-z0-9 ÁÉÍÓÚáéíóúÑñ.-]", "", name) or "Equipo"
    # SVG con atributos válidos en todos los navegadores. Evita rgba() en atributos SVG
    # porque algunos WebViews lo renderizan invisible. Siempre muestra escudo generado.
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96" role="img" aria-label="{safe_name}">
    <defs>
      <linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
      <filter id="s" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="7" stdDeviation="6" flood-color="{c1}" flood-opacity="0.42"/></filter>
    </defs>
    <rect width="96" height="96" rx="26" fill="#061126"/>
    <path filter="url(#s)" d="M48 6 L83 18 V44 C83 66 68 82 48 91 C28 82 13 66 13 44 V18 Z" fill="url(#g)" stroke="#ffffff" stroke-opacity="0.88" stroke-width="4"/>
    <path d="M28 27 H68 V37 H28 Z M28 45 H68 V55 H28 Z" fill="#061126" opacity="0.20"/>
    <circle cx="48" cy="49" r="24" fill="#061126" opacity="0.38" stroke="#ffffff" stroke-opacity="0.45" stroke-width="2"/>
    <text x="48" y="57" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="900" fill="#ffffff">{initials}</text>
    </svg>"""
    resp = Response(svg, mimetype="image/svg+xml")
    resp.headers["Cache-Control"] = "public, max-age=604800"
    return resp

@app.route("/api/performance-status")
def performance_status():
    try:
        usage = external_usage_stats()
    except Exception:
        usage = {}
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "safe_mode": PERFORMANCE_SAFE_MODE,
        "live_auto_refresh": LIVE_AUTO_REFRESH,
        "public_refresh_cooldown_seconds": PUBLIC_LIVE_REFRESH_COOLDOWN_SECONDS,
        "max_sports_per_refresh": MAX_SPORTS_PER_REFRESH,
        "telegram_during_refresh": TELEGRAM_AUTO_SEND_DURING_REFRESH,
        "http_timeout_seconds": HTTP_TIMEOUT_SECONDS,
        "snapshot": light_live_snapshot(),
        "usage": usage,
    })


@app.route("/api/stability-status")
def stability_status():
    gate = require_admin()
    if gate:
        return jsonify({"ok": False, "error": "admin_required"}), 401
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "hard_mode": STABILITY_HARD_MODE,
        "db_wal": DB_ENABLE_WAL,
        "db_busy_timeout_ms": DB_BUSY_TIMEOUT_MS,
        "background_jobs_enabled": BACKGROUND_JOBS_ENABLED,
        "performance_safe_mode": PERFORMANCE_SAFE_MODE,
        "public_cooldown_seconds": PUBLIC_LIVE_REFRESH_COOLDOWN_SECONDS,
        "admin_cooldown_seconds": ADMIN_REFRESH_COOLDOWN_SECONDS,
        "api_refresh_lock_seconds": API_REFRESH_LOCK_SECONDS,
        "http_timeout_seconds": HTTP_TIMEOUT_SECONDS,
        "telegram_during_refresh": TELEGRAM_AUTO_SEND_DURING_REFRESH,
        "counts": stability_counts(),
        "prune_report": globals().get("PRUNE_REPORT", {}),
        "snapshot": light_live_snapshot(),
    })



# V55.0 Final QA Production Check — revisión rápida antes de Stripe/lanzamiento.
def _table_count(cur, table, where="", params=()):
    try:
        q = f"SELECT COUNT(*) FROM {table} " + (where or "")
        cur.execute(q, params)
        return int(cur.fetchone()[0] or 0)
    except Exception:
        return 0

def production_check_summary():
    """Resumen seguro de producción para admin. No llama APIs externas ni bloquea workers."""
    checks = []
    def add(key, label, ok, detail="", level="ok"):
        checks.append({"key": key, "label": label, "ok": bool(ok), "detail": detail, "level": level if ok else "warn"})

    conn = get_db(); cur = conn.cursor()
    users = _table_count(cur, "users")
    picks = _table_count(cur, "picks")
    active_picks = _table_count(cur, "picks", "WHERE COALESCE(active,1)=1")
    telegram_users = _table_count(cur, "users", "WHERE COALESCE(telegram_chat_id,'')!=''")
    premium_users = _table_count(cur, "users", "WHERE plan IN ('PRO','ELITE','ADMIN')")
    alerts_today = 0
    try:
        cur.execute("SELECT COUNT(*) FROM alert_logs WHERE date(created_at)=date('now') AND status='sent'")
        alerts_today = int(cur.fetchone()[0] or 0)
    except Exception:
        pass
    saved_picks = _table_count(cur, "saved_picks")
    conn.close()

    add("db", "Base de datos", users >= 0, f"Usuarios: {users} · Picks: {picks}")
    add("odds", "The Odds API", bool(ODDS_API_KEY) and ENABLE_ODDS_API, "Clave configurada y motor activo" if bool(ODDS_API_KEY) else "Falta ODDS_API_KEY")
    add("telegram", "Telegram", bool(os.environ.get('TELEGRAM_BOT_TOKEN','').strip()) and bool(os.environ.get('TELEGRAM_CHAT_ID','').strip()) and ENABLE_PRO_ALERTS, "Bot, canal y alertas preparados" if (os.environ.get('TELEGRAM_BOT_TOKEN','').strip() and os.environ.get('TELEGRAM_CHAT_ID','').strip()) else "Revisa token/chat_id")
    add("push", "Push", bool(os.environ.get('PUSH_VAPID_PUBLIC_KEY','').strip()) and bool(os.environ.get('PUSH_VAPID_PRIVATE_KEY','').strip()), "Claves VAPID listas" if os.environ.get('PUSH_VAPID_PUBLIC_KEY','').strip() else "Opcional: faltan claves VAPID", "info")
    add("pwa", "PWA", os.path.exists(os.path.join(app.root_path, 'manifest.json')) and os.path.exists(os.path.join(app.root_path, 'service-worker.js')), "Manifest y service worker detectados")
    add("stability", "Estabilidad Render", PERFORMANCE_SAFE_MODE and STABILITY_HARD_MODE, "Modo seguro activo" if (PERFORMANCE_SAFE_MODE and STABILITY_HARD_MODE) else "Activa PERFORMANCE_SAFE_MODE y STABILITY_HARD_MODE")
    add("membership", "Membresías", True, f"Premium: {premium_users} · Expiración mensual preparada")
    add("client", "Experiencia cliente", True, "Dashboard, picks, partidos, alertas y clasificación disponibles")
    add("activity", "Actividad", True, f"Telegram conectados: {telegram_users} · Picks guardados: {saved_picks}")

    total = len(checks)
    passed = sum(1 for c in checks if c.get('ok'))
    score = round((passed / total) * 100) if total else 0
    ready = score >= 85 and bool(ODDS_API_KEY) and PERFORMANCE_SAFE_MODE
    return {
        "version": APP_VERSION,
        "time": madrid_iso_now(),
        "score": score,
        "ready": ready,
        "counts": {"users": users, "picks": picks, "active_picks": active_picks, "premium_users": premium_users, "telegram_users": telegram_users, "alerts_today": alerts_today},
        "checks": checks,
        "next_step": "Stripe / pagos reales" if ready else "Corregir avisos críticos antes de Stripe",
    }

@app.route("/healthz")
def healthz():
    return jsonify({"ok": True, "version": APP_VERSION, "time": madrid_iso_now()})



@app.route("/api/production-check")
def api_production_check():
    gate = require_admin()
    if gate:
        return jsonify({"ok": False, "error": "admin_required"}), 401
    return jsonify({"ok": True, **production_check_summary()})

@app.route("/admin/production-check")
def admin_production_check():
    gate = require_admin()
    if gate:
        return gate
    return render_template("admin_production_check.html", qa=production_check_summary(), platform=platform_health_summary())

@app.route("/api/live-data-status")
def public_live_data_status():
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "live_enabled": ENABLE_LIVE_API,
        "odds_enabled": ENABLE_ODDS_API,
        "auto_refresh": LIVE_AUTO_REFRESH,
        "has_theoddsapi_key": bool(ODDS_API_KEY),
        "has_football_data_key": bool(FOOTBALL_DATA_KEY),
        "standings_enabled": ENABLE_STANDINGS,
        "has_thesportsdb_key": bool(THESPORTSDB_KEY),
        "sports": get_active_odds_sport_keys(force=False),
        "sport_watchlist": get_sport_watchlist_status(force=False),
        "api_football_enabled": False,
        "has_api_football_key": False,
        "api_football_note": "V31.7 funciona solo con The Odds API",
        "cache_minutes": {"live": LIVE_CACHE_MINUTES, "odds": ODDS_CACHE_MINUTES}
    })


@app.route("/api/football-season-status")
def football_season_status():
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "mode": "football_season_auto",
        "sports": get_sport_watchlist_status(force=bool(is_admin() and request.args.get("force") == "1")),
        "env": {
            "football_first": FOOTBALL_FIRST,
            "show_basketball_default": SHOW_BASKETBALL_DEFAULT,
            "auto_filter_active_sports": AUTO_FILTER_ACTIVE_SPORTS,
            "max_events_per_sport": MAX_EVENTS_PER_SPORT,
            "odds_cache_minutes": ODDS_CACHE_MINUTES,
        }
    })

@app.route("/api/live-refresh", methods=["POST", "GET"])
def public_live_refresh():
    # V51: las visitas de clientes nunca disparan trabajo pesado. Solo admin con force=1 refresca APIs.
    force = bool(is_admin() and request.args.get("force") == "1")
    return jsonify(auto_refresh_real_live_data(force=force, public=not force))


@app.route("/api/admin/live-odds-status")
def admin_live_odds_status():
    gate = require_admin()
    if gate:
        return jsonify({"ok": False, "error": "admin_required"}), 401
    data = live_odds_manager_status()
    data["ok"] = True
    return jsonify(data)


@app.route("/admin/api-refresh/<kind>", methods=["POST"])
def admin_api_refresh(kind):
    gate = require_admin()
    if gate:
        return gate
    force = request.form.get("force") == "1"
    result = {"ok": False, "reason": "unknown"}
    if kind == "live":
        try:
            result = refresh_thesportsdb_live(force=force)
        except Exception as e:
            result = {"ok": False, "reason": str(e), "updated": 0}
    elif kind == "odds":
        try:
            result = refresh_theoddsapi(force=force)
        except Exception as e:
            result = {"ok": False, "reason": str(e), "updated": 0}
    elif kind == "api-football":
        result = {"ok": False, "reason": "API-Football desactivado en V31.7. Usa Solo The Odds API.", "updated": 0}
    elif kind == "all":
        live = {}
        odds = {}
        try:
            live = refresh_thesportsdb_live(force=force)
        except Exception as e:
            live = {"ok": False, "reason": str(e)}
        api_football = {"ok": False, "reason": "desactivado_v31_7_odds_only"}
        try:
            odds = refresh_theoddsapi(force=force)
        except Exception as e:
            odds = {"ok": False, "reason": str(e)}
        result = {"ok": True, "live": live, "odds": odds, "api_football": api_football}
    session["last_api_refresh"] = result
    session.modified = True
    return redirect("/admin#live-odds")

@app.route("/api/admin/api-spend")
def admin_api_spend():
    gate = require_admin()
    if gate:
        return jsonify({"ok": False, "error": "admin_required"}), 401
    data = get_api_spend_stats()
    data["ok"] = True
    return jsonify(data)


@app.route("/admin/client-mode")
def admin_client_mode():
    gate = require_admin()
    if gate:
        return gate
    # El admin conserva permisos de gestión, pero entra a su propia experiencia cliente.
    session["admin_client_mode"] = True
    session.modified = True
    return redirect("/clientes")


@app.route("/admin/back")
def admin_back():
    gate = require_admin()
    if gate:
        return gate
    session.pop("admin_client_mode", None)
    session.modified = True
    return redirect("/admin")


@app.route("/admin")
def admin():
    gate = require_admin()
    if gate:
        return gate

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id,username,role,plan,balance,created_at,last_login_at,last_seen_at,
               telegram_chat_id,telegram_username,telegram_connected_at,telegram_alerts_enabled,
               membership_source,membership_started_at,membership_expires_at,membership_auto_expire,membership_note,suspended
        FROM users
        ORDER BY id DESC
    """)
    users = cur.fetchall()
    cur.execute("SELECT * FROM picks ORDER BY id DESC")
    picks = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE plan IN ('PRO','ELITE','ADMIN')")
    premium_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE COALESCE(telegram_chat_id,'')!=''")
    telegram_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE membership_source IN ('admin_regalo','regalo') AND plan IN ('PRO','ELITE')")
    gifted_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE membership_source IN ('compra','stripe','paid') AND plan IN ('PRO','ELITE')")
    paid_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM picks")
    total_picks = cur.fetchone()[0]
    conn.close()

    stats = {"users": total_users, "premium": premium_users, "picks": total_picks, "telegram": telegram_users, "gifted": gifted_users, "paid": paid_users}
    api_stats = get_api_spend_stats()
    cur = None
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM alert_logs ORDER BY id DESC LIMIT 10")
    recent_alerts = cur.fetchall()
    conn.close()
    return render_template("admin.html", users=users, picks=picks, stats=stats, api_stats=api_stats, live_odds=live_odds_manager_status(), last_api_refresh=session.pop("last_api_refresh", None), platform=platform_health_summary(), recent_alerts=recent_alerts, quality=quality_control_status())


@app.route("/admin/alerts/test", methods=["POST"])
def admin_alert_test():
    gate = require_admin()
    if gate:
        return gate
    title = "Prueba de alerta SHARK"
    body = "✅ Telegram está conectado. Si recibes este mensaje, las alertas de NeMeSiS SHARK PRO funcionan correctamente."
    send_platform_alert("test", title, body)
    return redirect("/admin#alerts")


@app.route("/admin/alerts/send-top", methods=["POST"])
def admin_alert_send_top():
    gate = require_admin()
    if gate:
        return gate
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
      SELECT * FROM picks
      WHERE active=1 AND COALESCE(result_status,'pendiente')='pendiente'
      ORDER BY CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC
      LIMIT 1
    """)
    p = cur.fetchone(); conn.close()
    if p:
        send_pick_alert(p["id"], "top_pick")
    else:
        log_alert("top_pick", "Sin señales", "No hay picks activos para enviar.", "system", "empty", {})
    return redirect("/admin#alerts")


@app.route("/admin/alerts/test-plan", methods=["POST"])
def admin_alert_test_plan():
    gate = require_admin()
    if gate:
        return gate
    plan = normalize_plan(request.form.get("plan", "PRO"), allow_admin=True)
    chat_id = telegram_channel_chat_id(plan) or TELEGRAM_TEST_CHAT_ID or TELEGRAM_CHAT_ID
    body = "\n".join([
        f"🦈 <b>Prueba Telegram {plan}</b>",
        "Este mensaje confirma que el canal de este plan está conectado.",
        "✅ Si lo ves aquí, NeMeSiS ya puede enviar señales automáticamente.",
    ])
    send_telegram_message(chat_id, body, kind="test_plan", title=f"Prueba {plan}", payload={"plan": plan})
    return redirect("/admin#alerts")


@app.route("/api/admin/telegram-diagnostic")
def admin_telegram_diagnostic():
    gate = require_admin()
    if gate:
        return jsonify({"ok": False, "error": "admin_required"}), 401
    return jsonify({"ok": True, **telegram_config_status()})


@app.route("/api/admin/alerts-status")
def admin_alerts_status():
    gate = require_admin()
    if gate:
        return jsonify({"ok": False, "error": "admin_required"}), 401
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM alert_logs ORDER BY id DESC LIMIT 10")
    logs = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({
        "ok": True,
        "telegram_ready": telegram_ready(),
        "enabled": ENABLE_PRO_ALERTS,
        "has_token": bool(TELEGRAM_BOT_TOKEN),
        "has_chat_id": bool(TELEGRAM_CHAT_ID),
        "has_any_plan_chat": bool(TELEGRAM_FREE_CHAT_ID or TELEGRAM_PRO_CHAT_ID or TELEGRAM_ELITE_CHAT_ID),
        "config": telegram_config_status(),
        "min_score": TELEGRAM_ALERT_MIN_SCORE,
        "recent": logs,
    })



@app.route("/admin/quality")
def admin_quality():
    gate = require_admin()
    if gate:
        return gate
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT * FROM alert_logs
        WHERE kind IN ('odds_auto_pick','auto_pick','new_pick','admin_pick','channel_pick','user_pick')
        ORDER BY id DESC LIMIT 80
    """)
    logs = cur.fetchall()
    cur.execute("""
        SELECT COUNT(*) FROM alert_logs WHERE status='ok' AND date(created_at)=date('now')
    """)
    sent_today = cur.fetchone()[0]
    cur.execute("""
        SELECT COUNT(*) FROM alert_logs WHERE status='filtered' AND date(created_at)=date('now')
    """)
    filtered_today = cur.fetchone()[0]
    conn.close()
    return render_template("admin_quality.html", quality=quality_control_status(), logs=logs, sent_today=sent_today, filtered_today=filtered_today)


@app.route("/admin/activity")
def admin_activity():
    gate = require_admin()
    if gate:
        return gate
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM user_activity ORDER BY id DESC LIMIT 200")
    activity = cur.fetchall()
    conn.close()
    return render_template("admin_activity.html", activity=activity)


@app.route("/admin/pick/<int:pick_id>/resend", methods=["POST"])
def admin_pick_resend(pick_id):
    gate = require_admin()
    if gate:
        return gate
    send_pick_alert(pick_id, "manual_resend", force=True)
    return redirect("/admin/quality")

@app.route("/admin/user/create", methods=["POST"])
def admin_user_create():
    gate = require_admin()
    if gate:
        return gate

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    plan = normalize_plan(request.form.get("plan", "FREE"), allow_admin=True)
    role = "admin" if plan == "ADMIN" else "cliente"

    if username and len(password) >= 4:
        try:
            conn = get_db()
            cur = conn.cursor()
            source = request.form.get("membership_source", "admin_manual").strip() or "admin_manual"
            auto_expire = 1 if request.form.get("auto_expire") == "1" and plan in ("PRO","ELITE") else 0
            months = int(request.form.get("months", "1") or 1)
            now_iso = madrid_iso_now()
            expires = add_months_madrid(months) if auto_expire else ""
            cur.execute("INSERT INTO users(username,password,role,plan,balance,membership_source,membership_started_at,membership_expires_at,membership_auto_expire,membership_note) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (username, hash_password(password), role, plan, 100, source, now_iso if plan in ("PRO","ELITE") else "", expires, auto_expire, request.form.get("membership_note", "")))
            cur.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)",
                        (cur.lastrowid, username, "usuario_creado", f"Plan {plan} · origen {source}", now_iso))
            conn.commit()
            conn.close()
        except Exception:
            pass

    return redirect("/admin")


@app.route("/admin/user/<int:user_id>/plan", methods=["POST"])
def admin_user_plan(user_id):
    gate = require_admin()
    if gate:
        return gate

    plan = normalize_plan(request.form.get("plan", "FREE"), allow_admin=True)
    role = "admin" if plan == "ADMIN" else "cliente"
    source = request.form.get("membership_source", "admin_manual").strip() or "admin_manual"
    auto_expire = 1 if request.form.get("auto_expire") == "1" and plan in ("PRO","ELITE") else 0
    months = int(request.form.get("months", "1") or 1)
    note = request.form.get("membership_note", "").strip()
    now_iso = madrid_iso_now()
    expires = add_months_madrid(months) if auto_expire else ""

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET plan=?, role=?, membership_source=?, membership_started_at=?, membership_expires_at=?,
            membership_auto_expire=?, membership_note=?
        WHERE id=?
    """, (plan, role, source, now_iso if plan in ("PRO","ELITE") else "", expires, auto_expire, note, user_id))
    cur.execute("SELECT username FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    cur.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)",
                (user_id, row["username"] if row else "", "cambio_plan", f"Plan {plan} · origen {source} · caduca {'sí' if auto_expire else 'no'}", now_iso))
    conn.commit()
    conn.close()
    sync_session_if_same_user(user_id)
    return redirect("/admin")


@app.route("/admin/user/<int:user_id>/password", methods=["POST"])
def admin_user_password(user_id):
    gate = require_admin()
    if gate:
        return gate

    password = request.form.get("password", "").strip()
    if len(password) >= 4:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE id=?", (hash_password(password), user_id))
        conn.commit()
        conn.close()
    return redirect("/admin")


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_user_delete(user_id):
    gate = require_admin()
    if gate:
        return gate

    current = current_user() or {}
    # Seguridad: no permitir borrar el admin actualmente logueado.
    if int(current.get("id", 0) or 0) == int(user_id):
        return redirect("/admin")

    conn = get_db()
    cur = conn.cursor()

    # Seguridad extra: no borrar el último admin disponible.
    cur.execute("SELECT role FROM users WHERE id=?", (user_id,))
    target = cur.fetchone()
    if target and target["role"] == "admin":
        cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        admin_count = cur.fetchone()[0]
        if admin_count <= 1:
            conn.close()
            return redirect("/admin")

    # Limpieza compatible con SQLite existente. No borra /data ni toca DB_PATH.
    cur.execute("DELETE FROM user_picks WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM shark_ai_logs WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM api_usage_logs WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/admin/pick/create", methods=["POST"])
def admin_pick_create():
    gate = require_admin()
    if gate:
        return gate

    data = {
        "league": request.form.get("league", "").strip(),
        "title": request.form.get("title", "").strip(),
        "pick": request.form.get("pick", "").strip(),
        "cuota": request.form.get("cuota", "").strip(),
        "ev": request.form.get("ev", "").strip(),
        "score": request.form.get("score", "").strip(),
        "premium": "1" if request.form.get("premium") == "1" else "0",
        "live_status": request.form.get("live_status", "PROGRAMADO").strip().upper() or "PROGRAMADO",
        "live_score": request.form.get("live_score", "").strip(),
        "live_minute": request.form.get("live_minute", "").strip(),
        "kickoff_time": request.form.get("kickoff_time", "").strip(),
    }

    if data["title"]:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO picks(league,title,pick,cuota,ev,score,premium,live_status,live_score,live_minute,kickoff_time)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (data["league"], data["title"], data["pick"], data["cuota"], data["ev"], data["score"], data["premium"], data["live_status"], data["live_score"], data["live_minute"], data["kickoff_time"]))
        new_pick_id = cur.lastrowid
        conn.commit()
        conn.close()
        if TELEGRAM_SEND_ON_ADMIN_CREATE or request.form.get("send_alert") == "1":
            send_pick_alert(new_pick_id, "admin_pick", force=True)

    return redirect("/admin")


@app.route("/admin/pick/<int:pick_id>/live", methods=["POST"])
def admin_pick_live_update(pick_id):
    gate = require_admin()
    if gate:
        return gate

    live_status = request.form.get("live_status", "PROGRAMADO").strip().upper() or "PROGRAMADO"
    if live_status not in ["PROGRAMADO", "EN DIRECTO", "DESCANSO", "FINALIZADO", "SUSPENDIDO"]:
        live_status = "PROGRAMADO"
    live_score = request.form.get("live_score", "").strip()
    live_minute = request.form.get("live_minute", "").strip()
    kickoff_time = request.form.get("kickoff_time", "").strip()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    UPDATE picks
    SET live_status=?, live_score=?, live_minute=?, kickoff_time=?
    WHERE id=?
    """, (live_status, live_score, live_minute, kickoff_time, pick_id))
    conn.commit()
    conn.close()
    return redirect("/admin")



@app.route("/admin/pick/<int:pick_id>/result", methods=["POST"])
def admin_pick_result_update(pick_id):
    gate = require_admin()
    if gate:
        return gate
    status = request.form.get("result_status", "pendiente")
    result_score = request.form.get("result_score", "").strip()
    note = request.form.get("closing_note", "").strip()
    settle_pick_for_all_users(pick_id, status, result_score, note)
    if status in ["ganado", "perdido", "void"]:
        send_result_alert(pick_id, status, result_score)
    return redirect("/admin#picks")

@app.route("/admin/pick/<int:pick_id>/delete", methods=["POST"])
def admin_pick_delete(pick_id):
    gate = require_admin()
    if gate:
        return gate

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM picks WHERE id=?", (pick_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")



# ==========================================================
# PUSH NOTIFICATIONS — V50.0
# ==========================================================

def push_ready():
    return bool(ENABLE_PUSH_NOTIFICATIONS and PUSH_VAPID_PUBLIC_KEY and PUSH_VAPID_PRIVATE_KEY and webpush)


def user_push_count_today(user_id):
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM alert_logs
            WHERE channel='push' AND status='ok' AND date(created_at)=date('now')
            AND payload LIKE ?
        """, (f'%"user_id": {int(user_id)}%',))
        n=cur.fetchone()[0]; conn.close(); return int(n or 0)
    except Exception:
        return 0


def save_push_subscription(user_id, sub, ua=''):
    endpoint=(sub or {}).get('endpoint','')
    keys=(sub or {}).get('keys') or {}
    p256dh=keys.get('p256dh','')
    auth=keys.get('auth','')
    if not endpoint or not p256dh or not auth:
        return False, 'subscription_incompleta'
    conn=get_db(); cur=conn.cursor()
    cur.execute("""
        INSERT INTO push_subscriptions(user_id, endpoint, p256dh, auth, user_agent, enabled, created_at, last_seen_at)
        VALUES(?,?,?,?,?,1,?,?)
        ON CONFLICT(endpoint) DO UPDATE SET
          user_id=excluded.user_id,
          p256dh=excluded.p256dh,
          auth=excluded.auth,
          user_agent=excluded.user_agent,
          enabled=1,
          last_seen_at=excluded.last_seen_at
    """, (user_id, endpoint, p256dh, auth, (ua or '')[:180], iso_now(), iso_now()))
    conn.commit(); conn.close()
    return True, 'guardada'


def build_push_payload(title, body, url='/clientes', tag='nemesis-shark'):
    return {
        'title': title or 'NeMeSiS SHARK PRO',
        'body': body or 'Nueva actualización SHARK.',
        'url': url or '/clientes',
        'tag': tag or 'nemesis-shark',
        'icon': '/static/icons/icon-192.png',
        'badge': '/static/icons/icon-192.png'
    }


def send_push_subscription(row, payload, kind='push'):
    if not push_ready():
        log_alert(kind, payload.get('title','Push'), payload.get('body',''), 'push', 'not_configured', {'user_id': safe_row_get(row,'user_id','')})
        return {'ok': False, 'reason': 'push_not_configured'}
    sub={
        'endpoint': safe_row_get(row,'endpoint',''),
        'keys': {'p256dh': safe_row_get(row,'p256dh',''), 'auth': safe_row_get(row,'auth','')}
    }
    try:
        webpush(
            subscription_info=sub,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=PUSH_VAPID_PRIVATE_KEY,
            vapid_claims={'sub': PUSH_VAPID_SUBJECT}
        )
        conn=get_db(); cur=conn.cursor()
        cur.execute('UPDATE push_subscriptions SET last_sent_at=? WHERE id=?', (iso_now(), safe_row_get(row,'id')))
        conn.commit(); conn.close()
        log_alert(kind, payload.get('title','Push'), payload.get('body',''), 'push', 'ok', {'user_id': safe_row_get(row,'user_id',''), 'subscription_id': safe_row_get(row,'id')})
        return {'ok': True}
    except Exception as e:
        msg=str(e)[:200]
        log_alert(kind, payload.get('title','Push'), payload.get('body',''), 'push', 'error', {'error': msg, 'user_id': safe_row_get(row,'user_id',''), 'subscription_id': safe_row_get(row,'id')})
        # Si el navegador borró la suscripción, la desactivamos para no insistir.
        try:
            if '410' in msg or '404' in msg:
                conn=get_db(); cur=conn.cursor(); cur.execute('UPDATE push_subscriptions SET enabled=0 WHERE id=?', (safe_row_get(row,'id'),)); conn.commit(); conn.close()
        except Exception:
            pass
        return {'ok': False, 'reason': 'send_error'}


def send_push_to_user(user_id, title, body, url='/clientes', tag='nemesis-shark', kind='push'):
    if user_push_count_today(user_id) >= PUSH_MAX_DAILY_PER_USER:
        return {'ok': False, 'reason': 'daily_limit', 'sent': 0}
    payload=build_push_payload(title, body, url, tag)
    sent=0; results=[]
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute('SELECT * FROM push_subscriptions WHERE user_id=? AND enabled=1', (user_id,))
        rows=cur.fetchall(); conn.close()
        for r in rows:
            res=send_push_subscription(r, payload, kind)
            results.append(res)
            if res.get('ok'): sent += 1
        return {'ok': sent>0, 'sent': sent, 'results': results}
    except Exception as e:
        log_alert(kind, title, body, 'push', 'error', {'error': str(e)[:200], 'user_id': user_id})
        return {'ok': False, 'reason': 'db_error', 'sent': 0}


def send_push_to_connected_users(title, body, url='/picks', min_plan='FREE', kind='push_broadcast'):
    if not ENABLE_PUSH_NOTIFICATIONS:
        return {'ok': False, 'reason': 'push_disabled', 'sent': 0}
    plan_rank={'FREE':0,'PRO':1,'ELITE':2,'ADMIN':3}
    min_rank=plan_rank.get(normalize_plan(min_plan, allow_admin=True),0)
    sent=0
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute("SELECT id, plan FROM users WHERE role='cliente'")
        users=cur.fetchall(); conn.close()
        for u in users:
            plan=normalize_plan(safe_row_get(u,'plan','FREE'))
            if plan_rank.get(plan,0) < min_rank:
                continue
            res=send_push_to_user(safe_row_get(u,'id'), title, body, url, tag=kind, kind=kind)
            sent += int(res.get('sent',0) or 0)
        return {'ok': sent>0, 'sent': sent}
    except Exception:
        return {'ok': False, 'sent': 0}


def send_pick_push_notifications(pick_id):
    if not PUSH_SEND_ON_NEW_PICK:
        return {'ok': False, 'reason': 'push_new_pick_disabled'}
    p=fetch_pick_by_id(pick_id)
    if not p:
        return {'ok': False, 'reason': 'pick_not_found'}
    score=pick_score_value(p)
    if score < PUSH_MIN_SCORE:
        return {'ok': False, 'reason': 'score_low'}
    title_txt=safe_row_get(p,'title','Nuevo pick SHARK') or 'Nuevo pick SHARK'
    pick_txt=human_bet_choice(p) or safe_row_get(p,'pick','Pick disponible')
    cuota=safe_row_get(p,'cuota','') or safe_row_get(p,'odds_decimal','') or '-'
    body=f"Apuesta: {pick_txt} · Cuota {cuota} · SHARK {score}/100"
    min_plan='FREE' if score >= telegram_plan_policy('FREE')['min_score'] else 'PRO'
    if score >= telegram_plan_policy('ELITE')['min_score']:
        min_plan='ELITE'
    elif score >= telegram_plan_policy('PRO')['min_score']:
        min_plan='PRO'
    return send_push_to_connected_users('Nueva señal SHARK', body, f'/partido/{pick_id}', min_plan=min_plan, kind='push_pick')


@app.route('/api/push/config')
def api_push_config():
    u=current_user()
    if not u:
        return jsonify({'ok': False, 'login_required': True}), 401
    return jsonify({
        'ok': True,
        'enabled': ENABLE_PUSH_NOTIFICATIONS,
        'configured': bool(PUSH_VAPID_PUBLIC_KEY and PUSH_VAPID_PRIVATE_KEY and webpush),
        'publicKey': PUSH_VAPID_PUBLIC_KEY,
        'reason': '' if push_ready() else ('Faltan claves VAPID en Render o pywebpush no está instalado')
    })


@app.route('/api/push/subscribe', methods=['POST'])
def api_push_subscribe():
    u=current_user()
    if not u:
        return jsonify({'ok': False, 'message': 'Inicia sesión.'}), 401
    data=request.get_json(silent=True) or {}
    ok,msg=save_push_subscription(u['id'], data.get('subscription') or data, request.headers.get('User-Agent',''))
    if ok:
        log_user_activity(u['id'], 'push_connected', 'Notificaciones push activadas')
    return jsonify({'ok': ok, 'message': 'Notificaciones activadas.' if ok else 'No se pudo guardar la suscripción.', 'detail': msg})


@app.route('/api/push/unsubscribe', methods=['POST'])
def api_push_unsubscribe():
    u=current_user()
    if not u:
        return jsonify({'ok': False}), 401
    data=request.get_json(silent=True) or {}
    endpoint=(data.get('endpoint') or '').strip()
    conn=get_db(); cur=conn.cursor()
    if endpoint:
        cur.execute('UPDATE push_subscriptions SET enabled=0 WHERE user_id=? AND endpoint=?', (u['id'], endpoint))
    else:
        cur.execute('UPDATE push_subscriptions SET enabled=0 WHERE user_id=?', (u['id'],))
    conn.commit(); conn.close()
    log_user_activity(u['id'], 'push_disabled', 'Notificaciones push desactivadas')
    return jsonify({'ok': True, 'message': 'Notificaciones desactivadas.'})


@app.route('/api/push/status')
def api_push_status():
    u=current_user()
    if not u:
        return jsonify({'ok': False}), 401
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute('SELECT COUNT(*) FROM push_subscriptions WHERE user_id=? AND enabled=1', (u['id'],))
        n=cur.fetchone()[0]; conn.close()
    except Exception:
        n=0
    return jsonify({'ok': True, 'configured': push_ready(), 'subscriptions': int(n or 0), 'enabled': int(n or 0)>0})


@app.route('/api/push/test', methods=['POST'])
def api_push_test():
    u=current_user()
    if not u:
        return jsonify({'ok': False, 'message': 'Inicia sesión.'}), 401
    res=send_push_to_user(u['id'], 'Prueba NeMeSiS', 'Las notificaciones push ya están conectadas en este dispositivo.', '/clientes', 'push-test', 'push_test')
    return jsonify({'ok': bool(res.get('ok')), 'message': 'Push enviado.' if res.get('ok') else 'No se pudo enviar. Revisa permisos o claves VAPID.', **res})

# ==========================================================
# SHARK AI
# ==========================================================

@app.route("/alertas")
def alertas_cliente():
    u = current_user()
    if not u:
        return redirect("/cliente-login")
    full = user_full_from_db(u["id"])
    code = safe_row_get(full, "telegram_connect_code", "") if full else ""
    if not safe_row_get(full, "telegram_chat_id", "") and not code:
        code = make_telegram_connect_code(u["id"])
        full = user_full_from_db(u["id"])
    policy = telegram_plan_policy(u.get("plan"))
    return render_template("alertas.html", platform=platform_health_summary(), telegram_user=full, telegram_code=code, telegram_link=bot_start_link(code), policy=policy, telegram_group_url=telegram_plan_group_url(u.get("plan")), bot_username=TELEGRAM_BOT_USERNAME)


@app.route("/api/telegram/connect-code", methods=["POST"])
def api_telegram_connect_code():
    u = current_user()
    if not u:
        return jsonify({"ok": False, "error": "login_required"}), 401
    code = make_telegram_connect_code(u["id"])
    return jsonify({"ok": True, "code": code, "link": bot_start_link(code)})


@app.route("/api/telegram/check-connect", methods=["POST"])
def api_telegram_check_connect():
    u = current_user()
    if not u:
        return jsonify({"ok": False, "error": "login_required"}), 401
    ok, msg = try_link_telegram_from_updates(u["id"])
    full = user_full_from_db(u["id"])
    return jsonify({"ok": ok, "message": msg, "connected": bool(safe_row_get(full, "telegram_chat_id", "")), "username": safe_row_get(full, "telegram_username", "")})


@app.route("/api/telegram/test-user", methods=["POST"])
def api_telegram_test_user():
    u = current_user()
    if not u:
        return jsonify({"ok": False, "message": "Inicia sesión."}), 401
    full = user_full_from_db(u["id"])
    chat_id = safe_row_get(full, "telegram_chat_id", "") if full else ""
    if not chat_id:
        return jsonify({"ok": False, "message": "Primero conecta Telegram."})
    plan = normalize_plan(safe_row_get(full, "plan", "FREE"), allow_admin=True)
    body = "\n".join([
        f"🦈 <b>Telegram conectado correctamente</b>",
        f"Tu plan: <b>{plan}</b>",
        "A partir de ahora recibirás señales según tu membresía.",
        "Todo llegará claro: qué apostar, qué significa, cuota, riesgo y stake si tu plan lo incluye."
    ])
    res = send_private_telegram(chat_id, "Prueba usuario", body, {"user_id": u["id"], "plan": plan, "test": True})
    return jsonify({"ok": bool(res.get("ok")), "message": "Mensaje enviado a Telegram." if res.get("ok") else "No se pudo enviar. Revisa que hayas iniciado el bot."})


@app.route("/api/telegram/preferences", methods=["POST"])
def api_telegram_preferences():
    u = current_user()
    if not u:
        return jsonify({"ok": False, "error": "login_required"}), 401
    enabled = 1 if request.form.get("enabled", "1") == "1" else 0
    phone = (request.form.get("phone", "") or "").strip()[:40]
    quality = (request.form.get("quality", "auto") or "auto").strip()[:20]
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET telegram_alerts_enabled=?, telegram_phone_hint=?, telegram_quality=? WHERE id=?", (enabled, phone, quality, u["id"]))
        conn.commit(); conn.close()
        return jsonify({"ok": True})
    except Exception:
        return jsonify({"ok": False, "error": "db_error"}), 500


@app.route("/ayuda")
def ayuda():
    gate = require_user()
    if gate:
        return gate
    user = current_user()
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET help_seen_at=? WHERE id=?", (madrid_iso_now(), user["id"]))
        conn.commit(); conn.close()
    except Exception:
        pass
    return render_template("ayuda.html", user=user)

@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    gate = require_user()
    if gate:
        return gate
    user = current_user()
    if request.method == "POST":
        risk = (request.form.get("risk_preference") or "medio").strip().lower()
        sport = (request.form.get("favorite_sport") or "futbol").strip().lower()
        comp = (request.form.get("favorite_competition") or "").strip()[:80]
        if risk not in ("conservador", "medio", "agresivo"):
            risk = "medio"
        if sport not in ("futbol", "basket", "todos"):
            sport = "futbol"
        conn = get_db(); cur = conn.cursor()
        cur.execute("UPDATE users SET risk_preference=?, favorite_sport=?, favorite_competition=?, onboarding_completed_at=? WHERE id=?", (risk, sport, comp, madrid_iso_now(), user["id"]))
        conn.commit(); conn.close()
        log_user_activity(user["id"], "onboarding", "Perfil inicial completado")
        return redirect("/clientes?onboarding=ok")
    return render_template("onboarding.html", user=user)

@app.route("/favorito/<int:pick_id>/toggle", methods=["POST"])
def toggle_favorite(pick_id):
    gate = require_user()
    if gate:
        return gate
    user = current_user()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM user_favorites WHERE user_id=? AND pick_id=? AND kind='pick'", (user["id"], pick_id))
    row = cur.fetchone()
    if row:
        cur.execute("DELETE FROM user_favorites WHERE id=?", (row["id"],))
        state = False
        detail = "Favorito eliminado"
    else:
        cur.execute("INSERT OR IGNORE INTO user_favorites(user_id,pick_id,kind,created_at) VALUES(?,?,?,?)", (user["id"], pick_id, "pick", madrid_iso_now()))
        state = True
        detail = "Favorito guardado"
    conn.commit(); conn.close()
    log_user_activity(user["id"], "favorite", f"{detail}: pick {pick_id}")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"ok": True, "favorite": state})
    return redirect(request.referrer or "/clientes")

@app.route("/favoritos")
def favoritos():
    gate = require_user()
    if gate:
        return gate
    user = current_user()
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT p.*, uf.created_at AS favorited_at FROM user_favorites uf
                   JOIN picks p ON p.id=uf.pick_id
                   WHERE uf.user_id=? ORDER BY uf.id DESC LIMIT 100""", (user["id"],))
    picks = cur.fetchall(); conn.close()
    return render_template("favoritos.html", user=user, picks=picks, favorite_ids=user_favorite_ids(user["id"]))

@app.route("/shark-ai")
def shark_ai_page():
    return render_template("shark_ai.html")


def safe_float(value, default=0):
    try:
        if value is None:
            return default
        txt = str(value).replace("%", "").replace("€", "").replace(",", ".").strip()
        return float(txt) if txt else default
    except Exception:
        return default


def pick_quality(pick):
    cuota = safe_float(pick.get("cuota"), 0)
    ev = safe_float(pick.get("ev"), 0)
    score = safe_float(pick.get("score"), 0)
    premium = str(pick.get("premium") or "0") == "1"
    points = 0
    if ev >= 8:
        points += 3
    elif ev >= 4:
        points += 2
    elif ev > 0:
        points += 1
    if score >= 80:
        points += 3
    elif score >= 65:
        points += 2
    elif score >= 50:
        points += 1
    if 1.45 <= cuota <= 2.40:
        points += 2
    elif 2.40 < cuota <= 3.20:
        points += 1
    if premium:
        points += 1
    if points >= 7:
        return "ALTA", points
    if points >= 4:
        return "MEDIA", points
    return "BAJA", points


def enriched_picks(limit=10):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id,league,title,pick,cuota,ev,score,premium,created_at FROM picks WHERE active=1 " + real_only_clause() + football_priority_clause(default_only=True) + " ORDER BY " + football_order_sql() + " CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    for row in rows:
        row["cuota_num"] = safe_float(row.get("cuota"), 0)
        row["ev_num"] = safe_float(row.get("ev"), 0)
        row["score_num"] = safe_float(row.get("score"), 0)
        row["quality"], row["quality_points"] = pick_quality(row)
    return rows


def build_ai_context():
    picks = enriched_picks(12)
    user = current_user()
    user_stats = None
    saved = []
    recent_questions = []
    if user:
        try:
            _, saved_rows, user_stats = get_user_dashboard(user["id"])
            saved = [dict(r) for r in saved_rows[:10]]
        except Exception:
            user_stats = None
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT question,answer,source,created_at FROM shark_ai_logs WHERE user_id=? ORDER BY id DESC LIMIT 5", (user["id"],))
            recent_questions = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception:
            recent_questions = []

    best_pick = None
    if picks:
        best_pick = sorted(picks, key=lambda p: (p.get("quality_points", 0), p.get("score_num", 0), p.get("ev_num", 0)), reverse=True)[0]

    context = {
        "usuario": user,
        "user_stats": user_stats,
        "saved_picks": saved,
        "picks": picks,
        "best_pick": best_pick,
        "recent_questions": recent_questions,
        "rules": {
            "stake_free": "0.5%-1% de banca",
            "stake_pro": "1%-2% de banca",
            "stake_elite": "1%-3% de banca",
            "no_guarantees": True
        }
    }
    context["matches"] = get_live_matches_for_ai(limit=10)
    context["snapshot"] = get_ai_real_snapshot()
    context["signal"] = ai_signal_summary(context)
    return context


def recommended_stake(balance, plan, quality):
    plan = (plan or "FREE").upper()
    if quality == "ALTA":
        pct = 0.01 if plan == "FREE" else 0.02 if plan == "PRO" else 0.03
    elif quality == "MEDIA":
        pct = 0.0075 if plan == "FREE" else 0.015
    else:
        pct = 0.005
    return max(balance * pct, 0), pct * 100


def format_pick_line(p):
    if not p:
        return "No hay picks cargados todavía."
    return f"{p.get('title') or 'Partido'} · {p.get('pick') or 'Pick'} @ {p.get('cuota') or '-'} | EV {p.get('ev') or '-'} | SCORE {p.get('score') or '-'} | calidad {p.get('quality') or '-'}"



def ai_signal_summary(context):
    picks = context.get("picks", []) or []
    best = context.get("best_pick") or {}
    stats = context.get("user_stats") or {}
    user = context.get("usuario") or {}
    pending = safe_float(stats.get("pending_risk"), 0)
    balance = safe_float(user.get("balance"), 100)
    exposure_pct = (pending / balance * 100) if balance > 0 else 0
    roi = safe_float(stats.get("roi"), 0)
    high_quality = len([p for p in picks if p.get("quality") == "ALTA"])
    medium_quality = len([p for p in picks if p.get("quality") == "MEDIA"])
    risk_level = "BAJO"
    if exposure_pct >= 15:
        risk_level = "ALTO"
    elif exposure_pct >= 7:
        risk_level = "MEDIO"
    mode = "OpenAI" if OPENAI_API_KEY else "Fallback local"
    return {
        "mode": mode,
        "risk_level": risk_level,
        "exposure_pct": round(exposure_pct, 2),
        "roi": round(roi, 2),
        "high_quality_picks": high_quality,
        "medium_quality_picks": medium_quality,
        "best_title": best.get("title") if best else None,
        "best_pick": best.get("pick") if best else None,
        "best_quality": best.get("quality") if best else None,
    }

def local_ai_answer(message, context):
    text = normalize_ai_text(message)
    picks = context.get("picks", []) or []
    matches = context.get("matches", []) or []
    best = context.get("best_pick")
    stats = context.get("user_stats") or {}
    user = context.get("usuario") or {}
    saved = context.get("saved_picks") or []
    balance = safe_float(user.get("balance"), 100)
    plan = (user.get("plan") or "FREE").upper()
    filtered_picks = ai_filter_items(picks, message)
    filtered_matches = ai_filter_items(matches, message)

    if any(k in text for k in ["madrid", "barca", "barsa", "barcelona", "lakers", "warriors", "city", "arsenal", "nba", "betis", "sevilla", "atleti", "psg"]):
        if filtered_picks:
            p = filtered_picks[0]
            return (
                "He buscado esa referencia solo dentro de datos reales activos. Coincidencia encontrada:\n"
                f"🦈 {format_pick_line(p)}\n"
                "Te abro Picks para revisarlo completo."
            )
        if filtered_matches:
            m = filtered_matches[0]
            return (
                "He buscado ese partido solo dentro de partidos reales cargados. Coincidencia encontrada:\n"
                f"⚡ {m.get('title','Partido')} · {m.get('league','')} · {m.get('live_status','PROGRAMADO')} {m.get('live_score','')} {m.get('live_minute','')}\n"
                "Te abro Partidos para verlo completo."
            )
        return (
            "No encuentro esa búsqueda en la base real activa. No voy a inventar Madrid-Barça ni ningún partido. "
            "Actualiza API real desde admin o revisa Partidos/Picks cuando entren datos."
        )

    if any(k in text for k in ["partidos", "partido", "directo", "live", "hoy", "nba", "basket", "futbol", "football", "calendario"]):
        items = filtered_matches or matches
        if not items:
            return "Ahora mismo no hay partidos reales cargados desde API/admin. En modo real-only prefiero mostrar vacío antes que partidos falsos."
        lines = []
        for m in items[:4]:
            status = m.get("live_status") or "PROGRAMADO"
            score = f" · {m.get('live_score')}" if m.get("live_score") else ""
            minute = f" · {m.get('live_minute')}" if m.get("live_minute") else ""
            lines.append(f"⚡ {m.get('title','Partido')} · {status}{score}{minute}")
        return "Partidos reales encontrados:\n" + "\n".join(lines) + "\nPulsa el botón para abrir el centro live."

    if any(k in text for k in ["top", "score", "shark", "valor", "cuota", "cuotas", "ev", "seguro", "mejor", "recomiendas", "recomendacion", "recomendacion", "pick de hoy", "picks de hoy", "picks"]):
        items = filtered_picks or picks
        if not items:
            return "Ahora mismo no hay picks reales activos. Cuando entren desde API/admin, los ordenaré por SHARK SCORE, EV, cuota y riesgo."
        p = items[0]
        stake, pct = recommended_stake(balance, plan, p.get("quality"))
        extra = ""
        if len(items) > 1:
            extra = "\nMás opciones reales:\n" + "\n".join("• " + format_pick_line(x) for x in items[1:4])
        return (
            "Mi lectura real ahora mismo:\n"
            f"🦈 {format_pick_line(p)}\n"
            f"Stake sugerido para {plan}: {pct:.2f}% de banca, aprox. {stake:.2f}€."
            f"{extra}\nNo es garantía: es prioridad por valor/riesgo."
        )

    if any(k in text for k in ["tilt", "ansiedad", "perdidas", "perdida", "recuperar", "all in"]):
        return (
            "Modo protección SHARK: si vienes de pérdidas o quieres recuperar rápido, no subiría stake. "
            "Mantén stake fijo, pausa si encadenas 2-3 pérdidas y limita exposición pendiente. "
            "La IA debe ayudarte a decidir mejor, no a perseguir pérdidas."
        )

    if any(k in text for k in ["banca", "bankroll", "stake", "riesgo", "cuanto", "cuanta", "cuánto", "cuánta"]):
        pending = safe_float(stats.get("pending_risk"), 0)
        roi = safe_float(stats.get("roi"), 0)
        profit = safe_float(stats.get("total_profit"), 0)
        quality = best.get("quality") if best else "MEDIA"
        stake, pct = recommended_stake(balance, plan, quality)
        signal = context.get("signal") or {}
        return (
            f"Tu banca registrada es {balance:.2f}€. Riesgo pendiente: {pending:.2f}€ "
            f"({safe_float(signal.get('exposure_pct'), 0):.2f}% de exposición). "
            f"Nivel de riesgo: {signal.get('risk_level', 'BAJO')}. "
            f"Beneficio cerrado: {profit:.2f}€. ROI cerrado: {roi:.2f}%. "
            f"Para un pick de calidad {quality}, usaría {pct:.2f}% de banca: {stake:.2f}€ aprox. "
            "Evita subir stake después de una pérdida."
        )

    if any(k in text for k in ["historial", "mis picks", "guardados", "rendimiento"]):
        if not saved:
            return "Todavía no tienes picks guardados. Guarda picks desde tu dashboard para que pueda analizar tu historial, exposición, beneficio y ROI real."
        return (
            f"Tienes {len(saved)} picks recientes guardados. "
            f"Stake total registrado: {safe_float(stats.get('total_staked'), 0):.2f}€. "
            f"Riesgo pendiente: {safe_float(stats.get('pending_risk'), 0):.2f}€. "
            f"ROI cerrado: {safe_float(stats.get('roi'), 0):.2f}%. "
            "Cuando haya más resultados cerrados podré detectar patrones de ligas, cuotas y riesgo."
        )

    if "ev" in text or "valor esperado" in text:
        return "El valor esperado mide si una cuota parece pagar más de lo que debería según la probabilidad estimada. EV positivo no garantiza ganar, pero ayuda a tomar decisiones rentables a largo plazo."

    if "score" in text or "shark score" in text:
        return "SHARK SCORE™ prioriza picks combinando EV, cuota, riesgo, calidad del mercado y señal premium. Úsalo para ordenar oportunidades, no como promesa de acierto."

    if "premium" in text or "pro" in text or "elite" in text:
        return "FREE usa IA local básica. PRO desbloquea GPT limitado y herramientas avanzadas. ELITE desbloquea GPT premium, prioridad y análisis completo. La IA ajusta el stake sugerido según plan, banca y calidad del pick."

    if best:
        return "Puedo ayudarte con picks, banca, historial, partidos live, EV o SHARK SCORE. Ahora mismo la oportunidad mejor ordenada es: " + format_pick_line(best)

    return "Soy SHARK AI Smart Engine. Puedo buscar partidos reales, picks reales, banca, riesgo y live. Ahora mismo no hay picks reales activos en la base."


def save_ai_log(question, answer, source):
    user = current_user()
    if not user:
        return
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO shark_ai_logs(user_id,question,answer,source) VALUES(?,?,?,?)",
            (user["id"], question[:1000], answer[:4000], source)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass



def user_plan(user=None):
    user = user or current_user() or {}
    plan = str(user.get("plan") or "FREE").upper()
    if plan not in ALL_PLANS:
        plan = "FREE"
    return plan


def gpt_usage_today(user_id):
    if not user_id:
        return 0
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        SELECT COUNT(*) FROM api_usage_logs
        WHERE provider='openai' AND user_id=? AND date(created_at)=date('now')
        """, (user_id,))
        n = int(cur.fetchone()[0] or 0)
        conn.close()
        return n
    except Exception:
        return 0


def ai_access_for_current_user():
    user = current_user()
    plan = user_plan(user)
    limit = PLAN_LIMITS.get(plan, PLAN_LIMITS["FREE"])["gpt_daily"]
    used = gpt_usage_today(user.get("id")) if user else 0
    can_use = bool(OPENAI_API_KEY) and plan in ["PRO", "ELITE", "ADMIN"] and used < limit
    reason = "ok"
    if not OPENAI_API_KEY:
        reason = "openai_not_configured"
    elif plan == "FREE":
        reason = "free_local_only"
    elif used >= limit:
        reason = "daily_limit_reached"
    return {
        "plan": plan,
        "configured": bool(OPENAI_API_KEY),
        "can_use_openai": can_use,
        "daily_limit": limit,
        "used_today": used,
        "remaining_today": max(limit - used, 0) if limit < 9999 else 9999,
        "reason": reason,
    }


@app.route("/api/shark-ai/snapshot")
def shark_ai_snapshot_api():
    gate = require_user()
    if gate:
        return jsonify({"ok": False, "error": "login_required"}), 401
    snap = get_ai_real_snapshot()
    return jsonify({"ok": True, "snapshot": snap, "route_hint": smart_route_hint(request.args.get("q", ""))})

@app.route("/api/openai-status")
def openai_status():
    access = ai_access_for_current_user()
    if access["can_use_openai"]:
        msg = f"OpenAI activo para plan {access['plan']}"
        mode = "openai"
    elif access["reason"] == "free_local_only":
        msg = "Plan FREE: SHARK AI usa modo local sin gastar OpenAI"
        mode = "local_fallback"
    elif access["reason"] == "daily_limit_reached":
        msg = "Límite diario GPT alcanzado: usando fallback local"
        mode = "local_fallback"
    elif access["reason"] == "openai_not_configured":
        msg = "OpenAI no configurado: SHARK AI usa fallback local"
        mode = "local_fallback"
    else:
        msg = "SHARK AI en modo local"
        mode = "local_fallback"
    return jsonify({
        "ok": True,
        "configured": bool(OPENAI_API_KEY),
        "allowed_for_user": access["can_use_openai"],
        "plan": access["plan"],
        "daily_limit": access["daily_limit"],
        "used_today": access["used_today"],
        "remaining_today": access["remaining_today"],
        "mode": mode,
        "model": OPENAI_MODEL,
        "version": APP_VERSION,
        "month_spend_usd": get_api_spend_stats().get("month_cost", 0),
        "message": msg
    })

@app.route("/api/shark-ai", methods=["GET", "POST"])
def shark_ai_api():
    if request.method == "GET":
        context = build_ai_context()
        return jsonify({
            "ok": True,
            "message": "SHARK AI activo.",
            "openai_enabled": bool(OPENAI_API_KEY),
            "ai_access": ai_access_for_current_user(),
            "model": OPENAI_MODEL,
            "user_logged": bool(current_user()),
            "best_pick": context.get("best_pick"),
            "signal": context.get("signal"),
            "route_hint": smart_route_hint(""),
            "suggestions": ["Madrid Barça", "NBA hoy", "Live ahora", "Top SHARK", "Más seguro", "Mi banca"]
        })

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or request.form.get("message") or "").strip()

    if not message:
        return jsonify({"ok": False, "answer": "Escribe una pregunta para SHARK AI."}), 400

    context = build_ai_context()
    fallback = local_ai_answer(message, context)

    access = ai_access_for_current_user()
    if not access["can_use_openai"]:
        suffix = ""
        if access["reason"] == "free_local_only":
            suffix = "\n\n🔒 GPT premium está reservado para PRO y ELITE. Tu respuesta actual está en modo local para no generar coste API."
        elif access["reason"] == "daily_limit_reached":
            suffix = "\n\n⏳ Has alcanzado tu límite GPT diario del plan PRO. Sigo ayudándote en modo local."
        elif access["reason"] == "openai_not_configured":
            suffix = "\n\n⚙️ OpenAI no está configurado en Render; usando fallback local."
        answer_local = fallback + suffix
        save_ai_log(message, answer_local, "local")
        return jsonify({"ok": True, "answer": answer_local, "openai": False, "context_used": True, "ai_access": access, "route_hint": smart_route_hint(message), "snapshot": get_ai_real_snapshot()})

    try:
        answer = call_openai(message, context, fallback)
        save_ai_log(message, answer, "openai")
        return jsonify({"ok": True, "answer": answer, "openai": True, "context_used": True, "ai_access": access, "route_hint": smart_route_hint(message), "snapshot": get_ai_real_snapshot()})
    except Exception:
        save_ai_log(message, fallback, "local_fallback")
        return jsonify({"ok": True, "answer": fallback, "openai": False, "context_used": True, "ai_access": access, "route_hint": smart_route_hint(message), "snapshot": get_ai_real_snapshot()})


@app.route("/api/shark-ai/insights")
def shark_ai_insights():
    context = build_ai_context()
    best = context.get("best_pick")
    user = context.get("usuario") or {}
    stats = context.get("user_stats") or {}
    balance = safe_float(user.get("balance"), 100)
    stake, pct = recommended_stake(balance, user.get("plan", "FREE"), best.get("quality") if best else "MEDIA")
    return jsonify({
        "ok": True,
        "version": APP_VERSION,
        "openai_enabled": bool(OPENAI_API_KEY),
        "ai_access": ai_access_for_current_user(),
        "best_pick": best,
        "risk": {"recommended_percent": pct, "recommended_stake": stake},
        "stats": stats,
        "saved_count": len(context.get("saved_picks") or []),
        "matches": context.get("matches") or [],
        "snapshot": context.get("snapshot") or {},
        "signal": context.get("signal"),
        "suggestions": ["Madrid Barça", "NBA hoy", "Live ahora", "Top SHARK", "Más seguro", "Mi banca"]
    })


def call_openai(message, context, fallback):
    system = (
        "Eres SHARK AI, asistente premium de NeMeSiS SHARK PRO. "
        "Responde siempre en español, con estilo profesional y directo. "
        "Usa solo el contexto entregado para hablar de picks, banca, historial, EV, ROI y SHARK SCORE. "
        "No inventes resultados deportivos, cuotas externas ni datos que no estén en el contexto. "
        "No prometas ganancias ni fomentes apuestas irresponsables. Recomienda gestión de riesgo prudente. "
        "Cuando detectes tilt, recuperación de pérdidas o stake excesivo, prioriza protección de banca."
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "Contexto JSON de la plataforma: " + json.dumps(context, ensure_ascii=False)},
            {"role": "user", "content": message},
        ],
        "temperature": 0.35,
        "max_tokens": 550
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=18) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    usage = data.get("usage") or {}
    input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    output_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
    total_tokens = usage.get("total_tokens") or (int(input_tokens or 0) + int(output_tokens or 0))
    log_api_usage(data.get("model") or OPENAI_MODEL, "/api/shark-ai", input_tokens, output_tokens, total_tokens)

    return data["choices"][0]["message"]["content"].strip() or fallback


# ==========================================================
# ERROR HANDLERS
# ==========================================================
@app.errorhandler(404)
def error_404(e):
    return render_template("error.html", title="Página no encontrada", message="La ruta solicitada no existe."), 404


@app.errorhandler(500)
def error_500(e):
    return render_template("error.html", title="Error interno", message="Se ha producido un error temporal. Vuelve a intentarlo en unos segundos."), 500




# ============================================================
# V27.4 SHARK SCORE ENGINE - cálculo local sin gasto OpenAI
# ============================================================

def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default

def calculate_shark_score(pick=None, live=None, odds=None, user_plan="FREE"):
    """
    Score local premium:
    - No llama OpenAI.
    - Usa cuota, estado live, confianza base y plan.
    - Devuelve puntuación, riesgo, stake recomendado y explicación.
    """
    pick = pick or {}
    live = live or {}
    odds = odds or {}

    cuota = _safe_float(
        pick.get("cuota") or pick.get("odds") or odds.get("price") or odds.get("cuota"),
        1.80
    )

    base_conf = _safe_float(
        pick.get("confidence") or pick.get("confianza") or pick.get("probabilidad"),
        72
    )

    status = str(
        live.get("status") or pick.get("live_status") or pick.get("estado") or ""
    ).lower()

    minute = _safe_float(live.get("minute") or pick.get("minute") or pick.get("minuto"), 0)

    score = base_conf

    # Cuotas demasiado altas suelen implicar más riesgo
    if cuota <= 1.35:
        score += 4
    elif cuota <= 1.85:
        score += 7
    elif cuota <= 2.40:
        score += 2
    elif cuota <= 3.20:
        score -= 6
    else:
        score -= 12

    # Ajuste live básico
    if "live" in status or "1h" in status or "2h" in status or minute > 0:
        score += 3
        if minute >= 70:
            score -= 2

    # Planes premium ven una lectura más completa, pero el score base no se infla artificialmente
    plan = str(user_plan or "FREE").upper()
    if plan == "ELITE":
        model_label = "ELITE"
    elif plan == "PRO":
        model_label = "PRO"
    elif plan == "ADMIN":
        model_label = "ADMIN"
    else:
        model_label = "BASIC"

    score = max(1, min(99, round(score)))

    if score >= 82:
        risk = "Bajo"
        badge = "🟢"
        stake = 3.0
        verdict = "Pick fuerte con buena relación confianza/riesgo."
    elif score >= 68:
        risk = "Medio"
        badge = "🟡"
        stake = 2.0
        verdict = "Pick interesante, conviene controlar stake."
    else:
        risk = "Alto"
        badge = "🔴"
        stake = 1.0
        verdict = "Pick agresivo: mejor stake bajo o esperar confirmación."

    if cuota >= 2.8:
        stake = max(0.5, stake - 0.5)
    if score >= 88 and cuota <= 2.10:
        stake = min(4.0, stake + 0.5)

    return {
        "score": score,
        "risk": risk,
        "risk_badge": badge,
        "stake": stake,
        "verdict": verdict,
        "model": model_label,
        "odds": cuota,
        "live_status": status or "pre-match"
    }



@app.context_processor
def inject_shark_score_helpers():
    return dict(calculate_shark_score=calculate_shark_score)

@app.route("/api/shark-score")
def api_shark_score():
    """
    Endpoint ligero para frontend.
    Lee parámetros simples y calcula score local sin gastar OpenAI.
    """
    try:
        pick = {
            "cuota": request.args.get("cuota") or request.args.get("odds"),
            "confidence": request.args.get("confidence") or request.args.get("confianza"),
            "estado": request.args.get("estado"),
            "minute": request.args.get("minute") or request.args.get("minuto"),
        }
        user_plan = session.get("user_plan") or session.get("plan") or ("ADMIN" if session.get("admin_logged") else "FREE")
        return jsonify({
            "ok": True,
            "shark_score": calculate_shark_score(pick=pick, user_plan=user_plan)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/admin-api-control")
def admin_api_control():
    if not is_admin():
        return redirect("/admin-login")
    return render_template(
        "admin_api_control.html",
        limits=PLAN_AI_LIMITS
    )


try:
    cleanup_demo_picks_prod()
except Exception:
    pass


@app.route("/admin-shark-engine", methods=["GET", "POST"])
def admin_shark_engine():
    if not is_admin():
        return redirect("/admin-login")
    result = None
    saved = None
    if request.method == "POST":
        force = request.form.get("force") == "1"
        result = shark_auto_engine_fetch(force=force)
        saved = save_shark_engine_picks_to_db(result.get("picks", []))
    else:
        result = shark_auto_engine_fetch(force=False)
    return render_template("admin_shark_engine.html", result=result, saved=saved)

@app.route("/api/shark-engine")
def api_shark_engine():
    gate = require_user()
    if gate:
        return jsonify({"ok": False, "error": "login_required"}), 401
    result = shark_auto_engine_fetch(force=False)
    return jsonify(result)



@app.route("/admin-memberships", methods=["GET", "POST"])
def admin_memberships():
    if not is_admin():
        return redirect("/admin-login")

    message = None
    error = None

    if request.method == "POST":
        try:
            user_id = int(request.form.get("user_id"))
            new_plan = normalize_plan(request.form.get("plan"), allow_admin=False)

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT id, username, role FROM users WHERE id=?", (user_id,))
            target = cur.fetchone()

            if not target:
                error = "Usuario no encontrado."
            elif target["role"] == "admin":
                error = "El usuario ADMIN no se cambia desde membresías públicas."
            else:
                source = request.form.get("membership_source", "admin_manual").strip() or "admin_manual"
                auto_expire = 1 if request.form.get("auto_expire") == "1" and new_plan in ("PRO","ELITE") else 0
                months = int(request.form.get("months", "1") or 1)
                now_iso = madrid_iso_now()
                expires = add_months_madrid(months) if auto_expire else ""
                note = request.form.get("membership_note", "").strip()
                cur.execute("""
                    UPDATE users
                    SET plan=?, role='cliente', membership_source=?, membership_started_at=?, membership_expires_at=?,
                        membership_auto_expire=?, membership_note=?
                    WHERE id=?
                """, (new_plan, source, now_iso if new_plan in ("PRO","ELITE") else "", expires, auto_expire, note, user_id))
                cur.execute("INSERT INTO user_activity(user_id,username,action,detail,created_at) VALUES(?,?,?,?,?)",
                            (user_id, target["username"], "cambio_membresia", f"{new_plan} · {source}", now_iso))
                conn.commit()
                message = f"Membresía actualizada a {new_plan}."

                # Si el usuario cambiado es el usuario logueado, refrescar sesión.
                try:
                    sync_session_if_same_user(user_id)
                except Exception:
                    pass

            conn.close()
        except Exception:
            error = "No se pudo actualizar la membresía."

    users = get_all_users_for_admin()
    return render_template("admin_memberships.html", users=users, message=message, error=error)



@app.context_processor
def inject_v48_helpers():
    return dict(days_until_iso=days_until_iso, membership_badge_text=membership_badge_text)


@app.route("/api/real-picks")
def api_real_picks():
    gate = require_user()
    if gate:
        return jsonify({"ok": False, "error": "login_required"}), 401
    return jsonify({"ok": True, "picks": get_real_picks_for_ai(limit=20)})



# ===================== V59 SECURITY + ADMIN OBSERVABILITY =====================
SECURITY_LOG_MAX_ROWS = int(os.environ.get("SECURITY_LOG_MAX_ROWS", "800"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_LOGIN_MAX = int(os.environ.get("RATE_LIMIT_LOGIN_MAX", "12"))
RATE_LIMIT_AI_MAX = int(os.environ.get("RATE_LIMIT_AI_MAX", "30"))
_rate_limit_bucket = {}


def ensure_v59_security_tables():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                username TEXT,
                ip TEXT,
                path TEXT,
                detail TEXT,
                created_at TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)")
        conn.commit()
        conn.close()
    except Exception:
        pass


def security_log(event_type, detail="", username=None):
    try:
        ensure_v59_security_tables()
        uname = username or session.get("username") or ""
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO security_events(event_type,username,ip,path,detail,created_at) VALUES(?,?,?,?,?,?)",
                    (event_type, uname, ip, request.path, str(detail)[:300], madrid_iso_now()))
        cur.execute("DELETE FROM security_events WHERE id NOT IN (SELECT id FROM security_events ORDER BY id DESC LIMIT ?)", (SECURITY_LOG_MAX_ROWS,))
        conn.commit(); conn.close()
    except Exception:
        pass


def rate_limit_key(kind):
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "local").split(",")[0].strip()
    return f"{kind}:{ip}:{session.get('username','anon')}"


def allow_rate(kind, max_hits):
    now = time.time()
    key = rate_limit_key(kind)
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    hits = [t for t in _rate_limit_bucket.get(key, []) if t >= window_start]
    if len(hits) >= max_hits:
        security_log("rate_limit", f"{kind} bloqueado")
        _rate_limit_bucket[key] = hits
        return False
    hits.append(now)
    _rate_limit_bucket[key] = hits
    return True


@app.before_request
def v59_request_guard():
    # Guard ligero: no bloquea archivos estáticos ni healthchecks.
    if request.path.startswith('/static') or request.path in ('/healthz', '/manifest.json', '/service-worker.js'):
        return None
    if request.endpoint in (None,):
        return None
    if request.path in ('/login', '/admin-login') and request.method == 'POST':
        if not allow_rate('login', RATE_LIMIT_LOGIN_MAX):
            return render_template('error.html', message='Demasiados intentos. Espera un minuto y vuelve a probar.'), 429
    if request.path.startswith('/api/shark-ai') or request.path.startswith('/api/shark'):
        if not allow_rate('ai', RATE_LIMIT_AI_MAX):
            return jsonify({'ok': False, 'error': 'Demasiadas peticiones. Prueba de nuevo en un momento.'}), 429
    return None


@app.after_request
def v59_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    return response


def v59_backup_sqlite():
    try:
        src = DB_PATH
        if not os.path.exists(src):
            return {"ok": False, "message": "Base de datos no encontrada"}
        backup_dir = os.environ.get("BACKUP_DIR", "/data/backups")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = madrid_now().strftime('%Y%m%d_%H%M%S')
        dst = os.path.join(backup_dir, f"nemesis_backup_{stamp}.db")
        import shutil
        shutil.copy2(src, dst)
        # conservar últimas 10 copias
        files = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')])
        for old in files[:-10]:
            try: os.remove(old)
            except Exception: pass
        return {"ok": True, "file": os.path.basename(dst)}
    except Exception as e:
        return {"ok": False, "message": str(e)[:160]}


@app.route('/api/security-status')
def api_security_status():
    if not is_admin():
        return jsonify({'ok': False, 'error': 'admin_required'}), 403
    ensure_v59_security_tables()
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT event_type, COUNT(*) c FROM security_events GROUP BY event_type ORDER BY c DESC LIMIT 8")
        by_type = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT event_type, username, ip, path, detail, created_at FROM security_events ORDER BY id DESC LIMIT 30")
        events = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return jsonify({'ok': True, 'by_type': by_type, 'events': events, 'rate_keys': len(_rate_limit_bucket)})


@app.route('/admin/security', methods=['GET','POST'])
def admin_security_center():
    if not is_admin():
        return redirect('/admin-login')
    ensure_v59_security_tables()
    message = None
    if request.method == 'POST' and request.form.get('action') == 'backup':
        res = v59_backup_sqlite()
        message = 'Backup creado: ' + res.get('file','') if res.get('ok') else 'No se pudo crear backup: ' + res.get('message','')
        security_log('backup', message)
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT event_type, COUNT(*) c FROM security_events GROUP BY event_type ORDER BY c DESC LIMIT 10")
    by_type = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT event_type, username, ip, path, detail, created_at FROM security_events ORDER BY id DESC LIMIT 80")
    events = [dict(r) for r in cur.fetchall()]
    conn.close()
    return render_template('admin_security.html', events=events, by_type=by_type, message=message)


@app.route('/api/live-card-check')
def api_live_card_check():
    if not is_admin():
        return jsonify({'ok': False, 'error': 'admin_required'}), 403
    # Revisión ligera de datos que usan las tarjetas live sin forzar API externa.
    payload = {'ok': True, 'checks': []}
    try:
        conn = get_db(); cur = conn.cursor()
        tables = ['matches','picks','telegram_alerts','user_activity']
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) c FROM {t}")
                payload['checks'].append({'name': t, 'ok': True, 'count': cur.fetchone()['c']})
            except Exception as e:
                payload['checks'].append({'name': t, 'ok': False, 'detail': str(e)[:80]})
        conn.close()
    except Exception as e:
        payload['ok'] = False; payload['error'] = str(e)[:120]
    return jsonify(payload)
# =================== END V59 SECURITY + ADMIN OBSERVABILITY ===================



# =================== V60 TELEGRAM DELIVERY ENGINE + DEBUG CENTER ===================
TELEGRAM_DEBUG_MODE = os.environ.get("TELEGRAM_DEBUG_MODE", "true").lower() == "true"
TELEGRAM_RETRY_ON_FAIL = os.environ.get("TELEGRAM_RETRY_ON_FAIL", "true").lower() == "true"
TELEGRAM_MAX_RETRIES = int(os.environ.get("TELEGRAM_MAX_RETRIES", "3") or 3)
TELEGRAM_FORCE_TEST_ALERTS = os.environ.get("TELEGRAM_FORCE_TEST_ALERTS", "true").lower() == "true"


def telegram_last_logs(limit=80):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT * FROM alert_logs
            WHERE channel LIKE '%telegram%' OR kind LIKE '%telegram%' OR kind IN ('new_pick','odds_auto_pick','channel_pick','user_pick','manual_resend','telegram_test','telegram_pick_test')
            ORDER BY id DESC LIMIT ?
        """, (int(limit),))
        rows = cur.fetchall(); conn.close()
        return rows
    except Exception:
        return []


def telegram_debug_summary():
    status = telegram_config_status() if 'telegram_config_status' in globals() else {}
    try:
        pending = send_pending_telegram_signals(limit=0) if False else {"ok": True}
    except Exception:
        pending = {"ok": False}
    return {
        "enabled": bool(ENABLE_PRO_ALERTS),
        "ready": bool(telegram_ready()),
        "bot_token_set": bool(TELEGRAM_BOT_TOKEN),
        "general_chat_id_set": bool(TELEGRAM_CHAT_ID),
        "plan_channels_enabled": bool(TELEGRAM_SEND_TO_PLAN_CHANNELS),
        "connected_users_enabled": bool(TELEGRAM_SEND_TO_CONNECTED_USERS),
        "auto_engine": bool(TELEGRAM_AUTO_ALERT_ENGINE),
        "new_picks": bool(TELEGRAM_ALERT_NEW_PICKS),
        "quiet_hours": bool(TELEGRAM_QUIET_HOURS),
        "quiet_now": bool(telegram_is_quiet_now()),
        "min_score": int(TELEGRAM_ALERT_MIN_SCORE),
        "odds_min_score": int(TELEGRAM_ODDS_ALERT_MIN_SCORE),
        "chat_id_preview": (str(TELEGRAM_CHAT_ID)[:6] + "…" + str(TELEGRAM_CHAT_ID)[-4:]) if TELEGRAM_CHAT_ID else "",
        "status": status,
        "debug_mode": bool(TELEGRAM_DEBUG_MODE),
        "retry_on_fail": bool(TELEGRAM_RETRY_ON_FAIL),
        "max_retries": int(TELEGRAM_MAX_RETRIES),
    }


def send_telegram_message_with_retry(chat_id, body, kind="telegram", title="Mensaje SHARK", payload=None):
    attempts = max(1, int(TELEGRAM_MAX_RETRIES if TELEGRAM_RETRY_ON_FAIL else 1))
    last = None
    for attempt in range(1, attempts + 1):
        res = send_telegram_message(chat_id, body, kind=kind, title=title, payload={**(payload or {}), "attempt": attempt})
        last = res
        if res and res.get("ok"):
            return res
        try:
            time.sleep(min(0.4 * attempt, 1.2))
        except Exception:
            pass
    return last or {"ok": False, "reason": "unknown"}


@app.route('/api/telegram-status')
def api_telegram_status():
    if not is_admin():
        return jsonify({'ok': False, 'error': 'admin_required'}), 403
    return jsonify({'ok': True, **telegram_debug_summary()})


@app.route('/admin/telegram')
def admin_telegram_center():
    if not is_admin():
        return redirect('/admin-login')
    logs = telegram_last_logs(100)
    # Últimos picks candidatos, sin forzar APIs externas.
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""
            SELECT * FROM picks
            WHERE active=1
            ORDER BY CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC
            LIMIT 20
        """)
        picks = cur.fetchall(); conn.close()
    except Exception:
        picks = []
    return render_template('admin_telegram.html', tg=telegram_debug_summary(), logs=logs, picks=picks)


@app.route('/admin/telegram/test', methods=['POST'])
def admin_telegram_test():
    if not is_admin():
        return redirect('/admin-login')
    chat_id = request.form.get('chat_id','').strip() or TELEGRAM_TEST_CHAT_ID or TELEGRAM_CHAT_ID
    body = "🦈 <b>Prueba NeMeSiS SHARK PRO</b>\n\n✅ Telegram está conectado correctamente.\nSi ves este mensaje, el canal y el bot funcionan."
    send_telegram_message_with_retry(chat_id, body, kind='telegram_test', title='Prueba Telegram', payload={'manual': True})
    return redirect('/admin/telegram')


@app.route('/admin/telegram/test-pick', methods=['POST'])
def admin_telegram_test_pick():
    if not is_admin():
        return redirect('/admin-login')
    try:
        pick_id = int(request.form.get('pick_id','0') or 0)
    except Exception:
        pick_id = 0
    if pick_id:
        send_pick_alert(pick_id, kind='telegram_pick_test', force=bool(TELEGRAM_FORCE_TEST_ALERTS))
    else:
        # Buscar mejor pick activo y enviarlo forzado para probar el flujo completo.
        try:
            conn = get_db(); cur = conn.cursor()
            cur.execute("""
                SELECT id FROM picks WHERE active=1
                ORDER BY CAST(COALESCE(score,0) AS INTEGER) DESC, id DESC LIMIT 1
            """)
            row = cur.fetchone(); conn.close()
            if row:
                send_pick_alert(int(row['id']), kind='telegram_pick_test', force=bool(TELEGRAM_FORCE_TEST_ALERTS))
            else:
                log_alert('telegram_pick_test', 'Sin picks', 'No hay picks activos para probar Telegram.', 'system', 'empty', {})
        except Exception as e:
            log_alert('telegram_pick_test', 'Error prueba pick', str(e)[:200], 'system', 'error', {})
    return redirect('/admin/telegram')


@app.route('/admin/telegram/send-pending', methods=['POST'])
def admin_telegram_send_pending():
    if not is_admin():
        return redirect('/admin-login')
    try:
        limit = int(request.form.get('limit','3') or 3)
    except Exception:
        limit = 3
    res = send_pending_telegram_signals(limit=limit)
    log_alert('telegram_manual_pending', 'Enviar pendientes', str(res)[:500], 'system', 'ok' if res.get('ok') else 'blocked', {'limit': limit})
    return redirect('/admin/telegram')
# =================== END V60 TELEGRAM DELIVERY ENGINE + DEBUG CENTER ===================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))


# -------------------------------------------------------------------
# V69 MACHINE LEARNING FOUNDATION - safe registration
# -------------------------------------------------------------------
try:
    from ml_foundation.ml_schema import init_ml_tables
    init_ml_tables()
except Exception as e:
    print("[V69 ML] init warning:", e)

try:
    from ml_foundation.ml_routes import ml_bp
    app.register_blueprint(ml_bp)
except Exception as e:
    print("[V69 ML] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V70 ULTIMATE UI POLISH - safe registration
# -------------------------------------------------------------------
try:
    from ui_v70.routes import ui_v70_bp
    app.register_blueprint(ui_v70_bp)
except Exception as e:
    print("[V70 UI] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V71 SECURITY + SCALE HARDENING - safe registration
# -------------------------------------------------------------------
try:
    from security_v71.hardening import install_v71_hardening
    install_v71_hardening(app)
except Exception as e:
    print("[V71 Security] hardening warning:", e)

try:
    from security_v71.routes import security_v71_bp
    app.register_blueprint(security_v71_bp)
except Exception as e:
    print("[V71 Security] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V72 LAUNCH READINESS + BETA SYSTEM - safe registration
# -------------------------------------------------------------------
try:
    from launch_v72.launch_schema import init_launch_tables
    init_launch_tables()
except Exception as e:
    print("[V72 Launch] init warning:", e)

try:
    from launch_v72.routes import launch_v72_bp
    app.register_blueprint(launch_v72_bp)
except Exception as e:
    print("[V72 Launch] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V73 OBSERVABILITY + ERROR TRACKING PRO - safe registration
# -------------------------------------------------------------------
try:
    from observability_v73.observability_schema import init_observability_tables
    init_observability_tables()
except Exception as e:
    print("[V73 Observability] init warning:", e)

try:
    from observability_v73.middleware import install_v73_observability
    install_v73_observability(app)
except Exception as e:
    print("[V73 Observability] middleware warning:", e)

try:
    from observability_v73.routes import observability_v73_bp
    app.register_blueprint(observability_v73_bp)
except Exception as e:
    print("[V73 Observability] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V74 UX AUTOMATION + RETENTION ENGINE - safe registration
# -------------------------------------------------------------------
try:
    from retention_v74.retention_schema import init_retention_tables
    init_retention_tables()
except Exception as e:
    print("[V74 Retention] init warning:", e)

try:
    from retention_v74.routes import retention_v74_bp
    app.register_blueprint(retention_v74_bp)
except Exception as e:
    print("[V74 Retention] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V75-V78 FINAL PRE-STRIPE SUITE - safe registration
# -------------------------------------------------------------------
try:
    from personalization_v75.personalization_schema import init_personalization_tables
    init_personalization_tables()
except Exception as e:
    print("[V75 Personalization] init warning:", e)

try:
    from personalization_v75.routes import personalization_v75_bp
    app.register_blueprint(personalization_v75_bp)
except Exception as e:
    print("[V75 Personalization] blueprint warning:", e)

try:
    from community_v76.community_schema import init_community_tables
    init_community_tables()
except Exception as e:
    print("[V76 Community] init warning:", e)

try:
    from community_v76.routes import community_v76_bp
    app.register_blueprint(community_v76_bp)
except Exception as e:
    print("[V76 Community] blueprint warning:", e)

try:
    from performance_v77.performance_engine import optimize_sqlite
    optimize_sqlite()
except Exception as e:
    print("[V77 Performance] optimize warning:", e)

try:
    from performance_v77.routes import performance_v77_bp
    app.register_blueprint(performance_v77_bp)
except Exception as e:
    print("[V77 Performance] blueprint warning:", e)

try:
    from launch_candidate_v78.routes import launch_candidate_v78_bp
    app.register_blueprint(launch_candidate_v78_bp)
except Exception as e:
    print("[V78 Launch Candidate] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V79 SHARK AI REAL EVOLUTION - safe registration
# -------------------------------------------------------------------
try:
    from shark_ai_v79.shark_ai_schema import init_shark_ai_v79_tables
    init_shark_ai_v79_tables()
except Exception as e:
    print("[V79 SHARK AI] init warning:", e)

try:
    from shark_ai_v79.routes import shark_ai_v79_bp
    app.register_blueprint(shark_ai_v79_bp)
except Exception as e:
    print("[V79 SHARK AI] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V80 ENTERPRISE SCALE FOUNDATION - safe registration
# -------------------------------------------------------------------
try:
    from enterprise_v80.database import init_enterprise_db_settings
    init_enterprise_db_settings()
except Exception as e:
    print("[V80 Enterprise] db settings warning:", e)

try:
    from enterprise_v80.queue import init_enterprise_queue
    init_enterprise_queue()
except Exception as e:
    print("[V80 Enterprise] queue init warning:", e)

try:
    from enterprise_v80.routes import enterprise_v80_bp
    app.register_blueprint(enterprise_v80_bp)
except Exception as e:
    print("[V80 Enterprise] blueprint warning:", e)
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# V81 APP TOP COMERCIAL - safe registration
# -------------------------------------------------------------------
try:
    from commercial_v81.commercial_schema import init_commercial_tables
    init_commercial_tables()
except Exception as e:
    print("[V81 Commercial] init warning:", e)

try:
    from commercial_v81.routes import commercial_v81_bp
    app.register_blueprint(commercial_v81_bp)
except Exception as e:
    print("[V81 Commercial] blueprint warning:", e)
# -------------------------------------------------------------------
