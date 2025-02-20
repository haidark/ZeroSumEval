from collections import Counter
import random
from typing import Dict, List
from zero_sum_eval.game_state import Action, GameState, InvalidMoveError, PlayerDefinition
from zero_sum_eval.registry import GAME_REGISTRY
from zero_sum_eval.player import Move
from .poker_player import PokerPlayer

@GAME_REGISTRY.register("poker")
class PokerGame(GameState):
    """
    Implementation of a simplified Poker game where players take turns betting or folding.
    Supports a fixed number of rounds.
    
    The showdown and awarding of the pot is handled in update_game.
    The get_scores method remains pure and only returns the current chip counts.
    """
    
    def __init__(self, starting_chips: int = 1000, small_blind: int = 10, rounds: int = 3, **kwargs):
        super().__init__(**kwargs)
        self.num_players = len(self.players)
        self.starting_chips = starting_chips
        self.small_blind = small_blind
        self.big_blind = small_blind * 2
        self.player_keys = [f"player_{i}" for i in range(self.num_players)]
        self.dealer_pos = 0  # Track dealer position for blinds
        self.rounds = rounds
        self.current_round = 1
        self.message = "Start!"
        self.last_evaluation = None
        # Initialize chip counts only once (they persist across hands)
        self.chips = {player_key: self.starting_chips for player_key in self.player_keys}
        self.reset_game()

    def reset_game(self):
        """Reset the hand-specific state for a new hand, preserving chip counts."""
        self.deck = list(range(52))
        random.seed(1)
        random.shuffle(self.deck)
        
        self.hole_cards = {
            player_key: [self.deck.pop(), self.deck.pop()]
            for player_key in self.player_keys
        }
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.bets = {player_key: 0 for player_key in self.player_keys}
        self.folded = set()
        self.stage = "preflop"
        self.history = []
        self.hand_finalized = False
        
        # Post blinds for the new hand.
        sb_pos = (self.dealer_pos + 1) % self.num_players
        bb_pos = (self.dealer_pos + 2) % self.num_players
        sb_player = self.player_keys[sb_pos]
        bb_player = self.player_keys[bb_pos]
        
        self.chips[sb_player] -= self.small_blind
        self.bets[sb_player] = self.small_blind
        
        self.chips[bb_player] -= self.big_blind
        self.bets[bb_player] = self.big_blind
        
        self.pot = self.small_blind + self.big_blind
        self.current_bet = self.big_blind
        self.current_player_idx = (bb_pos + 1) % self.num_players

    def update_game(self, move: Move):
        """
        Process a player's move and update the game state.
        If the hand is complete and showdown has not yet occurred, handle the showdown here.
        """
        action = move.value.strip()
        player_key = self.get_next_action().player.player_key
        
        if action.startswith("Fold"):
            self.message = f"{player_key} folds"
            self.folded.add(player_key)
            self.history.append(f"{player_key}: Fold")
        elif action.startswith("Call"):
            amount = self.current_bet - self.bets[player_key]
            self.message = f"{player_key} calls {amount}"
            if amount > self.chips[player_key]:
                raise InvalidMoveError("Not enough chips to call")
            self.chips[player_key] -= amount
            self.bets[player_key] += amount
            self.pot += amount
            self.history.append(f"{player_key}: Call {amount}")
        elif action.startswith("Raise"):
            try:
                _, amount_str = action.split()
                amount = int(amount_str)
            except ValueError:
                raise InvalidMoveError("Invalid raise format")
            self.message = f"{player_key} raises {amount}"
            total_to_call = self.current_bet - self.bets[player_key] + amount
            if total_to_call > self.chips[player_key]:
                raise InvalidMoveError("Not enough chips to raise")
            if amount < self.big_blind:
                raise InvalidMoveError("Raise must be at least the big blind")
            self.chips[player_key] -= total_to_call
            self.pot += total_to_call
            self.bets[player_key] += total_to_call
            self.current_bet = self.bets[player_key]
            self.history.append(f"{player_key}: Raise {amount}")
        else:
            raise InvalidMoveError("Invalid action format")
            
        # Check if betting round is complete and advance stage if needed.
        if self._is_betting_round_complete():
            self._advance_stage()
            
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        while self.player_keys[self.current_player_idx] in self.folded:
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players

        # If the hand is complete and showdown has not been processed, handle it.
        if self._is_hand_over() and not self.hand_finalized:
            self._finalize_hand()
            # If there are more rounds (and more than one player remains), prepare the next hand.
            if self.current_round <= self.rounds and len([p for p in self.player_keys if self.chips[p] > 0]) > 1:
                self.current_round += 1
                self.dealer_pos = (self.dealer_pos + 1) % self.num_players
                self.reset_game()

    def _finalize_hand(self):
        """Handle the showdown and award the pot to the winning player."""
        if len(self.folded) == len(self.player_keys) - 1:
            # Only one player remains.
            winner = next(p for p in self.player_keys if p not in self.folded)
            self.chips[winner] += self.pot
            self.message = f"{winner} wins the pot of {self.pot} by default, as all other players have folded"
            
        else:
            # Showdown: evaluate hands for all active players.
            active_players = [p for p in self.player_keys if p not in self.folded]
            hand_ranks = {
                player: self._evaluate_hand(self.hole_cards[player], self.community_cards)
                for player in active_players
            }
            # Determine the winner based on the full evaluation tuple.
            winner = max(hand_ranks.items(), key=lambda x: x[1])[0]
            self.chips[winner] += self.pot
            self.last_evaluation = f"{winner} wins the showdown and takes the pot of {self.pot}\n"
            self.last_evaluation += "Hands:"
            category_names = {
                8: "Straight flush",
                7: "Four of a kind",
                6: "Full house",
                5: "Flush",
                4: "Straight",
                3: "Three of a kind",
                2: "Two pair",
                1: "One pair",
                0: "High card"
            }
            for player, eval_tuple in hand_ranks.items():
                # The first element is the hand category.
                cat = eval_tuple[0]
                tiebreakers = eval_tuple[1:]
                msg_line = f"{player}: {category_names.get(cat, 'Unknown')}"
                if tiebreakers:
                    msg_line += f" with tie-breakers {tiebreakers}"
                self.message += f"\n{msg_line}"
        self.hand_finalized = True

    def _evaluate_hand(self, hole_cards: List[int], community_cards: List[int]) -> tuple:
        """
        Evaluate a poker hand and return a tuple representing its rank.
        The tuple is constructed so that higher tuples represent stronger hands.
        
        Hand categories (first element of the tuple):
        8: Straight flush
        7: Four of a kind
        6: Full house
        5: Flush
        4: Straight
        3: Three of a kind
        2: Two pair
        1: One pair
        0: High card
        
        Additional elements in the tuple are used for tie-breaking.
        """
        all_cards = hole_cards + community_cards
        ranks = [card % 13 for card in all_cards]
        suits = [card // 13 for card in all_cards]
        
        rank_counts = Counter(ranks)
        suit_counts = Counter(suits)
        # For tie-breakers, sort all card ranks descending.
        sorted_ranks = sorted(ranks, reverse=True)
        
        # Helper: Given a sorted list (ascending) of unique ranks, check for a straight.
        def check_straight(unique_ranks):
            # To handle Ace-low straight, if Ace (12) is present, consider it as -1 as well.
            temp = list(unique_ranks)
            if 12 in unique_ranks:
                temp.insert(0, -1)
            for i in range(len(temp) - 4):
                window = temp[i:i+5]
                if window[4] - window[0] == 4 and len(set(window)) == 5:
                    return window[4]  # highest card in the straight (using our internal rank values)
            return None

        # Check for flush: any suit with 5 or more cards.
        flush_suit = None
        for suit, count in suit_counts.items():
            if count >= 5:
                flush_suit = suit
                break
        flush_ranks = []
        if flush_suit is not None:
            flush_ranks = sorted([ranks[i] for i in range(len(all_cards)) if suits[i] == flush_suit])
        
        # Check for straight flush: look for a straight among the flush cards.
        straight_flush_high = None
        if flush_ranks:
            unique_flush = sorted(set(flush_ranks))
            sf_high = check_straight(unique_flush)
            if sf_high is not None:
                straight_flush_high = sf_high
        if straight_flush_high is not None:
            return (8, straight_flush_high)
        
        # Four of a kind: one rank appears 4 times.
        fours = [r for r, count in rank_counts.items() if count == 4]
        if fours:
            four_rank = max(fours)
            # Kicker: highest card not part of the four.
            kickers = [r for r in sorted_ranks if r != four_rank]
            kicker = kickers[0] if kickers else 0
            return (7, four_rank, kicker)
        
        # Full house: one three-of-a-kind and one pair (or a second three-of-a-kind).
        trips = [r for r, count in rank_counts.items() if count == 3]
        pairs = [r for r, count in rank_counts.items() if count == 2]
        if trips:
            trip_rank = max(trips)
            remaining_pairs = pairs + [r for r in trips if r != trip_rank]
            if remaining_pairs:
                pair_rank = max(remaining_pairs)
                return (6, trip_rank, pair_rank)
        
        # Flush: return the top five cards of the flush suit.
        if flush_ranks:
            best_flush = sorted(flush_ranks, reverse=True)[:5]
            return (5, tuple(best_flush))
        
        # Straight: check among all unique ranks.
        unique_ranks = sorted(set(ranks))
        straight_high = check_straight(unique_ranks)
        if straight_high is not None:
            return (4, straight_high)
        
        # Three of a kind.
        if trips:
            trip_rank = max(trips)
            kickers = [r for r in sorted_ranks if r != trip_rank][:2]
            return (3, trip_rank, tuple(kickers))
        
        # Two pair.
        if len(pairs) >= 2:
            top_pairs = sorted(pairs, reverse=True)[:2]
            kicker_candidates = [r for r in sorted_ranks if r not in top_pairs]
            kicker = kicker_candidates[0] if kicker_candidates else 0
            return (2, tuple(top_pairs), kicker)
        
        # One pair.
        if pairs:
            pair_rank = max(pairs)
            kickers = [r for r in sorted_ranks if r != pair_rank][:3]
            return (1, pair_rank, tuple(kickers))
        
        # High card: top five cards.
        return (0, tuple(sorted_ranks[:5]))

    def _is_betting_round_complete(self) -> bool:
        """Check if the current betting round is complete."""
        active_players = [p for p in self.player_keys if p not in self.folded]
        return len(active_players) == 1 or all(self.bets[p] == self.current_bet for p in active_players)

    def _advance_stage(self):
        """Advance to the next stage of the hand if appropriate."""
        if len(self.folded) == 1:
            return  # No need to advance if only one player remains.
            
        if self.stage == "preflop":
            self.community_cards.extend([self.deck.pop() for _ in range(3)])
            self.stage = "flop"
        elif self.stage == "flop":
            self.community_cards.append(self.deck.pop())
            self.stage = "turn"
        elif self.stage == "turn":
            self.community_cards.append(self.deck.pop())
            self.stage = "river"
            
        # Reset bets for the new stage.
        self.bets = {player_key: 0 for player_key in self.player_keys}
        self.current_bet = 0

    def _is_hand_over(self) -> bool:
        """
        Determine if the current hand is complete.
        A hand is considered over if one player remains (by fold or by chips)
        or if the river betting round is complete.
        """
        active_players = [p for p in self.player_keys if self.chips[p] > 0]
        if len(active_players) == 1:
            return True

        return (len(self.folded) == len(self.player_keys) - 1) or (
            self.stage == "river" and self._is_betting_round_complete()
        )

    def is_over(self) -> bool:
        """Check if the game is over."""
        return self.current_round > self.rounds or len([p for p in self.player_keys if self.chips[p] > 0]) <= 1

    def get_scores(self) -> Dict[str, int]:
        """Return the current chip counts (pure, with no side effects)."""
        return self.chips.copy()

    def get_next_action(self) -> Action:
        """Return the next action for the current player."""
        return Action("MakeMove", self.players[self.player_keys[self.current_player_idx]])

    def player_inputs(self) -> Dict[str, str]:
        """Return the inputs for the next player's turn."""
        player_key = self.get_next_action().player.player_key
        return {
            'hole_cards': self._format_cards(self.hole_cards[player_key]),
            'community_cards': self._format_cards(self.community_cards),
            'pot': self.pot,
            'current_bet': self.current_bet,
            'chips': self.chips[player_key],
            'stage': self.stage,
            'history': "\n".join(self.history),
        }

    def _format_cards(self, cards: List[int]) -> str:
        """Convert card integers to a human-readable format."""
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return " ".join(f"{ranks[card % 13]}{suits[card // 13]}" for card in cards)

    def player_definitions(self) -> List[PlayerDefinition]:
        """Define the players for this game."""
        return [
            PlayerDefinition(player_key=player_key, actions=["MakeMove"], default_player_class=PokerPlayer, optional=i >= 2)
            for i, player_key in enumerate([f"player_{i}" for i in range(10)])
        ]

    def display(self) -> str:
        """Return a string representation of the game state."""
        display_str = f"{self.message}\n"
        # Show the last evaluation only if the hand is over and on the first display after the hand.
        if self.last_evaluation and self.history == []:
            display_str += f"Last hand's evaluation:\n{self.last_evaluation}\n"
        display_str += f"Round: {self.current_round}/{self.rounds}\n"
        display_str += f"Stage: {self.stage}\n"
        display_str += f"Community cards: {self._format_cards(self.community_cards)}\n"
        display_str += f"Pot: {self.pot}\n"
        display_str += f"Current bet: {self.current_bet}\n"
        for player_key in self.player_keys:
            display_str += f"{player_key} chips: {self.chips[player_key]}\n"
        display_str += "History:\n" + "\n".join(self.history) + "\n"
        display_str += f"Chips (scores): {self.get_scores()}\n"
        return display_str

    def export(self):
        """Export the game state."""
        return {
            'stage': self.stage,
            'pot': self.pot,
            'current_bet': self.current_bet,
            'chips': self.chips,
            'history': self.history,
            'scores': self.get_scores(),
            'round': f"{self.current_round}/{self.rounds}"
        }