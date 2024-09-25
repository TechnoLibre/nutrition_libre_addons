{
    'name': 'IMC Percentile Snippet',
    'description': 'Snippet pour calculer l\'IMC et le percentile des enfants',
    'author': 'Sandrine Signe',
    'website': 'https://votre-site.com',
    'category': 'Website',
    'version': '1.0',
    'depends': ['website'],
    'data': [
        'views/snippet_templates.xml',  # Le fichier XML contenant le template du snippet
        'views/res_config_settings_views.xml',  # Ajoutez le fichier XML pour les paramètres de configuration ici
    ],
    'assets': {
    'web.assets_frontend': [
        'website_snippet_imc/static/src/snippets/imc_snippet/snippet.css',  # Chemin correct du fichier CSS
        'website_snippet_imc/static/src/snippets/imc_snippet/snippet.js',   # Chemin correct du fichier JS
    ],
},
    'application': False,
}

