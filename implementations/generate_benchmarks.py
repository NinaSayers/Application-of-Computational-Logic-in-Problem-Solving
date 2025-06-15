import os
import random
import csv

# ====================================================
#           GENERADOR DE BENCHMARKS CNF DIVERSIFICADOS
# ====================================================
# Familias:
# 1. Random 3-SAT (por debajo, en y por encima del umbral de fase)
# 2. Pigeonhole principle
# 3. Random 4-SAT (cerca del umbral k-SAT)
# 4. Graph coloring en grafos aleatorios
# 5. Parity (XOR) constraints
# 6. BMC de circuito Flip-Flop simple
# 7. Problemas DLIS-friendly (cláusulas largas, sesgo en literales, baja densidad)
# 8. Problemas no DLIS-friendly (cláusulas cortas, sin sesgo, alta densidad)
# ====================================================

# Carpeta principal de salida
BASE_OUTPUT_DIR = "generated_benchmarks"
CSV_SUMMARY = os.path.join(BASE_OUTPUT_DIR, "benchmarks_summary.csv")

# Cantidades a generar (total aumentado para cubrir nuevos grupos)
NUM_RANDOM3 = 15    # instancias Random-3SAT
NUM_PIGEON = 15     # instancias Pigeonhole
NUM_RANDOM4 = 15    # instancias Random-4SAT
NUM_GRAPH = 10      # instancias Graph coloring
NUM_PARITY = 10     # instancias Parity
NUM_BMC = 10        # instancias BMC flip-flop
NUM_DLIS_PROBS = 30 # problemas DLIS-friendly nuevos
NUM_NON_DLIS_PROBS = 30 # problemas no DLIS-friendly nuevos

# Parámetros de generación
# Random-3SAT
RANDOM3_SIZES = [1000, 2000, 5000]
PHASE_RATIO3 = 4.26
RATIO_DELTA3 = 0.5
RATIOS3 = [PHASE_RATIO3 - RATIO_DELTA3, PHASE_RATIO3, PHASE_RATIO3 + RATIO_DELTA3]

# Random-4SAT
RANDOM4_SIZES = [500, 1000, 2000]
PHASE_RATIO4 = 9.88  # umbral aproximado para 4-SAT
RATIO_DELTA4 = 1.0
RATIOS4 = [PHASE_RATIO4 - RATIO_DELTA4, PHASE_RATIO4, PHASE_RATIO4 + RATIO_DELTA4]

# Graph coloring
graph_nodes = [50, 100, 200]
graph_edge_prob = [0.1, 0.3, 0.5]
num_colors = [3, 4, 5]

# Pigeonhole, Parity, BMC
PIGEON_SIZES = [10, 20, 30, 40, 50]
PARITY_SIZES = [10, 20, 30, 40, 50]
BMC_DEPTHS = [3, 5, 7, 9, 11]

SEED = 42

# ----------------------------------------------------

