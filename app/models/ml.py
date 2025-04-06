import numpy as np
import pandas as pd

# from google.colab import files


def calculate_crs_crr_with_bins(data):
    """
    Calculate Counseling Risk Score (CRS) and Counseling Risk Ratio (CRR)
    with 3-bin classifications for each component based on percentiles.

    Bins:
    - Low: Bottom 25% of values (below the 25th percentile)
    - Moderate: Middle 50% of values (between the 25th and 75th percentiles)
    - High: Top 25% of values (above the 75th percentile)

    Formula:
    CRS = 0.20×P + 0.25×B + 0.15×E + 0.10×W + 0.30×V
    CRR = CRS / (sum of coefficients for available data points)
    """
    # Create a copy of the data to avoid modifying the original
    result_df = data.copy()

    # Add columns to store component values - use NaN as initial value
    result_df["P_value"] = np.nan
    result_df["B_value"] = np.nan
    result_df["E_value"] = np.nan
    result_df["W_value"] = np.nan
    result_df["V_value"] = np.nan

    # Add CRS and CRR columns
    result_df["CRS"] = 0.0
    result_df["CRR"] = 0.0

    # Define weights for each component and subcomponent
    weights = {
        "P": 0.20,  # Performance component
        "B": 0.25,  # Behavioral component
        "E": 0.15,  # Engagement component
        "W": 0.10,  # Work Hours component
        "V": 0.30,  # Vibe Score component
        "performance_in_P": 0.6,
        "awards_in_P": 0.4,
        "leaves_in_B": 0.7,
        "onboarding_concern_in_B": 0.3,
        "mentor_in_E": 0.5,
        "training_in_E": 0.5,
    }

    # Process each row
    for idx, row in data.iterrows():
        # Initialize component values for calculations (not for storage)
        P_value = 0
        B_value = 0
        E_value = 0
        W_value = 0
        V_value = 0

        # Track if each component has data
        has_P_data = False
        has_B_data = False
        has_E_data = False
        has_W_data = False
        has_V_data = False

        # Track available feature coefficients
        available_coefficients = 0

        # Calculate P component (Performance + Awards)

        # Check if any P component features are available
        has_performance = pd.notna(row.get("Performance_Rating", None))
        has_awards = pd.notna(row.get("Reward_Points", None))

        if has_performance or has_awards:
            # Performance calculation
            performance_value = row.get("Performance_Rating", None)
            if pd.notna(performance_value):
                # Normalize using specified value
                norm_performance = performance_value / 4
                P_value += weights["performance_in_P"] * norm_performance
                available_coefficients += weights["P"] * weights["performance_in_P"]

            # Awards calculation
            awards_value = row.get("Reward_Points", None)
            if pd.notna(awards_value):
                # Normalize using specified value
                norm_awards = awards_value / 1516
                P_value += weights["awards_in_P"] * norm_awards
                available_coefficients += weights["P"] * weights["awards_in_P"]

            # Only mark as having data if any P inputs are available
            has_P_data = True

        # Calculate B component (Leaves + Onboarding Concern)

        # Check if any B component features are available
        has_leaves = pd.notna(row.get("Total_Leave_Days", None))
        has_concern = pd.notna(row.get("Onboarding_Concern_Flag", None))

        if has_leaves or has_concern:
            # Leaves calculation
            leaves_value = row.get("Total_Leave_Days", None)
            if pd.notna(leaves_value):
                # Normalize using specified value, and invert (fewer leaves is better)
                # Ensure the normalized leaves value is between 0 and 1
                leaves_value = min(leaves_value, 31)  # Cap at 31 days
                norm_leaves = 1 - (leaves_value / 31)
                B_value += weights["leaves_in_B"] * norm_leaves
                available_coefficients += weights["B"] * weights["leaves_in_B"]

            # Onboarding concern calculation
            concern_value = row.get("Onboarding_Concern_Flag", None)
            if pd.notna(concern_value):
                # Encode: True/Yes=1, False/No=0, and invert (False/No is good)
                if isinstance(concern_value, bool):
                    encoded_concern = 1 if concern_value else 0
                else:
                    encoded_concern = (
                        1 if str(concern_value).lower() in ["yes", "true", "1"] else 0
                    )

                norm_concern = 1 - encoded_concern  # Invert because no concern is good
                B_value += weights["onboarding_concern_in_B"] * norm_concern
                available_coefficients += (
                    weights["B"] * weights["onboarding_concern_in_B"]
                )

            # Only mark as having data if any B inputs are available
            has_B_data = True

        # Calculate E component (Mentor + Training)

        # Check if any E component features are available
        has_mentor = pd.notna(row.get("Mentor_Assigned", None))
        has_training = pd.notna(row.get("Initial_Training_Completed", None))

        if has_mentor or has_training:
            # Mentor calculation
            mentor_value = row.get("Mentor_Assigned", None)
            if pd.notna(mentor_value):
                # Encode: True/Yes=1, False/No=0
                if isinstance(mentor_value, bool):
                    norm_mentor = 1 if mentor_value else 0
                else:
                    norm_mentor = (
                        1 if str(mentor_value).lower() in ["yes", "true", "1"] else 0
                    )

                E_value += weights["mentor_in_E"] * norm_mentor
                available_coefficients += weights["E"] * weights["mentor_in_E"]

            # Training calculation
            training_value = row.get("Initial_Training_Completed", None)
            if pd.notna(training_value):
                # Encode: True/Yes=1, False/No=0
                if isinstance(training_value, bool):
                    norm_training = 1 if training_value else 0
                else:
                    norm_training = (
                        1 if str(training_value).lower() in ["yes", "true", "1"] else 0
                    )

                E_value += weights["training_in_E"] * norm_training
                available_coefficients += weights["E"] * weights["training_in_E"]

            # Only mark as having data if any E inputs are available
            has_E_data = True

        # Calculate W component (Work Hours)
        # Accept either 'work_hours' or 'Avg_Work_Hours'
        work_hours_value = None
        if "Avg_Work_Hours" in data.columns and pd.notna(row.get("Avg_Work_Hours")):
            work_hours_value = row.get("Avg_Work_Hours")
        elif "work_hours" in data.columns and pd.notna(row.get("work_hours")):
            work_hours_value = row.get("work_hours")

        if pd.notna(work_hours_value):
            # Normalize work hours
            norm_work_hours = min(work_hours_value / 10, 1.0)  # Cap at 1.0
            W_value = norm_work_hours
            available_coefficients += weights["W"]
            has_W_data = True

        # Calculate V component (Vibe Score)
        # Accept either 'vibe_score' or 'Avg_Vibe_Score'
        vibe_value = None
        if "Avg_Vibe_Score" in data.columns and pd.notna(row.get("Avg_Vibe_Score")):
            vibe_value = row.get("Avg_Vibe_Score")
        elif "vibe_score" in data.columns and pd.notna(row.get("vibe_score")):
            vibe_value = row.get("vibe_score")

        if pd.notna(vibe_value):
            # Normalize vibe score
            norm_vibe = min(vibe_value / 5, 1.0)  # Cap at 1.0
            V_value = norm_vibe
            available_coefficients += weights["V"]
            has_V_data = True

        # Store component values in the dataframe, only if we have data
        result_df.at[idx, "P_value"] = P_value if has_P_data else np.nan
        result_df.at[idx, "B_value"] = B_value if has_B_data else np.nan
        result_df.at[idx, "E_value"] = E_value if has_E_data else np.nan
        result_df.at[idx, "W_value"] = W_value if has_W_data else np.nan
        result_df.at[idx, "V_value"] = V_value if has_V_data else np.nan

        # Calculate the final CRS with updated formula
        crs = (
            (weights["P"] * P_value)
            + (weights["B"] * B_value)
            + (weights["E"] * E_value)
            + (weights["W"] * W_value)
            + (weights["V"] * V_value)
        )

        # Calculate CRR (avoid division by zero)
        crr = crs / available_coefficients if available_coefficients > 0 else 0

        # Store results
        result_df.at[idx, "CRS"] = crs
        result_df.at[idx, "CRR"] = crr

    # Calculate percentile thresholds for each component
    percentiles = [0, 25, 75, 100]

    # Create bin columns for each component
    result_df["P_bin"] = ""
    result_df["B_bin"] = ""
    result_df["E_bin"] = ""
    result_df["W_bin"] = ""
    result_df["V_bin"] = ""

    # Calculate percentile thresholds for each component, ignoring NaN values
    p_thresholds = np.nanpercentile(result_df["P_value"], percentiles)
    b_thresholds = np.nanpercentile(result_df["B_value"], percentiles)
    e_thresholds = np.nanpercentile(result_df["E_value"], percentiles)
    w_thresholds = np.nanpercentile(result_df["W_value"], percentiles)
    v_thresholds = np.nanpercentile(result_df["V_value"], percentiles)

    # Define function to assign bin based on thresholds
    def assign_bin(value, thresholds):
        if pd.isna(value):
            return ""  # Leave empty if value is NaN
        elif value <= thresholds[1]:  # Up to 25th percentile
            return "Low"
        elif value <= thresholds[2]:  # 25th to 75th percentile
            return "Moderate"
        else:  # Above 75th percentile
            return "High"

    # Assign bins to each component
    for idx, row in result_df.iterrows():
        result_df.at[idx, "P_bin"] = assign_bin(row["P_value"], p_thresholds)
        result_df.at[idx, "B_bin"] = assign_bin(row["B_value"], b_thresholds)
        result_df.at[idx, "E_bin"] = assign_bin(row["E_value"], e_thresholds)
        result_df.at[idx, "W_bin"] = assign_bin(row["W_value"], w_thresholds)
        result_df.at[idx, "V_bin"] = assign_bin(row["V_value"], v_thresholds)

    return result_df


