import requests
import json

"""
This is a REST client in python that accepts json input for a list of partners, processes it
to create output for each country to suggest a start date for when the event should be held based
on the number of partners that can attend.
Author: Ankur Bajoria
Created: 10/1/2016
"""

responseData = {}
countryListResponse = []
COUNTRY_STRING = 'country'
PARTNERS_STRING = 'partners'
AVAILABLE_DATES_STRING = 'availableDates'
EMAIL_STRING = 'email'
COUNTRIES_STRING = 'countries'
HTTP_STATUS_OK = 200
GET_URL = 'https://candidate.hubteam.com/candidateTest/v1/partners?userKey=d0d7a18c52ff557f23e18cdaeeaa'
POST_URL = 'https://candidate.hubteam.com/candidateTest/v1/results?userKey=d0d7a18c52ff557f23e18cdaeeaa'


# Class definition to hold the response for each country
class Country:
    attendeeCount = 0
    attendees = []
    name = ""
    startDate = ""

    def __init__(self, attendee_count, attendees, name, start_date):
        self.attendeeCount = attendee_count
        self.attendees = attendees
        self.name = name
        self.startDate = start_date


def default_class(o):
    if isinstance(o, set):
        return list(o)
    return o.__dict__


def get_request(url):

    try:
        r = requests.get(url)
        #Parse json from the output from r.text
        json_data = json.loads(r.text)
        process_json_data(json_data)
    except Exception as e:
        print(e.args)
    else:
        return r.status_code


def process_json_data(json_data):
    list_of_partners = json_data[PARTNERS_STRING]
    partner_dict = {}
    country_dict = {}

    # Get the unique list of countries and available dates for those countries
    for partner in list_of_partners:
        country = partner[COUNTRY_STRING]
        available_dates = partner[AVAILABLE_DATES_STRING]
        if country not in country_dict:
            country_dict[country] = available_dates
        else:
            existing_dates = country_dict[country]
            new_dates = set(existing_dates).union(available_dates)
            country_dict[country] = new_dates

    sorted_country_dict_keys = sorted(country_dict.keys())

    # Create a dictionary with all the partners available for a particular 'country:date' combination
    for country in sorted_country_dict_keys:
        for date in sorted(country_dict[country]):
            partner_email_list = []
            for partner in list_of_partners:
                if partner[COUNTRY_STRING] == country and date in partner[AVAILABLE_DATES_STRING]:
                    if partner[EMAIL_STRING] not in partner_email_list:
                        partner_email_list.append(partner[EMAIL_STRING])
            if (country + ":" + date) not in partner_dict.keys():
                partner_dict[country + ":" + date] = partner_email_list

    # Iterate over the partner dictionary to figure out the start date for each country based on the rules
    for country in sorted_country_dict_keys:
        start_idx = 0
        end_idx = 2
        attendees = 0
        event_start_date = ''
        email_list = []
        for x in range(0, len(sorted(country_dict[country]))):
            dates = sorted(country_dict[country])[start_idx:end_idx:]
            if len(dates) > 1:
                country_date_idx1 = country + ":" + dates[0]
                country_date_idx2 = country + ":" + dates[1]
                if country_date_idx1 in partner_dict.keys() and country_date_idx2 in partner_dict.keys():
                    partner_list1 = partner_dict[country_date_idx1]
                    partner_list2 = partner_dict[country_date_idx2]

                    # If there are no people in the list for the date then mark the date as null
                    if len(partner_list1) == 0 and len(partner_list2) == 0:
                        event_start_date = 'null'
                    elif partner_list1 == partner_list2:
                        # If both the dates have same number of people take the earlier date
                        event_start_date = dates[0]
                        attendees = len(partner_list1)
                        email_list = partner_list1
                    else:
                        # Check to see the number of people for two consecutive dates, calculate the intersection of both partner lists
                        common_emails_list = set(partner_list1).intersection(partner_list2)
                        common_emails_list_len = len(common_emails_list)

                        if common_emails_list_len > attendees:
                            event_start_date = dates[0]
                            email_list = common_emails_list
                            attendees = common_emails_list_len
                        start_idx += 1
                        end_idx += 1

        # Create an object of type Country.class and append it to the list of countries
        countryListResponse.append(Country(attendees, email_list, country, event_start_date))

    # Add the list of Country objects into the main response dictionary
    responseData[COUNTRIES_STRING] = countryListResponse


def post_request(url):

    try:
        headers = {'content-type': 'application/json', 'accept': 'application/json'}
        payload = json.dumps(responseData, ensure_ascii=False, default=default_class)
        r = requests.post(url, data=payload, headers=headers)
    except Exception as e:
        print(e.args)
    else:
        return r.status_code

if __name__ == '__main__':

    if get_request(GET_URL) == HTTP_STATUS_OK:
        print("Okay GET worked, time to POST")
        if post_request(POST_URL) == HTTP_STATUS_OK:
            print("Woohooo!!")
        else:
            print("Woops! Looks like something went wrong.")
    else:
        print("Woops! Looks like something went wrong.")