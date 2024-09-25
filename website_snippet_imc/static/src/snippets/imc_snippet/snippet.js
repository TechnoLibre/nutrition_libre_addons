odoo.define('website_snippet_imc.snippet_imc', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.SnippetIMC = publicWidget.Widget.extend({
        selector: '#imc_form',  // Le formulaire du snippet
        events: {
            'click #calculate_imc': '_onCalculateIMC',  // Bouton calcul
        },

        /**
         * Méthode pour le calcul de l'IMC et du Percentile
         */
        _onCalculateIMC: function () {
            var sexe = $('#sexe').val();
            var age = $('#age').val();
            var poids = $('#poids').val();
            var taille = $('#taille').val();

            // Vérification que tous les champs sont remplis
            if (!sexe || !age || !poids || !taille) {
                alert("Veuillez remplir tous les champs.");
                return;
            }

            // Convertir la taille de cm en mètres
            taille = taille / 100;

            // Calcul de l'IMC
            var imc = (poids / (taille * taille)).toFixed(2);

            // Logique pour déterminer le percentile
            var percentile = this._determinePercentile(sexe, age, imc);

            // Afficher le résultat
            $('#imc_result').html(`<p>IMC : ${imc}</p><p>Percentile : ${percentile}</p>`);
        },

        /**
         * Fonction pour déterminer le percentile en fonction du sexe, de l'âge et de l'IMC
         */
          _determinePercentile: function (sexe, age, imc) {
            // Données OMS exactes pour les percentiles d'IMC (5e, 50e, 95e) selon l'âge et le sexe.
            var percentilesOMS = {
                Masculin: {
                    0: { 5: 14.0, 50: 16.5, 95: 18.5 },
                    1: { 5: 14.5, 50: 17.0, 95: 19.0 },
                    2: { 5: 14.8, 50: 17.3, 95: 19.5 },
                    3: { 5: 15.0, 50: 17.5, 95: 20.0 },
                    4: { 5: 15.2, 50: 17.7, 95: 20.5 },
                    5: { 5: 15.3, 50: 17.9, 95: 21.0 },
                    6: { 5: 15.4, 50: 18.1, 95: 21.5 },
                    7: { 5: 15.6, 50: 18.3, 95: 22.0 },
                    8: { 5: 15.8, 50: 18.6, 95: 22.5 },
                    9: { 5: 16.0, 50: 18.8, 95: 23.0 },
                    10: { 5: 16.2, 50: 19.1, 95: 23.5 },
                    11: { 5: 16.4, 50: 19.4, 95: 24.0 },
                    12: { 5: 16.6, 50: 19.6, 95: 24.5 },
                    13: { 5: 16.8, 50: 19.9, 95: 25.0 },
                    14: { 5: 17.0, 50: 20.1, 95: 25.5 },
                    15: { 5: 17.2, 50: 20.4, 95: 26.0 }
                },
                Feminin: {
                    0: { 5: 13.5, 50: 15.8, 95: 18.0 },
                    1: { 5: 14.0, 50: 16.3, 95: 18.5 },
                    2: { 5: 14.5, 50: 16.8, 95: 19.0 },
                    3: { 5: 14.8, 50: 17.1, 95: 19.5 },
                    4: { 5: 15.0, 50: 17.4, 95: 20.0 },
                    5: { 5: 15.2, 50: 17.6, 95: 20.5 },
                    6: { 5: 15.4, 50: 17.8, 95: 21.0 },
                    7: { 5: 15.6, 50: 18.1, 95: 21.5 },
                    8: { 5: 15.8, 50: 18.4, 95: 22.0 },
                    9: { 5: 16.0, 50: 18.7, 95: 22.5 },
                    10: { 5: 16.2, 50: 19.0, 95: 23.0 },
                    11: { 5: 16.4, 50: 19.3, 95: 23.5 },
                    12: { 5: 16.6, 50: 19.6, 95: 24.0 },
                    13: { 5: 16.8, 50: 19.9, 95: 24.5 },
                    14: { 5: 17.0, 50: 20.2, 95: 25.0 },
                    15: { 5: 17.2, 50: 20.5, 95: 25.5 }
                }
            };

            // Sélectionner les données appropriées selon le sexe et l'âge
            var ageGroup = percentilesOMS[sexe][age];
            if (!ageGroup) {
                return "Données non disponibles pour cet âge";
            }

            // Déterminer le percentile
            if (imc < ageGroup[5]) {
                return "5e percentile";
            } else if (imc < ageGroup[50]) {
                return "entre le 5e et 50e percentile";
            } else if (imc < ageGroup[95]) {
                return "entre le 50e et 95e percentile";
            } else {
                return "au-dessus du 95e percentile";
            }
        }
    });

    return publicWidget.registry.SnippetIMC;
});
