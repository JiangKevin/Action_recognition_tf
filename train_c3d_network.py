import time
import logging
import tensorflow as tf
from dataset import Dataset
from c3d_network import C3D_Network, class_label

class Train_C3D_Network(object):

    depth = 16
    img_size = 112
    learning_rate = 0.0001
    model_save_path = './models/test_model/model.ckpt'

    def __init__(self, batch_size=20, train_step=5000, depth=16):
        self.batch_size = batch_size
        self.train_step = train_step
        self.depth = depth
        self._train_logger_init()

    def train(self):
        x = tf.placeholder(tf.float32, shape=[self.batch_size,
                                              self.depth,
                                              self.img_size,
                                              self.img_size,
                                              3])

        label = tf.placeholder(tf.float32, shape=[self.batch_size, len(class_label.keys())])
        network = C3D_Network(x, self.batch_size, dropout_prob=1, trainable=True)
        net_predict = network.contruct_graph()

        # 计算loss
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(labels=label, logits=net_predict)
        loss = tf.reduce_mean(cross_entropy)
        tf.add_to_collection('losses', loss)

        with tf.name_scope('total_loss'):
            total_loss = tf.add_n(tf.get_collection('losses'))
            tf.summary.scalar("total_loss", total_loss)

        with tf.name_scope('optimizer'):
            train_op = tf.train.AdamOptimizer(self.learning_rate).minimize(total_loss)

        with tf.name_scope('accuracy'):
            correct_prediction = tf.equal(tf.argmax(net_predict, 1), tf.argmax(label, 1))
            correct_prediction = tf.cast(correct_prediction, tf.float32)
            accuracy = tf.reduce_mean(correct_prediction)
            tf.summary.scalar("accuracy", accuracy)

        # 保存模型
        saver = tf.train.Saver()
        # tensorboard
        merged = tf.summary.merge_all()

        data = Dataset(self.batch_size, self.depth, self.img_size)

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            train_writer = tf.summary.FileWriter("./tensorboard_logs/", sess.graph)

            for step in range(1, self.train_step+1):
                train_x, train_y = data.get_next_batch()
                sess.run(train_op, feed_dict={x: train_x, label: train_y})
                summ = sess.run(merged, feed_dict={x: train_x, label: train_y})
                train_writer.add_summary(summ, global_step=step)

                if step%5 ==0:
                    res = sess.run([total_loss, accuracy], feed_dict={x: train_x, label: train_y})
                    self.train_logger.info('step:%d, accuracy: %6f, total loss: %6f' % (step, res[1], res[0]))
                if step%100 == 0:
                    save_path = saver.save(sess, self.model_save_path)
                    self.train_logger.info('model saved at', save_path)

            train_writer.close()

    def _train_logger_init(self):
        """
        初始化log日志
        :return:
        """
        self.train_logger = logging.getLogger('train')
        self.train_logger.setLevel(logging.DEBUG)

        # 添加文件输出
        log_file = './train_logs/' + time.strftime('%Y%m%d%H%M', time.localtime(time.time())) + '.logs'
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        self.train_logger.addHandler(file_handler)

        # 添加控制台输出
        consol_handler = logging.StreamHandler()
        consol_handler.setLevel(logging.DEBUG)
        consol_formatter = logging.Formatter('%(message)s')
        consol_handler.setFormatter(consol_formatter)
        self.train_logger.addHandler(consol_handler)


if __name__=="__main__":
    train = Train_C3D_Network(batch_size=20)
    train.train()