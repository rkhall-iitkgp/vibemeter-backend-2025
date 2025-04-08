import pandas as pd
import networkx as nx
from google import genai 
from langgraph.graph import StateGraph, END
import os
import json
import numpy as np

# Configure Gemini API
model = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Path to data files
DATA_DIR = "./data"
ACTIVITY_PATH = os.path.join(DATA_DIR, "activity_tracker_dataset.csv")
LEAVE_PATH = os.path.join(DATA_DIR, "leave_dataset.csv")
ONBOARDING_PATH = os.path.join(DATA_DIR, "onboarding_dataset.csv")
PERFORMANCE_PATH = os.path.join(DATA_DIR, "performance_dataset.csv")
REWARDS_PATH = os.path.join(DATA_DIR, "rewards_dataset.csv")
VIBEMETER_PATH = os.path.join(DATA_DIR, "vibemeter_dataset.csv")

# Function to load datasets from CSV files
def load_datasets():
    """Load all datasets from CSV files"""
    try:
        print("Loading activity data...")
        activity_df = pd.read_csv(ACTIVITY_PATH)
        
        print("Loading leave data...")
        leave_df = pd.read_csv(LEAVE_PATH)
        
        print("Loading onboarding data...")
        onboarding_df = pd.read_csv(ONBOARDING_PATH)
        
        print("Loading performance data...")
        performance_df = pd.read_csv(PERFORMANCE_PATH)
        
        print("Loading rewards data...")
        rewards_df = pd.read_csv(REWARDS_PATH)
        
        print("Loading vibemeter data...")
        vibemeter_df = pd.read_csv(VIBEMETER_PATH)
        
        # Convert date columns to datetime where applicable
        date_columns = {
            'leave_df': ['Leave_Start_Date', 'Leave_End_Date'],
            'activity_df': ['Date'],
            'onboarding_df': ['Joining_Date'],
            'vibemeter_df': ['Response_Date'],
            'rewards_df': ['Award_Date']
        }
        
        for df_name, columns in date_columns.items():
            df = locals()[df_name]
            for col in columns:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    except Exception as e:
                        print(f"Warning: Could not convert {col} in {df_name} to datetime: {e}")
        
        print("All datasets loaded successfully!")
        return activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df
    
    except FileNotFoundError as e:
        print(f"Error: Dataset file not found - {e}")
        raise
    except pd.errors.EmptyDataError:
        print(f"Error: One of the CSV files is empty")
        raise
    except pd.errors.ParserError:
        print(f"Error: Could not parse CSV file - check file format")
        raise
    except Exception as e:
        print(f"Unexpected error loading datasets: {e}")
        raise

# Define the state schema - add a get method to make it dict-like
class AgentState:
    def __init__(self):
        self.employee_id = None
        self.knowledge_graph = None
        self.issues = []
        self.conversation_history = []
        self.recommendations = []
        self.report = None
    
    # Add a get method to make it dict-like
    def get(self, key, default=None):
        return getattr(self, key, default)

