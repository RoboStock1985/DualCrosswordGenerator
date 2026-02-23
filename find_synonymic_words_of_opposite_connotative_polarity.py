import nltk
from nltk.corpus import wordnet

# Make sure to download WordNet if not already done
nltk.download('wordnet')
nltk.download('omw-1.4')

def find_length_synonyms(word):

    """
    Find synonyms of `word` that have the same length
    and share at least one letter with the original word.
    """

    word = word.lower()
    word_len = len(word)
    candidates = set()

    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            lemma_name = lemma.name().replace("_", "").lower()
            if lemma_name == word:
                continue
            if len(lemma_name) == word_len and any(c in lemma_name for c in word):
                candidates.add(lemma_name.upper())
    
    return sorted(candidates)

# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":

    words = ["Fixated", "Obsessive", "Chaotic", "Erratic", "Hyperactive", "Disruptive", "Inattentive", "Impulsive", "Self-Absorbed", "Overreactive", "Fragile", "Difficult", "Rigid", "Abrupt", "Distant", "Stingy", "Fanatical", "Paranoid", "Brutal", "Forceful", "Extreme", "Pedantical", "Pedantic", "Fanaticism", "Irritable", "Moody", "Overwhelmed", "Unpredictable", "Nervous", "Reserved", "Detached", "Shy", "Awkward", "Insecure", "Timid", "Solitary", "Cold", "Unfeeling", "Introverted", "Apologetic", "Difficult", "Stubborn", "Distracted", "Slow", "Confused", "Disorganized", "Unfocused", "Unmethodical", "Rash", "Clumsy", "Forgetful","Lazy","Irresponsible"]

    for w in words:
        syns = find_length_synonyms(w)
        print(f"{w.upper():12} → {syns}")