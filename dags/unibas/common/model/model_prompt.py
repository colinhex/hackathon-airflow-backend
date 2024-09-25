FEATURES = {
    "intended_audience": [],
    "faculties_departments": [],
    "degree_levels": [],
    "topics": [],
    "information_type": [],
    "keywords": [],
    "entities_mentioned": []
}

INTENDED_AUDIENCE = [
    "Prospective students",
    "Current students",
    "Graduates",
    "International students",
    "PhD candidates",
    "Faculty members",
    "Administrative staff",
    "Alumni",
    "Exchange students",
    "Parents",
    "Researchers",
    "Visiting scholars",
    "High school counselors",
    "University counselors",
    "Employers",
    "General public",
    "Donors",
    "Collaborating institutions",
    "Staff applicants",
    "Online learners"
]

DEPARTMENTS = [
    'Department Arts, Media, Philosophy',
    'Department Biomedicine',
    'Department Biozentrum',
    'Department Clinical Research',
    'Department Public Health (DPH)',
    'Department of Ancient Civilizations',
    'Department of Biomedical Engineering',
    'Department of Chemistry',
    'Department of Environmental Sciences',
    'Department of History',
    'Department of Languages and Literatures',
    'Department of Mathematics and Computer Science',
    'Department of Pharmaceutical Sciences',
    'Department of Physics',
    'Department of Social Sciences',
    'Department of Sport, Exercise and Health'
]


FACULTIES = [
    'Faculty of Business and Economics',
    'Faculty of Humanities and Social Sciences',
    'Faculty of Law',
    'Faculty of Medicine',
    'Faculty of Psychology',
    'Faculty of Science',
    'Faculty of Theology'
]


ADMINISTRATIVE_SERVICES = [
    'Academic Teaching',
    'Accounting',
    'Animal Facilities',
    'Avuba - Assistierendenvereinigung der Universität Basel',
    'Career Advancement',
    'Career Service Center (CSC)',
    'Cash Management',
    'Communications',
    'Communications and Marketing',
    'Continuing-Education Office',
    'Controlling & Reporting',
    'Data Protection',
    'Diversity & Inclusion',
    'Finances',
    'Fundraising',
    'General Secretariat',
    'Grants Office',
    'Human Resources',
    'IT-Services (ITS)',
    'International Office',
    'International Relations',
    'Language Center of the University of Basel',
    'Leadership & Development',
    'Legal Services',
    'Marketing and Event',
    'New Media Center',
    "President's Office and Administration",
    'Program Development',
    'Projects',
    'Quality Development',
    'Research Office',
    'SAP Competence Center',
    'Social Services',
    'Student Administration Office',
    'Student Administration Services',
    'Student Advice Center',
    'Student Exchange',
    'Student Services',
    'Sustainability',
    'Teaching Technology',
    'Unitectra Technologie Transfer',
    'University Archives',
    'University Sports',
    "Vice President's Office for Education",
    "Vice President's Office for Research",
    'Web Services',
    'Welcome & Euraxess Center / Dual Career Advice',
    'sciCORE'
]


DEGREE_LEVELS = [
    "Bachelor",
    "Master",
    "PhD",
    "Postdoctoral",
    "Continuing Education",
    "Certificate Programs",
    "Diploma Programs",
    "Non-degree Programs",
    "Associate Degree",
    "Doctorate",
    "Professional Development"
]

TOPICS = [
    "Admission",
    "Courses",
    "Exams",
    "Life in Basel",
    "Documents",
    "Deadlines",
    "Fees",
    "Registration",
    "Deregistration",
    "Exam Review Process",
    "Final Documents",
    "Diploma",
    "PhD Documents",
    "Requirements",
    "Course Catalog",
    "Mandatory Courses",
    "Optional Courses",
    "Modules",
    "Application Process",
    "Scholarships",
    "Housing",
    "Student Activities",
    "Research Opportunities",
    "Internship Programs",
    "Career Development",
    "Orientation Programs",
    "Health Services",
    "Counseling Services",
    "Financial Aid",
    "Visa Information",
    "Language Courses",
    "Online Learning",
    "Exchange Programs",
    "Accreditation",
    "Faculty Recruitment",
    "Alumni Events",
    "Library Access",
    "IT Support",
    "Campus Safety"
]

INFORMATION_TYPE = [
    "Procedural Information",
    "Requirements",
    "Deadlines",
    "Fees",
    "Course Information",
    "Contact Information",
    "Program Details",
    "Application Instructions",
    "Guidelines",
    "Policies",
    "Event Announcements",
    "News Updates",
    "FAQs",
    "Support Services",
    "Academic Calendar",
    "Workshop Schedules",
    "Seminar Information",
    "Research Publications",
    "Staff Directory",
    "Annual Reports",
    "Strategic Plans",
    "Legal Notices",
    "Alumni News",
    "Job Postings",
    "Press Releases",
    "Sustainability Initiatives"
]

FEATURE_EXTRACTION_PROMPT_INSTRUCTIONS = f"""
You are an assistant that extracts features from a text chunk to help classify university-related information.

**Instructions:**

For each of the enumerated fields below, select all applicable values **only** from the provided lists. Do not invent new categories or include any items not in the lists. If none of the categories apply, leave the list empty.

1. **intended_audience**: Select from the following list:
{INTENDED_AUDIENCE}

2. **departments**: Select from the following list:
{DEPARTMENTS}

3. **faculties**: Select from the following list:
{FACULTIES}

4. **administrative_services**: Select from the following list:
{ADMINISTRATIVE_SERVICES}

3. **degree_levels**: Select from the following list:
{DEGREE_LEVELS}

4. **topics**: Select from the following list:
{TOPICS}

5. **information_type**: Select from the following list:
{INFORMATION_TYPE}

6. **keywords**: List important keywords or phrases from the text (free text).

7. **entities_mentioned**: List specific entities mentioned in the text (e.g., names of documents, programs, courses, offices) (free text).

**Output Format:**

Your output must be a JSON object matching the structure provided in the `FEATURES` dictionary. Ensure that all fields are present in the JSON, even if some lists are empty.
"""


FEATURE_EXTRACTION_PROMPT_SUBJECT_TEXT_CHUNK = """
```chunk
{}
```
"""


def get_feature_extraction_prompt_instructions() -> str:
    return FEATURE_EXTRACTION_PROMPT_INSTRUCTIONS


def get_feature_extraction_prompt_subject(text_chunk: str) -> str:
    return FEATURE_EXTRACTION_PROMPT_SUBJECT_TEXT_CHUNK.format(text_chunk)


def create_feature_extraction_messages(text_chunk: str) -> list:
    return [
        {'role': 'system', 'content': get_feature_extraction_prompt_instructions()},
        {'role': 'user', 'content': get_feature_extraction_prompt_subject(text_chunk)},
    ]
