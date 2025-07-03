import os
import httpx
import google.generativeai as genai
import json
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any, Tuple
import asyncio

class GooglePlacesGeminiClient:
    """
    Google Places APIとGemini APIを連携させ、場所の検索、詳細情報の取得、
    口コミの要約、ジャンルの特定、画像取得を行うクライアント。
    """

    def __init__(self):
        """
        クライアントを初期化し、APIキーとGeminiモデルを設定する。
        """
        load_dotenv()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY 環境変数が設定されていません。")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY 環境変数が設定されていません。")

        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            raise RuntimeError(f"Geminiの初期化に失敗しました: {e}")

        print("GooglePlacesGeminiClient (本番用) 初期化済み。")

    async def _generate_content_with_gemini(self, reviews: List[Dict[str, Any]], base_prompt: str) -> str:
        """Gemini APIを呼び出し、与えられたプロンプトに基づいてコンテンツを生成する内部メソッド。"""
        if not self.gemini_model or not reviews:
            return "要約対象のレビューがありません。"

        # review_texts = [
        #     r.get("text", "") for r in reviews if r.get("text")
        # ]
        review_texts = [
            # .get("text", {})で安全に辞書を取得し、さらにその中の.get("text", "")で文字列を取得
            r.get("text", {}).get("text", "") for r in reviews if r.get("text", {}).get("text", "")
        ]
        if not review_texts:
            return "要約対象のレビューテキストがありません。"
            
        formatted_reviews = "\n- ".join(review_texts)
        prompt = f"""{base_prompt}

---
口コミ一覧:
- {formatted_reviews}
---

要約:
"""
        try:
            response = await self.gemini_model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[GooglePlacesGeminiClient] Gemini API呼び出し中にエラー: {e}")
            return "エラーが発生しました。"

    async def summarize_good_reviews(self, reviews: List[Dict[str, Any]]) -> str:
        """口コミリストから良い評価を要約する。"""
        prompt = "以下のレストランに関する良い口コミを要約し150字程度で簡潔に要約してください。なければ、「特にありません」と回答してください。"
        return await self._generate_content_with_gemini(reviews, prompt)

    async def summarize_bad_reviews(self, reviews: List[Dict[str, Any]]) -> str:
        """口コミリストから悪い評価を要約する。"""
        prompt = "以下のレストランに関する悪い口コミを要約し150字程度で簡潔に要約してください。なければ、「特にありません」と回答してください。"
        return await self._generate_content_with_gemini(reviews, prompt)

    async def get_genre_from_reviews(self, reviews: List[Dict[str, Any]]) -> str:
        """口コミリストから飲食店のジャンルを推定する。"""
        prompt = "以下のレストランに関する口コミから最も的確なジャンルを一つだけ、簡潔に回答してください。例: 居酒屋, イタリアン, ラーメン"
        return await self._generate_content_with_gemini(reviews, prompt)

    async def search_places_and_get_details(
        self,
        keyword: str,
        lat: float,
        lng: float,
        radius: int = 3000,
        price_levels: Optional[List[str]] = None,
        min_rating: float = 0.0,
        max_result_count: int = 3,
        language: str = "ja"
    ) -> Dict[str, Any]:
        """
        指定された条件で場所を検索し、Geminiによる要約付きの詳細情報を返す。
        """
        search_url = "https://places.googleapis.com/v1/places:searchText"
        search_headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.google_api_key,
            "X-Goog-FieldMask": "places.id,places.displayName",
        }

        query_body = {
            "textQuery": keyword,
            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius}},
            "languageCode": language,
            "minRating": min_rating,
            "maxResultCount": max_result_count,
        }
        if price_levels:
            query_body["priceLevels"] = price_levels

        async with httpx.AsyncClient() as client:
            try:
                search_res = await client.post(search_url, headers=search_headers, json=query_body)
                search_res.raise_for_status()
                places = search_res.json().get("places", [])
                print(f"[GooglePlacesGeminiClient] 飲食店検索結果 ({len(places)}件)")

            except httpx.HTTPStatusError as e:
                print(f"[GooglePlacesGeminiClient] 飲食店検索エラー: {e.response.text}")
                return {"results": []}
            except Exception as e:
                print(f"[GooglePlacesGeminiClient] 飲食店検索中に予期せぬエラー: {e}")
                return {"results": []}

            results = []
            for place in places:
                place_id = place.get("id")
                if not place_id:
                    continue

                try:
                    detail_url = f"https://places.googleapis.com/v1/places/{place_id}"
                    detail_headers = {
                        "X-Goog-Api-Key": self.google_api_key,
                        "X-Goog-FieldMask": "displayName,formattedAddress,rating,userRatingCount,reviews,photos,currentOpeningHours.weekdayDescriptions,websiteUri"
                    }
                    detail_params = {"languageCode": language}
                    detail_res = await client.get(detail_url, headers=detail_headers, params=detail_params)
                    detail_res.raise_for_status()
                    detail = detail_res.json()

                    reviews_list = detail.get("reviews", [])
                    review_good_summary = await self.summarize_good_reviews(reviews_list)
                    review_bad_summary = await self.summarize_bad_reviews(reviews_list)
                    genre = await self.get_genre_from_reviews(reviews_list)
                    
                    photo_resource_names = [p.get("name") for p in detail.get("photos", []) if p.get("name")]

                    results.append({
                        "place_id": place_id,
                        "name": detail.get("displayName", {}).get("text", ""),
                        "address": detail.get("formattedAddress", ""),
                        "rating": detail.get("rating"),
                        "userRatingCount": detail.get("userRatingCount"),
                        "website": detail.get("websiteUri", "Webサイト情報なし"),
                        "openingHours": detail.get("currentOpeningHours", {}).get("weekdayDescriptions", []),
                        "reviewGoodSummary": review_good_summary,
                        "reviewBadSummary": review_bad_summary,
                        "genre": genre,
                        "photo_resource_name": photo_resource_names[0] if photo_resource_names else None,
                    })
                    print(f"[GooglePlacesGeminiClient] 店舗詳細取得 ({place_id}): {detail.get('displayName', {}).get('text', '')}")

                except httpx.HTTPStatusError as e:
                    print(f"[GooglePlacesGeminiClient] 店舗詳細取得エラー ({place_id}): {e.response.text}")
                    continue
                except Exception as e:
                    print(f"[GooglePlacesGeminiClient] 店舗詳細取得中に予期せぬエラー ({place_id}): {e}")
                    continue

            return {"results": results}

