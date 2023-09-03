from django.conf import settings
import requests
import os
from json import JSONDecodeError

state = os.environ.get("STATE")
BASE_URL = "https://chat-profile.audrey.kr/"
GOOGLE_CALLBACK_URI = BASE_URL + "api/user/google/callback/"


def get_google_userinfo(code):
    client_id = settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID
    client_secret = settings.SOCIAL_AUTH_GOOGLE_SECRET

    # 1. 받은 코드로 구글에 access token 요청
    token_req = requests.post(
        f"https://oauth2.googleapis.com/token?client_id={client_id}&client_secret={client_secret}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}&state={state}"
    )

    ### 1-1. json으로 변환 & 에러 부분 파싱
    token_req_json = token_req.json()
    error = token_req_json.get("error")

    print("token+req: ", token_req_json)

    ### 1-2. 에러 발생 시 종료
    if error is not None:
        raise JSONDecodeError(error)

    ### 1-3. 성공 시 access_token 가져오기
    access_token = token_req_json.get("access_token")

    #################################################################

    # 2. 가져온 access_token으로 이메일값을 구글에 요청
    userinfo_req = requests.get(
        f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
    )
    userinfo_req_status = userinfo_req.status_code

    ### 2-1. 에러 발생 시 400 에러 반환
    if userinfo_req_status != 200:
        raise Exception()

    ### 2-2. 성공 시 이메일 가져오기
    return userinfo_req.json()
