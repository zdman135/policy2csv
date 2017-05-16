#!/usr/bin/python3
#
# Policy to csv
#
# Add rules

import base64, re, time, requests
import sys, json, code

tenant = 'tenant Id goes here'
env = 'environment goes here'
user = 'email_here'
pw = 'password_here'

# To drop in REPL for troubleshooting:
# code.interact(local=dict(globals(), **locals()))

base_url = "base url goes here"


def build_dictionary(mark_json):
    result = {}
    for mark in mark_json["Resources"]:
        result[mark['name']] = {}
        if 'detail' in mark and 'values' in mark['detail'] and mark['detail']['values']:
            for val in mark['detail']['values']:
                if 'name' in val and 'description' in val:
                    result[mark['name']][val['name']] = val['description']
    return result


def dequote(str):
    quoted=re.compile('"([^"]*)"')
    m = quoted.match(str)
    if(m):
        return m.group(1)
    else:
        return str


def quote(str):
    return('"' + str + '"')


def trim_leading_whitespace(str):
    ws=re.compile('[ \t]*([^ \t]+.*)')
    m = ws.match(str)
    if(m): return m.group(1)
    else: return str


def print_newlined_list(list):
    if(len(list) == 0): return
    if(len(list) == 1):
        print(list[0],end="")
    else:
        print('"',end="")
        for elem in range(0,len(list)-1):
            print(dequote(list[elem]), end="\n")
        print(dequote(list[len(list)-1]), end='"')
    return

#
# XXX - print all datamarking values
#


def print_enriched_policy(policy, mark_dict):
    rem = re.match('Data is marked with [^;]; or data is marked with (.*) matching any of (.*)',
                   policy['description'])
    if(not rem):
        rem=re.match('Data is marked with (.*) matching any of (.*)',
                     policy['description'])

    if(rem):
        policy_str = "Data is marked with %s matching any of " % rem.group(1)
        lst=re.findall("\d+", rem.group(2))
        for elem in lst:
            if(mark_dict.get(rem.group(1)) and
               mark_dict.get(rem.group(1)).get(elem)):
                elemstr = '%s (%s)' % (elem, mark_dict[rem.group(1)][elem])
            else:
                elemstr = elem
            policy_str += "%s, " % elemstr
        print(quote(policy_str), end="")
    else:
        rem = re.match('Data is marked with (.*) matching (\d+).',
                       policy['description'])
        if(rem):
            # print("***Match on %s\n" % policy['description'])
            if(mark_dict.get(rem.group(1)) and
               mark_dict.get(rem.group(1)).get(rem.group(2))):
                elemstr = '%s (%s)' % (rem.group(2),
                                       mark_dict[rem.group(1)][rem.group(2)])
            else:
                elemstr = rem.group(2)
            print("\"Data is marked with %s matching %s\"" %
                  (rem.group(1), elemstr), end="")
        else:
            # print("*** '%s' didn't match" % policy['description'])
            print(quote(policy['description']), end="")
    print(",", end="")


def print_detailed_policy(p, m):
    if 'target' in p and 'condition' in p['target'] and p['target']['condition']['functionId'] == 'string-at-least-one-member-of':
            for arg in p['target']['condition']['args']:
                if 'id' in arg:
                    idstr=arg['id']
                if 'value' in arg:
                    vals = arg['value']
            print('"' + p['description'])
            print('%s in ' % idstr, end=" ")
            for val in vals:
                for group in m:
                    if val in m[group]:
                        description = m[group][val]
                        print(description, end=",")
            print('"', end="")
    elif 'target' in p and 'condition' in p['target'] and p['target']['condition']['functionId'] == 'string-subset':
        for arg in p['target']['condition']['args']:
            if 'id' in arg:
                idstr = arg['id']
            if 'value' in arg:
                vals = arg['value']
        print('"')
        print('%s in ' % idstr, end=" ")
        for val in vals:
            for group in m:
                if val in m[group]:
                    description = m[group][val]
                    print(description, end=",")
        print('"', end="")
    else:
        print(quote(p['description']), end="")

    print(",", end="")


def print_rules(rules):
    all_rules=[]
    for rule in rules:
        all_rules.append('"' + rule['description'] + '"')
    print_newlined_list(all_rules)


def print_timestamp(timestamp):
    tm=time.gmtime(timestamp)
    print(time.strftime('%Y-%m-%d:%H.%M.%S', tm), end="")


def print_header():
    # sys.stdout = open('output.csv', 'w') # another way to output to csv
    print("Policy,Data marking,Rules,Enabled,Version,Created,Modified")


def print_policy(policy, mark_dict):
    print(policy['policyId'], end=",")
    print_detailed_policy(policy, mark_dict)
    print_rules(policy['rules'])
    print(",",policy['enabled'], end=",")
    print(policy['_version'], end=",")
    print_timestamp(policy['_createdTs'])
    print(",",end="")
    print_timestamp(policy['_updatedTs'])
    print("")


def print_all_data(data, mark_dict):
    print_header()
    for policy in data["Resources"]:
        print_policy(policy, mark_dict)

encoded = base64.b64encode(bytes(user + ':' + pw, 'utf-8'))
encoded = encoded.decode(encoding="utf-8", errors="strict")
headers = {'Authorization': 'Basic ' + encoded}

url_policy = base_url + '/policies'
policy = requests.get(url_policy, headers=headers)

url_markings = base_url + '/markings'
markings = requests.get(url_markings, headers=headers)

if policy.status_code == 200 and markings.status_code == 200:
    mark_dict = build_dictionary(markings.json())
    print_all_data(policy.json(), mark_dict)
else:
    print('Request error returned')
    print('Policy response returned ' + str(policy.status_code) + ' status code')
    print('Markings response returned ' + str(markings.status_code) + ' status code')
