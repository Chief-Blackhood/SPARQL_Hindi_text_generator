import sys
import re
from SPARQLWrapper import SPARQLWrapper, JSON

query = [
    """SELECT ?instanceLabel
    WHERE
    {
      wd:@SUBJECT@ wdt:@PROPERTY@ ?instance.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "hi". }
    }""",
    """SELECT ?instanceLabel
    WHERE
    {
      wd:@SUBJECT@ schema:description ?instanceLabel.
      FILTER ( lang(?instanceLabel) = "hi" )
    }""",
    """SELECT ?instanceLabel
    WHERE
    {
      ?instance wdt:P131 wd:@SUBJECT@;
                wdt:P31 ?type
                FILTER (?type IN (wd:Q27686, wd:Q143912, wd:Q811979 ) )
      
      SERVICE wikibase:label { bd:serviceParam wikibase:language "hi". }
    }
    LIMIT 9"""
]

template = [
    "@SUBJECT@ @OBJECT@ है।",
    "@SUBJECT@ @OBJECT@ का हिस्सा है।",
    "@SUBJECT@ @OBJECT@ की प्रशासनिक क्षेत्रीय इकाई में स्थित है",
    "@SUBJECT@ @COUNTRY@ का @OBJECT@ है।",
    "इसकी जनसंख्या @POPULATION@ है।",
    "@SUBJECT@ में @LANGUAGES@ जैसी कई भाषाएं बोली जाती हैं।",
    "@AUTHORITY@ @SUBJECT@ की विकास प्राधिकरण है।",
    "समुद्र तल से इसकी ऊंचाई @HEIGHT@ मीटर है।",
    "@SUBJECT@ का समय क्षेत्र @TIMEZONE@ है।",
    "इसका क्षेत्रफल @AREA@ किलोमीटर वर्ग में फैला है।",
    "इसके मुख्य आकर्षण और पर्यटन स्थल @MONUMENTS@ हैं।",
    "यह @OBJECT@ है।",
    "@SUBJECT@ का पोस्टल कोड @CODE@ है।",
    "इसका समन्वय @LATLONG@ है।",
    "इसका नाम @NAME@ के नाम पर रखा गया है।",
    "यह एयरपोर्ट @OWNED@ अथॉरिटी के अंतर्गत आता है।",
    "इसका IATA कोड @CODE@ है।",
    "ट्विटर पर इसके @NUMBER@ सोशल मीडिया फॉलोअर्स हैं।",
    "इसकी उद्घाटन तिथि @DATE@ है।",
    "इसका प्रशासन स्थान @LOCATION@ है।",
    "इस स्टेशन का रेलवे ऑपरेटर @OPERATOR@ है।",
    "यह स्टेशन @OWNED@ अथॉरिटी के अंतर्गत आता है।"
]


