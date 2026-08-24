import pandas as pd, numpy as np, time, os, sys, pickle

SRC = os.path.expanduser("~/mnt/graphrag/data/csv/BPI_Challenge_2019.csv")
OUT = os.path.expanduser("~/work")

usecols = ["case concept:name","case Purchasing Document","case Company",
           "case Spend area text","case Sub spend area text","case Vendor","case Name",
           "case Item Type","case Item Category","case Spend classification text",
           "case GR-Based Inv. Verif.","case Goods Receipt","case Document Type",
           "case Purch. Doc. Category name","case Item",
           "event org:resource","event concept:name",
           "event Cumulative net worth (EUR)","event time:timestamp"]

ren = {"case concept:name":"cID","case Purchasing Document":"PO","case Company":"company",
       "case Spend area text":"spend_area","case Sub spend area text":"sub_spend_area",
       "case Vendor":"vendor","case Name":"vendor_name","case Item Type":"item_type",
       "case Item Category":"item_cat","case Spend classification text":"spend_class",
       "case GR-Based Inv. Verif.":"gr_based_iv","case Goods Receipt":"gr_flag",
       "case Document Type":"doc_type","case Purch. Doc. Category name":"purdoc_cat",
       "case Item":"item","event org:resource":"resource","event concept:name":"activity",
       "event Cumulative net worth (EUR)":"netw","event time:timestamp":"ts"}

static_cols = ["PO","company","spend_area","sub_spend_area","vendor","vendor_name",
               "item_type","item_cat","spend_class","gr_based_iv","gr_flag","doc_type",
               "purdoc_cat","item"]

static_parts, act_parts, agg_parts = [], [], []
res_pairs = set()
t0 = time.time(); n = 0
for chunk in pd.read_csv(SRC, usecols=usecols, chunksize=400_000, dtype=str, encoding="latin-1",
                         low_memory=False):
    chunk = chunk.rename(columns=ren)
    n += len(chunk)
    static_parts.append(chunk.drop_duplicates("cID")[["cID"]+static_cols])
    act_parts.append(chunk.groupby(["cID","activity"]).size())
    ts = pd.to_datetime(chunk["ts"], format="%d-%m-%Y %H:%M:%S.%f", errors="coerce")
    nw = pd.to_numeric(chunk["netw"], errors="coerce")
    g = pd.DataFrame({"cID":chunk["cID"].values,"ts":ts.values,"nw":nw.values})
    agg_parts.append(g.groupby("cID").agg(ts_min=("ts","min"), ts_max=("ts","max"),
                                          nw_max=("nw","max"), nw_min=("nw","min"),
                                          n_ev=("ts","size")))
    res_pairs.update(map(tuple, chunk[["cID","resource"]].drop_duplicates().values))
    print(f"{n} rows  {time.time()-t0:.0f}s", flush=True)

print("combining", flush=True)
static = pd.concat(static_parts).drop_duplicates("cID").set_index("cID")
acts = pd.concat(act_parts).groupby(level=[0,1]).sum().unstack(fill_value=0)
agg = pd.concat(agg_parts).groupby(level=0).agg(ts_min=("ts_min","min"), ts_max=("ts_max","max"),
        nw_max=("nw_max","max"), nw_min=("nw_min","min"), n_ev=("n_ev","sum"))

rp = pd.DataFrame(list(res_pairs), columns=["cID","resource"])
rp["is_batch"] = rp["resource"].str.startswith("batch")
rp["is_none"]  = rp["resource"].eq("NONE")
rstat = rp.groupby("cID").agg(n_res=("resource","nunique"),
                              n_batch=("is_batch","sum"), n_human=("is_none","size"))
rstat["n_human"] = rp[(~rp.is_batch)&(~rp.is_none)].groupby("cID")["resource"].nunique().reindex(rstat.index).fillna(0).astype(int)

prof = static.join(agg).join(acts).join(rstat)
#parquet skipped
prof.to_csv(os.path.join(OUT,"case_profile.csv"))
print("DONE", prof.shape, f"{time.time()-t0:.0f}s", flush=True)
print(list(prof.columns), flush=True)
