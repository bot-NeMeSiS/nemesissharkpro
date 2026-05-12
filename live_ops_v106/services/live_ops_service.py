
from live_ops_v106.core.unified_ops_engine import build_live_ops_status, build_visible_routes_map, module_status
try:
    from auto_pick_v104.engine import scan_auto_picks
except Exception:
    scan_auto_picks = None

def run_safe_auto_scan(matches):
    if scan_auto_picks is None:
        return {
            "ok": False,
            "reason": "Auto Pick Engine no disponible.",
            "candidates": []
        }
    result = scan_auto_picks(matches or [], min_score=68, max_results=30, include_rejected=False)
    return {
        "ok": True,
        **result
    }

def get_ops_dashboard():
    status = build_live_ops_status()
    routes = build_visible_routes_map()
    return {
        **status,
        "routes": routes,
        "ops_message": "V106 unifica navegación, módulos, estado live, admin y control operativo."
    }

def get_modules():
    return module_status()
