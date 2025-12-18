#!/usr/bin/env python3
"""
SpaGCN method for spatially variable gene detection.

SpaGCN integrates gene expression, spatial location and histology to identify spatial domains
and spatially variable genes using graph convolutional network.

Omnibenchmark standard arguments:
  --output_dir: Directory where outputs will be saved
  --name: Dataset name
  --data.dataset: Input dataset h5ad file
"""

import anndata as ad
import SpaGCN as spg
import pandas as pd
import numpy as np
import scanpy as sc
import random
import torch
import argparse
import os

# Parse command line arguments
parser = argparse.ArgumentParser(description='SpaGCN method for spatially variable gene detection')
parser.add_argument('--output_dir', type=str, required=True,
                    help='Output directory where files will be saved')
parser.add_argument('--name', type=str, required=True,
                    help='Name of the dataset')
parser.add_argument('--data.dataset', type=str, required=True,
                    help='Path to input dataset h5ad file')

args = parser.parse_args()

# Get input using getattr for dotted arguments
input_data_path = getattr(args, 'data.dataset')

# Construct output path
os.makedirs(args.output_dir, exist_ok=True)
output_path = os.path.join(args.output_dir, f"{args.name}.predictions.h5ad")

print(f'Reading input data from: {input_data_path}', flush=True)
adata = ad.read_h5ad(input_data_path)

# Run normalization
adata.X = adata.layers['counts'].copy()
sc.pp.normalize_total(adata=adata)
sc.pp.log1p(adata)

print('Running SpaGCN', flush=True)
random_seed = 100

# Set seed
random.seed(random_seed)
torch.manual_seed(random_seed)
np.random.seed(random_seed)

p = 0.5
min_in_group_fraction = 0
min_in_out_group_ratio = 0
min_fold_change = 0

adj = spg.calculate_adj_matrix(
    x=adata.obsm["spatial"][:, 0],
    y=adata.obsm["spatial"][:, 1],
    histology=False
)
l = spg.search_l(p, adj, start=0.01, end=1000, tol=0.01, max_run=100)

clf = spg.SpaGCN()
clf.set_l(l)

# Run
clf.train(
    adata,
    adj,
    init_spa=True,
    init="louvain",
    res=0.5,
    tol=5e-3,
    lr=0.05,
    max_epochs=200,
)

y_pred, prob = clf.predict()
adata.obs["pred"] = y_pred
de_genes_all = list()
n_clusters = len(adata.obs["pred"].unique())

# Identify DE genes
for target in range(n_clusters):
    print(f"target: {target}")
    start, end = np.quantile(adj[adj != 0], q=0.001), np.quantile(
        adj[adj != 0], q=0.1
    )
    r = spg.search_radius(
        target_cluster=target,
        cell_id=adata.obs.index.tolist(),
        x=adata.obsm["spatial"][:, 0],
        y=adata.obsm["spatial"][:, 1],
        pred=adata.obs["pred"].tolist(),
        start=start,
        end=end,
        num_min=10,
        num_max=14,
        max_run=100,
    )

    try:
        nbr_domians = spg.find_neighbor_clusters(
            target_cluster=target,
            cell_id=adata.obs.index.tolist(),
            x=adata.obsm["spatial"][:, 0],
            y=adata.obsm["spatial"][:, 1],
            pred=adata.obs["pred"].tolist(),
            radius=r,
            ratio=0,
        )

        de_genes_info = spg.rank_genes_groups(
            input_adata=adata,
            target_cluster=target,
            nbr_list=nbr_domians,
            label_col="pred",
            adj_nbr=True,
            log=True,
        )
        de_genes_all.append(de_genes_info)
    except (RuntimeError, TypeError, NameError):
        pass

if len(de_genes_all) == 0:
    df = adata.var
    df['pvals_adj'] = np.random.random(adata.n_vars)
else:
    df_res = pd.concat(de_genes_all)
    df_res = df_res.groupby(["genes"]).min()
    df_res = df_res.loc[adata.var_names]
    df = pd.concat([df_res, adata.var], axis=1)

# Format output
df = df.loc[adata.var_names][['pvals_adj']]
df = df.reset_index()
df.columns = ['feature_id', 'pred_spatial_var_score']

# Reverse it to make sure a bigger score represents a higher spatial variation
df['pred_spatial_var_score'] = -np.log10(df['pred_spatial_var_score'])

output = ad.AnnData(
    var=df,
    uns={
        'dataset_id': adata.uns['dataset_id'],
        'method_id': 'spagcn'
    }
)

print(f"Writing output to: {output_path}", flush=True)
output.write_h5ad(output_path, compression='gzip')
print("Done!", flush=True)
