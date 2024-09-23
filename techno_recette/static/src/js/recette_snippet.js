odoo.define('recette.snippet', function(require) {
    'use strict';

    var ajax = require('web.ajax');

    $(document).ready(function() {
        function chargerRecettes() {
            ajax.jsonRpc('/get_recettes', 'POST', {})
            .then(function(recettes) {
                var recetteList = $('#recette_list');
                recetteList.empty();
                recettes.forEach(function(recette) {
                    recetteList.append('<li><a href="#" class="recette-item" data-id="' + recette.id + '">' + recette.name + '</a></li>');
                });
            });
        }

        // Afficher les détails de la recette
        $('body').on('click', '.recette-item', function(e) {
            e.preventDefault();
            var recetteId = $(this).data('id');
            ajax.jsonRpc('/get_recette_details', 'POST', {id: recetteId})
            .then(function(recette) {
                $('#recette_details').html('<h3>' + recette.name + '</h3><p>' + recette.description + '</p>');
            });
        });

        chargerRecettes();
    });
});
