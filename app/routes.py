from flask import Blueprint, jsonify, render_template, request, url_for
from .database import db
from .models import Participant, Answer
import pytz
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

main = Blueprint("main", __name__)


@main.route("/", methods=["GET"])
def home():
    # 참여자 정보 입력 페이지를 렌더링합니다.
    return render_template("index.html")


@main.route("/participants", methods=["POST"])
def add_participant():
    data = request.get_json()
    new_participant = Participant(
        name=data["name"],
        age=data["age"],
        gender=data["gender"],
        created_at=datetime.now(pytz.timezone("Asia/Seoul")),
    )
    db.session.add(new_participant)
    db.session.commit()

    # 리다이렉션 URL과 참여자 ID를 JSON 응답으로 전송
    return jsonify({"redirect": "/question", "participant_id": new_participant.id})


@main.route("/question", methods=["get"])
def question():
    return render_template("question.html")


@main.route("/submit", methods=["POST"])
def submit():
    participant_id = request.cookies.get("participant_id")
    if not participant_id:
        return jsonify({"error": "Participant ID not found"}), 400

    data = request.json
    answers = data.get("answers", [])

    for answer in answers:
        question_id = answer.get("question_id")
        chosen_answer = answer.get("chosen_answer")

        # 새 Answer 인스턴스 생성
        new_answer_entry = Answer(
            question_id=question_id,
            chosen_answer=chosen_answer,
            participant_id=participant_id,  # 참여자 ID를 Answer 모델과 연결
        )
        db.session.add(new_answer_entry)

    db.session.commit()
    return jsonify({"message": "Answers submitted successfully."})


@main.route("/results")
def show_results():
    seoul_timezone = pytz.timezone("Asia/Seoul")
    today = datetime.now(seoul_timezone).date()
    start_date = today - timedelta(days=6)
    end_date = today + timedelta(days=1)

    # 지정된 날짜 범위 내 모든 날짜 리스트 생성
    all_dates = pd.date_range(start=start_date, end=end_date).date

    # 실제 참가자 데이터 조회
    participants = Participant.query.filter(
        Participant.created_at.between(start_date, end_date)
    ).all()
    participants_data = [{
        "created_at": participant.created_at.astimezone(seoul_timezone).date(),
        "count": 1
    } for participant in participants]

    df_participants = pd.DataFrame(participants_data)
    if not df_participants.empty:
        df_participants = df_participants.groupby('created_at').sum().reindex(all_dates, fill_value=0).reset_index()
    else:
        # 참가자 데이터가 없는 경우
        df_participants = pd.DataFrame({"created_at": all_dates, "count": 0})

    fig_participants = px.bar(
        df_participants,
        x='created_at',
        y='count',
        title="날짜별 참가자 수",
        labels={"created_at": "날짜", "count": "참가자 수"}
    )
    graphJSON_participants = fig_participants.to_json()

    answers = Answer.query.all()
    df_answers = pd.DataFrame(
        [
            {"question_id": a.question_id, "chosen_answer": a.chosen_answer}
            for a in answers
        ]
    )
    graphsJSON_answers = {}
    for question_id in df_answers["question_id"].unique():
        df_question = df_answers[df_answers["question_id"] == question_id]
        fig_answer = px.pie(
            df_question, names="chosen_answer", title=f"문제 {question_id} 응답 비율"
        )
        graphsJSON_answers[question_id] = fig_answer.to_json()
    # 결과 페이지를 렌더링합니다.
    return render_template(
        "results.html",
        graphJSON_participants=graphJSON_participants,
        graphsJSON_answers=graphsJSON_answers,
    )
