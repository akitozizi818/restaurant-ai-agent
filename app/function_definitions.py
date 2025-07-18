# app/function_definitions.py
from vertexai.generative_models import FunctionDeclaration

# AI (Gemini) に「こんな関数が使えますよ」と教えるための定義リスト
function_declarations = [
    FunctionDeclaration(
        name="search_restaurants",
        description="個別ヒアリング中にユーザーの好みを探るために使用します。ユーザーが指定した地名や料理のジャンル、その他の特徴に基づいて、飲食店を検索し、結果をフォーマットして返します。",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "地名、料理のジャンル、その他の特徴を含む検索キーワード。例: '新宿 和食 個室'"
                },
                "min_price": {
                    "type": "number",
                    "description": "価格帯の下限（0:無料, 1:安い, 2:普通, 3:高い, 4:とても高い）"
                },
                "max_price": {
                    "type": "number",
                    "description": "価格帯の上限（0:無料, 1:安い, 2:普通, 3:高い, 4:とても高い）"
                }
            },
            "required": ["query"]
        }
    ),
    FunctionDeclaration(
        name="final_restaurant",
        description="グループlineで最終的なお店を送る場合に使用します。ユーザーが指定した地名や料理のジャンル、その他の特徴に基づいて、飲食店を検索し、結果をフォーマットして返します。",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "地名、料理のジャンル、その他の特徴を含む検索キーワード。例: '新宿 和食 個室'"
                },
                "min_price": {
                    "type": "number",
                    "description": "価格帯の下限（0:無料, 1:安い, 2:普通, 3:高い, 4:とても高い）"
                },
                "max_price": {
                    "type": "number",
                    "description": "価格帯の上限（0:無料, 1:安い, 2:普通, 3:高い, 4:とても高い）"
                }
            },
            "required": ["query"]
        }
    ),
    FunctionDeclaration(
        name="reply_with_quick_reply",
        description="ユーザーの希望が曖昧な場合や、確認したいことがある場合に、質問と選択肢を提示して回答を促すために使用します。",
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "ユーザーに投げかける質問文。例: 'ご希望の予算はどのくらいですか？'"
                },
                "choices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "ユーザーに提示する選択肢のリスト。例: ['3000円', '5000円', '8000円']"
                }
            },
            "required": ["question", "choices"]
        }
    ),
    FunctionDeclaration(
        name="start_individual_hearing",
        description="グループでの共通ヒアリングが完了したと判断した時に呼び出します。個別ヒアリングの案内と、「お店を決める」ボタンをグループに投稿します。",
        parameters={"type": "object", "properties": {}}
    ),
    # FunctionDeclaration(
    #     name="send_start_prompt",
    #     description="グループlineでのお店決めが終了した後や、ユーザーがお店決めをやり直したい場合にお店決めを新たに開始するために使用します。",
    #     parameters={
    #         "type": "object",
    #         "properties": {},
    #         "required": []
    #     }
    # )
]
