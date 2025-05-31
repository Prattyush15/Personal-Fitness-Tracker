import xml.etree.ElementTree as ET
import pandas as pd
import os

# This script parses an Apple Health export XML file and extracts workout data.
# It saves the extracted data into a CSV file for further analysis.

def parse_apple_health_export(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract workouts
    workouts = []
    for workout in root.findall('Workout'):
        data = {
            'workoutActivityType': workout.attrib.get('workoutActivityType'),
            'startDate': workout.attrib.get('startDate'),
            'endDate': workout.attrib.get('endDate'),
            'duration': workout.attrib.get('duration'),
            'totalDistance': workout.attrib.get('totalDistance'),
            'totalEnergyBurned': workout.attrib.get('totalEnergyBurned'),
            'sourceName': workout.attrib.get('sourceName'),
            'sourceVersion': workout.attrib.get('sourceVersion'),
            'device': workout.attrib.get('device'),
        }
        workouts.append(data)
    return workouts


if __name__ == "__main__":
    xml_path = os.path.join(os.path.dirname(__file__), 'export.xml')
    if not os.path.exists(xml_path):
        print("Place your Apple Health export.xml in this folder first.")
        exit(1)

    workouts = parse_apple_health_export(xml_path)
    df = pd.DataFrame(workouts)
    df.to_csv('apple_health_workouts.csv', index=False)
    print(f"Saved {len(df)} workouts to apple_health_workouts.csv") 