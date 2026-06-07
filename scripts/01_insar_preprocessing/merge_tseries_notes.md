# 2026-4-23

create script to run Overal Model Test --> detect appropriate deformation model for ascending and descending timeseries.

/mnt/fafalab_nas/PROJECT/001_CHOUSHUI_RIVER_BASIN/200_CRFP_S1A_HYP3/scripts_2026_Apr_May/A1_run_adaptive_omt_asc.py
/mnt/fafalab_nas/PROJECT/001_CHOUSHUI_RIVER_BASIN/200_CRFP_S1A_HYP3/scripts_2026_Apr_May/A1_run_adaptive_omt_desc.py
/mnt/fafalab_nas/PROJECT/001_CHOUSHUI_RIVER_BASIN/200_CRFP_S1A_HYP3/scripts_2026_Apr_May/A2_insar_omt_v3.py

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# 2026-4-24

create script to use the right-fit deformation model parameters and generate regular-spaced timeseries
in this case, I only want to have the first day of each month

/mnt/fafalab_nas/PROJECT/001_CHOUSHUI_RIVER_BASIN/200_CRFP_S1A_HYP3/scripts_2026_Apr_May/B_resample_timeseries_model.py

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# 2026-4-25

* * * * * * * * * * * * * * * * * * * * 

## Stage 1

I need to match the ascending and descending timeseries in spatial and temporal

**First** : change reference day of both time series to the first day of February

```
reference_date.py asc_ts_regular.h5 -r 20150201 -o asc_regts_ref.h5 --ram 4


reference_date.py desc_ts_regular.h5 -r 20150201 -o desc_regts_ref.h5 --ram 4
```

* * * * * * * * * * * * * * * * * * * * 

**Second** : crop the area to create common pixel and common temporal mask

```
python insar_crop_to_overlap.py 3_change_ref_date/asc_regts_ref.h5 3_change_ref_date/desc_regts_ref.h5 4_cropped/
```

```
python insar_crop_to_overlap.py 1_original/asc_temporalCoherence.h5 1_original/desc_temporalCoherence.h5 4_cropped/
```

```
python insar_crop_to_overlap.py 1_original/asc_geometryGeo.h5 1_original/desc_geometryGeo.h5 4_cropped/
```

```
python insar_crop_to_overlap.py 1_original/asc_maskTempCoh.h5 1_original/desc_maskTempCoh.h5 4_cropped/
```

* * * * * * * * * * * * * * * * * * * * 

## Stage 2

Create the common temporal coherence mask for cropped timeseries

```
(isce_ncu3) davidncu@isce-mintpy:~/ISCE_MintPy_122025/ASC_DESC_MERGE/merged_202604/4_cropped$ mask.py cropped_asc_maskTempCoh.h5 -m cropped_desc_maskTempCoh.h5 -o maskTempCoh_common.h5 --fill 0
```

* * * * * * * * * * * * * * * * * * * * 

## Stage 3

Mask the timeseries with common temporal coherence mask

```
mask.py 4_cropped/cropped_asc_regts_ref.h5 -m 4_cropped/maskTempCoh_common.h5 -o 5_masked/asc_regts_msk.h5

mask.py 4_cropped/cropped_desc_regts_ref.h5 -m 4_cropped/maskTempCoh_common.h5 -o 5_masked/desc_regts_msk.h5
```

```
mask.py 4_cropped/cropped_asc_geometryGeo.h5 -m 4_cropped/maskTempCoh_common.h5 -o 5_masked/asc_geometryGeo_msk.h5

mask.py 4_cropped/cropped_desc_geometryGeo.h5 -m 4_cropped/maskTempCoh_common.h5 -o 5_masked/desc_geometryGeo_msk.h5
```

* * * * * * * * * * * * * * * * * * * * 

## Stage 4

Remove the old reference date (should be in Stage 1 but I forget)

```
python insar_remove_dates.py 5_masked/asc_regts_msk.h5 20150114

=== MintPy Timeseries Date Removal Tool ===
Input file: 5_masked/asc_regts_msk.h5
Dates to remove: ['20150114']
Reading timeseries information from: 5_masked/asc_regts_msk.h5
  Number of dates: 132
  Date range: 20150114 to 20251201
  Data shape: (132, 2674, 2053)
Dates to be removed: ['20150114']

```

```
python insar_remove_dates.py 5_masked/desc_regts_msk.h5 20150116

=== MintPy Timeseries Date Removal Tool ===
Input file: 5_masked/desc_regts_msk.h5
Dates to remove: ['20150116']
Reading timeseries information from: 5_masked/desc_regts_msk.h5
  Number of dates: 132
  Date range: 20150116 to 20251201
  Data shape: (132, 2674, 2053)
Dates to be removed: ['20150116']

```

