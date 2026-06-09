# Evaluation
Each dataset is rated by the expert panel on the following criteria:
- **Metadata and provenance** (10 percent) – verifies that submissions satisfy [CEDE](https://cede.isek.org/) reporting matrices, thereby guaranteeing reproducibility and downstream re-use
- **Raw-signal quality** (30 percent) – gauges whether the HDsEMG signals are “decomposition-ready”. Key metrics include the baseline noise of each channel, residual power-line interference at 50/60 Hz, and the fraction of bad channels.
- **Label quality** (40 percent) – evaluates the quality and trustworthiness of the labeled motor unit spike trains. This includes the labeling approach (e.g., simultaneous invasive EMG) as well as established trustworthiness measures such as the silhouette score and interspike-interval variability.
- **Diversity** (20 percent) – rewards datasets that expand anatomical, functional, and demographic coverage. Experienced reviewers rate the novelty of submissions in terms of recorded muscles, tasks, and recording configurations, including pathological as well as healthy cohorts, and balancing biological sex and age.

**Additional considerations for synthetic data**: For simulations, the data quality can be precisely controlled, and spike train labels represent an unequivocal ground truth. Hence, during the data review phase, the review panel will evaluate the realism of the simulated spike trains and the underlying muscle model (80 percent of the dataset score).<br/>
**During the double-blind review phase**, reviewers will assign a score of 1-6 (1: strong reject, 2: reject, 3: borderline reject, 4: borderline accept, 5: accept, 6: strong accept) for each category.

## Scoring in codabench
The submitted data to codabench is automatically checked for validity for the subsequent procedures. Thereby, the following metrics are automatically calculated and introduce variance to the preliminary leaderboard:

<table style="width: 100%; table-layout: fixed; border-collapse: collapse;">
    <thead>
        <tr>
            <th style="border: 1px solid black; padding: 8px;">Metric</th>
            <th style="border: 1px solid black; padding: 8px;">Description</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="border: 1px solid black; padding: 8px;">Valid</td>
            <td style="border: 1px solid black; padding: 8px;">1 if the dataset passes validation</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;">Warning Density</td>
            <td style="border: 1px solid black; padding: 8px;">Average number of warnings per recording</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;">Labelled MUs per Recording</td>
            <td style="border: 1px solid black; padding: 8px;">Average number of labelled MUs per recording</td>
        </tr>
    </tbody>
</table>

## Further Information
Please recall that the **leaderboard in codabench is preliminary** and does not include results of the double-blind review process! The **final leaderboard will be provided on the competition-website**
<br/>

For the sake of transparency the [code of the automized score function and validation function](https://github.com/MUnitQuest/munitquest-data-submission/tree/main/bundle/scoring) evaluating the data submissions is shared
<br/>
Please refer to https://munitquest.github.io/data-challenge/ for more information!