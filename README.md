# ovulation_detection
Data handling pipeline and custom algorithm for detecting ovulation and menstrual phases for elite female athletes.

<IMG  src="https://mermaid.ink/img/pako:eNp1VMtu2zAQ_JWFgLaXBHVeh-pQwPEjdmI3Rlw0BzmHDbWWiFCkIFJJhSj_3pVoR3La-mSJO7M7M0u9BsLEFITBVpkXkWLh4Od4o4F_w2h4v36A4-Pv9eS3K1A4WPG5FDJH7WCut6aGy-gXKhlLV8EoJfH04LGXDQzq9lUIbQksCW1ZUEbaWchMQeBS1HBewygao0OYoY6V1Mk_OUaVUAQL0olL4ZHcC5GG05PjswuIsbJM4lEjj2q5CJbSWmZsJiiJi8bRHVnM8l6bHWAvcUnakm3VwbYwGbAJjPO1Y197T_SkKuioaphEc-2oyI1CJ41-OKjvjggapVzuzyf-fEyOuHVfYg3TyD8vMc-7aQ8RU6OUFKXCYu8M43zhdC9LqDKmEFbngI_mmeDbIE--Zgqk7sFruPoQJJzuOl4dxDB0oDhHB0ZTw9kL9SPjLFqUjlDBKkXLwtuRO29mB0r6pTXMI6ZuM4NWgO1g8__pOh90wjxbDdfRJfNxQgQjVM1cvQGud8J2BwT72pBVxZJX02w54wyl7q_QTXT7vCP6S9ONp5xKHcO6tI6hFMOdZPntLr1PwzOuePEXH00_2xEtDkxvCbobc3Ix-NTM9s72GWYySYlT8Z49El_md0NqWEZrYYpuiZaevXnJYodClLz61RGsefelk888Dz_kJOSWbzsPhwkrYfpVWnEUyiTSOvsFhlob1zrBvvyIJjrmBsFRkFHBrsX8VXltGm4Cl_KGbIKQ_8ZYPG2CjX7jOiydWVdaBKErSjoKyjzmHMYSkwKzINyisvT2B5pYh_A?type=png"/>

# Checks and exclusions

The algorithm developed to detect ovulation (Notebook, Modules) has been developed under certain cycle parameters. The goal is that these parameters reflect healthy cycles and do not exclude too many individuals from analysis, however there is a risk of developing too focused an algorithm which is not flexible to different types of menstrual cycle. 

Here are the checks, assumptions and exclusions made during the analysis, and an explanation of their use.

Cycle start assumption: The scripts assume that the measurements in a 'kit' begin on day 2 of the menstrual cycle. This is the protocol but there is a chance that this did not happen in the field, therefore we may miss valid cycles. 

Valid Measurements Check: This check ensures that the cycle has more than four valid hormone measurements. It's important because the accuracy of hormone-based ovulation detection and menstrual cycle analysis largely depends on the number and quality of available hormone measurements. Insufficient or inaccurate measurements can lead to misleading results.

Cycle Length Check: This check confirms if the cycle length is between 21 and 35 days. This range is considered normal for menstrual cycles. Cycles outside this range might indicate possible health issues, such as Polycystic Ovary Syndrome (PCOS) or menopause, which could affect the analysis.

Follicular P4 Check: This exclusion step removes any progesterone (P4) values above 90pg/ml from the follicular phase. Progesterone levels are usually low in the follicular phase and a high value may indicate a measurement error or some other biological anomaly.

Follicular P4 Measurement Check: This check ensures that there is at least one valid P4 measurement in the follicular phase. The follicular phase is when the egg matures, and P4 measurements in this phase are crucial for understanding the hormonal dynamics of the cycle.

Luteal P4 Check: This exclusion step removes any P4 values above 400pg/ml in the luteal phase. Progesterone levels increase after ovulation (luteal phase), but values above 400pg/ml could indicate a measurement error or a medical condition like ovarian hyperstimulation syndrome.

Ovulation Detection Check: This checks whether there's a sustained rise in progesterone levels (above 150% of the baseline) in the luteal phase, and that the highest value is below 400pg/ml. This is a primary indicator of ovulation, as progesterone levels rise after the ovary releases an egg. A sustained rise confirms ovulation, while the maximum value check prevents misinterpretation due to excessively high readings.


These checks and exclusions are necessary to ensure the accuracy of the menstrual cycle analysis, as they help to identify and exclude data anomalies that may skew the results. It's important to note that these are general checks based on typical menstrual cycle characteristics, and individual cycles can vary. Always consult a healthcare provider for personal medical advice.
# Ovulation Detection Script Wiki

## Overview

This script is designed to process hormone data, detect ovulation, and visualize the results. It reads data from DynamoDB tables, processes the data by interpolating missing values, calculates baseline values, detects ovulation using progesterone levels, and generates plots to visualize the results. The script is modular, consisting of several classes and functions that can be easily reused and adapted for different purposes.

## Workflow

