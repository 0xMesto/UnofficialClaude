import json
import logging
import time
import random
from claude_api import UnofficialClaudeAPI

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name, role, browser_ws_endpoint):
        self.name = name
        self.role = role
        self.browser_ws_endpoint = browser_ws_endpoint
        self.api = None

    def initialize(self):
        logger.info(f"Initializing agent: {self.name}")
        self.api = UnofficialClaudeAPI(self.browser_ws_endpoint)
        self.api.__enter__()
        self.api.start_conversation()
        # Remove the model selection for now
        logger.info(f"Agent {self.name} initialized and ready")

    def process(self, input_data):
        logger.info(f"Agent {self.name} processing input")
        prompt = f"""You are a {self.role}. Your task is to {self.name}.

Input: {input_data}

Provide a detailed and thorough response. If you need any clarification or additional information, please ask.

Response:"""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.api.send_message(prompt)
                logger.debug(f"Agent {self.name} received response: {response[:100]}...")  # Log first 100 chars
                return response
            except Exception as e:
                logger.warning(f"Error in agent {self.name} while processing (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = random.uniform(5, 15)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    logger.error(f"Max retries reached for agent {self.name}")
                    raise

    def close(self):
        logger.info(f"Closing agent: {self.name}")
        if self.api:
            self.api.__exit__(None, None, None)
        logger.info(f"Agent {self.name} closed")

class Workflow:
    def __init__(self, goal):
        self.goal = goal
        self.agents = []
        self.browser_ws_endpoint = "ws://localhost:9222/devtools/browser/0ae2c38e-54c6-497c-b9dc-244ea216fda7"  # Replace with your actual WebSocket endpoint
        logger.info(f"Workflow initialized with goal: {goal}")

    def add_agent(self, name, role):
        agent = Agent(name, role, self.browser_ws_endpoint)
        self.agents.append(agent)
        logger.info(f"Added agent to workflow: {name} ({role})")

    def run(self):
        result = self.goal
        for agent in self.agents:
            logger.info(f"Initializing and running agent: {agent.name}")
            try:
                agent.initialize()
                result = agent.process(result)
                logger.info(f"Agent {agent.name} completed processing")
            except Exception as e:
                logger.error(f"Error occurred while running agent {agent.name}: {e}")
                logger.info(f"Skipping agent {agent.name} and continuing with next agent")
            finally:
                agent.close()
            
            delay = random.uniform(5, 15)
            logger.info(f"Waiting for {delay:.2f} seconds before next agent")
            time.sleep(delay)
        
        return result

    def export_workflow(self, filename):
        workflow_data = {
            "goal": self.goal,
            "agents": [{"name": agent.name, "role": agent.role} for agent in self.agents]
        }
        with open(filename, 'w') as f:
            json.dump(workflow_data, f, indent=2)
        logger.info(f"Workflow exported to {filename}")

def main():
    # Goal Definition
    goal = "Research and write a comprehensive report on the impact of artificial intelligence on healthcare. Include current applications, potential future developments, ethical considerations, and challenges in implementation."

    # Workflow Creation
    workflow = Workflow(goal)

    # Agent Configuration
    workflow.add_agent("plan_research_and_outline", "Research Planner")
    workflow.add_agent("conduct_in_depth_research", "AI and Healthcare Researcher")
    workflow.add_agent("analyze_ethical_implications", "Ethics Analyst")
    workflow.add_agent("compile_comprehensive_report", "Technical Writer")

    # Execution and Monitoring
    try:
        final_report = workflow.run()
        logger.info("Workflow completed successfully")
        logger.info("Final Report Summary:")
        logger.info(final_report[:500] + "...")  # Log first 500 characters of the report
        
        # Save the full report to a file
        with open("ai_healthcare_report.txt", "w") as f:
            f.write(final_report)
        logger.info("Full report saved to ai_healthcare_report.txt")

    except Exception as e:
        logger.error(f"An error occurred during workflow execution: {e}")

    # Export Workflow
    workflow.export_workflow("ai_healthcare_workflow.json")

if __name__ == "__main__":
    main()