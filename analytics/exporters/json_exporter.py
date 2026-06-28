import json
import os
from utils.logger import log_info, log_error

def export_to_json(run_result, output_path):
    """
    Serializes the ScreenerRunResult object to JSON and writes it to the output_path.
    """
    try:
        # Ensure directories exist
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        data_dict = run_result.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
        log_info("JSON_EXPORT", status="SUCCESS", message=f"Exported JSON snapshot to {output_path}")
        return True
    except Exception as e:
        log_error("JSON_EXPORT", error_message=f"Failed to export JSON: {str(e)}")
        return False
