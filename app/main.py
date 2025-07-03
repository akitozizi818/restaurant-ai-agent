# app/main.py
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent, QuickReply, QuickReplyButton, MessageAction, BubbleContainer, CarouselContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, SeparatorComponent, URIAction, FlexSendMessage
from dotenv import load_dotenv
import os
from .line_actions import LineActions
from .function_definitions import function_declarations
from fastapi.staticfiles import StaticFiles
from .ai_agent import AIAgent
from .google_maps_actions import GoogleMapsActions

# Vertex AI関連のインポート
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Tool

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
# ハッカソン用のシンプルなセッション管理（共有メモ帳）
# サーバーのメモリ上に存在するため、再起動すると消えますが、デモでは十分です。
sessions = {}

# Vertex AIの初期化 (GCP_PROJECT_IDと認証情報を使用)
try:
    vertexai.init(
        project=GCP_PROJECT_ID, location="us-central1"
    )  # あなたのプロジェクトのリージョンに合わせてください
    gemini_model = GenerativeModel("gemini-2.5-flash",
        tools=[Tool.from_function_declarations(function_declarations)])
except Exception as e:
    print(f"Vertex AI initialization failed: {e}")
    gemini_model = None

# Google Maps APIクライアントの初期化
try:
    gmaps = googlemaps.Client(key=MAPS_API_KEY)
except Exception as e:
    print(f"Google Maps Client initialization failed: {e}")
    gmaps = None

gmaps_actions = GoogleMapsActions(gemini_model, os.getenv("NGROK_BASE_URL", ""))
actions = LineActions(line_bot_api, gmaps_actions)
ai_agent = AIAgent(gemini_model, actions)

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
    actions.send_start_prompt(event.reply_token)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ユーザーからのテキストメッセージを処理"""
    reply_token = event.reply_token
    user_id = event.source.user_id
    user_message = event.message.text

    # --- グループチャットでの処理 ---
    if hasattr(event.source, 'group_id'):
        group_id = event.source.group_id
        
        if user_message.lower().strip() == "スタート":
            # 「共有メモ帳」に、このグループ用の新しいページを作成
            sessions[group_id] = {
                "status": "hearing",
                "preferences": {}
            }

        if user_message.lower().strip() == "終了":
            actions.send_start_prompt(event.reply_token)

        if "common" not in sessions[group_id]["preferences"]:
            sessions[group_id]["preferences"]["common"] = []
        sessions[group_id]["preferences"]["common"].append(user_message)
        ai_agent.process_group_message(event, sessions[group_id])
        return

    # --- 1対1チャットでの処理 ---
    else:
        # ユーザーがどの飲み会に参加しているかを特定する（簡易的な方法）
        active_group_id = None
        for g_id, session in sessions.items():
            # このデモでは、ユーザーが最後にアクティブだったグループに参加していると仮定
            # (本来は、ユーザーが複数のグループに属している場合を考慮する必要がある)
            active_group_id = g_id
            break # 最初に見つかったセッションを使う

        if active_group_id:
            # 1. ユーザーの希望を「共有メモ帳」に記録
            if user_id not in sessions[active_group_id]["preferences"]:
                sessions[active_group_id]["preferences"][user_id] = []
            sessions[active_group_id]["preferences"][user_id].append(user_message)
            
            print("--- 現在の全希望 ---")
            print(sessions[active_group_id])
            print("--------------------")
            
            # 2. AIエージェントに、現在の全希望を渡して処理させる
            ai_agent.process_individual_message(event, sessions[active_group_id])
        else:
            actions.reply_with_text(reply_token, "参加中の飲み会調整が見つかりません。グループで幹事さんが「調整スタート」と入力したか確認してください。")

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
