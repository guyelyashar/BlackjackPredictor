import os
import secrets
from collections import Counter

from flask import Flask, redirect, render_template, request, session, url_for
from predictor import Predictor

app: Flask = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
predictor: Predictor = Predictor()
PREDICTION_LOG_LIMIT: int = 20
CARD_NAMES: tuple[str, ...] = (
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Jack",
    "Queen",
    "King",
    "Ace",
)


def parse_positive_integer(value: str | None, field_label: str, min_value: int) -> tuple[int, str | None]:
    if value is None or not value.isdigit() or int(value) < min_value:
        return 1, f"{field_label} must be a whole number of at least {min_value}."

    return int(value), None


def parse_card(value: str | None, field_label: str) -> tuple[str, str | None]:
    card_name = value or ""

    if not card_name:
        return "", None
    if card_name not in CARD_NAMES:
        return card_name, f"{field_label} must be a valid card."

    return card_name, None


def cards_fit_in_shoe(cards: list[str], num_of_decks: int) -> bool:
    return all(count <= 4 * num_of_decks for count in Counter(cards).values())


def round_is_complete(
    player_card_values: list[str], locked_player_card_indices: set[int], dealer_card: str, dealer_card_locked: bool
) -> bool:
    return (
        bool(player_card_values)
        and all(card.strip() for card in player_card_values)
        and all(index in locked_player_card_indices for index in range(1, len(player_card_values) + 1))
        and bool(dealer_card.strip())
        and dealer_card_locked
    )


def store_round_state(
    num_of_decks: int,
    num_players: int,
    player_card_values: list[str],
    dealer_card: str,
    table_locked: bool,
    locked_player_card_indices: set[int],
    dealer_card_locked: bool,
) -> None:
    session["round_state"] = {
        "num_of_decks": num_of_decks,
        "num_players": num_players,
        "player_card_values": player_card_values,
        "dealer_card": dealer_card,
        "table_locked": table_locked,
        "locked_player_card_indices": sorted(locked_player_card_indices),
        "dealer_card_locked": dealer_card_locked,
    }


