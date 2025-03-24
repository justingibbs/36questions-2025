from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from ..models.schemas import QuestionResponse

@dataclass
class QuestionDependencies:
    user_id: str
    data_dir: Path = Path("data")
    questions_path: Path = Path("data/36questions.json")
    answers_dir: Path = Path("data/user_answers")
    prompts_path: Path = Path("data/prompts.json")

class QuestionResult(BaseModel):
    html: str = Field(description='HTML response to be rendered')
    question_id: Optional[int] = Field(description='ID of the current question')

# Initialize the agent
question_agent = Agent(
    'gemini-pro',
    deps_type=QuestionDependencies,
    result_type=QuestionResult,
    system_prompt=(
        'You are a helpful assistant guiding users through answering questions. '
        'Maintain a supportive and encouraging tone.'
    )
)

@question_agent.tool
async def get_prompt(ctx: RunContext[QuestionDependencies], prompt_type: str) -> str:
    """Get a specific conversation prompt"""
    with open(ctx.deps.prompts_path) as f:
        prompts = json.load(f)
        if prompt_type in prompts["conversation"]:
            return prompts["conversation"][prompt_type]
        if isinstance(prompts["conversation"][prompt_type], list):
            import random
            return random.choice(prompts["conversation"][prompt_type])
        raise ValueError(f"Unknown prompt type: {prompt_type}")

@question_agent.tool
async def get_question(ctx: RunContext[QuestionDependencies], question_id: int) -> Dict:
    """Get a specific question and its guidance"""
    ctx.deps.answers_dir.mkdir(exist_ok=True)
    with open(ctx.deps.questions_path) as f:
        questions = json.load(f)["questions"]
        return next((q for q in questions if q["id"] == question_id), None)

@question_agent.tool
async def get_user_progress(ctx: RunContext[QuestionDependencies]) -> Dict:
    """Get user's answer progress and next question"""
    answers_file = ctx.deps.answers_dir / f"{ctx.deps.user_id}-answers.json"
    
    if not answers_file.exists():
        return {
            "next_question_id": 1,
            "answered": [],
            "skipped": []
        }
    
    with open(answers_file) as f:
        user_data = json.load(f)
        answered = [a["question_id"] for a in user_data["answers"] 
                   if a["status"] == "answered"]
        skipped = [a["question_id"] for a in user_data["answers"] 
                  if a["status"] == "skipped"]
        
        with open(ctx.deps.questions_path) as qf:
            all_ids = [q["id"] for q in json.load(qf)["questions"]]
            remaining = [qid for qid in all_ids 
                       if qid not in answered + skipped]
            next_id = min(remaining) if remaining else min(skipped) if skipped else None

        return {
            "next_question_id": next_id,
            "answered": answered,
            "skipped": skipped
        }

@question_agent.tool
async def save_answer(
    ctx: RunContext[QuestionDependencies],
    question_id: int,
    answer: str,
    status: str = "answered"
) -> bool:
    """Save or update user's answer"""
    answers_file = ctx.deps.answers_dir / f"{ctx.deps.user_id}-answers.json"
    
    data = {
        "user_id": ctx.deps.user_id,
        "answers": []
    }
    
    if answers_file.exists():
        with open(answers_file) as f:
            data = json.load(f)

    now = datetime.utcnow().isoformat()
    answer_entry = {
        "question_id": question_id,
        "answer": answer,
        "status": status,
        "timestamp": now,
        "last_modified": now
    }

    for idx, existing in enumerate(data["answers"]):
        if existing["question_id"] == question_id:
            answer_entry["timestamp"] = existing["timestamp"]
            data["answers"][idx] = answer_entry
            break
    else:
        data["answers"].append(answer_entry)

    with open(answers_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return True

@question_agent.tool
async def get_next_interaction(ctx: RunContext[QuestionDependencies]) -> QuestionResponse:
    """Get the next question or follow-up for the user"""
    progress = await ctx.deps.question_tools.get_user_progress(ctx.deps.user_id)
    
    if not progress["next_question_id"]:
        return QuestionResponse(
            html="Congratulations! You've answered all the questions.",
            question_id=None
        )
    
    question = await ctx.deps.question_tools.get_question(progress["next_question_id"])
    prompt = await ctx.deps.prompt_tools.format_question_prompt(question)
    
    return QuestionResponse(
        html=f"""
        <div class="question-container" hx-target="this" hx-swap="outerHTML">
            <div class="question">{prompt}</div>
            <textarea name="answer" 
                      placeholder="Type your answer here..."
                      hx-post="/submit-answer/{question['id']}"></textarea>
            <button hx-post="/skip-question/{question['id']}">
                Skip for now
            </button>
        </div>
        """,
        question_id=question["id"]
    ) 