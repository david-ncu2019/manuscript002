import numpy as np

npz = np.load('tau_demo_TUKU/results/tuku_aligned_data.npz', allow_pickle=True)
layers = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']
for layer in layers:
    prefix = layer + '__'
    head_m = npz[prefix + 'head_m'].astype(float)
    h_c    = float(npz[prefix + 'h_c'])
    i_m    = npz[prefix + 'i_m'].astype(bool)
    n_total = len(head_m)
    n_inel  = int(i_m.sum())
    pct_inel = n_inel / n_total * 100.0
    pctile = float(np.mean(head_m <= h_c) * 100.0)
    print(layer, 'h_c=', round(h_c,3), 'head_range=[', round(float(head_m.min()),3), ',', round(float(head_m.max()),3), ']  pct_inelastic=', round(pct_inel,1), '%  h_c_pctile=', round(pctile,1))
    for p in [10, 25, 50, 75, 90, 95, 99]:
        print('  p' + str(p) + '=', round(float(np.percentile(head_m, p)), 3))
    print()
