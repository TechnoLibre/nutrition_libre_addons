{
    'name': 'Recipe Snippet',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Snippet to manage dynamic recipes on the website',
    'description': """
        This module allows users to view, add, and manage recipes dynamically on the website,
        including adding ingredients and steps to each recipe.
    """,
    'author': 'Oussama Bouhlel',
    'website': 'https://www.harmoniesante.com',
    'depends': ['website'],
    'data': [
        'views/recipe_snippet_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'Snippet_recettes/static/src/js/recipe_snippet.js',
            'Snippet_recettes/static/css/recipe_snippet.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}