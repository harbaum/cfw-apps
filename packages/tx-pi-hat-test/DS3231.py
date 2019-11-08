#!/usr/bin/env python

# DS3231.py Python Driver Code
# SwitchDoc Labs 12/19/2014
# V 1.2
# only works in 24 hour mode
# please send patches to: https://github.com/switchdoclabs/RTC_SDL_DS3231


#encoding: utf-8

# Copyright (C) 2013 @XiErCh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function

from datetime import datetime
import time

import smbus

SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
MAX_DAYS_PER_MONTH = 31
MONTHS_PER_YEAR = 12
YEARS_PER_CENTURY = 100

OSCILLATOR_ON_MASK = 0b1<<7

def bcd_to_int(bcd, n=2):
    """Decode n least significant packed binary coded decimal digits to binary.
    Return binary result.
    n defaults to 2 (BCD digits).
    n=0 decodes all digits.
    """
    return int(('%x' % bcd)[-n:])


def int_to_bcd(x, n=2):
    """
    Encode the n least significant decimal digits of x
    to packed binary coded decimal (BCD).
    Return packed BCD value.
    n defaults to 2 (digits).
    n=0 encodes all digits.
    """
    return int(str(x)[-n:], 0x10)


class DS3231():
    (
        _REG_SECONDS,
        _REG_MINUTES,
        _REG_HOURS,
        _REG_DAY,
        _REG_DATE,
        _REG_MONTH,
        _REG_YEAR,
        _REG_ALARM1_SECONDS,
        _REG_ALARM1_MINUTES,
        _REG_ALARM1_HOURS,
        _REG_ALARM1_DAY_DATE,
        _REG_ALARM2_MINUTES,
        _REG_ALARM2_HOURS,
        _REG_ALARM2_DAY_DATE,
        _REG_CONTROL,
        _REG_STATUS,
        _REG_AGING,
        _REG_TEMP_MSB,
        _REG_TEMP_LSB,
    ) = range(19)

    ###########################
    # DS3231 Code
    # datasheet: https://datasheets.maximintegrated.com/en/ds/DS3231.pdf
    ###########################
    def __init__(self, bus=1, addr=0x68):
        self._bus = smbus.SMBus(bus)
        self._addr = addr

    def _write(self, register, data):
        if False:
            print(
                "addr =0x%x register = 0x%x data = 0x%x %i " %
                (self._addr, register, data, bcd_to_int(data)))
        self._bus.write_byte_data(self._addr, register, data)

    def _read(self, register_address):
        data = self._bus.read_byte_data(self._addr, register_address)
        if False:
            print(
                "addr = 0x%x register_address = 0x%x %i data = 0x%x %i "
                % (
                    self._addr, register_address, register_address,
                    data, bcd_to_int(data)))
        return data

    def _incoherent_read_all(self):
        """Return tuple of year, month, date, day, hours, minutes, seconds.
        Since each value is read one byte at a time,
        it might not be coherent."""
        
        register_addresses = (
            self._REG_SECONDS,
            self._REG_MINUTES,
            self._REG_HOURS,
            self._REG_DAY,
            self._REG_DATE,
            self._REG_MONTH,
            self._REG_YEAR,
        )
        seconds, minutes, hours, day, date, month, year = (
            self._read(register_address)
            for register_address in register_addresses
        )
        seconds &= ~OSCILLATOR_ON_MASK
        if True:
            # This stuff is suspicious.
            if hours == 0x64:
                hours = 0x40
            hours &= 0x3F
        return tuple(
            bcd_to_int(t)
            for t in (year, month, date, day, hours, minutes, seconds))

    def read_all(self):
        """Return tuple of year, month, date, day, hours, minutes, seconds.
        """

        """Read until one gets same result twice in a row.
        Then one knows the time is coherent."""

        old = self._incoherent_read_all()
        while True:
            new = self._incoherent_read_all()
            if old == new:
                break
            old = new
        return new

    def read_str(self):
        """Return a string such as 'YY-DD-MMTHH-MM-SS'.
        """
        year, month, date, _, hours, minutes, seconds = self.read_all()
        return (
            '%02d-%02d-%02dT%02d:%02d:%02d' %
            (year, month, date, hours, minutes, seconds)
        )

    def read_datetime(self, century=21, tzinfo=None):
        """Return the datetime.datetime object.
        """
        year, month, date, _, hours, minutes, seconds = self.read_all()
        year = 100 * (century - 1) + year
        return datetime(
            year, month, date, hours, minutes, seconds,
            0, tzinfo=tzinfo)

    def write_all(self, seconds=None, minutes=None, hours=None, day=None,
            date=None, month=None, year=None, save_as_24h=True):
        """Direct write un-none value.
        Range: seconds [0,59], minutes [0,59], hours [0,23],
               day [0,7], date [1-31], month [1-12], year [0-99].
        """
        if seconds is not None:
            if not 0 <= seconds < SECONDS_PER_MINUTE:
                raise ValueError('Seconds is out of range [0,59].')
            seconds_reg = int_to_bcd(seconds)
            self._write(self._REG_SECONDS, seconds_reg)

        if minutes is not None:
            if not 0 <= minutes < MINUTES_PER_HOUR:
                raise ValueError('Minutes is out of range [0,59].')
            self._write(self._REG_MINUTES, int_to_bcd(minutes))

        if hours is not None:
            if not 0 <= hours < HOURS_PER_DAY:
                raise ValueError('Hours is out of range [0,23].')
            self._write(self._REG_HOURS, int_to_bcd(hours) ) # not  | 0x40 according to datasheet

        if year is not None:
            if not 0 <= year < YEARS_PER_CENTURY:
                raise ValueError('Years is out of range [0,99].')
            self._write(self._REG_YEAR, int_to_bcd(year))

        if month is not None:
            if not 1 <= month <= MONTHS_PER_YEAR:
                raise ValueError('Month is out of range [1,12].')
            self._write(self._REG_MONTH, int_to_bcd(month))

        if date is not None:
            # How about a more sophisticated check?
            if not 1 <= date <= MAX_DAYS_PER_MONTH:
                raise ValueError('Date is out of range [1,31].')
            self._write(self._REG_DATE, int_to_bcd(date))

        if day is not None:
            if not 1 <= day <= DAYS_PER_WEEK:
                raise ValueError('Day is out of range [1,7].')
            self._write(self._REG_DAY, int_to_bcd(day))

    def write_datetime(self, dt):
        """Write from a datetime.datetime object.
        """
        self.write_all(dt.second, dt.minute, dt.hour,
                dt.isoweekday(), dt.day, dt.month, dt.year % 100)

    def write_now(self):
        """Equal to DS3231.write_datetime(datetime.datetime.now()).
        """
        self.write_datetime(datetime.now())

    def getTemp(self):
        byte_tmsb = self._bus.read_byte_data(self._addr,self._REG_TEMP_MSB)
        byte_tlsb = bin(self._bus.read_byte_data(self._addr,self._REG_TEMP_LSB))[2:].zfill(8)
        return byte_tmsb+int(byte_tlsb[0])*2**(-1)+int(byte_tlsb[1])*2**(-2)

    def ackPendingAlarm(self):
        self._write(self._REG_STATUS, self._read(self._REG_STATUS) & ~0x01)        
        # disable alarm1 interrupt 
        self._write(self._REG_CONTROL, self._read(self._REG_CONTROL) & ~0x01)
    
    def setAlarm(self, dt):
        # acknowlege any pending alarm1 interrupt        
        self.ackPendingAlarm()

        if dt.second != None: self._write(self._REG_ALARM1_SECONDS, int_to_bcd(dt.second))
        else:                 self._write(self._REG_ALARM1_SECONDS, 0x80)
        if dt.minute != None: self._write(self._REG_ALARM1_MINUTES, int_to_bcd(dt.minute))
        else:                 self._write(self._REG_ALARM1_MINUTES, 0x80)
        if dt.hour != None:   self._write(self._REG_ALARM1_HOURS, int_to_bcd(dt.hour))
        else:                 self._write(self._REG_ALARM1_HOURS, 0x80)        
        if dt.day != None:    self._write(self._REG_ALARM1_DAY_DATE, int_to_bcd(dt.day))
        else:                 self._write(self._REG_ALARM1_DAY_DATE, 0x80)

        # enable alarm1 interrupt 
        self._write(self._REG_CONTROL, self._read(self._REG_CONTROL) | 0x01)
