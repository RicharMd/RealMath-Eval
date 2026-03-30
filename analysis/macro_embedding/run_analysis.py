import json
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from sentence_transformers import SentenceTransformer
import umap
import hdbscan
import os
import torch
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.mixture import GaussianMixture
from scipy.cluster.hierarchy import linkage, leaves_list

# Default model: HuggingFace ID (auto-downloads if not cached)
# Override with --model-path for local path, e.g. /path/to/Qwen-Qwen3-Embedding-8B
DEFAULT_MODEL = "Qwen/Qwen3-Embedding-8B"
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_DATA_DIR = _SCRIPT_DIR.parent / "data" / "error_segment_bundle"
HUMAN_DATA_PATH = "human_error_segments.jsonl"
LLM_DATA_PATH = "llm_error_segments.jsonl"
STATS_OUTPUT_FILE = "clustering_statistics_summary.txt"

def load_data(filepath, source_label):
    data = []
    if not os.path.exists(filepath): return data
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                if item.get('status') == 'KEEP' or 'status' not in item:
                    data.append({
                        'text': item.get('segment_text', item.get('text', '')),
                        'source': source_label
                    })
            except: continue
    return data

def plot_heatmap(embeddings, title, filename):
    print(f"   Generating Heatmap for {title}...")
    dist_matrix = cosine_distances(embeddings)
    Z = linkage(dist_matrix, method='ward')
    sort_idx = leaves_list(Z)
    sorted_matrix = dist_matrix[sort_idx][:, sort_idx]
    
    plt.figure(figsize=(8, 8))
    sns.heatmap(sorted_matrix, cmap="viridis_r", xticklabels=False, yticklabels=False, square=True, cbar_kws={'label': 'Cosine Distance'})
    plt.title(f'{title}\nPairwise Distance Matrix', fontsize=14)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

def plot_silhouette(embeddings, labels, title, filename):
    print(f"   Generating Silhouette Plot for {title}...")
    mask = labels != -1
    if np.sum(mask) < 2: return None
    X_clustered = embeddings[mask]
    labels_clustered = labels[mask]
    n_clusters = len(set(labels_clustered))
    if n_clusters < 2: return None

    silhouette_avg = silhouette_score(X_clustered, labels_clustered, metric='cosine')
    sample_silhouette_values = silhouette_samples(X_clustered, labels_clustered, metric='cosine')

    fig, ax1 = plt.subplots(1, 1)
    fig.set_size_inches(10, 7)
    ax1.set_ylim([0, len(X_clustered) + (n_clusters + 1) * 10])
    ax1.set_xlim([-0.1, 1])

    y_lower = 10
    for i in range(n_clusters):
        ith_cluster_silhouette_values = sample_silhouette_values[labels_clustered == i]
        ith_cluster_silhouette_values.sort()
        size_cluster_i = ith_cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster_i
        color = cm.nipy_spectral(float(i) / n_clusters)
        ax1.fill_betweenx(np.arange(y_lower, y_upper), 0, ith_cluster_silhouette_values, facecolor=color, edgecolor=color, alpha=0.7)
        ax1.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))
        y_lower = y_upper + 10

    ax1.set_title(f"{title}\nAvg Silhouette Score: {silhouette_avg:.4f}", fontsize=14)
    ax1.set_xlabel("Silhouette Coefficient Values")
    ax1.set_ylabel("Cluster Label")
    ax1.axvline(x=silhouette_avg, color="red", linestyle="--")
    ax1.set_yticks([])
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()
    return silhouette_avg

def run_gmm_analysis(embeddings, max_k=30):
    bics = []
    k_values = range(2, max_k + 1)
    for k in k_values:
        # Use diagonal covariance to handle high dim better with few samples
        gmm = GaussianMixture(n_components=k, covariance_type='diag', random_state=42)
        gmm.fit(embeddings)
        bics.append(gmm.bic(embeddings))
    
    # Find optimal K (min BIC)
    optimal_k = k_values[np.argmin(bics)]
    return k_values, bics, optimal_k

def _resolve_model_path(model_path: str) -> str:
    """Resolve model path: use local if exists, else treat as HuggingFace ID (will download)."""
    if os.path.exists(model_path):
        print(f"Using local model: {model_path}")
        return model_path
    # Likely HuggingFace ID (e.g. Qwen/Qwen3-Embedding-8B)
    if "/" in model_path and not os.path.isabs(model_path):
        print(f"Model not found locally. Will download from HuggingFace: {model_path}")
        print("  (First run may take a few minutes; model is cached for later runs)")
        return model_path
    raise FileNotFoundError(
        f"Model not found: {model_path}\n"
        f"  - Use a local path (e.g. /path/to/Qwen-Qwen3-Embedding-8B), or\n"
        f"  - Use HuggingFace ID (e.g. {DEFAULT_MODEL}) to auto-download"
    )


