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
                },
                "location": {
                    "type": "object",
                    "description": "検索の中心となる地点の緯度と経度。",
                    "properties": {
                        "lat": {
                            "type": "number",
                            "description": "緯度 (例: 35.7056)"
                        },
                        "lon": {
                            "type": "number",
                            "description": "経度 (例: 139.7519)"
                        }
                    }
                },
                "radius": {
                    "type": "number",
                    "description": "指定した地点からの検索半径（メートル単位）。locationと合わせて使用します。"
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
            "required": []
        }
    )
]
