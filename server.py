import requests
import json
from os import remove
from flask import Flask
from flask import request
from gtts import gTTS

# load token and data to confirmation
with open("data.json", "r") as file:
    data = json.loads(file.read())


app = Flask(__name__)
# vk api
api = "https://api.vk.com/method/"


def get_params(**kwargs):
    '''Make param string for request'''
    return "?" + '&'.join(str(i) + "=" + str(j)for i, j in kwargs.items())


def upload_voice(file_name, user):
    '''Upload voice record with "file_name" on server vk as document'''
    # get upload url
    upload_url = requests.get(api + "docs.getMessagesUploadServer" +
                              get_params(access_token=data["token"],
                                         type="audio_message", peer_id=user)
                              ).json()['response']['upload_url']
    # upload file on server
    file = requests.post(upload_url,
                         files={"file": open(file_name, "rb")}
                         ).json()["file"]
    # save file as document
    resp = requests.post(api + "docs.save" +
                         get_params(access_token=data["token"],
                                    file=file)
                         ).json()["response"]
    # remove file(it is temp file)
    remove(file_name)
    # return finished link on this voice record
    return "doc" + str(resp[0]["owner_id"]) + "_" + str(resp[0]["did"])


def get_tts(text):
    '''Get voice from text'''
    # first 2 letters mean lang
    locale = text[:2]
    # rest letters text
    text = text[2:]
    # get tts from google
    voice = gTTS(text=text, lang=locale, slow=False)
    # save file and return file_name
    file_name = "temp.mp3"
    voice.save(file_name)
    return file_name


@app.route("/test", methods=['GET', 'POST'])
def test():
    '''Server for processing incoming messages'''
    # Check request content type is json
    if(request.method == 'POST' and
       request.headers.get('Content-Type') == 'application/json'):
        response = request.get_json()
        # if type - "message_new" send voice record to user
        if response["type"] == "message_new":
            # get user_id
            user = response["object"]["user_id"]
            # get body of msg
            body = response["object"]["body"]
            # make request to send voice msg
            url = api + "messages.send"
            url += get_params(access_token=data["token"],
                              message="",
                              v="5.0", user_id=user,
                              attachment=upload_voice(get_tts(body), user))
            requests.get(url)
            return "ok"
        # the confirmation
        elif response['group_id'] == data["group_id"]:
            return data["confirm"]
        else:
            pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='80')
