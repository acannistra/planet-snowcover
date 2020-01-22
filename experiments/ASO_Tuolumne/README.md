## Tuolumne (ASO ID:`ASOCATE`) Model Training

This folder documents the model training process for selected ASO sites. The documentation of the precise training infrastructure can be found elsewhere.

The `config_*.toml` files document the data going into each training step, and the files are ordered.

## Training Steps

Step| ASO ID                    | Config File                    | Starting Checkpoint                                                                                            |
|---|---------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------|
| 1 | ASO_3M_SD_USCATE_20180528 | ASO_3M_SD_USCATE_20180528.toml | n/a                                                                                                            |
|2 | ASO_3M_SD_USCASJ_20180601 | TBD                            | `s3://planet-snowcover-models/ASO-3M-SD-USCATE-20180528-2020-01-17-23-21-26-065/checkpoint-00050-of-00050.pth` |
|3 | ASO_3M_SD_USCAJW_20180423 | TBD                            | `s3://planet-snowcover-models/ASO-3M-SD-USCASJ-20180601-Step2-2020-01-21-21-37-55-126/checkpoint-00050-of-00050.pth`                                                                                                            |
