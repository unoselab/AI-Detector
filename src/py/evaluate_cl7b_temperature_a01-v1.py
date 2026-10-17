#!/usr/bin/env python3
"""A-01-v4 frozen CL-7B SVM+AST temperature evaluation.

Inputs: read-only A-01 analysis-v4 matched CSVs, historical 450-pair test,
       fitted SVM, original AST parser and CodeT5+ embedding implementation.
Outputs: separate run-x-a-02-v1 directory, no input mutation.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

TAGS = ('t02', 't04', 't06')
EXPERIMENT = 'codellama-7b_4500_complexity_stratified_maxlen2048'
DATASET = 'codesearchnet_codellama-7b_python_merged_4500'
MODEL_FILE = 'tuned_models_codesearchnet_codellama-7b_4500_complexity_stratified_maxlen2048_svm_20260530_202138.pkl'
MODEL_SHA = 'a7425af490022045d40da3aa660a38bfd2aabc22a27dd70a4f8ee5ebf1a61ce7'
MODEL_KEY = DATASET + 'ast_'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def codehash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def write_json(path, item):
    Path(path).write_text(json.dumps(item, sort_keys=True, indent=2, allow_nan=False) + '\n')


def arguments():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo-root', type=Path, required=True)
    p.add_argument('--analysis-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--mode', choices=('self-test','preflight','run','verify'), default='preflight')
    p.add_argument('--model-file', type=Path)
    p.add_argument('--device', default='cuda')
    p.add_argument('--batch-size', type=int, default=16)
    p.add_argument('--bootstrap', type=int, default=20000)
    p.add_argument('--stat-seed', type=int, default=20260723)
    p.add_argument('--resume', action='store_true')
    return p.parse_args()


def paths(a):
    r = a.repo_root.resolve()
    return {
        'test': r/'src/ml_embeddings/data_codesearchnet/splits'/EXPERIMENT/DATASET/'test_.csv',
        'manifest': r/'src/ml_embeddings/data_codesearchnet/splits'/EXPERIMENT/'complexity_stratified_pair_manifest.csv',
        'pickle': (a.model_file or r/'src/ml_embeddings/data_codesearchnet/models'/EXPERIMENT/MODEL_FILE).resolve(),
        'ast': r/'src/code-analyzer-tree-sitter/tree_sitter_ast_python.py',
        'grammar': r/'src/code-analyzer-tree-sitter/build/my-languages.so',
        'emb': r/'src/ml_embeddings/generate_embeddings.py',
    }


def preflight(a, p):
    require(sys.version_info[:2] == (3, 11), 'Python 3.11 required for historical embedding pipeline')
    require(a.bootstrap > 0 and a.batch_size > 0, 'Invalid bootstrap/batch-size')
    for key, path in p.items():
        require(path.is_file(), f'Missing {key}: {path}')
    require(digest(p['pickle']) == MODEL_SHA, 'Frozen fitted SVM hash mismatch')
    d = a.analysis_dir
    rev = json.loads((d/'full_review.json').read_text())
    require(rev['phase'] == 'full' and rev['complete_triplets'] == 2000, 'Incomplete A-01 full review')
    n = rev['common_ast_valid_triplets']
    require(n == 814, f'Unexpected A-01-v4 cohort: {n}; requires explicit review')
    require(rev['primary_machine_learning_metrics_computed'] is False, 'Not an input-only review')
    meta = pd.read_csv(d/'matched_prompt_metadata.csv', dtype={'prompt_sha256':str, 'human_sha256':str})
    require(len(meta) == n and meta.line_no.is_unique and meta.prompt_sha256.is_unique, 'Metadata IDs mismatch')
    ids = ['line'+str(x) for x in meta.line_no]
    frames = {}
    hashes = {'full_review':digest(d/'full_review.json'), 'metadata':digest(d/'matched_prompt_metadata.csv')}
    human_reference = None
    for tag in TAGS:
        f = d/f'matched_{tag}_pairs.csv'
        data = pd.read_csv(f, keep_default_na=False)
        require(len(data) == n*2 and data.idx.is_unique, f'{tag} row/ID mismatch')
        indexed = data.set_index('idx')
        require(set(indexed.index) == {pid+suf for pid in ids for suf in ('_human','_lm')}, f'{tag} unmatched IDs')
        require(all(indexed.at[pid+'_human','label'] == 'human' and indexed.at[pid+'_lm','label'] == 'lm' for pid in ids), f'{tag} label mismatch')
        hc = [str(indexed.at[pid+'_human','code']) for pid in ids]
        ac = [str(indexed.at[pid+'_lm','code']) for pid in ids]
        require(all(hc) and all(ac), f'{tag} empty source')
        if human_reference is None:
            human_reference = hc
        else:
            require(hc == human_reference, f'{tag} HWC drift')
        # Metadata records continuation hashes rather than full AGC code hashes;
        # AST input is therefore verified by ID correspondence and file SHA-256.
        frames[tag] = indexed
        hashes[tag] = digest(f)
    test = pd.read_csv(p['test'],keep_default_na=False)
    manifest = pd.read_csv(p['manifest'])
    require(len(test)==900 and len(manifest)==4500, 'Historical test/manifest sizes changed')
    require(test.idx.is_unique and {'code','ast','actual label'} <= set(test.columns), 'Historical test malformed')
    require(all('ast_'+str(k) in test.columns for k in range(256)), 'Missing historical AST embeddings')
    require(len(set(manifest.loc[manifest.split=='test','pair_id'])) == 450, 'Historical test split mismatch')
    hashes['historical_test']=digest(p['test'])
    hashes['historical_manifest']=digest(p['manifest'])
    hashes['model']=digest(p['pickle'])
    hashes['ast']=digest(p['ast'])
    hashes['grammar']=digest(p['grammar'])
    hashes['embedding_source']=digest(p['emb'])
    print(f'[PREFLIGHT] PASS 2000 completed prompts; {n} common-valid matched pairs per temperature; baseline 450 pairs')
    return test,meta,ids,frames,human_reference,hashes


def ast_sequences(p, codes):
    from tree_sitter import Language, Parser
    sys.path.insert(0,str(p['ast'].parent))
    from tree_sitter_ast_python import F
    parser=Parser()
    parser.set_language(Language(str(p['grammar']),'python'))
    result=[]
    for code in codes:
        raw=code.encode('utf-8')
        tree=parser.parse(raw)
        require(not tree.root_node.has_error,'Tree-sitter parse failure for matched Python source')
        result.append(' '.join(F(tree.root_node,raw)))
    return result


def embedding_helper(path):
    spec=importlib.util.spec_from_file_location('frozen_codet5p_embedding',str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.MODEL_ID=='Salesforce/codet5p-110m-embedding' and module.EMBED_DIM==256,'Encoder changed')
    return module


def classifier(path):
    # Only unpickle the trusted, SHA-256-verified historical classifier.
    with path.open('rb') as f:
        models=pickle.load(f)
    require(MODEL_KEY in models, 'Missing AST SVM model')
    x=models[MODEL_KEY]
    clf=x[0] if isinstance(x,(tuple,list)) else x
    require(clf.n_features_in_==256 and list(clf.classes_)==[0,1],'Classifier shape/labels changed')
    return clf


def scores(clf, features):
    x=np.asarray(features,dtype=np.float64)
    prediction=clf.predict(x)
    if hasattr(clf,'predict_proba'):
        try:
            return np.asarray(clf.predict_proba(x)[:,list(clf.classes_).index(1)],float),prediction,'proba'
        except Exception:
            pass
    return np.asarray(clf.decision_function(x),float).ravel(),prediction,'decision'


def auc(human,agc):
    n=len(human)
    vals=np.r_[human,agc]
    labels=np.r_[np.ones(n,dtype=int),np.zeros(n,dtype=int)]
    return float(roc_auc_score(labels,vals))


def bootstrap(human,agcs,repeats,seed):
    rng=np.random.default_rng(seed)
    n=len(human)
    samples=np.empty((repeats,6))
    for i in range(repeats):
        ix=rng.integers(0,n,n)
        x=[auc(human[ix],agcs[tag][ix]) for tag in TAGS]
        samples[i]=[*x,x[1]-x[0],x[2]-x[0],x[2]-x[1]]
        if (i+1)%5000==0:
            print(f'[BOOTSTRAP] {i+1}/{repeats}',flush=True)
    return samples


def run(a,p,cohort):
    test,meta,ids,frames,human_codes,hashes=cohort
    out=a.output_dir
    if out.exists() and not a.resume:
        raise RuntimeError(f'Output already exists: {out}; set RESUME=1 for same inputs')
    out.mkdir(parents=True,exist_ok=True)
    fingerprint=codehash(json.dumps(hashes,sort_keys=True))
    provenance=out/'embedding_provenance.json'
    cache=out/'embeddings.npz'
    clf=classifier(p['pickle'])
    reference_features=test[['ast_'+str(i) for i in range(256)]].to_numpy()
    base_scores,_,mode=scores(clf,reference_features)
    base=roc_auc_score(test['actual label'].astype(int),base_scores)
    require(abs(base-0.7950345679012345)<0.000051,'Historical 450-pair baseline AUROC mismatch')
    print(f'[BASELINE] cached 450-pair AUROC={base:.8f}')
    if a.resume and cache.is_file() and provenance.is_file():
        old=json.loads(provenance.read_text())
        require(old['fingerprint']==fingerprint and old['cache_sha256']==digest(cache),'Cache provenance mismatch')
        with np.load(cache) as f:
            embed={k:f[k].copy() for k in f.files}
        require(embed['reference'].shape==(900,256) and all(embed[k].shape==(len(ids),256) for k in ('hwc',*TAGS)), 'Cache shape mismatch')
        print('[EMBED] Verified cached embeddings')
    else:
        import torch
        require(a.device!='cuda' or torch.cuda.is_available(),'CUDA not available')
        helper=embedding_helper(p['emb'])
        sequences={'reference':ast_sequences(p,test.code.astype(str).tolist()),'hwc':ast_sequences(p,human_codes)}
        require(sequences['reference']==test.ast.astype(str).tolist(),'Historical AST representation drift')
        for tag in TAGS:
            sequences[tag]=ast_sequences(p,[str(frames[tag].at[pid+'_lm','code']) for pid in ids])
        tokenizer,model=helper.load_model(a.device)
        embed={name:helper.embed_batch(values,tokenizer,model,a.device,batch_size=a.batch_size,max_len=2048,desc=name+' AST') for name,values in sequences.items()}
        require(embed['reference'].shape==(900,256) and all(embed[k].shape==(len(ids),256) for k in ('hwc',*TAGS)), 'New embedding shape mismatch')
        np.savez_compressed(cache,**embed)
        write_json(provenance,{'fingerprint':fingerprint,'cache_sha256':digest(cache),'shapes':{k:list(v.shape) for k,v in embed.items()},'model':'Salesforce/codet5p-110m-embedding','max_len':2048})
    fresh,_,fresh_mode=scores(clf,embed['reference'])
    fresh_auc=roc_auc_score(test['actual label'].astype(int),fresh)
    drift=float(np.max(np.abs(fresh-base_scores)))
    require(fresh_mode==mode and abs(fresh_auc-base)<=0.005 and drift<=0.001,'Historical fresh embedding mismatch')
    print(f'[BASELINE] fresh 450-pair AUROC={fresh_auc:.8f} max_score_drift={drift:.6g}')
    hscore,hpred,_=scores(clf,embed['hwc'])
    ascore={};apred={}
    for tag in TAGS:
        ascore[tag],apred[tag],smode=scores(clf,embed[tag]);require(smode==mode,'Score mode changed')
    records=[]
    for i,pid in enumerate(ids):
        for label in (1,0):
            row={'pair_id':pid,'idx':pid+('_human' if label else '_lm'),'label':label,'source_stratum':meta.iloc[i].source_stratum,'human_body_tokens':int(meta.iloc[i].human_body_tokens)}
            for tag in TAGS:
                row['score_'+tag]=float(hscore[i] if label else ascore[tag][i])
                row['prediction_'+tag]=int(hpred[i] if label else apred[tag][i])
                row['agc_tokens_'+tag]=int(meta.iloc[i][tag+'_body_tokens'])
            records.append(row)
    df=pd.DataFrame(records)
    require(len(df)==len(ids)*2 and df.idx.is_unique,'Output predictions malformed')
    df.to_csv(out/'paired_predictions.csv',index=False)
    meta.to_csv(out/'matched_prompt_metadata.csv',index=False)
    means={tag:auc(hscore,ascore[tag]) for tag in TAGS}
    bs=bootstrap(hscore,ascore,a.bootstrap,a.stat_seed)
    cols=['t02','t04','t06','t04_minus_t02','t06_minus_t02','t06_minus_t04']
    pd.DataFrame(bs,columns=cols).to_csv(out/'bootstrap_replicates.csv',index=False)
    rows=[]
    for j,tag in enumerate(TAGS):
        lo,hi=np.quantile(bs[:,j],[0.025,0.975])
        rows.append({'tag':tag,'temperature':float(tag[1:])/10,'matched_pairs':len(ids),'auroc':means[tag],'ci95_low':lo,'ci95_high':hi})
    pd.DataFrame(rows).to_csv(out/'temperature_auroc.csv',index=False)
    contrasts=[]
    for col,i,j in [('t04_minus_t02',1,0),('t06_minus_t02',2,0),('t06_minus_t04',2,1)]:
        lo,hi=np.quantile(bs[:,cols.index(col)],[.025,.975])
        contrasts.append({'contrast':col,'delta_auroc':means[TAGS[i]]-means[TAGS[j]],'ci95_low':lo,'ci95_high':hi,'ci_excludes_zero':bool(lo>0 or hi<0)})
    pd.DataFrame(contrasts).to_csv(out/'temperature_contrasts.csv',index=False)
    write_json(out/'evaluation_summary.json',{'status':'PASS','experiment':'run-x-a-02-v1','matched_pairs':len(ids),'baseline_450_auroc_cached':base,'baseline_450_auroc_fresh':fresh_auc,'baseline_max_score_drift':drift,'bootstrap':a.bootstrap,'seed':a.stat_seed,'input_hashes':hashes,'input_fingerprint':fingerprint,'retrained':False,'auroc':means,'contrasts':contrasts})
    print('[RESULT] PASS ' + ', '.join(f'{tag}={means[tag]:.6f}' for tag in TAGS))


def verify(a,p,cohort):
    out=a.output_dir
    require((out/'evaluation_summary.json').is_file(),'Missing evaluation summary')
    result=json.loads((out/'evaluation_summary.json').read_text())
    require(result['status']=='PASS' and result['matched_pairs']==814,'Result status/count mismatch')
    require(result['input_hashes']==cohort[-1],'Source input hashes changed')
    scores=pd.read_csv(out/'paired_predictions.csv')
    require(len(scores)==1628 and scores.idx.is_unique,'Saved predictions mismatch')
    for tag in TAGS:
        actual=roc_auc_score(scores.label,scores['score_'+tag])
        require(abs(actual-result['auroc'][tag])<1e-12,f'Calculated AUROC mismatch: {tag}')
    require(len(pd.read_csv(out/'bootstrap_replicates.csv'))==result['bootstrap'],'Bootstrap count mismatch')
    print('[VERIFY] PASS inputs, 814 pairs, predictions, AUROCs and bootstrap count')


def main():
    a=arguments()
    if a.mode=='self-test':
        h=np.array([0.7,0.8]); g=np.array([0.2,0.3]);require(auc(h,g)==1.,'AUC self-test failed')
        print('[SELF-TEST] PASS');return
    p=paths(a)
    cohort=preflight(a,p)
    if a.mode=='preflight':return
    if a.mode=='verify':verify(a,p,cohort);return
    run(a,p,cohort)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('[ERROR]',type(e).__name__+':',e,file=sys.stderr)
        raise SystemExit(1)
