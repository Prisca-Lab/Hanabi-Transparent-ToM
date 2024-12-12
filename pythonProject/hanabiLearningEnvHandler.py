#  Teniamo in piedi due giochi, qui diamo le carte ecc... e le comunichiamo al client frontend;
#  poi, però, frontend e HanabiLearnEnv viaggeranno in parallelo ma separatamente. Questo semplicemente
#  comunicando le azioni fatte dai giocatori man mano (il client lo dice al backend e HLE replica).
#  In questo modo avremo le osservazioni sempre pronte per HCIC.
#  Lo schema comunicativo è il seguente:
#    (1) HLE dice al client le carte dei due giocatori
#    (2) Client interpreta le prime 5 carte per G1 e dice G1 è l'utente e G2 me le dai tu backend le azioni
#        Nota: G1 gioca sempre per primo, sarebbe player 0 in HLE.
#    (3) Client legge azione G1, aggiorna il gioco frontend e comunica l'azione al backend, e si mette in attesa
#    (4) Backend riceve azione G1, la replica in HLE, poi invoca modello ToM e prende l'azione per G2, la esegue
#        in HLE e poi la comunica al client, che la replica a sua volta, e poi si ritorna al passo (3), fino a game end.
#  Nota: il discorso cambia leggermente in caso di tom-tom, in cui invece il backend comunica sempre lui le azioni.
#  Nota 2: se si usa ProbLog si sincronizza HLE anche con la Knowledge Base.

from __future__ import print_function

import os
from time import sleep

import requests
from hanabi_learning_environment import pyhanabi

from furHatHandler import FurhatController
from logicBasedHandler import LogicBasedHandler
from decisionTreesHandler import DecisionTreesHandler
from utility_functions import load_env_file
from chatgptExplainer import Explainer

""" NOTA: per far funzionare il server backend su Linux, aprire un terminale e digitare in ordine:
   1. sudo apt install nodejs
   2. sudo apt-get install nodejs-dev node-gyp libssl1.0-dev
   3. sudo apt-get install npm
   4. npm install express
   5. npm install body-parser
"""


# Dato state.player_hands() (ossia player hands), metto le carte loro (prima G1 e poi G2) nel deck.
# Poi, le altre carte non posso recuperarle purtroppo dal deck dell'HLE; quindi, a ogni giro, se si fa play o discard,
# nel client si fa la fetch delle carte reali dei giocatori e le si aggiornano. Per cui qui metto le prime 10 carte,
# poi metto altre 10 carte finte.
def getDeckEncoding(playerHands):
    """ Deck must be as follows:
    new_custom_deck = [
        {"color": 'red', "number": 1, "impossible": {}},
        {"color": 'yellow', "number": 3, "impossible": {}},
        {"color": 'yellow', "number": 3, "impossible": {}},
        {"color": 'red', "number": 2, "impossible": {}},
        {"color": 'yellow', "number": 1, "impossible": {}},

        {"color": 'yellow', "number": 2, "impossible": {}},
        {"color": 'red', "number": 3, "impossible": {}},
        {"color": 'yellow', "number": 1, "impossible": {}},
        {"color": 'yellow', "number": 4, "impossible": {}},
        {"color": 'yellow', "number": 5, "impossible": {}},

        {"color": 'red', "number": 1, "impossible": {}},
        {"color": 'red', "number": 1, "impossible": {}},
        {"color": 'red', "number": 2, "impossible": {}},
        {"color": 'red', "number": 3, "impossible": {}},
        {"color": 'red', "number": 4, "impossible": {}},
        {"color": 'red', "number": 4, "impossible": {}},
        {"color": 'red', "number": 5, "impossible": {}},
        {"color": 'yellow', "number": 1, "impossible": {}},
        {"color": 'yellow', "number": 2, "impossible": {}},
        {"color": 'yellow', "number": 4, "impossible": {}}
    ]
    """
    deck = []
    for hand in playerHands:
        for card in hand:
            color = 'red' if str(card)[0] == 'R' else 'yellow'
            number = int(str(card)[1])
            deck.append({"color": color, "number": number, "impossible": {}})

    # Add dummy records if the deck has less than 20 items
    dummy_cards = [
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'yellow', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}},
        {"color": 'red', "number": 0, "impossible": {}}
    ]

    while len(deck) < 20:
        deck.append(dummy_cards[len(deck) % len(dummy_cards)])

    return deck


