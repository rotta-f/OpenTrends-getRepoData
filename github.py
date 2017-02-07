import urllib.request
import urllib.parse
import urllib.error
import json
import base64


class Github:
    def __init__(self, login=None, password=None, verbose=False):
        self.API_URL = "https://api.github.com"

        self.verbose = verbose
        self.loginBase64 = None
        self.__data_caching__ = {}
        if login and password:
            self.loginBase64 = base64.urlsafe_b64encode(("%s:%s" % (login, password)).encode('utf-8')).decode('utf-8')
        self.setRepository(None)

    def __getRequest__(self, endpoint, full_url=False):
        if full_url:
            request =  urllib.request.Request(endpoint)
        else:
            url = urllib.parse.urljoin(self.API_URL, endpoint)
            request = urllib.request.Request(url)
        if self.verbose:
            print("[Github] " + request.get_method() + " " + request.get_full_url())
        if self.loginBase64:
            request.add_header('Authorization', "Basic " + self.loginBase64)
        return request

    def getRateLimit(self):
        request = self.__getRequest__("rate_limit")
        content = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
        return content

    def setRepository(self, repository):
        self.repository = repository

    def getRepository(self):
        return self.repository

    def __getLinkParams__(self, response):
        links = response.getheader('Link').split(',')
        linksLen = len(links)
        linkParams = []
        for i in range(linksLen):
            link = {}
            for elem in links[i].split(';'):
                elem = elem.split()[0]
                if elem.find('rel=') != -1:
                    rel = elem.split('=')[1]
                    link["rel"] = rel.split('"')[1]
                else:
                    url = elem[1:-1]
                    link["url"] = url
                    parseUrl = urllib.parse.urlparse(url)
                    queryParams = {}
                    for param in parseUrl.query.split('&'):
                        keyPair = param.split('=')
                        queryParams[keyPair[0]] = keyPair[1]
                    link["queryParams"] = queryParams
                    if 'page' not in link["queryParams"]:
                        print(parseUrl, link)
                        raise Exception("Github", "Bad query response: " + link["url"])
            linkParams.append(link)
        return linkParams

    def __getRepositoryItems__(self, item, state='all', page='0', direction='desc'):
        if not self.repository:
            raise Exception("Github", "No repository set")
        request = self.__getRequest__("repos/" + self.repository + "/" + item + "?" +
                                      "page=" + page +
                                      ("&state=" + state if state else "") +
                                      ("&direction=" + direction if direction else ""))
        key = request.get_method() + ":" + request.get_full_url()
        if not key in self.__data_caching__:
            response = urllib.request.urlopen(request)
            self.__data_caching__[request.get_method() + ":" + request.get_full_url()] = {
                "response": response,
                "content": json.loads(response.read().decode("utf-8"))
            }
        return self.__data_caching__[key]["response"], self.__data_caching__[key]["content"]

    def __getItems__(self, item, state='all', page='0', direction='desc'):
        return self.__getRepositoryItems__(item, state=state, page=page, direction=direction)

    def getItemsCount(self, item, state='all', direction='desc'):
        response, content = self.__getItems__(item, state=state, direction=direction)

        pagination = len(content)

        if response.getheader('Link'):
            linkParams = self.__getLinkParams__(response)
            lastLink = None
            for link in linkParams:
                if link['rel'] == 'last':
                    lastLink = link

            response, content = self.__getItems__(item,
                                                  state=(lastLink["queryParams"]["state"] if 'state' in lastLink["queryParams"] else None),
                                                  page=lastLink["queryParams"]["page"],
                                                  direction=direction)
            nbPages = int(lastLink["queryParams"]["page"])

            count = (nbPages - 1) * pagination + len(content)
        else:
            count = pagination

        return count

    def getPullsCount(self, state='all'):
        return self.getItemsCount('pulls', state=state)

    def getIssuesCount(self, state='all'):
        return self.getItemsCount('issues', state=state) - self.getItemsCount('pulls', state=state)

    def getCommitsCount(self):
        return self.getItemsCount('commits', state=None, direction=None)

    def getOldestPullRequest(self, state='all'):
        response, content = self.__getItems__('pulls', state=state, direction='asc')
        if len(content) > 0:
            return content[0]
        return None

    def getOldestIssueRequest(self, state='all'):
        response, content = self.__getItems__('issues', state=state, direction='asc')
        first = True
        while response.getheader('Link') or first:
            first = False
            for elem in content:
                if not 'pull_request' in elem:
                    return elem
            if response.getheader('Link'):
                linkParams = self.__getLinkParams__(response)
                for link in linkParams:
                    if link['rel'] == 'next':
                        nextLink = link

                response, content = self.__getItems__('issues', state=nextLink["queryParams"]["state"], page=nextLink["queryParams"]["page"], direction='asc')
        return None


    def getRepositoryInfo(self, repository=None):
        if not repository:
            repository = self.repository

        if not self.repository:
            raise Exception("Github", "No repository set")

        request = self.__getRequest__("repos/" + self.repository)
        response = urllib.request.urlopen(request)
        content = json.loads(response.read().decode("utf-8"))
        return content