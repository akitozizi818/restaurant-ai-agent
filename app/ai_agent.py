# app/ai_agent.py
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from linebot.models import MessageEvent

# 内部モジュールをインポート
from .line_actions import LineActions
from .function_definitions import function_declarations

class AIAgent:
    def __init__(self, gemini_model: GenerativeModel, line_actions: LineActions):
        """
        コンストラクタで、初期化済みのVertex AIモデルとLineActionsを受け取ります。
        """
        self.model = gemini_model
        self.line_actions = line_actions
        # 会話履歴をユーザー/グループごとに管理するための辞書
        # この辞書が、AIの「記憶」の役割を果たします。
        self.chat_sessions = {}

    def _get_or_create_chat_session(self, session_id: str):
        """セッションIDに基づいてチャットセッションを取得または新規作成"""
        if session_id not in self.chat_sessions:
            # AIの行動指針となる、詳細な指示書（システムプロンプト）
            system_prompt = """
あなたは、飲み会の飲食店選びをサポートする、非常に優秀で配慮の天才なファシリテーターAIです。
あなたの目的は、参加者全員が納得する最適なレストランを1つ見つけることです。

【あなたの思考プロセスと行動ルール】
1.  **調整開始:** ユーザーが「調整スタート」ボタンを押したら、`start_group_hearing`関数を呼び出し、グループでのヒアリングを開始します。
2.  **グループヒアリング:** 「エリア」「食事の種類（朝食・ディナーなど）」「日時」など、全員に共通の質問を順番に投げかけてください。
3.  **個別ヒアリングへの移行:** グループでのヒアリングが終わったら、`start_individual_hearing`を呼び出し、個別ヒアリングの案内と「お店を決める」ボタンをグループに投稿してください。
4.  **個別ヒアリングと提案:** 1対1チャットでは、ユーザーの希望を聞き、その都度`propose_restaurant_in_individual_chat`を呼び出して、全員の最新の希望を反映したお店を数件提案してください。
5.  **最終決定:** 幹事が「お店を決める」ボタンを押したという情報を受け取ったら、`make_final_decision`を呼び出し、全ての情報を統合分析して、最終的な1軒をグループに報告してください。

【ルール】
1. **積極的な質問と`reply_with_quick_reply`の正しい使い方:**
    ユーザーの要望が曖昧な場合、あなたは**必ず`reply_with_quick_reply`関数を使って**、希望を具体化してください。
    その際、`choices`引数には、**必ずユーザーが選びやすい具体的な選択肢を3つか4つ、リスト形式で指定してください。**
    【良い例】: `reply_with_quick_reply(question="ご希望のジャンルは？", choices=["和食", "イタリアン", "中華"])`
    【悪い例】: `reply_with_quick_reply(question="ご希望は？", choices=[])` ← choicesが空なのはダメ

2.  **検索と提案:**
    必須情報が揃ったら、`search_restaurants`関数を呼び出し、お店を提案してください。ただし、この関数はグループlineではけして呼び出さないでください。
    個別チャットでのみ使用し、提案する際は、全員の希望を考慮した検索キーワードを生成してください。

3.  **スタート:**
    グループlineでの飲み会調整が終了した後や、ユーザーがお店決めをやり直したい場合は、`send_start_prompt`関数を呼び出して、グループlineに「スタート」ボタン付きのメッセージを送信してください。ただし、そうではない場合は絶対にやりなおしてはいけません。この関数を実行する前は一度確認をはさんでください。
あなたの役割は、焦ってお店を提案することではありません。丁寧なヒアリングを通じて、ユーザーの要望を完璧に理解し、無駄のない最適な提案を行うことです。
"""
            # ツールを認識済みのモデルから、新しいチャットセッションを開始
            self.chat_sessions[session_id] = self.model.start_chat()
            # 最初にシステムプロンプトを会話のコンテキストに含める
            self.chat_sessions[session_id].send_message(system_prompt)
            print(f"New chat session created for {session_id} with a detailed system prompt.")

        return self.chat_sessions[session_id]

    def process_individual_message(self, event: MessageEvent, session_data: dict):
        """
        個別ヒアリング中のメッセージを処理する。
        常に全員の希望を考慮して、次のアクションを判断する。
        """
        user_message = event.message.text
        reply_token = event.reply_token
        session_id = event.source.user_id # 1対1チャットなので、session_idはuser_id

        if not self.model:
            self.line_actions.reply_with_text(reply_token, "AIモデルが準備できていません。")
            return

        chat = self._get_or_create_chat_session(session_id)

        # AIに渡すプロンプトを、現在の全希望を含めて作成
        prompt = f"""
        現在、以下の希望が全員から集まっています。
        {session_data['preferences']}

        上記を踏まえた上で、以下の新しいメッセージに対して、最適なアクション（お店の提案、追加の質問、ただの返事など）を判断し、必要な関数を呼び出してください。
        お店を提案する際は、必ず全員の希望を考慮した検索キーワードを生成してください。
        以下はグループlineで決めた条件なので、個別チャットではこれらの情報を使ってください。
        {session_data['preferences']['common']}

        新しいメッセージ: "{user_message}"
        """
        
        self._send_prompt_and_execute_action(prompt, chat, reply_token)

    def process_group_message(self, event: MessageEvent, session_data: dict):
        """
        グループLINEのメッセージを処理する。
        """
        user_message = event.message.text
        reply_token = event.reply_token
        group_id = event.source.group_id
        session_id = event.source.user_id

        if not self.model:
            self.line_actions.reply_with_text(reply_token, "AIモデルが準備できていません。")
            return

        chat = self._get_or_create_chat_session(session_id)

        # AIに渡すプロンプトを、現在の全希望を含めて作成
        prompt = f"""
        現在、以下の希望が全員から集まっています。
        {session_data['preferences']}

        上記を踏まえた上で、以下の新しいメッセージに対して、最適なアクション（追加の質問、ただの返事、お店の決定など）を判断し、必要な関数を呼び出してください。質問をする際には、グループメンバー全員が答えやすい決まっていることのみにしてください。（日時、エリア、朝食か夕食かなど）決して意見のわかれる予算やジャンルなどの質問はしないでください。

        ユーザーID: "{session_id}"
        新しいメッセージ: "{user_message}"
        """
        
        self._send_prompt_and_execute_action(prompt, chat, reply_token)

    def _send_prompt_and_execute_action(self, prompt: str, chat, reply_token: str):
        """プロンプトをAIに送信し、Function Callingを実行する共通処理"""
        try:
            response = chat.send_message(prompt)
            
            if response.candidates and response.candidates[0].function_calls:
                function_call = response.candidates[0].function_calls[0]
                function_name = function_call.name
                args = {key: value for key, value in function_call.args.items()}
                
                print(f"AIが関数呼び出しを判断: {function_name}({args})")

                # 実行する関数に、reply_tokenも引数として渡す
                args_with_reply_token = {"reply_token": reply_token, **args}

                if hasattr(self.line_actions, function_name):
                    func = getattr(self.line_actions, function_name)
                    func(**args_with_reply_token)
                else:
                    self.line_actions.reply_with_text(reply_token, "AIが不明な関数を呼び出そうとしました。")
            
            else:
                # 関数呼び出しがない場合は、通常のテキスト応答
                self.line_actions.reply_with_text(reply_token, response.text.strip())

        except Exception as e:
            print(f"AIとの対話中にエラーが発生しました: {e}")
            self.line_actions.reply_with_text(reply_token, "すみません、AIが応答できませんでした。")
