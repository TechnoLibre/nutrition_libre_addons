

        odoo.define('bmi_calculateur_snippet.bmi_calculator_widget', function (require) {
            "use strict";
        
            var core = require('web.core');
            var publicWidget = require('web.public.widget');
            var _t = core._t;
        
            var CalculateurIMC = publicWidget.Widget.extend({
                selector: '.s_bmi_snippet',
                template: 'CalculateurIMCTemplate',
                events: {
                    'click .calculer-btn': 'calculerIMCPercentile',
                    'click .recalculer-btn': 'recalculer'
                },
                                       
                start: function () {
                    console.log("Widget started");
                    this.$el.html(core.qweb.render('CalculateurIMCTemplate', {}));
                    return this._super.apply(this, arguments);
                },
        
                calculerIMCPercentile: function () {
                    var age = parseFloat(this.$('#age').val());
                    var taille = parseFloat(this.$('#taille').val());
                    var poids = parseFloat(this.$('#poids').val());
                    var tailleUnit = this.$('#tailleUnit').val();
                    var poidsUnit = this.$('#poidsUnit').val();
                    var gender = this.$('input[name="gender"]:checked').val();
                    var ageGroup = this.$('input[name="ageGroup"]:checked').val();
        
                    // Vérification des plages d'âge
                    if (ageGroup === "Bebe" && (age < 0 || age > 24)) {
                        this.displayNotification({
                            type: 'warning',
                            title: _t("Attention"),
                            message: _t("L'âge pour les bébés doit être compris entre 0 et 24 mois.")
                        });
                        return;
                    } else if (ageGroup === "Enfant" && (age < 24 || age > 96)) {
                        this.displayNotification({
                            type: 'warning',
                            title: _t("Attention"),
                            message: _t("L'âge pour les enfants doit être compris entre 24 et 96 mois.")
                        });
                        return;
                    }
        
                    // Conversion des unités si nécessaire
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
                    // ... (insérez ici la logique de détermination du percentile et du message)
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
                    this.$('#resultats').html(`
                        <p>IMC: ${IMC.toFixed(2)}</p>
                        <p>${message}</p>
                    `);
        
                    // Mise à jour de l'interface utilisateur
                    this.$('#calculatorBox').hide();
                    this.$('#recalculerBtn').show();
                    this.$('#canvasContainer').show();
        
                    // Mise à jour du graphique
                    this.updateGraph(age, IMC, gender, ageGroup);
                },
        
                updateGraph: function (age, IMC, gender, ageGroup) {
                    // Logique pour mettre à jour le graphique
                    // ... (insérez ici la logique de mise à jour du graphique)
                     // Mettre à jour la source de l'image
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
        var ageEnAnnee = age / 12; // Convertir l'âge en années si nécessaire
        var ageMin = 0; // L'âge minimum représenté sur le graphique (par exemple, 0 ans)
        var ageMax = 18; // L'âge maximum représenté sur le graphique (par exemple, 20 ans)
        var IMCMin = 11; // L'IMC minimum représenté sur le graphique
        var IMCMax = 34; // L'IMC maximum représenté sur le graphique

        var x = ((ageEnAnnee - ageMin) / (ageMax - ageMin) * canvas.width) + 20;
        var y = (canvas.height - ((IMC - IMCMin) / (IMCMax - IMCMin) * canvas.height))-18;

        console.log(`Age en années: ${ageEnAnnee}`);
        console.log(`IMC: ${IMC}`);
        console.log(`Coordonnée X: ${x}`);
        console.log(`Coordonnée Y: ${y}`);

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
                    this.$('#calculatorBox').show();
                    this.$('#recalculerBtn').hide();
                    this.$('#canvasContainer').hide();
                    this.$('#resultats').empty();
                    this.$('#age, #taille, #poids').val('');
                    this.$('#tailleUnit').val('cm');
                    this.$('#poidsUnit').val('kg');
                }
            });
        
            publicWidget.registry.bmi_calculator_widget = CalculateurIMC;
        
            return CalculateurIMC;
        });
        