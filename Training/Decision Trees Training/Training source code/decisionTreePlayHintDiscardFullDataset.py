import pandas as pd
import ast
# from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, accuracy_score
# import lime.lime_tabular
import joblib

""" Max accuracy: 82.76% - Decision Tree per predire la migliore azione da eseguire tra PLAY, GIVE_HINT, DISCARD """

# Leggiamo il dataset dal file CSV
df = pd.read_csv('../fullDatasetMDP.csv')
df['Best action'] = df['Best action'].replace(['REVEAL_COLOR', 'REVEAL_RANK'], 'GIVE_HINT')

# Rimuoviamo i casi in cui viene dato un Hint ma con 0 info tokens, che sono casi errati
df = df[(df['Remaining info tokens'] != 0) | (df['Best action'] != 'GIVE_HINT')]
# Rimuoviamo la colonna "Info best action"
df = df.drop(columns=['Info best action'])

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


df = pd.concat(
    [df.drop(columns=['P1 Cards']),
     df['P1 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P1_')],
    axis=1)
df = pd.concat(
    [df.drop(columns=['P2 Cards']),
     df['P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P2_')],
    axis=1)
df = pd.concat(
    [df.drop(columns=['Actual P2 Cards']),
     df['Actual P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('Actual_P2_')],
    axis=1)
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

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

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
                          'importances/decision_tree_playHintDiscard_full_dataset_importances.txt', sep=' ', index=False)

# Salva il modello
joblib.dump(best_model,
            '../../../models/decision_trees_models_MDP/decision_tree_playHintDiscard_full_dataset.joblib')
print("Modello salvato.")

"""
# Using RandomForest for better performance
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)
print(f'Random Forest Accuracy: {rf_accuracy * 100:.2f}%')
"""

"""
# Utilizzo di LIME per spiegare le predizioni del modello
explainer = lime.lime_tabular.LimeTabularExplainer(X_train.values, feature_names=X_train.columns,
                                                   class_names=clf.classes_, verbose=True, mode='classification',
                                                   discretize_continuous=True)

num_features = 15
num_explanations = 5

# Seleziona degli esempi dal set di test e mostrane la spiegazione
# Questo è utile solamente per spiegazioni LOCALI e non globali
for i in range(num_explanations):
    exp_ = explainer.explain_instance(X_test.iloc[i], clf.predict_proba, num_features=num_features, top_labels=3)
    labels = exp_.available_labels()
    labels.sort()

    # Itero su ogni label così da fare uno schema per ciascuna di esse
    # Utile perché altrimenti la tabella a destra del notebook mostrata varrà solamente per la prima label
    for label in labels:
        exp = explainer.explain_instance(X_test.iloc[i], clf.predict_proba, num_features=num_features, labels=[label])

        # Questa è la tabella delle importanze delle features, esportata nei file html (quella sulla destra)
        # print(pd.DataFrame(exp.as_list(label=label), columns=['Feature', 'Contribution']))

        # Save Notebook style summary
        # A sinistra troviamo i valori negativi che contribuiscono a uno score negativo, a destra le feature
        # che contribuiscono con uno score positivo. Più a destra troviamo in ordine decrescente le
        # feature più importanti per la label corrente, affiancate dal loro valore nel dataset
        # (capisci la label in base al colore delle feature di destra).
        exp.save_to_file(f'../test_{i}_label_{label}.html')

        # fig = exp.as_pyplot_figure()
        # fig.tight_layout()
        # plt.show()
"""
