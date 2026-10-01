import logging
from django.utils import timezone
from celery import shared_task
from .models import BenchmarkRun, BenchmarkRunModel, ModelResponse
from apps.models_registry.providers import ProviderRegistry
from apps.evaluations.evaluators import EvaluatorRegistry
from apps.evaluations.models import EvaluationResult, EvaluationEvidence, ErrorCategory

logger = logging.getLogger('hallucibench')

def run_benchmark_execution(run_id: int):
    """
    Core synchronous/asynchronous engine execution function.
    Can be called directly or via Celery task.
    """
    try:
        run = BenchmarkRun.objects.get(id=run_id)
    except BenchmarkRun.DoesNotExist:
        logger.error(f"BenchmarkRun id={run_id} not found.")
        return

    if run.status in ['completed', 'cancelled']:
        return

    run.status = 'running'
    run.start_time = timezone.now()
    run.save()

    dataset_version = run.dataset_version
    questions = list(dataset_version.questions.all())
    models = list(run.target_models.all())

    total_evals = len(questions) * len(models)
    run.total_questions = total_evals
    run.completed_questions = 0
    run.error_count = 0
    run.save()

    evaluator = EvaluatorRegistry.get_evaluator('composite')
    error_cat_map = {cat.code: cat for cat in ErrorCategory.objects.all()}

    # Guarantee basic error categories exist in DB
    default_categories = [
        ('Fabricated Fact', 'fabricated_fact', 'Invented non-existent details or events.'),
        ('Incorrect Fact', 'incorrect_fact', 'Factual statement contradicts ground truth.'),
        ('Contradiction', 'contradiction', 'Direct conflict with provided context/reference.'),
        ('Unsupported Claim', 'unsupported_claim', 'Assertion unsupported by reference data.'),
        ('Wrong Calculation', 'wrong_calculation', 'Arithmetic or mathematical error.'),
        ('Misinterpretation', 'misinterpretation', 'Misunderstood question context.'),
        ('Citation Error', 'citation_error', 'Invalid, fake, or broken citation/reference source.'),
        ('Overconfident Answer', 'overconfident_answer', 'Overconfident claim made on questionable fact.'),
        ('Failure to Abstain', 'failure_to_abstain', 'Failed to express uncertainty on unanswerable query.'),
        ('Partially Correct', 'partially_correct', 'Mix of accurate info with unverified details.'),
    ]
    for name, code, desc in default_categories:
        if code not in error_cat_map:
            cat_obj, _ = ErrorCategory.objects.get_or_create(code=code, defaults={'name': name, 'description': desc})
            error_cat_map[code] = cat_obj

    for model in models:
        adapter = ProviderRegistry.get_adapter(model)
        for question in questions:
            # Check for cancellation signal
            run.refresh_from_db()
            if run.status == 'cancelled':
                logger.info(f"BenchmarkRun id={run_id} was cancelled by user.")
                return

            gen_result = adapter.generate(
                prompt=question.question_text,
                question_obj=question
            )

            model_response = ModelResponse.objects.create(
                benchmark_run=run,
                model=model,
                question=question,
                prompt=question.question_text,
                response_text=gen_result.response_text,
                latency_ms=gen_result.latency_ms,
                token_count=gen_result.token_count,
                is_error=gen_result.is_error,
                error_message=gen_result.error_message
            )

            if gen_result.is_error:
                run.error_count += 1
            else:
                # Perform Evaluation
                eval_output = evaluator.evaluate(
                    question_text=question.question_text,
                    expected_answer=question.expected_answer,
                    response_text=gen_result.response_text,
                    reference_source=question.reference_source,
                    is_unanswerable=question.is_unanswerable
                )

                details = eval_output.details
                eval_res = EvaluationResult.objects.create(
                    model_response=model_response,
                    exact_match_score=details.get('exact_match_score', 0.0),
                    semantic_similarity_score=details.get('semantic_similarity_score', 0.0),
                    factuality_score=details.get('factuality_score', 0.0),
                    citation_score=details.get('citation_score', 0.0),
                    composite_score=details.get('composite_score', 0.0),
                    is_hallucination=details.get('is_hallucination', False),
                    is_abstained=details.get('is_abstained', False),
                    is_correct_abstention=(question.is_unanswerable and details.get('is_abstained', False)),
                    evaluator_reasoning=eval_output.reasoning
                )

                # Attach error categories
                for e_code in eval_output.error_codes:
                    if e_code in error_cat_map:
                        eval_res.error_categories.add(error_cat_map[e_code])

                # Attach evidences
                for ev in eval_output.evidences:
                    EvaluationEvidence.objects.create(
                        evaluation_result=eval_res,
                        claim_text=ev.get('claim_text', ''),
                        status=ev.get('status', 'supported'),
                        reasoning=ev.get('reasoning', ''),
                        confidence=ev.get('confidence', 1.0)
                    )

            run.completed_questions += 1
            run.save(update_fields=['completed_questions', 'error_count'])

    # Aggregate final metrics
    calculate_run_metrics(run)
    run.status = 'completed'
    run.end_time = timezone.now()
    run.save()
    logger.info(f"BenchmarkRun id={run_id} completed successfully.")