* * * * * * * * * * * * * * * * * * * * 

## Stage 5

Decompose the ascending and descending into vertical and horizontal

```
python insar_asc_desc_decompose_parallel.py 5_masked/asc_regts_msk_filtered.h5 5_masked/desc_regts_msk_filtered.h5 -g 5_masked/asc_geometryGeo_msk.h5 5_masked/desc_geometryGeo_msk.h5 -o 6_decompose/ --block-size 200
```


* * * * * * * * * * * * * * * * * * * * 

## Stage 6

Compare with GPS and Leveling

```
view.py 6_decompose/vert_velocity_msk.h5 velocity --show-gps --gnss-source GENERIC --gnss-comp vert --ref-gnss GS23 --gnss-label --gnss-redo -c tab10 -v -8 2
```

```
python plot_insar_vs_gps_leveling.py
```

* * * * * * * * * * * * * * * * * * * * 

## Stage 7

I need to interpolate the monthly values to MLCW location points, as well as the grid points --> for constrained inversion

**First** I subset the region covering my output points. If we use entire InSAR result, it will cost much more time for nothing

```
subset.py 6_decompose/vert_regts_msk.h5 -l '2598313.6' '2685199.8' -L '815582.9' '883149.5' -o 6_decompose/sub_vert_timeseries_msk.h5
```


_ * * * * * * * * * * * * * THIS SHIT IS TOO SLOW  * * * * * * * * * * * * * * * * * * * * * * _
**Second** I run script `interp_timeseries_insar.py`

```
python scripts/interp_timeseries_insar.py --input 6_decompose/sub_vert_timeseries_msk.h5 --stations 7_interpolation/mlcw_station_utm50n.csv --output 7_interpolation/mlcw_interpolated_insar_utm50n.csv --param-cache 7_interpolation/kriging_cache_20260428.json --trial 0 --workers 1 --engine-workers 6 --n-trials 50 --n-splits 5 --poly-order 1 --max-points 5000 --buffer-radius 1000
```
_ * * * * * * * * * * * * * THIS SHIT IS TOO SLOW  * * * * * * * * * * * * * * * * * * * * * * _


**Second** I run script `interp_timeseries_IDW.py`

```
(isce_ncu3) davidncu@isce-mintpy:~/ISCE_MintPy_122025/ASC_DESC_MERGE/merged_202604$ python scripts/interp_timeseries_IDW.py --input 6_decompose/sub_vert_timeseries_msk.h5 --stations studyarea_SHP/mlcw_station_utm50n.shp --output 7_interpolation/mlcw_interp_insar_IDW.shp --trial 0 --workers 6 --neighbors 20 --buffer-radius 500
==================================================
Input: 6_decompose/sub_vert_timeseries_msk.h5
Stations: studyarea_SHP/mlcw_station_utm50n.shp
Output: 7_interpolation/mlcw_interp_insar_IDW.shp
==================================================

```

```
(isce_ncu3) davidncu@isce-mintpy:~/ISCE_MintPy_122025/ASC_DESC_MERGE/merged_202604$ python scripts/interp_timeseries_IDW.py --input 6_decompose/sub_vert_timeseries_msk.h5 --stations studyarea_SHP/gridpnt_crfp_500m_utm50.shp --output 7_interpolation/gridpnt_500m_interp_insar_IDW.shp --trial 0 --workers 6 --neighbors 20 --buffer-radius 500
==================================================
Input: 6_decompose/sub_vert_timeseries_msk.h5
Stations: studyarea_SHP/gridpnt_crfp_500m_utm50.shp
Output: 7_interpolation/gridpnt_500m_interp_insar_IDW.shp
==================================================

```

* * * * * * * * * * * * * * * * * * * * 

## Stage 8

Now I have enough materials to run the constrained inversion scripts, but I need to investigate the timeseries of MLCW and GPS, I need to identify the "prior" of the percentage contribution of the first 300 m compaction to the total regional subsidence

This prior knowledge will be used to inform the algorithm, so that it will not have to guess such percentage like current process.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

# 2026-5-5

#### Step 1

I want to try to perform the resample with more details, instead of getting value at the first day of each month, I will add more days, such as 1, 6, 11, 16, 21, 26

```
python scripts/resample_timeseries_model.py 1_original/asc_timeseries_SET_ERA5_ramp_demErr.h5 -o 2_modeled/asc_ts_reg_extend.h5 --poly 1 --period 10 5 1 0.5 --polyline 20210301 20180701 20160301 --ref-yx 1749 1436 --max-memory 4

python scripts/resample_timeseries_model.py 1_original/desc_timeseries_SET_ERA5_ramp_demErr.h5 -o 2_modeled/desc_ts_reg_extend.h5 --poly 1 --period 10 5 1 0.5 --ex 20220726 --polyline 20200904 20180101 20151007 --ref-yx 1749 1436 --max-memory 4

```

