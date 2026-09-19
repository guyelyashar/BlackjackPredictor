document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.querySelector("[data-theme-toggle]");
    const themeKnob = document.querySelector("[data-theme-knob]");
    const lightThemeIcon = document.querySelector('[data-theme-icon="light"]');
    const darkThemeIcon = document.querySelector('[data-theme-icon="dark"]');

    const applyTheme = (theme) => {
        const isDarkTheme = theme === "dark";
        document.documentElement.dataset.theme = isDarkTheme ? "dark" : "light";

        if (themeToggle instanceof HTMLButtonElement) {
            themeToggle.setAttribute("aria-label", `Switch to ${isDarkTheme ? "light" : "dark"} mode`);
            themeToggle.setAttribute("aria-checked", String(isDarkTheme));
        }

        if (themeKnob instanceof HTMLSpanElement) {
            themeKnob.classList.toggle("translate-x-6", isDarkTheme);
            themeKnob.classList.toggle("translate-x-0", !isDarkTheme);
        }

        if (lightThemeIcon instanceof SVGElement && darkThemeIcon instanceof SVGElement) {
            lightThemeIcon.classList.toggle("rotate-90", isDarkTheme);
            lightThemeIcon.classList.toggle("scale-0", isDarkTheme);
            lightThemeIcon.classList.toggle("opacity-0", isDarkTheme);
            darkThemeIcon.classList.toggle("rotate-90", !isDarkTheme);
            darkThemeIcon.classList.toggle("scale-0", !isDarkTheme);
            darkThemeIcon.classList.toggle("opacity-0", !isDarkTheme);
        }
    };

    if (themeToggle instanceof HTMLButtonElement) {
        try {
            applyTheme(window.localStorage.getItem("blackjackPredictorTheme") || "light");
        } catch {
            applyTheme("light");
        }

        themeToggle.addEventListener("click", () => {
            const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            applyTheme(nextTheme);

            try {
                window.localStorage.setItem("blackjackPredictorTheme", nextTheme);
            } catch {
                // Theme selection still works when browser storage is unavailable.
            }
        });
    }

    const addCardButton = document.getElementById("add-card-button");
    const playerCardInputs = document.getElementById("player-card-inputs");

    if (!(addCardButton instanceof HTMLButtonElement) || !(playerCardInputs instanceof HTMLDivElement)) {
        return;
    }

    const configureCardSubmit = (cardInput, submitButton) => {
        if (!(cardInput instanceof HTMLInputElement) || !(submitButton instanceof HTMLButtonElement)) {
            return;
        }

        const updateSubmitState = () => {
            if (!cardInput.readOnly) {
                submitButton.disabled = cardInput.value.trim() === "";
            }
        };

        cardInput.addEventListener("input", updateSubmitState);
        updateSubmitState();
    };

    document.querySelectorAll("[data-card-submit]").forEach((submitButton) => {
        if (submitButton instanceof HTMLButtonElement) {
            configureCardSubmit(document.getElementById(submitButton.value), submitButton);
        }
    });

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
        labelText.className = "label-text font-medium";
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
        submitButton.className = "btn btn-primary btn-sm self-center";
        submitButton.type = "submit";
        submitButton.name = "submitted_card";
        submitButton.value = `player-card-${cardCount}`;
        submitButton.dataset.cardSubmit = "";
        submitButton.textContent = "Submit";

        inputRow.append(cardInput, submitButton);
        cardControl.append(label, inputRow);
        playerCardInputs.append(cardControl);
        configureCardSubmit(cardInput, submitButton);
        cardInput.focus();
    });
});
