import yaml
import logging
from src.factory_sim_dx.engine import SimulationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    logging.info("Starting FactorySimDX Simulator...")
    
    # Load configuration
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
        
    engine = SimulationEngine(config)
    engine.setup()
    engine.run()
    
    logging.info("Simulation complete. Data generated in /output.")

if __name__ == "__main__":
    main()