* * * * * * * * * * * * * * * * * * * * 

#### Step 2

Now I need to change the reference date for the new files: `asc_ts_reg_extend.h5` and `desc_ts_reg_extend.h5`

```
reference_date.py 2_modeled/asc_ts_reg_extend.h5 --ref-date 20150116 -o 3_change_ref_date/asc_ts_reg_ext_ref.h5

update "REF_DATE" attribute value to 20150116
time used: 02 mins 26.3 secs.
```

I don't need to perform this function for `desc_ts_reg_extend.h5` because its reference date is 20150116 already.
I just change the file name --> `desc_ts_reg_ext_ref.h5`


**Remove the old reference date** in `asc_ts_reg_extend.h5`

```
python insar_remove_dates_optimized.py 3_change_ref_date/asc_ts_reg_ext_ref.h5 20150114 -o asc_ts_reg_ext_ref_rmdate.h5 --max-memory 4
```

after finishing, I got the new file:

```
info.py asc_ts_reg_ext_ref_rmdate.h5 --compact
******************** Basic File Info ************************
file name: /home/davidncu/ISCE_MintPy_122025/ASC_DESC_MERGE/merged_202604/asc_ts_reg_ext_ref_rmdate.h5
file type: timeseries
coordinates : GEO
SNWE: 2593360.0, 2702480.0, 817600.0, 899720.0.

******************** Date Stat Info *************************
Start Date: 20150116
End   Date: 20251211
Number of dates  : 786
STD of datetimes : 3.15 years

```

* * * * * * * * * * * * * * * * * * * * 

#### Step 3

Crop the area to create common pixel and common temporal mask

```
python insar_crop_to_overlap.py 3_change_ref_date/asc_ts_reg_ext_ref_rmdate.h5 3_change_ref_date/desc_ts_reg_ext_ref.h5 4_cropped/

```

temporalCoherence and geometryGeo are still the same


`maskTempCoh_common.h5` is also available already

* * * * * * * * * * * * * * * * * * * * 

#### Step 4

Mask the timeseries with common temporal coherence mask

```
mask.py 4_cropped/cropped_asc_ts_reg_ext_ref_rmdate.h5 -m 4_cropped/maskTempCoh_common.h5 -o 5_masked/asc_regts_ext_msk.h5

python insar_mask_optimized.py 4_cropped/cropped_desc_ts_reg_ext_ref.h5 -m 4_cropped/maskTempCoh_common.h5 -o 5_masked/desc_regts_ext_msk.h5
```

the initial version of `insar_mask_optimized.py` failed to include `date` data set
```
python -c 'import h5py; s=h5py.File("4_cropped/cropped_desc_ts_reg_ext_ref.h5","r"); d=h5py.File("5_masked/desc_regts_ext_msk.h5","a"); d.create_dataset("date", data=s["date"][:]); d.close(); s.close()'
```

* * * * * * * * * * * * * * * * * * * * 

#### Step 5

Decompose the ascending and descending into vertical and horizontal

```
python insar_asc_desc_decompose_optimized.py 5_masked/asc_regts_ext_msk.h5 5_masked/desc_regts_ext_msk.h5 -g 5_masked/asc_geometryGeo_msk.h5 5_masked/desc_geometryGeo_msk.h5 -o 6_decompose/ --max-memory 8
```

* * * * * * * * * * * * * * * * * * * * 

#### Step 6

interpolate values to MLCW location points, as well as the grid points --> for constrained inversion

* * * * * * * 
**First** I subset the region covering my output points. If we use entire InSAR result, it will cost much more time for nothing

```
subset.py 6_decompose/vert_regts_ext_msk.h5 -l '2598313.6' '2685199.8' -L '815582.9' '883149.5' -o 6_decompose/sub_vert_regts_ext_msk.h5
```

* * * * * * * 
**Second**

run script `interp_timeseries_IDW.py`

```
python scripts/interp_timeseries_IDW.py --input 6_decompose/sub_vert_regts_ext_msk.h5 --stations studyarea_SHP/mlcw_station_utm50n.shp --output 7_interpolation/mlcw_interp_insar_IDW_extend.shp --trial 0 --workers 6 --neighbors 10 --buffer-radius 1000

python scripts/interp_timeseries_IDW.py --input 6_decompose/sub_vert_regts_ext_msk.h5 --stations studyarea_SHP/gridpnt_crfp_500m_utm50.shp --output 7_interpolation/gridpnt_500m_interp_insar_IDW_extend.shp --trial 0 --workers 6 --neighbors 10 --buffer-radius 2000
```

