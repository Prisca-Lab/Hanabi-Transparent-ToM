import os
from openai import OpenAI

from utility_functions import getP1AndP2Cards
from utility_functions import load_env_file, use_db


def load_system_prompt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Errore: Il file '{file_path}' non è stato trovato.")


def interpret_move(move, hand):
    """
    Interpreta il valore di 'move' e restituisce l'azione corrispondente.

    Parametri:
    - move: stringa che descrive l'azione.
    - hand: lista delle carte nella mano del giocatore, come 'R1', 'R2', 'R3', 'R4', 'R5', 'Y1', 'Y2', 'Y3', 'Y4', 'Y5'.

    Ritorna:
    - Stringa che descrive l'azione eseguita.
    """
    colors = {'R': 'Red', 'Y': 'Yellow'}
    ranks = {'1': '1', '2': '2', '3': '3', '4': '4', '5': '5'}

    if "Play" in move:
        index = int(move.split()[1])
        card = hand[index]
        color = colors[card[0]]
        rank = ranks[card[1]]
        return f"Play {color} {rank}"

    elif "Discard" in move:
        index = int(move.split()[1])
        card = hand[index]
        color = colors[card[0]]
        rank = ranks[card[1]]
        return f"Discard {color} {rank}"

    elif "rank" in move:
        rank = move.split()[-1]
        return f"Hint Rank {rank}"

    elif "color" in move:
        color = move.split()[-1]
        return f"Hint Colour {colors[color]}"

    else:
        return "Unknown move"