# 1. Graph Builder Agent
class GraphBuilderAgent:
    def __init__(self, activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df):
        self.activity_df = activity_df
        self.leave_df = leave_df
        self.onboarding_df = onboarding_df
        self.performance_df = performance_df
        self.rewards_df = rewards_df
        self.vibemeter_df = vibemeter_df
        
    def build_knowledge_graph(self, employee_id):
        # Create an empty graph
        G = nx.Graph()
        
        # Add employee node
        G.add_node(employee_id, type='employee')
        
        # Process VibeMeter data
        employee_vibes = self.vibemeter_df[self.vibemeter_df['Employee_ID'] == employee_id]
        vibe_scores = list(employee_vibes['Vibe_Score'])
        vibe_dates = list(employee_vibes['Response_Date'])
        
        # Calculate vibe trend
        vibe_trend = 'stable'
        if len(vibe_scores) > 3:
            recent_vibes = vibe_scores[-3:]
            if all(recent_vibes[i] < recent_vibes[i-1] for i in range(1, len(recent_vibes))):
                vibe_trend = 'declining'
            elif all(recent_vibes[i] > recent_vibes[i-1] for i in range(1, len(recent_vibes))):
                vibe_trend = 'improving'
        
        # Add vibe node
        G.add_node(f"{employee_id}_vibe", type='vibe', scores=vibe_scores, trend=vibe_trend)
        G.add_edge(employee_id, f"{employee_id}_vibe", relation='has_vibe')
        
        # Process Activity data
        employee_activity = self.activity_df[self.activity_df['Employee_ID'] == employee_id]
        
        if not employee_activity.empty:
            recent_activities = employee_activity.sort_values('Date', ascending=False).head(10)
            avg_work_hours = recent_activities['Work_Hours'].mean()
            avg_messages = recent_activities['Teams_Messages_Sent'].mean()
            avg_emails = recent_activities['Emails_Sent'].mean()
            avg_meetings = recent_activities['Meetings_Attended'].mean()
            
            # Add activity node
            G.add_node(f"{employee_id}_activity", 
                      type='activity', 
                      avg_work_hours=avg_work_hours,
                      avg_messages=avg_messages,
                      avg_emails=avg_emails,
                      avg_meetings=avg_meetings)
            G.add_edge(employee_id, f"{employee_id}_activity", relation='has_activity')
        
        # Process Leave data
        employee_leaves = self.leave_df[self.leave_df['Employee_ID'] == employee_id]
        
        if not employee_leaves.empty:
            leave_count = len(employee_leaves)
            leave_days_total = employee_leaves['Leave_Days'].sum()
            leave_types = employee_leaves['Leave_Type'].value_counts().to_dict()
            
            # Add leave node
            G.add_node(f"{employee_id}_leave", 
                      type='leave', 
                      leave_count=leave_count,
                      leave_days_total=leave_days_total,
                      leave_types=leave_types)
            G.add_edge(employee_id, f"{employee_id}_leave", relation='has_leave')
        
        # Process Performance data
        employee_performance = self.performance_df[self.performance_df['Employee_ID'] == employee_id]
        
        if not employee_performance.empty:
            recent_performance = employee_performance.sort_values('Review_Period', ascending=False).iloc[0]
            rating = recent_performance['Performance_Rating']
            feedback = recent_performance['Manager_Feedback']
            promotion = recent_performance['Promotion_Consideration']
            
            # Add performance node
            G.add_node(f"{employee_id}_performance", 
                      type='performance', 
                      rating=rating,
                      feedback=feedback,
                      promotion=promotion)
            G.add_edge(employee_id, f"{employee_id}_performance", relation='has_performance')
        
        # Process Rewards data
        employee_rewards = self.rewards_df[self.rewards_df['Employee_ID'] == employee_id]
        
        if not employee_rewards.empty:
            reward_count = len(employee_rewards)
            reward_types = employee_rewards['Award_Type'].value_counts().to_dict()
            rewards_points = employee_rewards['Reward_Points'].sum()
            
            # Add rewards node
            G.add_node(f"{employee_id}_rewards", 
                      type='rewards', 
                      reward_count=reward_count,
                      reward_types=reward_types,
                      rewards_points=rewards_points)
            G.add_edge(employee_id, f"{employee_id}_rewards", relation='has_rewards')
        
        # Process Onboarding data
        employee_onboarding = self.onboarding_df[self.onboarding_df['Employee_ID'] == employee_id]
        
        if not employee_onboarding.empty:
            onboarding_data = employee_onboarding.iloc[0]
            joining_date = onboarding_data['Joining_Date']
            feedback = onboarding_data['Onboarding_Feedback']
            mentor = onboarding_data['Mentor_Assigned']
            training = onboarding_data['Initial_Training_Completed']
            
            # Add onboarding node
            G.add_node(f"{employee_id}_onboarding", 
                      type='onboarding', 
                      joining_date=joining_date,
                      feedback=feedback,
                      mentor=mentor,
                      training=training)
            G.add_edge(employee_id, f"{employee_id}_onboarding", relation='has_onboarding')
        
        return G
    
    def identify_issues(self, G, employee_id):
        issues = []
        
        # Check for vibe issues
        if f"{employee_id}_vibe" in G.nodes:
            vibe_node = G.nodes[f"{employee_id}_vibe"]
            if vibe_node['trend'] == 'declining':
                issues.append({
                    'type': 'vibe',
                    'severity': 'high',
                    'description': 'Declining vibe scores in recent surveys'
                })
            
            # Check for consistently low vibe scores
            vibe_scores = vibe_node['scores']
            if vibe_scores and sum(s < 5 for s in vibe_scores) / len(vibe_scores) > 0.5:
                issues.append({
                    'type': 'vibe',
                    'severity': 'high',
                    'description': 'Consistently low vibe scores (below 5)'
                })
        
        # Check for workload issues
        if f"{employee_id}_activity" in G.nodes:
            activity_node = G.nodes[f"{employee_id}_activity"]
            if activity_node['avg_work_hours'] > 9:
                issues.append({
                    'type': 'workload',
                    'severity': 'medium',
                    'description': f'High average working hours: {activity_node["avg_work_hours"]:.1f} hours'
                })
            if activity_node['avg_meetings'] > 5:
                issues.append({
                    'type': 'workload',
                    'severity': 'medium',
                    'description': f'High number of meetings: {activity_node["avg_meetings"]:.1f} per day'
                })
        
        # Check for performance issues
        if f"{employee_id}_performance" in G.nodes:
            performance_node = G.nodes[f"{employee_id}_performance"]
            if performance_node['rating'] < 3:
                issues.append({
                    'type': 'performance',
                    'severity': 'high',
                    'description': f'Low performance rating: {performance_node["rating"]}'
                })
            if performance_node['promotion'] == 'No':
                issues.append({
                    'type': 'career',
                    'severity': 'medium',
                    'description': 'Not considered for promotion'
                })
        
        # Check for reward issues
        if f"{employee_id}_rewards" in G.nodes and f"{employee_id}_performance" in G.nodes:
            rewards_node = G.nodes[f"{employee_id}_rewards"]
            performance_node = G.nodes[f"{employee_id}_performance"]
            
            if performance_node['rating'] >= 4 and rewards_node['reward_count'] == 0:
                issues.append({
                    'type': 'recognition',
                    'severity': 'medium',
                    'description': 'High performer with no rewards'
                })
        
        # Check for leave patterns
        if f"{employee_id}_leave" in G.nodes:
            leave_node = G.nodes[f"{employee_id}_leave"]
            if leave_node['leave_count'] > 10:
                issues.append({
                    'type': 'attendance',
                    'severity': 'medium',
                    'description': f'High leave count: {leave_node["leave_count"]} instances'
                })
            
            # Check for frequent sick leaves
            leave_types = leave_node.get('leave_types', {})
            sick_leaves = leave_types.get('Sick', 0)
            if sick_leaves > 5:
                issues.append({
                    'type': 'health',
                    'severity': 'medium',
                    'description': f'Frequent sick leaves: {sick_leaves} instances'
                })
        
        # Check for onboarding issues
        if f"{employee_id}_onboarding" in G.nodes:
            onboarding_node = G.nodes[f"{employee_id}_onboarding"]
            
            if onboarding_node['training'] == 'No':
                issues.append({
                    'type': 'training',
                    'severity': 'low',
                    'description': 'Initial training not completed'
                })
                
            if 'negative' in str(onboarding_node['feedback']).lower():
                issues.append({
                    'type': 'onboarding',
                    'severity': 'medium',
                    'description': 'Negative onboarding feedback'
                })
        
        return issues
    
    def run(self, employee_id):
        # Build knowledge graph
        G = self.build_knowledge_graph(employee_id)
        
        # Identify potential issues
        issues = self.identify_issues(G, employee_id)
        
        return G, issues

