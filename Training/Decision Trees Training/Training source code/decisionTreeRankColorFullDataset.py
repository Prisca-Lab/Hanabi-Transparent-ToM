import pandas as pd
import ast
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, accuracy_score

""" Decision Tree per predire la migliore azione da eseguire tra REVEAL_COLOR e REVEAL_RANK """
""" Max accuracy: 88.90% - Questa scelta è difficile, suggerire un rank o un colore è spesso ugualmente benefico """

# Leggiamo il dataset dal file CSV
df = pd.read_csv('../fullDatasetMDP.csv')
# Rimuoviamo la colonna "Info best action"
df = df.drop(columns=['Info best action'])

# Rimuovi le righe del dataset che contengono azioni diverse da REVEAL COLOR o REVEAL RANK
df = df[(df['Best action'] == 'REVEAL_COLOR') | (df['Best action'] == 'REVEAL_RANK')]

# Rimuoviamo i casi in cui viene dato un REVEAL_RANK o un REVEAL_COLOR ma con 0 info tokens, che sono casi errati
df = df[(df['Remaining info tokens'] != 0) | ~(df['Best action'].isin(['REVEAL_COLOR', 'REVEAL_RANK']))]

# Convertiamo le colonne che contengono liste e dizionari da stringhe agli oggetti appropriati
df['P1 Cards'] = df['P1 Cards'].apply(ast.literal_eval)
df['P2 Cards'] = df['P2 Cards'].apply(ast.literal_eval)
df['Actual P2 Cards'] = df['Actual P2 Cards'].apply(ast.literal_eval)
df['Fireworks'] = df['Fireworks'].apply(ast.literal_eval)
df['Discarded pile'] = df['Discarded pile'].apply(ast.literal_eval)


# Codifica delle carte per giocatore
def encode_cards(cards):
    card_counts = {}
    for card in cards:
        card_counts[card] = card_counts.get(card, 0) + 1
    return card_counts


df = pd.concat([df.drop(columns=['P1 Cards']),
                df['P1 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P1_')], axis=1)
df = pd.concat([df.drop(columns=['P2 Cards']),
                df['P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P2_')], axis=1)
df = pd.concat([df.drop(columns=['Actual P2 Cards']),
                df['Actual P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).
               astype(int).add_prefix('Actual_P2_')], axis=1)
df = pd.concat(
    [df.drop(columns=['Fireworks']), df['Fireworks'].apply(pd.Series).fillna(0).astype(int).add_prefix('Fireworks_')],
    axis=1)
df = pd.concat([df.drop(columns=['Discarded pile']),
                df['Discarded pile'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
                    'Discarded_')], axis=1)

X = df.drop(columns=['Best action'])
y = df['Best action']

print("Classes distribution:")
print(y.value_counts())

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Train the decision tree model with hyperparameter tuning
param_grid = {
    'max_depth': [5, 10, 15, 20],
    'min_samples_split': [2, 10, 20],
    'min_samples_leaf': [1, 5, 10]
}
grid_search = GridSearchCV(DecisionTreeClassifier(random_state=42), param_grid, cv=5, verbose=2)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_

# Make predictions
y_pred = best_model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f'Decision Tree Accuracy after hyperparameter tuning: {accuracy * 100:.2f}%')
print("Classification Report:\n", classification_report(y_test, y_pred))

importances = best_model.feature_importances_
feature_importance_df = pd.DataFrame({'Feature': X.columns, 'Importance': importances})
sorted_importances = feature_importance_df.sort_values(by='Importance', ascending=False)
print("Features importance:")
print(sorted_importances)

# Salva le importanze del modello
sorted_importances.to_csv('../../../models/decision_trees_models_MDP/'
                          'importances/decision_tree_rankColor_full_dataset_importances.txt', sep=' ', index=False)

# Salva il modello
joblib.dump(best_model, '../../../models/decision_trees_models_MDP/decision_tree_rankColor_full_dataset.joblib')
print("Modello salvato.")
