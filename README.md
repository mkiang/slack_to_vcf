## Slack to vCards (vcf)

A simple script that just takes your Slack API, downloads all information for all users on your team, and generates `vcf` files.

## Usage

Edit the `slack_creds.py.example` file with your actual Slack API and remove the `.example` from the file. Then simply run `python make_vcards.py`.

## Caveats

This has been minimally tested. The [`vCard` specification](https://tools.ietf.org/html/rfc6350) is pretty attrocious not everything works across all platforms. For example, the embedded images only seem to work for Apple products (and even then only OS X and not iOS) and Google Contacts seems to be picky about the order of the `skype` information in the `vcf`. 
