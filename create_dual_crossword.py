from reportlab.platypus import SimpleDocTemplate, Flowable
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
import random
import time

# -----------------------------
# Grid template
# -----------------------------
GRID_SIZE = 30
GRID_TEMPLATE = ["." * GRID_SIZE for _ in range(GRID_SIZE)]

# -----------------------------
# Word pairs (positive / negative)
# -----------------------------
word_pairs = {
    "FOCUSED": "FIXATED",
    "CAREFUL": "FEARFUL",
    "DIRECT": "ABRUPT",
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
    "PRAGMATIC": "UNFEELING",
    "DISCERNING": "NITPICKING",
    "INTUITIVE": "SKEPTICAL",
    "PASSIONATE": "COMPULSIVE",
    "CREATIVE": "ANARCHIC",
}

CENTER_PAIR = ("NEURODIVERGENT", "MISUNDERSTOOD?")

# -----------------------------
# Flowable to draw grid
# -----------------------------
class CrosswordGrid(Flowable):
    def __init__(self, grid, cell_size, numbers=None, show_pos=True, show_neg=True, show_slash=False, title=None, letters_scale=0.9):
        Flowable.__init__(self)
        self.grid = grid
        self.cell_size = cell_size
        self.numbers = numbers
        self.show_pos = show_pos
        self.show_neg = show_neg
        self.show_slash = show_slash
        self.title = title
        self.letters_scale = letters_scale
        self.width = len(grid[0]) * self.cell_size
        self.height = len(grid) * self.cell_size + (20*mm if title else 0)

    def draw(self):
        canvas = self.canv
        size = self.cell_size
        rows = len(self.grid)
        cols = len(self.grid[0])

        # Draw title
        y_offset = 0
        if self.title:
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawCentredString(self.width / 2, self.height - 12, self.title)
            y_offset = 20

        for r in range(rows):
            for c in range(cols):
                x = c * size
                y = (rows - 1 - r) * size + y_offset
                cell = self.grid[r][c]

                # Draw cell border
                canvas.rect(x, y, size, size)

                # Draw clue number
                if self.numbers and self.numbers[r][c]:
                    canvas.setFont("Helvetica", int(size * 0.25))
                    canvas.setFillColor(colors.black)
                    canvas.drawString(x + 1, y + size - size * 0.3, str(self.numbers[r][c]))

                if cell == "#":
                    canvas.setFillColor(colors.black)
                    canvas.rect(x, y, size, size, fill=1)
                    canvas.setFillColor(colors.black)
                elif cell is not None:
                    pos, neg = cell

                    if self.show_slash:
                        # Draw slash
                        canvas.setStrokeColor(colors.black)
                        canvas.line(x, y, x + size, y + size)

                        # Smaller letters for readability in dual
                        font_size = int(size * 0.35)
                        canvas.setFont("Helvetica-Bold", font_size)

                        if self.show_pos:
                            canvas.setFillColor(colors.darkgreen)
                            canvas.drawCentredString(
                                x + size * 0.25,
                                y + size * 0.75 - font_size / 2,
                                pos
                            )

                        if self.show_neg:
                            canvas.setFillColor(colors.darkred)
                            canvas.drawCentredString(
                                x + size * 0.75,
                                y + size * 0.25 - font_size / 2,
                                neg
                            )
                    else:
                        font_size = int(size * self.letters_scale)
                        canvas.setFont("Courier-Bold", font_size)

                        if self.show_pos:
                            canvas.setFillColor(colors.darkgreen)
                            canvas.drawCentredString(
                                x + size / 2,
                                y + size / 2 - font_size / 3,
                                pos
                            )

                        if self.show_neg:
                            canvas.setFillColor(colors.darkred)
                            canvas.drawCentredString(
                                x + size / 2,
                                y + size / 2 - font_size / 3,
                                neg
                            )

