# app/main.py
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, JoinEvent, QuickReply, QuickReplyButton, MessageAction, BubbleContainer, CarouselContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, SeparatorComponent, URIAction, FlexSendMessage
from dotenv import load_dotenv
import os

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

# --- この関数でカルーセルメッセージを作成して送信 ---
def send_restaurant_carousel(reply_token, restaurant_list):
    """
    レストラン情報のリストを受け取り、カルーセル形式のFlex Messageを送信する
    """
    bubbles = []
    # レストランの数だけ、情報カード（バブル）を作成
    for restaurant in restaurant_list:
        bubble = create_restaurant_bubble(restaurant)
        bubbles.append(bubble)

    # カルーセルコンテナを作成
    carousel_container = CarouselContainer(contents=bubbles)

    # FlexSendMessageを作成
    # alt_textは、LINEのトークリストに表示される代替テキストです
    flex_message = FlexSendMessage(
        alt_text="おすすめのレストランが見つかりました！",
        contents=carousel_container
    )

    # メッセージを送信
    line_bot_api.reply_message(reply_token, flex_message)


# --- 個別のレストラン情報カード（バブル）を作成するヘルパー関数 ---
def create_restaurant_bubble(restaurant: dict) -> BubbleContainer:
    """
    一つのレストラン情報から、一つのバブルコンテナを作成する
    """
    return BubbleContainer(
        # --- ヒーローブロック (メイン画像) ---
        hero=ImageComponent(
            url=restaurant.get("image_url", "https://example.com/default.jpg"),
            size="full",
            aspect_ratio="20:13",
            aspect_mode="cover",
            action=URIAction(uri=restaurant.get("url", "#"), label="ウェブサイト")
        ),
        # --- ボディブロック (店名、評価、場所などの情報) ---
        body=BoxComponent(
            layout="vertical",
            spacing="sm",
            contents=[
                # 店名
                TextComponent(
                    text=restaurant.get("name", "レストラン名なし"),
                    weight="bold",
                    size="xl",
                    wrap=True
                ),
                # 評価 (例: ★★★★☆ 4.0)
                BoxComponent(
                    layout="baseline",
                    margin="md",
                    contents=[
                        # ここは星の数だけループさせたり、固定の星画像にしたりする
                        TextComponent(text="★★★★☆", size="sm", color="#ffb740", flex=0),
                        TextComponent(text=str(restaurant.get("rating", 0.0)), size="sm", color="#999999", flex=0, margin="md"),
                    ]
                ),
                # ジャンルや場所
                BoxComponent(
                    layout="vertical",
                    margin="lg",
                    spacing="sm",
                    contents=[
                        BoxComponent(
                            layout="baseline",
                            spacing="sm",
                            contents=[
                                TextComponent(text="場所", color="#aaaaaa", size="sm", flex=1),
                                TextComponent(text=restaurant.get("address", "-"), color="#666666", size="sm", flex=4, wrap=True),
                            ]
                        ),
                        BoxComponent(
                            layout="baseline",
                            spacing="sm",
                            contents=[
                                TextComponent(text="ジャンル", color="#aaaaaa", size="sm", flex=1),
                                TextComponent(text=restaurant.get("genre", "-"), color="#666666", size="sm", flex=4, wrap=True),
                            ]
                        ),
                    ]
                ),
            ]
        ),
        # --- フッターブロック (アクションボタン) ---
        footer=BoxComponent(
            layout="vertical",
            spacing="sm",
            contents=[
                # 詳細を見るボタン (Webサイトへ)
                ButtonComponent(
                    style="link",
                    height="sm",
                    action=URIAction(label="詳しく見る", uri=restaurant.get("url", "#"))
                ),
                # このお店にするボタン (ボットへの返信)
                ButtonComponent(
                    style="primary",
                    height="sm",
                    action=MessageAction(label="このお店にする！", text=f"{restaurant.get('name')}に決めます")
                ),
            ]
        )
    )

dummy_restaurants = [
    {
        "name": "最高のイタリアン A",
        "image_url": "https://example.com/restaurant_a.jpg",
        "rating": 4.5,
        "address": "東京都文京区本郷1-2-3",
        "genre": "イタリアン",
        "url": "https://example.com/a"
    },
    {
        "name": "絶品和食 B",
        "image_url": "https://example.com/restaurant_b.jpg",
        "rating": 4.2,
        "address": "東京都文京区本郷4-5-6",
        "genre": "和食・割烹",
        "url": "https://example.com/b"
    },
]

# --- LINEイベントのハンドラ定義 ---
@handler.add(JoinEvent)
def handle_join(event):
    """
    ボットがグループに参加した時の処理
    """
    # 応答に必要な「リプライトークン」を取得
    reply_token = event.reply_token

    # 送信するメッセージを作成
    reply_message = TextSendMessage(
        text="こんにちは！飲み会調整ボットです🍻\n幹事さんは「調整スタート」と話しかけて、お店探しを始めてくださいね！"
    )

    # 応答メッセージを送信
    line_bot_api.reply_message(reply_token, reply_message)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_token = event.reply_token
    user_message = event.message.text

    # もしメッセージが「a」だったら
    if user_message == "a":
        # シンプルなテキストメッセージを作成
        reply = TextSendMessage(text="「a」が送られましたね。これはただのテキストメッセージです。")

    # もしメッセージが「b」だったら
    elif user_message == "b":
        # 選択肢付きのメッセージを作成
        reply = TextSendMessage(
            text="「b」が送られましたね。好きな果物を選んでください。",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(action=MessageAction(label="りんご🍎", text="りんご")),
                    QuickReplyButton(action=MessageAction(label="バナナ🍌", text="バナナ")),
                    QuickReplyButton(action=MessageAction(label="みかん🍊", text="みかん")),
                ]
            )
        )

    elif user_message == "c":
        send_restaurant_carousel(
            reply_token,
            dummy_restaurants
        )
    
    # 「a」でも「b」でもなかった場合
    else:
        reply = TextSendMessage(text=f"「{event.message.text}」と送られました。'a'か'b'か'c'と送ってみてください。")

    # 準備した応答メッセージを送信
    line_bot_api.reply_message(reply_token, reply)


### **ここから追加するテストエンドポイント** ---


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
