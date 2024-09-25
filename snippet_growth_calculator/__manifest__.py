{
    'name': 'Growth Calculator',
    'version': '16.0.1.0.0',
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
        'views/snippet_growth_calculator_category.xml',
    ],
    'assets': {
        'website.assets_frontend': [
            '/snippet_growth_calculator/static/src/css/growth_calculator.css',
            '/snippet_growth_calculator/static/src/css/bootstrap.min.css',
            '/snippet_growth_calculator/static/src/css/all.min.css',
            '/snippet_growth_calculator/static/src/js/growth_calculator.js',
            '/snippet_growth_calculator/static/src/js/bootstrap.bundle.min.js',
            '/snippet_growth_calculator/static/src/js/chart.min.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