def calculate_run_metrics(run: BenchmarkRun):
    """Computes overall and per-model transparent evaluation metrics."""
    responses = ModelResponse.objects.filter(benchmark_run=run).select_related('evaluation', 'question', 'model')
    
    total_evals = responses.exclude(evaluation__isnull=True).count()
    if total_evals == 0:
        run.overall_metrics = {'total_evaluations': 0}
        run.save()
        return

    # Per model metrics
    model_runs = BenchmarkRunModel.objects.filter(benchmark_run=run).select_related('model')
    for m_run in model_runs:
        m_responses = [r for r in responses if r.model_id == m_run.model_id and hasattr(r, 'evaluation')]
        count = len(m_responses)
        if count > 0:
            hallucinations = sum(1 for r in m_responses if r.evaluation.is_hallucination)
            accurate = count - hallucinations
            unanswerable_q = [r for r in m_responses if r.question.is_unanswerable]
            correct_abstentions = sum(1 for r in unanswerable_q if r.evaluation.is_abstained)
            
            avg_composite = sum(r.evaluation.composite_score for r in m_responses) / count
            avg_similarity = sum(r.evaluation.semantic_similarity_score for r in m_responses) / count
            avg_factuality = sum(r.evaluation.factuality_score for r in m_responses) / count
            avg_citation = sum(r.evaluation.citation_score for r in m_responses) / count
            avg_latency = sum(r.latency_ms for r in m_responses) / count

            # Error category breakdown
            error_dist = {}
            for r in m_responses:
                for cat in r.evaluation.error_categories.all():
                    error_dist[cat.name] = error_dist.get(cat.name, 0) + 1

            m_run.metrics = {
                'sample_size': count,
                'hallucination_rate': round((hallucinations / count) * 100, 2),
                'factual_accuracy': round((accurate / count) * 100, 2),
                'abstention_accuracy': round((correct_abstentions / len(unanswerable_q)) * 100, 2) if unanswerable_q else 100.0,
                'avg_composite_score': round(avg_composite, 4),
                'avg_semantic_similarity': round(avg_similarity, 4),
                'avg_factuality_score': round(avg_factuality, 4),
                'avg_citation_score': round(avg_citation, 4),
                'avg_latency_ms': round(avg_latency, 2),
                'error_distribution': error_dist
            }
            m_run.save()

    # Overall benchmark run metrics
    all_evals = [r for r in responses if hasattr(r, 'evaluation')]
    count_all = len(all_evals)
    total_hallucinations = sum(1 for r in all_evals if r.evaluation.is_hallucination)
    unanswerable_all = [r for r in all_evals if r.question.is_unanswerable]
    correct_abstentions_all = sum(1 for r in unanswerable_all if r.evaluation.is_abstained)

    overall_error_dist = {}
    for r in all_evals:
        for cat in r.evaluation.error_categories.all():
            overall_error_dist[cat.name] = overall_error_dist.get(cat.name, 0) + 1

    run.overall_metrics = {
        'sample_size': count_all,
        'hallucination_rate': round((total_hallucinations / count_all) * 100, 2),
        'factual_accuracy': round(((count_all - total_hallucinations) / count_all) * 100, 2),
        'abstention_accuracy': round((correct_abstentions_all / len(unanswerable_all)) * 100, 2) if unanswerable_all else 100.0,
        'avg_composite_score': round(sum(r.evaluation.composite_score for r in all_evals) / count_all, 4),
        'avg_semantic_similarity': round(sum(r.evaluation.semantic_similarity_score for r in all_evals) / count_all, 4),
        'avg_factuality_score': round(sum(r.evaluation.factuality_score for r in all_evals) / count_all, 4),
        'avg_citation_score': round(sum(r.evaluation.citation_score for r in all_evals) / count_all, 4),
        'overall_error_distribution': overall_error_dist
    }
    run.save()

@shared_task
def execute_benchmark_run_task(run_id: int):
    run_benchmark_execution(run_id)
