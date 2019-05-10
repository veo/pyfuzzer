#!/usr/bin/python

from __future__ import print_function
import os
import sys
import requests
import optparse
import logging
import threading


proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
headers = {'Content-Type': 'application/x-www-form-urlencoded','User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
logging.basicConfig(level=logging.WARNING,filename='data.log',filemode='w',format='%(message)s')
lentext = 0

class Fuzz(threading.Thread):
    tlist = []
    threads = 30
    evnt = threading.Event()
    lck = threading.Lock()
    def __init__(self,url,payload,data):
        threading.Thread.__init__(self)
        self.url = url
        self.data = data
        self.payload = payload.strip('\n')
    def run(self):
        global lentext
        while True:
            try:
                if self.data == "":
                    url = self.url.replace('$', self.payload)
                    r = requests.get(url, allow_redirects=False, headers=headers, timeout=30)
                    print("%s\t%s\t%.2f\t\t%s" % (r.status_code, len(r.content), r.elapsed.total_seconds() * 1000, self.payload))
                    logging.warning("Status: GET %s\tLength:%s\tTime:%.2f\t\tPayload:%s" % (r.status_code, len(r.content), r.elapsed.total_seconds() * 1000, self.payload))
                else:
                    r = requests.post(self.url, data=self.data.replace('$', self.payload), allow_redirects=False, headers=headers, timeout=30)
                    print("%s\t%s\t%.2f\t\t%s" % (r.status_code, len(r.content), r.elapsed.total_seconds() * 1000, self.payload))
                    logging.warning("Status: POST %s\tLength:%s\tTime:%.2f\t\tPayload:%s" % (r.status_code, len(r.content), r.elapsed.total_seconds() * 1000, self.payload))
                if len(r.content) != lentext:
                    print("%s\t%s\t%.2f\t\t%s success" % (r.status_code, len(r.content), r.elapsed.total_seconds() * 1000, self.payload))
                    logging.warning("Status: POST %s\tLength:%s\tTime:%.2f\t\tPayload:%s success" % (r.status_code, len(r.content), r.elapsed.total_seconds() * 1000, self.payload))
                    lentext = len(r.content)
                try:
                    with open('data/%s' % (self.payload), 'wb') as f:
                        f.write(r.content)
                except:
                    print("Error: could not write file 'data/%s'" % (self.payload))
                break
            except Exception as e:
                pass
        Fuzz.lck.acquire()
        Fuzz.tlist.remove(self)
        if len(Fuzz.tlist) < Fuzz.threads:
            Fuzz.evnt.set()
            Fuzz.evnt.clear()
        Fuzz.lck.release()
    def newthread(url,payload,data):
        Fuzz.lck.acquire()
        sc = Fuzz(url,payload,data)
        Fuzz.tlist.append(sc)
        Fuzz.lck.release()
        sc.start()
    newthread = staticmethod(newthread)



if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-s', '--save',
                      dest="save",
                      default=False,
                      action="store_true",
                      help='Save HTTP response content to files',
                      )
    parser.add_option('-d', '--data',
                      dest="data",
                      default="",
                      help='Post data',
                      )
    parser.set_usage("""Usage: ./PyIntruder.py [options] <base url> <payload list> --data <data>
        (Use '$' as variable in url that will be swapped out with each payload)
        Example:  pyfuzzer.py http://www.example.com/file/$.pdf payloads.txt (--data 'data')
            """)
    options, remainder = parser.parse_args()
    save_responses = options.save
    if len(remainder) == 2:
        baseurl = remainder[0]
        if '$' not in baseurl and '$' not in options.data:
            print("Error: Please include variable character ('$') in URL or POST data")
            sys.exit()
        payloadfile = remainder[1]
    else:
        print("Invalid number of arguments: use -h option for usage")
        sys.exit()
    try:
        with open(payloadfile) as f:
            payloaddata = f.readlines()
    except:
        print("Error: cannot read file '%s'" % payloadfile)
        sys.exit()
    print("Status\tLength\tTime\t\tPayload")
    print("------------------------------------------------------------------")
    if not os.path.exists('data'):
        os.makedirs('data')
    for payload in payloaddata:
        Fuzz.lck.acquire()
        if len(Fuzz.tlist) >= Fuzz.threads:
            Fuzz.lck.release()
            Fuzz.evnt.wait()
        else:
            Fuzz.lck.release()
        Fuzz.newthread(baseurl, payload, options.data)
    for t in Fuzz.tlist:
        t.join()
