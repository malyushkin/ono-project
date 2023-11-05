import natasha

from typing import Any, List, Optional, Set, Union

MODEL_NAME = "natasha"
NATASHA_KEYS = {"LOC", "ORG", "PER"}

segmenter = natasha.Segmenter()
morph_vocab = natasha.MorphVocab()
emb = natasha.NewsEmbedding()
morph_tagger = natasha.NewsMorphTagger(emb)
syntax_parser = natasha.NewsSyntaxParser(emb)
ner_tagger = natasha.NewsNERTagger(emb)
names_extractor = natasha.NamesExtractor(morph_vocab)


class NatashaClient():
    def __init__(self, text: str, analyzers: Optional[List[str]] = None):
        """
        Args:
            text:
            analyzers:
        Returns:
            A new cursor object using the connection
        """

        self.text = text
        self.analyzers = analyzers if analyzers else NATASHA_KEYS

    def doc(self, text) -> natasha.Doc:
        doc = natasha.Doc(text)
        doc.segment(segmenter)
        doc.tag_morph(morph_tagger)
        doc.tag_ner(ner_tagger)
        return doc

    def ner(self) -> Set:
        doc: natasha.Doc = self.doc(self.text)
        for span in doc.spans:
            span.normalize(morph_vocab)
        return {(_.type, _.normal) for _ in doc.spans}

# text = "Нетаньяху и Путин провели телефонный разговор. По сведениям газеты Haaretz, главной темой беседы стала ситуация вокруг сектора Газа"
# data = NatashaClient("А " + text)
# print(data.ner())
