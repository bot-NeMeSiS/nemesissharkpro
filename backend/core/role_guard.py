def has_access(user_plan, required_plan):
    hierarchy = {
        "FREE": 0,
        "PRO": 1,
        "ELITE": 2
    }
    return hierarchy.get(user_plan, 0) >= hierarchy.get(required_plan, 0)
