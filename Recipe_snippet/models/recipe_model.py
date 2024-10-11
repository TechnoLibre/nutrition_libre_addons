from odoo import models, fields

class Recipe(models.Model):
    _name = 'my_module.recipe'
    _description = 'Recette Alimentaire'

    name = fields.Char('Nom de la Recette', required=True)
    ingredient_ids = fields.One2many('my_module.ingredient', 'recipe_id', string='Ingrédients')
    step_ids = fields.One2many('my_module.step', 'recipe_id', string='Étapes')

class Ingredient(models.Model):
    _name = 'my_module.ingredient'
    _description = 'Ingrédient de la Recette'

    name = fields.Char('Nom de l\'Ingrédient', required=True)
    quantity = fields.Float('Quantité', required=True)
    unit = fields.Char('Unité de Mesure', required=True)
    recipe_id = fields.Many2one('my_module.recipe', string='Recette')

class Step(models.Model):
    _name = 'my_module.step'
    _description = 'Étape de Préparation'

    name = fields.Char('Nom de l\'Étape', required=True)
    description = fields.Text('Description')
    type = fields.Selection([('preparation', 'Préparation'), ('mélange', 'Mélange'), ('cuisson', 'Cuisson')], required=True)
    ingredient_ids = fields.Many2many('my_module.ingredient', string='Ingrédients Associés')
    recipe_id = fields.Many2one('my_module.recipe', string='Recette')