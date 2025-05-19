from collections import defaultdict
from statistics import mean, median, stdev, mode
from scipy.stats import pearsonr, linregress
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from core.models import StudentData, Survey, SurveyQuestion, Answer, Student


@dataclass
class QuestionStats:
    id: int
    text: str
    characteristic: str
    values: List[int]
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[int] = None
    stdev: Optional[float] = None


@dataclass
class CharacteristicBlock:
    name: str
    questions: List[QuestionStats] = field(default_factory=list)
    block_mean: Optional[float] = None
    weighted_block_mean: Optional[float] = None


@dataclass
class SurveyAnalysisDTO:
    survey_id: int
    name: str
    year: int
    total_responses: int
    total_students: int
    characteristics: List[CharacteristicBlock]
    overall_mean: Optional[float] = None
    overall_weighted_mean: Optional[float] = None
    weighted_averages: Dict[int, float] = field(default_factory=dict)
    correlation_matrix: Dict[str, Dict[str, Optional[float]]] = field(default_factory=dict)
    correlation_headers: List[str] = field(default_factory=list)
    correlation_labels: Dict[str, str] = field(default_factory=dict)
    regression_coefficients: Optional[Dict[str, float]] = None


def get_weight(student: Student) -> float:
    try:
        data = student.data
        grades = data.avg_score
        attendance = data.attendance_ratio
    except StudentData.DoesNotExist:
        grades = 4.0
        attendance = 0.9
    return (grades / 5 + attendance) / 2


def analyze_survey(survey: Survey) -> SurveyAnalysisDTO:
    survey_questions = SurveyQuestion.objects.filter(survey=survey).select_related('question')
    answers = Answer.objects.filter(form__survey=survey).select_related('form__student', 'question')
    total_students = survey.teacher_subject.group.student_set.count()
    total_responses = answers.values('form').distinct().count()

    grouped_data: Dict[str, CharacteristicBlock] = {}
    weight_sums = defaultdict(float)
    weighted_totals = defaultdict(float)

    question_map = {}
    for sq in survey_questions:
        q = sq.question
        question_map[q.id] = q
        if q.characteristic not in grouped_data:
            grouped_data[q.characteristic] = CharacteristicBlock(name=q.characteristic)
        grouped_data[q.characteristic].questions.append(
            QuestionStats(id=q.id, text=q.text, characteristic=q.characteristic, values=[])
        )

    for a in answers:
        try:
            value = int(a.value)
        except ValueError:
            continue
        q_id = a.question.id
        student = a.form.student
        w = get_weight(student)

        for block in grouped_data.values():
            for qstat in block.questions:
                if qstat.id == q_id:
                    qstat.values.append(value)

        weight_sums[q_id] += w
        weighted_totals[q_id] += w * value

    weighted_averages = {
        qid: round(weighted_totals[qid] / weight_sums[qid], 2)
        for qid in weighted_totals if weight_sums[qid] > 0
    }

    all_means = []
    all_weighted = []
    all_qstats = []

    for block in grouped_data.values():
        block_means = []
        weighted_means = []
        for q in block.questions:
            all_qstats.append(q)
            if q.values:
                q.mean = round(mean(q.values), 2)
                q.median = median(q.values)
                try:
                    q.mode = mode(q.values)
                except:
                    q.mode = None
                q.stdev = round(stdev(q.values), 2) if len(q.values) > 1 else 0
                block_means.append(q.mean)
                if q.id in weighted_averages:
                    weighted_mean = weighted_averages[q.id]
                    weighted_means.append(weighted_mean)
        block.block_mean = round(mean(block_means), 2) if block_means else None
        block.weighted_block_mean = round(mean(weighted_means), 2) if weighted_means else None
        all_means.extend(block_means)
        all_weighted.extend(weighted_means)

    overall_mean = round(mean(all_means), 2) if all_means else None
    overall_weighted_mean = round(mean(all_weighted), 2) if all_weighted else None

    short_labels = {q.text: f"Q{i+1}" for i, q in enumerate(all_qstats)}
    headers = [short_labels[q.text] for q in all_qstats]
    matrix = {}

    for q1 in all_qstats:
        short1 = short_labels[q1.text]
        row = {}
        for q2 in all_qstats:
            short2 = short_labels[q2.text]
            if q1.id == q2.id:
                row[short2] = 1.0
            elif len(q1.values) == len(q2.values) and len(q1.values) > 2:
                try:
                    r, _ = pearsonr(q1.values, q2.values)
                    row[short2] = round(r, 2)
                except:
                    row[short2] = None
            else:
                row[short2] = None
        matrix[short1] = row

    regression_coeffs = None
    try:
        target_block = grouped_data.get("Общее впечатление")
        if target_block and target_block.questions:
            y_values = target_block.questions[0].values
            x_blocks = [b for k, b in grouped_data.items() if k != "Общее впечатление"]
            x_matrix = []
            for i in range(len(y_values)):
                row = []
                for b in x_blocks:
                    avg = mean([q.values[i] for q in b.questions if len(q.values) > i])
                    row.append(avg if avg else 0)
                x_matrix.append(row)

            regression_coeffs = {
                b.name: round(linregress([row[i] for row in x_matrix], y_values).slope, 2)
                for i, b in enumerate(x_blocks)
            }
    except Exception:
        regression_coeffs = None

    return SurveyAnalysisDTO(
        survey_id=survey.id,
        name=survey.name,
        year=survey.year,
        total_students=total_students,
        total_responses=total_responses,
        characteristics=list(grouped_data.values()),
        overall_mean=overall_mean,
        overall_weighted_mean=overall_weighted_mean,
        weighted_averages=weighted_averages,
        correlation_matrix=matrix,
        correlation_headers=headers,
        correlation_labels=short_labels,
        regression_coefficients=regression_coeffs
    )
