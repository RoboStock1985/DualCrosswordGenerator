from reportlab.platypus import SimpleDocTemplate, Flowable
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
import random
import time

# -----------------------------
# Grid template: '.' = empty, '#' = block
# -----------------------------
GRID_TEMPLATE = [
    "###############################",
    "#########...........##########",
    "########...............########",
    "#######.................#######",
    "######...................######",
    "#####.....................#####",
    "####.......................####",
    "###.........................###",
    "...............................",  # central row index 8
    "###.........................###",
    "####.......................####",
    "#####.....................#####",
    "######...................######",
    "#######.................#######",
    "########...............########",
    "#########...........##########",
    "###############################",
    "###############################",
    "###############################",
    "###############################",
    "###############################",
]

# create a grid of 25 x 25 just dots - DO THIS IN CODE, NOT MANUALLY
GRID_TEMPLATE = ["." * 40 for _ in range(40)]

# -----------------------------
# Word pairs (positive / negative)
# Only include pairs with equal lengths
# -----------------------------
word_pairs = {
    "FOCUSED": "FIXATED",
    "CAREFUL": "FEARFUL",
    "DIRECT": "ABRUPT",
    # "FRUGAL": "STINGY",
    # "INTENSE": "EXTREME",
    "SENSITIVE": "OVERREACT",
    "THOROUGH": "PEDANTIC",    
    "DEDICATED": "OBSESSIVE",
    "RESERVED": "RETICENT",
    "ASSERTIVE": "CONCEITED",
    "INNOVATIVE": "DISRUPTIVE",
    "CAUTIOUS": "PARANOID",
    "INTROSPECTIVE": "SELF-CENTERED",
    "IMAGINATIVE": "INNATENTIVE",
    "CONFIDENT": "DIFFICULT",
    "STEADFAST": "OBSTINATE",
    "RIGOROUS": "STUBBORN",
    "ANIMATED": "FRENZIED",
    "ENERGETIC": "IMPULSIVE",
    "HONEST": "BRUTAL",
    "ENTERPRISING": "EXPLOITATIVE",
    # "ASPIRING": "RUTHLESS",
    # "AMBITIOUS": "CUTTHROAT",
    "PRAGMATIC": "UNFEELING",
    "DISCERNING": "NITPICKING",
    "INTUITIVE": "SKEPTICAL",
    "PASSIONATE": "COMPULSIVE",
    # "INSIGHTFUL": "OVERCRITICAL",
    "CREATIVE": "ANARCHIC",
}

CENTER_PAIR = ("-NEURODIVERGENT-", "-MISUNDERSTOOD?-")  # 14 letters each

# -----------------------------
# PDF rendering with scaling
# -----------------------------
class DualGrid(Flowable):
    def __init__(self, grid, cell_size=10*mm, scale=1.0):
        Flowable.__init__(self)
        self.grid = grid
        self.cell_size = cell_size * scale
        self.width = len(grid[0]) * self.cell_size
        self.height = len(grid) * self.cell_size

    def draw(self):
        canvas = self.canv
        size = self.cell_size
        rows = len(self.grid)
        cols = len(self.grid[0])
        canvas.setFont("Helvetica", 8 * (size / (10*mm)))  # scale font
        for r in range(rows):
            for c in range(cols):
                x = c * size
                y = (rows - 1 - r) * size
                cell = self.grid[r][c]

                # Outer box
                canvas.rect(x, y, size, size)

                if cell == "#":
                    canvas.setFillColor(colors.black)
                    canvas.rect(x, y, size, size, fill=1)
                    canvas.setFillColor(colors.black)
                elif cell is not None:
                    pos, neg = cell
                    # Diagonal slash
                    canvas.line(x, y, x + size, y + size)
                    # Positive (top-left)
                    canvas.drawCentredString(x + size * 0.3, y + size * 0.7, pos)
                    # Negative (bottom-right)
                    canvas.drawCentredString(x + size * 0.7, y + size * 0.3, neg)


def create_pdf(grid, filename="dual_crossword.pdf", scale=1.0):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = [DualGrid(grid, cell_size=10*mm, scale=scale)]
    doc.build(elements)

