from utility_functions import extract_cards_from_hcic2
from utility_functions import use_db
from problog.program import PrologFile
from problog.engine import DefaultEngine
import numpy as np

GLOBAL_COUNTER = 20
all_possible_cards = ['red1', 'red2', 'red3', 'red4', 'red5', 'yellow1', 'yellow2', 'yellow3', 'yellow4', 'yellow5']


def convert_cards(cards):
    # Creare un dizionario per mappare i colori delle carte
    color_map = {
        'R': 'red',
        'Y': 'yellow',
    }

    # Convertire le carte utilizzando il dizionario
    converted_cards = [color_map[card[0]] + card[1] for card in cards]

    return converted_cards


class LogicBasedHandler:
    def __init__(self, hcicModels):
        self.hcicModels = hcicModels
        pl_model_sr = PrologFile("hanabi.pl")
        self.db = DefaultEngine().prepare(pl_model_sr)

    def setUpKnowledgeBaseInitState(self, state, encoded_players_obs):
        # Iniziamo a impostare i valori iniziali per knows_at()
        self.setAtAndKnowsAtValues(state.player_hands(), encoded_players_obs)

        # Nota: puoi impostare tutti i fatti iniziali nella KB, tranne deck(). Per quello si
        # usa la strategia di chiedere ogni volta le carte aggiornate.

        # Per i restanti fatti della KB, essi sono già tutti inizializzati

    def getDb(self):
        return self.db

    def setKnowledgeBasePlayersMove(self, player, move, playersCards, encoded_players_obs):
        # Ci occorre playersCards perché non possiamo aggiornare deck() nella KB, dato che l'HLE non ci dà
        # l'info delle carte rimanenti nel deck;

        # Se player = 0, allora considereremo il giocatore 'a' nella KB. Altrimenti, il giocatore 'b'.
        actingPlayer = 'a' if player == 0 else 'b'
        # Se l'azione è un hint, calcoliamoci il potenziale hintedPlayer
        hintedPlayer = 'b' if actingPlayer == 'a' else 'a'

        # Compiamo l'azione 'move', assumendo che provenga da selectBestAction() e pertanto sia legale
        """ Possibili 'move':
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
        isPlay = 'Play' in move
        isDiscard = 'Discard' in move
        isHintRank = 'rank' in move
        isHintColor = 'color' in move

        # Nota: il GLOBAL_COUNTER non serve che sia diverso, basta che sia maggiore del max usato nel file .pl.
        # Per tale motivo, useremo sempre 100000 come esempio di valore massimo.
        if isHintRank:
            hintedRank = move[-2]
            query_extension = ":- hint_rank(" + hintedPlayer + ", " + hintedRank + ", 100000)."
        elif isHintColor:
            hintedColor = 'red' if move[-2] == 'R' else 'yellow'
            query_extension = ":- hint_color(" + hintedPlayer + ", " + hintedColor + ", 100000)."
        elif isDiscard:
            discardedCard = str(int(move[-2]) + 1)  # Nella KB gli indici vanno da 1 a 5, quindi aggiungo +1
            query_extension = ":- discard_card_action(" + actingPlayer + ", " + discardedCard + ", 100000)."
        elif isPlay:
            playedCard = str(int(move[-2]) + 1)
            query_extension = ":- play_card(" + actingPlayer + ", " + playedCard + ", 100000)."
        else:
            raise ValueError("Azione sconosciuta da eseguire nella base di conoscenza: " + move)

        print("Eseguo l'azione", query_extension, "nella Knowledge Base.")
        use_db(self.db, query_extension, print_evaluation=False)

        # Aggiorniamo at() e knows_at()
        self.setAtAndKnowsAtValues(playersCards, encoded_players_obs)

    def selectBestAction(self, gameState):
        currPlayer = gameState['Current Player']
        legalActions = gameState['Legal actions']
        legalActionsStr = [str(move) for move in legalActions]

        # Se currPlayer = 0, allora considereremo il giocatore 'a' nella KB. Altrimenti, il giocatore 'b'.
        actingPlayer = 'a' if currPlayer == 0 else 'b'
        # Se l'azione è un hint, calcoliamoci il potenziale hintedPlayer
        hintedPlayer = 'b' if actingPlayer == 'a' else 'a'

        # Non aggiorniamo knows_at(), non occorre, è già stato fatto per come lo gestisce il chiamante

        # Vediamo in legalActions se ci sono le mosse possibili (eccetto Play, che è sempre concesso), e se una di
        # esse manca, le inferenze per quella categoria di azione non verranno neppure calcolate.
        contains_reveal_rank = any('rank' in action for action in legalActionsStr)
        contains_reveal_color = any('color' in action for action in legalActionsStr)
        contains_discard = any('Discard' in action for action in legalActionsStr)
        # Nota: play è legale ma le carte non giocabili dovresti vedere probabilità 0.0

        # Dizionario che contiene le migliori mosse e le rispettive probabilità
        top_evaluations = {
            'rank_evaluation': None,
            'rank_evaluation_prob': 0.0,
            'color_evaluation': None,
            'color_evaluation_prob': 0.0,
            'discard_evaluation': None,
            'discard_evaluation_prob': 0.0,
            'play_evaluation': None,
            'play_evaluation_prob': 0.0,
        }

        global GLOBAL_COUNTER

        # Verifichiamo qual è il colore migliore da suggerire
        if contains_reveal_color:
            red_evaluation = use_db(self.db, "query(suggest_color_action_prob(" + actingPlayer + ", "
                                    + hintedPlayer + ", red, " + str(GLOBAL_COUNTER) + ")).", True)
            red_evaluation = list(red_evaluation.items())
            red_probability = float(red_evaluation[0][1])

            GLOBAL_COUNTER = GLOBAL_COUNTER + 1

            yellow_evaluation = use_db(self.db, "query(suggest_color_action_prob(" + actingPlayer + ", "
                                       + hintedPlayer + ", yellow, " + str(GLOBAL_COUNTER) + ")).", True)
            yellow_evaluation = list(yellow_evaluation.items())
            yellow_probability = float(yellow_evaluation[0][1])

            GLOBAL_COUNTER = GLOBAL_COUNTER + 1

            top_evaluations['color_evaluation'] = red_evaluation[0][0] \
                if red_probability > yellow_probability else yellow_evaluation[0][0]
            top_evaluations['color_evaluation_prob'] = red_probability \
                if red_probability > yellow_probability else yellow_probability

        # Verifichiamo qual è il rank migliore da suggerire
        if contains_reveal_rank:
            for rank in range(1, 6):
                evaluation = use_db(self.db, "query(suggest_rank_action_prob(" + actingPlayer + ", " + hintedPlayer +
                                    ", " + str(rank) + ", " + str(GLOBAL_COUNTER) + ")).", True)
                evaluation = list(evaluation.items())
                probability = float(evaluation[0][1])
                GLOBAL_COUNTER = GLOBAL_COUNTER + 1

                if probability > top_evaluations['rank_evaluation_prob']:
                    top_evaluations['rank_evaluation'] = evaluation[0][0]
                    top_evaluations['rank_evaluation_prob'] = probability

        # Verifichiamo qual è la carta migliore da scartare
        if contains_discard:
            for discardIndex in range(1, 6):
                evaluation = use_db(self.db, "query(discard_card_action_prob(" + actingPlayer + ", " +
                                    str(discardIndex) + ", " + str(GLOBAL_COUNTER) + ")).", True)
                evaluation = list(evaluation.items())
                probability = float(evaluation[0][1])
                GLOBAL_COUNTER = GLOBAL_COUNTER + 1

                if probability > top_evaluations['discard_evaluation_prob']:
                    top_evaluations['discard_evaluation'] = evaluation[0][0]
                    top_evaluations['discard_evaluation_prob'] = probability

        # Verifichiamo qual è la carta migliore da giocare
        for playIndex in range(1, 6):
            evaluation = use_db(self.db, "query(play_card_action_prob(" + actingPlayer + ", " + str(playIndex) +
                                ", " + str(GLOBAL_COUNTER) + ")).", True)
            evaluation = list(evaluation.items())
            probability = float(evaluation[0][1])
            GLOBAL_COUNTER = GLOBAL_COUNTER + 1

            if probability > top_evaluations['play_evaluation_prob']:
                top_evaluations['play_evaluation'] = evaluation[0][0]
                top_evaluations['play_evaluation_prob'] = probability

        # Confrontiamo le top probabilità per ciascuna delle azioni (se legali) e scegliamo
        # quella che ha più probabilità di essere favorevole
        best_action = None
        best_action_prob = 0.0

        if contains_reveal_rank and top_evaluations['rank_evaluation_prob'] > best_action_prob:
            best_action = top_evaluations['rank_evaluation']
            best_action_prob = top_evaluations['rank_evaluation_prob']

        if contains_reveal_color and top_evaluations['color_evaluation_prob'] > best_action_prob:
            best_action = top_evaluations['color_evaluation']
            best_action_prob = top_evaluations['color_evaluation_prob']

        if contains_discard and top_evaluations['discard_evaluation_prob'] > best_action_prob:
            best_action = top_evaluations['discard_evaluation']
            best_action_prob = top_evaluations['discard_evaluation_prob']

        if top_evaluations['play_evaluation_prob'] > best_action_prob:
            best_action = top_evaluations['play_evaluation']
            best_action_prob = top_evaluations['play_evaluation_prob']

        if 'color' in best_action.functor:
            suggestedColor = 'Y' if str(best_action.args[2]) == 'yellow' else 'R'
            for move in legalActions:
                if 'color ' + suggestedColor in str(move):
                    return move

            raise Exception("Cannot find suggested color; suggestedColor =",
                            suggestedColor, ", legalActions =", legalActionsStr)
        elif 'rank' in best_action.functor:
            suggestedRank = str(best_action.args[2])
            for move in legalActions:
                if 'rank ' + suggestedRank in str(move):
                    return move

            raise Exception("Cannot find suggested rank; suggestedRank =",
                            suggestedRank, ", legalActions =", legalActionsStr)
        elif 'discard' in best_action.functor:
            discardIndex = str(int(best_action.args[1])-1)
            for move in legalActions:
                if 'Discard ' + discardIndex in str(move):
                    return move

            raise Exception("Cannot find suggested discard move; discardIndex =",
                            discardIndex, ", legalActions =", legalActionsStr)
        else:  # 'play' in best_action.functor
            playIndex = str(int(best_action.args[1])-1)

            for move in legalActions:
                if 'Play ' + playIndex in str(move):
                    return move

            raise Exception("Cannot find suggested play move; playIndex =",
                            playIndex, ", legalActions =", legalActionsStr)

    def setAtAndKnowsAtValues(self, playersCards, encoded_players_obs):
        # Cancelliamo tutti gli at()
        use_db(self.db, ":- retractall(at(_,_,_)).", False)
        # Cancelliamo tutti i knows_at()
        use_db(self.db, ":- retractall(knows_at(_,_)).", False)

        p0_cards = convert_cards([str(card) for card in playersCards[0]])
        p1_cards = convert_cards([str(card) for card in playersCards[1]])

        global GLOBAL_COUNTER
        global all_possible_cards

        knows_a = []
        knows_b = []

        # Aggiorniamo at() per il giocatore 0 ossia 'a' nella KB:
        for index, a_card in enumerate(p0_cards):
            use_db(self.db, ":- assertz(at(a, " + str(index + 1) + ", " + a_card + ")).", False)
            knows_b.append("(a, " + str(index + 1) + ", " + a_card + ")")

        print("\nOra le carte del primo giocatore sono diventate le seguenti:")
        use_db(self.db, ":- print_hand(a, " + str(GLOBAL_COUNTER) + ").", False)

        GLOBAL_COUNTER = GLOBAL_COUNTER + 1

        # Aggiorniamo at() per il giocatore 1 ossia 'b' nella KB:
        for index, b_card in enumerate(p1_cards):
            use_db(self.db, ":- assertz(at(b, " + str(index + 1) + ", " + b_card + ")).", False)
            knows_a.append("(b, " + str(index + 1) + ", " + b_card + ")")

        print("\nOra le carte del secondo giocatore sono diventate le seguenti:")
        use_db(self.db, ":- print_hand(b, " + str(GLOBAL_COUNTER) + ").", False)
        print("")

        GLOBAL_COUNTER = GLOBAL_COUNTER + 1

        # Ora impostiamo le probabilità certe per at(), ossia 'a' conosce con certezza le carte di 'b', e viceversa
        # Init 1.0::knows_at(a, (b, ...))
        for tuple_knows_at_a in knows_a:
            knows_at_a_string = ":- assertz((1.0::knows_at(a, " + tuple_knows_at_a + ")))."
            print("Aggiorno " + "assertz((1.0::knows_at(a, " + tuple_knows_at_a + "))).")
            use_db(self.db, knows_at_a_string, False)

        print("------------------")

        # Init 1.0::knows_at(b, (a, ...))
        for tuple_knows_at_b in knows_b:
            knows_at_b_string = ":- assertz((1.0::knows_at(b, " + tuple_knows_at_b + ")))."
            print("Aggiorno " + "assertz((1.0::knows_at(b, " + tuple_knows_at_b + "))).")
            use_db(self.db, knows_at_b_string, False)

        print("------------------")

        use_db(self.db, "query(knows_at(a, (_,_,_))).", True)
        use_db(self.db, "query(knows_at(b, (_,_,_))).", True)

        # Adesso dobbiamo impostare le probabilità incerte di knows_at(), sia per 'a' che per 'b'

        # Iniziamo a recuperare le probabilità delle carte per ciascuno dei 5 indici per P0:
        player0_cards_prob = [None] * 5
        for i in range(0, 5):
            player0_cards_prob[i] = (self.hcicModels['index_' + str(i + 1)].
                                     predict(np.array(encoded_players_obs[0]).reshape(1, -1)))

        player1_cards_prob = [None] * 5
        # Recuperiamo le probabilità delle carte per ciascuno dei 5 indici per P1:
        for i in range(0, 5):
            player1_cards_prob[i] = (self.hcicModels['index_' + str(i + 1)].
                                     predict(np.array(encoded_players_obs[1]).reshape(1, -1)))

        # Usiamo le predizioni appena calcolate per impostare le probabilità per 'knows_at()' nella KB

        # Impostiamo le probabilità per il giocatore 0, ossia il giocatore 'a' nella KB
        print("------------------")
        print("Init probabilità incerte per knows_at(a, (a, ...)")
        for handIndex in range(0, 5):
            for cardIndex, cardProb in enumerate(player0_cards_prob[handIndex][0]):
                card = all_possible_cards[cardIndex]
                # cardProb varia per R1, ..., R5, Y1, ..., Y5 (10 prob., riferite a 10 carte diverse, per handIndex)
                knows_at_string = ":- assertz((" + str(cardProb) + "::knows_at(a, (a, " + str(
                    handIndex + 1) + ", " + card + "))))."
                use_db(self.db, knows_at_string, False)

        print("------------------")
        print("Init probabilità incerte per knows_at(b, (b, ...)")
        for handIndex in range(0, 5):
            for cardIndex, cardProb in enumerate(player1_cards_prob[handIndex][0]):
                card = all_possible_cards[cardIndex]
                # cardProb varia per R1, ..., R5, Y1, ..., Y5 (10 prob., riferite a 10 carte diverse, per handIndex)
                knows_at_string = ":- assertz((" + str(cardProb) + "::knows_at(b, (b, " + str(
                    handIndex) + ", " + card + "))))."
                use_db(self.db, knows_at_string, False)

        # use_db(self.db, "query(knows_at(a, (a,_,_))).", True)
        # use_db(self.db, "query(knows_at(b, (b,_,_))).", True)
