$(document).ready(function () {
    // Fonction pour charger les recettes
    function loadRecipes() {
        $.ajax({
            url: '/get_recipes',
            method: 'POST',
            contentType: 'application/json',
            success: function (data) {
                $('#recipe-list').empty();
                data.forEach(function (recipe) {
                    $('#recipe-list').append(
                        `<li class="list-group-item" data-id="${recipe.id}">${recipe.name}</li>`
                    );
                });
            },
            error: function () {
                alert('Erreur lors du chargement des recettes.');
            }
        });
    }

    // Afficher les détails d'une recette
    $(document).on('click', '#recipe-list li', function () {
        const recipeId = $(this).data('id');
        $.ajax({
            url: '/get_recipe_details',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ recipe_id: recipeId }),
            success: function (recipe) {
                $('#recipe-name').text(recipe.name);
                $('#ingredient-list').empty();
                recipe.ingredients.forEach(function (ingredient) {
                    $('#ingredient-list').append(
                        `<li class="list-group-item">${ingredient.quantity} ${ingredient.unit} - ${ingredient.name}</li>`
                    );
                });
                $('#step-list').empty();
                recipe.steps.forEach(function (step) {
                    $('#step-list').append(
                        `<li class="list-group-item">${step.name}: ${step.description}</li>`
                    );
                });
                $('#recipe-details-container').show();
                $('#recipe-list-container').hide();
            },
            error: function () {
                alert('Erreur lors du chargement des détails de la recette.');
            }
        });
    });

    // Retour à la liste des recettes
    $('#back-to-list').click(function () {
        $('#recipe-details-container').hide();
        $('#recipe-list-container').show();
    });

    // Ajout d'un ingrédient
    $('#add-ingredient').click(function () {
        $('#ingredient-container').append(`
            <div class="ingredient-entry mb-2">
                <input type="text" placeholder="Nom de l'ingrédient" required>
                <input type="number" placeholder="Quantité" required>
                <input type="text" placeholder="Unité" required>
                <button type="button" class="btn btn-danger remove-ingredient">Supprimer</button>
            </div>
        `);
    });

    // Suppression d'un ingrédient
    $(document).on('click', '.remove-ingredient', function () {
        $(this).closest('.ingredient-entry').remove();
    });

    // Ajout d'une étape
    $('#add-step').click(function () {
        $('#step-container').append(`
            <div class="step-entry mb-2">
                <input type="text" placeholder="Nom de l'étape" required>
                <textarea placeholder="Description"></textarea>
                <select required>
                    <option value="preparation">Préparation</option>
                    <option value="mélange">Mélange</option>
                    <option value="cuisson">Cuisson</option>
                </select>
                <button type="button" class="btn btn-danger remove-step">Supprimer</button>
            </div>
        `);
    });

    // Suppression d'une étape
    $(document).on('click', '.remove-step', function () {
        $(this).closest('.step-entry').remove();
    });

    // Soumettre une nouvelle recette
    $('#new-recipe-form').submit(function (event) {
        event.preventDefault();
        const ingredients = [];
        $('#ingredient-container .ingredient-entry').each(function () {
            const name = $(this).find('input').eq(0).val();
            const quantity = $(this).find('input').eq(1).val();
            const unit = $(this).find('input').eq(2).val();
            ingredients.push({ name, quantity, unit });
        });

        const steps = [];
        $('#step-container .step-entry').each(function () {
            const name = $(this).find('input').val();
            const description = $(this).find('textarea').val();
            const type = $(this).find('select').val();
            steps.push({ name, description, type });
        });

        const recipeData = {
            name: $('#recipe-name-input').val(),
            ingredients: ingredients,
            steps: steps
        };

        $.ajax({
            url: '/add_recipe',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(recipeData),
            success: function () {
                alert('Recette ajoutée avec succès !');
                loadRecipes(); // Recharge la liste des recettes
                $('#add-recipe-form').hide(); // Masque le formulaire
                $('#recipe-list-container').show(); // Affiche la liste
            },
            error: function () {
                alert('Erreur lors de l\'ajout de la recette.');
            }
        });
    });

    // Charger les recettes lors du chargement de la page
    loadRecipes();
});