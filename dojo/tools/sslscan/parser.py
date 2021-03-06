from xml.dom import NamespaceErr
import hashlib
from urllib.parse import urlparse
from defusedxml import ElementTree as ET
from dojo.models import Endpoint, Finding

__author__ = 'dr3dd589'


class SslscanXMLParser(object):
    def __init__(self, file, test):
        self.dupes = dict()
        self.items = ()
        if file is None:
            return

        tree = ET.parse(file)
        # get root of tree.
        root = tree.getroot()
        if 'document' not in root.tag:
            raise NamespaceErr("This doesn't seem to be a valid sslscan xml file.")

        for ssltest in root:
            for target in ssltest:
                title = ""
                severity = ""
                description = ""
                severity = "Info"
                url = ssltest.attrib['host']
                port = ssltest.attrib['port']
                parsedUrl = urlparse(url)
                protocol = parsedUrl.scheme
                query = parsedUrl.query
                fragment = parsedUrl.fragment
                path = parsedUrl.path
                try:
                    (host, port) = parsedUrl.netloc.split(':')
                except:
                    host = parsedUrl.netloc
                if target.tag == "heartbleed" and target.attrib['vulnerable'] == '1':
                    title = "heartbleed" + " | " + target.attrib['sslversion']
                    description = "**heartbleed** :" + "\n\n" + \
                                "**sslversion** : " + target.attrib['sslversion'] + "\n"
                if target.tag == "cipher" and target.attrib['strength'] not in ['acceptable', 'strong']:
                    title = "cipher" + " | " + target.attrib['sslversion']
                    description = "**Cipher** : " + target.attrib['cipher'] + "\n\n" + \
                                "**Status** : " + target.attrib['status'] + "\n\n" + \
                                "**strength** : " + target.attrib['strength'] + "\n\n" + \
                                "**sslversion** : " + target.attrib['sslversion'] + "\n"

                if title and description is not None:
                    dupe_key = hashlib.md5(str(description + title).encode('utf-8')).hexdigest()
                    if dupe_key in self.dupes:
                        finding = self.dupes[dupe_key]
                        if finding.references:
                            finding.references = finding.references
                        self.dupes[dupe_key] = finding
                    else:
                        self.dupes[dupe_key] = True

                        finding = Finding(
                            title=title,
                            test=test,
                            active=False,
                            verified=False,
                            description=description,
                            severity=severity,
                            numerical_severity=Finding.get_numerical_severity(severity),
                            dynamic_finding=True,)
                        finding.unsaved_endpoints = list()
                        self.dupes[dupe_key] = finding

                        if url is not None:
                            finding.unsaved_endpoints.append(Endpoint(
                                host=host,
                                port=port,
                                path=path,
                                protocol=protocol,
                                query=query,
                                fragment=fragment,))
                self.items = self.dupes.values()
