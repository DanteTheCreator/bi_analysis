import matplotlib.pyplot as plt
import pandas as pd

# Sample data provided
data = {
    'customer_id': [7296702, 900221, 3426220, 6710900, 7971600, 7365911, 1234233, 4349093, 7899773, 598773],
    'total_deposits': [62300.0, 49000.0, 42000.0, 24500.0, 21000.0, 18711.0, 16800.0, 16450.0, 15750.0, 14350.0]
}

# Create a DataFrame from the data
df = pd.DataFrame(data)

# Sorting the DataFrame by 'total_deposits' in descending order
df = df.sort_values('total_deposits', ascending=False)

# Plotting a bar chart
plt.figure(figsize=(12, 6))
plt.bar(df['customer_id'], df['total_deposits'], width=0.4, color='blue')  # Adjusted width and color
plt.xlabel('Customer ID')
plt.ylabel('Total Deposits')
plt.title('Total Deposits by Customer')
plt.xticks(rotation=45)
plt.show()

# Plotting a pie chart
# plt.figure(figsize=(8, 8))
# plt.pie(df['total_deposits'], labels=df['customer_id'], autopct='%1.1f%%', startangle=140)
# plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
# plt.title('Total Deposits Distribution')
# plt.show()