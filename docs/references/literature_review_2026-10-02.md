# Literature review: taxi-out time prediction and CPU-feasible tabular models

Prepared 2026-10-02 for the PRC Data Challenge 2026 team (taxi-out at 10 EU hubs, RMSE, post-ops).

**How things were checked.** "VERIFIED" means I found the bibliographic record at the URL given. For most entries that was a Crossref DOI lookup (`api.crossref.org/works/<doi>`, which returns title, authors, venue, volume and pages), plus the publisher, arXiv, NTRS or repository page where I could reach it. "UNVERIFIED" means I could not find a record. Accuracy numbers come from the abstract or full text I read; where a number came only from a search-engine summary, that is said.

---

## 0. The two citations you asked about, plus the ICAO documents (item 2)

| Item | Status | Exact bibliographic data | Verified at |
|---|---|---|---|
| (a) Idris et al. | **VERIFIED, with two corrections** | Idris, Husni; Clarke, John-Paul; Bhuva, Rani; Kang, Laura (2002). "Queuing Model for Taxi-Out Time Estimation." *Air Traffic Control Quarterly* **10**(1), **pp. 1–22**. **DOI 10.2514/atcq.10.1.1** (AIAA). Publisher of record: Air Traffic Control Association Institute. | Crossref record for DOI 10.2514/atcq.10.1.1; TRID record https://trid.trb.org/view.aspx?id=710804 (gives pp. 1–22); MIT DSpace copy https://dspace.mit.edu/handle/1721.1/37322 (dated there as Sept 2001, i.e. the preprint) |
| (b) Simaiakis & Balakrishnan | **VERIFIED** | Simaiakis, Ioannis; Balakrishnan, Hamsa (2016). "A Queuing Model of the Airport Departure Process." *Transportation Science* **50**(1), **pp. 94–109**. **DOI 10.1287/trsc.2015.0603**. Online November 2015, issue February 2016. | Crossref; https://pubsonline.informs.org/doi/10.1287/trsc.2015.0603 (403 to the bot, but listed); open copy https://dspace.mit.edu/handle/1721.1/105359 ; author PDF https://www.mit.edu/~hamsa/pubs/SimaiakisBalakrishnan_TS2014.pdf |
| ICAO Doc 9640 | VERIFIED | *Manual of Aircraft Ground De-icing/Anti-icing Operations* (Doc 9640), **3rd edition** (current on the ICAO Store). The publication date of 16 May 2018 comes from a search-result summary; the store page does not show a year. | https://store.icao.int/en/manual-of-aircraft-ground-de-icing-anti-icing-operations-doc-9640 |
| ICAO Doc 9365 | VERIFIED | *Manual of All-Weather Operations* (Doc 9365), **5th edition, 2024** (current on the ICAO Store). The 4th edition is from 2017, so update the citation if you cite the 4th. | https://store.icao.int/en/manual-of-all-weather-operations-doc-9365 |

Notes for METHODS.md:
- Idris et al. studied Boston Logan. They found that runway configuration, airline/terminal, downstream restrictions and **take-off queue size** drive taxi-out time, with queue size the most important. Their queue-size model's mean absolute error (MAE) was about 20% better than the FAA ETMS 14-day running average.
- Simaiakis & Balakrishnan model taxi-out as an unimpeded taxi time plus a wait in a runway queue. The queue is a transient D(t)/E_k(t)/1 queue. The unimpeded taxi-out distributions are estimated per airline, runway configuration and visibility, and fitted as log-normal. The case study is Newark (EWR): trained on 2011 data, tested on 2007 and 2010. In the author manuscript (Fig. 15), the individual-flight RMSE is about 8.8–9.9 min for 2010/2011 and 16.1 min for 2007, and 88% of flights fall within ±10 min in 2010/2011.

---

## 1. Taxi-out prediction literature

### 1.1 Queueing and analytical models

| Citation | Status / URL | Method | Features that mattered | Reported accuracy |
|---|---|---|---|---|
| Idris et al. 2002 (above) | VERIFIED | Regression on the predicted take-off queue size at pushback, allowing for aircraft that pass each other | Number of take-offs ahead (queue), runway configuration, airline/terminal, downstream restrictions | MAE about 20% better than the 14-day running average |
| Simaiakis & Balakrishnan 2016 (above) | VERIFIED | Unimpeded distribution plus a D(t)/E_k(t)/1 runway queue driven by the pushback schedule | Pushback schedule, runway service-time distribution, runway configuration | Individual-flight RMSE 8.8–9.9 min (EWR 2010/11) |
| Simaiakis, I.; Pyrgiotis, N. (2010). "An Analytical Queuing Model of Airport Departure Processes for Taxi Out Time Prediction." AIAA ATIO 2010. DOI 10.2514/6.2010-9148 | VERIFIED (Crossref) | Earlier conference version of the queueing model | — | — |
| Simaiakis, I.; Balakrishnan, H. (2010). "Impact of Congestion on Taxi Times, Fuel Burn, and Emissions at Major Airports." *Transportation Research Record* 2184, 22–30. DOI 10.3141/2184-03 | VERIFIED (Crossref) | Taxi time against the number of aircraft taxiing | Surface counts | — |
| Badrinath, S.; Li, M.Z.; Balakrishnan, H. (2019). "Integrated Surface–Airspace Model of Airport Departures." *J. Guidance, Control, and Dynamics* 42(5), 1049–1063. DOI 10.2514/1.G003964 | VERIFIED (Crossref) | Tandem queue model of ramp, taxiway, runway and departure fix | — | — |
| Truong, T.V. (2012). "The Distribution Function of Airport Taxi-Out Times and Selected Applications." *J. Transportation Research Forum* 50(2). DOI 10.5399/osu/jtrf.50.2.2721 | VERIFIED: https://journals3.library.oregonstate.edu/trforum/article/view/3831 | Distributional analysis | Scheduled demand | Taxi-out times defined from scheduled flights follow a uniform distribution, which linear regression estimates well |