# -----------------------------
# Word placement logic
# -----------------------------
def place_words(grid, center_pair, word_pairs):
    rows = len(grid)
    cols = len(grid[0])
    central_word_pos, central_word_neg = center_pair

    # -----------------------------
    # Place central word centered horizontally
    # -----------------------------
    central_row = rows // 2
    start_col = (cols - len(central_word_pos)) // 2
    central_cells = set()
    for i in range(len(central_word_pos)):
        grid[central_row][start_col + i] = (central_word_pos[i], central_word_neg[i])
        central_cells.add((central_row, start_col + i))

    placed_words = []

    # -----------------------------
    # Helper: Check if a word can be placed
    # -----------------------------
    def can_place_word(r, c, pos_word, neg_word, vertical=True):
        for i, (p, n) in enumerate(zip(pos_word, neg_word)):
            rr = r + i if vertical else r
            cc = c if vertical else c + i

            if rr < 0 or rr >= rows or cc < 0 or cc >= cols:
                return False  # Out of bounds

            existing = grid[rr][cc]
            if existing is not None and existing != "#" and existing != (p, n):
                return False  # Conflict with non-matching letter

        return True

    # -----------------------------
    # Try to place each word
    # -----------------------------
    for pos_word, neg_word in word_pairs.items():
        if len(pos_word) != len(neg_word):
            continue  # skip mismatched lengths

        placed = False

        # Shuffle positions of existing letters to maximize intersections
        positions = [(r, c) for r in range(rows) for c in range(cols) if isinstance(grid[r][c], tuple)]
        random.shuffle(positions)

        for r, c in positions:
            for j, (p, n) in enumerate(zip(pos_word, neg_word)):

                # Try vertical placement aligning j-th letter to (r, c)
                start_row = r - j
                start_col_v = c
                if can_place_word(start_row, start_col_v, pos_word, neg_word, vertical=True):
                    for k, (lp, ln) in enumerate(zip(pos_word, neg_word)):
                        rr = start_row + k
                        cc = start_col_v
                        grid[rr][cc] = (lp, ln)
                    placed_words.append((pos_word, neg_word))
                    placed = True
                    break

                # Try horizontal placement aligning j-th letter to (r, c)
                start_col = c - j
                start_row_h = r
                if can_place_word(start_row_h, start_col, pos_word, neg_word, vertical=False):
                    for k, (lp, ln) in enumerate(zip(pos_word, neg_word)):
                        rr = start_row_h
                        cc = start_col + k
                        grid[rr][cc] = (lp, ln)
                    if not placed:
                        placed_words.append((pos_word, neg_word))
                        placed = True
                    break

            if placed:
                break

    return grid, placed_words

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":

    # POS_LIST = ["CREATIVE", "VISIONARY", "INNOVATIVE", "INTUITIVE", "PASSIONATE"]
    # NEG_LIST = ["RECKLESS", "IMPRACTICAL", "CHAOTIC", "ANARCHIC", "SCATTERED"]
    
    # # look at POS and NEG lists - print out any words which are the same length and have at least one letter in common, to identify potential extra pairs to add to the word_pairs dict
    # potential_pairs = []
    # for pos in POS_LIST:
    #     for neg in NEG_LIST:
    #         if len(pos) == len(neg) and set(pos) & set(neg):
    #             potential_pairs.append((pos, neg))
    #             print(f"Potential pair: {pos} / {neg}")

    # remove any potential pairs that do not have any shared letters in the same position (to increase chances of intersection)
    # filtered_pairs = []
    # for pos, neg in potential_pairs:
    #     if any(p == n for p, n in zip(pos, neg)):
    #         filtered_pairs.append((pos, neg))
    #         print(f"Filtered pair: {pos} / {neg}")

    run_crossword_flag = True
    if not run_crossword_flag:
        print("Exiting without running crossword generation.")
        exit(0)

    # check word pair lengths
    for pos, neg in word_pairs.items():
        if len(pos) != len(neg):
            print(f"Warning: Skipping pair with mismatched lengths: {pos} {len(pos)} / {neg} {len(neg)}")

    # warn of any duplicate words, in any position (positive or negative)
    all_words = set()
    for pos, neg in word_pairs.items():
        if pos in all_words:
            print(f"Warning: Duplicate word found: {pos}")
        if neg in all_words:
            print(f"Warning: Duplicate word found: {neg}")
        all_words.add(pos)
        all_words.add(neg)

    # warn if any words in the pairs do not share any letters in the same position (to increase chances of intersection)
    # for pos, neg in word_pairs.items():
    #     if not any(p == n for p, n in zip(pos, neg)):
    #         print(f"Warning: Pair has no shared letters in the same position: {pos} / {neg}")

    # how many words total?
    print(f"Total word pairs (excluding center): {len(word_pairs)}")

    print(f"Total unique words in pairs: {len(all_words)}")

    # Initialize empty grid
    grid = [[None if c == "." else "#" for c in row] for row in GRID_TEMPLATE]

    # Place words
    # grid, placed = place_words(grid, CENTER_PAIR, word_pairs)

    # re-run while shuffling around the order of word pairs, to try to place more words    
    shuffled_pairs = list(word_pairs.items())
    max_attempts = 10000
    attempts = 0
    while attempts < max_attempts:

        print(f"Attempt {attempts + 1} of {max_attempts} with shuffled word pairs...")
        random.shuffle(shuffled_pairs)
        grid = [[None if c == "." else "#" for c in row] for row in GRID_TEMPLATE]
        grid, placed = place_words(grid, CENTER_PAIR, dict(shuffled_pairs))
        if len(placed) > len(word_pairs) * 0.99:  # If we placed more than 90% of the words, stop trying to shuffle
            break
        print(f"Placed {len(placed)} out of {len(word_pairs)} word pairs.")

        # keep best result so far
        if attempts == 0:
            best_grid = grid
            best_placed = placed

        if len(placed) > len(best_placed):
            best_grid = grid
            best_placed = placed

        attempts += 1

    # Finalize with best result
    grid = best_grid
    placed = best_placed

    # word pairs used/not used
    used_pairs = set(placed)
    for pos, neg in word_pairs.items():
        if (pos, neg) in used_pairs:
            print(f"Placed: {pos} / {neg}")
        else:
            print(f"Not placed: {pos} / {neg}")

    # Generate PDF
    current_time = int(time.time())
    filename = f"dual_crossword_{len(placed)}_words_{current_time}.pdf"
    create_pdf(grid, filename=filename, scale=0.5)
    print(f"Dual crossword PDF generated with {len(placed)} extra words placed: {filename}")