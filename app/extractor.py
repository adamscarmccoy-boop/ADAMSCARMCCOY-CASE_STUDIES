import gzip
import os
import xml.etree.ElementTree as ET

import pyarrow as pa
import pyarrow.parquet as pq

from app.config import settings


def extract_and_index_session(input_path: str) -> str:
    """
    Unpacks Gzipped Ableton XML project file entirely in-memory and 
    streams track configurations straight to a matching local Parquet ledger.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ Input Ableton file missing at: {input_path}")
        
    # Standardize matching name convention for the output parquet target
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_parquet_path = str(settings.parquet_lakehouse_dir / f"{base_name}.parquet")
    
    # Decompress Gzip data straight to RAM
    with gzip.open(input_path, 'rb') as f:
        xml_content = f.read()
        
    root = ET.fromstring(xml_content)
    
    track_ids, track_names, track_types, plugin_lists, referenced_samples = [], [], [], [], []
    tracks_node = root.find(".//Tracks")
    
    if tracks_node is None:
        raise ValueError("Malformed file configuration: No <Tracks> collection located.")
        
    for track in tracks_node:
        t_id = int(track.get("Id", -1))
        name_node = track.find(".//Name/EffectiveName")
        t_name = name_node.get("Value", "Untitled") if name_node is not None else "Untitled"
        t_type = track.tag
        
        devices = []
        device_chain = track.find(".//DeviceChain/DeviceChain/Devices")
        if device_chain is not None:
            for device in device_chain:
                dev_name_node = device.find(".//UserName")
                dev_name = dev_name_node.get("Value", "") if dev_name_node is not None else ""
                if not dev_name:
                    dev_name = device.tag
                devices.append(dev_name)
                
        track_ids.append(t_id)
        track_names.append(t_name)
        track_types.append(t_type)
        plugin_lists.append(devices)
        
        sample_files = []
        seen_samples = set()
        for sample_ref in track.findall(".//SampleRef"):
            rel_path_node = sample_ref.find(".//RelativePath")
            if rel_path_node is not None:
                val = rel_path_node.get("Value")
                if val:
                    # ⚡ Bolt Optimization: Use os.path.basename instead of nested pathlib import
                    # and use a set for O(1) membership checking instead of O(N) list search.
                    filename = os.path.basename(val)
                    if filename not in seen_samples:
                        seen_samples.add(filename)
                        sample_files.append(filename)
        referenced_samples.append(sample_files)

    # Instantiate zero-copy Apache Arrow Data Representation Table
    schema = pa.schema([
        ('track_id', pa.int64()),
        ('track_name', pa.string()),
        ('track_type', pa.string()),
        ('active_plugins', pa.list_(pa.string())),
        ('referenced_samples', pa.list_(pa.string()))
    ])
    arrow_table = pa.Table.from_arrays(
        [track_ids, track_names, track_types, plugin_lists, referenced_samples], schema=schema
    )
    
    # Commit binary array directly to local data storage
    pq.write_table(arrow_table, output_parquet_path)
    return output_parquet_path
