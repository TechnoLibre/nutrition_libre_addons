from odoo import http
from odoo.http import request

class RecipeController(http.Controller):

    @http.route('/get_recipes', type='json', auth='public', methods=['POST'])
    def get_recipes(self):
        recipes = request.env['my_module.recipe'].sudo().search([], order='name')
        recipe_list = [{'id': recipe.id, 'name': recipe.name} for recipe in recipes]
        return recipe_list

    @http.route('/get_recipe_details', type='json', auth='public', methods=['POST'])
    def get_recipe_details(self, recipe_id):
        recipe = request.env['my_module.recipe'].sudo().browse(recipe_id)
        ingredients = [{'name': ing.name, 'quantity': ing.quantity, 'unit': ing.unit} for ing in recipe.ingredient_ids]
        steps = [{'name': step.name, 'description': step.description, 'type': step.type} for step in recipe.step_ids]
        return {'name': recipe.name, 'ingredients': ingredients, 'steps': steps}

    @http.route('/add_recipe', type='json', auth='public', methods=['POST'])
    def add_recipe(self, **kwargs):
        name = kwargs.get('name')
        ingredient_data = kwargs.get('ingredients', [])
        step_data = kwargs.get('steps', [])

        # Créer la recette
        recipe = request.env['my_module.recipe'].sudo().create({'name': name})

        # Ajouter les ingrédients
        for ingredient in ingredient_data:
            request.env['my_module.ingredient'].sudo().create({
                'name': ingredient['name'],
                'quantity': ingredient['quantity'],
                'unit': ingredient['unit'],
                'recipe_id': recipe.id,
            })

        # Ajouter les étapes
        for step in step_data:
            step_record = request.env['my_module.step'].sudo().create({
                'name': step['name'],
                'description': step.get('description', ''),
                'type': step['type'],
                'recipe_id': recipe.id,
            })
            # Relier les ingrédients à l'étape
            step_record.ingredient_ids = [(6, 0, [ing['id'] for ing in step.get('ingredients', [])])]

        return {'status': 'success', 'message': 'Recette ajoutée avec succès'}