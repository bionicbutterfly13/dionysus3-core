"""
Script to convert generated JSON marketing assets to Markdown and export them.
Feature: 017-ias-marketing-suite
"""

import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("export_marketing")

SOURCE_DIR = "assets/"
TARGET_DIR = "/Volumes/Arkham/Marketing/stefan/assets/"

def convert_and_export():
    if not os.path.exists(SOURCE_DIR):
        logger.error(f"Source directory {SOURCE_DIR} not found.")
        return

    # Ensure target directory exists
    if not os.path.exists(TARGET_DIR):
        logger.error(f"Target directory {TARGET_DIR} not found. Ensure the volume is mounted.")
        # Fallback to local for testing
        target_path = "exported_assets/"
        os.makedirs(target_path, exist_ok=True)
    else:
        target_path = TARGET_DIR

    for filename in os.listdir(SOURCE_DIR):
        if not filename.endswith(".json"):
            continue
            
        with open(os.path.join(SOURCE_DIR, filename), "r") as f:
            data = json.load(f)
            
        base_name = filename.replace(".json", "")
        
        # Determine output filename
        if "email" in base_name:
            # email_05 -> IAS-email-05-v3.md
            num = base_name.split("_")[1]
            out_filename = f"IAS-email-{num}-v3.md"
            content = f"# Subject: {data.get('subject_line', 'No Subject')}\n\n{data.get('email_text', 'No Content')}"
        elif "sales_page" in base_name:
            out_filename = "IAS-tripwire-sales-page-v3.md"
            content = data.get("copy_text", str(data))
        elif "ias_scc" in base_name:
            out_filename = "IAS-SCC-VSL-script-v3.md"
            # For SCC, it's a complex object, we'll dump it as formatted text if it's not already
            if isinstance(data, dict) and "hook" in data:
                content = f"# {data.get('name', 'SCC Script')}\n\n"
                content += f"## Section 1: Hook\n{data['hook'].get('opening_statement', 'TBD')}\n\n"
                # ... Add other sections as needed
            else:
                content = str(data)
        else:
            out_filename = f"{base_name}.md"
            content = str(data)

        with open(os.path.join(target_path, out_filename), "w") as f:
            f.write(content)
            
        logger.info(f"Exported {filename} -> {out_filename}")

if __name__ == "__main__":
    convert_and_export()
