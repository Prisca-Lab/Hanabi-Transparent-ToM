from utility_functions import getP1AndP2Cards
import pandas as pd
import ast

# Nomi di colonne degli alberi (Play, Hint, Discard), (Rank, Colour), (Rank), (Colour)
all_columns = [
    'Remaining info tokens', 'Remaining life tokens', 'Deck size',
    'P1_Y5', 'P1_Y3', 'P1_R4', 'P1_R2', 'P1_Y2', 'P1_Y1',
    'P1_Y4', 'P1_R1', 'P1_R3', 'P1_R5', 'P2_Y4', 'P2_Y1', 'P2_Y3', 'P2_R1',
    'P2_R4', 'P2_Y2', 'P2_R2', 'P2_R3', 'P2_Y5', 'P2_R5', 'Actual_P2_Y1',
    'Actual_P2_Y4', 'Actual_P2_R1', 'Actual_P2_R4', 'Actual_P2_R5',
    'Actual_P2_Y3', 'Actual_P2_Y2', 'Actual_P2_R2', 'Actual_P2_R3',
    'Actual_P2_Y5', 'Fireworks_R', 'Fireworks_Y', 'Discarded_R3',
    'Discarded_Y1', 'Discarded_Y5', 'Discarded_Y3', 'Discarded_Y4',
    'Discarded_R1', 'Discarded_Y2', 'Discarded_R2', 'Discarded_R4',
    'Discarded_R5'
]

# Nomi di colonne degli alberi (Play) e (Discard)
play_discard_all_columns = [
    'Remaining info tokens', 'Fireworks_Y', 'Fireworks_R', 'Deck size',
    'P1_pos_1_Y1', 'P1_pos_0_R2', 'P1_pos_1_R1', 'P1_pos_3_R1',
    'P1_pos_3_Y1', 'P1_pos_0_Y2', 'P1_pos_2_Y1', 'P1_pos_2_Y3',
    'P1_pos_0_R1', 'P1_pos_2_R2', 'P1_pos_0_Y1', 'P1_pos_2_Y2',
    'P1_pos_4_Y1', 'P1_pos_2_R1', 'P1_pos_2_Y5', 'Remaining life tokens',
    'P2_pos_4_Y1', 'P1_pos_2_Y4', 'P1_pos_2_R4', 'Actual_P2_R1',
    'Actual_P2_Y1', 'P1_pos_4_Y2', 'P1_pos_1_R4', 'P1_pos_2_R3',
    'P1_pos_0_Y4', 'P2_pos_2_Y1', 'P1_pos_1_Y2', 'P1_pos_4_R2',
    'Actual_P2_R2', 'P2_pos_1_Y2', 'P2_pos_2_Y5', 'Actual_P2_R3',
    'Actual_P2_Y4', 'Discarded_Y1', 'Actual_P2_Y3', 'Discarded_R1',
    'P2_pos_3_Y3', 'P1_pos_0_Y3', 'P2_pos_1_Y3', 'Actual_P2_Y5',
    'P2_pos_1_R4', 'Actual_P2_Y2', 'P2_pos_0_R2', 'Actual_P2_R4',
    'Actual_P2_R5', 'Discarded_R3', 'Discarded_Y2', 'P1_pos_0_R3',
    'P1_pos_0_R4', 'P2_pos_3_Y4', 'P2_pos_0_Y4', 'Discarded_R4',
    'Discarded_Y3', 'P1_pos_1_Y3', 'P1_pos_4_R1', 'P1_pos_3_Y3',
    'Discarded_R2', 'P2_pos_2_R1', 'Discarded_Y4', 'P1_pos_4_R4',
    'P2_pos_2_Y3', 'P1_pos_1_R3', 'P1_pos_3_Y2', 'P2_pos_4_Y2',
    'P1_pos_3_Y4', 'P2_pos_4_R4', 'P2_pos_0_R3', 'P1_pos_0_Y5',
    'P2_pos_3_R2', 'Discarded_Y5', 'P1_pos_0_R5', 'P2_pos_0_Y2',
    'P2_pos_1_Y1', 'P2_pos_3_Y2', 'P2_pos_3_Y1', 'P2_pos_0_R5',
    'P1_pos_1_Y4', 'P2_pos_4_Y4', 'P2_pos_2_R2', 'P1_pos_4_R3',
    'P2_pos_0_Y3', 'P2_pos_4_R1', 'Discarded_R5', 'P2_pos_4_R2',
    'P2_pos_0_R1', 'P2_pos_3_R3', 'P2_pos_4_Y3', 'P2_pos_1_Y4',
    'P2_pos_0_Y1', 'P2_pos_3_R1', 'P1_pos_4_Y4', 'P1_pos_3_R2',
    'P1_pos_4_Y5', 'P2_pos_2_R4', 'P1_pos_3_R3', 'P2_pos_2_Y4',
    'P2_pos_0_R4', 'P2_pos_1_R2', 'P2_pos_3_R4', 'P2_pos_2_R3',
    'P2_pos_1_R3', 'P1_pos_1_Y5', 'P1_pos_3_R5', 'P1_pos_4_Y3',
    'P2_pos_1_R1', 'P2_pos_4_Y5', 'P1_pos_4_R5', 'P1_pos_3_Y5',
    'P2_pos_4_R3', 'P1_pos_1_R2', 'P2_pos_0_Y5', 'P1_pos_3_R4',
    'P1_pos_1_R5', 'P2_pos_1_Y5', 'P2_pos_4_R5', 'P2_pos_3_Y5',
    'P2_pos_2_R5', 'P2_pos_2_Y2', 'P2_pos_1_R5', 'P2_pos_3_R5',
    'P1_pos_2_R5'
]


