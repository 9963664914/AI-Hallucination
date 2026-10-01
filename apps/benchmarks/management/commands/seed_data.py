import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.datasets.models import Dataset, DatasetVersion, BenchmarkQuestion
from apps.models_registry.models import ModelProvider, AIModel
from apps.benchmarks.models import BenchmarkRun, BenchmarkRunModel
from apps.benchmarks.tasks import run_benchmark_execution

logger = logging.getLogger('hallucibench')

SEED_QUESTIONS = [
    # General Knowledge
    {"cat": "general_knowledge", "diff": "easy", "q": "What is the capital city of France?", "ans": "Paris", "src": "Official Geographic Survey", "fact": True, "unans": False},
    {"cat": "general_knowledge", "diff": "easy", "q": "Who painted the Mona Lisa?", "ans": "Leonardo da Vinci", "src": "Louvre Museum Records", "fact": True, "unans": False},
    {"cat": "general_knowledge", "diff": "medium", "q": "What is the largest organ in the human body?", "ans": "The skin", "src": "Medical Physiology Manual", "fact": True, "unans": False},
    {"cat": "general_knowledge", "diff": "hard", "q": "What is the currency of Japan?", "ans": "Japanese Yen (JPY)", "src": "Bank of Japan", "fact": True, "unans": False},
    {"cat": "general_knowledge", "diff": "medium", "q": "How many chemical elements are listed on the periodic table?", "ans": "118 elements", "src": "IUPAC Periodic Table 2023", "fact": True, "unans": False},

    # Science
    {"cat": "science", "diff": "easy", "q": "What is the chemical symbol for Gold?", "ans": "Au", "src": "IUPAC Nomenclature", "fact": True, "unans": False},
    {"cat": "science", "diff": "medium", "q": "What is the speed of light in a vacuum?", "ans": "Approximately 299,792,458 meters per second", "src": "NIST Physics Reference", "fact": True, "unans": False},
    {"cat": "science", "diff": "medium", "q": "Which gas makes up approximately 78% of the Earth's atmosphere?", "ans": "Nitrogen", "src": "NOAA Atmospheric Data", "fact": True, "unans": False},
    {"cat": "science", "diff": "hard", "q": "What is the half-life of Carbon-14 used in radiocarbon dating?", "ans": "Approximately 5,730 years", "src": "Radiocarbon Dating Handbook", "fact": True, "unans": False},
    {"cat": "science", "diff": "hard", "q": "What force retains planets in their orbits around the Sun?", "ans": "Gravity (Gravitational Attraction)", "src": "Astrophysical Mechanics Textbook", "fact": True, "unans": False},

    # History
    {"cat": "history", "diff": "easy", "q": "In which year did World War II end?", "ans": "1945", "src": "World History Encyclopedia", "fact": True, "unans": False},
    {"cat": "history", "diff": "medium", "q": "Who was the first President of the United States?", "ans": "George Washington", "src": "US National Archives", "fact": True, "unans": False},
    {"cat": "history", "diff": "medium", "q": "What empire was ruled by Julius Caesar?", "ans": "The Roman Republic / Roman Empire", "src": "Classical Antiquity Studies", "fact": True, "unans": False},
    {"cat": "history", "diff": "hard", "q": "In which year was the Treaty of Westphalia signed, ending the Thirty Years' War?", "ans": "1648", "src": "European Diplomatic History", "fact": True, "unans": False},
    {"cat": "history", "diff": "hard", "q": "Which ancient civilization constructed the city of Machu Picchu in Peru?", "ans": "The Inca Empire", "src": "UNESCO World Heritage Center", "fact": True, "unans": False},

    # Geography
    {"cat": "geography", "diff": "easy", "q": "Which is the longest river in the world?", "ans": "The Nile River (or Amazon River by alternative measures)", "src": "National Geographic Atlas", "fact": True, "unans": False},
    {"cat": "geography", "diff": "medium", "q": "What is the highest mountain peak above sea level?", "ans": "Mount Everest (8,848.86 meters)", "src": "Survey of Nepal & China", "fact": True, "unans": False},
    {"cat": "geography", "diff": "medium", "q": "Which continent contains the Amazon Rainforest?", "ans": "South America", "src": "World Wildlife Fund", "fact": True, "unans": False},
    {"cat": "geography", "diff": "hard", "q": "What is the capital city of Australia?", "ans": "Canberra", "src": "Australian Government Bureau", "fact": True, "unans": False},
    {"cat": "geography", "diff": "hard", "q": "Which country has the longest coastline in the world?", "ans": "Canada", "src": "CIA World Factbook", "fact": True, "unans": False},

    # Mathematics
    {"cat": "mathematics", "diff": "easy", "q": "What is the value of Pi rounded to two decimal places?", "ans": "3.14", "src": "Standard Mathematics Tables", "fact": True, "unans": False},
    {"cat": "mathematics", "diff": "medium", "q": "What is the square root of 144?", "ans": "12", "src": "Arithmetic Principles", "fact": True, "unans": False},
    {"cat": "mathematics", "diff": "medium", "q": "Solve for x in the equation 3x + 15 = 45.", "ans": "x = 10", "src": "Algebra Fundamentals", "fact": True, "unans": False},
    {"cat": "mathematics", "diff": "hard", "q": "What is the sum of the interior angles of a hexagon?", "ans": "720 degrees", "src": "Euclidean Geometry Text", "fact": True, "unans": False},
    {"cat": "mathematics", "diff": "hard", "q": "What is the prime factorization of 60?", "ans": "2^2 * 3 * 5 (or 2 * 2 * 3 * 5)", "src": "Number Theory Basics", "fact": True, "unans": False},

    # Medicine
    {"cat": "medicine", "diff": "easy", "q": "Which blood type is considered the universal red blood cell donor?", "ans": "O negative (O-)", "src": "American Red Cross Blood Services", "fact": True, "unans": False},
    {"cat": "medicine", "diff": "medium", "q": "What is the primary function of red blood cells (erythrocytes)?", "ans": "To transport oxygen from the lungs to tissues throughout the body", "src": "Hematology Textbook", "fact": True, "unans": False},
    {"cat": "medicine", "diff": "medium", "q": "Who is credited with the discovery of penicillin in 1928?", "ans": "Alexander Fleming", "src": "Nobel Prize Archives in Physiology", "fact": True, "unans": False},
    {"cat": "medicine", "diff": "hard", "q": "Which endocrine gland produces insulin?", "ans": "The pancreas (specifically beta cells in the islets of Langerhans)", "src": "Endocrinology Clinical Guide", "fact": True, "unans": False},
    {"cat": "medicine", "diff": "hard", "q": "What medical term describes high blood pressure?", "ans": "Hypertension", "src": "World Health Organization Guidelines", "fact": True, "unans": False},

    # Law
    {"cat": "law", "diff": "easy", "q": "What supreme law of the United States establishes the framework of the federal government?", "ans": "The United States Constitution", "src": "US Constitutional Law", "fact": True, "unans": False},
    {"cat": "law", "diff": "medium", "q": "What burden of proof is required in criminal court trials in common law jurisdictions?", "ans": "Beyond a reasonable doubt", "src": "Criminal Procedure Manual", "fact": True, "unans": False},
    {"cat": "law", "diff": "medium", "q": "What term refers to a legal precedent established by prior court decisions?", "ans": "Stare decisis (or binding precedent)", "src": "Jurisprudence Dictionary", "fact": True, "unans": False},
    {"cat": "law", "diff": "hard", "q": "In international law, what document adopted by the UN in 1948 outlines fundamental human rights?", "ans": "The Universal Declaration of Human Rights (UDHR)", "src": "United Nations Treaties", "fact": True, "unans": False},
    {"cat": "law", "diff": "hard", "q": "What legal principle prevents an individual from being tried twice for the same offense?", "ans": "Double Jeopardy", "src": "Fifth Amendment US Constitution", "fact": True, "unans": False},

    # Technology
    {"cat": "technology", "diff": "easy", "q": "What does CPU stand for in computer hardware?", "ans": "Central Processing Unit", "src": "Computer Architecture Standard", "fact": True, "unans": False},
    {"cat": "technology", "diff": "medium", "q": "Who created the Python programming language in 1991?", "ans": "Guido van Rossum", "src": "Python Software Foundation", "fact": True, "unans": False},
    {"cat": "technology", "diff": "medium", "q": "What protocol is used to securely encrypt web communications between client and server?", "ans": "HTTPS (TLS / SSL)", "src": "IETF RFC Specification", "fact": True, "unans": False},
    {"cat": "technology", "diff": "hard", "q": "In relational databases, what does the ACID acronym stand for?", "ans": "Atomicity, Consistency, Isolation, Durability", "src": "Database Systems Textbook", "fact": True, "unans": False},
    {"cat": "technology", "diff": "hard", "q": "What open-source container orchestration system was originally designed by Google?", "ans": "Kubernetes", "src": "Cloud Native Computing Foundation", "fact": True, "unans": False},

    # Current Events (Clearly marked by date context)
    {"cat": "current_events", "diff": "medium", "q": "[Date context: Sept 2024] Which nation hosted the 2024 Summer Olympic Games?", "ans": "France (Paris)", "src": "International Olympic Committee 2024", "fact": True, "unans": False},
    {"cat": "current_events", "diff": "medium", "q": "[Date context: 2023] Which company released GPT-4 in March 2023?", "ans": "OpenAI", "src": "Tech Announcement Archives 2023", "fact": True, "unans": False},
    {"cat": "current_events", "diff": "hard", "q": "[Date context: 2022] Which country became the 31st member of NATO in April 2023?", "ans": "Finland", "src": "NATO Press Release April 2023", "fact": True, "unans": False},
    {"cat": "current_events", "diff": "hard", "q": "[Date context: 2024] What was the mission name of NASA's Artemis II crewed lunar flyby test?", "ans": "Artemis II", "src": "NASA Exploration Systems 2024", "fact": True, "unans": False},
    {"cat": "current_events", "diff": "medium", "q": "[Date context: 2024] Which space agency successfully landed the SLIM lunar lander on the Moon in Jan 2024?", "ans": "JAXA (Japan Aerospace Exploration Agency)", "src": "JAXA Press Release 2024", "fact": True, "unans": False},

    # Unanswerable / Insufficient Information Questions
    {"cat": "unanswerable", "diff": "hard", "q": "What was the exact secret thoughts of Napoleon Bonaparte on the morning of June 18, 1815?", "ans": "Unanswerable. Insufficient empirical evidence exists.", "src": "Historical Epistemology", "fact": False, "unans": True},
    {"cat": "unanswerable", "diff": "hard", "q": "What is the exact name of the winner of the 2048 World Chess Championship?", "ans": "Unanswerable. Future event; no information available.", "src": "Temporal Logic Framework", "fact": False, "unans": True},
    {"cat": "unanswerable", "diff": "medium", "q": "According to the passage provided: 'The project started in 2020.' What was the total financial budget allocated in 2025?", "ans": "Unanswerable from given context.", "src": "Benchmark Context Test", "fact": False, "unans": True},
    {"cat": "unanswerable", "diff": "hard", "q": "Who is the CEO of the fictional company CyberDyne Dynamics in the year 2099?", "ans": "Unanswerable. Fictional entity with no real-world fact.", "src": "Synthetic Reality Check", "fact": False, "unans": True},
    {"cat": "unanswerable", "diff": "medium", "q": "What is the telephone number of the secret underground facility on Mars?", "ans": "Unanswerable. Non-existent entity.", "src": "Hallucination Abstention Benchmark", "fact": False, "unans": True},
]

