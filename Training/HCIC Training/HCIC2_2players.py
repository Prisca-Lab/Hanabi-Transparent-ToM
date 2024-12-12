from random import randint
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.layers import Dropout
import matplotlib.pyplot as plt
import os

# Carica il dataset
# dataset_df = pd.read_csv('/home/carmine/Scrivania/dataset2players [5hint 3fuse].csv')
dataset_df = pd.read_csv('dataset2players [5hint 3fuse].csv')

""" ########## Statistiche ########## """
"""
# Definizione dei nomi delle colonne
column_names = []
column_names.extend([f"Feature_{i}" for i in range(1, 308)])  # 307 colonne float
column_names.extend(['Index1', 'Index2', 'Index3', 'Index4', 'Index5'])  # 5 colonne index

# Caricamento del dataset senza header
dataset_df_tmp = pd.read_csv('dataset2players [5hint 3fuse].csv', header=None, names=column_names)
dataset_df_tmp = dataset_df_tmp.dropna()

num_samples = len(dataset_df_tmp)
print("Numero totale di campioni nel dataset:", num_samples)

# Per ogni index (R1, R2, R3, R4, R5 e Y1, Y2, Y3, Y4, Y5), devi calcolare la frequenza delle carte 
# per ciascuna classe di output. Supponendo che la colonna delle carte per ogni index sia denominata 
# come 'Index1', 'Index2', ..., 'Index5':
index_columns = ['Index1', 'Index2', 'Index3', 'Index4', 'Index5']
possible_cards = ['R1', 'R2', 'R3', 'R4', 'R5', 'Y1', 'Y2', 'Y3', 'Y4', 'Y5']

for index_col in index_columns:
    print(f"\nAnalisi per {index_col}:")
    card_counts = dataset_df_tmp[index_col].value_counts()
    for card in possible_cards:
        count = card_counts.get(card, 0)
        print(f"{card}: {count} campioni")
"""
""" ################################## """

# Estrai i dati di input e target dal DataFrame
X = dataset_df.iloc[:, :307].values  # Dati di input (307 valori float)
y = dataset_df.iloc[:, 307:].values  # Target (classi delle carte e relativi indici)

# Prima divisione: set di addestramento e test
random_state = randint(0, 1000)
print("Random state is", random_state)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=random_state)

# Seconda divisione: set di addestramento e validation
X_test, X_val, y_test, y_val = train_test_split(X_test, y_test, test_size=0.5, random_state=random_state)


# Funzione per creare il modello MLP
# Testare anche modello CNN qui https://github.com/jtwwang/hanabi/blob/master/predictors/conv_pred.py
# Ricorda di "Add an additional dimension for filters"
def create_model():
    model = Sequential()
    model.add(Dense(256, activation='relu', input_shape=(307,)))
    model.add(Dropout(0.2))
    model.add(Dense(128, activation='relu'))
    model.add(Dropout(0.1))
    model.add(Dense(128, activation='relu'))
    model.add(Dense(10, activation='softmax'))  # 10 classi per ogni posizione
    return model


