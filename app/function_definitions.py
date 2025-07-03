from vertexai.generative_models import FunctionDeclaration

## AI (Gemini) に「こんな関数が使えますよ」と教えるための定義リスト
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
    )
]
