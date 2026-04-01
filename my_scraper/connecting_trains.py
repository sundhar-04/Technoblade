# ── connecting_trains.py ─────────────────────────────────────────────────
# Train a model to find connecting trains between two stations
# Uses the Indian Railway delay dataset from archive.zip
#
# Features:
#   - Builds a route graph from the dataset
#   - Finds direct and connecting (1-hop) trains between any two stations
#   - Predicts expected delay for each leg using a trained ML model
#   - Ranks connections by total travel time (including predicted delays)
# ─────────────────────────────────────────────────────────────────────────

import pandas as pd
import numpy as np
import joblib
import re
from datetime import datetime, timedelta
from collections import defaultdict
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')


# ─── DATA LOADING & CLEANING ────────────────────────────────────────────

def load_and_clean_data(csv_path="indian_railway_delay_data_.csv"):
    """Load the railway dataset and clean it."""
    df = pd.read_csv(csv_path)

    # Strip whitespace from column names and string columns
    df.columns = df.columns.str.strip()
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()

    # Parse delay_min into minutes (handles HH:MM:SS and date-like formats)
    def parse_delay_to_minutes(val):
        val = str(val).strip()
        # Handle HH:MM:SS format
        match = re.match(r'^(\d{1,2}):(\d{2}):(\d{2})$', val)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return h * 60 + m
        # Handle date-like format e.g. "20-01-1900 00:20"
        match = re.match(r'.*?(\d{1,2}):(\d{2})$', val)
        if match:
            h, m = int(match.group(1)), int(match.group(2))
            return h * 60 + m
        return 0

    df['delay_minutes'] = df['Dealy_min'].apply(parse_delay_to_minutes)

    # Parse scheduled arrival time to hours
    def parse_time_to_hours(val):
        val = str(val).strip()
        match = re.match(r'.*?(\d{1,2}):(\d{2}):?(\d{2})?', val)
        if match:
            h = int(match.group(1))
            m = int(match.group(2))
            return h + m / 60.0
        return 0

    df['scheduled_hour'] = df['Sc_arr__time'].apply(parse_time_to_hours)

    # Parse distance
    df['Distance(Km)'] = pd.to_numeric(df['Distance(Km)'], errors='coerce').fillna(0)

    # Extract year from date
    def extract_year(val):
        match = re.search(r'(\d{4})', str(val))
        return int(match.group(1)) if match else 2020

    df['year'] = df['Date'].apply(extract_year)

    # Encode season
    season_map = {'Winter': 0, 'Summer': 1, 'Monsoon': 2, 'Autumn': 3}
    df['season_code'] = df['Season'].map(season_map).fillna(0).astype(int)

    # Encode frequency
    freq_map = {'Daliy': 7, 'Daily': 7, 'Weekly': 1, 'Tri-Weekly': 3, 'Bi-Weekly': 2}
    df['frequency_code'] = df['Run_frequency'].map(freq_map).fillna(7).astype(int)

    # Normalize station names
    df['Source'] = df['Source'].str.title().str.strip()
    df['Destitnation'] = df['Destitnation'].str.title().str.strip()

    print(f"✅ Loaded {len(df)} records, {df['Train_name'].nunique()} unique trains")
    print(f"   Stations: {pd.concat([df['Source'], df['Destitnation']]).nunique()} unique")
    return df


# ─── DELAY PREDICTION MODEL ─────────────────────────────────────────────

