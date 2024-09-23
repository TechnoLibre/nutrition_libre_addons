{
    'name': 'Techno Recette',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Proposer et gérer des recettes sur le site web',
    'description': """Application permettant aux utilisateurs de proposer des recettes alimentaires""",
    'author': 'Adil',
    'website': 'https://www.votre-site.com',
    'depends': ['website'],
    'data': [
        'security/recette_security.xml',
        'security/ir.model.access.csv',
        'views/recette_views.xml',
        'views/snippet_templates.xml',
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'techno_recette/static/src/css/recette_snippet.css',
            'techno_recette/static/src/js/recette_snippet.js',
        ],
    },
    'application': True,
    'installable': True,
}
