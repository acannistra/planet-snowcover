## Tuolumne (ASO IDs: `[USCATE, USCAJW, USCASJ]`) Model Training

This folder documents the model training process for selected ASO sites. The documentation of the precise training infrastructure can be found elsewhere.

The `config_*.toml` files document the data going into each training step, and the files are ordered.

## Training Steps

Step| ASO ID                    | Config File                    | Starting Checkpoint                                                                                            |
|---|---------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------|
| 1 | ASO_3M_SD_USCATE_20180528 | ASO_3M_SD_USCATE_20180528.toml | n/a                                                                                                            |
|2 | ASO_3M_SD_USCASJ_20180601 | ASO_3M_SD_USCASJ_20180601-Step2.toml                            | `s3://planet-snowcover-models/ASO-3M-SD-USCATE-20180528-2020-01-17-23-21-26-065/checkpoint-00050-of-00050.pth` |
|3 | ASO_3M_SD_USCAJW_20180423 | ASO_3M_SD_USCAJW_20180423-Step3.toml                            | `s3://planet-snowcover-models/ASO-3M-SD-USCASJ-20180601-Step2-2020-01-21-21-37-55-126/checkpoint-00050-of-00050.pth`                                                                                                            |

## Analysis Steps



1. `python run_prediction.py ASO_3M_SD_USCAJW_20180423-Step3.toml s3://planet-snowcover-models/ASO-3M-SD-USCAJW-20180423-Step3-2020-01-22-01-02-32-262 --aws_profile esip --test_only`
1. `python run_prediction.py ASO_3M_SD_USCASJ_20180601-Step2.toml s3://planet-snowcover-models/ASO-3M-SD-USCAJW-20180423-Step3-2020-01-22-01-02-32-262 --aws_profile esip --test_only --test_location s3://planet-snowcover-models/ASO-3M-SD-USCASJ-20180601-Step2-2020-01-21-21-37-55-126/test_ids.txt`
1. `python run_prediction.py ASO_3M_SD_USCATE_20180528-Step1.toml s3://planet-snowcover-models/ASO-3M-SD-USCAJW-20180423-Step3-2020-01-22-01-02-32-262 --aws_profile esip --test_only --test_location s3://planet-snowcover-models/ASO-3M-SD-USCATE-20180528-2020-01-17-23-21-26-065/test_ids.txt`


## Comparison

After running predictions, get IDs.

```
 aws s3 --profile esip ls s3://planet-snowcover-models/ASO-3M-SD-USCASJ-20180601-Step2-2020-01-21-21-37-55-126/ | grep clip/ | awk '{$1=$1};1'  | cut -f2 -d " "| sed 's/.$//' > ~/Dropbox/Projects/UW/planet-snowcover/experiments/ASO_Tuolumne/USCATE_predictions.txt
```

Run summaries:

```
 for file in (cat USCATE_predictions.txt); python summarize.py --aws_profile esip planet-snowcover-models/ASO-3M-SD-USCASJ-20180601-Step2-2020-01-21-21-37-55-126/$file /Volumes/wrangell-st-elias/research/planet/tuol-reruns/ --mask_loc planet-snowcover-snow/ASO_3M_SD_USCATE_20180528_binary ; end
```

or

```
parallel "python summarize.py --aws_profile esip planet-snowcover-models/ASO-3M-SD-USCASJ-20180601-Step2-2020-01-21-21-37-55-126/{} /Volumes/wrangell-st-elias/research/planet/tuol-reruns/ --mask_loc planet-snowcover-snow/ASO_3M_SD_USCATE_20180528_binary" ::: (cat USCATE_predictions.txt )

```


## Imagery Acqusition for Figures


### Tuolumne

1. Identify new Tuolumne ASO. (ASO_3M_SD_USCATE_20190503.tif)

2. Get imagery from archive over that ASO collect:

```
aws s3api restore-object --bucket planet-snowcover-archive --key  PSScene4Band_20190503_181900_100a_all_udm2.zip --restore-request '{"Days":25,"GlacierJobParameters":{"Tier":"Standard"}}'
```

check restore

```
aws s3api head-object --bucket planet-snowcover-archive --key  PSScene4Band_20190503_181900_100a_all_udm2.zip)
```

3. Tile image + mask
4. Prediciton + analysis workflow
