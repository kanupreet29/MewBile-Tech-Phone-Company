"""
CSC148, Winter 2023
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import datetime
from math import ceil
from typing import Optional
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: datetime.date
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ Advance to a new month in the contract, corresponding to <month> and
        <year>. This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """
    A term contract
    """
    _end_date: datetime.date
    _track_month: (int, int)

    def __init__(self, start: datetime.date, end: datetime.date) -> None:

        # as Term Contract is a subclass so to avoid duplicate code:
        Contract.__init__(self, start)
        # initializing the end date of contract and month tracker
        self._end_date = end
        self._track_month = (start.month, start.year)

    def new_month(self, month: int, year: int, bill: Bill) -> None:

        # initializing the bill
        self.bill = bill
        # setting the bill rates
        self.bill.set_rates("TERM", TERM_MINS_COST)
        if (month, year) != self._track_month:
            self.bill.add_fixed_cost(TERM_MONTHLY_FEE)
            # track month
            self._track_month = (month, year)
        # if it is the first month going on
        else:
            # if it is the first month going on
            self.bill.add_fixed_cost(TERM_DEPOSIT)
            self.bill.add_fixed_cost(TERM_MONTHLY_FEE)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill
        """
        # checking if term minutes are all used up or not
        free_minutes = self.bill.free_min
        # compare the term minutes then add the called minutes
        if free_minutes + ceil(call.duration / 60.0) <= TERM_MINS:
            self.bill.add_free_minutes(ceil(call.duration / 60.0))
        # else
        # adding the leftover free minutes to bill
        else:
            self.bill.add_free_minutes(TERM_MINS - free_minutes)
            self.bill.add_billed_minutes(ceil(call.duration / 60.0)
                                         - TERM_MINS + free_minutes)

    def cancel_contract(self) -> float:
        current_date = datetime.datetime(self._track_month[1],
                                         self._track_month[0], 1, 00, 00, 00)


        # If the customer cancels the contract early, the deposit is
        # forfeited. If the contract is carried to term, the customer gets back
        # the term deposit. That is, if the
        # contract gets cancelled after the end date of the contract, then the
        # term deposit is returned to the
        # customer, minus that month's cost.

        # Cancellation after end date
        if self._end_date <= current_date:
            contract_cancellation = (Contract.cancel_contract(self) -
                                     TERM_DEPOSIT)
            return contract_cancellation
        else:
            # ends before the cancellation date
            contract_cancellation = Contract.cancel_contract(self)
            return contract_cancellation


class MTMContract(Contract):
    """
    A month to month contract
    """
    def __init__(self, start: datetime.date) -> None:

        # as Month Contract is a subclass so to avoid duplicate code:
        Contract.__init__(self, start)

    def new_month(self, month: int, year: int, bill: Bill) -> None:

        # STORING THE BILL
        self.bill = bill
        # setting the mtm rate of the bill & adding the fixed monthly bill
        self.bill.set_rates("MTM", MTM_MINS_COST)
        self.bill.add_fixed_cost(MTM_MONTHLY_FEE)

    def bill_call(self, call: Call) -> None:
        # from the parent class
        Contract.bill_call(self, call)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.
        """
        # from the parent class
        return Contract.cancel_contract(self)


class PrepaidContract(Contract):
    """
    A prepaid contract

    """
    _balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:

        # as Term Contract is a subclass so to avoid duplicate code:
        Contract.__init__(self, start)
        self._balance = -1 * balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        # there are two conditions we are required to work on:
        # 1. when there is a new month, in that case there is no balance
        # to be carried over.
        starting_month = self.start.month
        starting_year = self.start.year
        if (month, year) == (starting_month, starting_year):
            # setting the bill
            self.bill = bill
            self.bill.set_rates("PREPAID", PREPAID_MINS_COST)
            self.bill.add_fixed_cost(self._balance)
        # 2. when it is not a new month, we add the balance
        else:
            if self.bill is not None:
                self._balance = self.bill.get_cost()
            # also need to check the minimum credit.
            if not self._balance <= -10:
                self._balance = self._balance - 25
            else:
                self.bill = bill
                self.bill.set_rates("PREPAID", PREPAID_MINS_COST)
                self.bill.add_fixed_cost(self._balance)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.
        """
        # bill for prepaid
        Contract.bill_call(self, call)

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        """
        self.start = None
        self._balance = self.bill.get_cost()
        # positive balance
        if self._balance >= 0:
            return self._balance
        else:
            # negative balance
            self._balance = 0.00
            return 0.00


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