#     async def get_photo(self, photo_resource_name: str, max_width_px: int = 400) -> Optional[Tuple[bytes, str]]:
#         """
#         Google Placesの写真リソース名から画像データを取得する。
        
#         Args:
#             photo_resource_name (str): 写真のリソース名 (例: 'places/ChI.../photos/A...').
#             max_width_px (int): 取得する画像の最大幅（ピクセル）。
        
#         Returns:
#             Optional[Tuple[bytes, str]]: (画像コンテンツ, コンテンツタイプ) のタプル。失敗した場合はNone。
#         """
#         if not photo_resource_name:
#             return None
            
#         photo_url = f"https://places.googleapis.com/v1/{photo_resource_name}/media?maxWidthPx={max_width_px}&key={self.google_api_key}"

#         async with httpx.AsyncClient(follow_redirects=True) as client:
#             try:
#                 response = await client.get(photo_url, timeout=10)
#                 response.raise_for_status()
#                 image_content = await response.aread()
#                 content_type = response.headers.get("Content-Type", "application/octet-stream")
#                 print(f"[GooglePlacesGeminiClient] 画像取得成功 ({photo_resource_name})")
#                 return (image_content, content_type)
#             except httpx.HTTPStatusError as e:
#                 print(f"[GooglePlacesGeminiClient] 画像取得エラー ({photo_resource_name}): Status {e.response.status_code}")
#                 return None
#             except Exception as e:
#                 print(f"[GooglePlacesGeminiClient] 画像取得中に予期せぬエラー ({photo_resource_name}): {e}")
#                 return None
            

# async def main():
#     """
#     クライアントを初期化し、パラメータを指定して飲食店を検索する。
#     """
#     try:
#         # クライアントを初期化
#         client = GooglePlacesGeminiClient()

#         # 検索条件を定義
#         search_params = {
#             "keyword": "ランチ",
#             "lat": 35.6895,  # 東京駅の緯度
#             "lng": 139.6917, # 東京駅の経度
#             "radius": 1500, # 検索半径
#             "max_result_count": 1, # 最大取得件数
#             "price_levels": ["PRICE_LEVEL_INEXPENSIVE"],  # 価格レベル「安い」「お手頃」のみを対象
#             "min_rating": 4.0,       # 評価が4.0以上の場所のみを対象
#         }

#         # メソッドを呼び出し
#         results = await client.search_places_and_get_details(**search_params)

#         # 結果を整形して出力
#         print(json.dumps(results, indent=2, ensure_ascii=False))

#     except (ValueError, RuntimeError) as e:
#         print(f"エラーが発生しました: {e}")


# if __name__ == "__main__":
#     # .envファイルから環境変数を読み込むために
#     # from dotenv import load_dotenv
#     # load_dotenv()
    
#     # 非同期関数を実行
#     asyncio.run(main())