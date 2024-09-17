{
    'name': 'Growth Calculator',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Module for Growth Calculator Snippet',
    'description': """
        This module adds a growth calculator snippet to the website.
    """,
    'author': 'Oussama Bouhlel',
    'website': 'https://www.harmoniesante.com',
    'depends': ['website'],
    'data': [
        'views/snippet_growth_calculator.xml',
        'views/snippet_growth_calculator_assets.xml',
        'views/snippet_growth_calculator_category.xml',
    ],
    'assets': {
        'website.assets_frontend': [
            'snippet_growth_calculator/static/src/css/growth_calculator.css',
            'snippet_growth_calculator/static/src/js/growth_calculator.js',
            'https://stackpath.bootstrapcdn.com/bootstrap/5.3.3/css/bootstrap.min.css',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',
            'https://cdn.jsdelivr.net/npm/chart.js@3.8.0/dist/chart.min.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
