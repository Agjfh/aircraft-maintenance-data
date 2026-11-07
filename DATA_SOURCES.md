# Data sources, licenses and caveats

| Data | Type | Source | License / notes |
|---|---|---|---|
| `data/raw/nasa_cmapss/` | Real (NASA simulation) | NASA Prognostics Center of Excellence, PHM08 challenge; copy taken from GitHub `jiaxiang-cheng/PyTorch-Transformer-for-RUL-Prediction` | Public NASA data. Cite: Saxena, Goebel, Simon, Eklund (2008), *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation*, PHM08. It is a turbofan engine simulation, not specifically an A320 engine. |
| `data/raw/faa_sdr/` | Real | FAA Service Difficulty Reporting System (https://sdrs.faa.gov/) via GitHub `Boeing/sdr-hazards-classification` | MIT (Boeing repo). 22,621 reports; 1,155 mention the A320 (almost all structural corrosion). `part_name`/`part_condition` were extracted with regex and are mostly empty. |
| `data/raw/a320_synthetic/` | Synthetic | Generated for this project | Realistic structure; check intervals are typical values, NOT official Airbus MPD data. Do not present as real operational data. |
| `data/raw/a320_extra/` | Unverified (probably synthetic) | GitHub `Mujtaba3249/airbus_320_Data` | No license stated; flight numbers/airports look random; operations (fuel) data, not maintenance. |

`data/processed/` is derived from the above (normalized / split) and is reproducible; see `ml/` for baselines.