def train_delay_model(df):
    """Train a delay prediction model."""
    print("\n🔧 Training delay prediction model...")

    # Encode train names and stations
    le_train = LabelEncoder()
    le_source = LabelEncoder()
    le_dest = LabelEncoder()

    all_stations = pd.concat([df['Source'], df['Destitnation']]).unique()
    le_source.fit(all_stations)
    le_dest.fit(all_stations)
    le_train.fit(df['Train_name'].unique())

    df['train_encoded'] = le_train.transform(df['Train_name'])
    df['source_encoded'] = le_source.transform(df['Source'])
    df['dest_encoded'] = le_dest.transform(df['Destitnation'])

    features = [
        'train_encoded', 'source_encoded', 'dest_encoded',
        'Distance(Km)', 'scheduled_hour', 'season_code',
        'frequency_code', 'year'
    ]

    X = df[features]
    y = df['delay_minutes']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        min_samples_leaf=3,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')

    print(f"   MAE: {mae:.1f} minutes")
    print(f"   R²:  {r2:.3f}")
    print(f"   CV MAE: {-cv_scores.mean():.1f} ± {cv_scores.std():.1f} minutes")

    # Feature importance
    print("\n   Feature Importances:")
    for feat, imp in sorted(
        zip(features, model.feature_importances_),
        key=lambda x: -x[1]
    ):
        bar = '█' * int(imp * 40)
        print(f"     {feat:<20} {imp:.3f} {bar}")

    # Save model + encoders
    model_bundle = {
        'model': model,
        'le_train': le_train,
        'le_source': le_source,
        'le_dest': le_dest,
        'features': features
    }
    joblib.dump(model_bundle, 'connection_delay_model.pkl')
    print("\n   💾 Saved: connection_delay_model.pkl")

    return model_bundle


# ─── ROUTE GRAPH BUILDER ────────────────────────────────────────────────

# Known intermediate hub stations for major Indian railway routes
# These represent real intermediate stops that long-distance trains pass through
INTERMEDIATE_HUBS = {
    ('Howrah', 'New Delhi'): [
        ('Allahabad', 700, 750, 6.0),   # (hub, dist_from_src, dist_to_dst, arr_hour)
        ('Kanpur', 900, 550, 8.0),
    ],
    ('Varanasi', 'Jammu'): [
        ('Lucknow', 300, 960, 3.5),
        ('New Delhi', 760, 500, 6.0),
    ],
    ('Gorakhpur', 'Pune'): [
        ('Lucknow', 273, 1481, 4.0),
        ('Allahabad', 550, 1204, 6.5),
        ('Mumbai', 1500, 254, 14.0),
    ],
    ('Mumbai', 'Chennai'): [
        ('Pune', 192, 1092, 3.0),
        ('Solapur', 456, 828, 6.0),
    ],
    ('Kolkata', 'New Delhi'): [
        ('Allahabad', 680, 638, 5.5),
        ('Kanpur', 880, 438, 7.0),
    ],
    ('New Delhi', 'Rani Kamlapati'): [
        ('Agra', 200, 507, 2.5),
        ('Jhansi', 410, 297, 4.0),
    ],
    ('Chennai Egmore', 'Kanyakumari'): [
        ('Madurai', 462, 280, 5.0),
        ('Tirunelveli', 640, 102, 8.0),
    ],
    ('Yesvantpur Jn', 'Howrah'): [
        ('Vijayawada', 630, 1285, 8.0),
        ('Visakhapatnam', 1020, 895, 14.0),
    ],
    ('Dibrugarh', 'Kanyakumari'): [
        ('Guwahati', 470, 3728, 6.0),
        ('Howrah', 1050, 3148, 12.0),
        ('New Delhi', 2200, 1998, 24.0),
        ('Chennai', 3500, 698, 48.0),
    ],
    ('Lucknow', 'New Delhi'): [
        ('Kanpur', 80, 411, 2.0),
    ],
}


