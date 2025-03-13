import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import os

def plot_process_timeline(json_file, output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    processes = defaultdict(list)
    for event in data:
        if isinstance(event['timestamp'], str):
            event['timestamp'] = int(float(event['timestamp']))
        
        if 'vpid' in event:
            processes[event['vpid']].append(event)
    
    min_time = min(event['timestamp'] for event in data)
    
    for pid, events in processes.items():
        procname = events[0]['procname'] if 'procname' in events[0] else f"Unknown-{pid}"
        
        event_types = sorted(set(event['event'] for event in events))
        
        num_event_types = len(event_types)
        fig, axes = plt.subplots(num_event_types, 1, figsize=(15, num_event_types * 1.2), sharex=True)
        
        if num_event_types == 1:
            axes = [axes]
        
        colors = plt.cm.tab10.colors
        
        for i, event_type in enumerate(event_types):
            ax = axes[i]
            
            type_events = [e for e in events if e['event'] == event_type]
            
            type_events.sort(key=lambda x: x['timestamp'])
            
            times = [(e['timestamp'] - min_time) / 1e9 for e in type_events]
            y_values = [0] * len(times)
            
            ax.scatter(times, y_values, color=colors[i % len(colors)], s=30, alpha=0.8)
            
            ax.set_yticks([])
            ax.set_ylabel(event_type.split(':')[-1], fontsize=8, rotation=0, ha='right', va='center')
            
            ax.grid(True, axis='x', linestyle='--', alpha=0.5)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False)
        
        axes[-1].set_xlabel('Time (seconds since trace start)')
        
        total_duration = (max(e['timestamp'] for e in events) - min_time) / 1e9
        
        axes[0].set_xlim(-0.1, total_duration + 0.1)
        
        plt.suptitle(f'ros2-tracer Trace Timeline\nProcess Name: {procname}\nProcess ID: {pid}', fontsize=14)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.9, hspace=0.3)
        
        output_file = os.path.join(output_dir, f"process_{pid}_{procname}.png")
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print(f"Generated timeline for process {procname} (ID: {pid})")

if __name__ == "__main__":
    json_file = "trace.json"
    
    plot_process_timeline(json_file)
