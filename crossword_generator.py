import random
import copy
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import pagesizes
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import NextPageTemplate
from reportlab.lib.units import inch

# ==========================
# CONFIGURATION
# ==========================

GRID_SIZE = 30

CENTER_PAIR = ("PUBQUIZ", "QUIZPUB")  # Change this

word_pairs = {
    "ROUND": "DNUOR",
    "TRIVIA": "AIVIRT",
    "BEER": "REEB",
    "HOST": "TSOH",
    "TEAM": "MAET",
    "POINT": "TNIOP",
    "MUSIC": "CISUM",
    "FILM": "MLIF",
    "SPORT": "TROPS",
    "HISTORY": "YROTSIH",
    "GEOGRAPHY": "YHPARGOEG",
    "SCIENCE": "ECNEICS",
    "ART": "TRA",
    "FOOD": "DOOF",
    "DRINK": "KNIRD",
}

# ==========================
# GRID UTILITIES
# ==========================

def empty_grid():
    return [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def can_place(grid, r, c, pos_word, neg_word, vertical):
    rows = len(grid)
    cols = len(grid[0])

    for i, (p, n) in enumerate(zip(pos_word, neg_word)):
        rr = r + i if vertical else r
        cc = c if vertical else c + i

        if rr < 0 or rr >= rows or cc < 0 or cc >= cols:
            return False

        existing = grid[rr][cc]

        if existing is not None:
            if existing[0] != p:
                return False

        # Side adjacency
        neighbors = []
        if vertical:
            if cc > 0:
                neighbors.append(grid[rr][cc - 1])
            if cc < cols - 1:
                neighbors.append(grid[rr][cc + 1])
        else:
            if rr > 0:
                neighbors.append(grid[rr - 1][cc])
            if rr < rows - 1:
                neighbors.append(grid[rr + 1][cc])

        for n_cell in neighbors:
            if n_cell is not None:
                if existing is None:
                    return False

    # Check boundaries
    before_r, before_c = (r - 1, c) if vertical else (r, c - 1)
    after_r, after_c = (r + len(pos_word), c) if vertical else (r, c + len(pos_word))

    if 0 <= before_r < rows and 0 <= before_c < cols:
        if grid[before_r][before_c] is not None:
            return False

    if 0 <= after_r < rows and 0 <= after_c < cols:
        if grid[after_r][after_c] is not None:
            return False

    return True


def place_word(grid, r, c, pos_word, neg_word, vertical):
    placed = []

    for i, (p, n) in enumerate(zip(pos_word, neg_word)):
        rr = r + i if vertical else r
        cc = c if vertical else c + i

        if grid[rr][cc] is None:
            grid[rr][cc] = (p, n)
            placed.append((rr, cc))

    return placed


def remove_word(grid, placed):
    for r, c in placed:
        grid[r][c] = None


def generate_positions(grid, pos_word, neg_word):
    rows = len(grid)
    cols = len(grid[0])
    placements = []

    for r in range(rows):
        for c in range(cols):
            for vertical in [True, False]:
                for offset in range(len(pos_word)):
                    start_r = r - offset if vertical else r
                    start_c = c if vertical else c - offset

                    if can_place(grid, start_r, start_c, pos_word, neg_word, vertical):
                        placements.append((start_r, start_c, vertical))

    return placements


# ==========================
# BACKTRACKING SOLVER
# ==========================

def solve(grid, words, index=0, best=None):
    if best is None:
        best = {"count": 0, "grid": None}

    if index >= len(words):
        if index > best["count"]:
            best["count"] = index
            best["grid"] = copy.deepcopy(grid)
        return best

    pos_word, neg_word = words[index]

    placements = generate_positions(grid, pos_word, neg_word)
    random.shuffle(placements)

    if not placements:
        return solve(grid, words, index + 1, best)

    for r, c, vertical in placements:
        placed = place_word(grid, r, c, pos_word, neg_word, vertical)
        best = solve(grid, words, index + 1, best)
        remove_word(grid, placed)

        if best["count"] == len(words):
            return best

    return best


# ==========================
# GRID TRIMMING
# ==========================

def trim_grid(grid):
    rows = len(grid)
    cols = len(grid[0])

    top = min(r for r in range(rows) for c in range(cols) if grid[r][c] is not None)
    bottom = max(r for r in range(rows) for c in range(cols) if grid[r][c] is not None)
    left = min(c for r in range(rows) for c in range(cols) if grid[r][c] is not None)
    right = max(c for r in range(rows) for c in range(cols) if grid[r][c] is not None)

    return [row[left:right+1] for row in grid[top:bottom+1]]


# ==========================
# PDF EXPORT
# ==========================

def export_pdf(grid, filename, show_solution=False):
    doc = SimpleDocTemplate(filename, pagesize=pagesizes.A4)
    elements = []

    cell_size = 18
    table_data = []

    for row in grid:
        row_data = []
        for cell in row:
            if cell is None:
                row_data.append("")
            else:
                row_data.append(cell[0] if show_solution else "")
        table_data.append(row_data)

    table = Table(table_data, colWidths=cell_size, rowHeights=cell_size)

    style = TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    table.setStyle(style)
    elements.append(table)
    doc.build(elements)


# ==========================
# MAIN EXECUTION
# ==========================

grid = empty_grid()

# Place centre word
mid = GRID_SIZE // 2
start_col = (GRID_SIZE - len(CENTER_PAIR[0])) // 2

for i, (p, n) in enumerate(zip(*CENTER_PAIR)):
    grid[mid][start_col + i] = (p, n)

# Sort words longest first
words = sorted(word_pairs.items(), key=lambda x: -len(x[0]))

solution = solve(grid, words)

if solution["grid"] is None:
    print("No solution found.")
    exit()

final_grid = trim_grid(solution["grid"])

print(f"Placed {solution['count']} out of {len(words)} words.")

export_pdf(final_grid, "crossword_puzzle.pdf", show_solution=False)
export_pdf(final_grid, "crossword_solution.pdf", show_solution=True)

print("PDFs exported.")