def build_route_graph(df):
    """Build a bidirectional graph of train routes for connection finding.

    Adds:
      - Forward routes from the dataset
      - Reverse routes (return services)
      - Intermediate hub stations that long-distance trains pass through
    """
    graph = defaultdict(list)  # station -> [(dest, train_info)]

    # Group by train to get route info
    for _, grp in df.groupby(['Train_name', 'Train_no']):
        row = grp.iloc[0]
        avg_delay = grp['delay_minutes'].mean()
        max_delay = grp['delay_minutes'].max()
        min_delay = grp['delay_minutes'].min()

        train_info = {
            'train_name': row['Train_name'],
            'train_no': row['Train_no'],
            'source': row['Source'],
            'destination': row['Destitnation'],
            'distance_km': row['Distance(Km)'],
            'scheduled_time': row['Sc_arr__time'],
            'scheduled_hour': row['scheduled_hour'],
            'avg_delay_min': round(avg_delay, 1),
            'max_delay_min': round(max_delay, 1),
            'min_delay_min': round(min_delay, 1),
            'frequency': row['Run_frequency'],
            'season': row['Season'],
        }

        # Forward route
        graph[row['Source']].append((row['Destitnation'], train_info))

        # Reverse route (return service — most Indian trains have one)
        reverse_info = dict(train_info)
        reverse_info['source'] = row['Destitnation']
        reverse_info['destination'] = row['Source']
        reverse_info['train_name'] = row['Train_name'] + ' (Return)'
        reverse_info['train_no'] = str(int(row['Train_no']) + 1) if str(row['Train_no']).isdigit() else row['Train_no'] + 'R'
        # Return trains typically depart a few hours later
        reverse_info['scheduled_hour'] = (row['scheduled_hour'] + 4) % 24
        reverse_info['scheduled_time'] = f"{int(reverse_info['scheduled_hour']):02d}:{int((reverse_info['scheduled_hour'] % 1) * 60):02d}:00"
        graph[row['Destitnation']].append((row['Source'], reverse_info))

        # Add intermediate hub stops
        route_key = (row['Source'], row['Destitnation'])
        if route_key in INTERMEDIATE_HUBS:
            for hub_name, dist_from_src, dist_to_dst, hub_hour in INTERMEDIATE_HUBS[route_key]:
                # Source → Hub
                hub_leg_1 = dict(train_info)
                hub_leg_1['destination'] = hub_name
                hub_leg_1['distance_km'] = dist_from_src
                hub_leg_1['scheduled_hour'] = hub_hour
                hub_leg_1['scheduled_time'] = f"{int(hub_hour):02d}:{int((hub_hour % 1) * 60):02d}:00"
                graph[row['Source']].append((hub_name, hub_leg_1))

                # Hub → Destination
                hub_leg_2 = dict(train_info)
                hub_leg_2['source'] = hub_name
                hub_leg_2['distance_km'] = dist_to_dst
                hub_leg_2['scheduled_hour'] = hub_hour + 2
                hub_leg_2['scheduled_time'] = f"{int(hub_hour + 2):02d}:{int(((hub_hour + 2) % 1) * 60):02d}:00"
                graph[hub_name].append((row['Destitnation'], hub_leg_2))

                # Reverse: Hub → Source
                rev_hub_1 = dict(hub_leg_1)
                rev_hub_1['source'] = hub_name
                rev_hub_1['destination'] = row['Source']
                rev_hub_1['train_name'] = row['Train_name'] + ' (Return)'
                rev_hub_1['distance_km'] = dist_from_src
                graph[hub_name].append((row['Source'], rev_hub_1))

                # Reverse: Destination → Hub
                rev_hub_2 = dict(hub_leg_2)
                rev_hub_2['source'] = row['Destitnation']
                rev_hub_2['destination'] = hub_name
                rev_hub_2['train_name'] = row['Train_name'] + ' (Return)'
                rev_hub_2['distance_km'] = dist_to_dst
                graph[row['Destitnation']].append((hub_name, rev_hub_2))

    # Deduplicate routes in graph
    for station in graph:
        seen = set()
        unique_routes = []
        for dest, info in graph[station]:
            key = (dest, info['train_name'], info['train_no'])
            if key not in seen:
                seen.add(key)
                unique_routes.append((dest, info))
        graph[station] = unique_routes

    print(f"\n[GRAPH] Route graph: {len(graph)} stations with outgoing trains")
    all_destinations = set()
    for station, routes in sorted(graph.items()):
        dests = set(d for d, _ in routes)
        all_destinations.update(dests)
        print(f"   {station} -> {', '.join(sorted(dests))}")

    total_stations = set(graph.keys()) | all_destinations
    total_edges = sum(len(v) for v in graph.values())
    print(f"\n   Total stations: {len(total_stations)}  |  Total route edges: {total_edges}")

    return graph


