from bs4 import BeautifulSoup
import requests
import urllib
import json
import csv
import time
from functools import cache


all_finder = "?NCNI-5&catStyle=ShowProducts"

appl_link = "https://www.homedepot.com/b/N-{id}"

dict_id = {
    "refrigerator":{
    "all_refrigerator" : "5yc1vZc3pi",
    "french_door_refrigerator": "5yc1vZc3oo",
    "side_by_side_refrigerator": "5yc1vZc3q0",
    "top_freezer_refrigerator" : "5yc1vZc3ns",
    "botton_freezer_refrigerator" : "5yc1vZc3p6",
    "mini_fridges" : "5yc1vZc4mo",
    "freezer": "5yc1vZc3p2",
    "commercial_refrigerators" : "5yc1vZc3oe",
    "freezerless_refrigerators" : "5yc1vZc3p9"
    },

    "washing_machine":{
    "all_washing_machine": "5yc1vZc3ol",
    "front_load_washers": "5yc1vZc3pj",
    "top_load_washers" : "5yc1vZc3oc",
    "top_load_washers" : "5yc1vZc3oc",
    "top_load_washers" : "5yc1vZc3ocZ1z17rwr",
    "Top Load Washers" : "5yc1vZc3ocZ1z17ryq"
    },

    "dryers":{
    "all_dryer":"5yc1vZc3p3",
    "electric_dryers" : "5yc1vZc3q1",
    "gas_dryers": "5yc1vZc3o3"
    },

}



api_key = "AEERpN6Zz1oZzOLDFP1juwAV"

"""
availability checker uses start online product_id number from hd.com
stop product_id and zip code that locates nearest home depot
to provide information if an appliance is in stock
"""

def availability_checker(start, stop, zip_code):

    mydict = dict()

    for product_id in range(start, stop):

        print(product_id)

        appliance_url = f"https://www.homedepot.com/mcc-cart/v3/appliance/deliveryAvailability/{product_id}/zipCode/{zip_code}"
        description_url = f"https://api.bazaarvoice.com/data/reviews.json?apiversion=5.4&Filter=ProductId:{product_id}&Include=Products&Limit=1&Passkey=u2tvlik5g1afeh78i745g4s1d"

        # uses url decode function to loop through url and extract data
        json_response = url_decoder(appliance_url)
        json_response_descr = url_decoder(description_url)

        # if key deliveryAvailability is on the json reponse returns true
        if "deliveryAvailability" in json_response["DeliveryAvailabilityResponse"]:

            mydict[product_id] = {}

            # shortned path
            shortned_response = json_response["DeliveryAvailabilityResponse"]["deliveryAvailability"]

            mydict[product_id]["product_id"] = product_id
            mydict[product_id]["modelNbr"] = shortned_response["availability"][0]["modelNbr"]
            mydict[product_id]["status"] = shortned_response["availability"][0]["status"]

            # checks if product is out of stock
            if "earliestAvailabilityDate" in json_response["DeliveryAvailabilityResponse"]["deliveryAvailability"]:

                mydict[product_id]["earliestAvailabilityDate"] = shortned_response["earliestAvailabilityDate"]
                description_parser(mydict, product_id)
                bs4_decoder(mydict,product_id)
                print(mydict)
                
            elif "en_US" in json_response_descr["Locale"]:
                print(f"{product_id} DNE")
                
            else:
                description_parser(mydict, product_id)
                bs4_decoder(mydict,product_id)
                print(mydict)
                
                

        else:
            print(f"{product_id} is not an Appliance")

        # cut code 1

        # CSV
        # csv file runs on each iteration
        # saves code until runs into a error
        json_dumper(mydict)
    csv_file(mydict)


def csv_file(dict):

    csv_columns = ['product_id', "Category", "Brand", "Type1", "Type2", 'modelNbr', "ApplType", 'reviewCount', 'height',  'depth', 'width', 'ratingValue', 'priceValidUntil', 'price',
                   'status', "earliestAvailabilityDate",  "Discontinued", "Title", "ImageUrl", "ProductPageUrl", "Description"]

    csv_file = "appliances_status.csv"
    try:
        with open(csv_file, 'w') as csvfile:
            # lineterminator removes extra space on each line on csv
            writer = csv.DictWriter(
                csvfile, fieldnames=csv_columns, lineterminator='\n')
            writer.writeheader()
            for data in dict.values():
                writer.writerow(data)
    except IOError:
        print("I/O error")


