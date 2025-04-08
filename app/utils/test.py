from app.models.schema import FocusGroup


def create_sample_focus_groups(db):
    """
    Creates and inserts sample FocusGroup records with detailed descriptions and
    elaborate titles focused on employee work-life improvement.
    """
    sample_data = [
        {
            "name": "Work-Life Harmony Initiative",
            "description": "This focus group aims to address the challenges of balancing professional responsibilities with personal life. The group will explore flexible scheduling options, remote work policies, and tools to help employees manage their time efficiently. We'll gather insights on current pain points and develop strategies to reduce burnout while maintaining productivity.",
            "metrics": [
                "work_satisfaction_score",
                "reported_stress_levels",
                "work_hour_flexibility",
                "burnout_index",
            ],
        },
        {
            "name": "Professional Growth & Career Development Pathway",
            "description": "This focus group concentrates on identifying and implementing effective career advancement opportunities within the organization. We'll examine current skill development programs, mentorship opportunities, and create clear pathways for professional growth. The group will assess how career stagnation affects employee engagement and develop solutions to ensure continuous learning and advancement.",
            "metrics": [
                "career_satisfaction",
                "skill_development_rate",
                "internal_promotion_percentage",
                "training_program_effectiveness",
            ],
        },
        {
            "name": "Workplace Connection & Community Building Framework",
            "description": "This focus group explores how to foster meaningful connections between employees in both physical and virtual work environments. We'll analyze current communication patterns, team-building activities, and community initiatives to understand what drives a sense of belonging. The group will develop strategies to combat isolation, especially for remote workers, and create a more cohesive organizational culture.",
            "metrics": [
                "belonging_index",
                "team_cohesion_score",
                "cross-department_collaboration_rate",
                "employee_isolation_levels",
            ],
        },
        {
            "name": "Holistic Wellbeing & Mental Health Support System",
            "description": "This focus group addresses the complete spectrum of employee wellbeing, with special emphasis on mental health. We'll evaluate current wellness programs, identify gaps in support services, and develop comprehensive strategies to promote physical, mental, and emotional health. The group will explore stress management tools, mental health resources, and how the workplace environment impacts overall wellbeing.",
            "metrics": [
                "mental_health_utilization",
                "wellness_program_participation",
                "absenteeism_rate",
                "health_risk_assessment_scores",
            ],
        },
        {
            "name": "Equitable Workplace & Inclusive Culture Development",
            "description": "This focus group examines how to create and maintain an inclusive environment where all employees feel valued and respected. We'll analyze current diversity metrics, inclusion practices, and identify barriers to equity in the workplace. The group will develop actionable strategies to promote diversity, address unconscious bias, and ensure fair treatment and opportunities for all employees regardless of background or identity.",
            "metrics": [
                "inclusion_survey_results",
                "demographic_representation",
                "pay_equity_measurements",
                "promotion_equality_index",
            ],
        },
    ]

    for data in sample_data:
        focus_group = FocusGroup(
            name=data["name"],
            description=data["description"],
            metrics=data["metrics"],
        )
        db.add(focus_group)

    db.commit()
    return "Sample focus group records inserted successfully."
