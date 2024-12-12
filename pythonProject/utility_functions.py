import os
import random
import pandas as pd
import numpy as np
from problog.program import PrologString
from problog import get_evaluatable


GLOBAL_COUNTER = 10

all_possible_cards = ['red1', 'red2', 'red3', 'red4', 'red5', 'yellow1', 'yellow2', 'yellow3', 'yellow4', 'yellow5']
deck = ['red1', 'red1', 'red1',
        'red2', 'red2',
        'red3', 'red3',
        'red4', 'red4',
        'red5',
        'yellow1', 'yellow1', 'yellow1',
        'yellow2', 'yellow2',
        'yellow3', 'yellow3',
        'yellow4', 'yellow4',
        'yellow5']
a_cards = []
b_cards = []


def assign_cards():
    global deck, a_cards, b_cards
    random.shuffle(deck)  # Mescola il mazzo
    a_cards = deck[:5]  # Assegna le prime 5 carte ad 'a'
    b_cards = deck[5:10]  # Assegna le carte successive a 'b'
    deck = deck[10:]  # Rimuovi le prime 10 carte da 'Deck'


def give_cards(db):
    global GLOBAL_COUNTER

    assign_cards()

    print("Carte di 'a':", a_cards)
    print("Carte di 'b':", b_cards)
    print("Mazzo rimanente:", deck)

    print("\nPYTHON: retractall(at(_,_,_))")
    use_db(db, ":- retractall(at(_,_,_)).", False)
    print("PYTHON: retractall(deck(_,_))")
    use_db(db, ":- retractall(deck(_,_)).", False)
    print("PYTHON: retractall(knows_at(_,_))")
    use_db(db, ":- retractall(knows_at(_,_)).", False)

    knows_a = []
    knows_b = []

    for index, a_card in enumerate(a_cards):
        use_db(db, ":- assertz(at(a, " + str(index + 1) + ", " + a_card + ")).", False)
        knows_b.append("(a, " + str(index + 1) + ", " + a_card + ")")

    print("\nOra le carte di 'a' sono diventate le seguenti:")
    use_db(db, ":- print_hand(a, " + str(GLOBAL_COUNTER) + ").", False)

    GLOBAL_COUNTER = GLOBAL_COUNTER + 1

    for index, b_card in enumerate(b_cards):
        use_db(db, ":- assertz(at(b, " + str(index + 1) + ", " + b_card + ")).", False)
        knows_a.append("(b, " + str(index + 1) + ", " + b_card + ")")

    print("\nOra le carte di 'b' sono diventate le seguenti:")
    use_db(db, ":- print_hand(b, " + str(GLOBAL_COUNTER) + ").", False)

    for index, card in enumerate(deck):
        use_db(db, ":- assertz(deck(" + str(index + 1) + ", " + card + ")).", False)

    print("\nOra le carte del mazzo sono diventate le seguenti:")
    use_db(db, ":- print_deck(" + str(GLOBAL_COUNTER) + ").", False)

    print("------------------")

    # Init 1.0::knows_at(a, (b, ...))
    for tuple_knows_at_a in knows_a:
        knows_at_a_string = ":- assertz((1.0::knows_at(a, " + tuple_knows_at_a + ")))."
        print("Aggiorno " + "assertz((1.0::knows_at(a, " + tuple_knows_at_a + "))).")
        use_db(db, knows_at_a_string, False)

    print("------------------")

    # Init 1.0::knows_at(b, (a, ...))
    for tuple_knows_at_b in knows_b:
        knows_at_b_string = ":- assertz((1.0::knows_at(b, " + tuple_knows_at_b + ")))."
        print("Aggiorno " + "assertz((1.0::knows_at(b, " + tuple_knows_at_b + "))).")
        use_db(db, knows_at_b_string, False)

    print("------------------")

    use_db(db, "query(knows_at(a, (_,_,_))).", True)
    use_db(db, "query(knows_at(b, (_,_,_))).", True)

    # Contiene le probabilità delle carte date quelle di 'a', ossia le probabilità per l'agente 'b'
    dictionary_a = {
        "red1": 0.0,
        "red2": 0.0,
        "red3": 0.0,
        "red4": 0.0,
        "red5": 0.0,
        "yellow1": 0.0,
        "yellow2": 0.0,
        "yellow3": 0.0,
        "yellow4": 0.0,
        "yellow5": 0.0
    }

    # Contiene le probabilità delle carte date quelle di 'b', ossia le probabilità per l'agente 'a'
    dictionary_b = dictionary_a.copy()

    # Calcolo delle probabilità relative per ciascuna carta rispetto a dictionary_a, ossia per l'agente 'b'
    for card in dictionary_a.copy().keys():
        # Conto quante carte 'card' ci sono nel deck, riaggiungendo al deck le carte di 'b' poiché 'b' non le conosce
        countInDeck = getCardCountInDeck(card, b_cards)
        probabilityToDrawCard = countInDeck / (len(deck) + len(b_cards))
        dictionary_a[card] = probabilityToDrawCard

    # Calcolo delle probabilità relative per ciascuna carta rispetto a dictionary_b, ossia per l'agente 'a'
    for card in dictionary_b.copy().keys():
        # Conto quante carte 'card' ci sono nel deck, riaggiungendo al deck le carte di 'a' poiché 'a' non le conosce
        countInDeck = getCardCountInDeck(card, a_cards)
        probabilityToDrawCard = countInDeck / (len(deck) + len(a_cards))
        dictionary_b[card] = probabilityToDrawCard

    print("------------------")
    print("Init probabilità incerte per knows_at(a, (a, ...)")

    # Init probabilità incerte per knows_at(a, (a, ...)
    for card in all_possible_cards:
        cardProbability = dictionary_b[card]
        for index in range(1, 6):  # Itero sui possibili indici di carte, da 1 a 5
            knows_at_string = ":- assertz((" + str(cardProbability) + "::knows_at(a, (a, " + str(
                index) + ", " + card + "))))."
            # print("Aggiorno " + knows_at_string)
            use_db(db, knows_at_string, False)

    print("------------------")
    print("Init probabilità incerte per knows_at(b, (b, ...)")

    # Init probabilità incerte per knows_at(b, (b, ...)
    for card in all_possible_cards:
        cardProbability = dictionary_a[card]
        for index in range(1, 6):  # Itero sui possibili indici di carte, da 1 a 5
            knows_at_string = ":- assertz((" + str(cardProbability) + "::knows_at(b, (b, " + str(
                index) + ", " + card + "))))."
            # print("Aggiorno " + knows_at_string)
            use_db(db, knows_at_string, False)

    print("------------------")
    print("Fine inizializzazione carte ai giocatori.\n")


