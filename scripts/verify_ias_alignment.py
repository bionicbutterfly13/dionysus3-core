import csv
import re
import sys
from pathlib import Path

def parse_ts_file(ts_path):
    content = Path(ts_path).read_text()
    
    # Extract Lessons
    # This is a rough regex, assuming the structure is consistent
    lessons = {}
    
    # Find all lessons
    lesson_blocks = re.split(r'id:\s*[\'"]lesson-\d+[\'"]', content)
    
    # We skip the first split as it's before the first lesson or the header
    # Actually, let's process the whole file looking for specific patterns
    
    # Pattern for Lesson
    # id: 'lesson-1', name: 'Breakthrough Basics', ... actions: [ ... ]
    
    # Let's iterate over phases then lessons then actions to be safer, or just flatten it
    
    # Extract all objects that look like actions with obstacles
    # structure: { id: 'action-X-Y', name: 'NAME', ... obstacles: [ { name: 'OBS_NAME' } ] }
    
    # Regex to capture Action Name and its Obstacles
    # We assume 'name' comes before 'obstacles'
    
    # Let's clean the content to make it easier (remove comments, excessive whitespace)
    # content = re.sub(r'//.*', '', content)
    
    # Find all actions
    action_pattern = re.compile(r"id:\s*['\"]action-(\d+)-(\d+)['\"],\s*name:\s*['\"](.*?)['\"],.*?obstacles:\s*\[(.*?)\]", re.DOTALL)
    
    matches = action_pattern.findall(content)
    
    data_ts = {} # Key: (LessonNum, ActionNum) -> [ObstacleNames]
    
    obstacle_pattern = re.compile(r"name:\s*['\"](.*?)['\"]")
    
    for lesson_num, action_num, action_name, obstacles_block in matches:
        obs_names = obstacle_pattern.findall(obstacles_block)
        data_ts[(int(lesson_num), int(action_num))] = {
            'action_name': action_name,
            'obstacles': obs_names
        }
        
    return data_ts

def parse_csv_file(csv_path):
    data_csv = {} # Key: (LessonNum, ActionNum) -> [ObstacleNames]
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        
        current_lesson_num = 0
        
        for row in reader:
            lesson_cell = row['Lesson']
            if lesson_cell:
                # Extract number "Lesson 1: ..."
                m = re.match(r"Lesson (\d+):", lesson_cell)
                if m:
                    current_lesson_num = int(m.group(1))
            
            action_cell = row['Action']
            # "Action 1: Choose patterns to address"
            m = re.match(r"Action (\d+): (.*)", action_cell)
            if m:
                action_num = int(m.group(1))
                action_name = m.group(2).strip()
                
                obstacles_cell = row['Obstacles']
                # "1. Name\n2. Name..."
                # split by newline
                obs_lines = obstacles_cell.split('\n')
                obs_names = []
                for line in obs_lines:
                    # remove "1. "
                    line = line.strip()
                    if not line: continue
                    clean_line = re.sub(r'^\d+\.\s*', '', line)
                    obs_names.append(clean_line)
                
                data_csv[(current_lesson_num, action_num)] = {
                    'action_name': action_name,
                    'obstacles': obs_names
                }
                
    return data_csv

def main():
    ts_path = '/Volumes/Asylum/dev/dionysus3-core/dionysus-dashboard/src/lib/ias-curriculum.ts'
    csv_path = '/Volumes/Asylum/dev/dionysus3-core/data/ground-truth/MOSAEIC Inner Architect Obstacle Matrix - IAS_Obstacle_Catalog_CleanedFormat.csv (1).csv'
    
    print(f"Verifying alignment between:\nCSV: {csv_path}\nTS:  {ts_path}\n")
    
    ts_data = parse_ts_file(ts_path)
    csv_data = parse_csv_file(csv_path)
    
    mismatches = []
    
    # Check coverage
    all_keys = set(ts_data.keys()) | set(csv_data.keys())
    
    for key in sorted(all_keys):
        l, a = key
        in_ts = key in ts_data
        in_csv = key in csv_data
        
        if not in_ts:
            mismatches.append(f"Missing in TS: Lesson {l} Action {a}")
            continue
        if not in_csv:
            mismatches.append(f"Missing in CSV: Lesson {l} Action {a}")
            continue
            
        ts_item = ts_data[key]
        csv_item = csv_data[key]
        
        # Check Action Name
        if ts_item['action_name'] != csv_item['action_name']:
            mismatches.append(f"Action Name Mismatch L{l}A{a}: TS='{ts_item['action_name']}' vs CSV='{csv_item['action_name']}'")
            
        # Check Obstacles
        ts_obs = ts_item['obstacles']
        csv_obs = csv_item['obstacles']
        
        if len(ts_obs) != len(csv_obs):
             mismatches.append(f"Obstacle Count Mismatch L{l}A{a}: TS={len(ts_obs)} vs CSV={len(csv_obs)}")
        else:
            for i in range(len(ts_obs)):
                if ts_obs[i] != csv_obs[i]:
                     mismatches.append(f"Obstacle Mismatch L{l}A{a}#{i+1}:\n  TS : {ts_obs[i]}\n  CSV: {csv_obs[i]}")

    if mismatches:
        print("❌ FAIL: Alignments mismatches found:")
        for m in mismatches:
            print(f" - {m}")
        sys.exit(1)
    else:
        print("✅ SUCCESS: CSV and TS data are perfectly aligned.")
        sys.exit(0)

if __name__ == "__main__":
    main()