def main():
    parser = argparse.ArgumentParser(description="Macro embedding analysis (Section 5.1)")
    parser.add_argument(
        "--model-path",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Path to embedding model or HuggingFace ID (default: {DEFAULT_MODEL}). "
             "If path does not exist, downloads from HuggingFace.",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(_DEFAULT_DATA_DIR),
        help="Directory containing human_error_segments.jsonl and llm_error_segments.jsonl (default: analysis/data/error_segment_bundle)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory for output figures and stats (default: current dir)",
    )
    args = parser.parse_args()

    human_path = os.path.join(args.data_dir, HUMAN_DATA_PATH)
    llm_path = os.path.join(args.data_dir, LLM_DATA_PATH)

    print("1. Loading Data...")
    human_data = load_data(human_path, 'Human')
    llm_data = load_data(llm_path, 'LLM')
    
    human_texts = [d['text'] for d in human_data]
    llm_texts = [d['text'] for d in llm_data]
    
    print("2. Generating High-Dim Embeddings...")
    model_path = _resolve_model_path(args.model_path)
    model_kwargs = {"trust_remote_code": True}
    if torch.cuda.is_available():
        model_kwargs["device"] = "cuda"
        model_kwargs["model_kwargs"] = {"torch_dtype": torch.float16}
    
    model = SentenceTransformer(model_path, **model_kwargs)
    model.max_seq_length = 8192
    
    emb_human = model.encode(human_texts, normalize_embeddings=True, show_progress_bar=True, batch_size=8)
    emb_llm = model.encode(llm_texts, normalize_embeddings=True, show_progress_bar=True, batch_size=8)

    stats = {}

    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)

    # --- Exp 1: Heatmap ---
    print("\n--- Exp 1: Distance Heatmaps ---")
    plot_heatmap(emb_human, "Human Errors", os.path.join(out_dir, "exp1_heatmap_human.png"))
    plot_heatmap(emb_llm, "LLM Errors", os.path.join(out_dir, "exp1_heatmap_llm.png"))

    # --- Exp 2: Density ---
    print("\n--- Exp 2: Local Density ---")
    def get_nn_dist(emb):
        nbrs = NearestNeighbors(n_neighbors=6, metric='cosine').fit(emb)
        dists, _ = nbrs.kneighbors(emb)
        return np.mean(dists[:, 1:], axis=1)

    dist_human = get_nn_dist(emb_human)
    dist_llm = get_nn_dist(emb_llm)
    
    stats['avg_nn_dist_human'] = np.mean(dist_human)
    stats['avg_nn_dist_llm'] = np.mean(dist_llm)
    
    plt.figure(figsize=(10, 6))
    sns.kdeplot(dist_human, fill=True, label=f'Human (Avg: {stats["avg_nn_dist_human"]:.4f})', color='#1f77b4', alpha=0.3)
    sns.kdeplot(dist_llm, fill=True, label=f'LLM (Avg: {stats["avg_nn_dist_llm"]:.4f})', color='#d62728', alpha=0.3)
    plt.title('Local Density Distribution (Mean NN Distance)', fontsize=14)
    plt.xlabel('Cosine Distance')
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'exp2_density.png'), dpi=300)
    plt.close()

    # --- Exp 3: PCA ---
    print("\n--- Exp 3: PCA Intrinsic Dimension ---")
    pca_human = PCA().fit(emb_human)
    pca_llm = PCA().fit(emb_llm)
    
    stats['total_variance_human'] = np.trace(np.cov(emb_human.T))
    stats['total_variance_llm'] = np.trace(np.cov(emb_llm.T))
    stats['pca_top10_var_human'] = np.sum(pca_human.explained_variance_ratio_[:10])
    stats['pca_top10_var_llm'] = np.sum(pca_llm.explained_variance_ratio_[:10])

    plt.figure(figsize=(10, 6))
    plt.plot(np.cumsum(pca_human.explained_variance_ratio_[:50]), label='Human', color='#1f77b4', linewidth=2)
    plt.plot(np.cumsum(pca_llm.explained_variance_ratio_[:50]), label='LLM', color='#d62728', linewidth=2)
    plt.title('Cumulative Explained Variance (PCA)', fontsize=14)
    plt.xlabel('Components')
    plt.ylabel('Variance Explained')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'exp3_pca.png'), dpi=300)
    plt.close()

    # --- Exp 4: Silhouette ---
    print("\n--- Exp 4: Silhouette Analysis ---")
    def get_cluster_labels(embeddings):
        reducer = umap.UMAP(n_neighbors=15, n_components=10, metric='cosine', min_dist=0.0, random_state=42)
        emb_reduced = reducer.fit_transform(embeddings)
        clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=3, metric='euclidean')
        return clusterer.fit_predict(emb_reduced)

    print("   Clustering Human Data...")
    labels_human = get_cluster_labels(emb_human)
    print("   Clustering LLM Data...")
    labels_llm = get_cluster_labels(emb_llm)
    
    stats['noise_ratio_human'] = list(labels_human).count(-1) / len(labels_human)
    stats['noise_ratio_llm'] = list(labels_llm).count(-1) / len(labels_llm)
    stats['n_clusters_human'] = len(set(labels_human)) - (1 if -1 in labels_human else 0)
    stats['n_clusters_llm'] = len(set(labels_llm)) - (1 if -1 in labels_llm else 0)
    stats['silhouette_score_human'] = plot_silhouette(emb_human, labels_human, "Human Error Clusters", os.path.join(out_dir, "exp4_silhouette_human.png"))
    stats['silhouette_score_llm'] = plot_silhouette(emb_llm, labels_llm, "LLM Error Clusters", os.path.join(out_dir, "exp4_silhouette_llm.png"))

    # --- Exp 5: GMM BIC (New!) ---
    print("\n--- Exp 5: GMM BIC Analysis ---")
    # Reduce to 50 dims for stable GMM
    pca_50 = PCA(n_components=50, random_state=42)
    emb_human_50 = pca_50.fit_transform(emb_human)
    emb_llm_50 = pca_50.fit_transform(emb_llm)

    k_vals, bic_human, opt_k_human = run_gmm_analysis(emb_human_50)
    k_vals, bic_llm, opt_k_llm = run_gmm_analysis(emb_llm_50)
    
    stats['gmm_optimal_k_human'] = opt_k_human
    stats['gmm_optimal_k_llm'] = opt_k_llm
    stats['gmm_min_bic_human'] = min(bic_human)
    stats['gmm_min_bic_llm'] = min(bic_llm)

    plt.figure(figsize=(10, 6))
    plt.plot(k_vals, bic_human, marker='o', label=f'Human (Opt K={opt_k_human})', color='#1f77b4')
    plt.plot(k_vals, bic_llm, marker='o', label=f'LLM (Opt K={opt_k_llm})', color='#d62728')
    plt.title('GMM Model Selection (BIC Score)\n(Lower is better, sharper elbow = clearer structure)', fontsize=14)
    plt.xlabel('Number of Components (K)')
    plt.ylabel('BIC Score')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(os.path.join(out_dir, 'exp5_gmm_bic.png'), dpi=300)
    plt.close()

    # --- Save Statistics ---
    stats_path = os.path.join(out_dir, STATS_OUTPUT_FILE)
    print(f"\n--- Saving Statistics to {stats_path} ---")
    with open(stats_path, "w") as f:
        f.write("=== Error Pattern Clustering Statistics ===\n\n")
        f.write("1. Local Density (Lower = More Convergent)\n")
        f.write(f"   Avg NN Dist (Human): {stats['avg_nn_dist_human']:.4f}\n")
        f.write(f"   Avg NN Dist (LLM):   {stats['avg_nn_dist_llm']:.4f}\n")
        f.write(f"   Ratio (LLM/Human):   {stats['avg_nn_dist_llm']/stats['avg_nn_dist_human']:.2f}\n\n")
        f.write("2. Global Variance & Dimensionality\n")
        f.write(f"   Total Variance (Human): {stats['total_variance_human']:.4f}\n")
        f.write(f"   Total Variance (LLM):   {stats['total_variance_llm']:.4f}\n")
        f.write(f"   PCA Top-10 Explained Var (Human): {stats['pca_top10_var_human']:.2%}\n")
        f.write(f"   PCA Top-10 Explained Var (LLM):   {stats['pca_top10_var_llm']:.2%}\n\n")
        f.write("3. Clustering Quality (HDBSCAN)\n")
        f.write(f"   Noise Ratio (Human): {stats['noise_ratio_human']:.2%}\n")
        f.write(f"   Noise Ratio (LLM):   {stats['noise_ratio_llm']:.2%}\n")
        f.write(f"   Silhouette Score (Human): {stats['silhouette_score_human'] if stats['silhouette_score_human'] else 'N/A'}\n")
        f.write(f"   Silhouette Score (LLM):   {stats['silhouette_score_llm'] if stats['silhouette_score_llm'] else 'N/A'}\n\n")
        f.write("4. Structural Clarity (GMM BIC)\n")
        f.write(f"   Optimal K (Human): {stats['gmm_optimal_k_human']}\n")
        f.write(f"   Optimal K (LLM):   {stats['gmm_optimal_k_llm']}\n")
        f.write(f"   Min BIC (Human):   {stats['gmm_min_bic_human']:.2f}\n")
        f.write(f"   Min BIC (LLM):     {stats['gmm_min_bic_llm']:.2f}\n")

    print("Done! All 5 experiments completed.")

if __name__ == "__main__":
    main()
