from app.phoneme_parser import TextSynthesis

if __name__ == '__main__':
    file = open("file.txt", "r")
    text = file.read()
    TextSynthesis(text=text).synthesize_by_deleting_chunks()
