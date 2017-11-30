import argparse, os, json
from AlphaGoZero.Network.main import Network
from AlphaGoZero.reinforcement_learning.sequential.optimization import optimize
from AlphaGoZero.reinforcement_learning.sequential.evaluator import evaluate
from AlphaGoZero.reinforcement_learning.sequential.selfplay import selfplay
from AlphaGoZero.reinforcement_learning.sequential.util import get_current_time


def main():
    """ File structure: The program uses 'data/models', 'data/selfplay/' and 'data/evaluations' as defaults.
        data/models contains the folders of tensorflow models, where the model names are time strings
        data/selfplay contains folders, who was once the best player. The folders contains sgf files ,pkl files generated from the selfplay.
        data/evaluations contains evaluation matches, whose names are concatenated from the player's name

        Metainfo are stored in data/config.json, please do not delete if it exists.
        Format: A dictionary with keys:
        'models': a list of strings of model names, ascending order in time
        'best_model': the name of the best model
        'selfplay': a list of model names that has selfplay data available in the selfplay folder, ascending order in time
        'should_selfplay': a bool indicating whether the selfplay data of the current best model is completed, False if it is.

    """
    parser = argparse.ArgumentParser(description='Reinforcement Learning trainer')
    parser.add_argument("--directory", "-d", help="Folder to store generated models and data", default='data')
    parser.add_argument("--iteration", "-i", help="Number of steps to train the NN", default=100)
    args = parser.parse_args()

    # Check if there is data in the location
    if os.path.exists(os.path.join(args.directory, 'models')) and os.path.exists(
            os.path.join(args.directory, 'selfplay')):
        # Check configuration file
        assert os.path.isfile(os.path.join(args.directory,
                                           'config.json')), \
            'Files found but config is missing, please consider add one manually'
        with open(os.path.join(args.directory, 'config.json')) as data:
            rl_info = json.load(data)
    else:
        # Initialize models from scratch

        # Create necessary folders
        if not os.path.exists(args.directory):
            os.makedirs(args.directory)
        os.makedirs(os.path.join(args.directory, 'models'))
        os.makedirs(os.path.join(args.directory, 'selfplay'))

        # Create config dictionary
        rl_info = {'models': [], 'selfplay': [], 'should_selfplay': True}

        # Create the first random model
        random_model = Network()
        random_model_name = get_current_time()
        random_model.save(os.path.join(args.directory, 'models', random_model_name))
        # Since this is the only model, it is the best
        rl_info['models'].append(random_model_name)
        rl_info['best_model'] = random_model_name

    # Evaluation folder is not important
    if not os.path.exists(os.path.join(args.directory, 'evaluations')):
        os.makedirs(os.path.join(args.directory, 'evaluations'))

    # Main Pipeline loop
    for t in range(args.iteration):
        if rl_info['should_selfplay']:
            # Generate selfplay data and save to a h5 file
            selfplay(rl_info['best_model'], base_dir=args.directory)
            rl_info['selfplay'].append(rl_info['best_model'])
            rl_info['should_selfplay'] = False

            # Use the recent (several) best selfplay data to optimize
            # Optimize takes a list of model names and loads the most recent model. It returns the newly created model.
            new_model_name = optimize(rl_info['selfplay'][-25:], rl_info['models'][-1], base_dir=args.directory)
            rl_info['models'].append(new_model_name)

            # Evaluate the newly created model with the current best one
            best_defeated = evaluate(rl_info['best'], new_model_name, base_dir=args.directory)
            if best_defeated:
                rl_info['best_model'] = new_model_name
            rl_info['should_selfplay'] = True

            if __name__ == '__main__':
                main()