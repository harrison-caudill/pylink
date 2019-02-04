#!/usr/bin/env python

import pylink
from pylink import TaggedAttribute as TA


def _net_salary_usd_per_month(model):
    return (model.gross_salary_usd_per_month
            * (1.0 - model.tax_rate))


def _expenses_usd_per_month(model):
    return (model.rent_usd_per_month
            + model.food_usd_per_month
            + model.other_expenses_usd_per_month)


def _savings_usd_per_month(model):
    return model.net_salary_usd_per_month - model.expenses_usd_per_month


class GenericFinancialModel(object):

    def __init__(self,
                 gross_salary_usd_per_month=10e3,
                 rent_usd_per_month=3e3,
                 food_usd_per_month=500,
                 other_expenses_usd_per_month=1e3,
                 tax_rate=0.4):
        self.tribute = {
            # calculators
            'net_salary_usd_per_month': _net_salary_usd_per_month,
            'expenses_usd_per_month': _expenses_usd_per_month,
            'savings_usd_per_month': _savings_usd_per_month,

            # constants
            'gross_salary_usd_per_month': gross_salary_usd_per_month,
            'tax_rate': tax_rate,
            'rent_usd_per_month': rent_usd_per_month,
            'food_usd_per_month': food_usd_per_month,
            'other_expenses_usd_per_month': other_expenses_usd_per_month,
            }


def _months_to_pay_for_car(model):
    return float(model.midlife_crisis_car_usd) / model.savings_usd_per_month


extras = {'midlife_crisis_car_usd': TA(110e3, model='Tesla P100d'),
          'months_to_pay_for_car': _months_to_pay_for_car,}
m = pylink.DAGModel([GenericFinancialModel()], **extras)
e = m.enum

print('Savings Rate ($/mo):        %3g' % m.savings_usd_per_month)
print('Cost of Midlife Crisis ($): %3g' % m.midlife_crisis_car_usd)
print('Car Model:                  %s' % m.get_meta(e.midlife_crisis_car_usd)['model'])
print('Months to Pay for Crisis:   %d' % round(m.months_to_pay_for_car, 0))