# Funzione per trovare la classe per Play o per Discard più probabile e che sia legale
def find_most_probable_legal_action(actionType, sorted_classes, legal_actions):
    for cls in sorted_classes:
        # Converti la classe da stringa a intero e sottrai 1 per adattarlo agli indici di Play
        # dell'HLE, che richiede i valori tra 0 e 4 e non tra 1 e 5
        index = int(cls) - 1

        # Costruisci l'azione 'Play/Discard X' corrispondente
        action = f'({actionType} {index})'

        # Verifica se l'azione è presente nelle azioni legali
        if action in legal_actions:
            return action

    # Se nessuna classe è legale, restituisci None
    return None


def find_most_probable_rank_or_color(actionType, sorted_classes, legal_actions):
    for cls in sorted_classes:
        # cls = 'R'/'Y' oppure '1'/.../'5' a seconda di actionType (se è rispettivamente color oppure rank)

        action = f'({actionType} {cls})'

        # Verifica se l'azione è presente nelle azioni legali
        if action in legal_actions:
            return action

    # Se nessuna classe è legale, restituisci None o una stringa di errore a tua scelta
    return None


def encode_cards(cards):
    card_counts = {}
    for card in cards:
        card_counts[card] = card_counts.get(card, 0) + 1
    return card_counts


def encode_cards_with_position(cards):
    encoded_cards = {}
    for idx, card in enumerate(cards):
        encoded_cards[f'pos_{idx}_{card}'] = 1
    return encoded_cards


