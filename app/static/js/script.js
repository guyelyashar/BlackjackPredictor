document.addEventListener("DOMContentLoaded", () => {
    const newVisitReset = document.querySelector("[data-reset-session-on-new-visit]");
    const sessionResetForm = document.querySelector("[data-session-reset-form]");
    const visitStorageKey = "blackjackPredictorVisitState";

    const navigationType = performance.getEntriesByType("navigation")[0]?.type;
    const isFreshVisit = navigationType === "navigate";

    const resetSessionForFreshVisit = async () => {
        if (!(newVisitReset instanceof HTMLElement)) {
            return;
        }

        try {
            const visitState = window.sessionStorage.getItem(visitStorageKey);
            if (visitState === "reset" || visitState === "form_submission") {
                window.sessionStorage.setItem(visitStorageKey, "active");
                return;
            }

            if (!isFreshVisit) {
                return;
            }

            const response = await window.fetch(window.location.href, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: "action=reset",
                credentials: "same-origin",
            });

            if (response.ok && response.redirected) {
                window.sessionStorage.setItem(visitStorageKey, "reset");
                window.location.replace(response.url);
            }
        } catch {
            // Storage or network restrictions leave the current session intact.
        }
    };

    void resetSessionForFreshVisit();

    if (sessionResetForm instanceof HTMLFormElement) {
        sessionResetForm.addEventListener("submit", () => {
            try {
                window.sessionStorage.setItem(visitStorageKey, "reset");
            } catch {
                // The server-side reset still works when browser storage is unavailable.
            }
        });
    }

    document.querySelectorAll("form").forEach((form) => {
        if (form !== sessionResetForm) {
            form.addEventListener("submit", () => {
                try {
                    window.sessionStorage.setItem(visitStorageKey, "form_submission");
                } catch {
                    // The form can still submit when browser storage is unavailable.
                }
            });
        }
    });

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
    const newRoundButton = document.querySelector("[data-new-round]");
    const editPlayersButton = document.querySelector("[data-edit-players]");
    const playersInput = document.getElementById("num-players");
    const cardOptionsElement = document.getElementById("card-options");

    let cardOptions = [];
    if (cardOptionsElement instanceof HTMLScriptElement) {
        try {
            const parsedOptions = JSON.parse(cardOptionsElement.textContent || "[]");
            if (Array.isArray(parsedOptions) && parsedOptions.every((option) => typeof option === "string")) {
                cardOptions = parsedOptions;
            }
        } catch {
            // The card fields remain usable as text inputs if options cannot be read.
        }
    }

    if (!(addCardButton instanceof HTMLButtonElement) || !(playerCardInputs instanceof HTMLDivElement)) {
        return;
    }

    const updateNewRoundState = () => {
        if (!(newRoundButton instanceof HTMLButtonElement)) {
            return;
        }

        const cardInputs = playerCardInputs.querySelectorAll('input[name="player_cards"]');
        const dealerCardInput = document.getElementById("dealer-card");
        const areAllCardsSubmitted = Array.from(cardInputs).every((cardInput) => (
            cardInput instanceof HTMLInputElement && cardInput.readOnly
        ));

        newRoundButton.disabled = !(
            areAllCardsSubmitted
            && dealerCardInput instanceof HTMLInputElement
            && dealerCardInput.readOnly
        );
    };

    const configureCardDropdown = (cardInput) => {
        if (!(cardInput instanceof HTMLInputElement) || cardInput.readOnly) {
            return;
        }

        const combobox = cardInput.closest("[data-card-combobox]");
        const menu = combobox?.querySelector("[data-card-menu]");
        if (!(menu instanceof HTMLDivElement)) {
            return;
        }

        let activeIndex = -1;
        let filteredOptions = [];

        const closeMenu = () => {
            menu.classList.add("hidden");
            cardInput.setAttribute("aria-expanded", "false");
            cardInput.removeAttribute("aria-activedescendant");
            activeIndex = -1;
        };

        const chooseCard = (card) => {
            cardInput.value = card;
            cardInput.dispatchEvent(new Event("input", { bubbles: true }));
            closeMenu();
            cardInput.focus();
        };

        const renderMenu = () => {
            const searchTerm = cardInput.value.trim().toLowerCase();
            filteredOptions = cardOptions.filter((card) => card.toLowerCase().includes(searchTerm));
            menu.replaceChildren();

            if (!filteredOptions.length) {
                closeMenu();
                return;
            }

            filteredOptions.forEach((card, index) => {
                const option = document.createElement("button");
                option.className = "btn btn-ghost btn-sm w-full justify-start";
                option.type = "button";
                option.id = `${cardInput.id}-option-${index}`;
                option.role = "option";
                option.ariaSelected = String(index === activeIndex);
                option.textContent = card;
                option.addEventListener("mousedown", (event) => event.preventDefault());
                option.addEventListener("click", () => chooseCard(card));
                menu.append(option);
            });

            menu.classList.remove("hidden");
            cardInput.setAttribute("aria-expanded", "true");
            if (activeIndex >= 0) {
                cardInput.setAttribute("aria-activedescendant", `${cardInput.id}-option-${activeIndex}`);
            }
        };

        const moveActiveOption = (offset) => {
            if (!filteredOptions.length) {
                renderMenu();
            }
            if (!filteredOptions.length) {
                return;
            }

            activeIndex = (activeIndex + offset + filteredOptions.length) % filteredOptions.length;
            renderMenu();
        };

        cardInput.addEventListener("focus", renderMenu);
        cardInput.addEventListener("input", () => {
            activeIndex = -1;
            renderMenu();
        });
        cardInput.addEventListener("keydown", (event) => {
            if (event.key === "ArrowDown") {
                event.preventDefault();
                moveActiveOption(1);
            } else if (event.key === "ArrowUp") {
                event.preventDefault();
                moveActiveOption(-1);
            } else if (event.key === "Enter" && activeIndex >= 0) {
                event.preventDefault();
                chooseCard(filteredOptions[activeIndex]);
            } else if (event.key === "Escape") {
                closeMenu();
            }
        });
        cardInput.addEventListener("blur", () => window.setTimeout(closeMenu, 100));
    };

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
        configureCardDropdown(cardInput);
        updateSubmitState();
        updateNewRoundState();
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

        const combobox = document.createElement("div");
        combobox.className = "relative min-w-0 flex-1";
        combobox.dataset.cardCombobox = "";

        const cardInput = document.createElement("input");
        cardInput.className = "input input-bordered w-full";
        cardInput.id = `player-card-${cardCount}`;
        cardInput.name = "player_cards";
        cardInput.type = "text";
        cardInput.placeholder = "Search cards";
        cardInput.autocomplete = "off";
        cardInput.setAttribute("role", "combobox");
        cardInput.setAttribute("aria-autocomplete", "list");
        cardInput.setAttribute("aria-controls", `player-card-options-${cardCount}`);
        cardInput.setAttribute("aria-expanded", "false");
        cardInput.dataset.cardInput = "";

        const menu = document.createElement("div");
        menu.className = "absolute z-10 mt-1 hidden max-h-52 w-full overflow-y-auto rounded-box border border-base-300 bg-base-100 p-1 shadow-lg";
        menu.id = `player-card-options-${cardCount}`;
        menu.role = "listbox";
        menu.dataset.cardMenu = "";

        const submitButton = document.createElement("button");
        submitButton.className = "btn btn-primary btn-sm self-center";
        submitButton.type = "submit";
        submitButton.name = "submitted_card";
        submitButton.value = `player-card-${cardCount}`;
        submitButton.dataset.cardSubmit = "";
        submitButton.textContent = "Submit";

        combobox.append(cardInput, menu);
        inputRow.append(combobox, submitButton);
        cardControl.append(label, inputRow);
        playerCardInputs.append(cardControl);
        configureCardSubmit(cardInput, submitButton);
        updateNewRoundState();
        cardInput.focus();
    });

    if (editPlayersButton instanceof HTMLButtonElement && playersInput instanceof HTMLInputElement) {
        editPlayersButton.addEventListener("click", () => {
            playersInput.readOnly = false;
            playersInput.removeAttribute("aria-readonly");
            editPlayersButton.closest("form")?.querySelector('button[type="submit"]')?.removeAttribute("disabled");
            playersInput.focus();
        });
    }
});
