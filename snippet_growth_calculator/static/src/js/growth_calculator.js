odoo.define('snippet_growth_calculator.GrowthCalculatorWidget', function (require) {
    "use strict";
    // Importer les modules nécessaires d'Odoo
    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var _t = core._t;

    // Définition du widget de calculateur de croissance
    var GrowthCalculatorWidget = publicWidget.Widget.extend({
        selector: '.growth-calculator', // Sélecteur du widget dans le DOM
        template: 'snippet_growth_calculator.snippet_growth_calculator',
        events: {
            'click .calculateButton': 'calculateIMCPercentile',
            'click .resetButton': 'resetFields',
        },
        // Propriétés pour les mappings
        ageMapping: [],
        weightMapping: [],
        // Méthode d'initialisation
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.initializeMappings(); // Initialiser les mappings lors de l'initialisation
        },

           // Méthode d'initialisation
        start: function () {
           return this._super.apply(this, arguments);
       },

        // Initialiser les mappings pour l'âge et le poids
        initializeMappings: function() {
            for (let i = 0; i <= 60; i += 0.5) {
                this.ageMapping.push(i);
            }
            for (let i = 2; i <= 30; i += 0.5) {
                this.weightMapping.push(i);
            }
            console.log("Mappings initialized:", this.ageMapping, this.weightMapping);
        },
        // Méthode pour calculer l'IMC et le percentile
        calculateIMCPercentile: function () {
            console.log("calculateIMCPercentile called");
            var age = parseFloat(this.$('#floatingAge').val());
            var weight = parseFloat(this.$('#floatingWeight').val());
            var height = parseFloat(this.$('#floatingHeight').val());
            var sexeValue = this.$('#floatingSex').val(); // Récupération de la valeur du sexe
            var sexe = sexeValue === 'true' ? 'garcon' : (sexeValue === 'false' ? 'fille' : null);
            console.log("Values - Age:", age, "Weight:", weight, "Height:", height, "Sexe:", sexe); 
            var ageGroup = this.$('input[name="ageGroup"]:checked').val();
            var error = this.validateFields(age, weight, height, sexe, ageGroup);
            if (error) return;
            var imc = (weight / Math.pow(height / 100, 2)).toFixed(2);
            var [percentile, message] = this.getPercentileAndMessage(imc, age, sexe, ageGroup);
            this.$('#resultats').html(`
                <p>IMC: ${imc}</p>
                <p>Percentile: ${percentile}</p>
                <p>${message}</p>
            `);
            this.showImage(sexe === 'garcon' ? 'garcon' : 'fille', age, weight);
        },
        // Méthode pour valider les champs
        validateFields: function(age, weight, height, sexe, ageGroup) {
            var error = false;
            var ageErrorElem = this.$('.ageError');
            var weightErrorElem = this.$('.weightError');
            var heightErrorElem = this.$('.heightError');
            var sexErrorElem = this.$('.sexError');
            // Validation des champs
            if (isNaN(age) || age < 0 || age > 60) {
                ageErrorElem.text(_t("L'âge doit être compris entre 0 et 60 mois."));
                error = true;
            } else if (ageGroup === "Bebe" && age > 24) {
                ageErrorElem.text(_t("Pour le groupe 'Bébé', l'âge doit être entre 0 et 24 mois."));
                error = true;
            } else if (ageGroup === "Enfant" && age < 25) {
                ageErrorElem.text(_t("Pour le groupe 'Enfant', l'âge doit être entre 25 et 60 mois."));
                error = true;
            } else {
                ageErrorElem.text("");
            }
            if (isNaN(weight) || weight < 2 || weight > 30) {
                weightErrorElem.text(_t("Le poids doit être compris entre 2 et 30 kg."));
                error = true;
            } else {
                weightErrorElem.text("");
            }
            if (isNaN(height) || height < 49 || height > 125) {
                heightErrorElem.text(_t("La taille doit être comprise entre 49 et 125 cm."));
                error = true;
            } else {
                heightErrorElem.text("");
            }

            if (sexe === null) {
                sexErrorElem.text(_t("Veuillez sélectionner le sexe."));
                error = true;
            } else {
                sexErrorElem.text(""); 
            }

            if (error) {
                this.$('.resultats').html("");
            }
            return error;
        },
        // Méthode pour obtenir le percentile et le message
        getPercentileAndMessage: function (imc, age, sexe, ageGroup) {
            const messages = {
                "default": _t("Les valeurs de percentile sont approximatives et il est recommandé de consulter un professionnel de la santé (nutritionniste, médecin, etc.) pour évaluer sa santé.")
            };
            // Seuils pour les groupes d'âge
            const seuils = {
                "Bebe": {
                    "garcon": [
                        { seuil: 14, percentile: "Sous le 5e percentile" },
                        { seuil: 15.5, percentile: "5e à 10e percentile" },
                        { seuil: 18, percentile: "10e à 85e percentile" },
                        { seuil: 20, percentile: "85e à 95e percentile" },
                        { seuil: Infinity, percentile: "Au-dessus du 95e percentile" }
                    ],
                    "fille": [
                        { seuil: 13.5, percentile: "Sous le 5e percentile" },
                        { seuil: 15, percentile: "5e à 10e percentile" },
                        { seuil: 17.5, percentile: "10e à 85e percentile" },
                        { seuil: 19, percentile: "85e à 95e percentile" },
                        { seuil: Infinity, percentile: "Au-dessus du 95e percentile" }
                    ]
                },
                "Enfant": {
                    "garcon": [
                        { seuil: 14, percentile: "Sous le 5e percentile" },
                        { seuil: 15.5, percentile: "5e à 10e percentile" },
                        { seuil: 18.5, percentile: "10e à 85e percentile" },
                        { seuil: 20.5, percentile: "85e à 95e percentile" },
                        { seuil: Infinity, percentile: "Au-dessus du 95e percentile" }
                    ],
                    "fille": [
                        { seuil: 13.5, percentile: "Sous le 5e percentile" },
                        { seuil: 15, percentile: "5e à 10e percentile" },
                        { seuil: 18.5, percentile: "10e à 85e percentile" },
                        { seuil: 20.5, percentile: "85e à 95e percentile" },
                        { seuil: Infinity, percentile: "Au-dessus du 95e percentile" }
                    ]
                }
            };
            // Vérifier si les seuils existent pour le groupe d'âge et le sexe
            if (!seuils[ageGroup] || !seuils[ageGroup][sexe]) {
                return ["Inconnu", messages.default];
            }
            const seuilsPourAgeGroupe = seuils[ageGroup][sexe];
            // Vérifier les seuils pour déterminer le percentile
            for (let seuil of seuilsPourAgeGroupe) {
                if (imc < seuil.seuil) {
                    const message = _t(`Votre ${ageGroup === "Bebe" ? "bébé" : "enfant"} a un IMC de ${imc} à ${age} mois. ${messages.default}`);
                    return [seuil.percentile, message];
                }
            }
            // Si l'IMC est supérieur à tous les seuils
            return [seuilsPourAgeGroupe[seuilsPourAgeGroupe.length - 1].percentile, messages.default];
        },
        // Méthode pour afficher l'image
        showImage: function (sexe, age, weight) {
            const canvasIMC = this.$('#canvasIMC')[0];
            const canvasPoids = this.$('#canvasPoids')[0];
            const pointRouge = this.$('#pointRouge')[0];

            // Cacher tous les canvases avant d'afficher les nouvelles images
            canvasIMC.style.display = 'none';
            canvasPoids.style.display = 'none';

            let imgIMC, imgPoids;
            // Déterminer quelle image afficher
            if (sexe === 'garcon') {
                imgIMC = '/snippet_growth_calculator/static/src/images/IMC-boys.jpg';
                imgPoids = '/snippet_growth_calculator/static/src/images/courbe_garcon_percentils.jpg';
            } else {
                imgIMC = '/snippet_growth_calculator/static/src/images/IMC-girls.jpg';
                imgPoids = '/snippet_growth_calculator/static/src/images/courbe_fille_percentils.jpg';
            }

            // Afficher l'image IMC
            const ctxIMC = canvasIMC.getContext('2d');
            const imgIMCObj = new Image();
            imgIMCObj.src = imgIMC;
            imgIMCObj.onload = () => {
                canvasIMC.width = imgIMCObj.width;
                canvasIMC.height = imgIMCObj.height;
                ctxIMC.drawImage(imgIMCObj, 0, 0);
                // Obtenir les coordonnées dynamiques
                const [xIMC, yIMC] = this.getCoordinates(age, weight, canvasIMC);
                // Positionner le point rouge sur l'image IMC
                pointRouge.style.left = `${xIMC}px`;
                pointRouge.style.top = `${yIMC}px`;
                pointRouge.style.display = 'block';
                ctxIMC.fillStyle = 'red';
                ctxIMC.beginPath();
                ctxIMC.arc(xIMC, yIMC, 30, 0, Math.PI * 2);
                ctxIMC.fill();
                canvasIMC.style.display = 'block'; // Afficher le canvas IMC
            };

            // Afficher l'image Poids
            const ctxPoids = canvasPoids.getContext('2d');
            const imgPoidsObj = new Image();
            imgPoidsObj.src = imgPoids;
            imgPoidsObj.onload = () => {
                canvasPoids.width = imgPoidsObj.width;
                canvasPoids.height = imgPoidsObj.height;
                ctxPoids.drawImage(imgPoidsObj, 0, 0);
                // Obtenir les coordonnées dynamiques
                const [xPoids, yPoids] = this.getCoordinates(age, weight, canvasPoids);
                // Positionner le point rouge sur l'image Poids
                pointRouge.style.left = `${xPoids}px`;
                pointRouge.style.top = `${yPoids}px`;
                ctxPoids.fillStyle = 'red';
                ctxPoids.beginPath();
                ctxPoids.arc(xPoids, yPoids, 30, 0, Math.PI * 2);
                ctxPoids.fill();
                canvasPoids.style.display = 'block'; // Afficher le canvas Poids
            };
        },
        // Méthode pour réinitialiser les champs
        resetFields: function () {
            this.$('#floatingAge, #floatingWeight, #floatingHeight, #floatingSex').val('');
            this.$('.ageError, .weightError, .heightError, .sexError').text('');
            this.$('#resultats').html('');
            this.$('#canvasIMC, #canvasPoids, #pointRouge').hide();
        },
        // Méthode pour obtenir les coordonnées selon l'âge et le poids
        getCoordinates: function(age, weight, canvas) {
            const ageIndex = this.ageMapping.indexOf(age);
            const weightIndex = this.weightMapping.indexOf(weight);
            if (ageIndex === -1 || weightIndex === -1) {
                console.error("Âge ou poids non valide.");
                return [0, 0]; // Valeurs par défaut si non trouvé
            }
            const marginX = 230; // Marge en pixels pour l'axe X
            const marginY = 230; // Marge en pixels pour l'axe Y
            const effectiveWidth = canvas.width - 2 * marginX; // Largeur effective
            const effectiveHeight = canvas.height - 2 * marginY; // Hauteur effective
            const x = marginX + (ageIndex * effectiveWidth / (this.ageMapping.length - 1)); // Échelle pour l'axe X
            const y = canvas.height - marginY - ((weightIndex + 0.1) * effectiveHeight / (this.weightMapping.length - 1)); // Échelle pour l'axe Y
            return [x, y];
        }
    });

    // Enregistrer le widget dans le registre d'actions
    publicWidget.registry.GrowthCalculatorWidget = GrowthCalculatorWidget;
    return GrowthCalculatorWidget;
});

