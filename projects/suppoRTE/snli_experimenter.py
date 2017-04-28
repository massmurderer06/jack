#creates bash commands for experiments with varying hyperparams.
import os
import sys
import itertools
import logging
import argparse
import numpy as np

#JTRPATH = '/Users/tdmeeste/workspace/jtr'
JTRPATH = '/users/tdmeeste/workspace/jtr'

LOGPATH = os.path.join('.', 'logs')
TBPATH = os.path.join('.', 'tb')

def cartesian_product(dicts):
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))

def summary(configuration):
    #not mentioning at the moment:
    # 'lowercase', 'vocab_max_size', 'vocab_min_freq', 'tensorboard_folder', 'train_pretrained',
    # 'hidden_dim', 'eval_batch_size', 'seed', 'logfile', 'write_metrics_to', 'jtr_path'
    keys2mention = ['pretrain', 'lowercase', 'batch_size', 'learning_rate', 'l2', 'dropout',
                    'epochs', 'debug', 'debug_examples']
    kvs = [(k, configuration[k]) for k in keys2mention if k in configuration]
    return '_'.join([('%s=%s' % (k, str(v))) for (k, v) in kvs])

def to_logfile(c, path, tag='experiment', ext='log'):
    outfile = os.path.join(path, "%s.%s.%s" % (tag, summary(c), ext))
    return outfile


def to_cmd(c, tag, log_path, tensorboard_path, which_gpu=None):
    snli_baseline = os.path.join(JTRPATH, 'projects', 'suppoRTE', 'snli_baseline.py')
    command = 'python3 {}' \
                ' --vocab_max_size {}' \
                ' --vocab_min_freq {}' \
                ' --hidden_dim {}' \
                ' --batch_size {}' \
                ' --eval_batch_size {}' \
                ' --learning_rate {}' \
                ' --l2 {}' \
                ' --dropout {}' \
                ' --epochs {}' \
                ' --seed {}' \
                ' --debug_examples {}' \
                ''.format(snli_baseline,
                          c['vocab_max_size'],
                          c['vocab_min_freq'],
                          c['hidden_dim'],
                          c['batch_size'],
                          c['eval_batch_size'],
                          c['learning_rate'],
                          c['l2'],
                          c['dropout'],
                          c['epochs'],
                          c['seed'],
                          c['debug_examples']
                          )

    if c['debug']:
        command += ' --debug'
    if c['lowercase']:
        command += ' --lowercase'
    if c['pretrain']:
        command += ' --pretrain'
    if c['train_pretrained']:
        command += ' --train_pretrained'

    command += ' --jtr_path {}'.format(JTRPATH)
    command += ' --tensorboard_path {}'.format(os.path.join(tensorboard_path, summary(c)))
    command += ' --write_metrics_to {}'.format(to_logfile(c, log_path, tag=tag, ext='metrics'))

    if which_gpu is not None:
        command = 'CUDA_VISIBLE_DEVICES={} {}'.format(which_gpu, command)

    return command


def main():

    hyperparam_space = dict(
        debug=[False],
        lowercase=[False],
        pretrain=[True],
        train_pretrained=[False],
        debug_examples=[100],
        vocab_max_size=[sys.maxsize],
        vocab_min_freq=[1],
        hidden_dim=[100],
        batch_size=[1024],
        eval_batch_size=[1024],
        learning_rate=[1.e-3, 1.e-2],
        l2=[0, 1.e-6, 1.e-5],
        dropout=[0.5, .6, .4, 0],
        epochs=[50],
        seed=[1337]
    )

    parser = argparse.ArgumentParser(description='Baseline SNLI model experiments')
    parser.add_argument('--tag', default="test", help="tag for the current experiment")
    parser.add_argument('--gpu', nargs='*', default=[None], type=int,
                        help='ids of gpus that get a separate run file (e.g. --gpu 0 1)')
    parser.add_argument('--log_path', default=LOGPATH, help='path for execution and metrics logs')
    parser.add_argument('--tensorboard_path', default=TBPATH, help='path for tensorboard logs')
    args = parser.parse_args()
    tag = args.tag
    gpus = list(args.gpu)
    log_path = args.log_path
    tensorboard_path = args.tensorboard_path

    if not os.path.exists(log_path):
        os.makedirs(log_path)
    if not os.path.exists(tensorboard_path):
        os.makedirs(tensorboard_path)

    configs = cartesian_product(hyperparam_space)
    config_chunks = [list(a) for a in np.array_split(list(configs), len(gpus))]

    #kill running python3 processes
    #print("ps aux | grep python3 | awk '{print $2}' | xargs kill -9")

    for gpu, config_chunk in zip(gpus, config_chunks):
        sh_file = '%s_%s.sh'%(tag, str(gpu)) if gpu is not None else '%s.sh'%(tag)
        with open(sh_file, 'w') as fID:

            for job_id, cfg in enumerate(config_chunk):
                log_file = to_logfile(cfg, log_path, tag=tag, ext='log')
                completed = False
                if os.path.isfile(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        completed = '\ttest' in content
                if not completed:
                    line = '{} > {} 2>&1'.format(to_cmd(cfg,
                                                        tag,
                                                        log_path,
                                                        tensorboard_path,
                                                        which_gpu=gpu), log_file)
                    fID.write(line+'\n')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()




