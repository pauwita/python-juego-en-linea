import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json


def get_server_addr(fname="pinggy.txt", default_host="172.26.137.102",
                    default_port=5555):
    """Reutilizamos pinggy.txt solo como host:puerto.
    Así no hay que tocar el código cada vez, solo editas el txt."""
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            line = f.read().strip()
            host, port = line.split(':')
            return host.strip(), int(port.strip())
    except:
        return default_host, default_port


class PigDiceClient:
    def __init__(self):
        self.client_socket = None
        self.player_id = None
        self.connected = False

        self.window = tk.Tk()
        self.window.title("Pig Dice Game")
        self.window.geometry("600x750")
        self.window.configure(bg="#fcfcf9")

        self.rematch_button = tk.Button(self.window, text="Rematch", font=("Arial", 14, "bold"),
                                        bg="#21808d", fg="white", padx=30, pady=10,
                                        command=self.request_rematch)
        self.rematch_button.pack(pady=10)
        self.rematch_button.pack_forget()

        self.setup_ui()

    def setup_ui(self):
        # Pantalla conexión
        self.connection_frame = tk.Frame(self.window, bg="#fcfcf9")
        self.connection_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        tk.Label(self.connection_frame, text="PIG DICE GAME", font=("Arial", 24, "bold"),
                 bg="#fcfcf9", fg="#21808d").pack(pady=20)

        tk.Label(self.connection_frame, text="Nombre del jugador:", font=("Arial", 12),
                 bg="#fcfcf9").pack(pady=5)
        self.name_entry = tk.Entry(self.connection_frame, font=("Arial", 14), width=20)
        self.name_entry.pack(pady=10)
        self.name_entry.insert(0, "Paula")

        self.connect_btn = tk.Button(self.connection_frame, text="CONECTAR", font=("Arial", 14, "bold"),
                                     bg="#21808d", fg="white", padx=30, pady=10,
                                     command=self.connect_to_server)
        self.connect_btn.pack(pady=20)

        self.status_label = tk.Label(self.connection_frame, text="", font=("Arial", 11),
                                     bg="#fcfcf9", fg="#666")
        self.status_label.pack()

        # --- Pantalla de juego ---
        self.game_frame = tk.Frame(self.window, bg="#fcfcf9")

        self.game_title = tk.Label(self.game_frame, text="PIG DICE", font=("Arial", 20, "bold"),
                                   bg="#fcfcf9", fg="#21808d")
        self.game_title.pack(pady=10)

        scores_frame = tk.Frame(self.game_frame, bg="#fcfcf9")
        scores_frame.pack(pady=10, fill=tk.X, padx=30)

        # Jugador 1
        self.p1_frame = tk.Frame(scores_frame, bg="#e6f7f9", relief=tk.RIDGE, bd=3)
        self.p1_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)
        tk.Label(self.p1_frame, text="JUGADOR 1", font=("Arial", 12, "bold"),
                 bg="#e6f7f9").pack(pady=5)
        self.p1_name_label = tk.Label(self.p1_frame, text="---", font=("Arial", 10), bg="#e6f7f9")
        self.p1_name_label.pack()
        self.p1_score_label = tk.Label(self.p1_frame, text="0", font=("Arial", 32, "bold"),
                                       bg="#e6f7f9", fg="#21808d")
        self.p1_score_label.pack(pady=5)
        self.p1_bank_label = tk.Label(self.p1_frame, text="Fichas: 100", font=("Arial", 11, "bold"),
                                      bg="#e6f7f9", fg="#21808d")
        self.p1_bank_label.pack(pady=5)

        # Jugador 2
        self.p2_frame = tk.Frame(scores_frame, bg="#fff3cd", relief=tk.RIDGE, bd=3)
        self.p2_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10)
        tk.Label(self.p2_frame, text="JUGADOR 2", font=("Arial", 12, "bold"),
                 bg="#fff3cd").pack(pady=5)
        self.p2_name_label = tk.Label(self.p2_frame, text="---", font=("Arial", 10), bg="#fff3cd")
        self.p2_name_label.pack()
        self.p2_score_label = tk.Label(self.p2_frame, text="0", font=("Arial", 32, "bold"),
                                       bg="#fff3cd", fg="#d97706")
        self.p2_score_label.pack(pady=5)
        self.p2_bank_label = tk.Label(self.p2_frame, text="Fichas: 100", font=("Arial", 11, "bold"),
                                      bg="#fff3cd", fg="#d97706")
        self.p2_bank_label.pack(pady=5)

        self.turn_label = tk.Label(self.game_frame, text="Esperando jugadores...",
                                   font=("Arial", 14, "bold"), bg="#fcfcf9", fg="#21808d")
        self.turn_label.pack(pady=10)

        # Dado
        self.dice_frame = tk.Frame(self.game_frame, bg="white", relief=tk.RAISED, bd=5)
        self.dice_frame.pack(pady=15)
        self.dice_label = tk.Label(self.dice_frame, text="", font=("Arial", 80), bg="white",
                                   width=3, height=1)
        self.dice_label.pack(padx=20, pady=20)

        self.turn_score_label = tk.Label(self.game_frame, text="Puntos del turno: 0",
                                         font=("Arial", 16, "bold"), bg="#fcfcf9", fg="#d97706")
        self.turn_score_label.pack(pady=5)

        # Apuestas
        bet_frame = tk.Frame(self.game_frame, bg="#fcfcf9")
        bet_frame.pack(pady=5)
        tk.Label(bet_frame, text="Apuesta (fichas):", font=("Arial", 12), bg="#fcfcf9").pack(side=tk.LEFT, padx=5)
        self.bet_entry = tk.Entry(bet_frame, font=("Arial", 12), width=8)
        self.bet_entry.insert(0, "10")
        self.bet_entry.pack(side=tk.LEFT, padx=5)
        self.bet_btn = tk.Button(bet_frame, text="APOSTAR", font=("Arial", 12, "bold"),
                                 bg="#21808d", fg="white", command=self.send_bet, state=tk.DISABLED)
        self.bet_btn.pack(side=tk.LEFT, padx=5)

        self.bet_status_label = tk.Label(self.game_frame, text="Apuesta actual: 0",
                                         font=("Arial", 12, "bold"), bg="#fcfcf9", fg="#333")
        self.bet_status_label.pack(pady=5)

        # Botones juego
        buttons_frame = tk.Frame(self.game_frame, bg="#fcfcf9")
        buttons_frame.pack(pady=10)
        self.roll_btn = tk.Button(buttons_frame, text="TIRAR DADO", font=("Arial", 14, "bold"),
                                  bg="#21808d", fg="white", padx=20, pady=15, state=tk.DISABLED,
                                  command=self.roll_dice)
        self.roll_btn.pack(side=tk.LEFT, padx=10)
        self.hold_btn = tk.Button(buttons_frame, text="HOLD", font=("Arial", 14, "bold"),
                                  bg="#ffc107", fg="black", padx=20, pady=15, state=tk.DISABLED,
                                  command=self.hold)
        self.hold_btn.pack(side=tk.LEFT, padx=10)

        self.message_label = tk.Label(self.game_frame, text="", font=("Arial", 12),
                                      bg="#fcfcf9", fg="#c0152f", wraplength=500)
        self.message_label.pack(pady=8)

        # Chat
        chat_frame = tk.Frame(self.game_frame, bg="#fcfcf9")
        chat_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        self.chat_history = tk.Text(chat_frame, height=6, state=tk.DISABLED, bg="white",
                                    fg="black", wrap=tk.WORD)
        self.chat_history.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        bottom_chat = tk.Frame(chat_frame, bg="#fcfcf9")
        bottom_chat.pack(fill=tk.X, padx=10, pady=5)
        self.chat_entry = tk.Entry(bottom_chat, font=("Arial", 11))
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chat_entry.bind("<Return>", lambda e: self.send_chat())
        self.chat_send_btn = tk.Button(bottom_chat, text="Enviar", font=("Arial", 11, "bold"),
                                       bg="#21808d", fg="white", command=self.send_chat)
        self.chat_send_btn.pack(side=tk.LEFT, padx=5)

        # Reacciones
        reactions_frame = tk.Frame(self.game_frame, bg="#fcfcf9")
        reactions_frame.pack(pady=5)
        for emoji in ["😀", "😂", "👍", "❤️", "😢"]:
            btn = tk.Button(reactions_frame, text=emoji, font=("Arial", 14), width=2,
                            command=lambda e=emoji: self.send_reaction(e))
            btn.pack(side=tk.LEFT, padx=3)

    def connect_to_server(self):
        player_name = self.name_entry.get().strip()
        if not player_name:
            messagebox.showwarning("Advertencia", "Por favor ingresa tu nombre")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            host, port = get_server_addr()
            self.client_socket.connect((host, port))

            # FIX: enviar con \n como delimitador
            data = {'name': player_name}
            self.client_socket.send((json.dumps(data) + '\n').encode('utf-8'))

            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()

            self.status_label.config(text=f'Conectando a {host}:{port}...', fg="#21808d")
            self.connect_btn.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f'No se pudo conectar al servidor: {e}')

    def receive_messages(self):
        # FIX: buffer acumulador para framing TCP correcto
        buffer = ''
        try:
            while True:
                chunk = self.client_socket.recv(4096).decode('utf-8')
                if not chunk:
                    break

                buffer += chunk
                # Procesar todos los mensajes completos disponibles en el buffer
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        message = json.loads(line)
                        self.window.after(0, lambda m=message: self.process_message(m))

        except Exception as e:
            print(f'Error recibiendo mensaje: {e}')
            self.window.after(0, lambda: messagebox.showerror("Error",
                                                              'Conexión perdida con el servidor'))

    def process_message(self, message):
        msg_type = message.get('type')

        if msg_type == 'connected':
            self.player_id = message['player_id']
            self.connected = True
            self.status_label.config(text=message['message'])
        elif msg_type == 'game_start':
            self.connection_frame.pack_forget()
            self.game_frame.pack(fill=tk.BOTH, expand=True)
            players = message['players']
            self.p1_name_label.config(text=players[0])
            self.p2_name_label.config(text=players[1])
            self.update_game_state(message)
        elif msg_type == 'update':
            self.update_game_state(message)
            action = message.get('last_action', {})
            if 'message' in action:
                self.message_label.config(text=action['message'])
            if 'roll' in action:
                dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
                self.dice_label.config(text=dice_faces[action['roll'] - 1])
        elif msg_type == 'error':
            messagebox.showerror("Error", message.get('message', 'Error desconocido'))
        elif msg_type == 'chat':
            sender = message.get('from', 'Jugador')
            text = message.get('text', '')
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.insert(tk.END, f"{sender}: {text}\n")
            self.chat_history.see(tk.END)
            self.chat_history.config(state=tk.DISABLED)
        elif msg_type == 'reaction':
            sender = message.get('from', 'Jugador')
            emoji = message.get('emoji', '')
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.insert(tk.END, f"{sender} reacción {emoji}\n")
            self.chat_history.see(tk.END)
            self.chat_history.config(state=tk.DISABLED)

    def update_game_state(self, state):
        scores = state.get('scores', [0, 0])
        bank = state.get('bank', [100, 100])
        bets = state.get('bets', [0, 0])

        self.p1_score_label.config(text=str(scores[0]))
        self.p2_score_label.config(text=str(scores[1]))
        self.p1_bank_label.config(text=f"Fichas: {bank[0]}")
        self.p2_bank_label.config(text=f"Fichas: {bank[1]}")

        current_player = state.get('current_player', 0)
        players = state.get('players', ['Jugador 1', 'Jugador 2'])
        turn_score = state.get('turn_score', 0)

        self.turn_score_label.config(text=f"Puntos del turno: {turn_score}")
        self.bet_status_label.config(text=f"Apuesta actual: {bets[current_player]}")

        if state.get('game_over'):
            winner = state.get('winner', 0)
            self.turn_label.config(text=f"{players[winner]} ¡GANA!")
            self.roll_btn.config(state=tk.DISABLED)
            self.hold_btn.config(state=tk.DISABLED)
            self.bet_btn.config(state=tk.DISABLED)
            self.rematch_button.config(state=tk.NORMAL)
            self.rematch_button.pack(pady=10)
            return

        self.rematch_button.pack_forget()
        self.turn_label.config(text=f"Turno de {players[current_player]}")

        if current_player == self.player_id:
            self.bet_btn.config(state=tk.NORMAL)
            self.roll_btn.config(state=tk.NORMAL)
            self.hold_btn.config(state=tk.NORMAL)
        else:
            self.bet_btn.config(state=tk.DISABLED)
            self.roll_btn.config(state=tk.DISABLED)
            self.hold_btn.config(state=tk.DISABLED)

        if current_player == 0:
            self.p1_frame.config(bg="#a7e6ed", bd=4)
            self.p2_frame.config(bg="#fff3cd", bd=2)
        else:
            self.p1_frame.config(bg="#e6f7f9", bd=2)
            self.p2_frame.config(bg="#ffd97d", bd=4)

    def send_bet(self):
        if not self.client_socket:
            return

        try:
            amount = int(self.bet_entry.get().strip() or 0)
        except:
            messagebox.showerror("Error", "La apuesta debe ser un número entero")
            return

        msg = {'type': 'bet', 'amount': amount}
        try:
            # FIX: enviar con \n como delimitador
            self.client_socket.send((json.dumps(msg) + '\n').encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Error", f'No se pudo enviar la apuesta: {e}')

    def roll_dice(self):
        if self.client_socket:
            # FIX: enviar con \n como delimitador
            self.client_socket.send((json.dumps({'type': 'roll'}) + '\n').encode('utf-8'))

    def hold(self):
        if self.client_socket:
            # FIX: enviar con \n como delimitador
            self.client_socket.send((json.dumps({'type': 'hold'}) + '\n').encode('utf-8'))

    def request_rematch(self):
        if not self.client_socket:
            messagebox.showerror("Error", "No hay conexión con el servidor.")
            return

        try:
            # FIX: enviar con \n como delimitador
            self.client_socket.send((json.dumps({'type': 'rematch_request'}) + '\n').encode('utf-8'))
            self.rematch_button.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f'Error solicitando rematch: {e}')

    def send_chat(self):
        if not self.client_socket:
            return

        text = self.chat_entry.get().strip()
        if not text:
            return

        msg = {'type': 'chat', 'text': text}
        try:
            # FIX: enviar con \n como delimitador
            self.client_socket.send((json.dumps(msg) + '\n').encode('utf-8'))
            self.chat_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f'No se pudo enviar el mensaje: {e}')

    def send_reaction(self, emoji):
        if not self.client_socket:
            return

        msg = {'type': 'reaction', 'emoji': emoji}
        try:
            # FIX: enviar con \n como delimitador
            self.client_socket.send((json.dumps(msg) + '\n').encode('utf-8'))
        except Exception as e:
            messagebox.showerror("Error", f'No se pudo enviar la reacción: {e}')

    def run(self):
        self.window.mainloop()


if __name__ == '__main__':
    client = PigDiceClient()
    client.run()