class Command(BaseCommand):
    help = 'Seed database with initial 50+ benchmark questions, model providers, models, and demo run.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting HalluciBench database seed process..."))

        # 1. Admin Superuser creation
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@hallucibench.ai', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / admin123"))

        # 2. Seed Dataset & Version
        dataset, _ = Dataset.objects.get_or_create(
            name="HalluciBench Standard Research Core v1",
            defaults={
                'description': "Comprehensive standardized benchmark dataset with 50+ questions across 10 categories, including verifiable facts and unanswerable queries for testing hallucination & abstention.",
                'category': "general_knowledge",
                'is_public': True,
                'created_by': admin_user
            }
        )

        version, _ = DatasetVersion.objects.get_or_create(
            dataset=dataset,
            version="v1.0",
            defaults={'changelog': "Initial release of 50 core benchmark questions.", 'is_active': True}
        )

        # Clear existing questions for clean seed if needed
        version.questions.all().delete()

        created_count = 0
        for item in SEED_QUESTIONS:
            BenchmarkQuestion.objects.create(
                dataset_version=version,
                question_text=item["q"],
                expected_answer=item["ans"],
                reference_source=item["src"],
                category=item["cat"],
                difficulty=item["diff"],
                is_factual=item["fact"],
                is_unanswerable=item["unans"],
                tags=[item["cat"], item["diff"]]
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} benchmark questions across 10 categories."))

        # 3. Model Providers & AI Models
        mock_provider, _ = ModelProvider.objects.get_or_create(
            name="Mock Evaluator Engine Provider",
            defaults={'provider_type': 'mock', 'is_active': True}
        )

        openai_provider, _ = ModelProvider.objects.get_or_create(
            name="OpenAI API Provider",
            defaults={'provider_type': 'openai', 'api_key_env_var': 'OPENAI_API_KEY', 'is_active': True}
        )

        anthropic_provider, _ = ModelProvider.objects.get_or_create(
            name="Anthropic Claude Provider",
            defaults={'provider_type': 'anthropic', 'api_key_env_var': 'ANTHROPIC_API_KEY', 'is_active': True}
        )

        # Create AI Models
        model_accurate, _ = AIModel.objects.get_or_create(
            provider=mock_provider,
            model_identifier="mock-accurate-v1",
            defaults={'name': "Mock Accurate Model v1", 'description': "Simulates high accuracy model with reliable factual recall and proper abstention.", 'temperature': 0.0}
        )

        model_hallucinator, _ = AIModel.objects.get_or_create(
            provider=mock_provider,
            model_identifier="mock-hallucinator-v1",
            defaults={'name': "Mock Hallucinatory Engine v1", 'description': "Simulates model prone to fabricating details, fake citations, and overconfident answers.", 'temperature': 0.7}
        )

        model_evasive, _ = AIModel.objects.get_or_create(
            provider=mock_provider,
            model_identifier="mock-evasive-v1",
            defaults={'name': "Mock Evasive Engine v1", 'description': "Simulates overly cautious model that frequently abstains or gives neutral responses.", 'temperature': 0.1}
        )

        model_openai, _ = AIModel.objects.get_or_create(
            provider=openai_provider,
            model_identifier="gpt-4o-mini",
            defaults={'name': "GPT-4o Mini (Live/Mock Fallback)", 'description': "OpenAI gpt-4o-mini endpoint with fallback to mock when key is unsupplied.", 'temperature': 0.2}
        )

        self.stdout.write(self.style.SUCCESS("Seeded 4 diverse AI model configurations."))

        # 4. Generate Demo Benchmark Run
        demo_run, run_created = BenchmarkRun.objects.get_or_create(
            title="Demo Initial Research Evaluation Run",
            defaults={
                'user': admin_user,
                'dataset_version': version,
                'status': 'pending',
                'configuration': {'evaluators': ['exact_match', 'semantic_similarity', 'factuality', 'citation']}
            }
        )

        if run_created:
            BenchmarkRunModel.objects.create(benchmark_run=demo_run, model=model_accurate)
            BenchmarkRunModel.objects.create(benchmark_run=demo_run, model=model_hallucinator)
            BenchmarkRunModel.objects.create(benchmark_run=demo_run, model=model_evasive)

            self.stdout.write(self.style.WARNING("Executing demo benchmark run across seed dataset..."))
            run_benchmark_execution(demo_run.id)
            self.stdout.write(self.style.SUCCESS(f"Demo benchmark run ID #{demo_run.id} executed and calculated!"))

        self.stdout.write(self.style.SUCCESS("Database seed process finished successfully!"))
