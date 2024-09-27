

odoo.define('imc_calculateur_snippet.imc_calculator', function (require) {
    "use strict";
   

     var core = require('web.core');
     var publicWidget = require('web.public.widget');
     var _t = core._t;

    var CalculateurIMC = publicWidget.Widget.extend({
        selector: '.s_imc_snippet',
        template: 's_imc_calculator',
        events: {
            'click .calculer-btn': 'calculerIMCPercentile',
            'click .recalculer-btn': 'recalculer',
            'change input[name="ageGroup"]': 'ajusterPlageAge'
        },
        ajusterPlageAge: function(event) {
            var ageGroup = $(event.target).val();
            var ageInput = this.$('#age');
            if (ageGroup === "Bebe") {
                ageInput.attr('min', 0);
                ageInput.attr('max', 24);
            } else {
                ageInput.attr('min', 24);
                ageInput.attr('max', 96);
            }
            // Ajuster la valeur si elle est hors de la nouvelle plage
            var currentAge = parseFloat(ageInput.val());
            if (currentAge < parseFloat(ageInput.attr('min'))) {
                ageInput.val(ageInput.attr('min'));
            } else if (currentAge > parseFloat(ageInput.attr('max'))) {
                ageInput.val(ageInput.attr('max'));
            }
        },                  
        start: function () {
            console.log("IMC Calculator Widget initialized");
            return this._super.apply(this, arguments);
        },

        calculerIMCPercentile: function () {
            // Réinitialiser tous les messages d'erreur
            this.$('.text-danger').text('');
            var age = parseFloat(this.$('#age').val());
            var taille = parseFloat(this.$('#taille').val());
            var poids = parseFloat(this.$('#poids').val());
            var tailleUnit = this.$('#tailleUnit').val();
            var poidsUnit = this.$('#poidsUnit').val();
            var gender = this.$('input[name="gender"]:checked').val();
            var ageGroup = this.$('input[name="ageGroup"]:checked').val();
            var isValid = true;

            // Vérification des plages taille poids et âge
            if (!age || age < 0) {
                this.$('#ageError').text("L'âge doit être rempli.");
                isValid = false;
            }
            if (!taille || taille <= 0) {
                this.$('#tailleError').text("La taille doit être remplie.");
                isValid = false;
            }
            if (!poids || poids <= 0) {
                this.$('#poidsError').text("Le poids doit être rempli.");
                isValid = false;
            }       
            if (!isValid) {
                return;
            }

            // Conversion des unités 
            if (tailleUnit === "pouces") {
                taille = taille * 2.54; // Conversion pouces en cm
            }
            if (poidsUnit === "livres") {
                poids = poids * 0.453592; // Conversion livres en kg
            }

            // Calcul de l'IMC
            var grandeur = taille / 100;
            var IMC = poids / (grandeur * grandeur);

            // Logique pour déterminer le percentile et le message
            var percentile, message;

     // Ajustements selon l'âge et le sexe
     if (ageGroup === "Bebe") {
        if (gender === "Garcon") {
            if (IMC < 14) {
                percentile = "Sous le 5e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme insuffisance pondérale. Consultez un pédiatre pour évaluer la santé de votre bébé.`;
            } else if (IMC >= 14 && IMC < 15.5) {
                percentile = "5e à 10e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est proche de l'insuffisance pondérale. Il est conseillé de surveiller son alimentation.`;
            } else if (IMC >= 15.5 && IMC < 18) {
                percentile = "10e à 85e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est normal. Assurez-vous qu'il a une alimentation équilibrée.`;
            } else if (IMC >= 18 && IMC < 20) {
                percentile = "85e à 95e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui peut indiquer un surpoids. Consultez un pédiatre pour évaluer son alimentation.`;
            } else {
                percentile = "Au-dessus du 95e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme obésité. Il est recommandé de consulter un pédiatre.`;
            }
        } else {
            if (IMC < 13.5) {
                percentile = "Sous le 5e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme insuffisance pondérale. Consultez un pédiatre pour évaluer la santé de votre bébé.`;
            } else if (IMC >= 13.5 && IMC < 15) {
                percentile = "5e à 10e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est proche de l'insuffisance pondérale. Il est conseillé de surveiller son alimentation.`;
            } else if (IMC >= 15 && IMC < 17.5) {
                percentile = "10e à 85e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est normal. Assurez-vous qu'il a une alimentation équilibrée.`;
            } else if (IMC >= 17.5 && IMC < 19.5) {
                percentile = "85e à 95e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui peut indiquer un surpoids. Consultez un pédiatre pour évaluer son alimentation.`;
            } else {
                percentile = "Au-dessus du 95e percentile";
                message = `Votre bébé a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme obésité. Il est recommandé de consulter un pédiatre.`;
            }
        }
    } else {
        // Traitement pour l'âge "Enfant"
        if (gender === "Garcon") {
            if (IMC < 14) {
                percentile = "Sous le 5e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme insuffisance pondérale. Consultez un pédiatre pour évaluer la santé de votre enfant.`;
            } else if (IMC >= 14 && IMC < 15.5) {
                percentile = "5e à 10e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est proche de l'insuffisance pondérale. Il est conseillé de surveiller son alimentation.`;
            } else if (IMC >= 15.5 && IMC < 18) {
                percentile = "10e à 85e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est normal. Assurez-vous qu'il a une alimentation équilibrée.`;
            } else if (IMC >= 18 && IMC < 20) {
                percentile = "85e à 95e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui peut indiquer un surpoids. Consultez un pédiatre pour évaluer son alimentation.`;
            } else {
                percentile = "Au-dessus du 95e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme obésité. Il est recommandé de consulter un pédiatre.`;
            }
        } else {
            if (IMC < 13.5) {
                percentile = "Sous le 5e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme insuffisance pondérale. Consultez un pédiatre pour évaluer la santé de votre enfant.`;
            } else if (IMC >= 13.5 && IMC < 15) {
                percentile = "5e à 10e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est proche de l'insuffisance pondérale. Il est conseillé de surveiller son alimentation.`;
            } else if (IMC >= 15 && IMC < 17.5) {
                percentile = "10e à 85e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est normal. Assurez-vous qu'il a une alimentation équilibrée.`;
            } else if (IMC >= 17.5 && IMC < 19.5) {
                percentile = "85e à 95e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui peut indiquer un surpoids. Consultez un pédiatre pour évaluer son alimentation.`;
            } else {
                percentile = "Au-dessus du 95e percentile";
                message = `Votre enfant a un IMC de ${IMC.toFixed(2)} à ${age} mois, ce qui est considéré comme obésité. Il est recommandé de consulter un pédiatre.`;
            }
        }
    }

            // Affichage des résultats
            var resultatsHTML = `
            <h3>Résultats</h3>
            <p>IMC: ${IMC.toFixed(2)}</p>
            <p>${message}</p>
        `;
        
        this.$('#resultats').html(resultatsHTML);
        
        // Faire défiler jusqu'aux résultats
        $('html, body').animate({
            scrollTop: this.$('#resultats').offset().top
        }, 1000);

            // Mise à jour du graphique
            this.updateGraph(age, IMC, gender, ageGroup);
        },

        updateGraph: function (age, IMC, gender, ageGroup) {
            this.$('#canvasContainer').show();
            // Logique pour mettre à jour le graphique
             // Mettre à jour la source de l'image
             var imagePath = '';
             if (ageGroup === "Bebe") {
                 if(gender === "Garcon"){
                     imagePath = '/imc_calculateur_snippet/static/src/img/courbe_garcon.png';
                 }else{
                     imagePath = '/imc_calculateur_snippet/static/src/img/courbe_fille.png';
                 }
             } else if (ageGroup === "Enfant") {
                 if(gender === "Garcon"){
                     imagePath = '/imc_calculateur_snippet/static/src/img/courbe_garcon.png';
                 }else{
                     imagePath = '/imc_calculateur_snippet/static/src/img/courbe_fille.png';
                 }
             }
var img = new Image();
img.src = imagePath;

img.onload = function () {
// Mettre à jour les dimensions du canvas
var canvas = document.getElementById('curveCanvas');
canvas.width = img.width;
canvas.height = img.height;

var ctx = canvas.getContext('2d');

// Effacer le canvas avant de dessiner
ctx.clearRect(0, 0, canvas.width, canvas.height);

// Dessiner l'image sur le canvas
ctx.drawImage(img, 0, 0);

// Calcul des coordonnées en fonction de l'âge et de l'IMC
var ageEnAnnee = age / 12; // Convertir l'âge en années 
var ageMin = 0; // L'âge minimum représenté sur le graphique 
var ageMax = 18; // L'âge maximum représenté sur le graphique 
var IMCMin = 11; // L'IMC minimum représenté sur le graphique
var IMCMax = 34; // L'IMC maximum représenté sur le graphique

var x = ((ageEnAnnee - ageMin) / (ageMax - ageMin) * canvas.width) + 20;
var y = (canvas.height - ((IMC - IMCMin) / (IMCMax - IMCMin) * canvas.height))-18;


// Dessiner le point sur le graphique
ctx.beginPath();
ctx.arc(x, y, 5, 0, 2 * Math.PI);
ctx.fillStyle = 'red';
ctx.fill();
ctx.strokeStyle = 'black';
ctx.stroke();

// Ajouter un texte pour indiquer la position
ctx.fillStyle = 'red';
ctx.fillText("Votre position", x + 10, y); // 'x + 10' décale le texte à droite du point
};
        },

        recalculer: function () {
            this.$('#resultats').empty();
            this.$('#canvasContainer').hide();

        }
    });

    publicWidget.registry.imc_calculator_widget = CalculateurIMC;


    return CalculateurIMC;
});
