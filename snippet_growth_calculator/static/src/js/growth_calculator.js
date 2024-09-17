const ageMapping = [];
for (let i = 0; i <= 60; i += 0.5) {
    ageMapping.push(i);
}
const weightMapping = [];
for (let i = 2; i <= 30; i += 0.5) {
    weightMapping.push(i);
}

function getCoordinates(age, weight, canvas) {
const ageIndex = ageMapping.indexOf(age);
const weightIndex = weightMapping.indexOf(weight);

if (ageIndex === -1 || weightIndex === -1) {
    console.error("Âge ou poids non valide.");
    return [0, 0]; // Valeurs par défaut si non trouvé
}

const marginX = 230; // Marge en pixels entre le début de l'image et le début de la courbe pour l'axe X
const marginY = 230; // Marge en pixels entre le haut/bas de l'image et le début de la courbe pour l'axe Y
const effectiveWidth = canvas.width - 2 * marginX; // Largeur effective du canvas après la marge
const effectiveHeight = canvas.height - 2 * marginY; // Hauteur effective du canvas après la marge

const x = marginX + (ageIndex * effectiveWidth / (ageMapping.length - 1)); // Échelle pour l'axe X avec marge proportionnelle
const y = canvas.height - marginY - ((weightIndex + 0.1) * effectiveHeight / (weightMapping.length - 1));
console.log(`Coordonnées pour l'âge ${age} et le poids ${weight} : (${x}, ${y})`);
return [x, y];
}

function afficherImage(sexe, age, weight) {
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
}

function calculerIMCPercentile() {
    var age = parseFloat(document.getElementById('floatingAge').value);
    var weight = parseFloat(document.getElementById('floatingWeight').value);
    var height = parseFloat(document.getElementById('floatingHeight').value);
    var sexe = document.getElementById('floatingSex').value === 'true' ? 'garcon' : 'fille'; 
    var ageGroup = document.querySelector('input[name="ageGroup"]:checked').value;

    // Validation des champs
    var error = false;
    var messagesErreur = {
        age: "L'âge doit être compris entre 0 et 60 mois.",
        ageGroupBebe: "Pour le groupe 'Bébé', l'âge doit être entre 0 et 24 mois.",
        ageGroupEnfant: "Pour le groupe 'Enfant', l'âge doit être entre 25 et 60 mois.",
        weight: "Le poids doit être compris entre 2 et 30 kg.",
        height: "La taille doit être comprise entre 49 et 125 cm.",
        sexe: "Veuillez sélectionner le sexe."
    };
    if (isNaN(age) || age < 0 || age > 60) {
        document.getElementById('ageError').textContent = messagesErreur.age;
        error = true;
    } else {
        if (ageGroup === "Bebe" && age > 24) {
            document.getElementById('ageError').textContent = messagesErreur.ageGroupBebe;
            error = true;
        } else if (ageGroup === "Enfant" && age < 25) {
            document.getElementById('ageError').textContent = messagesErreur.ageGroupEnfant;
            error = true;
        } else {
            document.getElementById('ageError').textContent = "";
        }
    }
    if (isNaN(weight) || weight < 2 || weight > 30) {
        document.getElementById('weightError').textContent = messagesErreur.weight;
        error = true;
    } else {
        document.getElementById('weightError').textContent = "";
    }
    if (isNaN(height) || height < 49 || height > 125) {
        document.getElementById('heightError').textContent = messagesErreur.height;
        error = true;
    } else {
        document.getElementById('heightError').textContent = "";
    }
    if (document.getElementById('floatingSex').value === "") {
        document.getElementById('sexError').textContent = messagesErreur.sexe;
        error = true;
    } else {
        document.getElementById('sexError').textContent = "";
    }
    if (error) {
        document.getElementById('resultats').innerHTML = "";
        return;
    }
    var imc = (weight / Math.pow(height / 100, 2)).toFixed(2); // Calcul de l'IMC
    var percentile, message;

            function getPercentileAndMessage(imc, age, sexe, ageGroup) {
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
                    "default": "Les valeurs de percentile sont approximatives et il est recommandé de consulter un professionnel de la santé (nutritionniste, médecin, etc.) pour évaluer sa santé."
                };

                // Vérifier si ageGroup et sexe existent dans les seuils
                if (!seuils[ageGroup] || !seuils[ageGroup][sexe]) {
                    return ["Inconnu", messages.default];
                }

                const seuilsPourAgeGroupe = seuils[ageGroup][sexe];
                for (let seuil of seuilsPourAgeGroupe) {
                    if (imc < seuil.seuil) {
                        percentile = seuil.percentile;
                        message = `Votre ${ageGroup === "Bebe" ? "bébé" : "enfant"} a un IMC de ${imc} à ${age} mois, ${messages.default}`;
                        return [percentile, message];
                    }
                }

                // Si aucun seuil n'a été trouvé
                return ["Inconnu", messages.default];
            }

            // Appeler la fonction pour obtenir le percentile et le message
            [percentile, message] = getPercentileAndMessage(imc, age, sexe, ageGroup);

            // Afficher les résultats
            document.getElementById('resultats').innerHTML = `
                <p>IMC: ${imc}</p>
                <p>Percentile: ${percentile}</p>
                <p>${message}</p>
            `;
    afficherImage(sexe === 'garcon' ? 'garcon' : 'fille', age, weight);
}

function reinitialiserChamps() {
    document.getElementById('floatingAge').value = '';
    document.getElementById('floatingWeight').value = '';
    document.getElementById('floatingHeight').value = '';
    document.getElementById('floatingSex').value = '';
    document.getElementById('ageError').textContent = '';
    document.getElementById('weightError').textContent = '';
    document.getElementById('heightError').textContent = '';
    document.getElementById('sexError').textContent = '';
    document.getElementById('resultats').innerHTML = '';
    document.getElementById('canvasIMC').style.display = 'none';
    document.getElementById('canvasPoids').style.display = 'none';
    document.getElementById('pointRouge').style.display = 'none';
}