# Enhanced ChatbotAgent with intelligent question generation and response analysis
class ChatbotAgent:
    def __init__(self):
        # Base templates revised to reference specific data fields from datasets
        self.question_templates = {
            'vibe': "I noticed your recent vibe scores in our surveys show {issue_description}. What workplace factors might be affecting this?",
            
            'workload': "Your activity data shows {issue_description}. How is this affecting your work-life balance?",
            
            'performance': "In your last performance review, {issue_description}. What obstacles are you facing in meeting your goals?",
            
            'career': "According to your records, {issue_description}. What do you feel is limiting your career progression here?",
            
            'recognition': "Looking at your rewards history, {issue_description}. How does the recognition system affect your motivation?",
            
            'attendance': "Your leave records show {issue_description}. What workplace factors influence your attendance patterns?",
            
            'health': "Your sick leave data indicates {issue_description}. Are there workplace conditions affecting your wellbeing?",
            
            'training': "Records show {issue_description} regarding your initial training. What additional training would be valuable?",
            
            'onboarding': "Your onboarding records indicate {issue_description}. How could we have improved your initial experience?"
        }
        
        self.conversation = []
        self.current_issues = []
        self.explored_issues = {}  # Track issues and their identified root causes
        self.current_issue_index = 0
        self.follow_up_count = 0
        self.max_follow_ups = 3
        
        # Track identified root causes
        self.root_causes = {}
        # Track themes across issues
        self.themes = set()
        # Track potential solutions for issues
        self.potential_solutions = {}

    def start_conversation(self, issues):
        """Initialize a new conversation focused on discovering root causes and providing solutions"""
        self.conversation = []
        # Sort issues by severity
        self.current_issues = sorted(issues, key=lambda x: {
            'high': 0,
            'medium': 1,
            'low': 2
        }[x['severity']])
        
        self.explored_issues = {issue['type']: {'explored': False, 'root_causes': []} for issue in self.current_issues}
        self.current_issue_index = 0
        self.follow_up_count = 0
        self.root_causes = {}
        self.themes = set()
        self.potential_solutions = {}  # New: track potential solutions for issues
        
        # Create a comprehensive system prompt that includes all issues
        issue_context = ""
        for issue in self.current_issues:
            issue_context += f"- {issue['type'].capitalize()}: {issue['description']}\n"
        
        # Generate supportive, solution-oriented greeting
        greeting_prompt = f"""
        You are a supportive, solution-oriented HR chatbot having a conversation with an employee.
        
        The employee has these potential areas to discuss:
        {issue_context}
        
        Generate a warm, empathetic greeting that:
        1. Welcomes the employee and expresses genuine interest in helping them
        2. Mentions you're here to understand their challenges AND find solutions together
        3. Conveys a supportive, problem-solving attitude
        4. Notes they can type /exit anytime to end the conversation
        
        The greeting should be friendly, supportive and under 3 sentences.
        """
        
        response = model.models.generate_content(
            contents=greeting_prompt,
            model="gemini-2.0-flash"
        )
        
        greeting = response.text.strip() if response.text else "Hi there! I'm here to chat about how things are going and find solutions that can help improve your work experience. You can type /exit anytime to end our conversation."
        
        self.conversation.append({
            "role": "assistant",
            "content": greeting
        })
        
        return greeting

    def generate_question(self, conversation_history=None):
        """Generate a helpful, solution-oriented question that's concise"""
        if conversation_history is None:
            conversation_history = []
        
        # Convert conversation history to a readable format for the prompt
        history_text = ""
        if conversation_history:
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-3:]])
        
        # Get information about current and unexplored issues
        current_issue = self.current_issues[self.current_issue_index] if self.current_issue_index < len(self.current_issues) else None
        unexplored_issues = [issue for issue in self.current_issues if not self.explored_issues[issue['type']]['explored']]
        
        # Create a context-aware prompt that emphasizes helpfulness and brevity
        if not history_text:
            # First question - start with high priority issue
            issue_type = current_issue['type']
            issue_description = current_issue['description']
            
            prompt = f"""
            You're a supportive, solution-oriented HR chatbot starting a conversation about {issue_type} ({issue_description}).
            
            Generate a brief, helpful question that:
            1. Is under 15 words but shows genuine interest in helping
            2. Feels natural and empathetic 
            3. Encourages them to share challenges so you can help find solutions
            4. Doesn't directly state that you identified an issue
            
            Write only the question itself, with no additional text.
            """
        else:
            # Follow-up or transition question
            prompt = f"""
            You're a supportive, solution-oriented HR chatbot continuing a conversation.
            
            RECENT CONVERSATION:
            {history_text}
            
            UNEXPLORED ISSUES: {[f"{i['type']}: {i['description']}" for i in unexplored_issues[:2]]}
            
            Generate a brief, helpful follow-up question that:
            1. Is under 15 words but shows genuine interest in helping solve their issues
            2. Naturally builds on their last response
            3. Explores potential solutions or ways you can help them
            4. Makes them feel supported and understood
            
            Write only the question itself, with no additional text.
            """
        
        try:
            response = model.models.generate_content(
                contents=prompt,
                model="gemini-2.0-flash"
            )
            return response.text.strip()
        except Exception as e:
            print(f"Error generating question: {e}")
            # Fallback to a simple but helpful question
            return "How can I help with this challenge you're facing?"

    def analyze_response(self, user_input, recent_conversation):
        """
        Analyze user response to identify root causes, themes, potential solutions
        """
        # Convert recent conversation to text for the prompt
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_conversation])
        
        # Get the current issue and all issues
        current_issue = self.current_issues[self.current_issue_index] if self.current_issue_index < len(self.current_issues) else None
        all_issues_text = "\n".join([f"- {issue['type']}: {issue['description']}" for issue in self.current_issues])
        
        # Prepare prompt for analysis that includes solutions
        analysis_prompt = f"""
        You are an HR analytics expert analyzing an employee's response about workplace issues.
        
        CURRENT CONVERSATION:
        {conversation_text}
        
        POTENTIAL ISSUES:
        {all_issues_text}
        
        CURRENTLY FOCUSED ISSUE: {current_issue['type'] if current_issue else 'None'} - {current_issue['description'] if current_issue else ''}
        
        Based on the employee's latest response, analyze:
        
        1. ROOT_CAUSES: What specific root causes did they mention for any issues? (Map issue types to lists of causes)
        2. THEMES: What broader themes emerged (work-life balance, communication, etc.)?
        3. POTENTIAL_SOLUTIONS: What specific solutions could help address the issues mentioned? (Map issue types to lists of solutions)
        4. SUFFICIENT_DEPTH: Has the current issue been explored sufficiently? (yes/no)
        5. SENTIMENT: What's the employee's sentiment about each issue mentioned? (Map issue types to sentiment)
        
        Format your response as JSON with these 5 keys.
        """
        
        try:
            response = model.models.generate_content(
                contents=analysis_prompt,
                model="gemini-2.0-flash"
            )
            
            # Clean and parse the response
            analysis_text = response.text
            analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()
            
            try:
                analysis = json.loads(analysis_text)
                
                # Update root causes based on analysis - with type checking
                if "ROOT_CAUSES" in analysis and isinstance(analysis["ROOT_CAUSES"], dict):
                    for issue_type, causes in analysis["ROOT_CAUSES"].items():
                        if issue_type not in self.root_causes:
                            self.root_causes[issue_type] = []
                        
                        # If causes is a list, extend our list with it
                        if isinstance(causes, list):
                            for cause in causes:
                                if cause not in self.root_causes[issue_type]:
                                    self.root_causes[issue_type].append(cause)
                        # If it's a string, add it as a single cause
                        elif isinstance(causes, str):
                            if causes not in self.root_causes[issue_type]:
                                self.root_causes[issue_type].append(causes)
                
                # Update themes - with type checking
                if "THEMES" in analysis and isinstance(analysis["THEMES"], list):
                    for theme in analysis["THEMES"]:
                        self.themes.add(theme)
                
                # Store potential solutions - with type checking
                if "POTENTIAL_SOLUTIONS" in analysis and isinstance(analysis["POTENTIAL_SOLUTIONS"], dict):
                    for issue_type, solutions in analysis["POTENTIAL_SOLUTIONS"].items():
                        if issue_type not in self.potential_solutions:
                            self.potential_solutions[issue_type] = []
                        
                        # If solutions is a list, extend our list with it
                        if isinstance(solutions, list):
                            for solution in solutions:
                                if solution not in self.potential_solutions[issue_type]:
                                    self.potential_solutions[issue_type].append(solution)
                        # If it's a string, add it as a single solution
                        elif isinstance(solutions, str):
                            if solutions not in self.potential_solutions[issue_type]:
                                self.potential_solutions[issue_type].append(solutions)
                
                # Store sentiment data - with type checking
                if "SENTIMENT" in analysis and isinstance(analysis["SENTIMENT"], dict):
                    if not hasattr(self, 'sentiment_data'):
                        self.sentiment_data = {}
                    
                    for issue_type, sentiment in analysis["SENTIMENT"].items():
                        if issue_type not in self.sentiment_data:
                            self.sentiment_data[issue_type] = []
                        self.sentiment_data[issue_type].append(sentiment)
                
                # Check for sufficient depth with fallback
                sufficient_depth = "no"
                if "SUFFICIENT_DEPTH" in analysis:
                    sufficient_depth = analysis["SUFFICIENT_DEPTH"].lower() if isinstance(analysis["SUFFICIENT_DEPTH"], str) else "no"
                
                # Mark the current issue as explored if sufficient depth achieved
                current_issue = self.current_issues[self.current_issue_index] if self.current_issue_index < len(self.current_issues) else None
                if current_issue and sufficient_depth == "yes":
                    self.explored_issues[current_issue['type']]['explored'] = True
                    self.explored_issues[current_issue['type']]['root_causes'] = self.root_causes.get(current_issue['type'], [])
                
                return analysis
                    
            except json.JSONDecodeError as e:
                print(f"Warning: JSON parsing error in analyze_response: {e}")
                # Default analysis if JSON parsing fails
                return {
                    "ROOT_CAUSES": {},
                    "THEMES": [],
                    "POTENTIAL_SOLUTIONS": {},
                    "SUFFICIENT_DEPTH": "no",
                    "SENTIMENT": {}
                }
                    
        except Exception as e:
            print(f"Warning: Error analyzing response: {e}")
            # Default analysis
            return {
                "ROOT_CAUSES": {},
                "THEMES": [],
                "POTENTIAL_SOLUTIONS": {},
                "SUFFICIENT_DEPTH": "no",
                "SENTIMENT": {}
            }

    def generate_findings_summary(self):
        """Generate a summary of findings about root causes and themes from conversation"""
        # If no root causes were identified, return empty string
        if not self.root_causes and not self.themes:
            conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation])
            issues_text = "\n".join([f"- {issue['type']}: {issue['description']}" for issue in self.current_issues])
            
            summary_prompt = f"""
            Review this conversation about workplace issues:

            ISSUES:
            {issues_text}

            CONVERSATION:
            {conversation_text}

            Generate a brief, insightful summary of:
            1. Root causes for the issues mentioned
            2. Common themes across issues
            
            Format as a concise markdown summary with bullet points. Be specific and helpful.
            """
            
            try:
                response = model.models.generate_content(
                    contents=summary_prompt,
                    model="gemini-2.0-flash"
                )
                return response.text.strip()
            except Exception:
                return "No clear findings were identified in our conversation."
        
        # Process identified root causes and themes
        summary_text = "# Key Findings\n\n"
        
        for issue_type, causes in self.root_causes.items():
            if causes:
                issue_data = next((i for i in self.current_issues if i['type'] == issue_type), None)
                description = issue_data['description'] if issue_data else issue_type
                
                summary_text += f"## {issue_type.capitalize()}\n"
                summary_text += f"*{description}*\n\n"
                for cause in causes:
                    summary_text += f"- {cause}\n"
                summary_text += "\n"
        
        if self.themes:
            summary_text += "## Common Themes\n"
            for theme in self.themes:
                summary_text += f"- {theme}\n"
                
        return summary_text

    def generate_solution_summary(self):
        """Generate a helpful summary of potential solutions to address the identified issues"""
        # If no potential solutions were identified, generate basic recommendations
        if not self.potential_solutions and not self.root_causes:
            conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation])
            issues_text = "\n".join([f"- {issue['type']}: {issue['description']}" for issue in self.current_issues])
            
            solution_prompt = f"""
            You are an HR chatbot providing practical recommendations to an employee.
            
            Review this conversation about workplace issues:

            ISSUES:
            {issues_text}

            CONVERSATION:
            {conversation_text}

            Generate 2-3 practical, supportive recommendations that:
            1. Address the employee's main concerns
            2. Offer actionable steps they can take 
            3. Include ways the company can support them
            
            FORMAT REQUIREMENTS:
            - Use brief, supportive bullet points
            - Be specific and empathetic
            - Do NOT include any analysis of the conversation
            - Do NOT suggest multiple options or alternatives for wording
            - Provide ONLY the final recommendations
            - Do NOT explain your thinking process
            """
            
            try:
                response = model.models.generate_content(
                    contents=solution_prompt,
                    model="gemini-2.0-flash"
                )
                # Check if response contains any analysis markers and remove them
                result = response.text.strip()
                if "option" in result.lower() or "options" in result.lower():
                    # If the model is providing options, try to extract just the recommendations
                    result = "Based on our conversation, here are some recommendations:\n\n• Schedule a meeting with your manager to discuss workload concerns\n• Consider documenting specific examples of challenges you're facing\n• Explore our company's well-being resources for additional support"
                return result
            except Exception:
                return "Based on our conversation, I recommend discussing your concerns with your manager and considering time management strategies that could help reduce stress."
        
        # Process identified solutions and root causes with clearer instructions
        prompt = f"""
        You are an HR chatbot providing specific recommendations to an employee.

        Create supportive, practical recommendations based on:

        ROOT CAUSES:
        {json.dumps(self.root_causes, indent=2)}
        
        POTENTIAL SOLUTIONS:
        {json.dumps(self.potential_solutions, indent=2)}
        
        ISSUES:
        {[{'type': issue['type'], 'description': issue['description']} for issue in self.current_issues]}

        INSTRUCTIONS:
        1. Generate 3-4 specific, actionable recommendations
        2. Include both employee actions and company support options
        3. Format as brief, clear bullet points
        4. Be specific and practical with no fluff
        5. Do NOT include any analysis, explanations or multiple options
        6. Do NOT show your reasoning process
        7. Provide ONLY the final recommendation text
        """
        
        try:
            response = model.models.generate_content(
                contents=prompt,
                model="gemini-2.0-flash"
            )
            # Verify the response doesn't contain option listings
            result = response.text.strip()
            if "option" in result.lower() or "**option" in result.lower():
                # Fallback to basic solution format
                solution_text = "Based on our conversation, here are some recommendations:\n\n"
                for issue_type, solutions in self.potential_solutions.items():
                    if solutions:
                        issue_data = next((i for i in self.current_issues if i['type'] == issue_type), None)
                        if issue_data and solutions[0]:
                            solution_text += f"• For {issue_data['description'].lower()}: {solutions[0]}\n"
                return solution_text
            
            return result
        except Exception:
            # Fallback to basic solution summary
            solution_text = "Based on our conversation, here are some recommendations:\n\n"
            
            for issue_type, solutions in self.potential_solutions.items():
                if solutions:
                    issue_data = next((i for i in self.current_issues if i['type'] == issue_type), None)
                    if issue_data and solutions[0]:
                        solution_text += f"• For {issue_data['description'].lower()}: {solutions[0]}\n"
                    
            return solution_text

    def run(self, issues):
        """
        Run an interactive conversation about the identified issues
        
        Args:
            issues: List of issue dictionaries identified for the employee
        
        Returns:
            List of conversation messages
        """
        # Start conversation with greeting
        greeting = self.start_conversation(issues)
        print(f"Assistant: {greeting}")
        
        # Continue conversation until all issues are explored or user exits
        conversation_complete = False
        while not conversation_complete:
            # Get user input
            user_input = input("You: ")
            
            # Check for exit command
            if user_input.strip().lower() == "/exit":
                farewell = "Thank you for your time. Let me share some suggestions based on our conversation before you go."
                solution_summary = self.generate_solution_summary()
                combined_message = f"{farewell}\n\n{solution_summary}"
                
                self.conversation.append({
                    "role": "assistant",
                    "content": combined_message
                })
                print(f"Assistant: {combined_message}")
                break
            
            # Add user input to conversation history
            self.conversation.append({
                "role": "user",
                "content": user_input
            })
            
            # Analyze the response
            analysis = self.analyze_response(user_input, self.conversation[-4:])
            
            # Move to next issue if current one is sufficiently explored
            if self.current_issue_index < len(self.current_issues):
                current_issue = self.current_issues[self.current_issue_index]
                sufficient_depth = analysis.get("SUFFICIENT_DEPTH", "no").lower() == "yes"
                
                if sufficient_depth or self.follow_up_count >= self.max_follow_ups:
                    # Mark current issue as explored
                    if current_issue:
                        self.explored_issues[current_issue['type']]['explored'] = True
                    
                    # Move to next issue
                    self.current_issue_index += 1
                    self.follow_up_count = 0
                else:
                    # Continue with follow-up questions on current issue
                    self.follow_up_count += 1
            
            # Check if all issues have been explored
            all_explored = all(data['explored'] for data in self.explored_issues.values())
            
            # Generate next question or wrap up
            if all_explored or self.current_issue_index >= len(self.current_issues):
                
                # Generate solutions based on the conversation (NEW)
                solutions = self.generate_solution_summary()
                
                # Create a helpful closing message with solutions
                closing_message = f"""Thank you for sharing your thoughts and experiences. Based on our conversation, I have some suggestions that might help:

{solutions}

I hope these recommendations are helpful. Your feedback is valuable and will help us create better workplace solutions."""

                self.conversation.append({
                    "role": "assistant",
                    "content": closing_message
                })
                print(f"Assistant: {closing_message}")

                conversation_complete = True
            else:
                # Generate next question based on updated conversation history
                next_question = self.generate_question(self.conversation[-6:])
                
                # Add to conversation
                self.conversation.append({
                    "role": "assistant",
                    "content": next_question
                })
                print(f"Assistant: {next_question}")
        
        return self.conversation

