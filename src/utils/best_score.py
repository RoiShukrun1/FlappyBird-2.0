import os

def load_best_score():
    try:
        score_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "best_score.txt")
        with open(score_file, 'r') as file:
            return int(file.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def save_best_score(score):
    try:
        current_best = load_best_score()
        if score > current_best:
            score_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "best_score.txt")
            with open(score_file, 'w') as file:
                file.write(str(score))
            return score
        return current_best
    except:
        return score  # If there's any error, just return the current score 