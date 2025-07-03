from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    MessageAction,
    BubbleContainer,
    CarouselContainer,
    ImageComponent,
    BoxComponent,
    TextComponent,
    ButtonComponent,
    URIAction,
    FlexSendMessage,
    IconComponent,
    SeparatorComponent,
)
from dotenv import load_dotenv
load_dotenv()
import os
from .google_maps_actions import GoogleMapsActions

NGROK_BASE_URL = os.getenv("NGROK_BASE_URL")

class LineActions:
    def __init__(self, line_bot_api: LineBotApi, gmaps_actions: GoogleMapsActions):
        """
        コンストラクタでLineBotApiのインスタンスを受け取る
        """
        self.line_bot_api = line_bot_api
        self.gmaps_actions = gmaps_actions 

    def search_restaurants(
        self, 
        reply_token: str, 
        query: str = None, 
        min_price: int = None,
        max_price: int = None
    ):
        """
        AIから呼び出される、レストランを検索・提案するための関数。
        """
        print(f"--- search_restaurants関数がAIによって呼び出されました ---")
        
        # ダミーデータではなく、GoogleMapsActionsを使って本物の情報を取得
        restaurant_list = self.gmaps_actions.search_and_format_restaurants(
            query=query,
            min_price=min_price,
            max_price=max_price,
            # target_datetime=datetime.now() # 日時指定がない場合は現在時刻で判定
        )
        
        if not restaurant_list:
            self.reply_with_text(reply_token, "すみません、条件に合うお店が見つかりませんでした。")
            return {"status": "error", "message": "No restaurants found."}

        # 取得した本物のデータでカルーセルを送信
        self.send_restaurant_carousel(reply_token, restaurant_list)
        
        return {"status": "success", "message": f"{len(restaurant_list)}件のレストランを提案しました。"}
    
    def final_restaurant(self, reply_token: str, query: str):
        """
        AIから呼び出される、レストランを決定する関数。
        """
        print(f"--- final_restaurant関数がAIによって呼び出されました ---")
        
        # ダミーデータではなく、GoogleMapsActionsを使って本物の情報を取得
        restaurant_list = self.gmaps_actions.search_and_format_restaurants(query)
        
        if not restaurant_list:
            self.reply_with_text(reply_token, "すみません、条件に合うお店が見つかりませんでした。")
            return {"status": "error", "message": "No restaurants found."}

        # 取得した本物のデータでカルーセルを送信
        self.send_final_restaurant(reply_token, restaurant_list[0])
        
        return {"status": "success", "message": "最終的なレストランを提案しました。"}


    def reply_with_text(self, reply_token: str, text: str):
        """シンプルなテキストメッセージを返信する"""
        try:
            self.line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
        except LineBotApiError as e:
            print(f"Error replying text message: {e}")

    def reply_with_quick_reply(self, reply_token: str, question: str, choices: list):
        """
        質問文と選択肢リストを受け取り、クイックリプライを送信する
        """
        items = []
        for choice in choices:
            button = QuickReplyButton(action=MessageAction(label=choice, text=choice))
            items.append(button)

        message = TextSendMessage(text=question, quick_reply=QuickReply(items=items))

        try:
            self.line_bot_api.reply_message(reply_token, message)
            return {"status": "success", "message": f"質問「{question}」を送信しました。"}
        except LineBotApiError as e:
            print(f"Error replying with quick reply: {e}")
            return {"status": "error", "message": str(e)}
        
    def send_join_greeting(self, reply_token: str):
        """グループ参加時の挨拶メッセージを送信する"""
        text = "こんにちは！飲み会調整ボットです🍻\n幹事さんは「調整スタート」と話しかけて、お店探しを始めてくださいね！"
        self.reply_with_text(reply_token, text)

    def start_individual_hearing(self, reply_token: str):
        """ダミーIDリストのメンバーに個別ヒアリングを開始する"""
        try:
            # 1. ダミーIDリストのメンバーに個別メッセージを一斉送信
            push_message = TextSendMessage(
                text="幹事さんからのお知らせです！\nお店探しの希望をこのトークで教えてくださいね！"
            )
            self.line_bot_api.multicast(self.dummy_member_ids, push_message)

            # 2. グループには成功したことを報告
            reply_text = f"{len(self.dummy_member_ids)}人のメンバーに、個別でヒアリングを開始しました！"

        except LineBotApiError as e:
            # エラーハンドリング
            print(f"LINE API Error: {e.status_code} {e.error.message}")
            reply_text = f"メッセージ送信でエラーが発生しました: {e.error.message}\n（メンバーがボットを友だち追加しているか確認してください）"

        # 3. グループへの応答メッセージを送信
        self.reply_with_text(reply_token, reply_text)

    def reply_during_hearing(self, reply_token: str, user_input: str):
        """個別ヒアリング中の応答"""
        text = f"希望をヒアリング中です...（「{user_input}」を受け付けました）"
        self.reply_with_text(reply_token, text)

    def send_final_restaurant(self, reply_token: str, restaurant: dict):
        """最終的に決定したレストランをFlex Messageで送信する"""
        bubble = self._create_final_restaurant_bubble(restaurant)
        messages_to_send = [
            TextSendMessage(text="お店が決定しました！"),
            FlexSendMessage(
                alt_text="お店が決定しました！",
                contents=bubble
            )
        ]
        self.line_bot_api.reply_message(reply_token, messages_to_send)

    def _create_final_restaurant_bubble(self, restaurant: dict) -> BubbleContainer:
        """最終的に提案するレストラン情報カード（バブル）を作成する"""
        return BubbleContainer(
            # hero: バブル上部のメイン画像エリア
            hero=ImageComponent(
                url=restaurant.get(
                    "image_url",
                    "https://placehold.co/600x400/EFEFEF/AAAAAA?text=No+Image",
                ),
                size="full",
                aspect_ratio="20:13",
                aspect_mode="cover",
                action=URIAction(uri=restaurant.get("url", "#"), label="ウェブサイト"),
            ),
            # body: 主要な情報を表示する中央のエリア
            body=BoxComponent(
                layout="vertical", # contents内の要素を縦に並べる
                spacing="md",
                background_color="#F9EDE7", # body全体の背景色
                contents=[
                    # 店名
                    TextComponent(
                        text=restaurant.get("name", "レストラン名なし"),
                        weight="bold", size="lg", wrap=True, color="#666565"
                    ),
                    # 評価（星と数字）
                    BoxComponent(
                        layout="horizontal", # 要素のベースライン（下端）を揃えて横に並べる
                        spacing="md", # 要素間のスペース
                        margin="md",
                        contents=[
                            TextComponent(text="★★★★☆", size="md", color="#FFBF47", flex=0, gravity="center"),
                            TextComponent(
                                text=str(restaurant.get("rating", 0.0)),
                                size="sm", color="#999999", flex=0, margin="md", gravity="center"
                            ),
                        ],
                    ),
                    # 住所（アイコン付き）
                    BoxComponent(
                        layout="baseline", spacing="md",
                        contents=[
                            IconComponent(
                                url=f"{NGROK_BASE_URL}/static/icons/place.png",
                                size="sm"
                            ),
                            TextComponent(
                                text=restaurant.get("address", "-"),
                                color="#929292", size="sm", flex=4, wrap=True,
                            ),
                        ],
                    ),
                    # 区切り線
                    SeparatorComponent(margin="lg", color="#D0D0D0"),
                    # 詳細情報（ジャンル、営業時間）
                    BoxComponent(
                        layout="vertical", margin="lg", spacing="sm",
                        contents=[
                            # ジャンルの行
                            BoxComponent(
                                layout="baseline", spacing="md",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/genre.png", size="sm"),
                                    TextComponent(text=restaurant.get("genre", "-"), color="#929292", size="sm", flex=4, wrap=True),
                                ],
                            ),
                            # 営業時間の行
                            BoxComponent(
                                layout="baseline", spacing="md",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/clock.png", size="sm"),
                                    TextComponent(text=restaurant.get("time", "9:00 ~ 22:00"), color="#929292", size="sm", flex=4, wrap=True),
                                ],
                            ),
                        ],
                    ),
                    # 区切り線
                    SeparatorComponent(margin="lg", color="#D0D0D0"),
                    # 口コミ件数
                    BoxComponent(
                        layout="baseline", spacing="md",
                        contents=[
                            IconComponent(url=f"{NGROK_BASE_URL}/static/icons/comment.png", size="sm"),
                            TextComponent(text=restaurant.get("userRatingCount", "200") + "件のレビュー", color="#929292", size="sm", flex=4, wrap=True),
                        ],
                    ),
                    # AIによる口コミ要約
                    BoxComponent(
                        layout="vertical", margin="lg", spacing="sm",
                        contents=[
                            # 良い口コミの要約
                            BoxComponent(
                                layout="baseline", spacing="sm",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/good.png", size="sm"),
                                    TextComponent(
                                        text=restaurant.get("reviewGoodSummary", "（AIによる良い口コミの要約）"),
                                        color="#929292", size="sm", flex=4, wrap=True,
                                    ),
                                ]
                            ),
                            # 悪い口コミの要約
                            BoxComponent(
                                layout="baseline", spacing="sm",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/bad.png", size="sm"),
                                    TextComponent(
                                        text=restaurant.get("reviewBadSummary", "（AIによる改善点や注意点の要約）"),
                                        color="#929292", size="sm", flex=4, wrap=True,
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            # footer: ボタンなどを配置する最下部のエリア
            footer=BoxComponent(
                layout="vertical",
                spacing="sm",
                background_color="#F9EDE7",
                contents=[
                    ButtonComponent(
                        style="primary",
                        height="sm",
                        action=URIAction(
                            label="予約する", uri=restaurant.get("url", "#")
                        ),
                        color="#CB2200" # 背景色
                    )
                ],
            ),
        )

    def send_restaurant_carousel(self, reply_token: str, restaurant_list: list):
        """レストラン候補をカルーセル形式のFlex Messageで送信する"""
        bubbles = [self._create_restaurant_bubble(r) for r in restaurant_list]
        carousel_container = CarouselContainer(contents=bubbles)
        messages_to_send = [
            TextSendMessage(text="こちらのレストランはいかがでしょうか？"),
            FlexSendMessage(
                alt_text="おすすめのレストランが見つかりました！",
                contents=carousel_container
            )
        ]
        self.line_bot_api.reply_message(reply_token, messages_to_send)

    def _create_restaurant_bubble(self, restaurant: dict) -> BubbleContainer:
        """カルーセル内の個々のレストラン情報カード（バブル）を作成する"""
        return BubbleContainer(
            # hero: バブル上部のメイン画像エリア
            hero=ImageComponent(
                url=restaurant.get(
                    "image_url",
                    "https://placehold.co/600x400/EFEFEF/AAAAAA?text=No+Image",
                ),
                size="full",
                aspect_ratio="20:13",
                aspect_mode="cover",
                action=URIAction(uri=restaurant.get("url", "#"), label="ウェブサイト"),
            ),
            # body: 主要な情報を表示する中央のエリア
            body=BoxComponent(
                layout="vertical", # contents内の要素を縦に並べる
                spacing="md",
                background_color="#F9EDE7", # body全体の背景色
                contents=[
                    # 店名
                    TextComponent(
                        text=restaurant.get("name", "レストラン名なし"),
                        weight="bold", size="lg", wrap=True, color="#666565"
                    ),
                    # 評価（星と数字）
                    BoxComponent(
                        layout="horizontal", # 要素のベースライン（下端）を揃えて横に並べる
                        spacing="md", # 要素間のスペース
                        margin="md",
                        contents=[
                            TextComponent(text="★★★★☆", size="md", color="#FFBF47", flex=0, gravity="center"),
                            TextComponent(
                                text=str(restaurant.get("rating", 0.0)),
                                size="sm", color="#999999", flex=0, margin="md", gravity="center"
                            ),
                        ],
                    ),
                    # 住所（アイコン付き）
                    BoxComponent(
                        layout="baseline", spacing="md",
                        contents=[
                            IconComponent(
                                url=f"{NGROK_BASE_URL}/static/icons/place.png",
                                size="sm"
                            ),
                            TextComponent(
                                text=restaurant.get("address", "-"),
                                color="#929292", size="sm", flex=4, wrap=True,
                            ),
                        ],
                    ),
                    # 区切り線
                    SeparatorComponent(margin="lg", color="#D0D0D0"),
                    # 詳細情報（ジャンル、営業時間）
                    BoxComponent(
                        layout="vertical", margin="lg", spacing="sm",
                        contents=[
                            # ジャンルの行
                            BoxComponent(
                                layout="baseline", spacing="md",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/genre.png", size="sm"),
                                    TextComponent(text=restaurant.get("genre", "-"), color="#929292", size="sm", flex=4, wrap=True),
                                ],
                            ),
                            # 営業時間の行
                            BoxComponent(
                                layout="baseline", spacing="md",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/clock.png", size="sm"),
                                    TextComponent(text=restaurant.get("time", "9:00 ~ 22:00"), color="#929292", size="sm", flex=4, wrap=True),
                                ],
                            ),
                        ],
                    ),
                    # 区切り線
                    SeparatorComponent(margin="lg", color="#D0D0D0"),
                    # 口コミ件数
                    BoxComponent(
                        layout="baseline", spacing="md",
                        contents=[
                            IconComponent(url=f"{NGROK_BASE_URL}/static/icons/comment.png", size="sm"),
                            TextComponent(text=restaurant.get("userRatingCount", "200") + "件のレビュー", color="#929292", size="sm", flex=4, wrap=True),
                        ],
                    ),
                    # AIによる口コミ要約
                    BoxComponent(
                        layout="vertical", margin="lg", spacing="sm",
                        contents=[
                            # 良い口コミの要約
                            BoxComponent(
                                layout="baseline", spacing="sm",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/good.png", size="sm"),
                                    TextComponent(
                                        text=restaurant.get("reviewGoodSummary", "（AIによる良い口コミの要約）"),
                                        color="#929292", size="sm", flex=4, wrap=True,
                                    ),
                                ]
                            ),
                            # 悪い口コミの要約
                            BoxComponent(
                                layout="baseline", spacing="sm",
                                contents=[
                                    IconComponent(url=f"{NGROK_BASE_URL}/static/icons/bad.png", size="sm"),
                                    TextComponent(
                                        text=restaurant.get("reviewBadSummary", "（AIによる改善点や注意点の要約）"),
                                        color="#929292", size="sm", flex=4, wrap=True,
                                    ),
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            # footer: ボタンなどを配置する最下部のエリア
            footer=BoxComponent(
                layout="vertical",
                spacing="sm",
                background_color="#F9EDE7",
                contents=[
                    ButtonComponent(
                        style="primary",
                        height="sm",
                        action=URIAction(
                            label="詳しく見る", uri=restaurant.get("url", "#")
                        ),
                        color="#CB2200" # 背景色
                    )
                ],
            ),
        )
