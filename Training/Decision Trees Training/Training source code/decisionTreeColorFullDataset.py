import pandas as pd
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report
import ast
import joblib


""" Max accuracy: 71.43% - Predizione del colore delle carte da suggerire """
""" Se ci pensiamo, l'accuratezza è relativa, nel senso che talvolta si suggerisce Rosso, quando magari
    in realtà suggerire giallo sarebbe stato ugualmente benefico, quindi non sempre c'è un'azione migliore da fare """

# Leggiamo il dataset dal file CSV
data = pd.read_csv('../fullDatasetMDP.csv')

# Rimuovi le righe del dataset che contengono azioni diverse da REVEAL COLOR
data = data[(data['Best action'] == 'REVEAL_COLOR')]

# Rimuoviamo i casi in cui viene dato un REVEAL_COLOR ma con 0 info tokens, che sono casi errati
data = data[(data['Remaining info tokens'] != 0) | (data['Best action'] != 'REVEAL_COLOR')]

# Convertiamo le colonne che contengono liste e dizionari da stringhe agli oggetti appropriati
data['P1 Cards'] = data['P1 Cards'].apply(ast.literal_eval)
data['P2 Cards'] = data['P2 Cards'].apply(ast.literal_eval)
data['Actual P2 Cards'] = data['Actual P2 Cards'].apply(ast.literal_eval)
data['Fireworks'] = data['Fireworks'].apply(ast.literal_eval)
data['Discarded pile'] = data['Discarded pile'].apply(ast.literal_eval)


# Codifica delle carte per giocatore
def encode_cards(cards):
    card_counts = {}
    for card in cards:
        card_counts[card] = card_counts.get(card, 0) + 1
    return card_counts


data = pd.concat([data.drop(columns=['P1 Cards']),
                  data['P1 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P1_')],
                 axis=1)
data = pd.concat([data.drop(columns=['P2 Cards']),
                  data['P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('P2_')],
                 axis=1)
data = pd.concat(
    [data.drop(columns=['Actual P2 Cards']),
     data['Actual P2 Cards'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix('Actual_P2_')],
    axis=1)
data = pd.concat(
    [data.drop(columns=['Fireworks']),
     data['Fireworks'].apply(pd.Series).fillna(0).astype(int).add_prefix('Fireworks_')], axis=1)
data = pd.concat([data.drop(columns=['Discarded pile']),
                  data['Discarded pile'].apply(encode_cards).apply(pd.Series).fillna(0).astype(int).add_prefix(
                      'Discarded_')], axis=1)

# Separate features and target variable
X = data.drop(columns=['Best action', 'Info best action'])  # Features
y = data['Info best action']  # Target variable

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
                          'importances/decision_tree_color_full_dataset_importances.txt', sep=' ', index=False)

# Salva il modello
joblib.dump(best_model, '../../../models/decision_trees_models_MDP/decision_tree_color_full_dataset.joblib')
print("Modello salvato.")

"""
# Visualize the decision tree
plt.figure(figsize=(60, 20))  # Adjust the figure size as necessary
plot_tree(best_model, filled=True, feature_names=X.columns, class_names=best_model.classes_)
plt.title("Decision Tree Visualization")
plt.show()
"""

"""
# Using RandomForest for better performance
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)
print(f'Random Forest Accuracy: {rf_accuracy * 100:.2f}%')
"""