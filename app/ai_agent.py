# app/ai_agent.py
from vertexai.generative_models import GenerativeModel, Tool
from .function_definitions import function_declarations
from .line_actions import LineActions # ★★★ LineActionsをインポート ★★★

class AIAgent:
    def __init__(self, gemini_model: GenerativeModel, line_actions: LineActions):
        self.model = gemini_model
        self.line_actions = line_actions
        
        if self.model:
            self.chat = self.model.start_chat()
            print("AIAgent chat session started.")
        else:
            self.chat = None
            print("AIAgent initialized without a model.")

    def process_message(self, event):
        """
        ユーザーのメッセージを処理し、AIの判断に基づいて応答または関数呼び出しを行う。
        """
        user_message = event.message.text
        reply_token = event.reply_token

        if not self.chat:
            self.line_actions.reply_with_text(reply_token, "AIモデルが準備できていません。")
            return

        try:
            response = self.chat.send_message(user_message)
            
            if response.candidates and response.candidates[0].function_calls:
                function_call = response.candidates[0].function_calls[0]
                function_name = function_call.name
                args = {key: value for key, value in function_call.args.items()}
                
                print(f"AIが関数呼び出しを判断: {function_name}({args})")

                # # ★★★ ここからが今回の修正の核心 ★★★
                # if function_name == "search_restaurants":
                #     # AIが判断した引数(query)と、イベントのreply_tokenを使って、
                #     # LineActionsのメソッドを呼び出す
                #     self.line_actions.search_restaurants(
                #         reply_token=reply_token,
                #         query=args.get("query", "")
                #     )
                # ★★★ ここからが今回の修正の核心 ★★★
                # 実行する関数に、reply_tokenも引数として渡す
                args_with_reply_token = {"reply_token": reply_token, **args}

                # 関数名に応じて、LineActionsの対応するメソッドを実行
                if hasattr(self.line_actions, function_name):
                    func = getattr(self.line_actions, function_name)
                    # **args_with_reply_tokenで辞書を展開して引数として渡す
                    func(**args_with_reply_token)
                else:
                    self.line_actions.reply_with_text(reply_token, "AIが不明な関数を呼び出そうとしました。")
            
            else:
                # 関数呼び出しがない場合は、通常のテキスト応答
                self.line_actions.reply_with_text(reply_token, response.text.strip())

        except Exception as e:
            print(f"AIとの対話中にエラーが発生しました: {e}")
            self.line_actions.reply_with_text(reply_token, "すみません、AIが応答できませんでした。")