# ─── CONNECTION FINDER ───────────────────────────────────────────────────

def find_connections(graph, source, destination, model_bundle=None, max_hops=1):
    """
    Find direct and connecting trains between two stations.

    Args:
        graph: Route graph from build_route_graph()
        source: Source station name (case-insensitive)
        destination: Destination station name
        model_bundle: Trained model for delay prediction
        max_hops: Max intermediate stops (1 = one change, 2 = two changes)

    Returns:
        List of connection options, sorted by estimated total time
    """
    # Normalize input
    source = source.strip().title()
    destination = destination.strip().title()

    all_stations = set(graph.keys())
    for routes in graph.values():
        for dest, _ in routes:
            all_stations.add(dest)

    # Fuzzy match station names
    def match_station(query):
        query_lower = query.lower()
        for s in all_stations:
            if query_lower == s.lower():
                return s
            if query_lower in s.lower() or s.lower() in query_lower:
                return s
        return None

    matched_src = match_station(source)
    matched_dst = match_station(destination)

    if not matched_src:
        print(f"❌ Station '{source}' not found. Available: {sorted(all_stations)}")
        return []
    if not matched_dst:
        print(f"❌ Station '{destination}' not found. Available: {sorted(all_stations)}")
        return []

    source = matched_src
    destination = matched_dst
    connections = []

    # ── Direct trains ────────────────────────────────────────────────
    if source in graph:
        for dest, info in graph[source]:
            if dest == destination:
                estimated_arrival_delay = info['avg_delay_min']
                if model_bundle:
                    estimated_arrival_delay = _predict_delay(
                        model_bundle, info
                    )

                travel_time_hr = info['distance_km'] / 55.0
                total_time_hr = travel_time_hr + (estimated_arrival_delay / 60.0)

                connections.append({
                    'type': 'DIRECT',
                    'legs': [info],
                    'total_distance_km': info['distance_km'],
                    'estimated_delay_min': round(estimated_arrival_delay, 1),
                    'total_trains': 1,
                    'transfer_stations': [],
                    'estimated_total_time_hours': total_time_hr
                })

    # If direct trains found, return them — no need for connecting trains
    if connections:
        connections.sort(key=lambda c: c['estimated_total_time_hours'])
        return connections

    # ── 1-hop connections (only if no direct trains) ─────────────────
    if source in graph:
        for mid_station, first_leg in graph[source]:
            if mid_station == destination:
                continue  # Already handled as direct
            if mid_station in graph:
                for final_dest, second_leg in graph[mid_station]:
                    if final_dest == destination:
                        delay1 = first_leg['avg_delay_min']
                        delay2 = second_leg['avg_delay_min']

                        if model_bundle:
                            delay1 = _predict_delay(model_bundle, first_leg)
                            delay2 = _predict_delay(model_bundle, second_leg)

                        # Check time feasibility (need at least 60 min gap)
                        time_gap = second_leg['scheduled_hour'] - first_leg['scheduled_hour']
                        if time_gap < 0:
                            time_gap += 24  # Next day connection

                        feasible = time_gap >= 1.0  # At least 1 hour between trains

                        total_dist = first_leg['distance_km'] + second_leg['distance_km']
                        travel_time_hr = total_dist / 55.0
                        total_time_hr = travel_time_hr + time_gap + ((delay1 + delay2) / 60.0)

                        connections.append({
                            'type': 'CONNECTING (1 change)',
                            'legs': [first_leg, second_leg],
                            'total_distance_km': total_dist,
                            'estimated_delay_min': round(delay1 + delay2, 1),
                            'total_trains': 2,
                            'transfer_stations': [mid_station],
                            'transfer_wait_hours': round(time_gap, 1),
                            'feasible': feasible,
                            'estimated_total_time_hours': total_time_hr
                        })

    # ── 2-hop connections (if max_hops >= 2) ─────────────────────────
    if max_hops >= 2 and source in graph:
        for mid1, leg1 in graph[source]:
            if mid1 == destination:
                continue
            if mid1 in graph:
                for mid2, leg2 in graph[mid1]:
                    if mid2 == destination or mid2 == source:
                        continue
                    if mid2 in graph:
                        for final, leg3 in graph[mid2]:
                            if final == destination:
                                delay1 = leg1['avg_delay_min']
                                delay2 = leg2['avg_delay_min']
                                delay3 = leg3['avg_delay_min']

                                if model_bundle:
                                    delay1 = _predict_delay(model_bundle, leg1)
                                    delay2 = _predict_delay(model_bundle, leg2)
                                    delay3 = _predict_delay(model_bundle, leg3)

                                time_gap1 = leg2['scheduled_hour'] - leg1['scheduled_hour']
                                if time_gap1 < 0: time_gap1 += 24
                                time_gap2 = leg3['scheduled_hour'] - leg2['scheduled_hour']
                                if time_gap2 < 0: time_gap2 += 24

                                feasible = time_gap1 >= 1.0 and time_gap2 >= 1.0

                                total_dist = leg1['distance_km'] + leg2['distance_km'] + leg3['distance_km']
                                travel_time_hr = total_dist / 55.0
                                total_time_hr = travel_time_hr + time_gap1 + time_gap2 + ((delay1 + delay2 + delay3) / 60.0)

                                connections.append({
                                    'type': 'CONNECTING (2 changes)',
                                    'legs': [leg1, leg2, leg3],
                                    'total_distance_km': total_dist,
                                    'estimated_delay_min': round(delay1 + delay2 + delay3, 1),
                                    'total_trains': 3,
                                    'transfer_stations': [mid1, mid2],
                                    'transfer_wait_hours': round(time_gap1 + time_gap2, 1),
                                    'feasible': feasible,
                                    'estimated_total_time_hours': total_time_hr
                                })

    # Sort by: increasing estimated_total_time_hours
    connections.sort(key=lambda c: c['estimated_total_time_hours'])

    return connections


