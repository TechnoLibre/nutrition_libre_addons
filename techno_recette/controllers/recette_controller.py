from odoo import http
from odoo.http import request

class RecetteController(http.Controller):
    @http.route('/get_recettes', type='json', auth='public')
    def get_recettes(self):
        recettes = request.env['recette.alimentaire'].search([], order='name asc')
        return [{'id': recette.id, 'name': recette.name} for recette in recettes]

    @http.route('/get_recette_details', type='json', auth='public')
    def get_recette_details(self, id):
        recette = request.env['recette.alimentaire'].browse(id)
        return {
            'name': recette.name,
            'description': recette.description,
            'ingredients': [{'name': ing.name, 'quantite': ing.quantite, 'unite_mesure': ing.unite_mesure} for ing in recette.ingredients_ids]
        }

    @http.route('/ajouter_recette', type='json', auth='public')
    def ajouter_recette(self, **kwargs):
        recette = request.env['recette.alimentaire'].create({
            'name': kwargs.get('name'),
            'description': kwargs.get('description')
        })
        for ingredient in kwargs.get('ingredients', []):
            request.env['recette.ingredient'].create({
                'name': ingredient.get('name'),
                'quantite': ingredient.get('quantite'),
                'unite_mesure': ingredient.get('unite_mesure'),
                'recette_id': recette.id
            })
        return True
