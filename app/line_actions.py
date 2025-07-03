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

NGROK_BASE_URL = "" 

class LineActions:
    def __init__(self, line_bot_api: LineBotApi):
        """
        コンストラクタでLineBotApiのインスタンスを受け取る
        """
        self.line_bot_api = line_bot_api

        # ★★★ ここにテスト参加者のユーザーIDを手動で設定 ★★★
        self.dummy_member_ids = [
            "",  # ダミーのユーザーID1
            # "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx2", # 友人AのユーザーID
            # "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx3", # 友人BのユーザーID
        ]

        # ダミーのレストランデータ
        self.dummy_restaurants = [
            # {
            #     "name": "ル・モンド新宿店",
            #     "address": "日本、〒160-0023 東京都新宿区西新宿１丁目１６−１１",
            #     "rating": 4.1,
            #     "userRatingCount": 1548,
            #     "website": "https://www.facebook.com/lemonde.shinjuku/",
            #     "openingHours": [
            #       "月曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "火曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "水曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "木曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "金曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "土曜日: 11時00分～14時45分, 17時00分～21時30分",
            #       "日曜日: 定休日"
            #     ],
            #     "reviewGoodSummary": "新宿ヨドバシ近くにある、カウンター席のみの小さなステーキ店。サーロイン、リブロースステーキが1700円台とコスパが良いと評判で、ランチ時は特に人気。肉質は柔らかくはないものの、旨味があり、噛み応えのある本格的なステーキが楽しめる。  ただし、店内は狭く、待ち時間が発生する場合もある。現金払いのみ。  全体的に、肉の質と価格のバランスが良く、リピーターも多い。",
            #     "reviewBadSummary": "店内は狭く、カウンター席のみで客席数も少ないため、待ち時間が発生する可能性がある。また、現金払いのみの対応となっている。肉質は口コミによって評価が分かれ、「噛みごたえがある」「柔らかい」など、一定ではない。接客は概ね良好だが、挨拶が丁寧でないという指摘もある。コスパは良いと評価する声もある一方で、「いきなり！ステーキ」の方が優れているとの意見もある。",
            #     "genre": "ステーキ",
            #     "photo_resource_name": "places/ChIJaU5nFNGMGGARy31fwXoQb3s/photos/ATKogpe77KZgFB3Qr6xZaiHDjNAHeohdBDPZ_GBncibWFeC-5IvXiB4_CfevSg1_CB7OcfLT6Y1QVBA4YdYdoh15o65m0yX_odR5-mfosnyVtsRD_0obPvZtcCj-NR8ESoWlidKX67rv250hk74pq1yw-u5q4NkHsalajKJBmVSyF8cKEBwB4lMVE0Ag-ab24UqMA9NbLGcQU-JWoZzXoGZoe2oTaN7hUmGdLaKeZdcKvnvAFkHMBhzyBvIMtbE8f2oWpoZIHqoGZEPWGFsZ_TkUZdXUJVq9bap50mYEwsgFGoyScL-zxsjaRepooFU59mSkD4f7IegPhdUY7vlwr3R2HnXukmhAvr4-HRNY7r-FrYcsodzePB3l7hfU4K2K1g0IGLGmmRDkApAXuXI-4mbk0Z53P3CvGjW6EZ4I651RCANc1Q",
            # },
            # {
            #     "name": "ル・モンド新宿店",
            #     "address": "日本、〒160-0023 東京都新宿区西新宿１丁目１６−１１",
            #     "rating": 4.1,
            #     "userRatingCount": 1548,
            #     "website": "https://www.facebook.com/lemonde.shinjuku/",
            #     "openingHours": [
            #       "月曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "火曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "水曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "木曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "金曜日: 11時00分～15時00分, 17時00分～21時30分",
            #       "土曜日: 11時00分～14時45分, 17時00分～21時30分",
            #       "日曜日: 定休日"
            #     ],
            #     "reviewGoodSummary": "新宿ヨドバシ近くにある、カウンター席のみの小さなステーキ店。サーロイン、リブロースステーキが1700円台とコスパが良いと評判で、ランチ時は特に人気。肉質は柔らかくはないものの、旨味があり、噛み応えのある本格的なステーキが楽しめる。  ただし、店内は狭く、待ち時間が発生する場合もある。現金払いのみ。  全体的に、肉の質と価格のバランスが良く、リピーターも多い。",
            #     "reviewBadSummary": "店内は狭く、カウンター席のみで客席数も少ないため、待ち時間が発生する可能性がある。また、現金払いのみの対応となっている。肉質は口コミによって評価が分かれ、「噛みごたえがある」「柔らかい」など、一定ではない。接客は概ね良好だが、挨拶が丁寧でないという指摘もある。コスパは良いと評価する声もある一方で、「いきなり！ステーキ」の方が優れているとの意見もある。",
            #     "genre": "ステーキ",
            #     "photo_resource_name": "places/ChIJaU5nFNGMGGARy31fwXoQb3s/photos/ATKogpe77KZgFB3Qr6xZaiHDjNAHeohdBDPZ_GBncibWFeC-5IvXiB4_CfevSg1_CB7OcfLT6Y1QVBA4YdYdoh15o65m0yX_odR5-mfosnyVtsRD_0obPvZtcCj-NR8ESoWlidKX67rv250hk74pq1yw-u5q4NkHsalajKJBmVSyF8cKEBwB4lMVE0Ag-ab24UqMA9NbLGcQU-JWoZzXoGZoe2oTaN7hUmGdLaKeZdcKvnvAFkHMBhzyBvIMtbE8f2oWpoZIHqoGZEPWGFsZ_TkUZdXUJVq9bap50mYEwsgFGoyScL-zxsjaRepooFU59mSkD4f7IegPhdUY7vlwr3R2HnXukmhAvr4-HRNY7r-FrYcsodzePB3l7hfU4K2K1g0IGLGmmRDkApAXuXI-4mbk0Z53P3CvGjW6EZ4I651RCANc1Q",
            # },
            {
                "name": "絶品和食 B",
                "image_url": "https://placehold.co/600x400/C2D8B2/FFFFFF?text=Washoku",
                "rating": 4.2,
                "address": "東京都文京区本郷4-5-6",
                "genre": "和食・割烹",
                "url": "https://example.com/b",
            },
        ]

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
            # 選択肢のテキストをそのまま、ボタンのラベルと押した時のテキストに設定
            button = QuickReplyButton(action=MessageAction(label=choice, text=choice))
            items.append(button)

        message = TextSendMessage(text=question, quick_reply=QuickReply(items=items))

        try:
            self.line_bot_api.reply_message(reply_token, message)
        except LineBotApiError as e:
            print(f"Error replying with quick reply: {e}")

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

    def send_restaurant_carousel(self, reply_token: str):
        """レストラン候補をカルーセル形式のFlex Messageで送信する"""
        bubbles = []
        for restaurant in self.dummy_restaurants:
            bubble = self._create_restaurant_bubble(restaurant)
            bubbles.append(bubble)

        carousel_container = CarouselContainer(contents=bubbles)

        # 提案メッセージとFlex Messageをリストで渡す
        messages_to_send = [
            TextSendMessage(text="以下のレストランから選んでください！"),
            FlexSendMessage(
                alt_text="おすすめのレストランが見つかりました！",
                contents=carousel_container,
            ),
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
