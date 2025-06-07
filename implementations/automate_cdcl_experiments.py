import os
import subprocess
import time
from glob import glob
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# ====================================================
#         CONFIGURACIÓN DE FLAGS DE CADICAL
# ====================================================
FLAG_VSIDS = "--score=false"  # VSIDS implícito
FLAG_DLIS_TRUE = "--dlis=true --score=false --bump=false --bumpreason=false"
FLAG_DLIS_FALSE = "--dlis=false"
FLAG_RESTART = "--restart=true"
FLAG_NO_RESTART = "--restart=false"
FLAG_STATS = "--stats"
FLAG_TIME = "-t 60"
CADICAL_EXECUTABLE = "./cadical/build/cadical"  # Ajusta la ruta si es necesario
# ====================================================

# Directorios y salida
INPUT_DIR = "./48_benchmarks/"
OUTPUT_CSV = "resultados_experimento.csv"

# Combinaciones a probar
COMBINACIONES = [
    {"vsids": 1, "dlis": 0, "restart": 1},
    {"vsids": 1, "dlis": 0, "restart": 0},
    {"vsids": 0, "dlis": 1, "restart": 1},
    {"vsids": 0, "dlis": 1, "restart": 0},
]

def construir_flags(comb):
    flags = [FLAG_STATS]
    flags += FLAG_TIME.split()

    if comb["vsids"]:
        flags += FLAG_VSIDS.split()

    flags += (FLAG_DLIS_TRUE if comb["dlis"] else FLAG_DLIS_FALSE).split()
    flags += (FLAG_RESTART if comb["restart"] else FLAG_NO_RESTART).split()
    return flags

# 1. Extraer características de cada CNF

def extract_cnf_features(cnf_path):
    num_vars = 0
    num_clauses = 0
    clause_lengths = []
    with open(cnf_path, 'r') as f:
        for line in f:
            if line.startswith('p cnf'):
                _, _, vars_, clauses_ = line.split()
                num_vars = int(vars_)
                num_clauses = int(clauses_)
            elif line and not line.startswith(('c', '%', '0')):
                lits = [int(x) for x in line.split() if x != '0']
                if lits:
                    clause_lengths.append(len(lits))
    avg_clause_length = np.mean(clause_lengths) if clause_lengths else 0
    clause_var_ratio = num_clauses / num_vars if num_vars else 0
    return {
        'path': cnf_path,
        'num_vars': num_vars,
        'num_clauses': num_clauses,
        'avg_clause_length': avg_clause_length,
        'clause_var_ratio': clause_var_ratio
    }

# 2. Crear matriz de características

def build_feature_matrix(cnf_dir):
    cnf_files = glob(os.path.join(cnf_dir, '*.cnf'))
    features = [extract_cnf_features(p) for p in cnf_files]
    return pd.DataFrame(features)

# 3. Clusterizar y seleccionar instancias representativas

def cluster_and_select(df, n_clusters=5, random_state=42):
    feature_cols = ['num_vars', 'num_clauses', 'avg_clause_length', 'clause_var_ratio']
    X = df[feature_cols].values
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    df['cluster'] = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_
    selected = []
    for i, center in enumerate(centers):
        cluster_df = df[df['cluster'] == i]
        dists = np.linalg.norm(cluster_df[feature_cols].values - center, axis=1)
        idx = dists.argmin()
        selected.append(cluster_df.iloc[idx]['path'])
    return selected, df

# 4. Ejecutar solver con cada combinación de flags

def run_solver(instances, combinations, timeout=60):
    results = []
    for comb in combinations:
        flags = construir_flags(comb)
        for inst in instances:
            cmd = [CADICAL_EXECUTABLE] + flags + [inst]
            start = time.time()
            try:
                proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
                if proc.returncode == 10:
                    status = 'sat'
                elif proc.returncode == 20:
                    status = 'unsat'
                else:
                    status = f'code_{proc.returncode}'
                elapsed = time.time() - start
            except subprocess.TimeoutExpired:
                status = 'timeout'
                elapsed = timeout
            results.append({
                'instance': os.path.basename(inst),
                'vsids': comb['vsids'],
                'dlis': comb['dlis'],
                'restart': comb['restart'],
                'status': status,
                'time': elapsed
            })
    return pd.DataFrame(results)

# 5. Generar informes automáticos

def generate_reports(results_df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    results_df.to_csv(os.path.join(output_dir, OUTPUT_CSV), index=False)

    # Tiempos medios por combinación
    summary = results_df.groupby(['vsids', 'dlis', 'restart'])['time'].mean().reset_index()
    summary.to_csv(os.path.join(output_dir, 'summary_times.csv'), index=False)

    # Gráfica de tiempo medio
    plt.figure()
    labels = summary.apply(lambda r: f"V{r.vsids}-D{r.dlis}-R{r.restart}", axis=1)
    plt.bar(labels, summary['time'])
    plt.xlabel('Combinación')
    plt.ylabel('Tiempo medio (s)')
    plt.title('Tiempo medio por configuración')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'avg_time_config.png'))
    plt.close()

    # Conteos de estado
    counts = results_df.groupby(['vsids','dlis','restart','status']).size().unstack(fill_value=0)
    counts.to_csv(os.path.join(output_dir, 'status_counts.csv'))
    counts.plot(kind='bar', stacked=True)
    plt.xlabel('Combinación')
    plt.ylabel('Conteo')
    plt.title('Distribución de estados por configuración')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'status_distribution.png'))
    plt.close()

# Flujo principal
if __name__ == '__main__':
    print('Extrayendo características...')
    feats_df = build_feature_matrix(INPUT_DIR)

    print('Clusterizando y seleccionando instancias...')
    selected, _ = cluster_and_select(feats_df, n_clusters=5)
    print('Instancias seleccionadas:', selected)

    print('Ejecutando solver en combinaciones...')
    results = run_solver(selected, COMBINACIONES, timeout=60)

    print('Generando informes...')
    generate_reports(results, 'experiment_results')
    print('Terminado. Revisa la carpeta experiment_results/')
