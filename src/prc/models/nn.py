"""Neural tabular model: MLP with categorical entity embeddings (M-013).

Same design matrix as the GBM (prc.models.gbm.design: numeric + OOF target encodings + categoricals) and the
same Jan/Jul-2025 hold-out protocol. Numeric inputs: per-feature quantile normalisation fitted on the training
rows, NaN -> 0 plus a missing indicator. Categoricals: one embedding table each; categories seen in fewer than
`min_count` training rows map to a shared 'rare' index. Loss: MSE on y / y_scale (RMSE metric).

  python -m prc.models.nn validate --config configs/nn.yaml
"""
import argparse
import json
import time

import numpy as np
import pandas as pd
import torch
from torch import nn

from prc import validate as V
from prc.models import gbm
from prc.paths import MODELS


class TabMLP(nn.Module):
    def __init__(self, n_num, cards, emb_dim, hidden, dropout):
        super().__init__()
        self.embs = nn.ModuleList([nn.Embedding(c, min(emb_dim, max(2, c // 2))) for c in cards])
        d = n_num + sum(e.embedding_dim for e in self.embs)
        layers = []
        for h in hidden:
            layers += [nn.Linear(d, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(dropout)]
            d = h
        self.mlp = nn.Sequential(*layers)
        self.head = nn.Linear(d, 1)

    def forward(self, xn, xc):
        z = [xn] + [e(xc[:, i]) for i, e in enumerate(self.embs)]
        return self.head(self.mlp(torch.cat(z, dim=1))).squeeze(1)


class Encoder:
    """Fit on training rows only; transform any rows (train/serve parity)."""

    def __init__(self, num_cols, cat_cols, min_count, n_quantiles=1000):
        self.num_cols, self.cat_cols, self.min_count, self.nq = num_cols, cat_cols, min_count, n_quantiles

    def fit(self, X):
        qs = np.linspace(0, 1, self.nq)
        self.q = {c: np.unique(np.nanquantile(X[c].to_numpy(float), qs)) for c in self.num_cols
                  if np.isfinite(X[c].to_numpy(float)).any()}
        self.maps = {}
        for c in self.cat_cols:
            vc = X[c].astype(str).value_counts()
            keep = vc[vc >= self.min_count].index
            self.maps[c] = {k: i + 1 for i, k in enumerate(keep)}  # 0 = rare/unseen
        return self

    def transform(self, X):
        cols = []
        for c in self.num_cols:
            v = X[c].to_numpy(float)
            miss = ~np.isfinite(v)
            if c in self.q and len(self.q[c]) > 1:
                z = np.interp(np.where(miss, 0, v), self.q[c], np.linspace(-1, 1, len(self.q[c])))
            else:
                z = np.zeros_like(v)
            cols += [np.where(miss, 0, z), miss.astype(float)]
        xn = np.stack(cols, axis=1).astype(np.float32)
        xc = np.stack([X[c].astype(str).map(self.maps[c]).fillna(0).to_numpy(np.int64) for c in self.cat_cols], axis=1)
        return xn, xc

    @property
    def cards(self):
        return [len(self.maps[c]) + 1 for c in self.cat_cols]


def train_predict(Xtr, ytr, Xte_list, cfg, seed):
    p = cfg["nn"]
    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(p.get("threads", 4))
    num_cols = [c for c in Xtr.columns if c not in cfg["categorical"]]
    enc = Encoder(num_cols, cfg["categorical"], p["min_count"]).fit(Xtr)
    xn, xc = enc.transform(Xtr)
    scale = p["y_scale"]
    y = torch.tensor(ytr / scale, dtype=torch.float32)
    xn, xc = torch.from_numpy(xn), torch.from_numpy(xc)
    model = TabMLP(xn.shape[1], enc.cards, p["emb_dim"], p["hidden"], p["dropout"])
    opt = torch.optim.AdamW(model.parameters(), lr=p["lr"], weight_decay=p["weight_decay"])
    n, bs = len(y), p["batch_size"]
    steps = p["epochs"] * ((n + bs - 1) // bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=p["lr"], total_steps=steps)
    g = torch.Generator().manual_seed(seed)
    for ep in range(p["epochs"]):
        model.train()
        t0, tot = time.time(), 0.0
        for idx in torch.randperm(n, generator=g).split(bs):
            opt.zero_grad()
            loss = nn.functional.mse_loss(model(xn[idx], xc[idx]), y[idx])
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), p["clip_grad"])
            opt.step()
            sched.step()
            tot += loss.item() * len(idx)
        print(f"    epoch {ep + 1}/{p['epochs']} train_rmse={np.sqrt(tot / n) * scale:.1f} ({time.time() - t0:.0f}s)", flush=True)
    model.eval()
    outs = []
    with torch.no_grad():
        for X in Xte_list:
            tn, tc = enc.transform(X)
            tn, tc = torch.from_numpy(tn), torch.from_numpy(tc)
            outs.append(torch.cat([model(tn[i:i + 65536], tc[i:i + 65536]) for i in range(0, len(tn), 65536)]).numpy() * scale)
    return outs


def validate(cfg, seeds=None):
    df = gbm.load_frame(cfg.get("weather", False), tuple(cfg.get("extra_tables", [])))
    tr_all = (df.ds == "train").to_numpy()
    seeds = seeds or [cfg["seed"]]
    results, per_seed = {}, {}
    for fold, trm, vam in V.folds(df.month.where(tr_all)):
        trm, vam = trm & tr_all, vam & tr_all
        X = gbm.design(df, cfg, trm)
        preds = []
        for s in seeds:
            t0 = time.time()
            (p,) = train_predict(X[trm], df.y[trm].to_numpy(float), [X[vam]], cfg, s)
            preds.append(p)
            per_seed.setdefault(fold, []).append(V.rmse(df.y[vam], p))
            print(f"  {fold} seed={s} rmse={per_seed[fold][-1]:.2f} ({time.time() - t0:.0f}s)", flush=True)
        va = df.loc[vam, gbm.EVAL_COLS].copy()
        va["pred"] = np.mean(preds, axis=0)
        results[fold] = va
    meta = {"data": V.data_version(), "git": V.git_sha(), "config": cfg["config_hash"], "seeds": seeds,
            "per_seed_rmse": {k: [round(v, 2) for v in vs] for k, vs in per_seed.items()}, "nn": json.dumps(cfg["nn"])}
    V.write_report(cfg["exp_id"], V.report_md(cfg["exp_id"], cfg["title"], results, meta))
    oof_dir = MODELS / "oof"
    oof_dir.mkdir(parents=True, exist_ok=True)
    for name, va in results.items():
        va.to_parquet(oof_dir / f"{cfg['exp_id']}_{name}.parquet")
    r = {k: V.rmse(v.y, v.pred) for k, v in results.items()}
    r["combined"] = V.rmse(pd.concat(results.values()).y, pd.concat(results.values()).pred)
    print(cfg["exp_id"], {k: round(v, 2) for k, v in r.items()})
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate"])
    ap.add_argument("--config", default="configs/nn.yaml")
    ap.add_argument("--seeds", type=int, nargs="*")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--exp-id")
    a = ap.parse_args()
    cfg = gbm.load_config(a.config)
    if a.epochs:
        cfg["nn"]["epochs"] = a.epochs
    if a.exp_id:
        cfg["exp_id"] = a.exp_id
    validate(cfg, a.seeds)
