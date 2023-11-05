from ono.ner.natasha import NatashaClient

text = "Нетаньяху и Путин провели телефонный разговор. По сведениям газеты Haaretz, главной темой беседы стала ситуация вокруг сектора Газа"
data = NatashaClient("А " + text)
print(data.ner())
