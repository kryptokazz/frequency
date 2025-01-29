import re
import argparse
from collections import Counter
import requests
from docx import Document
import nltk
from nltk.corpus import stopwords
import pysrt

# Download NLTK resources (run once)
nltk.download('punkt')
nltk.download('stopwords')

class TextProcessor:
    def __init__(self, language='english', custom_filter=None):
        self.stop_words = set(stopwords.words(language))
        self.custom_filter = custom_filter or set()
        self.word_pattern = re.compile(r'\b\w+\b', re.UNICODE)

    def process_file(self, file_path):
        if file_path.endswith('.srt'):
            return self._process_srt(file_path)
        elif file_path.endswith('.docx'):
            return self._process_docx(file_path)
        else:  # Assume plain text
            return self._process_text(file_path)

    def _process_text(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self._clean_text(text)

    def _process_docx(self, file_path):
        doc = Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return self._clean_text(text)

    def _process_srt(self, file_path):
        subs = pysrt.open(file_path)
        text = '\n'.join([sub.text for sub in subs])
        return self._clean_text(text)

    def _clean_text(self, text):
        text = text.lower()
        words = self.word_pattern.findall(text)
        filtered_words = [
            word for word in words 
            if word not in self.stop_words 
            and word not in self.custom_filter
        ]
        return filtered_words

class DictionaryAPI:
    def __init__(self, api_key=None):
        self.base_url = "https://api.dictionaryapi.dev/api/v2/entries/en/"
        self.api_key = api_key

    def get_definitions(self, word):
        try:
            response = requests.get(f"{self.base_url}{word}")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

def main():
    parser = argparse.ArgumentParser(description='Language Learning from Media Files')
    parser.add_argument('files', nargs='+', help='Input files (txt, srt, docx)')
    parser.add_argument('-t', '--top', type=int, default=50, help='Number of top words to analyze')
    parser.add_argument('-o', '--output', default='output.txt', help='Output file')
    args = parser.parse_args()

    # Initialize processor and API
    processor = TextProcessor(
        custom_filter={'like', 'get', 'go'}  # Add custom words to filter
    )
    dictionary = DictionaryAPI()

    # Process files and count words
    all_words = []
    for file in args.files:
        all_words.extend(processor.process_file(file))
    
    word_counts = Counter(all_words)
    top_words = word_counts.most_common(args.top)

    # Generate learning material
    with open(args.output, 'w', encoding='utf-8') as f:
        for word, count in top_words:
            f.write(f"\nWord: {word} (Frequency: {count})\n")
            
            data = dictionary.get_definitions(word)
            if data:
                for entry in data:
                    if 'meanings' in entry:
                        for meaning in entry['meanings']:
                            f.write(f"Part of Speech: {meaning['partOfSpeech']}\n")
                            if 'definitions' in meaning:
                                f.write(f"Definition: {meaning['definitions'][0]['definition']}\n")
                                if 'example' in meaning['definitions'][0]:
                                    f.write(f"Example: {meaning['definitions'][0]['example']}\n")
                            f.write("\n")
            else:
                f.write("No definition found\n")
            f.write("-"*50 + "\n")

if __name__ == "__main__":
    main()
