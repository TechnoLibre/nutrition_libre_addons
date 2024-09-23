from odoo import models, fields

class Recette(models.Model):
    _name = 'recette.alimentaire'
    _description = 'Recette Alimentaire'

    name = fields.Char(string='Nom de la Recette', required=True)
    description = fields.Text(string='Description')
    ingredients_ids = fields.One2many('recette.ingredient', 'recette_id', string='Ingrédients')
    etapes_ids = fields.One2many('recette.etape', 'recette_id', string='Étapes')

class Ingredient(models.Model):
    _name = 'recette.ingredient'
    _description = 'Ingrédient'

    name = fields.Char(string='Nom de l\'ingrédient', required=True)
    quantite = fields.Float(string='Quantité', required=True)
    unite_mesure = fields.Char(string='Unité de mesure', required=True)
    recette_id = fields.Many2one('recette.alimentaire', string='Recette', ondelete='cascade')

class Etape(models.Model):
    _name = 'recette.etape'
    _description = 'Étape de préparation'

    name = fields.Char(string='Nom de l\'étape', required=True)
    description = fields.Text(string='Description')
    type_etape = fields.Selection([('preparation', 'Préparation'), ('mélange', 'Mélange'), ('cuisson', 'Cuisson')],
                                  string='Type d\'étape', required=True)
    ingredients_ids = fields.Many2many('recette.ingredient', string='Ingrédients associés')
    recette_id = fields.Many2one('recette.alimentaire', string='Recette', ondelete='cascade')
