from flask import Flask, render_template, request, jsonify
import pandas as pd
import warnings

warnings.simplefilter(action="ignore", category=UserWarning)

app = Flask(__name__)

# رابط Google Sheet
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1pC1irvJ3NJCcIHIyk8I6Tx-XD6eCSc4mnAXa2O-zmu4/edit?usp=sharing"

# الكلمات المفتاحية للشيتات المطلوبة
TARGET_KEYWORDS = ["مهام", "اجتماع", "المهام", "الاجتماعات"]


def get_sheet_data():
    export_url = GOOGLE_SHEET_URL.split("/edit")[0] + "/export?format=xlsx"

    try:
        all_sheets = pd.read_excel(export_url, sheet_name=None)
        parsed_data = {}

        for sheet_name, df in all_sheets.items():

            # البحث عن الشيتات التي تحتوي أسماؤها على الكلمات المطلوبة
            if any(keyword in sheet_name for keyword in TARGET_KEYWORDS):

                df = df.fillna("")
                df_str = df.astype(str)

                parsed_data[sheet_name] = {
                    "headers": df_str.columns.tolist(),
                    "rows": df_str.values.tolist()
                }

        # إذا لم يجد الشيتات المطلوبة، يعرض أول شيتين
        if not parsed_data:

            for sheet_name in list(all_sheets.keys())[:2]:

                df = all_sheets[sheet_name].fillna("")
                df = df.astype(str)

                parsed_data[sheet_name] = {
                    "headers": df.columns.tolist(),
                    "rows": df.values.tolist()
                }

        return parsed_data

    except Exception as e:
        print("Error fetching sheet:", e)
        return {}


@app.route("/")
def index():

    data = get_sheet_data()
    sheet_names = list(data.keys())

    return render_template(
        "index.html",
        data=data,
        sheet_names=sheet_names
    )


@app.route("/api/chat", methods=["POST"])
def chat_api():

    user_query = request.json.get("query", "").strip()

    if not user_query:

        return jsonify({
            "reply": "يرجى كتابة نص للبحث."
        })

    data = get_sheet_data()
    results = []

    for sheet_name, sheet_data in data.items():

        for row in sheet_data["rows"]:

            row_str = " ".join(row)

            if user_query.lower() in row_str.lower():

                clean_row = [
                    value for value in row
                    if value != ""
                ]

                results.append(
                    f"📄 [{sheet_name}]: "
                    + " | ".join(clean_row)
                )

    if results:

        reply = (
            "إليك نتائج البحث في جدول المهام والاجتماعات:\n\n"
            + "\n\n".join(results[:10])
        )

    else:

        reply = (
            f"لم أجد أي نتائج مطابقة لـ '{user_query}'."
        )

    return jsonify({
        "reply": reply
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)