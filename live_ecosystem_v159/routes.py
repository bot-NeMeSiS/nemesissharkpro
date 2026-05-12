from flask import Blueprint, jsonify, render_template, session, request
from datetime import datetime

live_ecosystem_v159_bp = Blueprint('live_ecosystem_v159_bp', __name__)


def _uid():
    try:
        return str(session.get('user_id') or session.get('username') or session.get('user') or 'default')
    except Exception:
        return 'default'


def _home_live(user_id=None):
    try:
        from favorites_home_v150.core import build_home_live
        return build_home_live(user_id or _uid())
    except Exception as exc:
        return {
            'version': 'V159_LIVE_ECOSYSTEM_EXPERIENCE_PRO',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'favorites': [], 'favorite_matches': [], 'live_matches': [], 'upcoming_matches': [], 'feed': [],
            'empty_state': True,
            'error': str(exc),
            'policy': {'no_fake_matches': True, 'no_fake_feed': True, 'real_core_first': True}
        }


def _status_text(match):
    raw = str(match.get('status') or '').lower()
    minute = match.get('minute') or match.get('elapsed') or ''
    if raw in ['live', 'inplay', 'in_play', '1h', '2h', 'ht']:
        return f"{minute}'" if minute else 'LIVE'
    if raw in ['finished', 'final', 'ft']:
        return 'FINAL'
    return 'PRÓXIMO'


def _match_href(match):
    fid = match.get('id') or match.get('fixture_id') or match.get('event_id') or ''
    return f"/partido-pro/{fid}" if fid else '/match-center-pro'


def _normalize_match(match, idx=0):
    home = match.get('home_team') or match.get('home') or 'Equipo local'
    away = match.get('away_team') or match.get('away') or 'Equipo visitante'
    league = match.get('league') or match.get('competition') or 'Liga real'
    status = _status_text(match)
    is_live = status == 'LIVE' or status.endswith("'")
    score_home = match.get('home_score')
    score_away = match.get('away_score')
    if score_home is None or score_away is None:
        score = 'vs'
    else:
        score = f'{score_home} - {score_away}'
    return {
        'id': match.get('id') or match.get('fixture_id') or idx,
        'home_team': home,
        'away_team': away,
        'league': league,
        'status': status,
        'is_live': is_live,
        'score': score,
        'kickoff': match.get('kickoff') or match.get('date') or '',
        'href': _match_href(match),
        'shark_signal': 'Partido caliente' if is_live else 'Seguimiento preparado',
        'momentum_label': 'LIVE' if is_live else 'PRE',
    }


def build_live_ecosystem(user_id=None):
    data = _home_live(user_id)
    live = [_normalize_match(m, i) for i, m in enumerate(data.get('live_matches') or [])]
    favs = [_normalize_match(m, i) for i, m in enumerate(data.get('favorite_matches') or [])]
    upcoming = [_normalize_match(m, i) for i, m in enumerate(data.get('upcoming_matches') or [])]
    feed = list(data.get('feed') or [])[:12]
    hot = (live + favs + upcoming)[:10]
    ticker = live[:8] or favs[:8] or upcoming[:8]
    signals = []
    if live:
        signals.append({'level': 'live', 'title': 'Directos reales activos', 'text': f'{len(live)} partido(s) en seguimiento real.'})
    if favs:
        signals.append({'level': 'favorite', 'title': 'Favoritos activos', 'text': f'{len(favs)} favorito(s) con partido asociado.'})
    if not signals:
        signals.append({'level': 'empty', 'title': 'Real Core esperando datos', 'text': 'No se inventan partidos: cuando haya fixtures reales aparecerán aquí.'})
    return {
        'ok': True,
        'version': 'V159_LIVE_ECOSYSTEM_EXPERIENCE_PRO',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'real_only': True,
        'no_fake_policy': True,
        'counts': {
            'live': len(live), 'favorites': len(data.get('favorites') or []),
            'favorite_matches': len(favs), 'upcoming': len(upcoming), 'feed': len(feed), 'hot': len(hot)
        },
        'ticker': ticker,
        'hot_matches': hot,
        'live_matches': live,
        'favorite_matches': favs,
        'upcoming_matches': upcoming,
        'recent_activity': feed,
        'shark_signals': signals,
        'empty_state': not bool(ticker or hot or feed),
        'policy': data.get('policy') or {'no_fake_matches': True, 'no_fake_feed': True, 'real_core_first': True}
    }


@live_ecosystem_v159_bp.route('/api/v159/live-ecosystem')
def api_live_ecosystem():
    return jsonify(build_live_ecosystem(request.args.get('user_id') or _uid()))


@live_ecosystem_v159_bp.route('/api/v159/recent-activity')
def api_recent_activity():
    data = build_live_ecosystem(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'recent_activity': data['recent_activity'], 'counts': data['counts']})


@live_ecosystem_v159_bp.route('/api/v159/shark-signals')
def api_shark_signals():
    data = build_live_ecosystem(request.args.get('user_id') or _uid())
    return jsonify({'ok': True, 'version': data['version'], 'signals': data['shark_signals'], 'real_only': True})


@live_ecosystem_v159_bp.route('/live-ecosystem')
@live_ecosystem_v159_bp.route('/cliente/live-ecosystem')
@live_ecosystem_v159_bp.route('/home-live-pro')
def page_live_ecosystem():
    return render_template('live_ecosystem_v159.html', data=build_live_ecosystem(_uid()))