def convert_cards_to_server_format(cards):
    converted_cards = []
    for player_cards in cards:
        converted_player_cards = []
        for card in player_cards:
            color = str(card)[0]  # assuming R = red, Y = yellow
            if color == 'Y':
                color = 'yellow'
            else:
                color = 'red'

            number = int(str(card)[1:])  # extract the number part and convert to integer
            converted_card = {
                'color': color,
                'number': number,
                'impossible': {}
            }
            converted_player_cards.append(converted_card)
        converted_cards.append(converted_player_cards)
    return converted_cards


def convert_move_to_server_format(move):
    """
       Possibili 'move' nella lista 'legal_moves':
           (Play 0)
           (Play 1)
           (Play 2)
           (Play 3)
           (Play 4)
           (Discard 0)
           (Discard 1)
           (Discard 2)
           (Discard 3)
           (Discard 4)
           (Reveal player +1 rank 1) (ignora l'offset +1)
           (Reveal player +1 rank 2)
           (Reveal player +1 rank 3)
           (Reveal player +1 rank 4)
           (Reveal player +1 rank 5)
           (Reveal player +1 color R)
           (Reveal player +1 color Y)
    """
    move = move[1:-1]  # Rimozione delle parentesi tonde dalla mossa
    last_action = {}
    move_parts = move.split()

    action = move_parts[0]

    if action == "Play":
        index = move_parts[1]
        last_action = {
            "instructionType": "play-card",
            "info": str(index)
        }
    elif action == "Discard":
        index = move_parts[1]
        last_action = {
            "instructionType": "discard-card",
            "info": str(index)
        }
    elif action == "Reveal":
        reveal_type = move_parts[3]
        if reveal_type == "rank":
            number = move_parts[4]
            last_action = {
                "instructionType": "tell-number",
                "info": str(number)
            }
        elif reveal_type == "color":
            color = "red" if move_parts[4] == "R" else "yellow"
            last_action = {
                "instructionType": "tell-color",
                "info": color
            }

    return last_action


def convert_move_from_server_format(move, legal_moves):
    instruction_type = move.get('instructionType')
    info = move.get('info')

    # Determine the move string to match against legal_moves
    if instruction_type == 'tell-color':
        move_str = f'(Reveal player +1 color {info[0].upper()})'
    elif instruction_type == 'tell-number':
        move_str = f'(Reveal player +1 rank {info})'
    elif instruction_type == 'play-card':
        move_str = f'(Play {info})'
    elif instruction_type == 'discard-card':
        move_str = f'(Discard {info})'
    else:
        print(f"Errore: Tipo di istruzione non riconosciuto '{instruction_type}'")
        return None

    # Cerca l'indice del movimento corrispondente nei legal_moves
    move_index = None
    for i, legal_move in enumerate(legal_moves):
        if str(legal_move) == move_str:
            move_index = i
            break

    if move_index is None:
        print(f"Errore: azione '{move_str}' non trovata in legal_moves")
        return None

    return legal_moves[move_index]


def print_state(state):
    """Print some basic information about the state."""
    print("\nCurrent player: {}".format(state.cur_player()))
    print(state)

    # Example of more queries to provide more about this state. For
    # example, bots could use these methods to get information
    # about the state in order to act accordingly.
    print("### Information about the state retrieved separately ###")
    print("### Information tokens: {}".format(state.information_tokens()))
    print("### Life tokens: {}".format(state.life_tokens()))
    print("### Fireworks: {}".format(state.fireworks()))
    print("### Deck size: {}".format(state.deck_size()))
    print("### Discard pile: {}".format(str(state.discard_pile())))
    print("### Player hands: {}".format(str(state.player_hands())))
    print("")


def print_observation(observation):
    """Print some basic information about an agent observation."""
    print("--- Observation ---")
    print(observation)

    print("### Information about the observation retrieved separately ###")
    print("### Current player, relative to self: {}".format(
        observation.cur_player_offset()))
    print("### Observed hands: {}".format(observation.observed_hands()))
    print("### Card knowledge: {}".format(observation.card_knowledge()))
    print("### Discard pile: {}".format(observation.discard_pile()))
    print("### Fireworks: {}".format(observation.fireworks()))
    print("### Deck size: {}".format(observation.deck_size()))
    move_string = "### Last moves:"
    for move_tuple in observation.last_moves():
        move_string += " {}".format(move_tuple)
    print(move_string)
    print("### Information tokens: {}".format(observation.information_tokens()))
    print("### Life tokens: {}".format(observation.life_tokens()))
    print("### Legal moves: {}".format(observation.legal_moves()))
    print("--- EndObservation ---")


