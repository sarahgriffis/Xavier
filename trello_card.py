class TrelloCard:
    def __init__(self, json):
        self.name = json['name']
        self.desc = json['desc']
        self.url = 'https://trello.com/c/' + json['shortLink']
        self.github_link = self.__github_link(json)
        self.json_blob = self.json_blob()

    def json_blob(self):
        return {
            "text": self.desc,
            "title": self.name,
            "title_link": self.url,
            "fields":[
                {
                    "value": self.github_link
                }
            ]
        }

    def __github_link(self, json):
        attachments = [item for item in json['attachments'] if 'github' in item["url"]]
        if len(attachments) > 0:
            return attachments[0]['url']
