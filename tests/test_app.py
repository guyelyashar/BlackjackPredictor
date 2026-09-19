from pathlib import Path
import sys

import pytest


APP_DIRECTORY = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIRECTORY))

import app as app_module
from predictor import Predictor


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def test_table_statistics_submission_preserves_valid_values_without_running_prediction(
    client, monkeypatch
) -> None:
    def run_predictor(
        num_of_decks: int,
        num_players: int,
        user_hand: list[str],
        dealer_card: str,
        discarded_cards: list[str] | None = None,
    ) -> float:
        pytest.fail("The prediction should wait for round statistics.")
        return 50.0

    monkeypatch.setattr(app_module.predictor, "run_predictor", run_predictor)

    response = client.post("/", data={"num_of_decks": "6", "num_players": "2"})

    assert response.status_code == 200
    assert b'value="6"' in response.data
    assert b'value="2"' in response.data


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"num_of_decks": "0", "num_players": "2"}, b"Number of decks must be a whole number greater than 0."),
        ({"num_of_decks": "2", "num_players": "0"}, b"Number of players before you must be a whole number greater than 0."),
        ({"num_of_decks": "two", "num_players": "2"}, b"Number of decks must be a whole number greater than 0."),
    ],
)
def test_table_statistics_submission_rejects_non_positive_or_invalid_values(
    client, data: dict[str, str], message: bytes
) -> None:
    response = client.post("/", data=data)

    assert response.status_code == 400
    assert message in response.data


def test_round_statistics_submission_passes_selected_cards_to_predictor(
    client, monkeypatch
) -> None:
    predictor_call: dict[str, object] = {}

    def run_predictor(
        num_of_decks: int,
        num_players: int,
        user_hand: list[str],
        dealer_card: str,
        discarded_cards: list[str] | None = None,
    ) -> float:
        predictor_call["num_of_decks"] = num_of_decks
        predictor_call["num_players"] = num_players
        predictor_call["user_hand"] = user_hand
        predictor_call["dealer_card"] = dealer_card
        return 50.0

    monkeypatch.setattr(app_module.predictor, "run_predictor", run_predictor)

    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "6",
            "num_players": "2",
            "player_cards": ["Ace", "Ten"],
            "dealer_card": "Nine",
        },
    )

    assert response.status_code == 200
    assert predictor_call == {
        "num_of_decks": 6,
        "num_players": 2,
        "user_hand": ["Ace", "Ten"],
        "dealer_card": "Nine",
    }
    assert b"Card 1" in response.data
    assert b"Card 2" in response.data
    assert b'value="Ace"' in response.data
    assert b'value="Nine"' in response.data
    assert b"Winning percentage: 50.0%" in response.data


def test_round_statistics_submission_rejects_invalid_card_names(client) -> None:
    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Two", "Joker"],
            "dealer_card": "Ace",
        },
    )

    assert response.status_code == 400
    assert b"Card 2 must be a valid card." in response.data


@pytest.mark.parametrize(
    ("submitted_card", "message"),
    [
        ("player-card-1", b"Card 1 cannot be empty."),
        ("dealer-card", b"Dealer upcard cannot be empty."),
    ],
)
def test_round_statistics_submission_rejects_an_empty_selected_card(
    client, submitted_card: str, message: bytes
) -> None:
    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "2",
            "num_players": "1",
            "player_cards": ["", ""],
            "dealer_card": "",
            "submitted_card": submitted_card,
        },
    )

    assert response.status_code == 400
    assert message in response.data


def test_prediction_waits_for_two_player_cards_and_a_dealer_upcard(
    client, monkeypatch
) -> None:
    monkeypatch.setattr(
        app_module.predictor,
        "run_predictor",
        lambda *_: pytest.fail("The prediction requires a complete initial round."),
    )

    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Two", ""],
            "dealer_card": "",
            "submitted_card": "player-card-1",
        },
    )

    assert response.status_code == 200
    assert b"Add at least two player cards and a dealer upcard to calculate your winning percentage." in response.data


def test_prediction_log_keeps_previous_results_above_new_results(
    client, monkeypatch
) -> None:
    predictions = iter([42.0, 57.0])
    monkeypatch.setattr(app_module.predictor, "run_predictor", lambda *_: next(predictions))

    first_response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Ace", "Ten"],
            "dealer_card": "Nine",
            "submitted_card": "dealer-card",
        },
    )
    second_response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Eight", "Seven"],
            "dealer_card": "Six",
            "submitted_card": "dealer-card",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert b"Winning percentage: 42.0%" in second_response.data
    assert b"Winning percentage: 57.0%" in second_response.data
    assert second_response.data.index(b"Winning percentage: 42.0%") < second_response.data.index(
        b"Winning percentage: 57.0%"
    )


def test_new_round_discards_current_cards_and_resets_round_statistics(
    client, monkeypatch
) -> None:
    monkeypatch.setattr(
        app_module.predictor,
        "run_predictor",
        lambda *_: pytest.fail("Starting a new round does not calculate a prediction."),
    )

    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Ace", "Ten"],
            "dealer_card": "Nine",
            "action": "new_round",
        },
    )

    assert response.status_code == 200
    assert response.data.count(b'name="player_cards"') == 2
    assert response.data.count(b'value=""') >= 3
    with client.session_transaction() as flask_session:
        assert flask_session["discarded_cards"] == ["Ace", "Ten", "Nine"]


