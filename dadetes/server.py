import socket
import threading
import json
from game_logic import PigDiceGame


class GameServer:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # FIX: SO_REUSEADDR evita "Address already in use" al reiniciar
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []  # (socket, nombre, jugadorid)
        self.game = PigDiceGame()
        self.lock = threading.Lock()
        self.rematch_votes = [False, False]

    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f'Servidor Pig Dice iniciado en {self.host}:{self.port}')
        print('Esperando jugadores...')

        while True:
            client_socket, address = self.server.accept()
            print(f'Nueva conexión desde {address}')
            thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            thread.daemon = True
            thread.start()

    def handle_client(self, client_socket):
        player_id = None
        # FIX: buffer para manejar correctamente el framing TCP
        buffer = ''
        try:
            # Recibir nombre del jugador
            while '\n' not in buffer:
                chunk = client_socket.recv(4096).decode('utf-8')
                if not chunk:
                    client_socket.close()
                    return
                buffer += chunk

            line, buffer = buffer.split('\n', 1)
            player_info = json.loads(line)
            player_name = player_info.get('name', 'Jugador')

            with self.lock:
                player_id = len(self.clients)
                if player_id >= 2:
                    response = {'type': 'error', 'message': 'El juego ya está lleno'}
                    client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                    client_socket.close()
                    return

                self.clients.append((client_socket, player_name, player_id))
                response = {'type': 'connected', 'player_id': player_id,
                            'message': f'Conectado como Jugador {player_id + 1}'}
                client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
                print(f'Jugador {player_id + 1} ({player_name}) conectado')

                if len(self.clients) == 2:
                    self.start_game()

            # BUCLE ÚNICO: juego + apuestas + chat + reacciones + rematch
            while True:
                # FIX: acumular en buffer hasta tener un mensaje completo (\n)
                while '\n' not in buffer:
                    chunk = client_socket.recv(4096).decode('utf-8')
                    if not chunk:
                        return
                    buffer += chunk

                line, buffer = buffer.split('\n', 1)
                msg = json.loads(line)
                msg_type = msg.get('type')

                if msg_type in ['roll', 'hold']:
                    self.process_action(msg, player_id)
                elif msg_type == 'bet':
                    self.process_bet(msg, player_id)
                elif msg_type == 'rematch_request':
                    self.process_rematch(player_id)
                elif msg_type == 'chat':
                    with self.lock:
                        name = next((n for s, n, pid in self.clients if pid == player_id), 'Jugador')
                        chat_msg = {'type': 'chat', 'from': name, 'text': msg.get('text', '')}
                        self.broadcast(chat_msg)
                elif msg_type == 'reaction':
                    with self.lock:
                        name = next((n for s, n, pid in self.clients if pid == player_id), 'Jugador')
                        react_msg = {'type': 'reaction', 'from': name, 'emoji': msg.get('emoji', '')}
                        self.broadcast(react_msg)

        except Exception as e:
            print(f'Error con cliente: {e}')
        finally:
            with self.lock:
                self.clients = [(s, n, pid) for s, n, pid in self.clients if s != client_socket]
                print(f'Cliente desconectado. Jugadores actuales: {len(self.clients)}')
                self.rematch_votes = [False, False]

            try:
                client_socket.close()
            except:
                pass

    def start_game(self):
        print('¡El juego ha comenzado!')
        game_state = self.game.get_state()
        game_state['type'] = 'game_start'
        game_state['players'] = [name for _, name, _ in self.clients]
        self.broadcast(game_state)

    def process_bet(self, msg, player_id):
        with self.lock:
            if self.game.game_over:
                return

            amount = msg.get('amount', 0)
            try:
                amount = int(amount)
            except:
                amount = 0

            result = self.game.set_bet(player_id, amount)
            game_state = self.game.get_state()
            game_state['type'] = 'update'
            game_state['last_action'] = result
            game_state['players'] = [name for _, name, _ in self.clients]
            self.broadcast(game_state)

    def process_rematch(self, player_id):
        with self.lock:
            # FIX: condición corregida — solo rechazar IDs inválidos (>= 2)
            if player_id is None or player_id >= 2:
                return

            self.rematch_votes[player_id] = True

            # Si los 2 votan rematch
            if len(self.clients) == 2 and all(self.rematch_votes):
                self.game.reset_for_new_game(starting_player=0)
                self.rematch_votes = [False, False]
                self.start_game()

    def process_action(self, action, player_id):
        with self.lock:
            if self.game.current_player != player_id:
                return

            action_type = action.get('type')
            if action_type == 'roll':
                result = self.game.roll_dice()
            elif action_type == 'hold':
                result = self.game.hold()
            else:
                return

            game_state = self.game.get_state()
            game_state['type'] = 'update'
            game_state['last_action'] = result
            game_state['players'] = [name for _, name, _ in self.clients]
            self.broadcast(game_state)

            if result.get('winner') is not None:
                winner = result['winner']
                # FIX: f-string corregida con {} y sin manipulación de índice incorrecta
                print(f'¡{self.clients[winner][1]} ha ganado!')

    def broadcast(self, message):
        # FIX: añadir \n como delimitador de mensaje TCP
        message_str = json.dumps(message) + '\n'
        for client_socket, _, _ in self.clients:
            try:
                client_socket.send(message_str.encode('utf-8'))
            except:
                pass


if __name__ == '__main__':
    server = GameServer()
    server.start()
