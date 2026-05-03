import random


class PigDiceGame:
    def __init__(self, winning_score=100, starting_bank=100, win_bonus=50):
        self.winning_score = winning_score
        self.starting_bank = starting_bank
        self.win_bonus = win_bonus

        self.bank = [starting_bank, starting_bank]  # fichas
        self.bets = [0, 0]  # apuesta actual (se puede cambiar durante el turno)

        self.scores = [0, 0]
        self.current_player = 0
        self.turn_score = 0
        self.last_roll = None
        self.game_over = False
        self.winner = None

    def reset_for_new_game(self, starting_player=0):
        # conserva bank, resetea el resto
        self.bets = [0, 0]
        self.scores = [0, 0]
        self.current_player = starting_player
        self.turn_score = 0
        self.last_roll = None
        self.game_over = False
        self.winner = None

    def set_bet(self, player_id, amount):
        if self.game_over:
            return {"type": "bet", "error": "El juego ha terminado"}

        if player_id != self.current_player:
            return {"type": "bet", "error": "No es tu turno"}

        if amount is None:
            amount = 0

        try:
            amount = int(amount)
        except:
            amount = 0

        if amount < 0:
            return {"type": "bet", "error": "La apuesta no puede ser negativa"}

        # Para no bloquear si alguien se queda sin fichas, permitimos 0 (sin apuesta)
        if amount > self.bank[player_id]:
            return {
                "type": "bet",
                "error": "No tienes tantas fichas",
                "bank": self.bank[player_id],
                "bet": self.bets[player_id],
            }

        self.bets[player_id] = amount
        return {
            "type": "bet",
            "message": f"Apuesta actual: {amount}",
            "bet": amount,
            "bank": self.bank[player_id],
        }

    def roll_dice(self):
        if self.game_over:
            return {"error": "El juego ha terminado"}

        roll = random.randint(1, 6)
        self.last_roll = roll

        bet = self.bets[self.current_player]

        if roll == 1:
            # pierde turno + pierde apuesta (si era > 0)
            if bet > 0:
                self.bank[self.current_player] -= bet

            self.turn_score = 0
            result = {
                "roll": roll,
                "bet": bet,
                "bank": self.bank[self.current_player],
                "message": f"¡Sacaste 1! Pierdes tu turno. Apuesta: -{bet} fichas",
                "turn_score": 0,
                "switch_turn": True,
            }

            self.bets[self.current_player] = 0
            self.switch_player()
            return result

        # roll 2..6: suma puntos y gana apuesta (si era > 0)
        if bet > 0:
            self.bank[self.current_player] += bet

        self.turn_score += roll
        return {
            "roll": roll,
            "bet": bet,
            "bank": self.bank[self.current_player],
            "message": f"Sacaste {roll}. +{bet} fichas. Puntos del turno: {self.turn_score}",
            "turn_score": self.turn_score,
            "switch_turn": False,
        }

    def hold(self):
        if self.game_over:
            return {"error": "El juego ha terminado"}

        self.scores[self.current_player] += self.turn_score
        saved_score = self.turn_score

        result = {
            "message": f"¡Guardaste {saved_score} puntos!",
            "saved_score": saved_score,
            "total_score": self.scores[self.current_player],
            "switch_turn": True,
        }

        # Al cerrar turno, se resetea apuesta del jugador actual
        self.bets[self.current_player] = 0

        if self.scores[self.current_player] >= self.winning_score:
            self.game_over = True
            self.winner = self.current_player

            # Bonus de fichas al ganar
            self.bank[self.winner] += self.win_bonus

            result["winner"] = self.winner
            result["bank"] = self.bank[self.winner]
            result["message"] = (
                f"¡Jugador {self.current_player + 1} gana con {self.scores[self.current_player]} puntos! "
                f"(+{self.win_bonus} fichas)"
            )
            return result

        self.turn_score = 0
        self.switch_player()
        return result

    def switch_player(self):
        self.current_player = 1 - self.current_player
        self.turn_score = 0

    def get_state(self):
        return {
            "scores": self.scores,
            "current_player": self.current_player,
            "turn_score": self.turn_score,
            "last_roll": self.last_roll,
            "game_over": self.game_over,
            "winner": self.winner,
            "bank": self.bank,
            "bets": self.bets,
        }
