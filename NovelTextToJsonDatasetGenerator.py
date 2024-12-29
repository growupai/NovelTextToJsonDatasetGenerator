# NovelTextToJsonDatasetGenerator: A script to process novel text files, upload them to Gemini, and generate a JSON dataset for training purposes.
import os
import time
import json
from multiprocessing import Pool
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def log(message):
    """Logs a message with a timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def upload_to_gemini(file_path, mime_type=None):
    """Uploads a file to Gemini and returns the file object."""
    try:
        log(f"Uploading file: {file_path}")
        file = genai.upload_file(file_path, mime_type=mime_type)
        log(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        log(f"Failed to upload file: {e}")
        raise

def wait_for_files_active(files):
    """Waits for uploaded files to become active."""
    log("Waiting for file processing...")
    for file in files:
        while True:
            file_status = genai.get_file(file.name)
            if file_status.state.name == "ACTIVE":
                log(f"File '{file.display_name}' is now active.")
                break
            elif file_status.state.name == "FAILED":
                raise Exception(f"File {file.name} failed to process")
            log(f"File '{file.display_name}' is still processing...")
            time.sleep(10)
    log("All files are ready.\n")

def read_text_file(file_path):
    """Reads a text file and returns its lines."""
    try:
        log(f"Reading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        log(f"File '{file_path}' read successfully, {len(lines)} lines found.")
        return lines
    except Exception as e:
        log(f"Error reading file {file_path}: {e}")
        raise

def process_lines(lines, max_size=512):
    """Splits text lines into chunks of specified maximum size."""
    log("Processing lines into chunks...")
    sections = []
    section = ""
    for line in lines:
        if len(section) + len(line) < max_size:
            section += line
        else:
            sections.append(section)
            section = line
    if section:
        sections.append(section)
    log(f"Lines processed into {len(sections)} chunks.")
    return sections

def convert_to_records(sections):
    """Converts text chunks into JSON records."""
    log("Converting chunks to JSON records...")
    records = []
    for i in range(0, len(sections) - 1, 2):
        record = {
            'instruction': '下列为一部小说中的一部分内容，请参照这部分内容，续写下一部分。',
            'input': sections[i],
            'output': sections[i + 1]
        }
        records.append(record)
    log(f"Converted {len(records)} records.")
    return records

def process_single_file(file_path):
    """Processes a single file and returns JSON records."""
    log(f"Processing file: {file_path}")
    lines = read_text_file(file_path)
    sections = process_lines(lines)
    records = convert_to_records(sections)
    log(f"File '{file_path}' processed, {len(records)} records generated.")
    return records

def generate_json_dataset(input_dir, output_dir="./ok"):
    """Generates a JSON dataset from text files in the input directory."""
    log(f"Generating JSON dataset from directory: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)
    text_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.txt')]
    log(f"Found {len(text_files)} text files: {text_files}")
    
    with Pool() as pool:
        log("Starting multiprocessing pool for file processing...")
        results = pool.map(process_single_file, text_files)
    
    records = [record for sublist in results for record in sublist]
    log(f"All files processed, total {len(records)} records generated.")
    
    output_file = os.path.join(output_dir, 'dataset.json')
    log(f"Writing records to JSON file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=4, ensure_ascii=False)
    
    log(f"JSON dataset saved to {output_file}")
    return records

def main():
    # Upload file to Gemini
    file_path = r"G:\growupai\llama3-txt2json-dataset-maker\novel\近30年中国中篇小说精粹（棋王、小城之恋、天狗、红高粱、1934年的逃亡、伏羲伏羲、命若琴弦、桃花灿烂、生活秀、对面、上海女人、松鸦为什么.txt"
    uploaded_file = upload_to_gemini(file_path, mime_type="text/plain")
    
    # Wait for file to be active
    wait_for_files_active([uploaded_file])
    
    # Generate JSON dataset
    input_directory = os.path.dirname(file_path)
    generate_json_dataset(input_directory)

if __name__ == "__main__":
    main()