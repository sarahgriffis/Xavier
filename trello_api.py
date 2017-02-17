import requests

class TrelloApi:
    def __init__(self, trello_api_endpoint, key, token, board_id):
        self.api_endpoint = trello_api_endpoint
        self.key = key
        self.token = token
        self.board_id = board_id
        self.__std_payload = { 'key': self.key, 'token': self.token, 'idBoard': self.board_id }

    #get all lists
    def get_lists(self, payload=None):
        payload = payload or self.__std_payload #http://stackoverflow.com/questions/8131942
        lists = requests.get(self.api_endpoint + 'boards/' + self.board_id + '/lists', params = payload )
        return lists

    def find_column(self, column_name, payload=None):
        payload = payload or self.__std_payload #http://stackoverflow.com/questions/8131942
        lists = self.get_lists(payload)
        column = [item for item in lists.json()
                if item["name"] == column_name][0]
        return column

    def fetch_all_cards(self, list_id):
        list_cards_payload = { 'attachments': 'true' }
        req = requests.get(self.api_endpoint + '/lists/' + list_id + '/cards',
                         params = dict(list_cards_payload.items() + self.__std_payload.items()) )
        return req

    #move all cards
    def move_all_cards(self, old_list_id, new_list_id):
        move_all_cards_payload = { 'idList': new_list_id }
        move_all_cards = requests.post(self.api_endpoint + '/lists/' + old_list_id + '/moveAllCards',
                                   params = dict(move_all_cards_payload.items() + self.__std_payload.items()))

    #create comments on cards
    def create_comment(self, old_list_id, card_id, text):
        create_comment_payload = { 'text': text}
        requests.post(self.api_endpoint + '/cards/' + card_id + '/actions/comments',
                params = dict(create_comment_payload.items() + self.__std_payload.items()))

    #create new list
    def create_new_list(self, tag, position):
        new_list_payload = { 'name': 'DONE ' + tag, 'pos': position }
        new_list = requests.post(self.api_endpoint + '/lists', params = dict(new_list_payload.items() + self.__std_payload.items()))
        return new_list

    #edit card
    def edit_card(self, card_id, card_dict=None):
        edit_card_payload = card_dict
        req = requests.put(self.api_endpoint + "/cards/" + card_id,
                params = dict(edit_card_payload.items() + self.__std_payload.items()))
        return req
