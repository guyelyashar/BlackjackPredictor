import random
import copy
from typing import Self

class Deck:

    card_value_dict: dict[str, int] = {
                        "Two" : 2,
                        "Three" : 3,
                        "Four" : 4,
                        "Five" : 5,
                        "Six" : 6,
                        "Seven" : 7,
                        "Eight" : 8,
                        "Nine" : 9,
                        "Ten" : 10,
                        "Jack" : 10,
                        "Queen" : 10,
                        "King" : 10
                    }


    def __init__(self) -> None:
        self.card_list: list[str] = self.__add_one_deck(card_list=[])


    def combine_decks(self) -> None:
        self.card_list += self.__add_one_deck([])


    def __add_one_deck(self, card_list: list[str]) -> list[str]:
        for key in Deck.card_value_dict:
            for _ in range(4):
                card_list.append(key)
        
        for _ in range(4):
            card_list.append("Ace")

        return card_list


    def shuffle_deck(self) -> None:
        random.shuffle(self.card_list)

        
    def remove_card(self, card_name: str) -> None:
        self.card_list.remove(card_name)


    def pop_card(self) -> str:
        return self.card_list.pop()


    def get_deepcopy(self) -> Self:
        return copy.deepcopy(self)


    @staticmethod
    def is_card(card: str) -> bool:
        return card in Deck.card_value_dict
    