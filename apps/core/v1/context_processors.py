"""Navigation tree shared with every template via the context.

Keeping the sidebar structure in Python (not parsed from template strings)
makes it trivial to reorder modules or gate items by role later.
"""

NAV_GROUPS = [
    {
        "label": "Environmental", "icon": "🌱", "color": "text-emerald-400",
        "page": "environmental",
        "items": [
            ("Emission Factors", "emission-factors"),
            ("Product ESG Profiles", "products"),
            ("Carbon Transactions", "carbon"),
            ("Environmental Goals", "goals"),
        ],
    },
    {
        "label": "Social", "icon": "🤝", "color": "text-sky-400",
        "page": "social",
        "items": [
            ("CSR Activities", "csr"),
            ("Employee Participation", "participation"),
            ("Diversity Dashboard", "diversity"),
        ],
    },
    {
        "label": "Governance", "icon": "🏛️", "color": "text-violet-400",
        "page": "governance",
        "items": [
            ("Policies", "policies"),
            ("Policy Acknowledgements", "acks"),
            ("Audits", "audits"),
            ("Compliance Issues", "issues"),
        ],
    },
    {
        "label": "Gamification", "icon": "🏆", "color": "text-amber-400",
        "page": "gamification",
        "items": [
            ("Challenges", "challenges"),
            ("Challenge Participation", "challenge-participation"),
            ("Badges", "badges"),
            ("Rewards", "rewards"),
            ("Leaderboard", "leaderboard"),
        ],
    },
    {
        "label": "Reports", "icon": "📄", "color": "text-slate-300",
        "page": "reports",
        "items": [
            ("Environmental Report", "environmental"),
            ("Social Report", "social"),
            ("Governance Report", "governance"),
            ("ESG Summary", "esg"),
            ("Custom Report Builder", "custom"),
        ],
    },
    {
        "label": "Settings", "icon": "⚙️", "color": "text-slate-300",
        "page": "settings",
        "items": [
            ("Departments", "departments"),
            ("Categories", "categories"),
            ("ESG Configuration", "esg"),
            ("Notification Settings", "notifications"),
        ],
    },
]


def navigation(request):
    return {"nav_groups": NAV_GROUPS}
