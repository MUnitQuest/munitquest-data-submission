# How to Submit
The Data Challenge heaviliy relies on and support [EMG-BIDS](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electromyography.html)-specifications.

<br/>Information on how to submit in codabench can be found in this [Tutorial](https://github.com/MUnitQuest/MUnitQuest_tutorials/blob/main/codabench_tutorials/codabench_tutorial.md) under 2. Please adhere to the submission format also provided in 2.1.

```
zip-root/
└── BIDSDataset  -> name of the dataset
    ├── dataset_description.json
    ├── participants.tsv
    ├── participants.json
    ├── README
    ├── sub-01/
    │   ├── emg/
    │   │   ├── sub-01_task-xxx_emg.edf
    │   │   ├── sub-01_task-xxx_channels.tsv
    │   │   ├── sub-01_task-xxx_events.tsv
    │   │   ├── sub-01_task-xxx_electrodes.tsv
    │   │   └── sub-01_task-xxx_coordsystem.json
    │   └── ...
    └── sub-02/
        └── ...
```

## Validation
The submitted dataset will be validated in a multi-layer approach:
1. Check submission format
2. Apply official [BIDS Validator](https://bids.neuroimaging.io/tools/validator.html)
3. Apply custom MUnitQuest criteria

After validation, a HTML-report is provided, which contains detailed depictions of warnings and errors from steps 2 and 3. If and only if the validation has been successful the HTML-report contains the upload URL for a cloud storage location, where to upload the full dataset to.
## Further Information
For further information, please see: https://munitquest.github.io/registration_and_submission/ and refer to the provided [Tutorials](https://github.com/MUnitQuest/MUnitQuest_tutorials/tree/main).
<br/>**Please also check out the provided resources [here](https://munitquest.github.io/resources/)**

<br/>**We highly encourage you to upload different datasets** and, thus, **enable multiple leaderboard-effective submissions**. If you, however, wish to update an already submitted dataset on the leaderboard, **make sure to remove the old version from the leaderboard**. Please **notify the organizers** when submitting multiple datasets!