# Questo metodo ci consente di generalizzare il recupero della mossa migliore
# per gli alberi (Play) e (Discard)
def get_play_or_discard(decisionTreeModel, actionString, gameState, legal_actions):
    # Converti il dizionario in un DataFrame
    df = pd.DataFrame.from_dict(gameState)

    # Converti le colonne che contengono liste e dizionari da stringhe agli oggetti appropriati
    df['P1 Cards'] = df['P1 Cards'].apply(ast.literal_eval)
    df['P2 Cards'] = df['P2 Cards'].apply(ast.literal_eval)
    df['Actual P2 Cards'] = df['Actual P2 Cards'].apply(ast.literal_eval)
    df['Fireworks'] = df['Fireworks'].apply(ast.literal_eval)
    df['Discarded pile'] = df['Discarded pile'].apply(ast.literal_eval)

    # Crea DataFrame per ciascuna categoria
    df_p1 = df['P1 Cards'].apply(encode_cards_with_position).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'P1_')
    df_p2 = df['P2 Cards'].apply(encode_cards_with_position).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'P2_')
    df_actual_p2 = df['Actual P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'Actual_P2_')
    df_fireworks = df['Fireworks'].apply(pd.Series).fillna(0).astype(int).add_prefix('Fireworks_')
    df_discarded = df['Discarded pile'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'Discarded_')

    # Concatenate DataFrames
    df = pd.concat([df.drop(columns=['P1 Cards', 'P2 Cards', 'Actual P2 Cards', 'Fireworks', 'Discarded pile']),
                    df_p1, df_p2, df_actual_p2, df_fireworks, df_discarded], axis=1)

    # Aggiungi colonne mancanti con valore 0 in un colpo solo
    missing_cols = [col for col in play_discard_all_columns if col not in df.columns]
    if missing_cols:
        df = pd.concat([df, pd.DataFrame(0, index=df.index, columns=missing_cols)], axis=1)

    feature_names = decisionTreeModel.feature_names_in_.tolist()
    # Riordina le colonne secondo l'ordine del modello
    df = df[feature_names]

    y_prob = decisionTreeModel.predict_proba(df)

    classes = decisionTreeModel.classes_
    # Converti le probabilità in un DataFrame con le classi come colonne
    df_prob = pd.DataFrame(y_prob, columns=classes)

    # Ordina le probabilità per ogni riga in ordine decrescente e recupera le classi ordinate
    df_sorted = df_prob.apply(lambda row: row.sort_values(ascending=False).index.tolist(), axis=1)

    # Ora df_sorted contiene le classi ordinate per probabilità e df_prob_sorted contiene le probabilità ordinate

    # Ora qui abbiamo una lista di 5 stringhe, ['1' '2' '3' '4' '5'],
    sorted_classes = df_sorted[0]

    legal_actions_str = [str(move) for move in legal_actions]
    most_probable_legal_action = find_most_probable_legal_action(actionString, sorted_classes, legal_actions_str)

    # Trova e restituisci il primo oggetto HanabiMove che corrisponde a most_probable_legal_action
    return next((legal_move for legal_move in legal_actions if str(legal_move) == most_probable_legal_action), None)


# Questo metodo ci consente di generalizzare il recupero della mossa migliore per gli alberi
# (Rank, Colour), (Rank), (Colour)
def get_sorted_classes(decisionTreeModel, gameState):
    # Converti il dizionario in un DataFrame
    df = pd.DataFrame.from_dict(gameState)

    # Converti le colonne che contengono liste e dizionari da stringhe agli oggetti appropriati
    df['P1 Cards'] = df['P1 Cards'].apply(ast.literal_eval)
    df['P2 Cards'] = df['P2 Cards'].apply(ast.literal_eval)
    df['Actual P2 Cards'] = df['Actual P2 Cards'].apply(ast.literal_eval)
    df['Fireworks'] = df['Fireworks'].apply(ast.literal_eval)
    df['Discarded pile'] = df['Discarded pile'].apply(ast.literal_eval)

    # Crea DataFrame per ciascuna categoria
    df_p1 = df['P1 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'P1_')
    df_p2 = df['P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'P2_')
    df_actual_p2 = df['Actual P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'Actual_P2_')
    df_fireworks = df['Fireworks'].apply(pd.Series).fillna(0).astype(int).add_prefix('Fireworks_')
    df_discarded = df['Discarded pile'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
        'Discarded_')

    # Concatenate DataFrames
    df = pd.concat([df.drop(columns=['P1 Cards', 'P2 Cards', 'Actual P2 Cards', 'Fireworks', 'Discarded pile']),
                    df_p1, df_p2, df_actual_p2, df_fireworks, df_discarded], axis=1)

    # Aggiungi colonne mancanti con valore 0 in un colpo solo
    missing_cols = [col for col in all_columns if col not in df.columns]
    if missing_cols:
        df = pd.concat([df, pd.DataFrame(0, index=df.index, columns=missing_cols)], axis=1)

    feature_names = decisionTreeModel.feature_names_in_.tolist()
    # Riordina le colonne secondo l'ordine del modello
    df = df[feature_names]

    y_prob = decisionTreeModel.predict_proba(df)

    classes = decisionTreeModel.classes_
    # Converti le probabilità in un DataFrame con le classi come colonne
    df_prob = pd.DataFrame(y_prob, columns=classes)

    # Ordina le probabilità per ogni riga in ordine decrescente e recupera le classi ordinate
    df_sorted = df_prob.apply(lambda row: row.sort_values(ascending=False).index.tolist(), axis=1)
    return df_sorted[0]


class DecisionTreesHandler:
    def __init__(self, decisionTreesModels, hcicModels):
        self.decisionTreesModels = decisionTreesModels
        self.hcicModels = hcicModels

    def selectBestAction(self, gameState):
        """ The decisionTreesModels are:
            - self.decisionTreesModels['decision_tree_color']
            - self.decisionTreesModels['decision_tree_discard']
            - self.decisionTreesModels['decision_tree_playHintDiscard']
            - self.decisionTreesModels['decision_tree_play']
            - self.decisionTreesModels['decision_tree_rankColor']
            - self.decisionTreesModels['decision_tree_rank']

            We need to structure the info based on the used decision trees. We need to end up with something like:
            "['Y4', 'Y1', 'R1', 'Y4', 'R4']","['Y1', 'Y1', 'R3', 'Y3', 'Y1']","['Y1', 'Y1', 'R2', 'R3', 'Y2']"
            "{'R': 2, 'Y': 1}",8,1,"['Y2', 'R2']",7

            Then, we will filter these information in the appropriate format for the specific decision tree.
            These filtering operations are inspired from the ones used in the training processes.

            -------------------------------------------------------------------

            'gameState' will have the following information:
            gameState['observation_vectors', 'Actual P2 Cards', 'Fireworks', 'Remaining info tokens',
            'Remaining life tokens', 'Discarded pile', 'Deck size', 'Legal actions']
            Note that 'Best action' and 'Info best action' are the info we need to find, so we won't take them in input.
            'observation_vectors' is a list of two observation vectors of 307 features each, each from a
            different player.

            We'll alter 'gameState' such that it will have:
            gameState['P1 Cards', 'P2 Cards', 'Actual P2 Cards', 'Fireworks', 'Remaining info tokens',
            'Remaining life tokens', 'Discarded pile', 'Deck size', 'Legal actions']
            To do this we'll use the HCIC models, giving them the 'observation_vectors'[0]/[1] parameter. After that,
            we'll be able to filter the information in the appropriate format, as mentioned before.

            This function then proceeds to pass gameState to each specific function designed for the specific
            decision tree, which will proceed to filter the information.
            This function will then call the 'playHintDiscard' handler function, and based on its response invoke the
            appropriate functions which will call other decision trees.
        """

        p1_cards, p2_cards = getP1AndP2Cards(self.hcicModels, gameState['observation_vectors'])

        print("Predicted cards with HCIC modules:")
        print("p1_cards =", p1_cards)
        print("p2_cards =", p2_cards)

        # Aggiungiamo le carte predette a gameState
        gameState['P1 Cards'] = p1_cards
        gameState['P2 Cards'] = p2_cards

        return self.playHintDiscard(gameState)

    def playHintDiscard(self, gameState):
        # Rimuoviamo ciò che non ci occorre del dizionario gameState
        gameState_cleaned = [
            {k: v for k, v in gameState.items() if k != 'observation_vectors' and k != 'Legal actions'}]

        # Converti il dizionario in un DataFrame
        df = pd.DataFrame.from_dict(gameState_cleaned)

        # Converti le colonne che contengono liste e dizionari da stringhe agli oggetti appropriati
        df['P1 Cards'] = df['P1 Cards'].apply(ast.literal_eval)
        df['P2 Cards'] = df['P2 Cards'].apply(ast.literal_eval)
        df['Actual P2 Cards'] = df['Actual P2 Cards'].apply(ast.literal_eval)
        df['Fireworks'] = df['Fireworks'].apply(ast.literal_eval)
        df['Discarded pile'] = df['Discarded pile'].apply(ast.literal_eval)

        # Crea DataFrame per ciascuna categoria
        df_p1 = df['P1 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P1_')
        df_p2 = df['P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P2_')
        df_actual_p2 = df['Actual P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
            'Actual_P2_')
        df_fireworks = df['Fireworks'].apply(pd.Series).fillna(0).astype(int).add_prefix('Fireworks_')
        df_discarded = df['Discarded pile'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
            'Discarded_')

        # Concatenate DataFrames
        df = pd.concat([df.drop(columns=['P1 Cards', 'P2 Cards', 'Actual P2 Cards', 'Fireworks', 'Discarded pile']),
                        df_p1, df_p2, df_actual_p2, df_fireworks, df_discarded], axis=1)

        # Aggiungi colonne mancanti con valore 0
        for col in all_columns:
            if col not in df.columns:
                df[col] = 0

        feature_names = self.decisionTreesModels['decision_tree_playHintDiscard'].feature_names_in_.tolist()
        # Riordina le colonne secondo l'ordine del modello
        df = df[feature_names]

        # y_prob è una matrice in cui ogni riga contiene le probabilità di ciascuna classe per ogni campione
        y_prob = self.decisionTreesModels['decision_tree_playHintDiscard'].predict_proba(df)

        classes = self.decisionTreesModels['decision_tree_playHintDiscard'].classes_
        # Converti le probabilità in un DataFrame con le classi come colonne
        df_prob = pd.DataFrame(y_prob, columns=classes)

        # Ordina le probabilità per ogni riga in ordine decrescente e recupera le classi ordinate
        df_sorted = df_prob.apply(lambda row: row.sort_values(ascending=False).index.tolist(), axis=1)

        # Ora df_sorted contiene le classi ordinate per probabilità e df_prob_sorted contiene le probabilità ordinate
        print("Classi ordinate per probabilità:")
        print(df_sorted)

        # Ora qui abbiamo una lista di 3 stringhe, ['DISCARD' 'GIVE_HINT' 'PLAY'],
        # ordinate in base al ranking delle probabilità
        sorted_classes = df_sorted[0]

        legal_actions = gameState['Legal actions']
        legal_actions_str = [str(move) for move in legal_actions]

        # Nota: in sorted_classes[0] c'è la classe più probabile, per cui partiamo da quella
        if sorted_classes[0] == 'GIVE_HINT':
            # Verifichiamo se è possibile dare almeno un hint:
            # verifichiamo se esiste almeno un'azione che contiene "Reveal"
            contains_reveal = any('Reveal' in action for action in legal_actions_str)

            if contains_reveal:
                # Esiste almeno un'azione che contiene 'Reveal'
                # Occorre passare all'albero (Rank, Color) per scegliere quale hint dare
                return self.rankColour(gameState_cleaned, legal_actions)
            else:
                # Nessuna azione contiene 'Reveal', allora passiamo alla seconda classe più probabile:
                if sorted_classes[1] == 'DISCARD':
                    contains_discard = any('Discard' in action for action in legal_actions_str)

                    if contains_discard:
                        return self.discard(gameState_cleaned, legal_actions)
                    else:
                        # Non possiamo nemmeno scartare carte, allora non ci resta che fare 'Play'
                        return self.play(gameState_cleaned, legal_actions)
                else:  # sorted_classes[1] == 'PLAY'
                    return self.play(gameState_cleaned, legal_actions)

        elif sorted_classes[0] == 'DISCARD':
            # Verifichiamo se è possibile scartare almeno una carta:
            # verifichiamo se esiste almeno un'azione che contiene "Discard"
            contains_discard = any('Discard' in action for action in legal_actions_str)

            if contains_discard:
                # Esiste almeno un'azione che contiene 'Discard'
                # Occorre passare all'albero (Discard) per scegliere quale carta scartare
                return self.discard(gameState_cleaned, legal_actions)
            else:
                # Nessuna azione contiene 'Discard', allora passiamo alla seconda classe più probabile:
                if sorted_classes[1] == 'GIVE_HINT':
                    contains_reveal = any('Reveal' in action for action in legal_actions_str)
                    if contains_reveal:
                        # Occorre passare all'albero (Rank, Color) per scegliere quale hint dare
                        return self.rankColour(gameState_cleaned, legal_actions)
                    else:
                        # Non possiamo nemmeno dare indizi, allora non ci resta che fare 'Play'
                        return self.play(gameState_cleaned, legal_actions)
                else:  # sorted_classes[1] == 'PLAY'
                    return self.play(gameState_cleaned, legal_actions)
        else:  # sorted_classes[0] == 'PLAY'
            # Play è sempre un'azione legale
            return self.play(gameState_cleaned, legal_actions)

    def play(self, gameState, legal_actions):
        return get_play_or_discard(self.decisionTreesModels['decision_tree_play'],
                                   'Play', gameState, legal_actions)

    def discard(self, gameState, legal_actions):
        return get_play_or_discard(self.decisionTreesModels['decision_tree_discard'],
                                   'Discard', gameState, legal_actions)

    def rankColour(self, gameState, legal_actions):
        # Verifica se esiste almeno un hint color o hint rank, perché se uno dei due non esiste,
        # passi immediatamente all'albero rank oppure color a seconda di ciò che esiste.
        """
        Gli hint hanno questa forma nell'HLE:
        (Reveal player +1 rank 1) (ignora l'offset +1)
        (Reveal player +1 rank 2)
        (Reveal player +1 rank 3)
        (Reveal player +1 rank 4)
        (Reveal player +1 rank 5)
        (Reveal player +1 color R)
        (Reveal player +1 color Y)
        """
        legal_actions_str = [str(move) for move in legal_actions]
        contains_reveal_rank = any('Reveal player +1 rank' in action for action in legal_actions_str)
        contains_reveal_color = any('Reveal player +1 color' in action for action in legal_actions_str)

        # Nota: se siamo qui, almeno uno tra rank e color deve essere legale
        if contains_reveal_rank and not contains_reveal_color:
            # In questo caso invochiamo direttamente l'albero (Rank)
            return self.rank(gameState, legal_actions)
        elif not contains_reveal_rank and contains_reveal_color:
            # In questo caso invochiamo direttamente l'albero (Color)
            return self.colour(gameState, legal_actions)
        else:
            # Allora sia reveal rank che reveal color sono entrambe concesse,
            #  dobbiamo prendere una decisione con l'albero (Rank, Colour)
            sorted_classes = get_sorted_classes(self.decisionTreesModels['decision_tree_rankColor'], gameState)

            if sorted_classes[0] == 'REVEAL_COLOR':
                return self.colour(gameState, legal_actions)
            else:
                return self.rank(gameState, legal_actions)

    def rank(self, gameState, legal_actions):
        sorted_classes = get_sorted_classes(self.decisionTreesModels['decision_tree_rank'], gameState)

        legal_actions_str = [str(move) for move in legal_actions]
        most_probable_legal_action = find_most_probable_rank_or_color('Reveal player +1 rank', sorted_classes,
                                                                      legal_actions_str)

        # Trova e restituisci il primo oggetto HanabiMove che corrisponde a most_probable_legal_action
        return next((legal_move for legal_move in legal_actions
                     if str(legal_move) == most_probable_legal_action), None)

    def colour(self, gameState, legal_actions):
        sorted_classes = get_sorted_classes(self.decisionTreesModels['decision_tree_color'], gameState)

        legal_actions_str = [str(move) for move in legal_actions]
        most_probable_legal_action = find_most_probable_rank_or_color('Reveal player +1 color', sorted_classes,
                                                                      legal_actions_str)

        # Trova e restituisci il primo oggetto HanabiMove che corrisponde a most_probable_legal_action
        return next((legal_move for legal_move in legal_actions
                     if str(legal_move) == most_probable_legal_action), None)
