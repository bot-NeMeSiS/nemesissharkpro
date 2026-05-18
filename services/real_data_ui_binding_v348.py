
def ui_binding_status():
    return {
        "ok": True,
        "version": "V348",
        "name": "REAL_DATA_UI_BINDING_PRO",
        "real_only": True,
        "binds": [
            "home_client",
            "live_command_center",
            "match_center",
            "one_x2",
            "favorites",
            "shark"
        ],
        "uses": [
            "V347 normalized sample",
            "fallback crests",
            "score/minute contract",
            "LOW DATA state"
        ],
        "routes": [
            "/cliente/real-data-ui",
            "/api/client/real-data-ui/status-v348",
            "/api/live/normalizer/sample-v347"
        ]
    }
