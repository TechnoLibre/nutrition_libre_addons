{
    'name': 'BMI Calculateur Snippet',
    "version": "16.0.1.0.1",
    'summary': 'Calculateur de IMC et Percentile',
    'description': """Ce bout de code ajoute une fonctionnalité à votre site web : un calculateur d'IMC et de percentiles pour enfants.""",
    'category': 'Website',
    'author': 'Adil Goumih',
    'website': 'http://www.votre-website.com',
    'depends': ['website'],  # Assure-toi que le module 'website' est installé
    'data': [
       'static/src/xml/bmi_calculator_template.xml',
       'views/snippets/bmi_calculator_snippet.xml',
    ],
    'assets': {
        'web.assets_frontend': [
             'bmi_calculateur_snippet/static/src/js/bmi_calculator_widget.js',
             'bmi_calculateur_snippet/static/src/css/snippet_style.css',

        ],
    },
    'installable': True,  # Ce champ doit être True
    'license': 'AGPL-3',
}
