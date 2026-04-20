# Evaluation
Each dataset is rated by the expert panel on the following criteria:
- **Metadata and provenance** (10 percent) – verifies that submissions satisfy [CEDE](https://cede.isek.org/) reporting matrices, thereby guaranteeing reproducibility and downstream re-use
- **Raw-signal quality** (30 percent) – gauges whether the HDsEMG signals are “decomposition-ready”. Key metrics include the baseline noise of each channel, residual power-line interference at 50/60 Hz, and the fraction of bad channels.
- **Label quality** (40 percent) – evaluates the quality and trustworthiness of the labeled motor unit spike trains. This includes the labeling approach (e.g., simultaneous invasive EMG) as well as established trustworthiness measures such as the silhouette score and interspike-interval variability.
- **Diversity** (20 percent) – rewards datasets that expand anatomical, functional, and demographic coverage. Experienced reviewers rate the novelty of submissions in terms of recorded muscles, tasks, and recording configurations, including pathological as well as healthy cohorts, and balancing biological sex and age.

**Additional considerations for synthetic data**: For simulations, the data quality can be precisely controlled, and spike train labels represent an unequivocal ground truth. Hence, during the data review phase, the review panel will evaluate the realism of the simulated spike trains and the underlying muscle model (80 percent of the dataset score).
<br/>

## Scoring
During the double-blind review phase, reviewers will assign a score of 1-6 (1: strong reject, 2: reject, 3: borderline reject, 4: borderline accept, 5: accept, 6: strong accept) for each category.
<br/><br/>
*for transparency the code of the automized score function and validation function evaluating the data submissions is shared
<br/><br/>Please refer to https://munitquest.github.io/data-challenge/