from __future__ import print_function

import urllib2, urllib
import argparse
import time
import os
import json
import sys
from urlparse import urlparse
from datetime import date
from utils import stringjoin

# Hack-ish way to handle unicode (finger crossed)
reload(sys)
sys.setdefaultencoding('UTF8')


# Wrap open to create directory before opening a file
def mkdir_p(path):
    try:
        os.makedirs(path)
    except:
        if os.path.isdir(path):
            pass
        else:
            raise


def check_dir(file_path):
    """
    Get a path as input, it will creates all the necessary (missing) directories in order to follow the provided path

    :param file_path:
        ex. /tmp/random/pizza
        it will create the directories random and pizza if not already present in the system

    :return:
        none
    """
    directory = os.path.dirname(file_path)
    mkdir_p(directory)


def wrap_open(method, exceptions = (OSError, IOError)):
    def fn(*args, **kwargs):
        try:
            check_dir(args[0])
            return method(*args, **kwargs)
        except exceptions:
            sys.exit('Can\'t open \'{0}\'. Error #{1[0]}: {1[1]}'.format(args[0], sys.exc_info()[1].args))

    return fn

open = wrap_open(open)

def wrap_exit(method, exceptions = (OSError, IOError)):
    def fn(*args, **kwargs):
        try:
            print(reset)
            return method(*args, **kwargs)
        except exceptions:
            sys.exit('Can\'t open \'{0}\'. Error #{1[0]}: {1[1]}'.format(args[0], sys.exc_info()[1].args))

    return fn
exit = wrap_exit(exit)

# colors for terminal messages
red = ""
green = ""
white = ""
yellow = ""
reset = ""

def posix_colors():
    global red, green, white, yellow, reset
    red = "\033[1;31;10m[!] "
    green = "\033[1;32;10m[+] "
    white = "\033[1;37;10m"
    yellow = "\033[1;33;10m[!] "
    reset = "\033[0;0m"

def supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.
    """
    plat = sys.platform
    supported_platform = plat != 'Pocket PC' and (plat != 'win32' or
                                                  'ANSICON' in os.environ)
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    return supported_platform and is_a_tty

if supports_color():
    posix_colors()

# CSS style used for the documentation
stl = """
<style>
body {
  font-family: Roboto;
  background-color: #f9f9f9;
}

li.query {
  color: #368cbf;
}

li.mutation {
  color: #30a;
}

li.subscription {
  color: #397D13;
}

li.argument {
  color: #edae49;
}

li.type {
  color: #7ebc59;
}

li.deprecated {
  color: red;
  ext-decoration: underline wavy red;
}

li.field {

}

li.description {
  color: grey;
}
span.query {
  color: #368cbf;
}

span.mutation {
  color: #30a;
}

span.subscription {
  color: #397D13;
}

span.argument {
  color: #edae49;
}

span.type {
  color: #7ebc59;
}

span.deprecated {
  color: red;
  ext-decoration: underline wavy red;
}

span.field {

}

span.description {
  color: grey;
}

