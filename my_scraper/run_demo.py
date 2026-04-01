# Quick demo runner - outputs results to a file only
import sys
import os

# Write all output to file only (avoids PowerShell encoding issues)
output_file = open('demo_output.txt', 'w', encoding='utf-8')
sys.stdout = output_file
sys.stderr = output_file

from connecting_trains import load_and_clean_data, train_delay_model, build_route_graph, find_connections, display_connections

csv_path = None
candidates = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'archive_extracted', 'indian_railway_delay_data_.csv'),
    'indian_railway_delay_data_.csv',
]
for c in candidates:
    if os.path.exists(c):
        csv_path = c
        break

if not csv_path:
    print("Dataset not found!")
    sys.exit(1)

# Step 1: Load & clean data
df = load_and_clean_data(csv_path)

# Step 2: Train delay prediction model
model_bundle = train_delay_model(df)

# Step 3: Build route graph
graph = build_route_graph(df)

# Step 4: Demo searches
demo_pairs = [
    ("Howrah", "New Delhi"),
    ("Varanasi", "Pune"),
    ("Mumbai", "Kanyakumari"),
    ("Chennai Egmore", "Kanyakumari"),
    ("Lucknow", "New Delhi"),
    ("Kolkata", "Chennai"),
    ("Varanasi", "New Delhi"),
    ("Howrah", "Kanyakumari"),
]

print("\n" + "="*70)
print("  RUNNING DEMO SEARCHES")
print("="*70)

for src, dst in demo_pairs:
    connections = find_connections(graph, src, dst, model_bundle, max_hops=2)
    display_connections(connections, src, dst)

output_file.flush()
output_file.close()

# Print status to real stderr
sys.stderr = sys.__stderr__
sys.stdout = sys.__stdout__
print("Done! Results saved to demo_output.txt")
