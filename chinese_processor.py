import re
import argparse
from collections import Counter
import jieba
import jieba.analyse
import pysrt
from docx import Document
import requests
from pypinyin import pinyin, Style
import opencc

# Initialize converter for Traditional to Simplified Chinese
converter = opencc.OpenCC('t2s.json')

class ChineseTextProcessor:
    def __init__(self, stopwords_path='chinese_stopwords.txt', custom_filter=None):
        self.stopwords = self._load_stopwords(stopwords_path)
        self.custom_filter = custom_filter or set()
        jieba.setLogLevel(jieba.logging.INFO)

    def _load_stopwords(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f)
        except FileNotFoundError:
            print(f"Stopwords file {path} not found. Using empty stopwords list.")
            return set()

    def process_file(self, file_path):
        print(f"Processing file: {file_path}")
        if file_path.endswith('.srt'):
            return self._process_srt(file_path)
        elif file_path.endswith('.docx'):
            return self._process_docx(file_path)
        else:
            return self._process_text(file_path)

    def _process_text(self, file_path):
        print(f"Reading text file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self._process_content(text)

    def _process_docx(self, file_path):
        print(f"Reading DOCX file: {file_path}")
        doc = Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return self._process_content(text)

    def _process_srt(self, file_path):
        print(f"Reading SRT file: {file_path}")
        subs = pysrt.open(file_path)
        text = '\n'.join([sub.text for sub in subs])
        return self._process_content(text)

    def _process_content(self, text):
        print("Processing content...")
        # Convert Traditional to Simplified Chinese
        text = converter.convert(text)
        # Remove non-Chinese characters
        text = re.sub(r'[^\u4e00-\u9fff]', ' ', text)
        # Tokenize with Jieba
        words = jieba.lcut(text)
        # Filter short words and stopwords
        filtered_words = [
            word for word in words 
            if len(word) > 1 
            and word not in self.stopwords 
            and word not in self.custom_filter
        ]
        print(f"Filtered {len(filtered_words)} words.")
        return filtered_words

class ChineseDictionaryAPI:
    def __init__(self):
        self.base_url = "https://api.openccce.com/cedict/"

    def get_definitions(self, word):
        try:
            print(f"Fetching definition for: {word}")
            response = requests.get(f"{self.base_url}{word}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Chinese Language Learning from Movies')
    parser.add_argument('files', nargs='+', help='Input files (txt, srt, docx)')
    parser.add_argument('-t', '--top', type=int, default=50, help='Number of top words to analyze')
    parser.add_argument('-o', '--output', default='output.txt', help='Output file')
    parser.add_argument('--stopwords', default='chinese_stopwords.txt', 
                      help='Path to Chinese stopwords file')
    args = parser.parse_args()

    print("Initializing ChineseTextProcessor...")
    processor = ChineseTextProcessor(
        stopwords_path=args.stopwords,
        custom_filter={'这个', '那个', '可以'}  # Add custom filter words
    )
    dictionary = ChineseDictionaryAPI()

    # Process files and count words
    all_words = []
    for file in args.files:
        print(f"Processing file: {file}")
        all_words.extend(processor.process_file(file))
    
    print("Counting words...")
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(args.top)

    # Generate learning material
    print(f"Writing output to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        for word, count in top_words:
            f.write(f"\n汉字: {word} (出现次数: {count})\n")
            
            # Get Pinyin
            pinyin_str = ' '.join([item[0] for item in pinyin(word, style=Style.TONE3)])
            f.write(f"拼音: {pinyin_str}\n")
            
            # Get dictionary definitions
            data = dictionary.get_definitions(word)
            if data and 'definitions' in data:
                for idx, definition in enumerate(data['definitions'][:3], 1):
                    f.write(f"{idx}. {definition['definition']}\n")
                    if 'example' in definition:
                        example = converter.convert(definition['example'])
                        f.write(f"   例句: {example}\n")
            else:
                f.write("未找到词典定义\n")
            
            f.write("-"*60 + "\n")
    
    print("Done! Check the output file for results.")

if __name__ == "__main__":
    main()
