odoo.define('snippet_growth_calculator.snippet_growth_calculator', function (require) {
    "use strict";

    // Importer les modules nécessaires d'Odoo
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;

    // Définir les traductions
    var translations = {
        fr: {
            age: "L'âge doit être compris entre 0 et 60 mois.",
            ageGroupBebe: "Pour le groupe 'Bébé', l'âge doit être entre 0 et 24 mois.",
            ageGroupEnfant: "Pour le groupe 'Enfant', l'âge doit être entre 25 et 60 mois.",
            weight: "Le poids doit être compris entre 2 et 30 kg.",
            height: "La taille doit être comprise entre 49 et 125 cm.",
            sexe: "Veuillez sélectionner le sexe.",
            imcMessage: "Les valeurs de percentile sont approximatives et il est recommandé de consulter un professionnel de la santé (nutritionniste, médecin, etc.) pour évaluer sa santé."
        },
        en: {
            age: "Age must be between 0 and 60 months.",
            ageGroupBebe: "For 'Baby' group, age must be between 0 and 24 months.",
            ageGroupEnfant: "For 'Child' group, age must be between 25 and 60 months.",
            weight: "Weight must be between 2 and 30 kg.",
            height: "Height must be between 49 and 125 cm.",
            sexe: "Please select gender.",
            imcMessage: "The percentile values are approximate and it is recommended to consult a health professional (nutritionist, doctor, etc.) to assess health."
        }
    };

    // Fonction pour obtenir le message traduit selon la langue active
    function t(key) {
        var language = 'fr'; 
        return translations[language][key];
    }

    // Classe principale du calculateur de croissance
    var GrowthCalculator = AbstractAction.extend({
        template: 'snippet_growth_calculator', // Template à définir dans les vues Odoo

        // Propriétés de classe
        ageMapping: [],
        weightMapping: [],

        // Méthode d'initialisation
        init: function (parent, options) {
            this._super(parent, options);
            this.initializeMappings();
        },

        // Initialiser les mappings pour l'âge et le poids
        initializeMappings: function() {
            for (let i = 0; i <= 60; i += 0.5) {
                this.ageMapping.push(i);
            }
            for (let i = 2; i <= 30; i += 0.5) {
                this.weightMapping.push(i);
            }
        },

        // Fonction pour obtenir les coordonnées selon l'âge et le poids
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
            console.log(`Coordonnées pour l'âge ${age} et le poids ${weight} : (${x}, ${y})`);
            return [x, y];
        },
        
        // Méthode pour calculer l'IMC et le percentile
        calculerIMCPercentile: function () {
            var age = parseFloat(this.$('.floatingAge').val());
            var weight = parseFloat(this.$('.floatingWeight').val());
            var height = parseFloat(this.$('.floatingHeight').val());
            var sexe = this.$('.floatingSex').val() === 'true' ? 'garcon' : 'fille'; 
            var ageGroup = this.$('input[name="ageGroup"]:checked').val();

            // Validation des champs
            var error = false;

            // Messages d'erreur traduits
            var messagesErreur = {
                age: t('age'),
                ageGroupBebe: t('ageGroupBebe'),
                ageGroupEnfant: t('ageGroupEnfant'),
                weight: t('weight'),
                height: t('height'),
                sexe: t('sexe')
            };
            
            var ageErrorElem = this.$('.ageError');
            var weightErrorElem = this.$('.weightError');
            var heightErrorElem = this.$('.heightError');
            var sexErrorElem = this.$('.sexError');

            // Validation des champs d'âge, poids, taille et sexe avec affichage des messages traduits
            if (isNaN(age) || age < 0 || age > 60) {
                ageErrorElem.text(messagesErreur.age);
                error = true;
            } else {
                if (ageGroup === "Bebe" && age > 24) {
                    ageErrorElem.text(messagesErreur.ageGroupBebe);
                    error = true;
                } else if (ageGroup === "Enfant" && age < 25) {
                    ageErrorElem.text(messagesErreur.ageGroupEnfant);
                    error = true;
                } else {
                    ageErrorElem.text("");
                }
            }

            if (isNaN(weight) || weight < 2 || weight > 30) {
                weightErrorElem.text(messagesErreur.weight);
                error = true;
            } else {
                weightErrorElem.text("");
            }

            if (isNaN(height) || height < 49 || height > 125) {
                heightErrorElem.text(messagesErreur.height);
                error = true;
            } else {
                heightErrorElem.text("");
            }

            if (this.$('.floatingSex').val() === "") {
                sexErrorElem.text(messagesErreur.sexe);
                error = true;
            } else {
                sexErrorElem.text("");
            }

            if (error) {
                this.$('.resultats').html("");
                return;
            }

            // Calcul de l'IMC
            var imc = (weight / Math.pow(height / 100, 2)).toFixed(2);
            var [percentile, message] = this.getPercentileAndMessage(imc, age, sexe, ageGroup);

            // Afficher les résultats
            this.$('#resultats').html(`
                <p>IMC: ${imc}</p>
                <p>Percentile: ${percentile}</p>
                <p>${message}</p>
            `);

            this.afficherImage(sexe === 'garcon' ? 'garcon' : 'fille', age, weight);
        },

        // Fonction pour obtenir le percentile et le message
        getPercentileAndMessage: function (imc, age, sexe, ageGroup) {
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

            const messages = {
                "default": t('imcMessage')
            };

            if (!seuils[ageGroup] || !seuils[ageGroup][sexe]) {
                return ["Inconnu", messages.default];
            }

            const seuilsPourAgeGroupe = seuils[ageGroup][sexe];
            for (let seuil of seuilsPourAgeGroupe) {
                if (imc < seuil.seuil) {
                    const message = `Votre ${ageGroup === "Bebe" ? "bébé" : "enfant"} a un IMC de ${imc} à ${age} mois, ${messages.default}`;
                    return [seuil.percentile, message];
                }
            }

            return ["Inconnu", messages.default];
        },

        // Fonction pour réinitialiser les champs
        reinitialiserChamps: function () {
            this.$('#floatingAge').val('');
            this.$('#floatingWeight').val('');
            this.$('#floatingHeight').val('');
            this.$('#floatingSex').val('');
            this.$('.ageError').text('');
            this.$('.weightError').text('');
            this.$('.heightError').text('');
            this.$('.sexError').text('');
            this.$('#resultats').html('');
            this.$('#canvasIMC').hide();
            this.$('#canvasPoids').hide();
            this.$('#pointRouge').hide();
        },

        // Méthode pour afficher l'image
        afficherImage: function (sexe, age, weight) {
            const canvasIMC = document.getElementById('canvasIMC');
        const canvasPoids = document.getElementById('canvasPoids');
    const pointRouge = document.getElementById('pointRouge');

    // Cacher tous les canvases
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

    imgIMCObj.onload = function() {
        canvasIMC.width = imgIMCObj.width;
        canvasIMC.height = imgIMCObj.height;
        ctxIMC.drawImage(imgIMCObj, 0, 0);

        // Obtenir les coordonnées dynamiques
        const [xIMC, yIMC] = getCoordinates(age, weight, canvasIMC);

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

    imgPoidsObj.onload = function() {
        canvasPoids.width = imgPoidsObj.width;
        canvasPoids.height = imgPoidsObj.height;
        ctxPoids.drawImage(imgPoidsObj, 0, 0);

        // Obtenir les coordonnées dynamiques
        const [xPoids, yPoids] = getCoordinates(age, weight, canvasPoids);

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
    });

    // Enregistrer le module dans Odoo
    core.action_registry.add('growth_calculator', GrowthCalculator);
});
