from odoo import http
from odoo.http import request
import json

class AlimentController(http.Controller):

    @http.route('/aliments/get_list', type='json', auth='public')
    def get_aliments(self):
        aliments = request.env['aliment.aliment'].sudo().search_read([], ['name'])
        return json.dumps(aliments)

    @http.route('/aliments/add', type='json', auth='public')
    def add_aliment(self, name):
        new_aliment = request.env['aliment.aliment'].sudo().create({'name': name})
        return json.dumps({'success': True, 'id': new_aliment.id, 'name': new_aliment.name})
