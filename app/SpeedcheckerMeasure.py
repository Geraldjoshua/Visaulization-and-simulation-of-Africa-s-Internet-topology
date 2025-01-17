import json
import random

import requests

from app import MongoOperations as mo

"""
get all active probes in Africa
"""
ApiKey = ""

Availableprobes = {}
ping_test_id = []
trace_test_id = []
African_countries = ["DZ", "AO", "BJ", "BW", "BF", "BI", "CM", "CV", "CF", "TD", "KM", "CG", "CD", "CI", "DJ",
                     "EG", "GQ", "ER", "ET", "GA", "GM", "GH", "GN", "GW", "KE", "LS", "LR", "LY", "MG", "MW",
                     "ML", "MR", "MU", "YT", "MA", "MZ", "NA", "NE", "NG", "RE", "RW", "SH", "ST", "SN", "SC",
                     "SL", "SO", "ZA", "SS", "SD", "SZ", "TZ", "TG", "TN", "UG", "EH", "ZM", "ZW"]


def get_available_probes():
    african_countries = African_countries
    african_countries = random.sample(african_countries, len(african_countries))
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apikey": ApiKey,
    }
    url = "https://kong.speedcheckerapi.com:8443/ProbeAPIv2/GetProbes?apikey=7295deda-f359-4ac9-918f-93fdc01992a8"

    global Availableprobes
    country_probes = {}
    # check which country has probes
    for country in african_countries:
        payload = {
            "criteria": {
                "Sources": [
                    {
                        "CountryCode": str(country)
                    }
                ],
                "ProbeInfoProperties": [
                    "Latitude",
                    "Longitude",
                    "ProbeID",
                    "CountryCode",
                    "CityName",
                    "IPAddress",
                    "ASN"
                ]
            }
        }
        data = json.dumps(payload)
        try:
            r = requests.post(url, data=data, headers=headers)
        except requests.exceptions.RequestException as e:
            return "Request FAILED"
        json_result = r.json()
        if len(json_result['GetProbesResult']['Probes']) != 0:
            country_probes.update({country.strip(): len(json_result['GetProbesResult']['Probes'])})

    return country_probes


"""
doing a ping given a list of destination ip address
"""


def post_ping_all_ip_test(ip_Africa_address):
    data = get_available_probes()
    global ping_test_id
    ip_address = ip_Africa_address
    ip_address = random.sample(ip_address, len(ip_address))
    ip_start = 0
    url = 'https://kong.speedcheckerapi.com:8443/ProbeAPIv2/StartPingTest'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apikey": ApiKey,

    }
    test_res = []

    # for probe in probe_id:
    for x, y in data.items():
        numb_of_dest = 0
        # id = probe.strip()
        id = x.strip()
        test_count = 1
        if y >= 10:
            test_count = 10
        else:
            test_count = y
        for i in range(ip_start, len(ip_address)):
            ip = str(ip_address[i]).strip()
            if numb_of_dest > 1:
                if i == (len(ip_address) - 1):
                    ip_start = 0
                else:
                    ip_start = i
                break
            if i == (len(ip_address) - 1):
                ip_start = 0
            payload = {
                "testSettings": {
                    "PingType": "icmp",
                    "Count": 3,
                    "Timeout": 4000,
                    "TestCount": test_count,
                    "Sources": [
                        {
                            # "ProbeID": id
                            "CountryCode": id

                        }
                    ],
                    "Destinations": [
                        ip
                    ],
                    "ProbeInfoProperties": [
                        "ASN",
                        "CountryCode",
                    ]
                }

            }
            data = json.dumps(payload)

            try:
                r = requests.post(url, data=data, headers=headers)

            except requests.exceptions.RequestException as e:
                # post was not successful
                pass
                # return "Request failed"
            res = json.loads(r.text)
            if "OK" == res['StartPingTestResult']['Status']['StatusText']:
                test_res.append(res['StartPingTestResult']['TestID'])
            else:
                # the trace was not successful
                pass
                # print(res)
                # print("failed")
            numb_of_dest += 1
    ping_test_id = test_res


"""
returning ping results for a list of destination ip address
"""


def get_ping_all_result():
    API_ENDPOINT = "https://kong.speedcheckerapi.com:8443/ProbeAPIv2/"
    for result in ping_test_id:
        testID = result.strip()
        url = API_ENDPOINT + "GetPingResults?apikey=" + ApiKey + "&testID=" + testID
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "apikey": ApiKey,

        }
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.RequestException as e:
            print("empty")
        res = json.loads(r.text)
        if "200" == res['ResponseStatus']['StatusCode']:
            mo.upload_ping_to_mongo("SpeedChecker", res)


"""
doing a trace given a list of destination ip address
"""


# def post_trace_all_ip_test(ip_Africa_address):
def post_trace_all_ip_test(ip_Africa_address):
    data = get_available_probes()
    ip_address = ip_Africa_address
    ip_address = random.sample(ip_address, len(ip_address))
    ip_start = 0
    url = 'https://kong.speedcheckerapi.com:8443/ProbeAPIv2/StartTracertTest'
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apikey": ApiKey,

    }
    test_res = []

    # for probe in probe_id:
    for x, y in data.items():
        numb_of_dest = 0
        # id = probe.strip()
        id = x.strip()
        test_count = 1
        if y >= 10:
            test_count = 10
        else:
            test_count = y
        for i in range(ip_start, len(ip_address)):
            ip = str(ip_address[i]).strip()
            if numb_of_dest > 3:
                if i == (len(ip_address) - 1):
                    ip_start = 0
                else:
                    ip_start = i
                break
            if i == (len(ip_address) - 1):
                ip_start = 0
            payload = {
                "testSettings": {
                    "BufferSize": 32,
                    "Count": 3,
                    "Fragment": 1,
                    "Ipv4only": 0,
                    "Ipv6only": 0,
                    "MaxFailedHops": 0,
                    "Resolve": 1,
                    "Sleep": 300,
                    "Ttl": 128,
                    "TtlStart": 1,
                    "Timeout": 100000,
                    "HopTimeout": 3000,
                    "TestCount": test_count,
                    "Sources": [
                        {
                            # "ProbeID": id
                            "CountryCode": id

                        }
                    ],
                    "Destinations": [
                        ip
                    ],
                    "ProbeInfoProperties": [
                        "ASN",
                        "CountryCode",
                    ]
                }

            }
            data = json.dumps(payload)

            try:
                r = requests.post(url, data=data, headers=headers)

            except requests.exceptions.RequestException as e:
                return "Request failed"
            res = json.loads(r.text)
            # print(res)
            if "OK" == res['StartTracertTestResult']['Status']['StatusText']:
                test_res.append(res['StartTracertTestResult']['TestID'])
            else:
                # print(res)
                print("failed")
            numb_of_dest += 1

    global trace_test_id
    trace_test_id = test_res


"""
returning trace results for a list of destination ip address
"""


def get_trace_all_result():
    API_ENDPOINT = "https://kong.speedcheckerapi.com:8443/ProbeAPIv2/"
    if len(trace_test_id) > 0:
        mo.drop_mongo_collection("SpeedChecker")
    for result in trace_test_id:
        if result is not None:
            testID = result.strip()
            url = API_ENDPOINT + "GetTracertResults?apikey=" + ApiKey + "&testID=" + testID
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "apikey": ApiKey,

            }
            try:
                r = requests.get(url, headers=headers)
            except requests.exceptions.RequestException as e:
                print("empty")
            res = json.loads(r.text)
            if "200" == res['ResponseStatus']['StatusCode']:
                mo.upload_to_mongo("SpeedChecker", res)