def identify_scenarios(data):
    """
    Identify scenarios for each employee based on their component bins
    and add corresponding corporate concerns.
    """
    # Create a copy of the data
    result_df = data.copy()

    # Add columns for concerns and sent status
    result_df["Concern"] = ""
    result_df["Sent"] = "No"

    # Define scenario conditions and concerns
    scenarios = {
        "Scenario 1": {
            "condition": lambda row: row["V_bin"] == "Low",
            "concern": "Retaining talent and addressing dissatisfaction early",
        },
        "Scenario 2": {
            "condition": lambda row: row["P_bin"] == "Low",
            "concern": "Maintaining productivity and ensuring employees meet goals",
        },
        "Scenario 3": {
            "condition": lambda row: row["B_bin"] == "High",
            "concern": "Reducing absenteeism and ensuring smooth onboarding processes",
        },
        "Scenario 4": {
            "condition": lambda row: row["E_bin"] == "Low" and row["P_bin"] == "Low",
            "concern": "Building a culture of support and reducing turnover risk",
        },
        "Scenario 5": {
            "condition": lambda row: row["W_bin"] == "High" and (row["P_bin"] == "Low"),
            "concern": "Preventing burnout to maintain long-term productivity and well-being",
        },
        "Scenario 6": {
            "condition": lambda row: (
                row["P_bin"] == "Moderate"
                and row["V_bin"] == "Moderate"
                and row["E_bin"] == "Moderate"
                and row["W_bin"] == "Moderate"
            ),
            "concern": "Preventing moderate risks from turning into high risks",
        },
        "Scenario 7": {
            "condition": lambda row: (
                row["P_bin"] == "High"
                and row["E_bin"] == "High"
                and row["V_bin"] == "High"
                and row["B_bin"] == "Low"
            ),
            "concern": "Retaining top talent and fostering resilience in high performers",
        },
    }

    # Evaluate each employee against all scenarios
    for idx, row in result_df.iterrows():
        concerns = []
        triggered = False

        # Check each scenario
        for scenario_name, scenario_info in scenarios.items():
            # Make sure we don't apply scenarios to empty bins
            if (
                (scenario_name == "Scenario 1" and row["V_bin"] == "")
                or (scenario_name == "Scenario 2" and row["P_bin"] == "")
                or (scenario_name == "Scenario 3" and row["B_bin"] == "")
                or (
                    scenario_name == "Scenario 4"
                    and (row["E_bin"] == "" or row["P_bin"] == "")
                )
                or (
                    scenario_name == "Scenario 5"
                    and (row["W_bin"] == "" or row["P_bin"] == "")
                )
                or (
                    scenario_name == "Scenario 6"
                    and (
                        row["P_bin"] == ""
                        or row["V_bin"] == ""
                        or row["E_bin"] == ""
                        or row["W_bin"] == ""
                    )
                )
                or (
                    scenario_name == "Scenario 7"
                    and (
                        row["P_bin"] == ""
                        or row["E_bin"] == ""
                        or row["V_bin"] == ""
                        or row["B_bin"] == ""
                    )
                )
            ):
                continue

            if scenario_info["condition"](row):
                concerns.append(scenario_info["concern"])
                triggered = True

        # If any scenario was triggered, update the concern and sent columns
        if triggered:
            result_df.at[idx, "Concern"] = "; ".join(concerns)
            result_df.at[idx, "Sent"] = "Yes"

    return result_df


