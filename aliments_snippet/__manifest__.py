{
    'name': 'Aliments Snippet',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Ajoute un snippet pour afficher une liste d\'aliments',
    'author': 'Heritiana Ravelojaona',
    'website': 'https://www.heritiana.com',
    'depends': ['website', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/aliment_views.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'aliments_snippet/static/src/js/snippet.js',
            'aliments_snippet/static/src/scss/snippet.scss',
            'aliments_snippet/static/src/xml/snippet.xml',
        ],
    },
    'images': ['static/src/img/icon.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',

}
