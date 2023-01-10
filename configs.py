from copy import deepcopy
from argparse import Namespace
from pytorch_lightning.strategies import DDPStrategy

# ---------- Configs ----------
Exp_Name = 'BarcodeDet'
# ExpLogs_Dir = '/home/junjieyang/ExpLogs'

conf = Namespace(data=Namespace(), model=Namespace(), train=Namespace())

# data conf
conf.data.batch_size = 20
conf.data.num_workers = 16
# conf.data.root_dir = "/Users/yjunj/Data/Barcode-Detection-Data"
conf.data.root_dir = "/home/junjieyang/Data/Barcode-Detection-Data"

# models conf
conf.model.lr = 5e-4

# train conf
conf.train.devices = [0, 1, 2, 3, 4, 5, 6, 7]
conf.train.accelerator = 'gpu'
conf.train.strategy = DDPStrategy(find_unused_parameters=False)
conf.train.max_epochs = 400
conf.train.profiler = 'simple'
# conf.train.default_root_dir = ExpLogs_Dir
# conf.train.logger = configure_logger(ExpLogs_Dir, Exp_Name)

# ---------- Configs ----------

conf_dict = deepcopy({k: vars(v) for k, v in vars(conf).items()})
# del conf_dict['train']['plugins']
# del conf_dict['train']['logger']
