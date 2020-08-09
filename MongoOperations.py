from pymongo import MongoClient
import geoip2.database
import json
import os
import csv
import pandas as pd


def upload_to_mongo():
    # establishing connection
    try:
        connect = MongoClient('mongodb://localhost:27017/')
        print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    # connecting or switching to the database
    db = connect.tracerouteDB

    # creating or switching to demoCollection
    collection = db.traces

    # directory = r'C:/Users/tshit/Documents/Blessed/Honours Courses/Honors Project/code/trace'
    directory = "files/trace"
    for filename in os.listdir(directory):
        a = filename
        with open("trace/" + a) as json_file:
            data = json.load(json_file)
            for testResult in data["TracerouteTestResults"]:
                collection.insert_one(testResult)

    connect.close()


def update_mongo_with_asn():
    # establing connection
    try:
        connect = MongoClient('mongodb://localhost:27017/')
        print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    # connecting or switching to the database
    db = connect.tracerouteDB

    # creating or switching to demoCollection
    collection = db.traces

    # This creates a Reader object. You should use the same object
    # across multiple requests as creation of it is expensive.
    pathToDb = "files/GeoLite2-ASN.mmdb"
    with geoip2.database.Reader(pathToDb) as reader:
        # iterate through each document's Tracert array
        for x in collection.find():
            for trace in x['Tracert']:
                ip = trace['IP']
                try:
                    response = reader.asn(ip)
                    asn = response.autonomous_system_number
                except:
                    print("Address not in database")
                    asn = ""
                qu = {}
                update = {"$set": {"Tracert.$[inner].ASN": asn}}
                filter = [{"inner.IP": ip}]
                collection.update_many(qu, update, upsert=True, array_filters=filter)
    connect.close()


def update_mongo_with_alias_set():
    # establing connection
    try:
        connect = MongoClient('mongodb://localhost:27017/')
        print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    # connecting or switching to the database
    db = connect.tracerouteDB

    # creating or switching to demoCollection
    collection = db.traces

    f = open('files/midar-83.sets', 'r')
    # loop through file and discard the first 6 lines beginning with hash
    for line in f:
        if line[0:1] == '#':
            continue
        else:
            break

    lineCount = 0
    ip = ""
    for line in f:
        if line[0:1] == '#':
            lineCount += 1
        else:
            ip = line.strip()
            qu = {}
            update = {"$set": {"Tracert.$[inner].setNumber": lineCount}}
            filter = [{"inner.IP": ip}]
            collection.update_many(qu, update, upsert=True, array_filters=filter)
            qu = {"IP": ip}
            update = {"$set": {"setNumber": lineCount}}
            collection.update_many(qu, update)

    connect.close()
    os.remove("files/midar-83.sets")


def get_asn_location():
    # establing connection
    try:
        connect = MongoClient('mongodb://localhost:27017/')
        # print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    # connecting or switching to the database
    db = connect.tracerouteDB

    # creating or switching to demoCollection
    collection = db.traces

    # read the file with the asns and find each corresponding IP and geolocate it
    f = open("files/uniqueAsn.txt", "r")
    f.readline()

    # This creates a Reader object. You should use the same object
    # across multiple requests as creation of it is expensive.
    path_to_db = "files/GeoLite2-City.mmdb"
    with geoip2.database.Reader(path_to_db) as reader:
        with open('files/asn_lat_long.csv', mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['IP', 'ASN', 'Longitude', 'Latitude'])
            for line in f:
                for x in collection.find({"Tracert.ASN": int(line.strip())},
                                         {"Tracert": {"$elemMatch": {"ASN": int(line.strip())}}}):
                    response = reader.city(x['Tracert'][0]['IP'])
                    csv_writer.writerow([x['Tracert'][0]['IP'], x['Tracert'][0]['ASN'], response.location.longitude,
                                         response.location.latitude])
                    break

    # close file
    f.close()
    connect.close()
    os.remove("files/uniqueAsn.txt")


def get_linked_asn():
    # establing connection
    try:
        connect = MongoClient('mongodb://localhost:27017/')
        print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    mydb = connect["tracerouteDB"]
    mycol = mydb["traces"]

    sources = []
    targets = []
    for x in mycol.find():
        # check if document has set attribute
        source = x['ProbeInfo']['ASN']

        # iterate through every element in the document's Tracert array checking set number
        for a in x['Tracert']:
            # first check if ASN=''
            if a['ASN'] == '':
                continue

            destination = a['ASN']
            # keep updating the destination variable until the ASN is different from source
            if source == destination:
                continue

            sources.append(source)
            targets.append(destination)

            # exchange the variables
            source = destination

    df = pd.DataFrame({'Source': sources, 'Target': targets})
    df.to_csv('files/asn_source_destination.csv', index=False, encoding='utf-8')
    print("done and stored asn_source_destination in csv file")
    connect.close()


def drop_mongo_collection():
    # establing connection
    try:
        connect = MongoClient('localhost', 27017)
        print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    mydb = connect["tracerouteDB"]
    mycol = mydb["traces"]

    mycol.drop()
    connect.close()

def get_asn():
    # establing connection
    try:
        connect = MongoClient('mongodb://localhost:27017/')
        print("Connected successfully!!!")
    except:
        print("Could not connect to MongoDB")

    mydb = connect["tracerouteDB"]
    mycol = mydb["traces"]

    asn = []
    for x in mycol.find():
        # check if document has set attribute
        source = x['ProbeInfo']['ASN']

        # iterate through every element in the document's Tracert array checking set number
        for a in x['Tracert']:
            # first check if ASN=''
            if a['ASN'] == '':
                continue

            destination = a['ASN']
            # keep updating the destination variable until the ASN is different from source
            if source == destination:
                continue

            if source not in asn:
                asn.append(source)
            if destination not in asn:
                asn.append(destination)

            # exchange the variables
            source = destination
    connect.close()
    return asn
