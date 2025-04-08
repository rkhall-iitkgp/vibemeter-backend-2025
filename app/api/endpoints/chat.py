from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ml.chatbot import graph_builder, ChatbotAgent,ReportGeneratorAgent
from app.models.schema import EmployeeReport
from app.utils.db import get_db
from app.socket import manager

router = APIRouter()


@router.websocket("/{user_id}")
async def chat(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)

    knowledge_graph, issues = graph_builder.run(user_id)
    agent = ChatbotAgent()
    report_generator = ReportGeneratorAgent()
    greeting = agent.start_conversation(issues)
    await manager.send_message(greeting, user_id)

    print(f"Found {len(issues)} potential issues for Employee {user_id}")
    print("Starting interactive conversation...\n")

    conversation_complete = False

    try:
        while not conversation_complete:
            print("Waiting for user input...")
            data = await websocket.receive_text()
            agent.conversation.append({"role": "user", "content": data})
            analysis = agent.analyze_response(data, agent.conversation[-10:])

            if agent.current_issue_index < len(agent.current_issues):
                current_issue = agent.current_issues[agent.current_issue_index]
                sufficient_depth = (
                    analysis.get("SUFFICIENT_DEPTH", "no").lower() == "yes"
                )

                if sufficient_depth or agent.follow_up_count >= agent.max_follow_ups:
                    # Mark current issue as explored
                    if current_issue:
                        agent.explored_issues[current_issue["type"]]["explored"] = True

                    # Move to next issue
                    agent.current_issue_index += 1
                    agent.follow_up_count = 0
                else:
                    # Continue with follow-up questions on current issue
                    agent.follow_up_count += 1

            # Check if all issues have been explored
            all_explored = all(
                data["explored"] for data in agent.explored_issues.values()
            )
            if all_explored or agent.current_issue_index >= len(agent.current_issues):

                # Generate solutions based on the conversation (NEW)
                solutions = agent.generate_solution_summary()

                # Create a helpful closing message with solutions
                closing_message = f"""Thank you for sharing your thoughts and experiences. Based on our conversation, I have some suggestions that might help:

{solutions}

I hope these recommendations are helpful. Your feedback is valuable and will help us create better workplace solutions."""

                agent.conversation.append(
                    {"role": "assistant", "content": closing_message}
                )
                # print(f"Assistant: {closing_message}")
                await manager.send_message(closing_message, user_id)

                # Generate and save report after conversation is complete
                print("\nGenerating employee report...")
                report = report_generator.run(user_id, knowledge_graph, issues, agent.conversation)
                print(f"Successfully generated report for employee {user_id}")

                # Save report to database
                try:
                    db = next(get_db())
                    
                    # Create consolidated report data
                    report_data = {
                        "full_report": report,
                        "conversation_summary": {
                            "issues_discussed": list(agent.explored_issues.keys()),
                            "root_causes": agent.root_causes,
                            "themes": list(agent.themes)
                        },
                        "recommendations": [
                            line.strip() for line in solutions.split('\n') 
                            if line.strip().startswith('•')
                        ],
                        "metrics": {
                            "vibe_trend": knowledge_graph.nodes[f"{user_id}_vibe"]["trend"],
                            "performance_rating": knowledge_graph.nodes.get(f"{user_id}_performance", {}).get("rating"),
                            "avg_work_hours": knowledge_graph.nodes.get(f"{user_id}_activity", {}).get("avg_work_hours")
                        }
                    }
                    
                    # Create new report entry
                    db_report = EmployeeReport(
                        employee_id=user_id,
                        report_content=report_data
                    )
                    
                    db.add(db_report)
                    db.commit()
                    print(f"Report saved to database for employee {user_id}")
                    
                except Exception as e:
                    print(f"Error saving report to database: {e}")

                conversation_complete = True
                print("Conversation complete. All issues explored.")
                await manager.send_message("Thank you for your time!", user_id)
            else:
                # Generate next question based on updated conversation history
                next_question = agent.generate_question(agent.conversation[-6:])

                # Add to conversation
                agent.conversation.append(
                    {"role": "assistant", "content": next_question}
                )
                # print(f"Assistant: {next_question}")
                await manager.send_message(next_question, user_id)

            # await manager.send_message("Heyyy, how's it going?", user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")
