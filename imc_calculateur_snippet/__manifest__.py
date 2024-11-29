{
    'name': 'IMC Calculateur Snippet',
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Snippet pour calculer l\'IMC et le percentile',
    'author': 'Adil Goumih',
    'website': 'https://www.votresite.com',
    'depends': ['website'],
    'data': [
        'views/snippets/imc_calculateur_snippet.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/imc_calculateur_snippet/static/src/css/imc_calculateur_style.css',
            '/imc_calculateur_snippet/static/src/js/imc_calculateur.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
