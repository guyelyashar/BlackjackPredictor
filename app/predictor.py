import random
from deck import Deck

class Predictor():

    def run_predictor(
        self,
        num_of_decks: int,
        num_players: int,
        user_hand: list[str],
        dealer_card: str,
        discarded_cards: list[str] | None = None,
    ) -> float:
        simulation_deck: Deck = Deck()

        for _ in range(num_of_decks - 1):
            simulation_deck.combine_decks()

        known_cards: list[str] = (discarded_cards or []).copy()
        known_cards.extend(user_hand)
        if dealer_card:
            known_cards.append(dealer_card)

        for card in known_cards:
            simulation_deck.remove_card(card)

        simulation_deck.shuffle_deck()

        if num_players > 0:
            num_cards_remove: int = 0
            random_num_cards_remover: float = random.random()

            if random_num_cards_remover <= 0.48:
                num_cards_remove = num_players * 2
            elif random_num_cards_remover <= 0.78:
                num_cards_remove = random.randint(num_players * 2 + 1, num_players * 3)
            elif random_num_cards_remover <= 0.92:
                num_cards_remove = random.randint(num_players * 2 + 1, num_players * 4)
            elif random_num_cards_remover <= 0.97:
                num_cards_remove = random.randint(num_players * 3 + 1, num_players * 5)
            else:
                num_cards_remove = random.randint(num_players * 3 + 1, num_players * 6)

            for _ in range(num_cards_remove):
                simulation_deck.pop_card()

        # Set User And Dealer Initial Cards

        #for i in range(1, 3):
        #    user_hand.append(user_input_card := self.card_input_smart("Input Card " + str(i) + ": "))

        winning_percent: float = self.play_games(user_hand, dealer_card, simulation_deck)

        return winning_percent
        
        

    def test_game(self, user_hand: list[str], dealer_first_card: str, deck: Deck) -> float:
        user_hand_value_and_strategy: tuple[int, str] = self.calculate_hand_value_and_strategy(user_hand)
        user_hand_value: int = user_hand_value_and_strategy[0]
        strategy: str = user_hand_value_and_strategy[1]

        dealer_first_card_value: int = self.calculate_hand_value_and_strategy([dealer_first_card])[0]

        move: str = ""

        if "Pair" in strategy:
            if "Pair237" in strategy and (dealer_first_card_value >= 2 and dealer_first_card_value <= 7):
                strategy = "Split"
            elif "Pair4" in strategy and (dealer_first_card_value == 5 or dealer_first_card_value == 6):
                strategy = "Split"
            elif "Pair5" in strategy and (dealer_first_card_value >= 2 and dealer_first_card_value <= 9):
                strategy = ""
                move = "DoubleDown"
            elif "Pair6" in strategy and (dealer_first_card_value >= 2 and dealer_first_card_value <= 6):
                strategy = "Split"
            elif "Pair9" in strategy and (dealer_first_card_value >= 2 and dealer_first_card_value <= 9 and dealer_first_card_value != 7):
                strategy = "Split"
            else:
                strategy = "Hard"

        if strategy != "":
            while move != "Stand" and user_hand_value < 21:
                num_cards: int = len(user_hand)
                if num_cards > 2:
                    user_hand_value_and_strategy = self.calculate_hand_value_and_strategy(user_hand)
                    user_hand_value = user_hand_value_and_strategy[0]
                    strategy = user_hand_value_and_strategy[1]
                if strategy == "Hard":
                    if user_hand_value <= 8:
                        move = "Hit"
                    elif user_hand_value == 9:
                        if dealer_first_card_value >= 3 and dealer_first_card_value <= 6 and num_cards == 2:
                            move = "DoubleDown"
                            break
                        else:
                            move = "Hit"
                    elif user_hand_value == 10:
                        if dealer_first_card_value >= 2 and dealer_first_card_value <= 9 and num_cards == 2:
                            move = "DoubleDown"
                            break
                        else:
                            move = "Hit"
                    elif user_hand_value == 11:
                        if dealer_first_card != "Ace" and num_cards == 2:
                            move = "DoubleDown"
                            break
                        else:
                            move = "Hit"
                    elif user_hand_value >= 12 and user_hand_value <= 16:
                        if user_hand_value == 12 and (dealer_first_card_value == 2 or dealer_first_card_value == 3):
                            move = "Hit"
                        elif dealer_first_card_value >= 2 and dealer_first_card_value <= 6:
                            move = "Stand"
                        else:
                            move = "Hit"
                    else:
                        move = "Stand"

                elif strategy == "Soft":
                    if user_hand_value >= 13 and user_hand_value <= 18:
                        if dealer_first_card_value >= 3 and dealer_first_card_value <= 6 and num_cards == 2:
                            move = "DoubleDown"
                            break
                        else:
                            move = "Hit"
                    elif user_hand_value == 19:
                        if dealer_first_card_value >= 2 and dealer_first_card_value <= 6 and num_cards == 2:
                            move = "DoubleDown"
                            break
                        elif dealer_first_card_value == 7 or dealer_first_card_value == 8:
                            move = "Stand"
                        else:
                            move = "Hit"
                    else:
                        move = "Stand"

                elif strategy == "Split":
                    user_hand1: list[str] = [user_hand[0], deck.pop_card()]
                    user_hand2: list[str] = [user_hand[1], deck.pop_card()]

                    deck_copy: Deck = deck.get_deepcopy()
                    hand1_win_value: float = self.test_game(user_hand1, dealer_first_card, deck_copy)
                    hand2_win_value: float = self.test_game(user_hand2, dealer_first_card, deck_copy)

                    if hand1_win_value == hand2_win_value:
                        return hand1_win_value
                    else:
                        return (hand1_win_value + hand2_win_value) / 2

                if move == "Hit":
                    user_hand.append(deck.pop_card())

        if move == "DoubleDown":
            user_hand.append(deck.pop_card())

        dealer_hand: list[str] = [dealer_first_card]
        dealer_hand.append(deck.pop_card())

        while (dealer_hand_value := self.calculate_hand_value_and_strategy(dealer_hand)[0]) < 17:
            dealer_hand.append(deck.pop_card())

        user_hand_value = self.calculate_hand_value_and_strategy(user_hand)[0]

        # User Has More Than Dealer
        if user_hand_value > dealer_hand_value and user_hand_value <= 21:
            return 1
        # Dealer Has More Than User
        elif dealer_hand_value > user_hand_value and dealer_hand_value <= 21:
            return 0
        # Dealer Busts
        elif dealer_hand_value > 21 and user_hand_value <= 21:
            return 1
        # User Busts
        elif user_hand_value > 21 and dealer_hand_value <= 21:
            return 0
        # User and Dealer Bust
        elif user_hand_value > 21 and dealer_hand_value > 21:
            return 0
        # User and Dealer Tie at Less Than 21 -- Dealer Wins
        elif user_hand_value == dealer_hand_value and user_hand_value < 21:
            return 0
        # Both Dealer And User Get 21
        else:
            # Both Get Natural Blackjack -- Push
            if len(user_hand) == len(dealer_hand) == 2:
                return 0.5
            # Player Gets Natural Blackjack And Dealer Does Not
            elif len(user_hand) == 2 and len(dealer_hand) > 2:
                return 1
            # Dealer Gets Natural Blackjack and Player Does Not
            elif len (dealer_hand) == 2 and len(user_hand) > 2:
                return 0
            # Neither Get Natural Blackjack -- Push
            else:
                return 0.5


    # Calculate The Value Of Any Hand
    def calculate_hand_value_and_strategy(self, hand: list[str]) -> tuple[int, str]:
        hand_value: int = 0
        ace_counter: int = 0
        strategy: str = ""
            
        # Add Cards (Other Than Aces) To Hand Value
        for card in hand:
            if card != "Ace" and card in Deck.card_value_dict.keys():
                hand_value += Deck.card_value_dict[card]
            else:
                ace_counter += 1

        # Add Aces Correctly Based On Hand Value
        if ace_counter == 0:
            strategy = "Hard"
        else:
            for _ in range(ace_counter):
                if hand_value + 11 <= 21:
                    hand_value += 11
                    strategy = "Soft"
                else:
                    hand_value += 1
                    strategy = "Hard"

        # See If There Is Pair And What Kind
        if len(hand) == 2:
            if hand[0] != "Ace" and hand[1] != "Ace" and hand[0] in Deck.card_value_dict.keys() and hand[1] in Deck.card_value_dict.keys():
                if (pair_value := Deck.card_value_dict[hand[0]]) == Deck.card_value_dict[hand[1]]:
                    if pair_value == 2 or pair_value == 3 or pair_value == 7:
                        strategy += " Pair237"
                    elif pair_value == 4:
                        strategy += " Pair4"
                    elif pair_value == 5:
                        strategy += " Pair5"
                    elif pair_value == 6:
                        strategy += " Pair6"
                    elif pair_value == 9:
                        strategy += " Pair9"
                    elif pair_value == 8:
                        strategy = "Split"
            elif hand[0] == hand[1] == "Ace":
                strategy = "Split"
                
        return (hand_value, strategy)

    def play_games(self, user_hand: list[str], dealer_first_card: str, deck: Deck) -> float:
        average: float = 0
        for _ in range(10000):
            simulation_hand: list[str] = user_hand.copy()
            simulation_deck: Deck = deck.get_deepcopy()
            simulation_deck.shuffle_deck()
            average += self.test_game(simulation_hand, dealer_first_card, simulation_deck)

        return (average / 10000) * 100
