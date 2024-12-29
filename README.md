# NovelTextToJsonDatasetGenerator
这个脚本的主要功能是将小说文本文件处理成JSON格式的数据集，以便用于训练目的。
目的是方便产生供LLaMA-Factory进行微调使用的数据集，主要转换文本文件到json

以下是逐行解释：

### 1. 导入必要的库
```python
import os
import time
import json
from multiprocessing import Pool
import google.generativeai as genai
```
- `os`: 用于处理文件和目录路径。
- `time`: 用于获取当前时间和进行时间延迟。
- `json`: 用于处理JSON格式的数据。
- `multiprocessing.Pool`: 用于并行处理多个文件。
- `google.generativeai`: Google的生成式AI库，用于与Gemini API交互。

### 2. 配置Gemini API
```python
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
```
- 使用环境变量中的API密钥配置Gemini API。

### 3. 日志函数
```python
def log(message):
    """Logs a message with a timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
```
- 该函数用于打印带有时间戳的日志信息。

### 4. 上传文件到Gemini
```python
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
```
- 该函数将指定文件上传到Gemini，并返回文件对象。如果上传失败，会记录错误并抛出异常。

### 5. 等待文件激活
```python
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
```
- 该函数等待上传的文件在Gemini中变为“ACTIVE”状态。如果文件处理失败，会抛出异常。

### 6. 读取文本文件
```python
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
```
- 该函数读取指定文本文件的内容，并返回文件的所有行。如果读取失败，会记录错误并抛出异常。

### 7. 处理文本行
```python
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
```
- 该函数将文本行分割成指定最大大小的块，并返回这些块。

### 8. 转换为JSON记录
```python
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
```
- 该函数将文本块转换为JSON记录，每个记录包含一个指令、输入和输出。

### 9. 处理单个文件
```python
def process_single_file(file_path):
    """Processes a single file and returns JSON records."""
    log(f"Processing file: {file_path}")
    lines = read_text_file(file_path)
    sections = process_lines(lines)
    records = convert_to_records(sections)
    log(f"File '{file_path}' processed, {len(records)} records generated.")
    return records
```
- 该函数处理单个文件，读取文件内容，将其分割成块，并转换为JSON记录。

### 10. 生成JSON数据集
```python
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
```
- 该函数从指定目录中的文本文件生成JSON数据集。它使用多进程并行处理文件，并将结果保存到指定的输出目录中。

### 11. 主函数
```python
def main():
    # Upload file to Gemini
    file_path = r"G:\growupai\llama3-txt2json-dataset-maker\novel\近30年中国中篇小说精粹（棋王、小城之恋、天狗、红高粱、1934年的逃亡、伏羲伏羲、命若琴弦、桃花灿烂、生活秀、对面、上海女人、松鸦为什么.txt"
    uploaded_file = upload_to_gemini(file_path, mime_type="text/plain")
    
    # Wait for file to be active
    wait_for_files_active([uploaded_file])
    
    # Generate JSON dataset
    input_directory = os.path.dirname(file_path)
    generate_json_dataset(input_directory)
```
- 主函数首先上传文件到Gemini，然后等待文件激活，最后生成JSON数据集。

### 12. 脚本入口
```python
if __name__ == "__main__":
    main()
```
- 这是脚本的入口点，当脚本直接运行时，会调用`main()`函数。

### 总结
这个脚本通过读取小说文本文件，将其分割成块，并转换为JSON格式的数据集。它使用了Gemini API来上传文件，并利用多进程并行处理多个文件，最终生成一个可用于训练的JSON数据集。
