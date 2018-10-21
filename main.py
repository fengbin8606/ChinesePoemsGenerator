import argparse

def parse_args():
    parser=argparse.ArgumentParser(description='Chinese Poems Generator AI')
    help_='Please choose to train or generate.'
    parser.add_argument('--train',dest='train',action='store_true',help=help_)
    parser.add_argument('--generate',dest='train',action='store_false',help=help_)
    parser.set_defaults(tain=True)

    args_=parser.parse_args()
    return args_

if __name__=='__main__':
    args=parse_args()
    if args.train:
        tang_poems().main(True)
    else:
        tang_poems().main(False)


