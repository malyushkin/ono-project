## I. Install Pullenti Server

1. Pull `pullenti` container:

```shell
sudo docker pull pullenti/pullenti-server
```

2. Run it on 8081 port:

```shell
sudo docker run -d --name pullenti --platform linux/amd64 -v $(pwd)/pullenti-server/conf.xml:/app/conf.xml -p 8081:8080 pullenti/pullenti-server
```

3. Check server by command:

```shell
curl localhost:8081 -d 'Варшава — столица и крупнейший по населению и занимаемой территории город Польши. Город стал столицей в 1596 году, когда после пожара в Вавельском замке в Кракове король Сигизмунд III перенёс сюда свою резиденцию. Столичный статус города, был подтверждён только в Конституции 1791 года. Через город протекает река, Висла, разделяющая город приблизительно поровну.'
```

```text
<?xml version="1.0" encoding="utf-8"?>
<result>
  <referent id="41396006" type="GEO" />
  <slot parent="41396006" value="PL" key="ALPHA2" />
  <slot parent="41396006" value="РЕСПУБЛИКА ПОЛЬША" key="NAME" />
  <slot parent="41396006" value="ПОЛЬША" key="NAME" />
  <slot parent="41396006" value="государство" key="TYPE" />
  <referent id="55257223" type="GEO" />
  <slot parent="55257223" value="ВАРШАВА" key="NAME" />
  <slot parent="55257223" value="город" key="TYPE" />
  <referent id="51903897" type="PERSONPROPERTY" />
  <slot parent="51903897" value="король" key="NAME" />
  <referent id="31251362" type="PERSON" />
  <slot parent="31251362" value="MALE" key="SEX" />
  <slot parent="31251362" value="III" key="NICKNAME" />
  <slot parent="31251362" value="СИГИЗМУНД" key="FIRSTNAME" />
  <slot parent="31251362" referent="51903897" key="ATTRIBUTE" />
  <match id="15449714" referent="55257223" start="0" stop="7" />
  <match id="34768531" referent="41396006" start="74" stop="80" />
  <match id="11367247" referent="31251362" start="163" stop="183" />
  <match id="17934983" parent="11367247" referent="51903897" start="163" stop="169" />
</result>  
```

4. Stop `pullenti` container:

```shell
docker kill pullenti
```

5. Remove `pullenti` container:

```shell
docker rm pullenti
```

## II. Install Pullenti Client

1. Install Pyhton venv:

```shell
python3 -m venv ./pullenti-client/vevn
```

2. Copy setup and demo scripts to client folder:

```shell
cp ./demo/setup.py ./pullenti-client/setup.py
cp ./demo/script.py ./pullenti-client/script.py
```

3. Install libs:

```shell
pip install -e ./pullenti-client
```

4. Run puthon script:

```shell
source ./pullenti-client/vevn/bin/activate
python3 pullenti-client/script.py
```

```
[Match(referent=Referent(label='PERSON', slots=[Slot(key='SEX', value='MALE'), Slot(key='LASTNAME', value='ШТЮБГЕН'), Slot(key='FIRSTNAME', value='БРАНДЕНБУРГ'), Slot(key='MIDDLENAME', value='МИХАЭЛЬ'), Slot(key='ATTRIBUTE', value=Referent(label='PERSONPROPERTY', slots=[Slot(key='NAME', value='министр внутренних дел федеральной земли')]))]), span=Span(start=1, stop=69), children=[Match(referent=Referent(label='PERSONPROPERTY', slots=[Slot(key='NAME', value='министр внутренних дел федеральной земли')]), span=Span(start=1, stop=41), children=[])]), Match(referent=Referent(label='GEO', slots=[Slot(key='ALPHA2', value='PL'), Slot(key='NAME', value='РЕСПУБЛИКА ПОЛЬША'), Slot(key='NAME', value='ПОЛЬША'), Slot(key='TYPE', value='государство')]), span=Span(start=176, stop=183), children=[]), Match(referent=Referent(label='ORGANIZATION', slots=[Slot(key='PROFILE', value='Media'), Slot(key='PROFILE', value='Press'), Slot(key='TYPE', value='газета'), Slot(key='NAME', value='NEUE OSNABRÜCKER ZEITUNG')]), span=Span(start=380, stop=411), children=[]), Match(referent=Referent(label='PERSON', slots=[Slot(key='SEX', value='MALE'), Slot(key='LASTNAME', value='ШТЮБГЕН'), Slot(key='FIRSTNAME', value='БРАНДЕНБУРГ'), Slot(key='MIDDLENAME', value='МИХАЭЛЬ'), Slot(key='ATTRIBUTE', value=Referent(label='PERSONPROPERTY', slots=[Slot(key='NAME', value='министр внутренних дел федеральной земли')]))]), span=Span(start=464, stop=472), children=[])]
```