import os
import shutil
from glob import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from mpl_toolkits.mplot3d import Axes3D

# Configuración
INPUT_DIR = "./benchmarks/"
OUTPUT_DIR = "./selected_benchmarks2/"
N_CLUSTERS = 5
PLOT_FILE = "cluster_visualization_3d.png"

# -------------------------------
# Funciones auxiliares
# -------------------------------

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

def build_feature_matrix(cnf_dir):
    cnf_files = glob(os.path.join(cnf_dir, '*.cnf'))
    features = []
    for p in cnf_files:
        try:
            feat = extract_cnf_features(p)
            if feat['num_vars'] > 0 and feat['num_clauses'] > 0:
                features.append(feat)
        except Exception as e:
            print(f"[ERROR] No se pudo procesar {p}: {e}")
    return pd.DataFrame(features)

def cluster_and_select(df, n_clusters=5, random_state=42):
    feature_cols = ['num_vars', 'num_clauses', 'avg_clause_length', 'clause_var_ratio']
    X = df[feature_cols].values
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state)
    df['cluster'] = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_
    selected_paths = []
    selected_indices = []

    for i, center in enumerate(centers):
        cluster_df = df[df['cluster'] == i]
        dists = np.linalg.norm(cluster_df[feature_cols].values - center, axis=1)
        idx = dists.argmin()
        selected_paths.append(cluster_df.iloc[idx]['path'])
        selected_indices.append(cluster_df.index[idx])

    return selected_paths, df, centers, selected_indices, kmeans

def copy_selected_instances(selected_paths, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for path in selected_paths:
        shutil.copy(path, output_dir)
    print(f"✅ Se copiaron {len(selected_paths)} archivos a {output_dir}")

def plot_clusters_3d(df, selected_paths, kmeans, output_path="cluster_visualization_3d.png"):
    feature_cols = ['num_vars', 'num_clauses', 'avg_clause_length', 'clause_var_ratio']
    X = df[feature_cols].values

    # PCA a 3 componentes
    pca = PCA(n_components=3)
    X_3d = pca.fit_transform(X)
    centers_3d = pca.transform(kmeans.cluster_centers_)

    # Añadir componentes al DataFrame
    df['pc1'] = X_3d[:, 0]
    df['pc2'] = X_3d[:, 1]
    df['pc3'] = X_3d[:, 2]

    selected_df = df[df['path'].isin(selected_paths)]

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(df['pc1'], df['pc2'], df['pc3'],
               c=df['cluster'], cmap='tab10', s=40, alpha=0.6, label="Instancias")
    
    ax.scatter(selected_df['pc1'], selected_df['pc2'], selected_df['pc3'],
               c='red', s=100, edgecolor='black', label="Seleccionadas")
    
    ax.scatter(centers_3d[:, 0], centers_3d[:, 1], centers_3d[:, 2],
               c='black', marker='X', s=150, label="Centroides")

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("PC3")
    ax.set_title("Visualización 3D de Clusters de Benchmarks CNF")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.show()
    print(f"✅ Gráfico 3D guardado en {output_path}")

# -------------------------------
# Flujo principal
# -------------------------------

if __name__ == '__main__':
    print('📌 Extrayendo características...')
    feats_df = build_feature_matrix(INPUT_DIR)

    print('📌 Clusterizando y seleccionando instancias...')
    selected, feats_df, centers, selected_idxs, kmeans_model = cluster_and_select(
        feats_df, n_clusters=N_CLUSTERS
    )

    print('📌 Copiando instancias seleccionadas...')
    copy_selected_instances(selected, OUTPUT_DIR)

    print('📌 Generando gráfico 3D del análisis de clusters...')
    plot_clusters_3d(feats_df, selected, kmeans_model)

    print('✅ Listo. Benchmarks seleccionados y visualización generados.')