div.box {
  background-color: white;
  width: 300px;
  border: 5px solid grey;
  padding: 10px;
  margin: 10px;
}
</style>
"""


def query(target, key, proxyDict):
    """
    Execute the introspection query against the GraphQL endpoint

    :param target:
        Expects a valid URL ex. https://example.com/graphql
        Raise an exception if HTTP/HTTPS schema is missing

    :param key:
        Optional parameter to be used as authentication header
        "Basic dXNlcjp0ZXN0"
        "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

    :param proxyDict:
        Optional parameter to be used as web proxy to go through
        ex. http://127.0.0.1:8080

    :return:
        Returns a dictionary objects to be parsed
    """
    # Introspection Query
    # -----------------------
    query = "query IntrospectionQuery{__schema{queryType{name}mutationType{name}subscriptionType{name}types{...FullType}directives{name description locations args{...InputValue}}}}fragment FullType on __Type{kind name description fields(includeDeprecated:true){name description args{...InputValue}type{...TypeRef}isDeprecated deprecationReason}inputFields{...InputValue}interfaces{...TypeRef}enumValues(includeDeprecated:true){name description isDeprecated deprecationReason}possibleTypes{...TypeRef}}fragment InputValue on __InputValue{name description type{...TypeRef}defaultValue}fragment TypeRef on __Type{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name}}}}}}}}"
    old_query = "query IntrospectionQuery{__schema{queryType{name}mutationType{name}subscriptionType{name}types{...FullType}directives{name description args{...InputValue}onOperation onFragment onField}}}fragment FullType on __Type{kind name description fields(includeDeprecated:true){name description args{...InputValue}type{...TypeRef}isDeprecated deprecationReason}inputFields{...InputValue}interfaces{...TypeRef}enumValues(includeDeprecated:true){name description isDeprecated deprecationReason}possibleTypes{...TypeRef}}fragment InputValue on __InputValue{name description type{...TypeRef}defaultValue}fragment TypeRef on __Type{kind name ofType{kind name ofType{kind name ofType{kind name}}}}"
    # -----------------------
    if key:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0",
            "Authorization": key
            # TODO add the option for custom headers and variables
        }
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0"
        }
    try:
        # Issue the Introspection request against the GraphQL endpoint
        data = urllib.urlencode({"query": query})
        if proxyDict:
            proxy = urllib2.ProxyHandler(proxyDict)
            opener = urllib2.build_opener(proxy)
            urllib2.install_opener(opener)
        request = urllib2.Request(target, data, headers=headers)
        contents = urllib2.urlopen(request).read()
        return contents

    except urllib2.HTTPError, e:
        print(stringjoin(red, str(e), white))

    except urllib2.URLError, e:
        print(stringjoin(red, str(e), white))


def file_write(URL, file_path, today, timestamp, file_name, content, mode):
    """
    This function is used in order to generate the Queries Mutations & Subscriptions templates.
    Path and file name will be generated as follow:

    :param URL:
        the target graphql endpoint stripped of its schema (HTTP/HTTPS)

    :param file_path:
        query, mutation, subscription

    :param today:
        date.today (2019-03-12)

    :param timestamp:
        1552562387

    :param file_name:
        query, mutation, subscription names

    :param content:
        file content

    :param mode:
        w, a and so on

    :return:
        none
    """

    write_file = open(os.path.join(URL, file_path, today, timestamp, '%s.query' % file_name), mode)
    write_file.write(content)
    write_file.close()


def detect_type(types):
    """
    This function will replace known GraphQL arguments types with placeholder values (useful for Burp Suite Repeater)

    :param types:
        Known types: String, Boolean, Float, Int, NOT_NULL
        TODO: add the support for custom objects and lists (partially handled since v4.1)

    :return:
        Returns a placeholder accordingly to the provided type
    """
    # strip the ! character (not null symbol) before returning the type
    types = types.replace("!", "")
    # Switch between known args types
    if "String" in types:
        # needed for Burp Repeater string handling
        types = stringjoin('\\"', types, '\\"')
        types = types.replace("String", "asd")
    elif "Boolean" in types:
        types = types.replace("Boolean", "TRUE")
    elif "Float" in types:
        types = types.replace("Float", "0.5")
    elif "Int" in types:
        types = types.replace("Int", "1")
    return types


def main():
    """
    Query a GraphQL endpoint with introspection in order to retrieve the documentation of all the Queries, Mutations & Subscriptions.
    It will also generate Queries, Mutations & Subscriptions templates (with optional placeholders) for all the known types.

    :return:
        none
    """
    # Args parser definition
    # -----------------------
    parser = argparse.ArgumentParser(prog="inql", description="GraphQL Scanner")
    parser.add_argument("-t", default=None, dest="target",
                        help="Remote GraphQL Endpoint (https://<Target_IP>/graphql)")
    parser.add_argument("-f", dest="schema_json_file", default=None, help="Schema file in JSON format")
    parser.add_argument("-k", dest="key", help="API Authentication Key")
    parser.add_argument('-p', dest="proxy", default=None,
                        help='IP of web proxy to go through (http://127.0.0.1:8080)')
    parser.add_argument("-d", dest="detect", action='store_true', default=False,
                        help="Replace known GraphQL arguments types with placeholder values (useful for Burp Suite)")
    parser.add_argument("-o", dest="output_directory", default=os.getcwd(),
                        help="Output Directory")
    args = parser.parse_args()
    # -----------------------

    mkdir_p(args.output_directory)
    os.chdir(args.output_directory)

    return init(args, lambda: parser.print_help())


def init(args, print_help=None):
    # At least one between -t or -f (target) parameters must be set
    if args.target is None and args.schema_json_file is None:
        print(stringjoin(red, "Remote GraphQL Endpoint OR a Schema file in JSON format must be specified!", white))
        if print_help:
            print_help()
            exit(1)

    # Only one of them -t OR -f :)
    if args.target is not None and args.schema_json_file is not None:
        print(stringjoin(red, "Only a Remote GraphQL Endpoint OR a Schema file in JSON format must be specified, not both!", white))
        if print_help:
            print_help()
            exit(1)

    # Takes care of any configured proxy (-p param)
    if args.proxy is not None:
        print(stringjoin(yellow, "Proxy ENABLED: ", args.proxy, white))
        proxyDict = {"http": args.proxy, "https": args.proxy}
    else:
        proxyDict = {}

    if args.target is not None or args.schema_json_file is not None:
        if args.target is not None:
            # Acquire GraphQL endpoint URL as a target
            URL = urlparse(args.target).netloc
        else:
            # Acquire a local JSON file as a target
            print(stringjoin(yellow, "Parsing local schema file", white))
            URL = "localschema"
        detect = args.detect
        if detect:
            print(stringjoin(yellow, "Detect arguments is ENABLED, known types will be replaced with placeholder values", white))
        # Used to generate 'unique' file names for multiple documentation
        timestamp = str(int(time.time()))  # Can be printed with: str(int(timestamp))
        today = str(date.today())
        # -----------------------
        # Setup lists for templates generation
        # -----------------------
        q_name = []
        q_args_name = []
        q_args_type = []
        q_type = []
        m_name = []
        m_args_name = []
        m_args_type = []
        m_type = []
        s_name = []
        s_args_name = []
        s_args_type = []
        s_type = []
        # holds custom objects
        # [[obj name 1,field name 1,field name 2],[obj name 2,field name 1,field name 2, field name 3]]
        fields_names = []
        # -----------------------
        # Custom Objects are required for fields names in the documentation and templates generation
        # old -c parameter, enabled by default
        custom = True
        # Generate the documentation for the target
        with open(os.path.join(URL, "doc-%s-%s.html" % (today, timestamp)), 'w') as output_file:
            if args.target is not None:
                # Parse response from the GraphQL endpoint
                result = query(args.target, args.key, proxyDict)
                # returns a dict
                result = json.loads(result)
            else:
                # Parse the local JSON file
                with open(args.schema_json_file, "r") as s:
                    result_raw = s.read()
                    result = json.loads(result_raw)
            # Write schema file
            schema_file = open(os.path.join(URL, "schema-%s-%s.json" % (today, timestamp)), "w")
            if args.target is not None:
                # returns a prettified json
                schema_file.write(json.dumps(result, indent=4))
            else:
                schema_file.write(result_raw)
            schema_file.close()
            # Write HTML header for the documentation
            # --------------------
            output_file.write("<html><head><title>GraphQL Schema</title>")
            # write CSS
            output_file.write(stl)
            # write target URL
            output_file.write("</head><body><h2>GraphQL Schema</h2><h3><a href='{0}'>{0}</a></h3>".format(args.target))
            # write legend box
            output_file.write(
                "<div class='box'><h4>Legend</h4><ul><li class='query'>Queries</li><li class='mutation'>Mutations</li><"
                "li class='subscription'>Subscriptions</li><li class='argument'>Arguments</li>"
                "<li class='type'>Types: String, Float, not_null!, [list]</li><li class='deprecated'>Deprecated</li>"
                "<li class='field'>Fields</li></ul></div>")
            # --------------------
            output_file.write("<p>Available Operations Types:</p>")
            try:
                # Print available operation types, usually: Query, Mutations & Subscriptions
                # This part also holds custom names (schema[Type]['name'] != 'RootQuery', 'RootMutation', 'Subscriptions')
                # --------------------
                if result['data']['__schema']['mutationType'] is not None:
                    output_file.write("<ul><li class='mutation'>{0}</li>".format(
                        result['data']['__schema']['mutationType']['name']))
                    Mutation = result['data']['__schema']['mutationType']['name']
                else:
                    # Needed since not all GraphQL endpoints use/have all the three types (Query, Mutations & Subscriptions)
                    Mutation = None
                if result['data']['__schema']['queryType'] is not None:
                    output_file.write("<li class='query'>{0}</li>".format(
                        result['data']['__schema']['queryType']['name']))
                    Query = result['data']['__schema']['queryType']['name']
                else:
                    Query = None
                if result['data']['__schema']['subscriptionType'] is not None:
                    output_file.write(
                        "<li class='subscription'>{0}</li></ul>".format(
                            result['data']['__schema']['subscriptionType']['name']))
                    Subscription = result['data']['__schema']['subscriptionType']['name']
                else:
                    Subscription = None
                # --------------------
                i = 0
                ##########################################################################################
                # Parsing JSON response/file structure as follows
                # data
                #   __schema
                #       directives
                #       mutationType
                #       queryType
                #       subscriptionType
                #       types (kind, name, description)
                #              name (RootQuery, RootMutation, Subscriptions, [custom] OBJECT)
                #              fields
                #                     name (query names)
                #                     args
                #                            name (args names)
                #                            type
                #                                   name (args types)
                ##########################################################################################
                # Start looping trough types
                if result['data']['__schema']['types'] is not None:
                    rt = result['data']['__schema']['types']
                    # holds the number of custom objects
                    xxx = 0
                    for types in rt:
                        j = 0
                        # Data -> Schema -> Types (kind, name, description)
                        # filtering out primitive types
                        # TODO: exclude interfaces & union types
                        primitives = ['Int', 'Float', 'String', 'Boolean', 'ID', '__TypeKind', '__Type', '__Schema',
                                      '__Field', '__InputValue', '__EnumValue', '__Directive', '__DirectiveLocation']
                        advanced_kind = ['INPUT_OBJECT']
                        # This super if is BOOLEAN able to switch between ENABLED custom types parameter (-c)
                        # It will selectively routine trough values needed to print
                        if ((custom is False and ((rt[i]['kind'] is not None and rt[i]['name'] is not None) and (
                                rt[i]['name'] not in primitives) and (rt[i]['kind'] not in advanced_kind) and (
                                                          (rt[i]['kind'] == "OBJECT") and (
                                                          (rt[i]['name'] == Query) or (rt[i]['name'] == Mutation) or (
                                                          rt[i]['name'] == Subscription))))) or (
                                custom is not False and ((rt[i]['kind'] is not None and rt[i]['name'] is not None) and (
                                rt[i]['name'] not in primitives) and (rt[i]['kind'] not in advanced_kind)))):
                            output_file.write("<li>{0}</li>".format(rt[i]['kind']))
                            # Print our types RootQuery, RootMutation, Subscriptions
                            # --------------------
                            if rt[i]['name'] == Mutation:
                                output_file.write("<li class='mutation'>{0}</li>".format(rt[i]['name']))
                            elif rt[i]['name'] == Query:
                                output_file.write("<li class='query'>{0}</li>".format(rt[i]['name']))
                            elif rt[i]['name'] == Subscription:
                                output_file.write("<li class='subscription'>{0}</li>".format(rt[i]['name']))
                            # Handles custom objects (FIELDS)
                            elif rt[i]['kind'] == "OBJECT" and rt[i]['name'] is not None:
                                output_file.write("<span class='type'>{0}</span><br>".format(rt[i]['name']))
                                fields_names.append([rt[i]['name']])
                                xxx += 1
                            if rt[i]['description'] is not None:
                                output_file.write(
                                    "<span class='description'>{0}</span><br>".format(rt[i]['description']))
                            # --------------------
                        k = 0
                        # Retrieving general docs regarding primitives (filtered out from documentation, not needed)
                        # Data -> Schema -> Types -> enumValues (name, description, isDeprecated, deprecationReason)
                        # My super BOOLEAN IF, used to switch between ENABLED custom types parameter (-c)
                        if ((custom is False and (
                                rt[i]['enumValues'] is not None and (rt[i]['name'] not in primitives) and (
                                rt[i]['kind'] not in advanced_kind) and (
                                        (rt[i]['kind'] == "OBJECT") and (
                                        (rt[i]['name'] == Query) or (rt[i]['name'] == Mutation) or (
                                        rt[i]['name'] == Subscription))))) or (
                                custom is not False and ((rt[i]['enumValues'] is not None) and (
                                rt[i]['name'] not in primitives) and (rt[i]['kind'] not in advanced_kind)))):
                            for enumValues in rt[i]['enumValues']:
                                # Name
                                if rt[i]['enumValues'][k]['name'] is not None:
                                    output_file.write("<span>{0}</span><br>".format(rt[i]['enumValues'][k]['name']))
                                # Description
                                if rt[i]['enumValues'][k]['description'] is not None:
                                    output_file.write("<span class='description'>{0}</span><br>".format(
                                        rt[i]['enumValues'][k]['description']))
                                # Is Deprecated?
                                if rt[i]['enumValues'][k]['isDeprecated'] is not False and rt[i]['enumValues'][k][
                                    'isDeprecated'] is not None:
                                    output_file.write("<span class='deprecated'>Is Deprecated</span><br>")
                                # Deprecation Reason
                                if rt[i]['enumValues'][k]['deprecationReason'] is not None:
                                    output_file.write("<span>Reason: {0}</span><br>".format(
                                        rt[i]['enumValues'][k]['deprecationReason']))
                                k = k + 1
                        # Retrieving queries, mutations and subscriptions information
                        # Data -> Schema -> Types -> Fields (name, isDeprecated, deprecationReason, description)
                        # My super BOOLEAN IF, used to switch between ENABLED custom types parameter (-c)
                        if ((custom is False and ((
                                                          rt[i]['fields'] is not None) and (
                                                          rt[i]['name'] not in primitives) and (
                                                          rt[i]['kind'] not in advanced_kind) and (
                                                          (rt[i]['kind'] == "OBJECT") and (
                                                          (rt[i]['name'] == Query) or (rt[i]['name'] == Mutation) or (
                                                          rt[i]['name'] == Subscription))))) or (
                                custom is not False and ((
                                                                 rt[i]['fields'] is not None) and (
                                                                 rt[i]['name'] not in primitives) and (
                                                                 rt[i]['kind'] not in advanced_kind)))):
                            # Printing out queries, mutations, subscriptions and custom object names
                            # --------------------
                            # number of fields per obj
                            for fields in result['data']['__schema']['types'][i]['fields']:
                                if rt[i]['fields'][j]['name'] is not None:
                                    # Query
                                    if rt[i]['name'] == Query:
                                        output_file.write(
                                            "<li class='query'>{0}</li>".format(rt[i]['fields'][j]['name']))
                                        # Get field name and its type, if none is an advanced element (es. list) and we get it from ofType
                                        q_name.append(rt[i]['fields'][j]['name'])
                                        q_args_name.append([])
                                        if rt[i]['fields'][j]['type']['name'] is not None:
                                            q_type.append(rt[i]['fields'][j]['type']['name'])
                                        else:
                                            q_type.append(rt[i]['fields'][j]['type']['ofType']['name'])
                                    # Mutation
                                    elif rt[i]['name'] == Mutation:
                                        output_file.write(
                                            "<li class='mutation'>{0}</li>".format(rt[i]['fields'][j]['name']))
                                        # Get field name and its type, if none is an advanced element (es. list) and we get it from ofType
                                        m_name.append(rt[i]['fields'][j]['name'])
                                        m_args_name.append([])
                                        if rt[i]['fields'][j]['type']['name'] is not None:
                                            m_type.append(rt[i]['fields'][j]['type']['name'])
                                        else:
                                            m_type.append(rt[i]['fields'][j]['type']['ofType']['name'])
                                    # Subscription
                                    elif rt[i]['name'] == Subscription:
                                        output_file.write(
                                            "<li class='subscription'>{0}</li>".format(rt[i]['fields'][j]['name']))
                                        # Get field name and its type, if none is an advanced element (es. list) and we get it from ofType
                                        s_name.append(rt[i]['fields'][j]['name'])
                                        s_args_name.append([])
                                        if rt[i]['fields'][j]['type']['name'] is not None:
                                            s_type.append(rt[i]['fields'][j]['type']['name'])
                                        else:
                                            s_type.append(rt[i]['fields'][j]['type']['ofType']['name'])
                                    # It handle custom objects
                                    elif rt[i]['kind'] == "OBJECT":
                                        output_file.write(
                                            "<span class='field'>{0}</span>&nbsp;&nbsp;".format(
                                                rt[i]['fields'][j]['name']))
                                        # here I  add the args name the field list
                                        # xxx-1 since it will be incremented after the assign, otherwise list out of bound
                                        fields_names[xxx - 1].append(rt[i]['fields'][j]['name'])
                                    # Seems that i do not need the following two lines
                                    # else:
                                    #    output_file.write("<li>{0}</li>".format(rt[i]['fields'][j]['name']))
                                # --------------------
                                # Printing info regarding the queries, mutations and subscriptions above
                                # --------------------
                                # Deprecated
                                if rt[i]['fields'][j]['isDeprecated'] is not False and rt[i]['fields'][j][
                                    'isDeprecated'] is not None:
                                    output_file.write("<span class='deprecated'>Is Deprecated</span><br>")
                                # Deprecated Reason
                                if rt[i]['fields'][j]['deprecationReason'] is not None:
                                    output_file.write(
                                        "<span>Reason: {0}</span><br>".format(rt[i]['fields'][j]['deprecationReason']))
                                # Description
                                if rt[i]['fields'][j]['description'] is not None and rt[i]['fields'][j][
                                    'description'] != '':
                                    output_file.write(
                                        "<span class='description'>{0}</span><br>".format(
                                            rt[i]['fields'][j]['description']))
                                # Name (fields type)
                                if rt[i]['fields'][j]['type'] is not None:
                                    if rt[i]['fields'][j]['type']['name'] is not None:
                                        output_file.write("<span class='type'>{0}</span><br>".format(
                                            rt[i]['fields'][j]['type']['name']))
                                # oFType
                                if rt[i]['fields'][j]['type']['ofType'] is not None and \
                                        rt[i]['fields'][j]['type']['ofType']['name'] is not None:
                                    # LIST
                                    if rt[i]['fields'][j]['type']['kind'] is not None and rt[i]['fields'][j]['type'][
                                        'kind'] == "LIST":
                                        output_file.write("<span class='type'>[{0}]</span><br>".format(
                                            rt[i]['fields'][j]['type']['ofType']['name']))
                                    # NOT NULL
                                    elif rt[i]['fields'][j]['type']['kind'] is not None and rt[i]['fields'][j]['type'][
                                        'kind'] == "NON_NULL":
                                        output_file.write("<span class='type'>!{0}</span><br>".format(
                                            rt[i]['fields'][j]['type']['ofType']['name']))
                                    # CUSTOM TYPE
                                    else:
                                        output_file.write("<span class='type'>{0}</span><br>".format(
                                            rt[i]['fields'][j]['type']['ofType']['name']))
                                # --------------------
                                x = 0
                                # Prepare a list of ARGS names for queries, mutations and subscriptions
                                # --------------------
                                # My super BOOLEAN IF, used to switch between ENABLED custom types parameter (-c)
                                if ((custom is False and ((rt[i]['fields'][j]['args'] is not None) and (
                                        rt[i]['name'] not in primitives) and (
                                                                  rt[i]['kind'] not in advanced_kind) and (
                                                                  (rt[i]['kind'] == "OBJECT") and (
                                                                  (rt[i]['name'] == Query) or (
                                                                  rt[i]['name'] == Mutation) or (
                                                                          rt[i]['name'] == Subscription))))) or (
                                        custom is not False and ((rt[i]['fields'][j]['args'] is not None) and (
                                        rt[i]['name'] not in primitives) and (rt[i]['kind'] not in advanced_kind)))):
                                    # Printing out queries, mutations and subscriptions ARGS name
                                    # Data -> Schema -> Types -> Fields -> Args (defaultValue, name, description)
                                    # --------------------
                                    for args in rt[i]['fields'][j]['args']:
                                        # Default value if present
                                        if rt[i]['fields'][j]['args'][x]['defaultValue'] is not None:
                                            output_file.write(
                                                "<span>{0}</span><br>".format(
                                                    rt[i]['fields'][j]['args'][x]['defaultValue']))
                                        # ARGS name
                                        if rt[i]['fields'][j]['args'][x]['name'] is not None:
                                            output_file.write("<span class='argument'>{0}</span>&nbsp;&nbsp;".format(
                                                rt[i]['fields'][j]['args'][x]['name']))
                                            # Will append the ARG name to the correct list
                                            # based on if it is an argument from query, mutation or subscription
                                            # --------------------
                                            if rt[i]['name'] == Query:
                                                q_args_name[j].append(rt[i]['fields'][j]['args'][x]['name'])
                                            elif rt[i]['name'] == Mutation:
                                                m_args_name[j].append(rt[i]['fields'][j]['args'][x]['name'])
                                            elif rt[i]['name'] == Subscription:
                                                s_args_name[j].append(rt[i]['fields'][j]['args'][x]['name'])
                                            # --------------------
                                        # ARGS description
                                        if rt[i]['fields'][j]['args'][x]['description'] is not None and \
                                                rt[i]['fields'][j]['args'][x]['description'] != '':
                                            output_file.write("<span class='description'>{0}</span><br>".format(
                                                rt[i]['fields'][j]['args'][x]['description']))
                                        # --------------------
                                        # Printing out ARGS types
                                        # Data -> Schema -> Types -> Fields -> Args -> Type (name, ofType, kind)
                                        # TODO half a bug: there are custom objects that have multiple types as the following example
                                        # in this case ![LIST], at the moment this specific case is handled casting the returning value of
                                        # rt[i]['fields'][j]['args'][x]['type']['ofType']['name'] to STRING
                                        # in order to prevent errors (None type concatenated to a string)
                                        # we are missing the custom object but at least the script does not falls apart
                                        """
                                             "description":null,
                                             "isDeprecated":false,
                                             "args":[  ],
                                             "deprecationReason":null,
                                             "type":{  
                                                "kind":"NON_NULL",
                                                "name":null,
                                                "ofType":{  
                                                   "kind":"LIST",
                                                   "name":null,
                                                   "ofType":{  
                                                      "kind":"NON_NULL",
                                                      "name":null,
                                                      "ofType":{  
                                                         "kind":"SCALAR",
                                                         "name":"String",
                                                         "ofType":null
                                                      }
                                                   }
                                                }
                                             },
                                             "name":"roles"
                                        """
                                        # --------------------
                                        if rt[i]['fields'][j]['args'][x]['type'] is not None and (
                                                rt[i]['name'] not in primitives) and (
                                                rt[i]['kind'] not in advanced_kind):
                                            # LIST
                                            if rt[i]['fields'][j]['args'][x]['type']['kind'] == "LIST":
                                                output_file.write("<span class='type'>[{0}]</span><br>".format(
                                                    rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                                if rt[i]['name'] == Query:
                                                    q_args_type.append(
                                                        "[%s]" % str(rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                                elif rt[i]['name'] == Mutation:
                                                    m_args_type.append(
                                                        "[%s]" % str(rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                                elif rt[i]['name'] == Subscription:
                                                    s_args_type.append(
                                                        "[%s]" % str(rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                            # NOT NULL
                                            elif rt[i]['fields'][j]['args'][x]['type']['kind'] == "NON_NULL":
                                                output_file.write("<span class='type'>{0}!</span><br>".format(
                                                    rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                                if rt[i]['name'] == Query:
                                                    q_args_type.append(
                                                        "!%s" % str(
                                                            rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                                elif rt[i]['name'] == Mutation:
                                                    m_args_type.append(
                                                        "!%s" % str(
                                                            rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                                elif rt[i]['name'] == Subscription:
                                                    s_args_type.append(
                                                        "!%s" % str(
                                                            rt[i]['fields'][j]['args'][x]['type']['ofType']['name']))
                                            # Holds simple types like float, string, int etc.
                                            else:
                                                if rt[i]['fields'][j]['args'][x]['type']['name'] is not None:
                                                    output_file.write("<span class='type'>{0}</span><br>".format(
                                                        rt[i]['fields'][j]['args'][x]['type']['name']))
                                                    if rt[i]['name'] == Query:
                                                        q_args_type.append(
                                                            str(rt[i]['fields'][j]['args'][x]['type']['name']))
                                                    elif rt[i]['name'] == Mutation:
                                                        m_args_type.append(
                                                            str(rt[i]['fields'][j]['args'][x]['type']['name']))
                                                    elif rt[i]['name'] == Subscription:
                                                        s_args_type.append(
                                                            str(rt[i]['fields'][j]['args'][x]['type']['name']))
                                        # --------------------
                                        x += 1
                                j += 1
                        i += 1
            # For None key exceptions use: except KeyError:
            except Exception:
                raise
            # Close documentation
            output_file.write("</body></html>")
            output_file.close()
            # Writing templates
            # Reverse args list in order to use pop
            q_args_type.reverse()
            m_args_type.reverse()
            s_args_type.reverse()
            # replacing None items to String for a smooth exec
            q_type = map(str, q_type)
            m_type = map(str, m_type)
            s_type = map(str, s_type)
            # --------------------
            # QUERY
            # --------------------
            print(stringjoin(green, "Writing Queries Templates", white))
            index = 0
            for qname in q_name:
                print(" |  %s" % str(qname))
                file_write(URL, "query", today, timestamp, qname, "{\"query\":\"query %s {%s" % (qname, qname), "w")
                if len(q_args_name[index]) != 0:
                    file_write(URL, "query", today, timestamp, qname, "(", "a")
                    for argsname in q_args_name[index]:
                        # POP out of the list empty values
                        if argsname != "":
                            # if detect type (-d param) is enabled, retrieve placeholders according to arg type
                            if detect:
                                file_write(URL, "query", today, timestamp, qname,
                                           "%s:%s " % (argsname, detect_type(q_args_type.pop())), "a")
                            else:
                                file_write(URL, "query", today, timestamp, qname, "%s:%s " % (argsname, q_args_type.pop()), "a")
                        else:
                            q_args_type.pop()
                    # Query name
                    file_write(URL, "query", today, timestamp, qname, ")", "a")
                file_write(URL, "query", today, timestamp, qname, "{", "a")
                # Query fields
                f_index = 0
                for fieldsnames in fields_names:
                    if q_type[index] in fields_names[f_index][0]:
                        for items in fields_names[f_index][1:]:
                            file_write(URL, "query", today, timestamp, qname, "%s " % items, "a")
                        break
                    f_index += 1
                # Close query
                file_write(URL, "query", today, timestamp, qname, "}}\"}", "a")
                index += 1
            # --------------------
            # MUTATION
            # --------------------
            print(stringjoin(green, "Writing Mutations Templates", white))
            index = 0
            for mname in m_name:
                print(" |  %s" % str(mname))
                file_write(URL, "mutation", today, timestamp, mname, "{\"query\":\"mutation{%s(" % mname, "w")
                for argsname in m_args_name[index]:
                    # POP out of the list empty values
                    if argsname != "":
                        # if detect type (-d param) is enabled, retrieve placeholders according to arg type
                        if detect:
                            file_write(URL, "mutation", today, timestamp, mname,
                                       "%s:%s " % (argsname, detect_type(m_args_type.pop())), "a")
                        else:
                            file_write(URL, "mutation", today, timestamp, mname,
                                       "%s:%s " % (argsname, m_args_type.pop()), "a")
                    else:
                        m_args_type.pop()
                # Mutation name
                file_write(URL, "mutation", today, timestamp, mname, "){", "a")
                # Mutation fields
                f_index = 0
                for fieldsnames in fields_names:
                    if m_type[index] in fields_names[f_index][0]:
                        for items in fields_names[f_index][1:]:
                            file_write(URL, "mutation", today, timestamp, mname, "%s " % items, "a")
                        break
                    f_index += 1
                # Close mutation
                file_write(URL, "mutation", today, timestamp, mname, "}}\"}", "a")
                index += 1
            # --------------------
            # SUBSCRIPTION
            # --------------------
            print(stringjoin(green, "Writing Subscriptions Templates", white))
            index = 0
            for sname in s_name:
                print(" |  %s" % str(sname))
                file_write(URL, "subscription", today, timestamp, sname, "{\"query\":\"subscription{%s(" % sname,
                           "w")
                for argsname in s_args_name[index]:
                    # POP out of the list empty values
                    if argsname != "":
                        # if detect type (-d param) is enabled, retrieve placeholders according to arg type
                        if detect:
                            file_write(URL, "subscription", today, timestamp, sname,
                                       "%s:%s " % (argsname, detect_type(s_args_type.pop())), "a")
                        else:
                            file_write(URL, "subscription", today, timestamp, sname,
                                       "%s:%s " % (argsname, s_args_type.pop()), "a")
                    else:
                        s_args_type.pop()
                # Subscription name
                file_write(URL, "subscription", today, timestamp, sname, "){", "a")
                # Subscription fields
                f_index = 0
                for fieldsnames in fields_names:
                    if s_type[index] in fields_names[f_index][0]:
                        for items in fields_names[f_index][1:]:
                            file_write(URL, "subscription", today, timestamp, sname, "%s " % items, "a")
                        break
                    f_index += 1
                # Close subscription
                file_write(URL, "subscription", today, timestamp, sname, "}}\"}", "a")
                index += 1
            # --------------------
            # THE END, they all lived happily ever after (hopefully)
            print(stringjoin(green, "DONE", white))
    else:
        # Likely missing a required arguments
        print("Missing Arguments")
        if print_help:
            print(white)
            print_help()
            exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Catch CTRL+C, it will abruptly kill the script
        print(stringjoin(red, "Exiting...", reset))