def print_encoded_observations(encoder, state, num_players):
    print("--- EncodedObservations ---")
    print("Observation encoding shape: {}".format(encoder.shape()))
    print("Current actual player: {}".format(state.cur_player()))
    for i in range(num_players):
        print("Encoded observation for player {}: {}".format(
            i, encoder.encode(state.observation(i))))
    print("--- EndEncodedObservations ---")


class HanabiHandler:
    def __init__(self, explainerChoiceToM1, explainerChoiceToM2, approachChoice, approachChoiceToM1, approachChoiceToM2,
                 gameChoice, decisionTreesModels, hcicModels):
        # Check that the cdef and pyhanabi library were loaded from the standard paths.
        assert pyhanabi.cdef_loaded(), "cdef failed to load"
        assert pyhanabi.lib_loaded(), "lib failed to load"

        self.gameChoice = gameChoice

        # Load environment variables
        load_env_file('properties.env')

        # Let's start by loading the first furhat IP for the explainer
        first_furhat_ip = os.getenv('FIRST_FURHAT_IP')
        if not first_furhat_ip:
            raise ValueError("FIRST_FURHAT_IP not found in environment variables.")
        self.first_furhat = FurhatController(first_furhat_ip, gameChoice, 'Carla')
        self.first_furhat.connect()

        # If the game choice is such that we need to play with two furhats, then we also load the second furhat IP
        if gameChoice == "ToM":
            second_furhat_ip = os.getenv('SECOND_FURHAT_IP')
            if not second_furhat_ip:
                raise ValueError("SECOND_FURHAT_IP not found in environment variables.")
            # if first_furhat_ip == second_furhat_ip:
            #    raise ValueError("FIRST_FURHAT_IP and SECOND_FURHAT_IP cannot be the same address.")

            self.second_furhat = FurhatController(second_furhat_ip, gameChoice, 'Bianca-Neural')
            self.second_furhat.connect()

        backend_ip = os.getenv('BACKEND_HOST_IP')
        backend_port = os.getenv('BACKEND_HOST_PORT')
        if not backend_ip or not backend_port:
            raise ValueError("BACKEND_HOST_IP or BACKEND_HOST_PORT not found in environment variables.")

        # URL of Node.js server where backend is in execution
        self.base_url = 'http://' + backend_ip + ':' + backend_port

        if gameChoice == "ToM_Human":
            self.explainer = Explainer(explainerChoiceToM1, approachChoice, hcicModels)

            if approachChoice == "decision-trees":
                self.dec_tree_handler = DecisionTreesHandler(decisionTreesModels, hcicModels)
                self.startDecTreesPlay()
            else:
                self.logic_based_handler = LogicBasedHandler(hcicModels)
                self.startLogicBasedPlay()
        else:
            self.explainerToM1 = Explainer(explainerChoiceToM1, approachChoiceToM1, hcicModels)
            self.explainerToM2 = Explainer(explainerChoiceToM2, approachChoiceToM2, hcicModels)
            if approachChoiceToM1 == approachChoiceToM2:
                if approachChoiceToM1 == "decision-trees":
                    self.dec_tree_handler = DecisionTreesHandler(decisionTreesModels, hcicModels)
                    self.startDecTreesPlay()
                else:
                    self.logic_based_handler = LogicBasedHandler(hcicModels)
                    self.startLogicBasedPlay()
            else:
                self.approachChoiceToM1 = approachChoiceToM1
                self.approachChoiceToM2 = approachChoiceToM2
                self.dec_tree_handler = DecisionTreesHandler(decisionTreesModels, hcicModels)
                self.logic_based_handler = LogicBasedHandler(hcicModels)
                self.startHybridPlay()

    def startDecTreesPlay(self):
        self.run_game_dec_trees({"players": 2,
                                 "random_start_player": False,  # Parte sempre il giocatore 0
                                 "max_information_tokens": 5,
                                 "max_life_tokens": 3,
                                 "hand_size": 5,
                                 "ranks": 5,
                                 "colors": 2,
                                 "observation_type": 1})  # 1 = kCardKnowledge, conoscenza standard tradizionale

    def startLogicBasedPlay(self):
        self.run_game_logic_based({"players": 2,
                                   "random_start_player": False,
                                   "max_information_tokens": 5,
                                   "max_life_tokens": 3,
                                   "hand_size": 5,
                                   "ranks": 5,
                                   "colors": 2,
                                   "observation_type": 1})

    def startHybridPlay(self):
        self.run_hybrid_game({"players": 2,
                              "random_start_player": False,
                              "max_information_tokens": 5,
                              "max_life_tokens": 3,
                              "hand_size": 5,
                              "ranks": 5,
                              "colors": 2,
                              "observation_type": 1})

    def initClientGameCards(self, playerHands):
        set_custom_deck_url = self.base_url + '/set_custom_deck'
        deck = getDeckEncoding(playerHands)

        # Invia la richiesta POST con il nuovo mazzo personalizzato
        response = requests.post(set_custom_deck_url, json=deck)

        # Verifica della risposta del server
        if response.status_code == 200:
            print("Mazzo personalizzato impostato con successo!")
        else:
            # self.backendServerProcess.terminate()
            raise ConnectionError(f"Errore durante l'impostazione del mazzo personalizzato: "
                                  f"{response.status_code} - {response.text}")

    # Funzione per aggiornare le carte nel backend che poi le darà al frontend ogni volta che occorre
    def sendPlayersCards(self, currPlayer, cards):
        set_cards_url = self.base_url + '/set_cards'

        cards = convert_cards_to_server_format(cards)

        cards = {
            'p1cards': cards[0],
            'p2cards': cards[1],
            'currPlayer': currPlayer
        }

        # Invia la richiesta POST con il nuovo mazzo personalizzato
        response = requests.post(set_cards_url, json=cards)

        # Verifica della risposta del server
        if response.status_code == 200:
            print("Carte dei giocatori inviate al server con successo!")
        else:
            # self.backendServerProcess.terminate()
            raise ConnectionError(f"Errore durante l'aggiornamento delle carte dei giocatori al server: "
                                  f"{response.status_code} - {response.text}")

    def sendMove(self, currPlayer, move, gameChoice):
        print('Sono il backend e ora invio la mossa: ', move, 'al giocatore ', currPlayer)

        if gameChoice == "ToM":
            set_move_url = self.base_url + '/set_last_action_tom'
        else:
            set_move_url = self.base_url + '/set_last_action'

        # Converti la mossa nel formato richiesto dal server
        move = convert_move_to_server_format(move)

        # Aggiungi il giocatore corrente alla mossa
        payload = {
            'player': currPlayer,
            'action': move
        }

        # Invia la richiesta POST con la mossa intrapresa
        response = requests.post(set_move_url, json=payload)

        # Verifica della risposta del server
        if response.status_code == 200:
            print("Azione inviata al server con successo!")
        else:
            raise ConnectionError(f"Errore durante l'aggiornamento dell'azione al server: "
                                  f"{response.status_code} - {response.text}")

    def waitForBoardToBeReady(self):
        wait_url = self.base_url + '/wait_for_board'
        response = requests.get(wait_url, timeout=None)  # Remove timeout to wait indefinitely

        # Verifica che la richiesta sia andata a buon fine
        if response.status_code == 204:
            print('Board è pronta!')
        else:
            print(f"Errore nella richiesta: {response.status_code}")
            raise ConnectionError(f"Errore durante l'aggiornamento dell'azione al server: "
                                  f"{response.status_code} - {response.text}")

    # Nota: la parte di attesa è già implementata nel server, questa funzione va in pausa quando fa la get
    def getMove(self, otherPlayer, legal_moves):
        get_move_url = self.base_url + '/get_last_action'

        # Definisci i parametri della query
        params = {'player': otherPlayer}

        # Invia la richiesta GET per recuperare la mossa intrapresa
        response = requests.get(get_move_url, params=params)

        # Verifica che la richiesta sia andata a buon fine
        if response.status_code == 200:
            # Ottieni i dati in formato JSON
            data = response.json()
            print('ok in python ora data = ', str(data))
            return convert_move_from_server_format(data, legal_moves)
        else:
            print(f"Errore nella richiesta: {response.status_code}")
            raise ConnectionError(f"Errore durante l'aggiornamento dell'azione al server: "
                                  f"{response.status_code} - {response.text}")

    def run_game_dec_trees(self, game_parameters):
        game = pyhanabi.HanabiGame(game_parameters)
        print(game.parameter_string(), end="")
        obs_encoder = pyhanabi.ObservationEncoder(
            game, enc_type=pyhanabi.ObservationEncoderType.CANONICAL)

        move_str = ""
        currPlayer = -1
        state = game.new_initial_state()
        deck_initialized = False
        boardIsReady = False
        encoded_players_obs = []

        while not state.is_terminal():
            # While all players didn't receive yet all the cards...
            if state.cur_player() == pyhanabi.CHANCE_PLAYER_ID:
                state.deal_random_card()
                continue

            if move_str.startswith("(Play") or move_str.startswith("(Discard"):
                # La mossa è di tipo Play o Discard. Devo aggiornare le carte al server backend.
                print("La mossa fatta è ", move_str)
                print("Sto per chiamare sendPlayersCards con state.player_hands() = ", state.player_hands())
                self.sendPlayersCards(currPlayer, state.player_hands())

            if not deck_initialized:
                self.initClientGameCards(state.player_hands())
                deck_initialized = True

            print_state(state)

            observation = state.observation(state.cur_player())
            print_observation(observation)
            print_encoded_observations(obs_encoder, state, game.num_players())

            legal_moves = state.legal_moves()
            print("\nNumber of legal moves: {}".format(len(legal_moves)))

            currPlayer = state.cur_player()
            gameState = {}

            # Verifichiamo se davvero ci occorre prepararci per fare una predizione
            if (self.gameChoice == "ToM_Human" and currPlayer == 1) or self.gameChoice == "ToM":
                encoded_players_obs = []
                encoded_player0_obs = obs_encoder.encode(state.observation(0))
                encoded_player1_obs = obs_encoder.encode(state.observation(1))

                discard_pile = str([str(card) for card in state.discard_pile()])

                if self.gameChoice == "ToM_Human":
                    # Allora l'altro giocatore è il giocatore 0 e io sono 1
                    encoded_players_obs.append(encoded_player1_obs)  # P1 Cards, me stesso
                    encoded_players_obs.append(encoded_player0_obs)  # P2 Cards, l'altro giocatore
                    otherPlayerIdx = 0
                else:  # self.gameChoice == "ToM"
                    # Allora l'altro giocatore può essere sia 0 che 1, dipende dal current player
                    if currPlayer == 0:
                        otherPlayerIdx = 1
                        encoded_players_obs.append(encoded_player0_obs)  # P1 Cards, me stesso
                        encoded_players_obs.append(encoded_player1_obs)  # P2 Cards, l'altro giocatore
                    else:  # currPlayer == 1
                        otherPlayerIdx = 0
                        encoded_players_obs.append(encoded_player1_obs)  # P1 Cards, me stesso
                        encoded_players_obs.append(encoded_player0_obs)  # P2 Cards, l'altro giocatore

                actual_other_player_cards = str([str(card) for card in state.player_hands()[otherPlayerIdx]])

                gameState = {
                    'observation_vectors': encoded_players_obs,
                    'Actual P2 Cards': actual_other_player_cards,
                    'Fireworks': str({'R': state.fireworks()[0] + 1, 'Y': state.fireworks()[1] + 1}),
                    'Remaining info tokens': state.information_tokens(),
                    'Remaining life tokens': state.life_tokens(),
                    'Discarded pile': discard_pile,
                    'Deck size': state.deck_size(),
                    'Legal actions': legal_moves
                }

            if not boardIsReady:
                self.waitForBoardToBeReady()
                boardIsReady = True

            # Adesso da qui è possibile procedere con furhat dando le spiegazioni

            if self.gameChoice == "ToM":
                sleep(1)
                move = self.dec_tree_handler.selectBestAction(gameState)

                if currPlayer == 0:
                    explanation = self.explainerToM1.ask_chatgpt(None, currPlayer, state, encoded_players_obs, str(move))
                    self.first_furhat.say_something(explanation)
                else:
                    explanation = self.explainerToM2.ask_chatgpt(None, currPlayer, state, encoded_players_obs, str(move))
                    self.second_furhat.say_something(explanation)

                print("Chose legal move: {}".format(move))

                # Comunico l'azione intrapresa al server
                self.sendMove(currPlayer, str(move), self.gameChoice)
            else:  # self.gameChoice == "ToM_Human"
                # L'id 0 è l'id del giocatore umano, quindi non devo fare la scelta dell'azione bensì devo
                # mettermi in attesa sul server fino a quando non ricevo l'azione
                if currPlayer == 0:
                    move = self.getMove(0, legal_moves)
                    assert (move is not None)
                else:  # Allora devo fare io la scelta e comunicarla al server
                    move = self.dec_tree_handler.selectBestAction(gameState)
                    explanation = self.explainer.ask_chatgpt(None, currPlayer, state, encoded_players_obs, str(move))
                    self.first_furhat.say_something(explanation)

                    print("Chose legal move: {}".format(move))

                    # Comunico l'azione intrapresa al server
                    self.sendMove(currPlayer, str(move), self.gameChoice)

            print("move done by player " + str(state.cur_player()) + ": ", move)
            state.apply_move(move)

            move_str = str(move)

            if state.is_terminal():
                if move_str.startswith("(Play") or move_str.startswith("(Discard"):
                    # La mossa è di tipo Play o Discard. Devo aggiornare le carte al server backend.
                    print("La mossa fatta è ", move_str)
                    print("Sto per chiamare sendPlayersCards con state.player_hands(); player hands: ",
                          state.player_hands())
                    self.sendPlayersCards(currPlayer, state.player_hands())

        print("\nGame done. Terminal state:\n")
        print(state)
        print("\nScore (automatically 0 if all fuse tokens were used): {}".format(state.score()))

    def run_game_logic_based(self, game_parameters):
        game = pyhanabi.HanabiGame(game_parameters)
        print(game.parameter_string(), end="")
        obs_encoder = pyhanabi.ObservationEncoder(
            game, enc_type=pyhanabi.ObservationEncoderType.CANONICAL)

        move_str = ""
        currPlayer = -1
        state = game.new_initial_state()
        deck_initialized = False
        boardIsReady = False
        encoded_players_obs = None
        encoded_players_obs = []

        while not state.is_terminal():
            # While all players didn't receive yet all the cards...
            if state.cur_player() == pyhanabi.CHANCE_PLAYER_ID:
                state.deal_random_card()
                continue

            if move_str.startswith("(Play") or move_str.startswith("(Discard"):
                # La mossa è di tipo Play o Discard. Devo aggiornare le carte al server backend.
                print("La mossa fatta è ", move_str)
                print("Sto per chiamare sendPlayersCards con state.player_hands() = ", state.player_hands())
                self.sendPlayersCards(currPlayer, state.player_hands())

            if move_str != "":
                # Aggiorna la KB con l'azione eseguita dal giocatore corrente
                # Questo viene fatto qui perché bisogna che le carte dei giocatori siano aggiornate
                self.logic_based_handler.setKnowledgeBasePlayersMove(
                    currPlayer, move_str, state.player_hands(), encoded_players_obs)

            if not deck_initialized:
                self.initClientGameCards(state.player_hands())
                deck_initialized = True
                encoded_players_obs = [obs_encoder.encode(state.observation(0)),
                                       obs_encoder.encode(state.observation(1))]
                self.logic_based_handler.setUpKnowledgeBaseInitState(state, encoded_players_obs)

            print_state(state)

            observation = state.observation(state.cur_player())
            print_observation(observation)
            print_encoded_observations(obs_encoder, state, game.num_players())

            legal_moves = state.legal_moves()
            print("\nNumber of legal moves: {}".format(len(legal_moves)))

            currPlayer = state.cur_player()

            # encoded_players_obs = [obs_encoder.encode(state.observation(0)),
            #                        obs_encoder.encode(state.observation(1))]

            gameState = {
                'Current Player': currPlayer,
                'Legal actions': legal_moves
            }

            if not boardIsReady:
                self.waitForBoardToBeReady()
                boardIsReady = True

            # Adesso da qui è possibile procedere con furhat dando le spiegazioni

            if self.gameChoice == "ToM":
                # sleep(1)
                move = self.logic_based_handler.selectBestAction(gameState)

                if currPlayer == 0:
                    explanation = self.explainerToM1.ask_chatgpt(self.logic_based_handler.getDb(), currPlayer, state,
                                                                 encoded_players_obs, str(move))
                    self.first_furhat.say_something(explanation)
                else:
                    explanation = self.explainerToM2.ask_chatgpt(self.logic_based_handler.getDb(), currPlayer, state,
                                                                 encoded_players_obs, str(move))
                    self.second_furhat.say_something(explanation)

                print("Chose legal move: {}".format(move))

                # Comunico l'azione intrapresa al server
                self.sendMove(currPlayer, str(move), self.gameChoice)
            else:  # self.gameChoice == "ToM_Human"
                # L'id 0 è l'id del giocatore umano, quindi non devo fare la scelta dell'azione bensì devo
                # mettermi in attesa sul server fino a quando non ricevo l'azione
                if currPlayer == 0:
                    move = self.getMove(0, legal_moves)
                    assert (move is not None)
                else:  # Allora devo fare io la scelta e comunicarla al server
                    move = self.logic_based_handler.selectBestAction(gameState)
                    explanation = self.explainer.ask_chatgpt(self.logic_based_handler.getDb(), currPlayer, state, encoded_players_obs, str(move))
                    self.first_furhat.say_something(explanation)

                    print("Chose legal move: {}".format(move))

                    # Comunico l'azione intrapresa al server
                    self.sendMove(currPlayer, str(move), self.gameChoice)

            print("move done by player " + str(state.cur_player()) + ": ", move)
            state.apply_move(move)

            move_str = str(move)

            # Ricalcoliamo encoded_players_obs
            encoded_players_obs = [obs_encoder.encode(state.observation(0)),
                                   obs_encoder.encode(state.observation(1))]

            if state.is_terminal():
                if move_str.startswith("(Play") or move_str.startswith("(Discard"):
                    # La mossa è di tipo Play o Discard. Devo aggiornare le carte al server backend.
                    print("La mossa fatta è ", move_str)
                    print("Sto per chiamare sendPlayersCards con state.player_hands(); player hands: ",
                          state.player_hands())
                    self.sendPlayersCards(currPlayer, state.player_hands())

        print("\nGame done. Terminal state:\n")
        print(state)
        print("\nScore (automatically 0 if all fuse tokens were used): {}".format(state.score()))

    def run_hybrid_game(self, game_parameters):
        game = pyhanabi.HanabiGame(game_parameters)
        print(game.parameter_string(), end="")
        obs_encoder = pyhanabi.ObservationEncoder(
            game, enc_type=pyhanabi.ObservationEncoderType.CANONICAL)

        move_str = ""
        currPlayer = -1
        state = game.new_initial_state()
        deck_initialized = False
        boardIsReady = False
        encoded_players_obs = None

        while not state.is_terminal():
            # While all players didn't receive yet all the cards...
            if state.cur_player() == pyhanabi.CHANCE_PLAYER_ID:
                state.deal_random_card()
                continue

            if move_str.startswith("(Play") or move_str.startswith("(Discard"):
                # La mossa è di tipo Play o Discard. Devo aggiornare le carte al server backend.
                print("La mossa fatta è ", move_str)
                print("Sto per chiamare sendPlayersCards con state.player_hands() = ", state.player_hands())
                self.sendPlayersCards(currPlayer, state.player_hands())

            if move_str != "":
                # Aggiorna la KB con l'azione eseguita dal giocatore corrente
                # Questo viene fatto qui perché bisogna che le carte dei giocatori siano aggiornate
                self.logic_based_handler.setKnowledgeBasePlayersMove(
                    currPlayer, move_str, state.player_hands(), encoded_players_obs)

            if not deck_initialized:
                self.initClientGameCards(state.player_hands())
                deck_initialized = True
                encoded_players_obs = [obs_encoder.encode(state.observation(0)),
                                       obs_encoder.encode(state.observation(1))]
                self.logic_based_handler.setUpKnowledgeBaseInitState(state, encoded_players_obs)

            print_state(state)

            observation = state.observation(state.cur_player())
            print_observation(observation)
            print_encoded_observations(obs_encoder, state, game.num_players())

            legal_moves = state.legal_moves()
            print("\nNumber of legal moves: {}".format(len(legal_moves)))

            currPlayer = state.cur_player()
            gameState = {}

            # Verifichiamo se davvero ci occorre prepararci per fare una predizione
            if (self.approachChoiceToM1 == "decision-trees" and currPlayer == 0 or
                    self.approachChoiceToM2 == "decision-trees" and currPlayer == 1):  # and self.gameChoice == "ToM":
                encoded_players_obs_ = []
                encoded_player0_obs = obs_encoder.encode(state.observation(0))
                encoded_player1_obs = obs_encoder.encode(state.observation(1))

                discard_pile = str([str(card) for card in state.discard_pile()])

                # Allora l'altro giocatore può essere sia 0 che 1, dipende dal current player
                if currPlayer == 0:
                    otherPlayerIdx = 1
                    encoded_players_obs_.append(encoded_player0_obs)  # P1 Cards, me stesso
                    encoded_players_obs_.append(encoded_player1_obs)  # P2 Cards, l'altro giocatore
                else:  # currPlayer == 1
                    otherPlayerIdx = 0
                    encoded_players_obs_.append(encoded_player1_obs)  # P1 Cards, me stesso
                    encoded_players_obs_.append(encoded_player0_obs)  # P2 Cards, l'altro giocatore

                actual_other_player_cards = str([str(card) for card in state.player_hands()[otherPlayerIdx]])

                gameState = {
                    'observation_vectors': encoded_players_obs_,
                    'Actual P2 Cards': actual_other_player_cards,
                    'Fireworks': str({'R': state.fireworks()[0] + 1, 'Y': state.fireworks()[1] + 1}),
                    'Remaining info tokens': state.information_tokens(),
                    'Remaining life tokens': state.life_tokens(),
                    'Discarded pile': discard_pile,
                    'Deck size': state.deck_size(),
                    'Legal actions': legal_moves
                }

            if not boardIsReady:
                self.waitForBoardToBeReady()
                boardIsReady = True

            # Adesso da qui è possibile procedere con furhat dando le spiegazioni

            if (self.approachChoiceToM1 == "decision-trees" and currPlayer == 0 or
                    self.approachChoiceToM2 == "decision-trees" and currPlayer == 1):  # and self.gameChoice == "ToM":
                sleep(1)
                move = self.dec_tree_handler.selectBestAction(gameState)
            else:
                # sleep(1)
                gameState_logicBased = {
                    'Current Player': currPlayer,
                    'Legal actions': legal_moves
                }
                move = self.logic_based_handler.selectBestAction(gameState_logicBased)

            if self.approachChoiceToM1 == "decision-trees":
                dbToM1 = None
            else:
                dbToM1 = self.logic_based_handler.getDb()

            if self.approachChoiceToM2 == "decision-trees":
                dbToM2 = None
            else:
                dbToM2 = self.logic_based_handler.getDb()

            if currPlayer == 0:
                explanation = self.explainerToM1.ask_chatgpt(dbToM1, currPlayer, state, encoded_players_obs, str(move))
                self.first_furhat.say_something(explanation)
            else:
                explanation = self.explainerToM2.ask_chatgpt(dbToM2, currPlayer, state, encoded_players_obs, str(move))
                self.second_furhat.say_something(explanation)

            print("Chose legal move: {}".format(move))

            # Comunico l'azione intrapresa al server
            self.sendMove(currPlayer, str(move), self.gameChoice)

            print("move done by player " + str(state.cur_player()) + ": ", move)
            state.apply_move(move)

            move_str = str(move)

            # Ricalcoliamo encoded_players_obs, per l'approccio logico
            encoded_players_obs = [obs_encoder.encode(state.observation(0)),
                                   obs_encoder.encode(state.observation(1))]

            if state.is_terminal():
                if move_str.startswith("(Play") or move_str.startswith("(Discard"):
                    # La mossa è di tipo Play o Discard. Devo aggiornare le carte al server backend.
                    print("La mossa fatta è ", move_str)
                    print("Sto per chiamare sendPlayersCards con state.player_hands(); player hands: ",
                          state.player_hands())
                    self.sendPlayersCards(currPlayer, state.player_hands())

        print("\nGame done. Terminal state:\n")
        print(state)
        print("\nScore (automatically 0 if all fuse tokens were used): {}".format(state.score()))