def test_new_round_adds_a_divider_after_existing_predictions(client, monkeypatch) -> None:
    monkeypatch.setattr(
        app_module.predictor,
        "run_predictor",
        lambda *_: pytest.fail("Starting a new round does not calculate a prediction."),
    )
    with client.session_transaction() as flask_session:
        flask_session["prediction_log"] = [
            {
                "user_hand": "Ace, Ten",
                "dealer_card": "Nine",
                "winning_percent": 50.0,
            }
        ]

    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "2",
            "num_players": "1",
            "player_cards": ["Ace", "Ten"],
            "dealer_card": "Nine",
            "action": "new_round",
        },
    )

    assert response.status_code == 200
    assert b"New round" in response.data
    assert response.data.index(b"Winning percentage: 50.0%") < response.data.index(
        b"New round"
    )


def test_prediction_log_badge_excludes_round_breaks(client) -> None:
    with client.session_transaction() as flask_session:
        flask_session["prediction_log"] = [
            {"winning_percent": 50.0},
            {"type": "round_break"},
            {"winning_percent": 60.0},
        ]

    response = client.get("/")

    assert response.status_code == 200
    assert b'<span class="badge badge-outline">2</span>' in response.data


def test_predictor_removes_known_cards_from_a_fresh_shoe(monkeypatch) -> None:
    predictor = Predictor()
    captured_cards: list[str] = []

    def play_games(user_hand: list[str], dealer_card: str, deck) -> float:
        captured_cards.extend(deck.card_list)
        return 50.0

    monkeypatch.setattr(predictor, "play_games", play_games)

    predictor.run_predictor(1, 0, ["Ace", "Ten"], "Nine", ["Two"])

    assert captured_cards.count("Ace") == 3
    assert captured_cards.count("Nine") == 3
    assert captured_cards.count("Two") == 3
    assert captured_cards.count("Ten") == 3


def test_next_round_passes_discarded_cards_to_predictor(client, monkeypatch) -> None:
    discarded_cards_received: list[str] = []

    monkeypatch.setattr(app_module.predictor, "run_predictor", lambda *_: 50.0)
    client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Ace", "Ten"],
            "dealer_card": "Nine",
            "action": "new_round",
        },
    )

    def run_predictor(
        num_of_decks: int,
        num_players: int,
        user_hand: list[str],
        dealer_card: str,
        discarded_cards: list[str],
    ) -> float:
        discarded_cards_received.extend(discarded_cards)
        return 50.0

    monkeypatch.setattr(app_module.predictor, "run_predictor", run_predictor)
    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Eight", "Seven"],
            "dealer_card": "Six",
            "submitted_card": "dealer-card",
        },
    )

    assert response.status_code == 200
    assert discarded_cards_received == ["Ace", "Ten", "Nine"]


def test_reset_clears_session_data_and_returns_to_initial_page(client) -> None:
    with client.session_transaction() as flask_session:
        flask_session["discarded_cards"] = ["Ace", "Ten", "Nine"]
        flask_session["prediction_log"] = [{"winning_percent": 50.0}]

    response = client.post("/", data={"action": "reset"})

    assert response.status_code == 302
    with client.session_transaction() as flask_session:
        assert "discarded_cards" not in flask_session
        assert "prediction_log" not in flask_session

    initial_page = client.get(response.headers["Location"])
    assert initial_page.status_code == 200
    assert initial_page.data.count(b'name="player_cards"') == 2
    assert b'value="1"' in initial_page.data
    assert b"Winning percentage: 50.0%" not in initial_page.data


def test_page_includes_a_theme_toggle_next_to_reset(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert b'data-theme-toggle' in response.data
    assert b'type="button"' in response.data
    assert b'role="switch"' in response.data
    assert b'data-theme-knob' in response.data
    assert b'cursor-pointer' in response.data
    assert b'border border-base-content/30' in response.data
    assert b'bg-primary' not in response.data
    assert b'data-theme-icon="light"' in response.data
    assert b'data-theme-icon="dark"' in response.data
    assert b'data-theme-label' not in response.data
    assert b">Light</span>" not in response.data
    assert b">Dark</span>" not in response.data
    assert response.data.index(b'data-theme-toggle') < response.data.index(b">Reset</button>")


def test_round_statistics_form_starts_with_two_searchable_card_inputs(
    client, monkeypatch
) -> None:
    monkeypatch.setattr(app_module.predictor, "run_predictor", lambda *_: 50.0)

    response = client.get("/")

    assert response.status_code == 200
    assert response.data.count(b'name="player_cards"') == 2
    assert b'id="add-card-button"' in response.data
    assert b'list="card-options"' in response.data
    assert b'<option value="Two"></option>' in response.data
    assert b'<option value="Ace"></option>' in response.data


def test_table_statistics_fields_lock_after_update(client, monkeypatch) -> None:
    monkeypatch.setattr(app_module.predictor, "run_predictor", lambda *_: 50.0)

    response = client.post("/", data={"num_of_decks": "6", "num_players": "2"})

    assert response.status_code == 200
    assert response.data.count(b'aria-readonly="true"') == 2
    assert b"Update table settings</button>" in response.data


def test_submitted_player_card_locks_while_other_card_remains_editable(
    client, monkeypatch
) -> None:
    monkeypatch.setattr(app_module.predictor, "run_predictor", lambda *_: 50.0)

    response = client.post(
        "/",
        data={
            "form_name": "round_statistics",
            "num_of_decks": "1",
            "num_players": "1",
            "player_cards": ["Two", "Three"],
            "dealer_card": "Ace",
            "submitted_card": "player-card-1",
        },
    )

    assert response.status_code == 200
    assert b'id="player-card-1"' in response.data
    assert b'aria-readonly="true"' in response.data
    assert b'name="locked_player_cards" value="1"' in response.data
