# app/main.py
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent, QuickReply, QuickReplyButton, MessageAction, BubbleContainer, CarouselContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, SeparatorComponent, URIAction, FlexSendMessage
from dotenv import load_dotenv
import os
from .line_actions import LineActions
from fastapi.staticfiles import StaticFiles

# Vertex AI関連のインポート
import vertexai
from vertexai.preview.generative_models import GenerativeModel

# Google Maps Platform関連のインポート
import googlemaps  # パッケージ名がgooglemapsであることに注意

# 環境変数をロード
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
MAPS_API_KEY = os.getenv("Maps_API_KEY")  # .envのキー名に合わせてください
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN") # ngrokサービスがDocker Composeで動くため、Pythonコードで直接使う必要は通常ありません

# 環境変数の存在チェック (テストのために一旦緩めるか、正確な値を設定してください)
# if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, MAPS_API_KEY, GCP_PROJECT_ID]):
#     raise ValueError("Required environment variables are not set. Check your .env file.")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI()
actions = LineActions(line_bot_api)

# Vertex AIの初期化 (GCP_PROJECT_IDと認証情報を使用)
try:
    vertexai.init(
        project=GCP_PROJECT_ID, location="us-central1"
    )  # あなたのプロジェクトのリージョンに合わせてください
    gemini_model = GenerativeModel("gemini-2.5-flash")
except Exception as e:
    print(f"Vertex AI initialization failed: {e}")
    gemini_model = None

# Google Maps APIクライアントの初期化
try:
    gmaps = googlemaps.Client(key=MAPS_API_KEY)
except Exception as e:
    print(f"Google Maps Client initialization failed: {e}")
    gmaps = None

# "app/static" ディレクトリを "/static" というパスで公開する
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def root():
    return {"message": "AI Restaurant Agent is running!"}


@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# --- LINEイベントのハンドラ定義 ---
@handler.add(JoinEvent)
def handle_join(event):
    """ボットがグループに参加した時の処理"""
    actions.send_join_greeting(event.reply_token)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ユーザーからのテキストメッセージを処理"""
    reply_token = event.reply_token
    user_id = event.source.user_id
    user_message = event.message.text.lower().strip()

    # --- グループチャットでの処理 ---
    if hasattr(event.source, 'group_id'):
        
        if user_message == "調整スタート":
            actions.start_individual_hearing(reply_token)
        
        elif user_message == "まとめて":
            actions.send_restaurant_carousel(reply_token)
            
        return

    # --- 1対1チャットでの処理 ---
    else:
        if user_message == "id確認":
            actions.reply_with_text(reply_token, f"あなたのユーザーIDはこちらです：\n{user_id}")
            return
        
        # ★★★ 新しい関数の呼び出しデモを追加 ★★★
        elif user_message == "b":
            question = "好きな果物を選んでください。"
            choices = ["りんご🍎", "バナナ🍌", "みかん🍊"]
            actions.reply_with_quick_reply(reply_token, question, choices)
            return

        # 通常のヒアリング会話
        else:
            actions.reply_during_hearing(reply_token, event.message.text)

@app.get("/test/vertex-ai")
async def test_vertex_ai_connection():
    if not gemini_model:
        raise HTTPException(
            status_code=500,
            detail="Vertex AI model not initialized. Check logs for errors.",
        )
    try:
        response = await gemini_model.generate_content_async(
            "こんにちは。自己紹介をしてください。"
        )
        # 応答が複数の部分に分かれる可能性があるため、text属性で結合
        model_response = "".join(
            [part.text for part in response.candidates[0].content.parts]
        )
        return {"status": "success", "model_response": model_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vertex AI test failed: {e}")


@app.get("/test/google-maps")
async def test_Maps_connection():
    if not gmaps:
        raise HTTPException(
            status_code=500,
            detail="Google Maps client not initialized. Check logs for errors.",
        )
    try:
        # 東京駅周辺のカフェを検索する例
        query = "東京駅 カフェ"
        places_result = gmaps.places(query=query)

        if places_result and places_result.get("results"):
            first_place_name = places_result["results"][0]["name"]
            first_place_id = places_result["results"][0]["place_id"]

            # その場所の口コミを取得 (Places APIの詳細リクエストが必要)
            place_details = gmaps.place(place_id=first_place_id, fields=["reviews"])
            reviews = place_details.get("result", {}).get("reviews", [])

            return {
                "status": "success",
                "query": query,
                "first_place_name": first_place_name,
                "first_place_id": first_place_id,
                "reviews_count": len(reviews),
                "sample_review": reviews[0]["text"] if reviews else "No reviews found",
            }
        else:
            return {
                "status": "no_results",
                "query": query,
                "message": "No places found for the query.",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Maps test failed: {e}")
