{
    'name': 'Harmonie Certification',
    'version': '1.0',
    'category': 'Training',
    'summary': 'Gestion des certifications pour Harmonie Santé',
    'description': """
        Ce module permet de gérer les certifications des formations 
        d'Harmonie Santé, incluant la génération automatique d'attestations.
    """,
    'author': 'Votre Nom',
    'website': 'https://www.harmoniesante.com',
    'depends': ['base', 'mail', 'web'],
    'external_dependencies': {
        'python': ['docx'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/formation_certification_views.xml',
        'views/menu_views.xml',
    ],
    'qweb': [
        'static/src/xml/certification_dashboard.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'harmonie_certification/static/src/js/certification_dashboard.js',
            'harmonie_certification/static/src/scss/certification_style.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}