# -----------------------------
# PDF generation
# -----------------------------
def create_pdf(grid, filename, cell_size, numbers=None, show_pos=True, show_neg=True, show_slash=False, title=None, letters_scale=0.9):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    elements = [CrosswordGrid(grid, cell_size, numbers, show_pos, show_neg, show_slash, title, letters_scale)]
    doc.build(elements)

# -----------------------------
# Number the crossword
# -----------------------------
def number_crossword(grid):
    rows = len(grid)
    cols = len(grid[0])
    number_grid = [[None for _ in range(cols)] for _ in range(rows)]
    across_clues = []
    down_clues = []
    clue_number = 1

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            if not isinstance(cell, tuple):
                continue

            start_across = (c == 0 or grid[r][c-1] == "#") and (c + 1 < cols and isinstance(grid[r][c+1], tuple))
            start_down = (r == 0 or grid[r-1][c] == "#") and (r + 1 < rows and isinstance(grid[r+1][c], tuple))

            if start_across or start_down:
                number_grid[r][c] = clue_number

                if start_across:
                    word = []
                    cc = c
                    while cc < cols and isinstance(grid[r][cc], tuple):
                        word.append(grid[r][cc])
                        cc += 1
                    across_clues.append((clue_number, r, c, word))

                if start_down:
                    word = []
                    rr = r
                    while rr < rows and isinstance(grid[rr][c], tuple):
                        word.append(grid[rr][c])
                        rr += 1
                    down_clues.append((clue_number, r, c, word))

                clue_number += 1

    return number_grid, across_clues, down_clues