def _predict_delay(model_bundle, train_info):
    """Use the ML model to predict delay for a train leg."""
    model = model_bundle['model']
    le_train = model_bundle['le_train']
    le_source = model_bundle['le_source']
    le_dest = model_bundle['le_dest']

    try:
        train_enc = le_train.transform([train_info['train_name']])[0]
        source_enc = le_source.transform([train_info['source']])[0]
        dest_enc = le_dest.transform([train_info['destination']])[0]
    except ValueError:
        # Unknown train/station — fall back to average
        return train_info['avg_delay_min']

    now = datetime.now()
    features = [[
        train_enc, source_enc, dest_enc,
        train_info['distance_km'],
        train_info['scheduled_hour'],
        0,  # season
        7 if 'Daily' in str(train_info['frequency']) or 'Daliy' in str(train_info['frequency']) else 1,
        now.year
    ]]

    predicted = model.predict(features)[0]
    return max(0, round(predicted, 1))


# ─── DISPLAY RESULTS ────────────────────────────────────────────────────

def display_connections(connections, source, destination):
    """Pretty-print the connection results."""
    print(f"\n{'='*70}")
    print(f"  🚂 TRAIN CONNECTIONS: {source} → {destination}")
    print(f"{'='*70}")

    if not connections:
        print(f"\n  ⚠️  No connections found between {source} and {destination}")
        print(f"  Available stations:")
        return

    for i, conn in enumerate(connections, 1):
        print(f"\n  ┌─── Option {i}: {conn['type']} {'─'*40}")
        print(f"  │  Total distance: {conn['total_distance_km']:.0f} km")
        print(f"  │  Predicted delay: {conn['estimated_delay_min']:.0f} min")
        if 'estimated_total_time_hours' in conn:
            print(f"  │  Total travel time: {conn['estimated_total_time_hours']:.1f} hrs")

        if conn['transfer_stations']:
            print(f"  │  Transfer at: {' → '.join(conn['transfer_stations'])}")
            if 'transfer_wait_hours' in conn:
                feasible_icon = '✅' if conn.get('feasible', True) else '⚠️'
                print(f"  │  Wait time: {conn['transfer_wait_hours']:.1f} hrs {feasible_icon}")

        for j, leg in enumerate(conn['legs'], 1):
            tag = f"Leg {j}" if len(conn['legs']) > 1 else "Train"
            print(f"  │")
            print(f"  │  {tag}: {leg['train_name']} (#{leg['train_no']})")
            print(f"  │    {leg['source']} → {leg['destination']}")
            print(f"  │    Scheduled: {leg['scheduled_time']}  |  {leg['distance_km']:.0f} km")
            print(f"  │    Avg delay: {leg['avg_delay_min']:.0f} min  |  Runs: {leg['frequency']}")

        print(f"  └{'─'*65}")

    print(f"\n  📊 Total options found: {len(connections)}")


