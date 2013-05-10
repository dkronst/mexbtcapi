from currency import *
from mexbtcapi.util.constant_generator import constant_generator

ISO_4217_2008= ('AFN', 'EUR', 'ALL', 'DZD', 'USD', 'EUR', 'AOA', 'XCD', 'XCD', 'ARS', 'AMD', 'AWG', 'AUD', 'EUR', 'AZN', 'BSD', 'BHD', 'BDT', 'BBD', 'BYR', 'EUR', 'BZD', 'XOF', 'BMD', 'BTN', 'INR', 'BOB', 'BOV', 'USD', 'BAM', 'BWP', 'NOK', 'BRL', 'USD', 'BND', 'BGN', 'XOF', 'BIF', 'KHR', 'XAF', 'CAD', 'CVE', 'KYD', 'XAF', 'XAF', 'CLF', 'CLP', 'CNY', 'AUD', 'AUD', 'COP', 'COU', 'KMF', 'XAF', 'CDF', 'NZD', 'CRC', 'XOF', 'HRK', 'CUC', 'CUP', 'ANG', 'EUR', 'CZK', 'DKK', 'DJF', 'XCD', 'DOP', 'USD', 'EGP', 'SVC', 'USD', 'XAF', 'ERN', 'EUR', 'ETB', 'EUR', 'FKP', 'DKK', 'FJD', 'EUR', 'EUR', 'EUR', 'XPF', 'EUR', 'XAF', 'GMD', 'GEL', 'EUR', 'GHS', 'GIP', 'EUR', 'DKK', 'XCD', 'EUR', 'USD', 'GTQ', 'GBP', 'GNF', 'XOF', 'GYD', 'HTG', 'USD', 'AUD', 'EUR', 'HNL', 'HKD', 'HUF', 'ISK', 'INR', 'IDR', 'XDR', 'IRR', 'IQD', 'EUR', 'GBP', 'ILS', 'EUR', 'JMD', 'JPY', 'GBP', 'JOD', 'KZT', 'KES', 'AUD', 'KPW', 'KRW', 'KWD', 'KGS', 'LAK', 'LVL', 'LBP', 'LSL', 'ZAR', 'LRD', 'LYD', 'CHF', 'LTL', 'EUR', 'MOP', 'MKD', 'MGA', 'MWK', 'MYR', 'MVR', 'XOF', 'EUR', 'USD', 'EUR', 'MRO', 'MUR', 'EUR', 'XUA', 'MXN', 'MXV', 'USD', 'MDL', 'EUR', 'MNT', 'EUR', 'XCD', 'MAD', 'MZN', 'MMK', 'NAD', 'ZAR', 'AUD', 'NPR', 'EUR', 'XPF', 'NZD', 'NIO', 'XOF', 'NGN', 'NZD', 'AUD', 'USD', 'NOK', 'OMR', 'PKR', 'USD', 'PAB', 'USD', 'PGK', 'PYG', 'PEN', 'PHP', 'NZD', 'PLN', 'EUR', 'USD', 'QAR', 'EUR', 'RON', 'RUB', 'RWF', 'EUR', 'SHP', 'XCD', 'XCD', 'EUR', 'EUR', 'XCD', 'WST', 'EUR', 'STD', 'SAR', 'XOF', 'RSD', 'SCR', 'SLL', 'SGD', 'ANG', 'XSU', 'EUR', 'EUR', 'SBD', 'SOS', 'ZAR', 'SSP', 'EUR', 'LKR', 'SDG', 'SRD', 'NOK', 'SZL', 'SEK', 'CHE', 'CHF', 'CHW', 'SYP', 'TWD', 'TJS', 'TZS', 'THB', 'USD', 'XOF', 'NZD', 'TOP', 'TTD', 'TND', 'TRY', 'TMT', 'USD', 'AUD', 'UGX', 'UAH', 'AED', 'GBP', 'USD', 'USN', 'USS', 'USD', 'UYI', 'UYU', 'UZS', 'VUV', 'EUR', 'VEF', 'VND', 'USD', 'USD', 'XPF', 'MAD', 'YER', 'ZMW', 'ZWL', 'XBA', 'XBB', 'XBC', 'XBD', 'XFU', 'XTS', 'XXX', 'XAU', 'XPD', 'XPT', 'XAG')
EXTRA= ('BTC', 'LTC', 'PPC', 'TRC', 'FTC', 'XRP')
names = ISO_4217_2008

currencies = map(FiatCurrency, names)
constant_generator(locals(), names, currencies)

currencies = map(CryptoCurrency, EXTRA)
constant_generator(locals(), EXTRA, currencies)
