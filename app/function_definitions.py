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
    )
]