# Function to handle file upload and processing
def process_employee_data():
    print("Please upload your CSV file...")
    # uploaded = files.upload()

    # for filename, content in uploaded.items():
    #     print(f"Processing {filename}...")

    # Read the CSV content
    # filename = "app/models/Merged_Employee_Targeting_Data.csv"
    filename = "app/models/employee_targeting_results.csv"
    df = pd.read_csv(filename)

    # Check for required columns (using both potential naming conventions)
    required_columns = [
        ["Performance_Rating"],
        ["Reward_Points"],
        ["Total_Leave_Days"],
        ["Onboarding_Concern_Flag"],
        ["Mentor_Assigned"],
        ["Initial_Training_Completed"],
        ["work_hours", "Avg_Work_Hours"],  # Either of these column names
        ["vibe_score", "Avg_Vibe_Score"],  # Either of these column names
    ]

    missing_columns_msg = []
    for req_cols in required_columns:
        if not any(col in df.columns for col in req_cols):
            missing_cols = ", ".join(req_cols)
            missing_columns_msg.append(missing_cols)

    if missing_columns_msg:
        print(f"Warning: Missing these column groups: {', '.join(missing_columns_msg)}")
        print("These metrics will be left blank in the results.")

    # Calculate CRS, CRR and bin values
    print("Calculating CRS, CRR, and component bins...")
    binned_df = calculate_crs_crr_with_bins(df)

    # Identify scenarios and concerns
    print("Identifying scenarios and concerns...")
    result_df = identify_scenarios(binned_df)

    # Display sample results
    print("\nSample results (first 5 rows):")
    display_cols = [
        "Employee_ID",
        "P_bin",
        "B_bin",
        "E_bin",
        "W_bin",
        "V_bin",
        "Concern",
        "Sent",
    ]
    print(result_df[display_cols].head())

    # Print the bin thresholds
    print("\nBin threshold values (Percentiles):")
    for component, name in zip(
        ["P_value", "B_value", "E_value", "W_value", "V_value"],
        ["Performance", "Behavioral", "Engagement", "Work Hours", "Vibe Score"],
    ):
        # Only show thresholds if we have non-NaN values
        if not result_df[component].isna().all():
            thresholds = np.nanpercentile(result_df[component], [0, 25, 75, 100])
            print(f"{name} Component Thresholds:")
            print(f"  Low: {thresholds[0]:.4f} to {thresholds[1]:.4f}")
            print(f"  Moderate: {thresholds[1]:.4f} to {thresholds[2]:.4f}")
            print(f"  High: {thresholds[2]:.4f} to {thresholds[3]:.4f}")
        else:
            print(f"{name} Component: No data available")

    # Print summary statistics
    print("\nSummary Statistics:")
    concern_count = len(result_df[result_df["Sent"] == "Yes"])
    print(f"- Total employees: {len(result_df)}")
    print(
        f"- Employees with concerns: {concern_count} ({concern_count/len(result_df)*100:.1f}%)"
    )

    # Count scenarios
    scenario_counts = {
        "Scenario 1 (Low Vibe Score)": 0,
        "Scenario 2 (Poor Performance)": 0,
        "Scenario 3 (Behavioral Red Flags)": 0,
        "Scenario 4 (Low Engagement)": 0,
        "Scenario 5 (High Work Hours)": 0,
        "Scenario 6 (Moderate Issues)": 0,
        "Scenario 7 (Happy Employee)": 0,
    }

    for _, row in result_df.iterrows():
        if row["Sent"] == "Yes":
            concern = row["Concern"]
            if "dissatisfaction early" in concern:
                scenario_counts["Scenario 1 (Low Vibe Score)"] += 1
            if "productivity and ensuring" in concern:
                scenario_counts["Scenario 2 (Poor Performance)"] += 1
            if "absenteeism" in concern:
                scenario_counts["Scenario 3 (Behavioral Red Flags)"] += 1
            if "culture of support" in concern:
                scenario_counts["Scenario 4 (Low Engagement)"] += 1
            if "burnout" in concern:
                scenario_counts["Scenario 5 (High Work Hours)"] += 1
            if "moderate risks" in concern:
                scenario_counts["Scenario 6 (Moderate Issues)"] += 1
            if "top talent" in concern:
                scenario_counts["Scenario 7 (Happy Employee)"] += 1

    print("\nScenario counts:")
    for scenario, count in scenario_counts.items():
        print(f"- {scenario}: {count} employees")

    # Generate output filename
    output_filename = f"{filename.split('.')[0]}_results.csv"

    # Save the results to a CSV file
    result_df.to_csv(output_filename, index=False)

    # Provide download link
    print("\nDownload your results:")
    # files.download(output_filename)

    return result_df


# Run the main function
process_employee_data()