### 1.2 Benchmark and reference methods (EUROCONTROL / PRU)

**EUROCONTROL (2023). *Additional taxi-out time performance indicator document*, Edition 01.00, 16 March 2023.** Author S. Mesón-Mancha; reviewer R. Koelle; approver D. Huet (EGSD/AIU). VERIFIED by reading the PDF: https://ansperformance.eu/library/ATXOT_indicator_documentation_mar23.pdf (linked from https://ansperformance.eu/methodology/additional-taxi-out-time/).

What the methodology does (read from §3.2–3.5 and Fig. 4):
- Taxi-out time = ATOT − AOBT, from APDF data combined with NM trajectory data.
- Flights are grouped by **departure stand × departure runway**. Aircraft class is deliberately *not* used, to keep the samples large enough.
- The reference ("unimpeded") time for each group is the **10th percentile (P10)** of a **rolling 12 months** of departures, selected by local take-off time. A group needs at least 10 flights with taxi-out at or below P10.
- Excluded flights: taxi-out over 120 min, missing data, helicopters, and **flights de-iced after off-block**.
- Additional time = actual − reference.

Lee et al. 2016 (below) also use P10 per (gate, spot, runway) as their "unimpeded taxi time" feature. This makes stand×runway P10 a documented, citable feature. It sits alongside, not instead of, our median stand×runway target encoding.

### 1.3 Machine-learning approaches