def write_cnf(clauses, n_vars, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(f"p cnf {n_vars} {len(clauses)}\n")
        for clause in clauses:
            f.write(' '.join(str(lit) for lit in clause) + ' 0\n')

# 1. Random k-SAT genérico

def generate_random_ksat(n_vars, k, ratio, idx, output_dir):
    random.seed(SEED + idx)
    n_clauses = int(n_vars * ratio)
    clauses = []
    for _ in range(n_clauses):
        lits = set()
        while len(lits) < k:
            var = random.randint(1, n_vars)
            sign = random.choice([1, -1])
            lits.add(sign * var)
        clauses.append(list(lits))
    filename = f"random{k}sat_n{n_vars}_r{ratio:.2f}_{idx}.cnf"
    filepath = os.path.join(output_dir, filename)
    write_cnf(clauses, n_vars, filepath)
    return filename, n_vars, n_clauses, f"random{k}sat"

# Función para generar cláusulas con sesgo en literales (más positivas o negativas)

def generate_biased_clause(n_vars, k, bias_pos=0.7):
    """
    Genera una cláusula con k literales, donde la probabilidad de que un literal sea positivo es bias_pos,
    para introducir sesgos en la distribución de literales.
    """
    lits = set()
    while len(lits) < k:
        var = random.randint(1, n_vars)
        sign = 1 if random.random() < bias_pos else -1
        lits.add(sign * var)
    return list(lits)

def generate_biased_ksat(n_vars, k, ratio, idx, output_dir, bias_pos=0.7):
    random.seed(SEED + idx)
    n_clauses = int(n_vars * ratio)
    clauses = [generate_biased_clause(n_vars, k, bias_pos) for _ in range(n_clauses)]
    filename = f"biased_random{k}sat_n{n_vars}_r{ratio:.2f}_b{bias_pos:.2f}_{idx}.cnf"
    filepath = os.path.join(output_dir, filename)
    write_cnf(clauses, n_vars, filepath)
    return filename, n_vars, n_clauses, f"biased_random{k}sat"

# 2. Pigeonhole

def generate_pigeonhole(n_holes, idx, output_dir):
    n_pigeons = n_holes + 1
    def var(p, h): return (p - 1) * n_holes + h
    clauses = []
    for p in range(1, n_pigeons + 1):
        clauses.append([var(p, h) for h in range(1, n_holes + 1)])
    for h in range(1, n_holes + 1):
        for p1 in range(1, n_pigeons + 1):
            for p2 in range(p1 + 1, n_pigeons + 1):
                clauses.append([-var(p1, h), -var(p2, h)])
    n_vars = n_pigeons * n_holes
    filename = f"pigeon_{n_pigeons}_into_{n_holes}_{idx}.cnf"
    filepath = os.path.join(output_dir, filename)
    write_cnf(clauses, n_vars, filepath)
    return filename, n_vars, len(clauses), "pigeonhole"

# 3. Graph coloring: k colores en grafo aleatorio

def generate_graph_coloring(n, p, k, idx, output_dir):
    random.seed(SEED + idx)
    # asignar variable x_{v,c} = v* k + c
    var_index = lambda v, c: (v - 1) * k + c
    clauses = []
    # generar aristas
    edges = [(i, j) for i in range(1, n + 1) for j in range(i + 1, n + 1) if random.random() < p]
    # cada vértice tiene al menos un color
    for v in range(1, n + 1):
        clauses.append([var_index(v, c) for c in range(1, k + 1)])
    # cada vértice un solo color
    for v in range(1, n + 1):
        for c1 in range(1, k + 1):
            for c2 in range(c1 + 1, k + 1):
                clauses.append([-var_index(v, c1), -var_index(v, c2)])
    # adyacencia: vértices conectados no comparten color
    for i, j in edges:
        for c in range(1, k + 1):
            clauses.append([-var_index(i, c), -var_index(j, c)])
    n_vars = n * k
    filename = f"graphcol_n{n}_p{p:.2f}_k{k}_{idx}.cnf"
    filepath = os.path.join(output_dir, filename)
    write_cnf(clauses, n_vars, filepath)
    return filename, n_vars, len(clauses), "graphcolor"

# 4. Parity XOR

def generate_parity(n_vars, idx, output_dir):
    clauses = [[i for i in range(1, n_vars + 1)]]
    for i in range(1, n_vars + 1):
        for j in range(i + 1, n_vars + 1):
            clauses.append([-i, -j])
    filename = f"parity_n{n_vars}_{idx}.cnf"
    filepath = os.path.join(output_dir, filename)
    write_cnf(clauses, n_vars, filepath)
    return filename, n_vars, len(clauses), "parity"

# 5. BMC flip-flop

def generate_bmc_flipflop(depth, idx, output_dir):
    clauses = []
    for t in range(depth):
        clauses.append([-(t + 1), -(t + 2)])
        clauses.append([t + 1, t + 2])
    clauses.append([1])
    clauses.append([depth + 1])
    n_vars = depth + 1
    filename = f"bmc_flipflop_d{depth}_{idx}.cnf"
    filepath = os.path.join(output_dir, filename)
    write_cnf(clauses, n_vars, filepath)
    return filename, n_vars, len(clauses), "bmc"

# -------------------
# Main: generación y CSV resumen
# -------------------
if __name__ == '__main__':
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
    summary = []

    # Random-3SAT
    for idx in range(NUM_RANDOM3):
        n = RANDOM3_SIZES[idx % len(RANDOM3_SIZES)]
        ratio = RATIOS3[idx % len(RATIOS3)]
        summary.append(generate_random_ksat(n, 3, ratio, idx, BASE_OUTPUT_DIR))

    # Pigeonhole
    for idx in range(NUM_PIGEON):
        n = PIGEON_SIZES[idx % len(PIGEON_SIZES)]
        summary.append(generate_pigeonhole(n, idx, BASE_OUTPUT_DIR))

    # Random-4SAT
    for idx in range(NUM_RANDOM4):
        n = RANDOM4_SIZES[idx % len(RANDOM4_SIZES)]
        ratio = RATIOS4[idx % len(RATIOS4)]
        summary.append(generate_random_ksat(n, 4, ratio, idx, BASE_OUTPUT_DIR))

    # Graph coloring
    for idx in range(NUM_GRAPH):
        n = graph_nodes[idx % len(graph_nodes)]
        p = graph_edge_prob[idx % len(graph_edge_prob)]
        k = num_colors[idx % len(num_colors)]
        summary.append(generate_graph_coloring(n, p, k, idx, BASE_OUTPUT_DIR))

    # Parity
    for idx in range(NUM_PARITY):
        n = PARITY_SIZES[idx % len(PARITY_SIZES)]
        summary.append(generate_parity(n, idx, BASE_OUTPUT_DIR))

    # BMC flip-flop
    for idx in range(NUM_BMC):
        d = BMC_DEPTHS[idx % len(BMC_DEPTHS)]
        summary.append(generate_bmc_flipflop(d, idx, BASE_OUTPUT_DIR))

    # Problemas DLIS-friendly (cláusulas largas, sesgo en literales, baja densidad)
    for idx in range(NUM_DLIS_PROBS):
        n_vars = random.choice([200, 300, 400])
        k = random.choice([5, 6])
        ratio = random.uniform(2.0, 3.5)
        bias_pos = random.uniform(0.7, 0.8)
        summary.append(generate_biased_ksat(n_vars, k, ratio, idx + 2000, BASE_OUTPUT_DIR, bias_pos))

    # Problemas no DLIS-friendly (cláusulas cortas, sin sesgo, alta densidad)
    for idx in range(NUM_NON_DLIS_PROBS):
        n_vars = random.choice([1000, 2000, 5000])
        k = 3
        ratio = random.uniform(4.0, 5.0)
        bias_pos = 0.5
        summary.append(generate_biased_ksat(n_vars, k, ratio, idx + 3000, BASE_OUTPUT_DIR, bias_pos))

    # Escribir CSV resumen
    with open(CSV_SUMMARY, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'n_vars', 'n_clauses', 'category'])
        for row in summary:
            writer.writerow(row)

    print(f"✅ Generados {len(summary)} benchmarks en '{BASE_OUTPUT_DIR}'")
    print(f"✅ CSV de resumen guardado en '{CSV_SUMMARY}'")
