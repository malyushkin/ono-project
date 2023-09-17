from pullenti_client import Client

pullenti_client = Client("localhost", 8081)

demo_text = """
Министр внутренних дел федеральной земли Бранденбург Михаэль Штюбген обеспокоен все 
менее контролируемой ситуацией с наплывом нелегальных мигрантов через границу с 
соседней Польшей. "Ситуация на границе систематически ухудшается уже многие месяцы. 
В результате число новоприбывших, регистрируемых в приемных центрах Бранденбурга, 
значительно выросло", - заявил он в интервью газете Neue Osnabrücker Zeitung, 
обнародованном в субботу, 16 сентября.

По словам Штюбгена, сейчас федеральная полиция ежедневно направляет в приемный центр в 
среднем по 58 мигрантов, тогда как только в июле ежедневное число предполагаемых 
нелегалов составляло 22 человека.
"""

result = pullenti_client(demo_text)
print(result)