# 3. Report Generator Agent
class ReportGeneratorAgent:
    def __init__(self):
        pass
    
    def generate_report(self, employee_id, knowledge_graph, issues, conversation):
        """Generate a structured employee report based on knowledge graph and conversation"""
        # Convert the knowledge graph to a dictionary format for easier analysis
        graph_data = self.graph_to_dict(knowledge_graph)
        
        # Extract key metrics from the graph
        metrics = self.extract_metrics(graph_data, employee_id)
        
        # Process conversation to extract key insights
        # Convert conversation to plain text format for analysis
        conversation_text = ""
        for msg in conversation:
            if msg["role"] == "user":
                conversation_text += f"Employee: {msg['content']}\n"
            else:
                conversation_text += f"HR Bot: {msg['content']}\n"
        
        # Prepare structured report prompt
        prompt = f"""
        Generate a professional HR report for employee {employee_id} based on the following data.
        
        KEY METRICS:
        {json.dumps(metrics, indent=2)}
        
        IDENTIFIED ISSUES:
        {json.dumps(issues, indent=2)}
        
        CONVERSATION INSIGHTS:
        {conversation_text[:2000]}  
        
        FORMAT THE REPORT WITH THESE SECTIONS:
        1. Executive Summary (3-4 sentences overview)
        2. Key Metrics Analysis (bullet points of important metrics)
        3. Primary Issues Identified (bullet points)
        4. Root Causes (based on conversation)
        5. Recommended Actions (3-5 specific recommendations)
        
        The report should be factual, professional, and action-oriented. No fluff or filler content.
        """
        
        try:
            response = model.models.generate_content(
                contents=prompt,
                model="gemini-2.0-flash"
            )
            return response.text
        except Exception as e:
            print(f"Error generating report content: {e}")
            return f"Error generating report for employee {employee_id}: {str(e)}"
    
    def graph_to_dict(self, G):
        result = {}
        for node in G.nodes:
            result[node] = dict(G.nodes[node])
        return result
    
    def extract_metrics(self, graph_data, employee_id):
        metrics = {}
        
        # Extract vibe metrics
        vibe_node = graph_data.get(f"{employee_id}_vibe", {})
        if vibe_node:
            vibe_scores = vibe_node.get('scores', [])
            metrics['average_vibe'] = sum(vibe_scores) / len(vibe_scores) if vibe_scores else 0
            metrics['vibe_trend'] = vibe_node.get('trend', 'unknown')
        
        # Extract activity metrics
        activity_node = graph_data.get(f"{employee_id}_activity", {})
        if activity_node:
            metrics['avg_work_hours'] = activity_node.get('avg_work_hours', 0)
            metrics['avg_meetings'] = activity_node.get('avg_meetings', 0)
            metrics['avg_messages'] = activity_node.get('avg_messages', 0)
            metrics['avg_emails'] = activity_node.get('avg_emails', 0)
        
        # Extract performance metrics
        performance_node = graph_data.get(f"{employee_id}_performance", {})
        if performance_node:
            metrics['performance_rating'] = performance_node.get('rating', 0)
            metrics['promotion_consideration'] = performance_node.get('promotion', 'unknown')
        
        # Extract leave metrics
        leave_node = graph_data.get(f"{employee_id}_leave", {})
        if leave_node:
            metrics['leave_count'] = leave_node.get('leave_count', 0)
            metrics['leave_days_total'] = leave_node.get('leave_days_total', 0)
            metrics['leave_types'] = leave_node.get('leave_types', {})
        
        # Extract rewards metrics
        rewards_node = graph_data.get(f"{employee_id}_rewards", {})
        if rewards_node:
            metrics['reward_count'] = rewards_node.get('reward_count', 0)
            metrics['rewards_points'] = rewards_node.get('rewards_points', 0)
        
        # Convert any NumPy types to native Python types
        for key, value in metrics.items():
            if isinstance(value, (np.integer, np.int64)):
                metrics[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                metrics[key] = float(value)
            elif isinstance(value, dict):
                # Handle nested dictionaries (like leave_types)
                for k, v in value.items():
                    if isinstance(v, (np.integer, np.int64)):
                        metrics[key][k] = int(v)
                    elif isinstance(v, (np.floating, np.float64)):
                        metrics[key][k] = float(v)
        
        return metrics
    
    def run(self, employee_id, knowledge_graph, issues, conversation_history):
        # Generate the report
        report = self.generate_report(employee_id, knowledge_graph, issues, conversation_history)
        
        # Save the report to a file
        report_filename = f"emp_{employee_id}_report.txt"
        with open(report_filename, "w") as f:
            f.write(report)
        
        print(f"Report saved to {report_filename}")
        
        return report

# Define the LangGraph workflow
def build_workflow(activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df):
    # Initialize agents
    graph_builder = GraphBuilderAgent(
        activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df
    )
    chatbot = ChatbotAgent()
    report_generator = ReportGeneratorAgent()
    
    # Define node functions
    def build_graph(state):
        employee_id = state.get('employee_id')
        knowledge_graph, issues = graph_builder.run(employee_id)
        
        return {
            'employee_id': employee_id,
            'knowledge_graph': knowledge_graph,
            'issues': issues
        }
    
    def conduct_conversation(state):
        issues = state.get('issues', [])
        conversation_history = chatbot.run(issues)
        
        return {
            'conversation_history': conversation_history
        }
    
    def generate_report(state):
        employee_id = state.get('employee_id')
        knowledge_graph = state.get('knowledge_graph')
        issues = state.get('issues', [])
        conversation_history = state.get('conversation_history', [])
        
        report = report_generator.run(employee_id, knowledge_graph, issues, conversation_history)
        
        return {
            'report': report
        }
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("build_graph", build_graph)
    workflow.add_node("conduct_conversation", conduct_conversation)
    workflow.add_node("generate_report", generate_report)
    
    # Add edges
    workflow.add_edge("build_graph", "conduct_conversation")
    workflow.add_edge("conduct_conversation", "generate_report")
    workflow.add_edge("generate_report", END)
    
    # Set the entry point
    workflow.set_entry_point("build_graph")
    
    return workflow.compile()

# Function to run the entire workflow
def run_hr_analysis(employee_id, activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df):
    # Build the workflow
    workflow = build_workflow(
        activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df
    )
    
    # Run the workflow
    result = workflow.invoke({
        "employee_id": employee_id
    })
    
    return result

activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df = load_datasets()

# Create the agents directly for better error handling
graph_builder = GraphBuilderAgent(
    activity_df, leave_df, onboarding_df, performance_df, rewards_df, vibemeter_df
)

# Example usage
def main():
    # Load datasets
    try:
        # Run the analysis for an employee
        employee_id = 'EMP0387'
        chatbot = ChatbotAgent()
        report_generator = ReportGeneratorAgent()
        
        # Build knowledge graph and identify issues
        knowledge_graph, issues = graph_builder.run(employee_id)
        
        print(f"Found {len(issues)} potential issues for Employee {employee_id}")
        print("Starting interactive conversation...\n")
        
        # Run interactive conversation
        conversation = chatbot.run(issues)
        
        print("\nConversation complete! Generating report...")
        
        # Generate and save report
        report = report_generator.run(employee_id, knowledge_graph, issues, conversation)
        
        print(f"Successfully generated report for employee {employee_id}")
        
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()  # This will help identify where the error is occurring

if __name__ == "__main__":
    main()
