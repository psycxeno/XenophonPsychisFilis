import csv
import random
from datetime import datetime, timedelta

num_columns = 150
num_rows = 500#1_000_000

# Generate generic column names
column_names = [f"Col{i+1}" for i in range(num_columns)]

genders = ["Male", "Female", "Other"]
countries = ["USA", "UK", "Canada", "Australia", "Germany"]
cities = ["New York", "London", "Toronto", "Sydney", "Berlin"]
departments = ["HR", "Engineering", "Sales", "Marketing"]
statuses = ["Active", "Inactive", "On Leave"]
occupations = ["Engineer", "Manager", "Analyst", "Clerk"]
companies = ["Acme Corp", "Globex", "Initech", "Umbrella"]
managers = ["Alice", "Bob", "Charlie", "Diana"]
teams = ["Alpha", "Beta", "Gamma", "Delta"]

# Helper to generate random data by type
random_types = [
    lambda i: f"Name{i+1}",
    lambda i: random.randint(20, 65),
    lambda i: random.choice(genders),
    lambda i: random.choice(countries),
    lambda i: random.choice(cities),
    lambda i: f"user{i+1}@example.com",
    lambda i: f"+1-555-{random.randint(1000,9999)}",
    lambda i: random.choice(occupations),
    lambda i: random.choice(companies),
    lambda i: random.randint(30000, 120000),
    lambda i: random.choice(departments),
    lambda i: random.choice(managers),
    lambda i: (datetime(2000, 1, 1) + timedelta(days=random.randint(0, 7670))).strftime("%Y-%m-%d"),
    lambda i: random.choice(statuses),
    lambda i: f"{random.randint(100,999)} Main St",
    lambda i: f"{random.randint(10000,99999)}",
    lambda i: random.choice(countries),
    lambda i: f"Note {i+1}",
    lambda i: round(random.uniform(0, 100), 2),
    lambda i: random.randint(1, 10),
    lambda i: random.randint(0, 40),
    lambda i: f"Project {random.randint(1, 100)}",
    lambda i: random.choice(teams),
    lambda i: random.randint(0, 10000),
]

def maybe_null(value, null_prob=0.1):
    return value if random.random() > null_prob else ""

with open('large_file_500rows_150cols_backslash.txt', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\\')
    writer.writerow(column_names)
    for i in range(num_rows):
        row = []
        for c in range(num_columns):
            value = random_types[c % len(random_types)](i)
            if c == 0:
                # First column never null
                row.append(str(value))
            else:
                row.append(str(maybe_null(value)))
        writer.writerow(row)
