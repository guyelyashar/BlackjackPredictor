document.addEventListener("DOMContentLoaded", () => {
    const addCardButton = document.getElementById("add-card-button");
    const playerCardInputs = document.getElementById("player-card-inputs");

    if (!(addCardButton instanceof HTMLButtonElement) || !(playerCardInputs instanceof HTMLDivElement)) {
        return;
    }

    let cardCount = Number(playerCardInputs.dataset.cardCount);

    addCardButton.addEventListener("click", () => {
        cardCount += 1;

        const cardControl = document.createElement("div");
        cardControl.className = "form-control";
        cardControl.dataset.playerCard = "";

        const label = document.createElement("label");
        label.className = "label";
        label.htmlFor = `player-card-${cardCount}`;

        const labelText = document.createElement("span");
        labelText.className = "label-text";
        labelText.textContent = `Card ${cardCount}`;
        label.append(labelText);

        const inputRow = document.createElement("div");
        inputRow.className = "flex gap-2";

        const cardInput = document.createElement("input");
        cardInput.className = "input input-bordered min-w-0 flex-1";
        cardInput.id = `player-card-${cardCount}`;
        cardInput.name = "player_cards";
        cardInput.type = "text";
        cardInput.setAttribute("list", "card-options");
        cardInput.placeholder = "Search cards";
        cardInput.autocomplete = "off";

        const submitButton = document.createElement("button");
        submitButton.className = "btn btn-secondary";
        submitButton.type = "submit";
        submitButton.name = "submitted_card";
        submitButton.value = `player-card-${cardCount}`;
        submitButton.textContent = "Submit";

        inputRow.append(cardInput, submitButton);
        cardControl.append(label, inputRow);
        playerCardInputs.append(cardControl);
        cardInput.focus();
    });
});
