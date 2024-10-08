# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Nutrition Libre Migrate phase 1 clienta",
    "version": "16.0.0.1",
    "author": "TechnoLibre",
    "website": "https://technolibre.ca",
    "license": "AGPL-3",
    "category": "Extra tools",
    "summary": "Migrate database of project clienta",
    "description": """
Migrate phase 1 for ClientA
===========================
""",
    "depends": [],
    "external_dependencies": {
        "python": [
            "pymssql",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
}
