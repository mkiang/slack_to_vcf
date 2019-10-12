import requests
import base64
import errno
import os
import numpy as np
import pandas as pd

def mkdir_p(path):
    """ If a directory does not exist, create it. """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def is_bot(member):
    """ Recognize if slack workspace member is bot

    :param dict member struct from the slack api json response
    :return: boolean
    """
    return member['is_bot'] or member['name'] == 'slackbot'


def get_user_list(api_key, make_useful=True, return_request=False,
                  ignore_key='#ignore'):
    """ Downloads the Slack user list and returns a pd.DataFrame

    :param str api_key: your Slack API key as a string
    :param bool make_useful: cleans up and removes useless rows/cols
    :param bool return_request: return the request instead of a dataframe
    :param str ignore_key: a string indicating this user should not be included
    :return: returns a pandas.DataFrame

    """
    url = 'https://slack.com/api/users.list'
    payload = {'token': api_key}
    r = requests.get(url, params=payload)

    if return_request: # Useful for debugging
        return r

    if not r.ok:
        raise Exception("Bad request. Error code: {}".format(r.status_code))
    else:
        members = r.json()['members']
        filtered_members = [m for m in members if not is_bot(m)]
        df = pd.io.json.json_normalize(filtered_members)

        # Slightly better column names
        df.columns = [c.replace('.', '_').replace('profile_', '')
                        for c in df.columns]

        if make_useful:
            df = df[['first_name', 'last_name', 'real_name_normalized',
                     'email', 'skype', 'phone', 'title', 'image_1024']]

            # Clean up the weird unicode stuff a bit, clean up white space
            df = df.apply(lambda(x): x.str.encode('ascii',
                                                    'ignore').str.strip())
            df.replace('', np.nan, inplace=True)

            # Take out the people who don't want to be scraped
            df = df[df.title != ignore_key]

            # Take out the people without a first and last name
            df = df[(pd.notnull(df.real_name_normalized))]
            
            df.reset_index(inplace=True, drop=True)

        return df


def img_to_b64(url):
    """ Takes an image url, downloads it, converts to base64 string

    :param str url: URL of photo to be base64 encoded
    :return: A long base64 encoding of the image
    :rtype: str
    """
    r = requests.get(url)
    encoded_string = base64.b64encode(r.content)

    return encoded_string


def write_vcard(filename, first, last, full, email, tel, skype, title, pic_url):
    """
    Takes a bunch of personal info and returns a vCard (.vcf) file

    :param str filename: Full path of your file (including .vcd extension)
    :param str first: First name of the contact
    :param str last: Last name of the contact
    :param str full: Full name of the contact (not necessarily the above)
    :param str email: Contact email address
    :param str tel: Telephone number (in any format)
    :param str skype: Skype username -- renders both Google and Apple-friendly
    :param str title: Contact title
    :param str pic_url: A URL to a contact photo -- only works with Apple
    """

    with open(filename, 'wb') as f:
        f.write("BEGIN:VCARD\nVERSION:3.0\n")
        
        if pd.notnull(first) and pd.notnull(last) and pd.notnull(full):
            f.write("FN:{}\nN:{};{};;;\n".format(full, last, first))
        
        if pd.notnull(email):
            f.write("EMAIL;TYPE=INTERNET;TYPE=HOME:{}\n".format(email))
        
        if pd.notnull(tel):
            f.write("TEL;TYPE=CELL:{}\n".format(tel))
        
        if pd.notnull(skype):
            # NOTE: ORDER MATTERS! Google Contacts won't recognize this field
            # if the apple format comes after.
            # apple format
            f.write("IMPP;X-SERVICE-TYPE=Skype;type=HOME;")
            f.write("skype:{}\n".format(skype))
            # google format
            f.write("X-SKYPE:{}\n".format(skype))
        
        if pd.notnull(title):
            f.write("TITLE:{}\n".format(title))
        
        if pd.notnull(pic_url):
            # Note: jpg files need to be specified JPEG while png can be PNG.
            f.write("PHOTO;ENCODING=b;TYPE=")
            url_ext = os.path.splitext(pic_url)[1]
            if url_ext in ['.jpeg', '.jpg']:
                ext = 'JPEG'
            else:
                ext = url_ext.upper()
            f.write("{}:{}\n".format(ext, img_to_b64(pic_url)))
            # f.write("PHOTO:{}\n".format(pic_url))
    
        f.write("END:VCARD\n")


if __name__ == "__main__":
    from slack_creds import API_KEY
    df = get_user_list(API_KEY)
    dir_name = './slack_vcfs/'
    mkdir_p(dir_name)
    df.to_csv(dir_name + '0_contacts.csv', index=False)

    for row in df.itertuples():
        filename = "{}{}.vcf".format(dir_name, row.real_name_normalized)
        filename = filename.lower().replace(' ', '_').replace('-', '_')
        filename = filename.replace('(', '').replace(')', '')
        print("Making {}".format(filename))
        write_vcard(filename = filename, 
                    first = row.first_name,
                    last = row.last_name,
                    full = row.real_name_normalized, 
                    email = row.email, 
                    tel = row.phone, 
                    skype = row.skype, 
                    title = row.title, 
                    pic_url = row.image_1024)