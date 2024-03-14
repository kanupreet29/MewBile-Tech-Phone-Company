import datetime

import pytest

from application import create_customers, process_event_history
from contract import TermContract, MTMContract, PrepaidContract
from customer import Customer
from filter import DurationFilter, CustomerFilter, ResetFilter, LocationFilter
from phoneline import PhoneLine
from callhistory import CallHistory

"""
This is a sample test file with a limited set of cases, which are similar in
nature to the full autotesting suite

Use this framework to check some of your work and as a starting point for
creating your own tests

*** Passing these tests does not mean that it will necessarily pass the
autotests ***
"""


def create_single_customer_with_all_lines() -> Customer:
    """ Create a customer with one of each type of PhoneLine
    """
    contracts = [
        TermContract(start=datetime.date(year=2017, month=12, day=25),
                     end=datetime.date(year=2019, month=6, day=25)),
        MTMContract(start=datetime.date(year=2017, month=12, day=25)),
        PrepaidContract(start=datetime.date(year=2017, month=12, day=25),
                        balance=100)
    ]
    numbers = ['867-5309', '273-8255', '649-2568']
    customer = Customer(cid=5555)

    for i in range(len(contracts)):
        customer.add_phone_line(PhoneLine(numbers[i], contracts[i]))

    customer.new_month(12, 2017)
    return customer


