# app/function_definitions.py
from vertexai.generative_models import FunctionDeclaration

# AI (Gemini) に「こんな関数が使えますよ」と教えるための定義リスト
function_declarations = [
    FunctionDeclaration(
        name="search_restaurants",
        description="ユーザーがレストランや飲食店を探してほしいと依頼した時に、そのお店を検索するために使用します。",
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
    # ★★★ ここに新しい関数の定義を追加 ★★★
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
