"""Contest business logic.

Lifecycle of a work:
1. submit_work()      — status=PENDING, work saved, photo kept as file_id
2. attach_group_message() — store chat/message IDs after posting to judges group
3. submit_score()     — one row per judge per work, UniqueConstraint enforces
                        single vote; status flips to SCORING after first vote
4. finalize_if_complete() — once all judges have voted, compute average and
                            status=FINALIZED; returns True if just finalized
"""
from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session

from app.models import (
    Contest, ContestWork, ContestScore, WorkStatus,
    User, UserRole,
)


class ContestError(Exception):
    def __init__(self, code: str, **extra):
        self.code = code
        self.extra = extra
        super().__init__(code)


# ---------- Contest lifecycle ----------
def get_active_contest(db: Session) -> Contest | None:
    """Return the single active contest, or None."""
    return db.query(Contest).filter(Contest.is_active.is_(True)).first()


def start_contest(
    db: Session, name: str, description: str | None, judge_chat_id: int | None,
) -> Contest:
    """End any existing active contest, start a new one."""
    existing = get_active_contest(db)
    if existing:
        existing.is_active = False
        from datetime import datetime, timezone
        existing.ended_at = datetime.now(timezone.utc)
    new = Contest(
        name=name[:200],
        description=(description or "").strip() or None,
        judge_chat_id=judge_chat_id,
        is_active=True,
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def end_contest(db: Session) -> Contest | None:
    """End the current active contest."""
    contest = get_active_contest(db)
    if contest is None:
        return None
    from datetime import datetime, timezone
    contest.is_active = False
    contest.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(contest)
    return contest


def leaderboard(db: Session, contest: Contest, limit: int = 10) -> list[ContestWork]:
    """Top-N finalized works ordered by average_score desc."""
    return (
        db.query(ContestWork)
        .filter(
            ContestWork.contest_id == contest.id,
            ContestWork.status == WorkStatus.FINALIZED.value,
        )
        .order_by(ContestWork.average_score.desc().nullslast())
        .limit(limit)
        .all()
    )


# ---------- Work submission ----------
def submit_work(
    db: Session,
    user: User,
    contest: Contest,
    photo_file_id: str,
    description: str | None,
) -> ContestWork:
    if not photo_file_id:
        raise ContestError("no_photo")
    if description and len(description) > 2000:
        raise ContestError("description_too_long")

    work = ContestWork(
        contest_id=contest.id,
        user_id=user.id,
        photo_file_id=photo_file_id,
        description=(description or "").strip() or None,
        status=WorkStatus.PENDING.value,
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    return work


def attach_group_message(
    db: Session, work_id: uuid.UUID, chat_id: int, message_id: int,
) -> None:
    work = db.get(ContestWork, work_id)
    if work:
        work.group_chat_id = chat_id
        work.group_message_id = message_id
        db.commit()


def find_by_group_message(
    db: Session, chat_id: int, message_id: int,
) -> ContestWork | None:
    return (
        db.query(ContestWork)
        .filter(
            ContestWork.group_chat_id == chat_id,
            ContestWork.group_message_id == message_id,
        )
        .first()
    )


# ---------- Scoring ----------
def submit_score(
    db: Session,
    work: ContestWork,
    judge: User,
    c1: int, c2: int, c3: int, c4: int, c5: int,
) -> ContestScore:
    """Record a judge's 5-criteria score. Enforces 1-vote-per-judge-per-work."""
    if judge.role != UserRole.JUDGE.value:
        raise ContestError("not_a_judge")
    for v in (c1, c2, c3, c4, c5):
        if not (1 <= v <= 10):
            raise ContestError("score_out_of_range", value=v)

    existing = (
        db.query(ContestScore)
        .filter(
            ContestScore.work_id == work.id,
            ContestScore.judge_id == judge.id,
        )
        .first()
    )
    if existing:
        raise ContestError("already_scored")

    score = ContestScore(
        work_id=work.id,
        judge_id=judge.id,
        c1=c1, c2=c2, c3=c3, c4=c4, c5=c5,
    )
    db.add(score)

    if work.status == WorkStatus.PENDING.value:
        work.status = WorkStatus.SCORING.value

    db.commit()
    db.refresh(score)
    return score


def count_judges(db: Session) -> int:
    """Total number of registered judges."""
    return (
        db.query(User)
        .filter(User.role == UserRole.JUDGE.value, User.is_active.is_(True))
        .count()
    )


def count_scores(db: Session, work: ContestWork) -> int:
    return (
        db.query(ContestScore)
        .filter(ContestScore.work_id == work.id)
        .count()
    )


def finalize_if_complete(db: Session, work: ContestWork) -> bool:
    """If every judge has scored this work, compute avg and finalize.

    Returns True if the work just got finalized (first time).
    """
    if work.status == WorkStatus.FINALIZED.value:
        return False

    total_judges = count_judges(db)
    if total_judges == 0:
        return False

    scored = count_scores(db, work)
    if scored < total_judges:
        return False

    # Compute average across all 5 criteria × all judges
    scores = (
        db.query(ContestScore)
        .filter(ContestScore.work_id == work.id)
        .all()
    )
    all_values = [
        s.c1 for s in scores
    ] + [s.c2 for s in scores] + [s.c3 for s in scores] + [
        s.c4 for s in scores
    ] + [s.c5 for s in scores]
    if not all_values:
        return False

    avg = Decimal(sum(all_values)) / Decimal(len(all_values))
    avg = avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    work.average_score = avg
    work.status = WorkStatus.FINALIZED.value
    db.commit()
    db.refresh(work)
    return True


def average_so_far(db: Session, work: ContestWork) -> Decimal | None:
    """Current average based on scores submitted so far (for live update)."""
    scores = (
        db.query(ContestScore)
        .filter(ContestScore.work_id == work.id)
        .all()
    )
    if not scores:
        return None
    all_values = [
        s.c1 for s in scores
    ] + [s.c2 for s in scores] + [s.c3 for s in scores] + [
        s.c4 for s in scores
    ] + [s.c5 for s in scores]
    avg = Decimal(sum(all_values)) / Decimal(len(all_values))
    return avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
