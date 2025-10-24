"""Dummy test documents for testing the Knowledge Graph Index."""

# Test Document 1: Technology Overview
TECH_DOCUMENT = """
Artificial Intelligence and Machine Learning

Artificial Intelligence (AI) is revolutionizing the technology industry.
Machine Learning, a critical subset of AI, enables computers to learn from
data without being explicitly programmed. Deep Learning, which uses artificial
neural networks, has achieved remarkable breakthroughs in computer vision and
natural language processing.

Key Companies and Their Contributions

Google developed TensorFlow, an open-source machine learning framework that
has become widely adopted in the AI community. Microsoft created Azure AI
services and invested heavily in OpenAI. OpenAI, founded by Sam Altman and
others, developed GPT models that transformed natural language understanding.

Meta (formerly Facebook) focuses on computer vision research and developed
PyTorch, another popular deep learning framework. Amazon built Amazon Web
Services AI tools for cloud-based machine learning.

Applications and Impact

AI applications span multiple domains. In healthcare, AI assists with medical
diagnosis and drug discovery. Autonomous vehicles use AI for navigation and
decision-making. Recommendation systems powered by machine learning personalize
user experiences on platforms like Netflix and Spotify.

Natural language processing enables chatbots and virtual assistants like Siri,
Alexa, and Google Assistant to understand and respond to human language.
Computer vision powers facial recognition systems and image classification tools.

Future Challenges

The AI community faces several challenges. Explainability remains a critical
issue - understanding how AI models make decisions. Ethics in AI development
includes addressing bias, fairness, and privacy concerns. AI safety research
focuses on ensuring AI systems remain beneficial and aligned with human values.

Researchers at organizations like DeepMind, OpenAI, and university labs work
on advancing AI capabilities while addressing these fundamental challenges.
"""

# Test Document 2: Software Development
SOFTWARE_DOCUMENT = """
Modern Software Development Practices

Software development has evolved significantly with the adoption of agile
methodologies and DevOps practices. Continuous Integration and Continuous
Deployment (CI/CD) have become standard practices in modern development teams.

Version Control and Collaboration

Git, created by Linus Torvalds, is the dominant version control system used
by developers worldwide. GitHub, acquired by Microsoft, provides a platform
for hosting Git repositories and facilitating collaboration. GitLab and
Bitbucket offer similar services with different feature sets.

Developers use pull requests for code review, ensuring code quality and
knowledge sharing within teams. Branching strategies like Git Flow and
trunk-based development help teams manage code changes effectively.

Programming Languages and Frameworks

Python has become the most popular language for data science and machine
learning applications. JavaScript dominates web development, with frameworks
like React, Vue, and Angular enabling rich user interfaces. TypeScript adds
static typing to JavaScript, improving code maintainability.

Go, developed by Google, is valued for its simplicity and performance in
building microservices. Rust provides memory safety without garbage collection,
making it ideal for systems programming. Java remains widely used in enterprise
applications.

Cloud Infrastructure

Amazon Web Services (AWS) pioneered cloud computing and remains the market
leader. Microsoft Azure has grown rapidly, especially in enterprise markets.
Google Cloud Platform offers strong capabilities in data analytics and
machine learning.

Kubernetes, originally developed by Google, has become the standard for
container orchestration. Docker revolutionized application deployment through
containerization. Infrastructure as Code tools like Terraform enable
reproducible infrastructure management.

Testing and Quality Assurance

Test-Driven Development (TDD) encourages writing tests before implementation.
Unit testing frameworks like Jest, PyTest, and JUnit help developers verify
code correctness. Integration testing ensures different components work
together properly.

Code coverage tools measure how much code is tested. Static analysis tools
like ESLint and Pylint catch common errors and enforce coding standards.
Continuous testing in CI/CD pipelines provides rapid feedback to developers.
"""

# Test Document 3: Startup Ecosystem
STARTUP_DOCUMENT = """
The Modern Startup Ecosystem

The startup ecosystem has transformed dramatically over the past two decades.
Silicon Valley remains the epicenter of technology startups, but other hubs
like Austin, Seattle, and international cities have gained prominence.

Venture Capital and Funding

Sequoia Capital, one of the most prestigious venture capital firms, has funded
companies like Apple, Google, and Airbnb. Andreessen Horowitz (a16z), founded
by Marc Andreessen and Ben Horowitz, focuses on technology investments.
Y Combinator, a startup accelerator, has launched successful companies
including Airbnb, Stripe, and Dropbox.

Venture capital operates through different funding stages. Seed funding helps
startups develop initial products. Series A funding scales proven business
models. Later stages (Series B, C, D) fund rapid growth and market expansion.

Successful Startup Stories

Airbnb, founded by Brian Chesky, transformed the hospitality industry by
enabling peer-to-peer property rentals. Uber revolutionized transportation
through its ride-sharing platform. Stripe, created by Patrick and John Collison,
simplified online payment processing for businesses.

SpaceX, founded by Elon Musk, made space travel more accessible through
reusable rockets. Tesla disrupted the automotive industry with electric
vehicles and autonomous driving technology. Coinbase became the leading
cryptocurrency exchange platform.

Startup Culture and Practices

Lean Startup methodology, popularized by Eric Ries, emphasizes rapid iteration
and customer feedback. The concept of Minimum Viable Product (MVP) helps
startups test ideas quickly. Product-market fit remains the critical milestone
for startup success.

Remote work has become standard in many startups, expanding access to global
talent. Equity compensation through stock options attracts employees to
high-risk, high-reward opportunities. Company culture and mission drive
employee engagement in startup environments.

Challenges and Failures

Many startups fail due to lack of market need for their product. Running out
of cash before achieving profitability ends many ventures. Competition from
established companies and other startups creates difficult market dynamics.

The "move fast and break things" mentality sometimes leads to ethical issues
and regulatory challenges. Scaling too quickly can strain operations and
company culture. Maintaining innovation while growing requires careful
management.
"""

