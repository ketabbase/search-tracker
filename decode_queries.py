#!/usr/bin/env python3
"""
Script to decode URL-encoded Persian queries from Search Tracker CSV files.
This will help you see what the Persian text actually says.
"""

import urllib.parse
import csv
import os
import sys

def decode_query(encoded_query):
    """Decode URL-encoded query to readable text"""
    try:
        return urllib.parse.unquote_plus(encoded_query)
    except Exception as e:
        print(f"Error decoding query: {e}")
        return encoded_query

def process_queries_csv(csv_file_path):
    """Process a queries.csv file and show decoded queries"""
    if not os.path.exists(csv_file_path):
        print(f"File not found: {csv_file_path}")
        return
    
    print(f"Processing: {csv_file_path}")
    print("=" * 60)
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
        if len(rows) < 2:
            print("No queries found in the file.")
            return
            
        print(f"Found {len(rows)-1} queries:")
        print()
        
        for i, row in enumerate(rows[1:], 1):  # Skip header row
            if len(row) >= 2:
                timestamp = row[0]
                encoded_query = row[1]
                decoded_query = decode_query(encoded_query)
                
                print(f"Query {i}:")
                print(f"  Timestamp: {timestamp}")
                print(f"  Encoded:   {encoded_query}")
                print(f"  Decoded:   {decoded_query}")
                print()

def main():
    """Main function to decode queries"""
    print("Search Tracker Query Decoder")
    print("=" * 60)
    
    # Check if a specific file was provided
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        process_queries_csv(csv_file)
    else:
        # Look for the most recent queries.csv file
        data_dir = "data"
        if os.path.exists(data_dir):
            # Find the most recent directory
            subdirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
            if subdirs:
                latest_dir = sorted(subdirs)[-1]
                queries_file = os.path.join(data_dir, latest_dir, "queries.csv")
                process_queries_csv(queries_file)
            else:
                print("No data directories found in ./data/")
        else:
            print("Data directory not found. Please specify the path to queries.csv")
            print("Usage: python decode_queries.py [path/to/queries.csv]")

if __name__ == "__main__":
    main()