class Generator:
    def __init__(self, queries, template, subject=""):
        if queries is None:
            queries = []
        self.queries = queries
        self.template = template
        self.endpoint_url = "https://query.wikidata.org/sparql"
        self.data = {}
        self.subject = subject
        self.airport_name = "छत्रपति शिवाजी महाराज"
        self.railway_name = "मुंबई सेंट्रल"
        self.text = ""
        self.property_mapping = {"part of": "P361", "country": "P17", "lat long": "P625", "authority": "P797",
                                 "population": "P1082", "elevation above sea level": "P2044",
                                 "located in time zone": "P421", "language used": "P2936", "size": "P2046",
                                 "postal code": "P281"}
        self.airport_property_mapping = {"airport instance of": "P31", "airport country": "P17",
                                         "airport named after": "P138", "airport lat long": "P625",
                                         "airport elevation above sea level": "P2044", "airport owned by": "P127",
                                         "IATA code": "P238", "airport social media followers": "P8687"}
        self.railway_property_mapping = {"railway instance of": "P31", "railway country": "P17",
                                         "railway administration location": "P131", "railway opening data": "P1619",
                                         "railway owned by": "P127", "railway lat long": "P625",
                                         "railway operator": "P137"
                                         }

    def get_results(self, query):
        user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
        sparql = SPARQLWrapper(self.endpoint_url, agent=user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

    def add_info(self, row=0, subject_id="", property="", query_no=0, key=""):
        query_str = self.queries[query_no]
        if property != "":
            query_str = query_str.replace("@PROPERTY@", property)
        if subject_id != "":
            query_str = query_str.replace("@SUBJECT@", subject_id)
        result = self.get_results(query=query_str)
        value = result["results"]["bindings"][row]['instanceLabel']['value']
        if value.startswith("Point"):
            value = value[6:-1]
        if key in ["language used", "monuments"]:
            temp = ""
            for result in result["results"]["bindings"]:
                if not result['instanceLabel']['value'].startswith('Q'):
                    temp += result['instanceLabel']['value'] + ', '
            value = temp[:-2]
        self.data[key] = value

    def get_info(self):
        self.add_info(query_no=0, row=4, subject_id="Q1156", property="P31", key="instance of")
        self.add_info(query_no=1, subject_id="Q1156", key="description")
        self.add_info(query_no=2, subject_id="Q1156", key="monuments")

        for key, value in self.property_mapping.items():
            self.add_info(subject_id="Q1156", property=value, key=key)
        for key, value in self.airport_property_mapping.items():
            self.add_info(subject_id="Q504368", property=value, key=key)
        for key, value in self.railway_property_mapping.items():
            self.add_info(subject_id="Q3539796", property=value, key=key)
        self.add_info(query_no=0, row=1, subject_id="Q504368", property="P138", key="airport named after")
        # self.add_info(query_no=0, row=0, subject_id="Q1156", property="P2936", key="language used")

    def create_line(self, replacement, template_no=0):
        out_template = self.template[template_no]
        to_replace = re.findall(r'@\b\S+?\b@', out_template)
        for i in range(len(replacement)):
            out_template = re.sub(to_replace[i], replacement[i], out_template, 1)
        self.text += out_template + ' '

    def generate_text(self):
        # for key, value in self.data.items():
        #     print(key, value)

        self.create_line(template_no=3, replacement=[self.subject, self.data['country'], self.data['instance of']])
        self.create_line(template_no=11, replacement=[self.data['description']])
        self.create_line(template_no=1, replacement=[self.subject, self.data['part of']])
        self.create_line(template_no=4, replacement=[self.data['population']])
        self.text += '\n'
        self.create_line(template_no=5, replacement=[self.subject, self.data['language used']])
        self.create_line(template_no=6, replacement=[self.data['authority'], self.subject])
        self.text += '\n'
        self.create_line(template_no=7, replacement=[self.data['elevation above sea level']])
        self.create_line(template_no=8, replacement=[self.subject, self.data['located in time zone']])
        self.create_line(template_no=9, replacement=[self.data['size']])
        self.create_line(template_no=13, replacement=[self.data['lat long']])
        self.text += '\n'
        self.create_line(template_no=10, replacement=[self.data['monuments']])
        self.create_line(template_no=12, replacement=[self.subject, self.data['postal code']])
        self.text += '\n\n'
        self.create_line(template_no=3, replacement=[self.airport_name, self.subject, self.data['airport instance of']])
        self.create_line(template_no=14, replacement=[self.data['airport named after']])
        self.create_line(template_no=7, replacement=[self.data['airport elevation above sea level']])
        self.create_line(template_no=13, replacement=[self.data['airport lat long']])
        self.text += '\n'
        self.create_line(template_no=15, replacement=[self.data['airport owned by']])
        self.create_line(template_no=16, replacement=[self.data['IATA code']])
        self.create_line(template_no=17, replacement=[self.data['airport social media followers']])
        self.text += '\n\n'
        self.create_line(template_no=3, replacement=[self.railway_name, self.subject, self.data['railway instance of']])
        self.create_line(template_no=18, replacement=[self.data['railway opening data']])
        self.create_line(template_no=19, replacement=[self.data['railway administration location']])
        self.create_line(template_no=20, replacement=[self.data['railway operator']])
        self.text += '\n'
        self.create_line(template_no=21, replacement=[self.data['railway owned by']])
        self.create_line(template_no=13, replacement=[self.data['railway lat long']])

        print(self.text)


if __name__ == "__main__":
    generator = Generator(subject="मुंबई", queries=query, template=template)
    generator.get_info()
    generator.generate_text()
# for result in results["results"]["bindings"][4]:
