#!/usr/bin/env python3.6

###################################################################################################################################
#### Script Name: sf_code_challenge.py
#### Description: Accomplishes the functionality specified in https://github.com/sflydwh/code-challenge.
#### Assumptions: 1) Formula for Simple LTV if followed as instructed, might be different from reality.
####              2) Weekly calculations extrapolated by daily multiplied by 7  
####              3) Used relative paths for Input and Output directories based on github master repo, not absolute paths.    
####                 Testing done using absolute paths of local machine.    
#### Remarks:     1) Script is doing all operations in memory, might need customizations on scaling up(like use sqlite3 for a DB etc)
####              2) DRY(don't repeat yourself) hasn't been strictly followed in interest of time & step by step testing :)  
####              3) Using Customer as parent might have been a good idea, but since it works so ..May be later.  
####              4) If the number of customers to report in TopX, provided by user is not between 1 to 10, graceful error appears. 
####                 If data ingested is less than queried(e.g. topX variable gets 10 from user while input has only 5 customer's   
####                 data), we will just get the data for 5 customers without any errors. 
###################################################################################################################################
#### VersionNo        ModifiedDate    ModifiedBy          Email(Optional)
#### Draft version    20170205        Rohit Vashishtha    excuseme@notnow.thankyou
###################################################################################################################################

import json
import collections
from datetime import datetime

# Parent Class - Event definition
class Event(object):

 # Ingesting input data to lists for each event, initializing each list
 customer_rel = []
 site_visit_rel = []
 image_rel = []
 order_rel = []

 # Initializing dictionaries for all the methods we'll use for our LTV calculation
 cust_ln = {}
 cust_minevent = {}
 cust_maxevent = {}
 cust_numdays = {}
 cust_visits = {}
 cust_image = {}
 cust_order = {}
 cust_ltv = {}
 
 def __init__(self,type):
  self.type = type

# Child Class - Customer definition
 
class Customer(Event):

 def __init__(self,**kwargs):
  super(Customer, self).__init__(kwargs["type"])
  if self.type == 'CUSTOMER':
   self.customer_rel.append(kwargs["key"])
   self.customer_rel.append(kwargs["event_time"])
   self.customer_rel.append(kwargs["last_name"])
   self.customer_rel.append(kwargs["adr_city"])
   self.customer_rel.append(kwargs["adr_state"]) 
   self.customer_rel.append(kwargs["type"])
   self.customer_rel.append(kwargs["verb"])
   self.customer_id = kwargs["key"]
   self.last_name = kwargs["last_name"]
   
  else: pass

 # getting customer name, not used in output but use if requirement says so
   
 def get_custrec(self,**kwargs):
  if self.type == 'CUSTOMER':
   self.cust_ln.update({kwargs["key"]:kwargs["last_name"]})
   return self.cust_ln
  
# Child Class - Site_Visit definition

class Site_visit(Event):

 def __init__(self,**kwargs):
  super(Site_visit, self).__init__(kwargs["type"])
  if self.type == 'SITE_VISIT':
       self.site_visit_rel.append(kwargs["customer_id"])
       self.site_visit_rel.append(kwargs["key"])
       self.site_visit_rel.append(kwargs["event_time"])
       self.site_visit_rel.append(kwargs["tags"])
  else: pass

 # getting customer's minimum site_visit date

 def get_mineventtime(self,**kwargs):
  if self.type == 'SITE_VISIT':
     if kwargs["customer_id"] in self.cust_minevent.keys():
      if kwargs["event_time"][0:10] < (self.cust_minevent[kwargs["customer_id"]] if self.cust_minevent[kwargs["customer_id"]] is not None else "9999-12-31"):
       self.cust_minevent[kwargs["customer_id"]] = kwargs["event_time"][0:10]
      else: pass
     else: 
      self.cust_minevent.update({kwargs["customer_id"]:kwargs["event_time"][0:10]})
  else: pass    
  return self.cust_minevent
    
 # getting customer's maximum site_visit date

 def get_maxeventtime(self,**kwargs):
  if self.type == 'SITE_VISIT':
     if kwargs["customer_id"] in self.cust_maxevent.keys():
      if kwargs["event_time"][0:10] > (self.cust_maxevent[kwargs["customer_id"]] if self.cust_maxevent[kwargs["customer_id"]] is not None else "0001-01-01"):
       self.cust_maxevent[kwargs["customer_id"]] = kwargs["event_time"][0:10]
      else: pass
     else: 
      self.cust_maxevent.update({kwargs["customer_id"]:kwargs["event_time"][0:10]})
  else: pass    
  return self.cust_maxevent

 # getting customer's presence duration on site
 
 def get_numdays(self,**kwargs):
  if self.type == 'SITE_VISIT':
     if kwargs["customer_id"] in self.cust_numdays.keys():
      numdays = abs(datetime.strptime(self.cust_maxevent[kwargs["customer_id"]],"%Y-%m-%d") - datetime.strptime(self.cust_minevent[kwargs["customer_id"]],"%Y-%m-%d")).days
      self.cust_numdays[kwargs["customer_id"]] = numdays
     else: 
      self.cust_numdays.update({kwargs["customer_id"]:"0"})
  else: pass
  return self.cust_numdays

 # getting customer's number of visits in that duration

 def get_custvisits(self,**kwargs):
  if self.type == 'SITE_VISIT':
     if kwargs["customer_id"] in self.cust_visits.keys():
      self.cust_visits[kwargs["customer_id"]] += 1
     else: 
      self.cust_visits.update({kwargs["customer_id"]:int(1)})
  else: pass  
  return self.cust_visits

# Child Class - Image definition, this isn't used for LTV calculation

class Image(Event):

 def __init__(self,**kwargs):
  super(Image, self).__init__(kwargs["type"])
  if self.type == 'IMAGE':
       self.image_rel.append(kwargs["customer_id"])
       self.image_rel.append(kwargs["key"])
       self.image_rel.append(kwargs["event_time"])
       self.image_rel.append(kwargs["camera_make"])
       self.image_rel.append(kwargs["camera_model"])
  else: pass

 # getting customer's image_id, in case we want to output in our report

 def get_custimage(self,**kwargs):
  if self.type == 'IMAGE':
   self.cust_image.update({kwargs["customer_id"]:kwargs["key"]})
   return self.cust_image

# Child Class - Order definition, this is when LTV comes into existence else it remains 0

class Order(Event):

 def __init__(self,**kwargs):
  super(Order, self).__init__(kwargs["type"])
  if self.type == 'ORDER':
       self.order_rel.append(kwargs["customer_id"])
       self.order_rel.append(kwargs["key"])
       self.order_rel.append(kwargs["event_time"])
       self.order_rel.append(kwargs["total_amount"])
  else: pass

 # getting customer's cumulative expenditure

 def get_amount(self,**kwargs):
  if self.type == 'ORDER':
     if kwargs["customer_id"] in self.cust_order.keys():
      self.cust_order[kwargs["customer_id"]] += float(kwargs["total_amount"])
     else: 
      self.cust_order.update({kwargs["customer_id"]:float(kwargs["total_amount"])})
  else: pass  
  return self.cust_order

 # getting customer's LTV

 def get_custltv(self,**kwargs):
  if self.type == 'ORDER':
   if kwargs["customer_id"] in self.cust_ltv.keys():
    numvisit = int(self.cust_visits[kwargs["customer_id"]] if self.cust_visits[kwargs["customer_id"]] is not None else 0)
    expense = float(self.cust_order[kwargs["customer_id"]] if self.cust_order[kwargs["customer_id"]] is not None else 0)
    visitdays = int(self.cust_numdays[kwargs["customer_id"]] if self.cust_numdays[kwargs["customer_id"]] is not None else 0)
    # Simple LTV = 52 * ( (expense/numvisit) * ((numvisit/visitdays) * 7) ) * t(10) ...... hence numvisits not needed
    if visitdays == 0:   # Averting Divide by Zero Error
     self.cust_ltv.update({kwargs["customer_id"]:float(0)})
    else:
     self.cust_ltv[kwargs["customer_id"]] = float(52 * ((expense/visitdays)* 7) * 10)
   else: 
    self.cust_ltv.update({kwargs["customer_id"]:float(0)})
  return self.cust_ltv


########### ------------------START OF THE MAIN METHOD--------------------- ############

def main():

 # Read the input json

 with open('../input/input.txt') as json_ip:
  e=json.load(json_ip)

 # Define Ingest method
  
  def Ingest(**kwargs):
   if kwargs is not None:
    event = Event(kwargs["type"])
    customer = Customer(**kwargs)
    site_visit = Site_visit(**kwargs)
    image = Image(**kwargs)
    order = Order(**kwargs)
    
   else:
    pass
   return customer.customer_rel,site_visit.site_visit_rel,image.image_rel,order.order_rel

 # Call Ingest method
  for line in e: 
   D = Ingest(**line)
   
#  print(D)                         # If you would like to look at D list, used while testing

 # Define method for calculating LTV
 
  def GetCustLTV(**kwargs):
   if kwargs is not None:
    event = Event(kwargs["type"])
    cust_ln = Customer(**kwargs)
    cust_numdays = Site_visit(**kwargs)
    cust_image = Image(**kwargs)
    cust_exp = Order(**kwargs)
    
    customer_rec = cust_ln.get_custrec(**kwargs),
    customer_minevent = cust_numdays.get_mineventtime(**kwargs),
    customer_maxevent = cust_numdays.get_maxeventtime(**kwargs),
    customer_visitdays = cust_numdays.get_numdays(**kwargs),
    customer_numvisits = cust_numdays.get_custvisits(**kwargs),
    customer_expenditure = cust_exp.get_amount(**kwargs)
    customer_ltv = cust_exp.get_custltv(**kwargs)
    
    return customer_ltv
    
   else:
    pass
    
 # Call method for calculating LTV
   
  for line in e: 
    cust_ltv = GetCustLTV(**line)

 # Order the results by LTV descending

 cust_ltv_list = list(cust_ltv.items())
 cust_ltv_list.sort(key=lambda t: t[1], reverse=True)

 # Define the method in requirements: TopXSimpleLTVCustomers(x,D)

 def TopXSimpleLTVCustomers(x,D): 
  return D[:x]

 # Accept user input for number "X" in topX customer requirement, report error if number not between 1 to 10
 
 topX = int(input("Enter Top X(How Many?) Customers needed to report : "))
 
 if topX < 1:
  print("Too few customers to report on, provided by user")
 elif topX > 10:
  print("Too many customers to report on, provided by user")
 else:
 # Call the method in requirements: TopXSimpleLTVCustomers(x,D)

  TopXSimpleLTVCustomers = TopXSimpleLTVCustomers(topX,cust_ltv_list)

 # Move the results to output file

  outfile = open('../output/output.txt','w')
  outfile.write('CustomerId               LTV \n')
  outfile.write('\n'.join('%s          %s' % x for x in TopXSimpleLTVCustomers))

#  print(TopXSimpleLTVCustomers) # on console if you want to, while testing

############## -----------CALL THE MAIN METHOD, THE END--------------- ################# 
if __name__ == '__main__': main()