def json_dumper(dict):

    data_json = "hd_data.json"
    try:
        with open(data_json, 'w') as fp:
            json.dump(dict, fp,  indent=4)
    except IOError:
        print("I/O error")


def bs4_decoder(dict,my_product_id):

    #temp dict

    details_url = f"https://www.homedepot.com/s/{my_product_id}"

    with urllib.request.urlopen(details_url) as url:
        # decodes json file
        soup = BeautifulSoup(url, "html.parser")

    res = soup.find('script',id="thd-helmet__script--productStructureData")

    try:
        json_object = json.loads(res.contents[0])
        print(json_object)

    except AttributeError:
        print("Empty")
        dict[my_product_id]["Discontinued"] = True
        
    try:
        if "offers" in json_object:

            dict[my_product_id]["depth"] = json_object["depth"]
            dict[my_product_id]["height"] = json_object["height"]
            dict[my_product_id]["width"] = json_object["width"]
            dict[my_product_id]["ratingValue"] = json_object["aggregateRating"]["ratingValue"]
            dict[my_product_id]["reviewCount"] = json_object["aggregateRating"]["reviewCount"]
            dict[my_product_id]["price"] = json_object["offers"]["price"]
            dict[my_product_id]["priceValidUntil"] = json_object["offers"]["priceValidUntil"]
            
    except Exception as e:
        print(getattr(e, 'message', repr(e)))
        print(getattr(e, 'message', str(e)))
    # Logs the error appropriately. 


# bs4_decoder(205343880)

@cache
def url_decoder(url_encoded):
    # uses urllib to open json file and read
    with urllib.request.urlopen(url_encoded) as url:
        # decodes json file
        json_response = json.loads(url.read().decode())

    return json_response


def description_parser(dict, my_product_id):

    description_url = f"https://api.bazaarvoice.com/data/reviews.json?apiversion=5.4&Filter=ProductId:{my_product_id}&Include=Products&Limit=1&Passkey=u2tvlik5g1afeh78i745g4s1d"

    json_response_descr = url_decoder(description_url)



    try:
        for key, value in json_response_descr["Includes"]["Products"].items():
            print(key)

    except KeyError:
        print("Bad key")
    
    
    if my_product_id != key:
        new_product_id = key

    # item number is diferent from imput

    short_response_descr = json_response_descr[
        "Includes"]["Products"][f"{new_product_id}"]

    item_category = short_response_descr["Attributes"]["Category"]["Values"][0]["Value"].split()[
        0].rstrip(">")

    if item_category == "APPLIANCES":

        dict[my_product_id]["Category"] = item_category
        dict[my_product_id]["ApplType"] = short_response_descr["Attributes"]["THDClass_name"]["Values"][0]["Value"]
        dict[my_product_id]["Type1"] = short_response_descr["Attributes"]["THDSubClass_name"]["Values"][0]["Value"]
        try:
            dict[my_product_id]["Type2"] = short_response_descr["Attributes"]["THD_SubSubClass_name"]["Values"][0]["Value"]
        except KeyError:
            print('Can not find "something"')
        dict[my_product_id]["Title"] = short_response_descr["Name"]
        dict[my_product_id]["Brand"] = short_response_descr["Brand"]["Name"]
        dict[my_product_id]["ImageUrl"] = short_response_descr["ImageUrl"]
        dict[my_product_id]["ProductPageUrl"] = short_response_descr["ProductPageUrl"]
        dict[my_product_id]["Description"] = short_response_descr["Description"]


availability_checker(0, 205344410, 33315)


























# cut code 1
# checks is key have an error
# elif "errorData" in json_response["DeliveryAvailabilityResponse"]:

#     mydict[product_id] = {}
#     mydict[product_id]["product_id"] = product_id

#     # shortned path
#     error = json_response["DeliveryAvailabilityResponse"]["errorData"]["errors"]["error"]["errorCode"]

#     mydict[product_id]["error"] = error

# elif "en_US" in json_response_descr["Locale"]:
#     print("DNE")

# else:
#     shortned_response_descr = json_response_descr[
#         "Includes"]["Products"][f"{product_id}"]
#     print(shortned_response_descr["Description"])