test_dict = {'events': [
    {"type": "sms",
     "src_number": "867-5309",
     "dst_number": "273-8255",
     "time": "2018-01-01 01:01:01",
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
    {"type": "sms",
     "src_number": "273-8255",
     "dst_number": "649-2568",
     "time": "2018-01-01 01:01:02",
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
    {"type": "sms",
     "src_number": "649-2568",
     "dst_number": "867-5309",
     "time": "2018-01-01 01:01:03",
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
    {"type": "call",
     "src_number": "273-8255",
     "dst_number": "867-5309",
     "time": "2018-01-01 01:01:04",
     "duration": 10,
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
    {"type": "call",
     "src_number": "867-5309",
     "dst_number": "649-2568",
     "time": "2018-01-01 01:01:05",
     "duration": 50,
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
    {"type": "call",
     "src_number": "649-2568",
     "dst_number": "273-8255",
     "time": "2018-01-01 01:01:06",
     "duration": 50,
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},

    {"type": "call",
     "src_number": "649-2568",
     "dst_number": "856-5357",
     "time": "2018-07-01 01:06:06",
     "duration": 138,
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.53845693913239, 43.756338501653378]},

    {"type": "call",
     "src_number": "640-2569",
     "dst_number": "856-5357",
     "time": "2018-10-01 01:09:06",
     "duration": 250,
     "src_loc": [-79.42748154284123, 43.645401675960370],
     "dst_loc": [-79.53748693913239, 43.752338501653674]},
    {"type": "sms",
     "src_number": "273-8255",
     "dst_number": "856-5357",
     "time": "2018-11-01 01:18:03",
     "src_loc": [-79.42848154284123, 43.641401675960374],
     "dst_loc": [-79.52745693913239, 43.750338501653374]},
],
    'customers': [
        {'lines': [
            {'number': '867-5309',
             'contract': 'term'},
            {'number': '273-8255',
             'contract': 'mtm'},
            {'number': '649-2568',
             'contract': 'prepaid'}
        ],
            'id': 5555},
        {'lines': [
            {'number': '856-5357',
             'contract': 'mtm'},
            {'number': '640-2569',
             'contract': 'prepaid'}
        ],
            'id': 6545}

    ]
}


def test_customer_creation() -> None:
    """ Test for the correct creation of Customer, PhoneLine, and Contract
    classes
    """
    customer = create_single_customer_with_all_lines()
    bill = customer.generate_bill(12, 2017)

    assert len(customer.get_phone_numbers()) == 3
    assert len(bill) == 3
    assert bill[0] == 5555
    assert bill[1] == 270.0
    assert len(bill[2]) == 3
    assert bill[2][0]['total'] == 320
    assert bill[2][1]['total'] == 50
    assert bill[2][2]['total'] == -100

    # Check for the customer creation in application.py
    customer = create_customers(test_dict)[0]
    customer.new_month(12, 2017)
    bill = customer.generate_bill(12, 2017)

    assert len(customer.get_phone_numbers()) == 3
    assert len(bill) == 3
    assert bill[0] == 5555
    assert bill[1] == 270.0
    assert len(bill[2]) == 3
    assert bill[2][0]['total'] == 320
    assert bill[2][1]['total'] == 50
    assert bill[2][2]['total'] == -100


def test_events() -> None:
    """ Test the ability to make calls, and ensure that the CallHistory objects
    are populated
    """
    customers = create_customers(test_dict)
    customers[0].new_month(1, 2018)

    process_event_history(test_dict, customers)

    # Check the bill has been computed correctly
    bill = customers[0].generate_bill(1, 2018)
    assert bill[0] == 5555
    assert bill[1] == pytest.approx(-29.925)
    assert bill[2][0]['total'] == pytest.approx(20)
    assert bill[2][0]['free_mins'] == 1
    assert bill[2][1]['total'] == pytest.approx(50.05)
    assert bill[2][1]['billed_mins'] == 1
    assert bill[2][2]['total'] == pytest.approx(-99.975)
    assert bill[2][2]['billed_mins'] == 1

    # Check the CallHistory objects are populated
    history = customers[0].get_call_history('867-5309')
    assert len(history) == 1
    assert len(history[0].incoming_calls) == 1
    assert len(history[0].outgoing_calls) == 1

    history = customers[0].get_call_history()
    assert len(history) == 3
    assert len(history[0].incoming_calls) == 1
    assert len(history[0].outgoing_calls) == 1


def test_contract_start_dates() -> None:
    """ Test the start dates of the contracts.

    Ensure that the start dates are the correct dates as specified in the given
    starter code.
    """
    customers = create_customers(test_dict)
    for c in customers:
        for pl in c._phone_lines:
            assert pl.contract.start == datetime.date(
                year=2017, month=12, day=25)
            if hasattr(pl.contract, 'end'):  # only check if there is an end date (TermContract)
                assert pl.contract.end == datetime.date(
                    year=2019, month=6, day=25)


def test_filters() -> None:
    """ Test the functionality of the filters.

    We are only giving you a couple of tests here, you should expand both the
    dataset and the tests for the different types of applicable filters
    """
    customers = create_customers(test_dict)
    process_event_history(test_dict, customers)

    # Populate the list of calls:
    calls = []
    hist = customers[0].get_history()
    # only consider outgoing calls, we don't want to duplicate calls in the test

    for each_call in hist[0]:
        if each_call not in calls:
            calls.append(each_call)

    for each_call in hist[1]:
        if each_call not in calls:
            calls.append(each_call)

    hist2 = customers[1].get_history()

    for each_call in hist2[0]:
        if each_call not in calls:
            calls.append(each_call)

    for each_call in hist2[1]:
        if each_call not in calls:
            calls.append(each_call)

    # The different filters we are testing
    filters = [
        DurationFilter(),
        CustomerFilter(),
        LocationFilter(),
        ResetFilter()
    ]

    # These are the inputs to each of the above filters in order.
    # Each list is a test for this input to the filter
    filter_strings = [
        ["L050", "G010", "L000", "50", "AA", "", "L3408", "K050", "l200", "L200 ", "l50", "L50",
         " l050", " l050 ", "l00050 ", "l0 50", "g10", "g000010"],
        ["5555", "1111", "9999", "aaaaaaaa", "", ",", "6545", "34567", "12p9"],
        ["", "-79.53748154284123, 43.643401675960374, -79.42745693913239, 43.755338501653374", "a,a,a,a",
         "-79.53748154284123, 43.643401675960374,-79.42745693913239,43.755338501653374",
         "-79.5, 43.6, -79.4, 43.7, 50.1",
         "-79.53748154284123, 43.643401675960374, aaaa, 43.755338501653374",
         "-79.53748154284123, 43.643401675ij60374,  ab-79.42745693913239,  43.755338501653374",
         "-79.53748154284123, 43.643401675960374", "43.643401675960374",
         "-79.53748154284123, 43.6434016   75960374,-79.427456  93913239,43.755338501653374"],
        ["rrrr", ""]
    ]

    # These are the expected outputs from the above filter application
    # onto the full list of calls
    expected_return_lengths = [
        [1, 4, 0, 5, 5, 5, 5, 5, 4, 4, 1, 1, 1, 1, 1, 5, 4, 4],
        [4, 5, 5, 5, 5, 5, 2, 5, 5],
        [5, 4, 5, 4, 5, 5, 5, 5, 5, 5],
        [5, 5]
    ]

    for i in range(len(filters)):
        for j in range(len(filter_strings[i])):
            result = filters[i].apply(customers, calls, filter_strings[i][j])
            # print(len(result), expected_return_lengths[i][j], filter_strings[i][j])
            assert len(result) == expected_return_lengths[i][j]


if __name__ == '__main__':
    pytest.main(['a1_my_tests.py'])