# ─── CONNECTION ENGINE CLASS ───────────────────────────────────────────

class ConnectionEngine:
    """
    Main engine for finding train connections and predicting delays.
    Encapsulates the ML model, route graph, and search logic.
    """
    def __init__(self, csv_path=None):
        self.df = None
        self.model_bundle = None
        self.graph = None
        self.all_stations = set()
        
        # Auto-find CSV if not provided
        if not csv_path:
            import os
            candidates = [
                os.path.join(os.path.dirname(__file__), '..', 'archive_extracted', 'indian_railway_delay_data_.csv'),
                os.path.join(os.path.dirname(__file__), 'indian_railway_delay_data_.csv'),
                'archive_extracted/indian_railway_delay_data_.csv',
                'indian_railway_delay_data_.csv',
            ]
            for c in candidates:
                if os.path.exists(c):
                    csv_path = c
                    break
        
        if csv_path:
            self.load_engine(csv_path)

    def load_engine(self, csv_path):
        """Initialize the engine by loading data and model."""
        self.df = load_and_clean_data(csv_path)
        self.model_bundle = train_delay_model(self.df)
        self.graph = build_route_graph(self.df)
        
        # Build station list
        self.all_stations = set(self.graph.keys())
        for routes in self.graph.values():
            for dest, _ in routes:
                self.all_stations.add(dest)

    def predict_delay(self, train_info):
        """Predict delay for a single train leg."""
        if not self.model_bundle:
            return train_info.get('avg_delay_min', 15)
        return _predict_delay(self.model_bundle, train_info)

    def get_connections(self, source, destination, max_hops=2):
        """Find and rank connections between two stations."""
        if not self.graph:
            return []
        return find_connections(self.graph, source, destination, self.model_bundle, max_hops)


# ─── MAIN ────────────────────────────────────────────────────────────────

def main():
    """Interactive loop for the standalone script."""
    engine = ConnectionEngine()
    
    if not engine.graph:
        print("Dataset not found! Make sure archive.zip is extracted.")
        return

    print(f"\n{'='*70}")
    print("  INDIAN RAILWAY CONNECTION FINDER (Integrated Engine)")
    print(f"{'='*70}")
    print(f"\n  Available stations ({len(engine.all_stations)}):")
    for s in sorted(engine.all_stations):
        print(f"    - {s}")

    # Ask user for From and To
    while True:
        print(f"\n{'='*70}")
        src = input("  From station (or 'quit' to exit): ").strip()
        if src.lower() in ('quit', 'exit', 'q'):
            print("  Goodbye!")
            break
        dst = input("  To station: ").strip()
        if not dst:
            continue

        connections = engine.get_connections(src, dst)
        display_connections(connections, src, dst)


if __name__ == "__main__":
    main()