# Test Document 4: Climate and Environment
CLIMATE_DOCUMENT = """
Climate Change and Environmental Technology

Climate change represents one of the most significant challenges facing
humanity. Rising global temperatures, caused primarily by greenhouse gas
emissions, threaten ecosystems and human societies worldwide.

Renewable Energy Solutions

Solar power has become increasingly cost-effective, with companies like
Tesla and SunPower developing advanced solar panels and energy storage
systems. Wind energy provides clean electricity generation, with offshore
wind farms expanding rapidly in Europe and Asia.

Tesla's electric vehicles and energy storage products accelerate the
transition away from fossil fuels. Rivian and Lucid Motors compete in the
electric vehicle market with innovative designs and technology.

Carbon Capture and Sequestration

Carbon capture technology removes CO2 from the atmosphere or industrial
processes. Climeworks operates direct air capture facilities in Iceland
and Switzerland. Carbon sequestration stores captured carbon in geological
formations or materials.

Research institutions like MIT and Stanford work on improving carbon
capture efficiency and reducing costs. The technology remains expensive
but shows promise for achieving net-zero emissions.

Sustainable Agriculture

Vertical farming uses controlled environments to grow crops with minimal
water and land use. Companies like AeroFarms and Plenty pioneer this
approach in urban areas. Precision agriculture uses sensors and AI to
optimize crop yields while reducing resource consumption.

Plant-based meat alternatives from companies like Beyond Meat and
Impossible Foods reduce the environmental impact of food production.
Cultured meat grown from cells could eliminate the need for animal
agriculture.

Conservation and Biodiversity

Protecting biodiversity requires preserving natural habitats and
endangered species. Organizations like the World Wildlife Fund and
The Nature Conservancy lead conservation efforts globally. Reforestation
projects restore ecosystems and sequester carbon.

Ocean conservation addresses plastic pollution, overfishing, and coral
reef degradation. Marine protected areas provide safe havens for ocean
life to recover and thrive.

Policy and International Cooperation

The Paris Agreement commits nations to limiting global temperature rise
to well below 2 degrees Celsius. The European Union's Green Deal aims
for carbon neutrality by 2050. The United States rejoined international
climate efforts under President Biden.

Carbon pricing through taxes or cap-and-trade systems creates economic
incentives to reduce emissions. Renewable energy subsidies and fossil
fuel regulations shape energy markets toward sustainability.
"""

# Test queries to verify the knowledge graph
TEST_QUERIES = [
    "What is machine learning?",
    "Which companies work on AI?",
    "Tell me about Git and version control",
    "What are the funding stages for startups?",
    "How does solar power work?",
    "What is carbon capture?",
    "Who founded OpenAI?",
    "Explain Kubernetes",
    "What is Y Combinator?",
    "Tell me about electric vehicles"
]

# Document metadata
DOCUMENTS = [
    {
        "document_id": "tech-ai-ml-001",
        "title": "Artificial Intelligence and Machine Learning Overview",
        "content": TECH_DOCUMENT,
        "metadata": {
            "category": "technology",
            "tags": ["AI", "Machine Learning", "Deep Learning"],
            "author": "Test Suite",
            "date": "2024-01-15"
        }
    },
    {
        "document_id": "software-dev-002",
        "title": "Modern Software Development Practices",
        "content": SOFTWARE_DOCUMENT,
        "metadata": {
            "category": "software engineering",
            "tags": ["DevOps", "Programming", "Cloud"],
            "author": "Test Suite",
            "date": "2024-01-16"
        }
    },
    {
        "document_id": "startup-ecosystem-003",
        "title": "The Modern Startup Ecosystem",
        "content": STARTUP_DOCUMENT,
        "metadata": {
            "category": "business",
            "tags": ["Startups", "Venture Capital", "Entrepreneurship"],
            "author": "Test Suite",
            "date": "2024-01-17"
        }
    },
    {
        "document_id": "climate-environment-004",
        "title": "Climate Change and Environmental Technology",
        "content": CLIMATE_DOCUMENT,
        "metadata": {
            "category": "environment",
            "tags": ["Climate", "Renewable Energy", "Sustainability"],
            "author": "Test Suite",
            "date": "2024-01-18"
        }
    }
]
