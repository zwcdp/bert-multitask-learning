import unittest
import logging
import tensorflow as tf
import tempfile
import shutil

from src.params import Params
from src.model_fn import BertMultiTask
from src.estimator import Estimator
from src.ckpt_restore_hook import RestoreCheckpointHook
from src.input_fn import train_eval_input_fn, predict_input_fn


class TestProblems(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.params = Params()
        self.params.train_epoch = 1
        self.params.prefetch = 100
        self.params.shuffle_buffer = 100
        self.test_dir = tempfile.mkdtemp()

        self.dist_trategy = tf.contrib.distribute.MirroredStrategy(
            num_gpus=int(1),
            cross_tower_ops=tf.contrib.distribute.AllReduceCrossTowerOps(
                'nccl', num_packs=int(1)))

        self.run_config = tf.estimator.RunConfig(
            train_distribute=self.dist_trategy,
            eval_distribute=self.dist_trategy,
            log_step_count_steps=self.params.log_every_n_steps)

    def train_eval_pred(self, params):
        model = BertMultiTask(params)
        model_fn = model.get_model_fn(False)
        estimator = Estimator(
            model_fn,
            model_dir=params.ckpt_dir,
            params=params,
            config=self.run_config)
        train_hook = RestoreCheckpointHook(params)

        def train_input_fn(): return train_eval_input_fn(params)
        estimator.train(
            train_input_fn,
            max_steps=params.train_steps,
            hooks=[train_hook])

        def input_fn(): return train_eval_input_fn(params, mode='eval')
        estimator.evaluate(input_fn=input_fn)

        p = estimator.predict(input_fn=input_fn)
        for _ in p:
            pass

    def test_seq2seq_tag(self):
        self.params.assign_problem(
            'weibo_fake_seq2seq_tag', gpu=1, base_dir=self.test_dir)

        self.train_eval_pred(self.params)

    def test_cls(self):
        self.params.assign_problem(
            'WeiboFakeCLS', gpu=1, base_dir=self.test_dir)

        self.train_eval_pred(self.params)

    def test_seq_tag(self):
        self.params.assign_problem(
            'weibo_fake_seq_tag', gpu=1, base_dir=self.test_dir)

        self.train_eval_pred(self.params)

    def test_pretrain(self):
        pass

    def test_lt_gru(self):
        self.params.assign_problem(
            'WeiboFakeCLS&weibo_fake_seq_tag&weibo_fake_seq2seq_tag', gpu=1, base_dir=self.test_dir)
        self.params.label_transfer = True
        self.params.label_transfer_gru = True

        self.train_eval_pred(self.params)

    def test_mutual_predict(self):
        self.params.assign_problem(
            'WeiboFakeCLS&weibo_fake_seq_tag&weibo_fake_seq2seq_tag', gpu=1, base_dir=self.test_dir)
        self.params.mutual_prediction = True
        self.train_eval_pred(self.params)

    def test_grid_transformer(self):
        self.params.assign_problem(
            'WeiboFakeCLS&weibo_fake_seq_tag&weibo_fake_seq2seq_tag', gpu=1, base_dir=self.test_dir)
        self.params.grid_transformer = True
        self.train_eval_pred(self.params)

    def test_augument_mask_lm(self):
        self.params.assign_problem(
            'WeiboFakeCLS&weibo_fake_seq_tag&weibo_fake_seq2seq_tag', gpu=1, base_dir=self.test_dir)
        self.params.augument_mask_lm = True
        self.train_eval_pred(self.params)

    def tearDown(self):
        shutil.rmtree(self.test_dir)


if __name__ == "__main__":
    tf.logging.set_verbosity(tf.logging.DEBUG)
    unittest.main()