# Plot delle curve di addestramento e validazione
def plot_history(i, history):
    plt.figure(figsize=(12, 4))

    # Accuracy plot
    plt.subplot(1, 2, 1)
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Val Accuracy')
    plt.title(f'Index {i + 1} - Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()

    # Loss plot
    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Val Loss')
    plt.title(f'Index {i + 1} - Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()

    plt.tight_layout()
    plt.show()


# Crea la cartella per salvare i modelli, se non esiste
os.makedirs("hcic2models_2players", exist_ok=True)

# Il numero di modelli da generare, cioè i modelli di predizione di index di carte da 1 a 5
numberOfIndexes = 5

# Compila i modelli per ciascuna posizione delle carte
models = [create_model() for _ in range(numberOfIndexes)]
for model in models:
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Addestra un modello per ciascuna posizione delle carte
label_encoders = []
histories = []

for i in range(numberOfIndexes):
    # Codifica le etichette per la i-esima posizione
    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train[:, i])
    y_val_encoded = label_encoder.transform(y_val[:, i])
    label_encoders.append(label_encoder)

    # Converti le etichette in formato one-hot encoded per la i-esima posizione
    y_train_one_hot = to_categorical(y_train_encoded, num_classes=10)
    y_val_one_hot = to_categorical(y_val_encoded, num_classes=10)

    # Definisci il checkpoint per salvare il modello
    checkpoint = ModelCheckpoint(filepath=f"hcic2models_2players/model_pos_{i + 1}.h5", save_best_only=True,
                                 monitor='val_loss', mode='min')

    # Addestra il modello
    history = models[i].fit(X_train, y_train_one_hot, epochs=100, batch_size=64,
                            validation_data=(X_val, y_val_one_hot), callbacks=[checkpoint])
    histories.append(history)
    plot_history(i, history)

# Per fare predizioni con i modelli
predictions = []
for i in range(numberOfIndexes):
    preds = models[i].predict(X_test)
    decoded_preds = label_encoders[i].inverse_transform(np.argmax(preds, axis=1))
    predictions.append(decoded_preds)

# Combina le predizioni per ottenere la mano completa del giocatore
final_predictions = np.column_stack(predictions)

# Inizializza le variabili per conteggiare gli errori per ciascuna posizione
errors_per_position = [{'total_wrong_rank_color_rank_only_one_diff': 0,
                        'total_wrong_rank_color': 0,
                        'total_wrong_rank_only_one_diff': 0,
                        'total_wrong_rank_only': 0,
                        'total_wrong_color_only': 0} for _ in range(numberOfIndexes)]

# Itera su ogni posizione e raccogli le statistiche degli errori
for i in range(numberOfIndexes):
    for j in range(len(X_test)):
        prediction = final_predictions[j][i]
        real_value = y_test[j][i]

        # Estrai rank e colore dalla predizione e dal valore reale
        pred_color, pred_rank = prediction[0], int(prediction[1])
        real_color, real_rank = real_value[0], int(real_value[1])

        # Confronta rank e colore per la posizione i
        if pred_rank != real_rank and pred_color != real_color:
            if abs(pred_rank - real_rank) == 1:
                errors_per_position[i]['total_wrong_rank_color_rank_only_one_diff'] += 1
            else:
                errors_per_position[i]['total_wrong_rank_color'] += 1
        elif pred_rank != real_rank and pred_color == real_color:
            if abs(pred_rank - real_rank) == 1:
                errors_per_position[i]['total_wrong_rank_only_one_diff'] += 1
            else:
                errors_per_position[i]['total_wrong_rank_only'] += 1
        elif pred_rank == real_rank and pred_color != real_color:
            errors_per_position[i]['total_wrong_color_only'] += 1

# Calcola e stampa le statistiche per ciascuna posizione
for i in range(numberOfIndexes):
    errors = errors_per_position[i]
    total_errors = sum(errors.values())
    total_rank_errors = total_errors - errors['total_wrong_color_only']
    total_color_errors = total_errors - errors['total_wrong_rank_only'] - errors['total_wrong_rank_only_one_diff']
    total_predictions = len(X_test)

    print(f"Statistiche sugli errori di predizione per la posizione {i + 1}:")
    print(f"Totale predizioni: {total_predictions}")
    print(f"1. Sia rank che colore: {errors['total_wrong_rank_color']}")
    print(f"2. Sia rank che colore ma il rank differisce di 1 numero: {errors['total_wrong_rank_color_rank_only_one_diff']}")
    print(f"3. Solo il rank: {errors['total_wrong_rank_only']}")
    print(f"4. Solo il rank ma il rank differisce di 1 numero: {errors['total_wrong_rank_only_one_diff']}")
    print(f"5. Solo il colore: {errors['total_wrong_color_only']}")
    print(f"Totale errori: {total_errors}")
    print(f"Totale accuratezza previsioni perfette: {round(100-((total_errors/total_predictions)*100), 2)}%")
    print(f"Totale accuratezza previsioni rank: {round(100-((total_rank_errors/total_predictions)*100), 2)}%")
    print(f"Totale accuratezza previsioni colors: {round(100-((total_color_errors/total_predictions)*100), 2)}%")
    print()
