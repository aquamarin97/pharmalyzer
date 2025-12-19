# app\willbedeleted\models\regration_model.py
import numpy as np
from sklearn.linear_model import LinearRegression


class RegressionModel:
    def __init__(self, hex_column, fam_column):
        self.hex_column = hex_column
        self.fam_column = fam_column
        self.model = LinearRegression()
        self.final_residuals = None

    def preprocess_data(self, df):
        """
        Preprocess data by removing outliers using z-score.

        Args:
            df (pd.DataFrame): Input DataFrame.
        Returns:
            pd.DataFrame: Cleaned DataFrame.
        """
        df = df[df['Regresyon'] == 'Güvenli Bölge']
        return df  # Remove rows with high z-score

    def fit(self, df, mask, threshold=2.0, max_iter=10):
        """
        Iterative regression fit with preprocessed data.

        Args:
            df (pd.DataFrame): Training DataFrame.
            mask (pd.Series): Filter mask.
            threshold (float): Outlier threshold.
            max_iter (int): Maximum iterations for outlier removal.
        """
        filtered_df = self.preprocess_data(df.loc[mask].copy())
        
        for i in range(max_iter):
            x_data = filtered_df[self.fam_column].values.reshape(-1, 1)
            y_data = filtered_df[self.hex_column].values

            # Fit the model
            self.model.fit(x_data, y_data)
            predictions = self.model.predict(x_data)

            # Calculate residuals
            residuals = y_data - predictions
            sigma = np.std(residuals)

            # Identify non-outliers
            mask_upper = np.abs(residuals) <= (threshold + 10) + 2.2 * sigma
            mask_lower = np.abs(residuals) >= threshold - 2.2 * sigma
            mask = mask_upper & mask_lower

            new_filtered_df = filtered_df[mask]

            # Stop if no more outliers
            if new_filtered_df.shape[0] == filtered_df.shape[0]:
                break

            filtered_df = new_filtered_df

        # Store final residuals for external use
        self.final_residuals = residuals

    def predict(self, x_values):
        """
        Predict using the trained regression model.

        Args:
            x_values (np.array): Input values for prediction.

        Returns:
            np.array: Predicted values.
        """
        return self.model.predict(x_values)

    def calculate_residuals(self, df, mask):
        """
        Calculate residuals after fitting the model.

        Args:
            df (pd.DataFrame): DataFrame.
            mask (pd.Series): Filter mask.

        Returns:
            np.array: Residuals.
        """
        if self.final_residuals is not None:
            return self.final_residuals

        x_data = df.loc[mask, self.fam_column].values.reshape(-1, 1)
        y_data = df.loc[mask, self.hex_column].values
        predictions = self.model.predict(x_data)
        return y_data - predictions
