# File: utils/questions.py
from transformers import pipeline
import torch
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionGenerator:
    def __init__(self):
        torch.set_num_threads(1)  # Limit torch threads
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        self.models = self._load_models()
    
    def _load_models(self):
        """Load models with verified, stable alternatives"""
        models = {
            'MCQ': self._init_mcq_model(),
            'SHORT': self._init_short_model(),
            'TRUE_FALSE': self._init_truefalse_model(),
            'LONG': self._init_long_model()  # New long answer option
        }
        return models
    
    def _init_mcq_model(self):
        try:
            return {
                'model': pipeline("text2text-generation", model="google/flan-t5-base", device=0 if self.device == "cuda" else -1),
                'type': 'pipeline'
            }
        except Exception as e:
            logger.error(f"MCQ model initialization failed: {e}")
            raise RuntimeError("Failed to initialize MCQ generator")

    def _init_short_model(self):
        try:
            return {
                'model': pipeline("question-answering", model="distilbert-base-cased-distilled-squad", device=0 if self.device == "cuda" else -1),
                'type': 'pipeline'
            }
        except Exception as e:
            logger.error(f"Short answer model initialization failed: {e}")
            raise RuntimeError("Failed to initialize short answer generator")

    def _init_truefalse_model(self):
        try:
            return {
                'model': pipeline("text-classification", model="cross-encoder/nli-deberta-v3-small", device=0 if self.device == "cuda" else -1),
                'type': 'pipeline'
            }
        except Exception as e:
            logger.error(f"True/False model initialization failed: {e}")
            raise RuntimeError("Failed to initialize true/false generator")

    def _init_long_model(self):
        try:
            return {
                'model': pipeline("summarization", model="facebook/bart-large-cnn", device=0 if self.device == "cuda" else -1),
                'type': 'pipeline'
            }
        except Exception as e:
            logger.error(f"Long answer model initialization failed: {e}")
            raise RuntimeError("Failed to initialize long answer generator")

    def generate_questions(self, context: str, q_type: str, count: int = 5) -> List[Dict]:
        """Generate questions with robust error handling"""
        if not context.strip():
            raise ValueError("Context cannot be empty")
        
        if q_type not in self.models:
            raise ValueError(f"Invalid question type: {q_type}. Choose from: {list(self.models.keys())}")
        
        questions = []
        attempts = 0
        max_attempts = count * 2 
        
        while len(questions) < count and attempts < max_attempts:
            attempts += 1
            try:
                question = self._generate_question(context, q_type)
                if self._validate_question(question):
                    questions.append(question)
            except Exception as e:
                logger.warning(f"Attempt {attempts} failed: {e}")
                continue
        
        if not questions:
            raise RuntimeError(f"Failed to generate valid {q_type} questions after {max_attempts} attempts")
        
        return questions[:count]

    def _generate_question(self, context: str, q_type: str) -> Dict:
        """Generate a single question based on type"""
        context = context[:1000] 
        
        if q_type == 'MCQ':
            prompt = f"Generate a multiple choice question about: {context}"
            result = self.models['MCQ']['model'](prompt, max_length=200)
            question = result[0]['generated_text']
            answer = self._extract_answer(context, question)
            return {'question': question, 'answer': answer, 'options': [answer] + self._generate_distractors(context, answer), 'type': 'MCQ'}
        
        elif q_type == 'SHORT':
            result = self.models['SHORT']['model'](question="What is a good question about this text?", context=context)
            question = result['answer']
            answer = self._extract_answer(context, question)
            return {'question': question, 'answer': answer, 'type': 'SHORT'}
        
        elif q_type == 'TRUE_FALSE':
            result = self.models['TRUE_FALSE']['model'](f"This text: {context}", candidate_labels=["entailment", "contradiction"])
            statement = result['sequence']
            is_true = result['labels'][0] == "entailment"
            return {'question': f"True or False: {statement}", 'answer': "True" if is_true else "False", 'type': 'TRUE_FALSE'}
        
        elif q_type == 'LONG':  # New Long Answer Option
            result = self.models['LONG']['model'](context, max_length=300, min_length=100)
            long_answer = result[0]['summary_text']
            return {'question': f"Provide a detailed explanation of: {context[:100]}", 'answer': long_answer, 'type': 'LONG'}

    def _extract_answer(self, context: str, question: str) -> str:
        """Simple answer extraction (override with better logic)"""
        return context.split('.')[0].strip() or "Answer not found"

    def _generate_distractors(self, context: str, correct: str) -> List[str]:
        """Generate plausible wrong answers"""
        return ["None of the above", "All of the above", "The text doesn't say"]

    def _validate_question(self, question: Dict) -> bool:
        """Quality checks for generated questions"""
        required_keys = ['question', 'answer', 'type']
        return all(key in question for key in required_keys) and len(question['question'].strip()) > 10 and question['answer'].strip()