# -----------------------------
# Place words
# -----------------------------
def place_words(grid, center_pair, word_pairs):
    rows, cols = len(grid), len(grid[0])
    central_word_pos, central_word_neg = center_pair
    central_row = rows // 2

    for i in range(len(central_word_pos)):
        grid[central_row][(cols - len(central_word_pos))//2 + i] = (central_word_pos[i], central_word_neg[i])

    placed_words = []

    def can_place_word(r, c, pos_word, neg_word, vertical=True):
        word_length = len(pos_word)

        # -----------------------------
        # 1️⃣ Bounds check
        # -----------------------------
        for i in range(word_length):
            rr = r + i if vertical else r
            cc = c if vertical else c + i

            if rr < 0 or rr >= rows or cc < 0 or cc >= cols:
                return False

        # -----------------------------
        # 2️⃣ Prevent same-direction appending
        # -----------------------------
        if vertical:
            before_r, before_c = r - 1, c
            after_r, after_c = r + word_length, c
        else:
            before_r, before_c = r, c - 1
            after_r, after_c = r, c + word_length

        if 0 <= before_r < rows and 0 <= before_c < cols:
            if isinstance(grid[before_r][before_c], tuple):
                return False

        if 0 <= after_r < rows and 0 <= after_c < cols:
            if isinstance(grid[after_r][after_c], tuple):
                return False

        # -----------------------------
        # 3️⃣ Letter placement checks
        # -----------------------------
        for i, (p, n) in enumerate(zip(pos_word, neg_word)):
            rr = r + i if vertical else r
            cc = c if vertical else c + i

            existing = grid[rr][cc]

            # Conflict
            if existing is not None and existing != "#" and existing != (p, n):
                return False

            # -----------------------------
            # 4️⃣ NEW: True perpendicular adjacency rule
            # -----------------------------
            if existing is None:
                if vertical:
                    # Check left and right neighbours
                    if cc > 0 and isinstance(grid[rr][cc - 1], tuple):
                        return False
                    if cc < cols - 1 and isinstance(grid[rr][cc + 1], tuple):
                        return False
                else:
                    # Check above and below neighbours
                    if rr > 0 and isinstance(grid[rr - 1][cc], tuple):
                        return False
                    if rr < rows - 1 and isinstance(grid[rr + 1][cc], tuple):
                        return False

        return True

    for pos_word, neg_word in word_pairs.items():
        placed = False
        positions = [(r, c) for r in range(rows) for c in range(cols) if isinstance(grid[r][c], tuple)]
        random.shuffle(positions)
        for r, c in positions:
            for j in range(len(pos_word)):
                # Vertical
                start_row = r - j
                if can_place_word(start_row, c, pos_word, neg_word, vertical=True):
                    for k, (p, n) in enumerate(zip(pos_word, neg_word)):
                        grid[start_row + k][c] = (p, n)
                    placed_words.append((pos_word, neg_word))
                    placed = True
                    break
                # Horizontal
                start_col = c - j
                if can_place_word(r, start_col, pos_word, neg_word, vertical=False):
                    for k, (p, n) in enumerate(zip(pos_word, neg_word)):
                        grid[r][start_col + k] = (p, n)
                    if not placed:
                        placed_words.append((pos_word, neg_word))
                        placed = True
                    break
            if placed:
                break
    return grid, placed_words
# -----------------------------
# Fill remaining empty with black
# -----------------------------
def fill_empty_with_black(grid):
    return [[cell if cell is not None else "#" for cell in row] for row in grid]

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    start_time = time.time()
    max_attempts = 1000000
    best_placed = 0
    best_grid = None

    for attempt in range(max_attempts):
        print(f"Attempt {attempt+1}/{max_attempts} - Placed {best_placed}/{len(word_pairs)} words", end="\r")
        grid = [[None if c == "." else "#" for c in row] for row in GRID_TEMPLATE]
        shuffled_pairs = list(word_pairs.items())
        random.shuffle(shuffled_pairs)

        grid, placed = place_words(grid, CENTER_PAIR, dict(shuffled_pairs))

        if len(placed) > best_placed:
            best_placed = len(placed)
            best_grid = [row.copy() for row in grid]

        if len(placed) == len(word_pairs):
            break

    if best_grid is None:
        print("Could not place all words.")
        exit(1)

    grid = best_grid
    filled_grid = fill_empty_with_black([row.copy() for row in grid])

    # Number the grid
    number_grid, across, down = number_crossword(filled_grid)

    # Determine cell size
    page_width, page_height = A4
    margin = 15*mm
    max_cell_width = (page_width - 2*margin) / len(filled_grid[0])
    max_cell_height = (page_height - 2*margin - 30) / len(filled_grid)
    cell_size = min(max_cell_width, max_cell_height)

    timestamp = int(time.time())

    # -----------------------------
    # PDFs with numbering
    # -----------------------------
    create_pdf(
        filled_grid,
        f"crossword_dual_{timestamp}.pdf",
        cell_size,
        # numbers=number_grid,
        show_pos=True,
        show_neg=True,
        show_slash=True,
        title="Neurodivergent Traits Crossword"
    )

    create_pdf(
        filled_grid,
        f"crossword_pos_{timestamp}.pdf",
        cell_size,
        numbers=number_grid,
        show_pos=True,
        show_neg=False,
        show_slash=False,
        title="Positive Traits Only",
        letters_scale=0.9
    )

    create_pdf(
        filled_grid,
        f"crossword_neg_{timestamp}.pdf",
        cell_size,
        numbers=number_grid,
        show_pos=False,
        show_neg=True,
        show_slash=False,
        title="Negative Traits Only",
        letters_scale=0.9
    )

    # ✅ Blank grid still shows clue numbers
    blank_grid = [[cell if cell == "#" else None for cell in row] for row in filled_grid]
    create_pdf(
        blank_grid,
        f"crossword_blank_{timestamp}.pdf",
        cell_size,
        numbers=number_grid,
        show_pos=False,
        show_neg=False,
        show_slash=False,
        title="Blank Crossword"
    )

    print(f"Best attempt placed {best_placed}/{len(word_pairs)} words.")
    print(f"PDFs generated successfully! Total time: {time.time() - start_time:.2f} seconds")