# Data una carta e le carte di un giocatore, aggiunge di nuovo le carte di quel giocatore al deck e conta le occorrenze.
# L'idea è ottenere il conteggio senza considerare che playerCards non è più nel deck, ossia un giocatore 'a' se vede
# che 'b' ha un red4, allora 'a' assume che in deck ci sia al più 1 carta 'red4' rimasta, ma non considera che
# nel suo playerCards potrebbe già esserci un 'red4' e pertanto nel deck ce ne saranno 0. Questa funzione, invece,
# restituisce 1 in questo caso.
def getCardCountInDeck(card, playerCards):
    count = 0
    tmpDeck = deck.copy()
    tmpDeck.extend(playerCards)

    for deckCard in tmpDeck:
        if deckCard == card:
            count = count + 1

    return count


def use_db(db, query_extension, print_evaluation):
    # Nota: se non si volesse modificare db, occorrerebbe fare una copia del DefaultEngine nuova
    # pl_model_sr = PrologFile("hanabi.pl")
    # db_tmp = DefaultEngine().prepare(pl_model_sr)

    # Nota: l'istruzione che segue NON crea una copia. Il DefaultEngine è condiviso.
    # Questa istruzione crea problemi se esegui più volte hint_rank; sembra comunque non necessaria
    # Forse è necessaria quando si aggiungono predicati esterni (tipo query(), o hint_rank(..) senza ":-")
    if print_evaluation:
        db = db.extend()

    # Aggiungiamo le dichiarazioni fornite in query_extension a db
    for statement in PrologString(query_extension):
        db += statement

    # Valutiamo il database
    evaluation = get_evaluatable().create_from(db).evaluate()

    # Stampiamo l'evaluation solo se print_evaluation è True
    if print_evaluation:
        print(evaluation)

    return evaluation


def load_env_file(filepath):
    with open(filepath) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value


def extract_cards_from_hcic2(data):
    # Definisci le carte per ogni gruppo di 10 colonne
    cards = ['R1', 'R2', 'R3', 'R4', 'R5', 'Y1', 'Y2', 'Y3', 'Y4', 'Y5']

    # Funzione per trasformare una riga
    def transform_row(row):
        transformed_row = []
        for i in range(0, 50, 10):
            group = row[i:i + 10]
            max_idx = group.idxmax()
            card = cards[max_idx % 10]
            transformed_row.append(card)
        return transformed_row

    # Applica la trasformazione alle prime 100 colonne
    return data.T.iloc[:, :50].apply(transform_row, axis=1)

def getP1AndP2Cards(hcicModels, obs_vectors):
    predicted_player0_hand = [None] * 5
    # Iniziamo a recuperare le 5 carte più probabili per P1, e ottenere così 'P1 Cards':
    for i in range(0, 5):
        predicted_player0_hand[i] = (hcicModels['index_' + str(i + 1)].
                                     predict(np.array(obs_vectors[0]).reshape(1, -1)))

    predicted_player0_hand = np.concatenate(
        [predicted_player0_hand[i].flatten() for i in range(0, 5)])

    predicted_player0_hand = extract_cards_from_hcic2(pd.DataFrame(predicted_player0_hand))
    p1_cards = str(predicted_player0_hand[0])

    predicted_player1_hand = [None] * 5
    # Iniziamo a recuperare le 5 carte più probabili per P1, e ottenere così 'P1 Cards':
    for i in range(0, 5):
        predicted_player1_hand[i] = (hcicModels['index_' + str(i + 1)].
                                     predict(np.array(obs_vectors[1]).reshape(1, -1)))

    predicted_player1_hand = np.concatenate(
        [predicted_player1_hand[i].flatten() for i in range(0, 5)])

    predicted_player1_hand = extract_cards_from_hcic2(pd.DataFrame(predicted_player1_hand))
    p2_cards = str(predicted_player1_hand[0])

    return p1_cards, p2_cards