@app.route("/", methods=["GET", "POST"])
def home():
    num_of_decks: int = 1
    num_players: int = 0
    user_hand: list[str] = []
    dealer_card: str = ""
    player_card_values: list[str] = ["", ""]
    table_locked: bool = False
    locked_player_card_indices: set[int] = set()
    dealer_card_locked: bool = False
    round_complete: bool = False
    can_edit_players: bool = session.get("can_edit_players", False)
    errors: dict[str, str] = {}
    prediction_log: list[dict[str, str | float]] = session.get("prediction_log", [])
    discarded_cards: list[str] = session.get("discarded_cards", [])

    if request.method == "GET":
        round_state = session.get("round_state", {})
        num_of_decks = round_state.get("num_of_decks", num_of_decks)
        num_players = round_state.get("num_players", num_players)
        player_card_values = round_state.get("player_card_values", player_card_values)
        dealer_card = round_state.get("dealer_card", dealer_card)
        table_locked = round_state.get("table_locked", table_locked)
        locked_player_card_indices = set(round_state.get("locked_player_card_indices", []))
        dealer_card_locked = round_state.get("dealer_card_locked", dealer_card_locked)
        round_complete = round_is_complete(
            player_card_values, locked_player_card_indices, dealer_card, dealer_card_locked
        )

    if request.method == "POST":
        if request.form.get("action") == "reset":
            session.clear()
            return redirect(url_for("home"))

        is_round_statistics_submission = request.form.get("form_name") == "round_statistics"
        parsed_num_of_decks, decks_error = parse_positive_integer(
            request.form.get("num_of_decks"), "Number of decks", 1
        )
        parsed_num_players, players_error = parse_positive_integer(
            request.form.get("num_players"), "Number of players before you", 0
        )

        if decks_error:
            errors["num_of_decks"] = decks_error
        else:
            num_of_decks = parsed_num_of_decks

        if players_error:
            errors["num_players"] = players_error
        else:
            num_players = parsed_num_players

        if is_round_statistics_submission:
            table_locked = request.form.get("table_locked") == "true"
            locked_player_card_indices = {
                int(value)
                for value in request.form.getlist("locked_player_cards")
                if value.isdigit() and int(value) > 0
            }
            dealer_card_locked = request.form.get("dealer_card_locked") == "true"
            submitted_player_cards = request.form.getlist("player_cards")
            player_card_values = submitted_player_cards or ["", ""]

            for index, submitted_card in enumerate(player_card_values, start=1):
                card_name, card_error = parse_card(submitted_card, f"Card {index}")
                if card_error:
                    errors[f"player_card_{index}"] = card_error
                elif card_name:
                    user_hand.append(card_name)

            dealer_card, dealer_card_error = parse_card(
                request.form.get("dealer_card"), "Dealer upcard"
            )
            if dealer_card_error:
                errors["dealer_card"] = dealer_card_error

            submitted_card = request.form.get("submitted_card", "")
            if submitted_card.startswith("player-card-"):
                card_index = submitted_card.removeprefix("player-card-")
                if card_index.isdigit():
                    player_card_index = int(card_index) - 1
                    if (
                        0 <= player_card_index < len(player_card_values)
                        and not player_card_values[player_card_index].strip()
                    ):
                        errors[f"player_card_{player_card_index + 1}"] = (
                            f"Card {player_card_index + 1} cannot be empty."
                        )
            elif submitted_card == "dealer-card" and not dealer_card.strip():
                errors["dealer_card"] = "Dealer upcard cannot be empty."

            known_cards = discarded_cards + user_hand + ([dealer_card] if dealer_card else [])
            if not errors and not cards_fit_in_shoe(known_cards, num_of_decks):
                errors["round_statistics"] = "The submitted cards exceed the cards available in this shoe."

            if request.form.get("action") == "new_round":
                if not round_is_complete(
                    player_card_values, locked_player_card_indices, dealer_card, dealer_card_locked
                ):
                    errors["round_statistics"] = (
                        "Submit every player card and the dealer upcard before starting a new round."
                    )

            round_complete = round_is_complete(
                player_card_values, locked_player_card_indices, dealer_card, dealer_card_locked
            )

        if errors:
            return (
                render_template(
                    "index.html",
                    num_of_decks=request.form.get("num_of_decks", ""),
                    num_players=request.form.get("num_players", ""),
                    player_card_values=player_card_values,
                    dealer_card=request.form.get("dealer_card", ""),
                    card_options=CARD_NAMES,
                    table_locked=table_locked,
                    locked_player_card_indices=locked_player_card_indices,
                    dealer_card_locked=dealer_card_locked,
                    round_complete=round_complete,
                    can_edit_players=can_edit_players,
                    winning_percent=None,
                    prediction_log=prediction_log,
                    errors=errors,
                ),
                400,
            )

        if is_round_statistics_submission and request.form.get("action") == "new_round":
            discarded_cards.extend(user_hand)
            if dealer_card:
                discarded_cards.append(dealer_card)
            session["discarded_cards"] = discarded_cards
            if prediction_log:
                prediction_log.append({"type": "round_break"})
                prediction_log = prediction_log[-PREDICTION_LOG_LIMIT:]
                session["prediction_log"] = prediction_log
            user_hand = []
            dealer_card = ""
            player_card_values = ["", ""]
            locked_player_card_indices = set()
            dealer_card_locked = False
            round_complete = False
            can_edit_players = True
            session["can_edit_players"] = can_edit_players
        elif is_round_statistics_submission:
            submitted_card = request.form.get("submitted_card", "")
            if submitted_card.startswith("player-card-"):
                card_index = submitted_card.removeprefix("player-card-")
                if card_index.isdigit() and int(card_index) > 0:
                    locked_player_card_indices.add(int(card_index))
            elif submitted_card == "dealer-card":
                dealer_card_locked = True
            round_complete = round_is_complete(
                player_card_values, locked_player_card_indices, dealer_card, dealer_card_locked
            )
        else:
            table_locked = True

    winning_percent: float | None = None
    if request.method == "POST" and round_complete:
        winning_percent = predictor.run_predictor(
            num_of_decks, num_players, user_hand, dealer_card, discarded_cards
        )
        prediction_log.append(
            {
                "type": "prediction",
                "user_hand": ", ".join(user_hand),
                "dealer_card": dealer_card,
                "winning_percent": round(winning_percent, 1),
            }
        )
        prediction_log = prediction_log[-PREDICTION_LOG_LIMIT:]
        session["prediction_log"] = prediction_log
        can_edit_players = False
        session["can_edit_players"] = can_edit_players

    if request.method == "POST":
        store_round_state(
            num_of_decks,
            num_players,
            player_card_values,
            dealer_card,
            table_locked,
            locked_player_card_indices,
            dealer_card_locked,
        )
        return redirect(url_for("home"))

    return render_template(
        "index.html",
        num_of_decks=num_of_decks,
        num_players=num_players,
        user_hand=user_hand,
        dealer_card=dealer_card,
        player_card_values=player_card_values,
        card_options=CARD_NAMES,
        table_locked=table_locked,
        locked_player_card_indices=locked_player_card_indices,
        dealer_card_locked=dealer_card_locked,
        round_complete=round_complete,
        can_edit_players=can_edit_players,
        winning_percent=winning_percent,
        prediction_log=prediction_log,
        errors=errors,
    )

if __name__ == "__main__":
    app.run()
