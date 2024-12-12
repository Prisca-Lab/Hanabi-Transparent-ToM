import os
import joblib
from keras.models import load_model
from hanabiLearningEnvHandler import HanabiHandler

# Global variables
decisionTreesModels = {}
hcicModels = {}


def loadModels(loadDecisionTrees=False):
    if loadDecisionTrees:
        # Imposta TensorFlow per usare solo la CPU
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

        # Carico i modelli dei decision trees e li memorizzo nel dizionario decisionTreesModels
        decisionTreesModels['decision_tree_color'] = joblib.load(
            'models/decision_trees_models_MDP/decision_tree_color_full_dataset.joblib')
        decisionTreesModels['decision_tree_discard'] = joblib.load(
            'models/decision_trees_models_MDP/decision_tree_discard_full_dataset.joblib')
        decisionTreesModels['decision_tree_playHintDiscard'] = joblib.load(
            'models/decision_trees_models_MDP/decision_tree_playHintDiscard_full_dataset.joblib')
        decisionTreesModels['decision_tree_play'] = joblib.load(
            'models/decision_trees_models_MDP/decision_tree_play_full_dataset.joblib')
        decisionTreesModels['decision_tree_rankColor'] = joblib.load(
            'models/decision_trees_models_MDP/decision_tree_rankColor_full_dataset.joblib')
        decisionTreesModels['decision_tree_rank'] = joblib.load(
            'models/decision_trees_models_MDP/decision_tree_rank_full_dataset.joblib')

    # Carico i modelli HCIC e li memorizzo nel dizionario hcicModels
    hcicModels['index_1'] = load_model('models/HCIC_models_2players/model_pos_1.h5')
    hcicModels['index_2'] = load_model('models/HCIC_models_2players/model_pos_2.h5')
    hcicModels['index_3'] = load_model('models/HCIC_models_2players/model_pos_3.h5')
    hcicModels['index_4'] = load_model('models/HCIC_models_2players/model_pos_4.h5')
    hcicModels['index_5'] = load_model('models/HCIC_models_2players/model_pos_5.h5')


def main():
    print("Hanabi Card Game Backend")
    approachChoiceToM1 = ''
    approachChoiceToM2 = ''
    approachChoice = None
    explainerChoiceToM1 = None
    explainerChoiceToM2 = None

    while True:
        # Ask the user which game type they want to use
        gameChoice = input("Choose which type of gameplay you want for the Hanabi card game "
                           "(1: ToM with Human, 2: ToM with ToM): ").strip()

        if gameChoice == "1":
            print("You chose the ToM with Human gameplay.")
            gameChoice = "ToM_Human"
            break
        elif gameChoice == "2":
            print("You chose the ToM with ToM gameplay.")
            gameChoice = "ToM"
            break
        else:
            print("Invalid choice. Please type '1' for the ToM with Human gameplay "
                  "or '2' for the ToM with ToM gameplay.")

    if gameChoice == "ToM_Human":
        while True:
            # Ask the user which approach they want to use
            approachChoice = input("Choose an approach for the Hanabi card game "
                                   "(1: logic-based, 2: decision trees): ").strip()

            if approachChoice == "1":
                print("You chose the logic-based approach.")
                loadModels(False)
                approachChoice = "logic-based"
                break
            elif approachChoice == "2":
                print("You chose the decision trees approach.")
                loadModels(True)
                approachChoice = "decision-trees"
                break
            else:
                print("Invalid choice. Please type '1' for the logic-based approach "
                      "or '2' for the decision trees approach.")

        while True:
            # Ask the user which explainer they want to use
            explainerChoiceToM1 = input("Choose an explainer for the ToM model "
                                        "(1: low-level, 2: high-level): ").strip()

            if explainerChoiceToM1 == "1":
                print("You chose the low-level explainer.")
                explainerChoiceToM1 = "low-level"
                break
            elif explainerChoiceToM1 == "2":
                print("You chose the high-level explainer.")
                explainerChoiceToM1 = "high-level"
                break
            else:
                print("Invalid choice. Please type '1' for the low-level explainer "
                      "or '2' for the high-level explainer.")
    else:
        while True:
            # Ask the user which approach they want to use for the first ToM model
            approachChoice = input("Choose an approach for the first ToM model "
                                   "(1: logic-based, 2: decision trees): ").strip()

            if approachChoice == "1":
                print("You chose the logic-based approach.")
                approachChoiceToM1 = "logic-based"
                break
            elif approachChoice == "2":
                print("You chose the decision trees approach.")
                approachChoiceToM1 = "decision-trees"
                break
            else:
                print("Invalid choice. Please type '1' for the logic-based approach "
                      "or '2' for the decision trees approach.")

        while True:
            # Ask the user which approach they want to use for the second ToM model
            approachChoice = input("Choose an approach for the second ToM model "
                                   "(1: logic-based, 2: decision trees): ").strip()

            if approachChoice == "1":
                print("You chose the logic-based approach.")
                approachChoiceToM2 = "logic-based"
                break
            elif approachChoice == "2":
                print("You chose the decision trees approach.")
                approachChoiceToM2 = "decision-trees"
                break
            else:
                print("Invalid choice. Please type '1' for the logic-based approach "
                      "or '2' for the decision trees approach.")

        if approachChoiceToM1 == "decision-trees" or approachChoiceToM2 == "decision-trees":
            loadModels(True)
        else:
            loadModels(False)

        while True:
            # Ask the user which explainer they want to use
            explainerChoiceToM1 = input("Choose an explainer for the first ToM model "
                                    "(1: low-level, 2: high-level): ").strip()

            if explainerChoiceToM1 == "1":
                print("You chose the low-level explainer.")
                explainerChoiceToM1 = "low-level"
                break
            elif explainerChoiceToM1 == "2":
                print("You chose the high-level explainer.")
                explainerChoiceToM1 = "high-level"
                break
            else:
                print("Invalid choice. Please type '1' for the low-level explainer "
                      "or '2' for the high-level explainer.")

        while True:
            # Ask the user which explainer they want to use
            explainerChoiceToM2 = input("Choose an explainer for the second ToM model "
                                        "(1: low-level, 2: high-level): ").strip()

            if explainerChoiceToM2 == "1":
                print("You chose the low-level explainer.")
                explainerChoiceToM2 = "low-level"
                break
            elif explainerChoiceToM2 == "2":
                print("You chose the high-level explainer.")
                explainerChoiceToM2 = "high-level"
                break
            else:
                print("Invalid choice. Please type '1' for the low-level explainer "
                      "or '2' for the high-level explainer.")

    if gameChoice == "ToM_Human":
        HanabiHandler(explainerChoiceToM1, None, approachChoice, None, None, gameChoice, decisionTreesModels, hcicModels)
    else:
        HanabiHandler(explainerChoiceToM1, explainerChoiceToM2, None, approachChoiceToM1, approachChoiceToM2, gameChoice, decisionTreesModels, hcicModels)


if __name__ == "__main__":
    main()