1. Import necessary libraries.
2. Set the directories for the input files, output files, and output plots.
3. Create an empty list `listofdfs` to store DataFrames for each participant and cycle.
4. Iterate through the rows of the input DataFrame `progid_df`.
5. Extract necessary information such as participant ID, kit number, organization code, and program ID.
6. Create a DataFrame `df` from the participant's data file.
7. Resample the data to a weekly frequency, creating a new DataFrame `weekly_df`.
8. Create a dictionary named `freq_dict` containing 'Original' and 'Weekly' DataFrames.
9. Loop through each frequency and the corresponding DataFrame in `freq_dict`.
10. Perform ovulation detection using the `detector` object.
11. Calculate the baseline for the participant and the current frequency.
12. Determine the follicular length based on the cycle length.
13. Calculate the baseline for the 'E2_linear' and 'P4_linear' columns.
14. Detect ovulation using progesterone values.
15. Update the DataFrame with the ovulation detection results.
16. Calculate the ratio of E2 to P4 for each row in the DataFrame.
17. Plot the cycle with and without ovulation markers.
18. Save the final DataFrame as a CSV file.
19. Update the per-participant dictionary with the results.
20. Create a DataFrame from the per-participant dictionary and save it as a CSV file.
21. Append the per-participant DataFrame to the list of DataFrames.
22. Concatenate all the DataFrames in `listofdfs` and `perpardfs` lists.
23. Remove duplicates from the concatenated DataFrames.
24. Save the final DataFrames as CSV files.
25. Merge multiple CSV files in a specified directory.
26. Drop duplicates from the merged DataFrame.
27. Calculate performance metrics for each frequency in the merged data.
28. Save the performance metrics as CSV files.
-----
## Modules and Functions
### Class: getdata

This class is responsible for fetching data from DynamoDB tables and processing the data for further analysis.

- `__init__(self, path)`: Initializes the class with the given path.
- `connect_dynamodb(region, profile)`: Connects to DynamoDB using the specified region and profile.
- `scan_table(dynamoTable, filterExp, expAttrNames)`: Scans the specified DynamoDB table and returns the results based on filter expressions and attribute names.
- `get_org_from_dynamo(table)`: Retrieves organization codes from the DynamoDB table.
- `get_prog_from_org(org_code_GCR)`: Retrieves program IDs from the organization code.
- `get_participants_from_study(programme_id, org_code_GCR)`: Fetches participant IDs from the study.
- `get_participants_from_org(org_code_GCR)`: Fetches participant IDs from the organization.
- `get_participants_from_org_full(org_code_GCR)`: Fetches full participant IDs from the organization.
- `get_test_batch_codes(table1)`: Retrieves test batch codes for estradiol and progesterone.
- `getmostrecentkit(par, scan_table, table_measurement, estradiol_tbc_id)`: Returns the most recent kit number for the given participant.

- `getmostrecentkit(par, scan_table, table_measurement, estradiol_tbc_id)`: Returns the most recent kit number for the given participant.
- `getallkitnums(par, scan_table)`: Returns all kit numbers for the given participant.
- `get_e_df_and_p_df(estradiol_tbc_id_l, progesterone_tbc_id_l, scan_table)`: Fetches estradiol and progesterone DataFrames.
- `get_samples(scan_table)`: Retrieves sample data from the specified DynamoDB table.
- `get_answers(scan_table)`: Fetches answers data from the specified DynamoDB table.
- `aws_data_merge(par, kitnum, e_df, p_df, answers_df)`: Merges AWS data into a single DataFrame.

-----

### Class: datahandling

This class handles data manipulation and preprocessing.

- `__init__(self, dataframe, path)`: Initializes the class with the given DataFrame and path.
- `interpolate_data(data, column)`: Interpolates missing values in the specified column.
- `mnc_missing_values(data)`: Handles missing values in the DataFrame.
- `closest_date_with_p4(self, df, landmark_date)`: splits data into weekly (or as close to allows within the data) frequency. 

    
-----
### Class: detection

This class is responsible for detecting ovulation and visualizing the results.

- `__init__(self, dataframe, path)`: Initializes the class with the given DataFrame and path.
- `baseline(player, cycle, column, base)`: Calculates the baseline for the specified player, cycle, and column.
- `p4_ov_detect(data, start_threshold)`: Detects ovulation using progesterone levels.
- `p4_ov_day(data, start)`: Determines the ovulation day based on progesterone levels.
- `e2p4_ov_day(indata, baird)`: Determines the ovulation day based on the E2/P4 ratio.
- `plotcycle(data, org, p, c, f, base)`: Generates a plot of the hormone data with ovulation markers.
- `plotcycle_no_ov(data, org, p, c, f)`: Generates a plot of the hormone data without ovulation markers.


By chaining together various methods from the detection class, you can efficiently analyze your data, detect events or patterns, and visualize the results for further analysis.


---
## Validation against gold standard

The `validate_ovulation_detection` function calculates performance metrics for ovulation detection by comparing the algorithm's results with manual annotations. The function merges all the previously annotated CSV files in a specified directory, adds the manual annotations from an RB_key.csv file, and calculates the performance metrics for each cycle. The metrics are then saved to CSV files.

### Function

```python
def validate_ovulation_detection(csv_directory, rb_key_path):
    ...
```

**Input Parameters:**
- `csv_directory`: The path to the directory containing the CSV files.
- `rb_key_path`: The path to the RB_key.csv file containing manual annotations.

**Output:**
- A dictionary containing the performance metrics for each frequency.

### Usage

1. Set the path to the directory containing the CSV files and the path to the RB_key.csv file.
2. Call the `validate_ovulation_detection` function with the specified paths.
3. The function reads and merges all the CSV files in the specified directory.
4. The function reads the RB_key.csv file and merges it with the merged DataFrame.
5. Duplicates are removed from the merged DataFrame.
6. The function loops through each unique frequency in the DataFrame and filters the data accordingly.
7. Performance metrics such as True Positive, False Positive, True Negative, False Negative, Precision, Recall, Accuracy, F1 Score, and Specificity are calculated for each frequency.
8. The metrics are converted to a DataFrame and saved as CSV files in the specified directory.
9. The function returns a dictionary containing the performance metrics for each frequency.

**Example:**

```python
csv_directory = "path/to/csv/directory"
rb_key_path = "path/to/RB_key.csv"
metrics_results = validate_ovulation_detection(csv_directory, rb_key_path)
```

---