| Citation | Status / URL | Method | Features that mattered | Reported accuracy |
|---|---|---|---|---|
| **Ravizza, S.; Atkin, J.A.D.; Maathuis, M.H.; Burke, E.K. (2013).** "A combined statistical approach and ground movement model for improving taxi time estimations at airports." *J. Operational Research Society* 64(9), 1347–1360. DOI 10.1057/jors.2012.123 | VERIFIED (Crossref; https://ideas.repec.org/a/pal/jorsoc/v64y2013i9p1347-1360.html) | Multiple linear regression on airport-layout features plus historic taxi times; arrivals and departures | Distance, turning angle, surface-traffic counts. Two European hubs (Stockholm-Arlanda and Zurich, per Chen et al. 2011 below) | "Promising"; compared against US results. I did not read the numbers. |
| **Ravizza, S.; Chen, J.; Atkin, J.A.D.; Stewart, P.; Burke, E.K. (2014).** "Aircraft taxi time prediction: comparisons and insights." *Applied Soft Computing* 14, 397–406. DOI 10.1016/j.asoc.2013.10.004 | VERIFIED (Crossref) | Compares linear regression, least median of squares, support vector regression (SVR), TSK fuzzy rule-based system, etc.; cross-validated | Same feature set | A TSK fuzzy rule-based system was best |
| Chen, J.; Ravizza, S.; Atkin, J.A.D.; Stewart, P. (2011). "On the Utilisation of Fuzzy Rule-Based Systems for Taxi Time Estimations at Airports." ATMOS 2011, OASIcs. DOI 10.4230/OASIcs.ATMOS.2011.134 | VERIFIED: https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.ATMOS.2011.134 ; PDF https://people.cs.nott.ac.uk/pszja/papers/ATMOS2011.pdf | Fuzzy rule-based system on **Zurich (LSZH)**, 679 movements | **N** = aircraft already taxiing when this one starts; **Q** = aircraft that stop taxiing while this one taxis, split by ARR/DEP (8 counts); log distance; log total turning angle; operating mode (morning/day/evening). The paper notes the take-off queue is **not** dominant at ARN/ZRH, unlike Boston. | ±2/3/5-min hit rates |
| **Lee, H.; Malik, W.; Jung, Y.C. (2016).** "Taxi-Out Time Prediction for Departures at Charlotte Airport Using Machine Learning Techniques." 16th AIAA ATIO. DOI 10.2514/6.2016-3910 | VERIFIED: https://ntrs.nasa.gov/citations/20180002162 (full text read) | Linear regression (LR), SVM, kNN, random forest (RF), neural network; CLT 2014, 246,083 departures | Concourse, gate, spot, runway, departure fix, aircraft model, weight class, gate–runway distance, scheduled pushback hour, **departures on the surface by runway**, **arrivals on the surface by concourse**, **unimpeded time = P10 per gate-spot-runway** | RMSE (min): LR 4.83/5.53/5.29/5.13; RF 4.82/5.39/5.47/5.19; NN 6.61/6.51/6.10/6.65 on four test sets. **The neural network was worst.** |
| Lee, H.; Malik, W.; Zhang, B.; Nagarajan, B.; Jung, Y.C. (2015). "Taxi Time Prediction at Charlotte Airport Using Fast-Time Simulation and Machine Learning Techniques." AIAA ATIO 2015. DOI 10.2514/6.2015-2272 | VERIFIED (Crossref) | Fast-time simulation combined with ML | — | — |
| Jordan, R.; Ishutkina, M.A.; Reynolds, T.G. (2010). "A statistical learning approach to the modeling of aircraft taxi time." 29th DASC. DOI 10.1109/DASC.2010.5655532 | VERIFIED (Crossref; https://www.ll.mit.edu/r-d/publications/statistical-learning-approach-modeling-aircraft-taxi-time) | Statistical learning; simple interpretable models | — | "Remarkably accurate" (abstract only) |
| Srivastava, A. (2011). "Improving departure taxi time predictions using ASDE-X surveillance data." 30th DASC. DOI 10.1109/DASC.2011.6096185 | VERIFIED (Crossref; https://mitre.org/news-insights/publication/improving-departure-taxi-time-predictions-using-asde-x-surveillance-data) | Adaptive model on a historical surface-flow database; JFK, summer 2010 | Queue position, distance to runway, arrival/departure rates, weather | Better than ETMS-based predictions |
| Balakrishna, P.; Ganesan, R.; Sherry, L. (2010). "Accuracy of reinforcement learning algorithms for predicting aircraft taxi-out times: A case-study of Tampa Bay departures." *Transportation Research Part C* 18(6), 950–962. DOI 10.1016/j.trc.2010.03.003 | VERIFIED (Crossref) | Reinforcement learning / stochastic dynamic programming | — | — |
| **Herrema, F.; Curran, R.; Visser, H.; Huet, D.; Lacote, R. (2018).** "Taxi-Out Time Prediction Model at Charles de Gaulle Airport." *J. Aerospace Information Systems* 15(3), 120–130. DOI 10.2514/1.I010502 | VERIFIED (Crossref) | Neural nets, regression trees, reinforcement learning, MLP, compared at **LFPG** | — | Regression tree best, average error about 1.6 min. This figure is from a search-engine summary; I could not reach the publisher page. |
| "Herrema et al. 2019 on Schiphol" | **UNVERIFIED as cited.** No 2019 Herrema taxi-out paper on Schiphol was found. The 2019 Herrema paper is Herrema, F.; Curran, R.; Hartjes, S.; Ellejmi, M.; Bancroft, S.; Schultz, M., "A machine learning model to predict runway exit at Vienna airport," *Transportation Research Part E* 131, 329–342, DOI 10.1016/j.tre.2019.10.002 (VERIFIED, Crossref). The Herrema taxi-out paper is the CDG one above. Fix the citation. | | | |
| **Lian, G.; Zhang, Y.; Desai, J.; Xing, Z.; Luo, X. (2018).** "Predicting Taxi-Out Time at Congested Airports with Optimization-Based Support Vector Regression Methods." *Mathematical Problems in Engineering* 2018, 7509508. DOI 10.1155/2018/7509508 | VERIFIED (Crossref) | GLM, softmax, ANN, and PSO/firefly-optimised SVR at Beijing Capital (PEK) | Delay identified as significant at congested airports | Improved-firefly SVR best |
| Yin, J.; Hu, Y.; Ma, Y.; Xu, Y.; Han, K.; Chen, D. (2018). "Machine Learning Techniques for Taxi-out Time Prediction with a Macroscopic Network Topology." 37th DASC. DOI 10.1109/DASC.2018.8569664 | VERIFIED (Crossref) | LR, SVM, RF at Shanghai Pudong (PVG) | Surface instantaneous and cumulative flow indices, aircraft queue-length indices, slot-demand indices | RF on one month of training data best |
| **Wang, X.; Brownlee, A.E.I.; Woodward, J.R.; Weiszer, M.; Mahfouf, M.; Chen, J. (2021).** "Aircraft taxi time prediction: Feature importance and their implications." *Transportation Research Part C* 124, 102892. DOI 10.1016/j.trc.2020.102892 | VERIFIED (Crossref; https://eprints.whiterose.ac.uk/169934/) | Several models, several international airports | A small subset generalises across airports: departure/arrival, **distance, total turns, average speed, number of recent aircraft**, plus a few airport-specific features | Going from all features to the subset costs under 1 percentage point in ±1/3/5-min hit rate |
| Kim, J.; Baik, H. (2021). "Taxi-Out Time Prediction at a Busy Airport using Random Forest Algorithm." 40th DASC. DOI 10.1109/DASC52595.2021.9594491 | VERIFIED (Crossref) | RF on Incheon **A-CDM + METAR** data | Feature-importance-based selection | — |
| Kato, F.; Itoh, E. (2023). "Aircraft Taxi Time Prediction Using Machine Learning and its Application for Departure Metering." 42nd DASC. DOI 10.1109/DASC58513.2023.10311276 | VERIFIED (Crossref) | Six ML methods at Tokyo Haneda | — | — |
| Lim, Y.; Alam, S.; Tan, F.; Lilith, N. (2024). "Variable Taxi-Out Time Prediction Based on Machine Learning with Interpretable Attributes." *Trans. JSASS* 67(3), 136–144. DOI 10.2322/tjsass.67.136 | VERIFIED (Crossref; abstract via Semantic Scholar) | **Two GBDTs**: gate→queue taxiing time and runway queuing time; SHAP | Taxiing model: route features; queuing model: **runway-queue features** | RMSE 1.79 min (taxiing), 0.92 min (queuing) |
| Yuan, L.; Liu, J.; Chen, H. (2024). "Additional Taxi-Out Time Prediction for Flights at Busy Airports by Fusing Flow Control Information." *Applied Sciences* 14(21), 9968. DOI 10.3390/app14219968 | VERIFIED (Crossref) | Unimpeded time per stand-group×runway from multiple linear regression on arrival/departure flows; target = additional time; XGBoost tuned by a nutcracker optimiser; PVG | **Flow-control (ATFM) information**, corridor departure/arrival flows, departure-flow share per origin–destination pair | Beat plain XGBoost |
| Yin, J.; Zhang, M.; Ma, Y.; Wu, W.; Li, H.; Chen, P. (2024). "Prediction and Analysis of Airport Surface Taxi Time: Classification, Features, and Methodology." *Applied Sciences* 14(3), 1306. DOI 10.3390/app14031306 | VERIFIED (Crossref) | **Review paper**, a useful bibliography | — | — |
| Dalmau, R.; Ballerini, F.; Naessens, H.; Belkoura, S.; Wangnick, S. (2021). "An explainable machine learning approach to improve take-off time predictions." *J. Air Transport Management* 95, 102090. DOI 10.1016/j.jairtraman.2021.102090 | VERIFIED (Crossref) | EUROCONTROL NM, GBDT-type model with explanations, take-off time (not taxi-out) | NM flight-plan / ETFMS data | 30% error reduction vs. the current system 1 h before EOBT |

### 1.4 Deep learning, sequence and graph models

| Citation | Status / URL | Method | Notes |
|---|---|---|---|
| **Lim, Y.; Alam, S.; Lilith, N.; Tan, F.; Toon, P.L. (2025).** "Graph Neural Networks with Spatiotemporal Flow Features for Aircraft Taxi-Out-Time Prediction." *J. Air Transportation* 33(4), 297–318. DOI 10.2514/1.D0369 | VERIFIED (Crossref; abstract via Semantic Scholar) | Node-link airport graph; each departure is a subgraph with flow edge attributes; GNN with transformer layers | GNN and GBM both 40–60% better than the FAA/EUROCONTROL standard methods. **GNN beats GBM by about 8 s (about 10%).** Needs route/node-link data and movement start times, i.e. surface surveillance. |
| Yang, X.; Yang, H.; Mao, Y.; Wang, Q.; Yin, S. (2024). "Multi-Task Dynamic Spatio-Temporal Graph Attention Network: A Variable Taxi Time Prediction Model for Airport Surface Operation." *Aerospace* 11(5), 371. DOI 10.3390/aerospace11050371 | VERIFIED (Crossref) | Multi-task spatio-temporal graph attention (MT-DSTGAN) at Beijing Capital; auxiliary targets are airport and segment traffic flow | Needs segment-level flows from surveillance |
| Li, N.; Jiao, Q.; Zhu, X.; Wang, S. (2020). "Prediction of Departure Aircraft Taxi Time Based on Deep Learning." *Trans. Nanjing Univ. Aeronautics & Astronautics* 37(2) (STEDL model) | VERIFIED (journal page https://tnuaa.nuaa.edu.cn/njhkhten/article/html/202002006); DOI not found | Time-flow, spatial (taxi distance) and environmental (weather, ATC, runway configuration, aircraft category) sub-networks; Hong Kong | "95.4% accuracy" (metric undefined in what I could read) |
| Vargo, E.; Tien, A.; Jafari, A.; Hubbard, W. (2022). "Airport Taxi Time Prediction and Alerting: A Convolutional Neural Network Approach." AIAA AVIATION 2022. DOI 10.2514/6.2022-4026 (arXiv 2111.09139) | VERIFIED (Crossref, arXiv) | CNN on surface-radar images | Predicts whether the **airport-average** taxi-out will exceed a threshold in the next hour, not per-flight time |
| Tran, T.-N.; Pham, D.-T.; Alam, S.; Duong, V. (2020). "Taxi-speed Prediction by Spatio-Temporal Graph-based Trajectory Representation and Its Applications." ICRAT 2020 | VERIFIED (https://dr.ntu.edu.sg/server/api/core/bitstreams/bf76396d-2c39-4a1d-86af-bd04644449ec/content) | Graph representation of the trajectory, then RF on speed | Speed error ±1.08 m/s (taxi-out) |
| "Lim, Jardines, Hansman, *Variable taxi-out time prediction using graph neural networks*, SIDs 2021" | **UNVERIFIED.** Cited as ref. [25] in Swatowska & Gabagnou 2025; no record found. | | |
| "Du, Chen, Li, *Using deep learning method to predict taxi time of aircraft: A case of Hong Kong Airport*, TR-C 114 (2020)" | **UNVERIFIED.** Same reference list, [24]; no record found. | | |
| "Yuan, Wang, Chen, *Predicting additional taxi-out time using CNN–GRU at Shanghai Pudong*, TR-C 158, 104432 (2024)" | **UNVERIFIED.** Same list, [26]. The verifiable Yuan/Liu/Chen 2024 paper is the *Applied Sciences* NOA-XGBoost paper above. Do not copy these three references. | | |

Takeaway: every deep, sequence or graph model that beat GBDT relied on **surface-surveillance-derived route and flow features**. None of them shows deep learning beating GBDT on airport/NM-record features alone. Lee et al. 2016 (NN worst) and Murça et al. 2025 (section 5) point the other way.

### 1.5 European / A-CDM studies

**Swatowska, A.; Gabagnou, L. (2025). "A Generalisable Machine Learning Framework for Taxi Time Prediction at A-CDM Airports." SESAR Innovation Days 2025 (EUROCONTROL Innovation Hub).** VERIFIED (PDF read): https://www.sesarju.eu/sites/default/files/documents/sid/2025/papers/SIDs_2025_paper_119-final%20v2.pdf. This is the closest prior work to our task.
- Data: **APDF** (the same airport data flow as our `_mvt` columns) plus METAR (SADIS) plus BADA aircraft data plus Airport Corner works. 4.1M flights, 2022–2024, at EBBR, LFPO, LKPR, LOWW, **LSZH** and **LTFM**.
- Model: a single **CatBoost** model with a mean-absolute-error loss, tuned with Optuna (300 iterations, depth 8). Trained on 2022–23, tested on 2024. They trimmed the top and bottom 0.1% of targets per airport-phase.
- Model benchmark (MAE / RMSE in min, ARR and DEP combined): LR 2.92/4.21; RF 2.92/4.34; **CatBoost 2.73/4.05**.
- Departure MAE vs. the standard-taxi-time baseline: LSZH 2m18s vs 2m34s; LTFM 3m32s vs 3m45s (only 4–6% better at LTFM).
- Departure SHAP shares: phase 29%, **runway 19%, stand 14%**, airport 9%, **de-/anti-icing status 7%**, airline 5%, MTOW 3%, hour 3%. METAR adds up to only about 3%.
- Caveat for us: they say the model **lacks surface-queue / congestion indicators** and that this limits accuracy at congested airports such as LTFM. Our congestion and sequence features address exactly that gap.
- Caveat on the paper itself: at least three entries in its reference list could not be verified (see 1.4).

**EUROCONTROL ATXOT document (section 1.2)**: the official stand×runway P10 reference method.

### 1.6 Uncertainty / probabilistic approaches

- Simaiakis & Balakrishnan 2016 output the expected taxi-out **and its variance** for each flight.
- Chen, J.; Weiszer, M.; Zareian, E.; Mahfouf, M.; Obajemu, O. (2017). "Multi-objective fuzzy rule-based prediction and uncertainty quantification of aircraft taxi time." IEEE ITSC 2017. DOI 10.1109/ITSC.2017.8317826. VERIFIED (Crossref).
- Badrinath, S.; Balakrishnan, H.; Clemons, E.; Reynolds, T. (2018). "Evaluating the Impact of Uncertainty on Airport Surface Operations." AIAA ATIO 2018. DOI 10.2514/6.2018-4242. VERIFIED (Crossref).
- Truong 2012 (distribution-function view), section 1.1.
- What this means for us: RMSE is minimised by the conditional mean. A probabilistic model only helps if it is used to **hedge rows with ambiguous labels** (e.g. a mixture of "echoed default block time" vs. "real" values), not as an end in itself. No taxi-out paper I found does this. It would be our own experiment and needs an EXP ID.

---

## 2. Deep learning for tabular regression on CPU (item 3)

### 2.1 Methods and implementations

| Method | Citation (VERIFIED, arXiv API) | Official code and licence (GitHub API, 2026-10-02) | GPU needed? | Assessment for 2.1M rows, 4 threads, 15 GB |
|---|---|---|---|---|
| MLP with **entity embeddings** for categoricals | Guo, C.; Berkhahn, F. (2016). "Entity Embeddings of Categorical Variables." arXiv:1604.06737 (3rd place in Kaggle Rossmann) | Author repo `entron/entity-embedding-rossmann`: **no licence file** (GitHub API returns none), so don't reuse it. Our own PyTorch `nn.Embedding` is trivial. | No | **Credible.** Cheapest deep-learning option. |
| ResNet-MLP and **FT-Transformer** | Gorishniy, Y.; Rubachev, I.; Khrulkov, V.; Babenko, A. (2021). "Revisiting Deep Learning Models for Tabular Data." NeurIPS 2021. arXiv:2106.11959 | `yandex-research/rtdl-revisiting-models`, **Apache-2.0** | ResNet no; FT-Transformer in practice yes | ResNet credible. **FT-Transformer is not credible on CPU**: attention over about 70 feature tokens costs roughly 100× an MLP (estimate below). README: "FT-Transformer is slower than MLP-like models." |
| **Numerical-feature embeddings** (piecewise-linear encoding PLE, periodic/PLR) | Gorishniy, Y.; Rubachev, I.; Babenko, A. (2022). "On Embeddings for Numerical Features in Tabular Deep Learning." NeurIPS 2022. arXiv:2203.05556 | `yandex-research/rtdl-num-embeddings` (pip `rtdl_num_embeddings`), **MIT** | No | **Credible.** With these embeddings "simple MLP-like models can perform on par with attention-based architectures." Cost: the first layer grows by about the embedding width. |
| **TabM** (parameter-efficient ensemble of k MLPs, BatchEnsemble-style) | Gorishniy, Y.; Kotelnikov, A.; Babenko, A. (2025). "TabM: Advancing Tabular Deep Learning with Parameter-Efficient Ensembling." ICLR 2025. arXiv:2410.24210 | `yandex-research/tabm` (pip `tabm`), **Apache-2.0** | Recommended, not required | **Borderline.** README: largest paper dataset 13M rows; "relatively slower than MLPs and GBDT". Compute scales with k (default k=32). On CPU, use a small k (about 8) and a narrow width (256). Best tabular deep-learning model in the paper and strong on TabReD (time-drift benchmark, arXiv:2406.19380, VERIFIED). |
| **RealMLP** (tuned-default MLP) | Holzmüller, D.; Grinsztajn, L.; Steinwart, I. (2024). "Better by Default: Strong Pre-Tuned MLPs and Boosted Trees on Tabular Data." NeurIPS 2024. arXiv:2407.04491 | `dholzmueller/pytabkit`, **Apache-2.0**; documented `device='cpu'` | No | **Credible.** Abstract: "favorable time-accuracy tradeoff", benchmarks on 1K–500K-row datasets, and "a combination of RealMLP and GBDTs with improved default parameters can achieve excellent results without hyperparameter tuning." |
| **TabPFN v2 / 2.5 / 3.x** | Hollmann, N. et al. (2025). "Accurate predictions on small data with a tabular foundation model." *Nature* 637, 319–326. DOI 10.1038/s41586-024-08328-6 (Crossref) | `PriorLabs/TabPFN`: code **Apache-2.0**. Weights: v2 under the "Prior Labs License" (Apache-2.0 plus attribution); **2.5/2.6/3/3.5 weights non-commercial**; licence acceptance requires an account login. | **Yes.** README: on CPU only up to **5,000 samples** (TabPFN-3.x), 1,000 for older versions. GPU limit 1M rows for TabPFN-3.5. | **Not credible** at 2M rows on CPU. The licence and login step also conflict with our open/reproducible rule. |
| **TabICL / TabICLv2** | Qu, J.; Holzmüller, D.; Varoquaux, G.; Le Morvan, M. (2025). "TabICL: A Tabular Foundation Model for In-Context Learning on Large Data." ICML 2025. arXiv:2502.05564. TabICLv2: arXiv:2602.11139 (ICML 2026) | `soda-inria/tabicl`, **BSD-3-Clause** | README recommends a GPU for large data; "can scale to … 500K samples through CPU and disk offloading"; pretrained on up to 48K–60K rows | **Not credible** for 2.1M rows on 4 threads. |
| SAINT (row+column attention) | Somepalli, G. et al. (2021). arXiv:2106.01342 | — | Yes in practice | Not credible; in Murça et al. 2025, SAINT was worse than the MLP (section 5). |

### 2.2 Benchmark evidence: GBDT vs. deep learning

- **Grinsztajn, L.; Oyallon, E.; Varoquaux, G. (2022).** "Why do tree-based models still outperform deep learning on typical tabular data?" NeurIPS 2022 Datasets & Benchmarks. arXiv:2207.08815. Trees are state of the art on medium-sized data (about 10K rows). Neural nets struggle with uninformative features, with rotation invariance, and with learning irregular functions.
- **McElfresh, D. et al. (2023).** "When Do Neural Nets Outperform Boosted Trees on Tabular Data?" NeurIPS 2023 Datasets & Benchmarks. arXiv:2305.02997. 19 algorithms on 176 datasets. The NN-vs-GBDT difference is often negligible, and light GBDT tuning matters more. **"GBDTs are much better than NNs at handling skewed or heavy-tailed feature distributions"**, which describes our target and our congestion counts.
- **Shwartz-Ziv, R.; Armon, A. (2022).** "Tabular data: Deep learning is not all you need." *Information Fusion* 81, 84–90. DOI 10.1016/j.inffus.2021.11.011 (Crossref). XGBoost beat the deep models, but **an ensemble of deep models plus XGBoost beat XGBoost alone.**
- **Erickson, N.; Purucker, L.; Tschalzev, A.; Holzmüller, D.; Desai, P.M.; Salinas, D.; Hutter, F. (2025).** "TabArena: A Living Benchmark for Machine Learning on Tabular Data." NeurIPS 2025 Datasets & Benchmarks (spotlight). arXiv:2506.16791; code `autogluon/tabarena` (Apache-2.0). GBDTs remain strong; deep learning "caught up under larger time budgets with ensembling"; foundation models excel on small data; "**ensembles across models advance the state-of-the-art**". It also warns that some deep models are over-represented in ensembles because of **validation-set overfitting**.
- Ye, H.-J. et al. (2024). "A Closer Look at Deep Learning Methods on Tabular Datasets" (TALENT benchmark, 300+ datasets). arXiv:2407.00956. Ensembling helps both trees and neural nets; GBDTs remain very strong baselines.
- Rubachev, I. et al. "TabReD." arXiv:2406.19380. Industrial datasets with **time-based splits**; this is the benchmark closest to our Jan/Jul month-holdout set-up.

### 2.3 Practical CPU training-time expectations (my estimate, not measured)

These are back-of-envelope figures: FLOPs per sample × 2.1M rows, assuming PyTorch fp32 on 4 threads sustains about 50–150 GFLOP/s for batch-1024 matrix multiplies. **Measure on a 200k-row subsample before committing.**

| Model (about 60 numeric + about 10 categorical features) | Approx. train FLOPs/sample | Est. time per epoch (2.1M rows) | Typical epochs | Est. total |
|---|---|---|---|---|
| MLP 3×512 + entity embeddings | about 4 MFLOP | about 1–3 min | 20–50 | **0.5–2 h** |
| Same + PLR/periodic numeric embeddings (d≈16–24) | about 8–10 MFLOP | about 2–6 min | 20–50 | 1–4 h |
| RealMLP (pytabkit defaults) | similar to the line above | about 2–6 min | defaults | 1–4 h |
| TabM, k=32, width 512 | about 32× MLP | 30–90 min | 10–30 | **not practical** |
| TabM, k=8, width 256 | about 2× MLP | 3–8 min | 20–40 | 1–5 h |
| FT-Transformer (3 blocks, d=192, about 70 tokens) | about 500 MFLOP | 2–6 h | 10+ | **not practical** |
| TabPFN / TabICL | in-context; CPU limit 5K rows (TabPFN) | — | — | **not practical** |

Memory: 2.1M × 70 float32 ≈ 0.6 GB, which fits easily. Determinism: set `torch.manual_seed`, `torch.use_deterministic_algorithms(True)` and a fixed thread count, and check those API names against the installed torch version before use (CLAUDE.md rule 2).

---

## 3. Ensembling and stacking evidence (item 4)

- **Wolpert, D.H. (1992).** "Stacked generalization." *Neural Networks* 5(2), 241–259. DOI 10.1016/S0893-6080(05)80023-1. VERIFIED (Crossref). The original out-of-fold level-2 learner.
- **Breiman, L. (1996).** "Stacked regressions." *Machine Learning* 24, 49–64. DOI 10.1007/BF00117832. VERIFIED (Crossref). Non-negative weighted combinations of out-of-fold predictions; the basis for "blend weights fitted on OOF predictions".
- **van der Laan, M.J.; Polley, E.C.; Hubbard, A.E. (2007).** "Super Learner." *Stat. Appl. Genet. Mol. Biol.* 6(1). DOI 10.2202/1544-6115.1309. VERIFIED (Crossref). The cross-validated weighted ensemble is asymptotically as good as the best weighted combination.
- **Shwartz-Ziv & Armon 2022; TabArena 2025; Holzmüller et al. 2024; TALENT 2024** (section 2.2): GBDT + neural-net ensembles beat single models. TabArena warns that blend weights fitted on a validation set can overfit, so fit them on month-grouped OOF predictions.
- **PRC evidence** (section 5): the 2024 runner-up, a weighted QP/stacking blend of CatBoost, LightGBM, XGBoost, MLP and SAINT, beat the best single model by only about **0.2%**. The 2024 winner used **seed-averaged LightGBM** only.
- **Residual corrector:** this is a special case of stacking. The second-stage model takes the OOF base prediction as an input or as an offset (e.g. a GBDT initial score) and learns the residual. Provenance: Wolpert 1992 / Breiman 1996, and forum (a participant, a participant) per CLAUDE.md. I found no taxi-specific paper on this.
- Target-encoding basis for the stand×runway feature: Micci-Barreca, D. (2001). "A preprocessing scheme for high-cardinality categorical attributes in classification and prediction problems." *SIGKDD Explorations* 3(1), 27–32. DOI 10.1145/507533.507538. VERIFIED (Crossref). CatBoost's ordered target statistics: Prokhorenkova, L. et al. "CatBoost: unbiased boosting with categorical features." NeurIPS 2018, arXiv:1706.09516. VERIFIED (arXiv).

---

## 4. Past PRC Data Challenge solutions (item 5)

**2024 (take-off weight)**
- **Winner: team_likable_jelly**, R. Alligier and D. Gianazza (ENAC). Repos: https://github.com/richardalligier/prc (GPL-3.0) and https://github.com/PRC-Data-Challenge-2024/team_likable_jelly. Read from the README:
  - **average of several LightGBM models trained with different seeds**, same data and hyperparameters;
  - about 65 min per model on their machine;
  - ADS-B features (spline-smoothed, altitude-sliced energy rate, OpenAP mass) plus METAR thunderstorm/fog features;
  - METARs archived because upstream changed;
  - `deterministic=True` only guaranteed identical results on the same system.
- **Runner-up:** Murça, M.C.R.; Maximo, M.R.O.A.; Dantas, J.P.A.; Szenczuk, J.B.T.; de Lima, C.R.; Carvalho, L.O.; de Melo, G.A. (2025). "Open Machine Learning Models for Actual Takeoff Weight Prediction." *J. Open Aviation Science* 3(2). DOI 10.59490/joas.2025.7963. VERIFIED (PDF read). Their Table 6:
  - test RMSE (kg): MLP 3,864; SAINT 3,921; **CatBoost 2,215.5**; **QP-weighted ensemble 2,210.4**;
  - the ensemble gain over CatBoost is about 0.2%, and the neural nets were far worse on their own.
- Overview paper: Spinielli, E.; Sun, J.; Strohmeier, M.; Olive, X.; Goens, Q.; Koelle, R.; Tart, A.; Fitzgerald, J. (2025). "Aircraft Takeoff Weight Estimation: The EUROCONTROL PRC 2024 Data Challenge." *JOAS* 3(2). DOI 10.59490/joas.2025.8252. VERIFIED: https://journals.open.tudelft.nl/joas/article/view/8252

**2025 (fuel burn)**: results at https://ansperformance.eu/study/data-challenge/dc2025/outcome.html (via search summary): 1. resourceful-quiver, RMSE 200.83; 2. jubilant-vase, 211.99; 3. outspoken-tornado, 219.85.
- **resourceful-quiver** (GPL-3.0): **LightGBM** on fuel flow, then integrated per segment, with a LightGBM mass estimator, OpenAP and ACARS. Report: `PRC_2025_report.pdf` in https://github.com/PRC-Data-Challenge-2025/resourceful-quiver. They chose LightGBM over RF, CatBoost and XGBoost for efficiency.
- **jubilant-vase**: **weighted blend of XGBoost + LightGBM + CatBoost** (blend weights fitted with scipy `minimize`), Optuna tuning, physics features (OpenAP, Acropole).
- **outspoken-tornado** (GPL-3.0): **CatBoost** + Optuna.
- No top-3 solution in either year used a neural net as its main model.

---

## 5. Recommendations for our setup (ranked)

1. **Queue and "passing" features built from the take-off sequence, plus the official P10 reference.**
   - Basis: Idris et al. 2002 (queue size is the top factor); Simaiakis & Balakrishnan 2016 (taxi-out = unimpeded + runway-queue wait); Chen/Ravizza et al. 2011 (N and Q counts at LSZH); Lee et al. 2016 and EUROCONTROL ATXOT 2023 (P10 unimpeded per stand×runway).
   - Post-ops twist: we know each departure's ATOT. Count take-offs from the same runway between a proxy off-block time (AOBT_3, else EOBT) and the flight's own ATOT. This is Idris's "flights ahead" and Chen's "Q".
   - Also add the stand×runway **P10** (12-month rolling, out-of-fold) as a feature. As a separate experiment, try the **additional time (target − P10)** as the target.
   - Build the proxy times identically in train and serve, because other departures' AOBT is blank in ranking. A parity test is needed.
2. **A second GBDT family plus seed averaging, blended on month-grouped OOF predictions.**
   - CatBoost with ordered target statistics for operator/stand/type: Prokhorenkova et al. 2018. It is the model EUROCONTROL used on APDF data (Swatowska & Gabagnou 2025) and 2nd/3rd-place PRC teams used it.
   - Seed-averaged LightGBM: Alligier's 2024-winning recipe.
   - Non-negative blend weights on OOF predictions: Breiman 1996 / Super Learner.
   - Expect small gains (about 0.2% in Murça et al. 2025). Accept only if larger than the 3-seed spread.
3. **OOF residual corrector (P5 in the roadmap)**: a second-stage GBDT that takes the OOF base prediction as an offset and learns from flags, NM-match status, label-defect indicators and carrier. Basis: Wolpert 1992; Breiman 1996; forum (a participant). Keep the folds strictly month-grouped (TabArena's validation-overfitting warning).
4. **One CPU-cheap neural member for diversity, not as a replacement.**
   - Model: an MLP with entity embeddings (Guo & Berkhahn 2016) and PLR numeric embeddings (Gorishniy et al. 2022, MIT), or RealMLP via pytabkit (Apache-2.0).
   - Target: log1p or Huber-clipped, with RMSE evaluated on the original scale.
   - Budget about 1–4 h on our CPU (estimate; measure on a 200k-row subsample first).
   - Add it to the blend only if month-OOF RMSE improves beyond seed noise. Shwartz-Ziv & Armon 2022 and TabArena 2025 support blending gains; McElfresh et al. 2023 warn that heavy-tailed features favour GBDTs. TabM only with k≈8 and width 256.
5. **Do not pursue now:**
   - FT-Transformer and SAINT: about 100× MLP compute on CPU, and SAINT lost to the MLP in Murça et al.
   - TabPFN/TabICL: CPU limit of 5K rows (TabPFN); TabPFN 2.5+ weights are non-commercial and need a login.
   - LSTM/GNN surface models: Lim et al. 2025's GNN gain of about 8 s over GBM needs node-link routes and movement-start times from surveillance, which our adsb.lol coverage cannot supply consistently (LTFM/LIRF gaps).
   - Weather: on APDF data METAR contributed only about 3% of SHAP (Swatowska & Gabagnou 2025), so keep weather as an ablation, not a priority. De-icing status was 7%; check whether our data has a usable de-icing indicator. **This is an open question for the organizers**: APDF carries de-icing status (per the EIH paper), but our columns may not.

### Citation fixes to apply in our docs
- Idris et al.: add **pp. 1–22** and **DOI 10.2514/atcq.10.1.1**.
- Simaiakis & Balakrishnan: add **pp. 94–109** and **DOI 10.1287/trsc.2015.0603**.
- "Herrema et al. 2019, Schiphol": replace with Herrema et al. 2018, *JAIS* 15(3), 120–130 (CDG, taxi-out).
- ICAO Doc 9365: current edition is the **5th (2024)**. ICAO Doc 9640: **3rd edition (2018)**.
- Do not cite the Lim/Jardines/Hansman 2021, Du/Chen/Li 2020 or Yuan/Wang/Chen (TR-C 2024) references; they are unverified.