class Explainer:
    def __init__(self, explainerChoice, approachChoice, hcicModels):
        # Carica le variabili dal file .env
        load_env_file('properties.env')

        self.hcicModels = hcicModels

        self.chatgptApiKey = os.getenv('OPENAI_API_KEY')
        if not self.chatgptApiKey:
            raise ValueError("OPENAI_API_KEY non trovata nell'ambiente")

        self.client = OpenAI(
            api_key=self.chatgptApiKey,
        )

        self.approachChoice = approachChoice

        if approachChoice == 'logic-based':
            if explainerChoice == 'low-level':
                system_prompt_file = 'prompt_logic_based-low-level.txt'
            else:
                system_prompt_file = 'prompt_logic_based-high-level.txt'

            try:
                file_path = 'hanabiKbMoves/play.txt'
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.kbPlayAction = file.read().strip()

                file_path = 'hanabiKbMoves/discard.txt'
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.kbDiscardAction = file.read().strip()

                file_path = 'hanabiKbMoves/hintRank.txt'
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.kbHintRankAction = file.read().strip()

                file_path = 'hanabiKbMoves/hintColor.txt'
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.kbHintColorAction = file.read().strip()

            except FileNotFoundError:
                print(f"Errore: Il file '{file_path}' non è stato trovato.")
        else:
            if explainerChoice == 'high-level':
                system_prompt_file = 'prompt_decision_trees-low-level.txt'
            else:
                system_prompt_file = 'prompt_decision_trees-high-level.txt'

        self.system_prompt = load_system_prompt(system_prompt_file)

    def ask_chatgpt(self, db, currPlayer, state, obs_vectors, move):
        message, newSystemPrompt, decision = self.process_input_data(db, currPlayer, state, obs_vectors, move)
        message = "PARLA ITALIANO e non stilare liste o elenchi quando parli. " + \
                  "Parla come se parlassi al giocatore che ha ricevuto l'indizio che vuole capire perché hai fatto quella azione. L'input è il seguente:\n\n" + \
                  message + "\n\nSpiegami perché hai deciso di fare l'azione " + decision + "."

        chat = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": newSystemPrompt},
                      {"role": "user", "content": message}],
            max_tokens=50
        )

        reply = chat.choices[0].message.content
        print(f"ChatGPT: {reply}")
        return reply

    def process_input_data(self, db, currPlayer, state, obs_vectors, move):
        """
        Esempio di input da costruire:
        - Fireworks: Red 1, Yellow 3
        - Remaining information tokens: 2
        - Remaining fuse tokens: 3
        - Remaining deck size: 8
        - Decision: Hint Rank 3
        Se è un hint la Decision:
           - Actual hint-receiving player cards: ['R1', 'Y3', 'Y3', 'R2', 'R3']
        Se logic-based:
           - knows_at() values: ...50 fatti estratti dalla query db...
        Se decision-trees:
           - P1 Cards from HCIC: ...carte estratte da HCIC...
           - P2 Cards from HCIC: ...carte estratte da HCIC...
        """
        fireworks = 'Red ' + str(state.fireworks()[0] + 1) + ', Yellow ' + str(state.fireworks()[1] + 1)
        remainingInfoTokens = state.information_tokens()
        remainingFuseTokens = state.life_tokens()
        remainingDeckSize = state.deck_size()

        if currPlayer == 0:
            actualOtherPlayerCards = str(state.player_hands()[1])
            actualPlayerCards = [str(card) for card in state.player_hands()[0]]
        else:
            actualOtherPlayerCards = str(state.player_hands()[0])
            actualPlayerCards = [str(card) for card in state.player_hands()[1]]

        decision = interpret_move(move[1:-1], actualPlayerCards)

        if self.approachChoice == 'logic-based':
            actionPrompt = self.getAction(move)
            newSystemPrompt = self.system_prompt + '\n\n' + actionPrompt

            isPlay = 'Play' in move
            isDiscard = 'Discard' in move

            if isPlay or isDiscard:
                if currPlayer == 0:
                    knows_at_values = use_db(db, "query(knows_at(a, (a,_,_))).", True)
                else:
                    knows_at_values = use_db(db, "query(knows_at(b, (b,_,_))).", True)

                return f"""
                   - Fireworks: {fireworks}
                   - Remaining information tokens: {remainingInfoTokens}
                   - Remaining fuse tokens: {remainingFuseTokens}
                   - Remaining deck size: {remainingDeckSize}
                   - Decision: {decision}
                   - knows_at() values: {knows_at_values}
                   """, newSystemPrompt, decision
            else:
                if currPlayer == 0:
                    knows_at_values = use_db(db, "query(knows_at(b, (b,_,_))).", True)
                else:
                    knows_at_values = use_db(db, "query(knows_at(a, (a,_,_))).", True)

                return f"""
                   - Fireworks: {fireworks}
                   - Remaining information tokens: {remainingInfoTokens}
                   - Remaining fuse tokens: {remainingFuseTokens}
                   - Remaining deck size: {remainingDeckSize}
                   - Decision: {decision}
                   - Actual hint-receiving player cards: {actualOtherPlayerCards}
                   - knows_at() values: {knows_at_values}
                   """, newSystemPrompt, decision
        else:
            p0_cards, p1_cards = getP1AndP2Cards(self.hcicModels, obs_vectors)
            # In questo caso non c'è la KB logica, quindi il prompt non subisce modifiche
            newSystemPrompt = self.system_prompt

            return f"""
               - Fireworks: {fireworks}
               - Remaining information tokens: {remainingInfoTokens}
               - Remaining fuse tokens: {remainingFuseTokens}
               - Remaining deck size: {remainingDeckSize}
               - Decision: {decision}
               - P1 Cards from HCIC: {str(p0_cards)}
               - P2 Cards from HCIC: {str(p1_cards)}
               - Actual P2 cards: {actualOtherPlayerCards}
               """, newSystemPrompt, decision

    def getAction(self, move):
        isPlay = 'Play' in move
        isDiscard = 'Discard' in move
        isHintRank = 'rank' in move
        isHintColor = 'color' in move

        if isHintRank:
            return self.kbHintRankAction
        elif isHintColor:
            return self.kbHintColorAction
        elif isDiscard:
            return self.kbDiscardAction
        elif isPlay:
            return self.kbPlayAction
        else:
            raise ValueError("Azione sconosciuta: " + move)
