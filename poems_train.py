import tensorflow as tf
import numpy as np
import collections as collections
import os

model_prefix = 'poems'
model_dir = 'model/'
file_path = "poems.txt"
begin_token = 'B'
end_token = 'E'
batch_size = 64
rnn_size = 64
num_layers = 2
keep_prob = 0.5
learning_rate = 0.1
epochs = 50

# 训练模型
def load_poems(file_path):
    poems = []
    with open(file_path, mode='r', encoding='utf-8') as f:
        for line in f.readlines():
            try:
                split = line.strip().split(':')
                content = split[len(split) - 1]
                content = content.replace(' ', '')
                if '_' in content or '(' in content or '（' in content or '《' in content or '[' in content or \
                                begin_token in content or end_token in content:
                    continue
                if len(content) < 5 or len(content) > 79:
                    continue
                content = begin_token + content + end_token
                poems.append(content)
            except ValueError as e:
                pass
    poems = sorted(poems, key=lambda l : len(line))
    print('poems count is %s' % (len(poems)))
    return poems


def process_poems(poems):
    all_words = []
    for poem in poems:
        all_words += [word for word in poem]

    # 统计每个字的频数
    count = collections.Counter(all_words)
    sort = sorted(count.items(), key=lambda x: -x[1])
    # 解压sort
    words, _ = zip(*sort)
    words = words[:len(words)] + (' ',)
    # 创建一个字典，key:文字,value:序号  将
    dict_words = dict(zip(words, range(len(words))))
    # 以序号的形式表示诗
    vector = [list(map(lambda word: dict_words.get(word, len(words)), poem)) for poem in poems]
    return words, dict_words, vector


def generate_batch(batch_size, vector, dict_words):
    # 一个epochs有多少个batch_size
    num = len(vector) / batch_size
    data_x = []
    data_y = []
    for i in range(num):
        start_index = i * batch_size
        end_index = start_index + batch_size

        batch_poems = vector[start_index:end_index]
        length = max(map(len, batch_poems))
        x = np.full((batch_size, length), dict_words[' '], np.int32)
        for row in range(batch_size):
            x[row, :len(batch_poems[row])] = batch_poems[row]
        y = np.copy(x)
        # y_data = x_data去掉第一列
        y[:, :-1] = x[:, 1:]
        data_x.append(x)
        data_y.append(y)
    return data_x, data_y


def rnn_model(input_data, output_data, vector_length):
    end_points = {}
    # lstm_cell = tf.contrib.rnn.BasicLSTMCell(rnn_size, state_is_tuple=True)
    lstm = tf.nn.rnn_cell.BasicLSTMCell(rnn_size, state_is_tuple=True)
    # cell = tf.nn.rnn_cell.MultiRNNCell([lstm] * num_layers, state_is_tuple=True)
    cell = tf.contrib.rnn.MultiRNNCell([lstm] * num_layers, state_is_tuple=True)
    # 初始化状态，全是0的向量
    if output_data is not None:
        initial_state = cell.zero_state(batch_size, tf.float32)
    else:
        initial_state = cell.zero_state(1, tf.float32)

    with tf.device("/cpu:0"):
        embedding = tf.get_variable('embedding', initializer=tf.random_uniform([vector_length + 1, rnn_size], -1.0, 1.0))
        inputs = tf.nn.embedding_lookup(embedding, input_data)
        if output_data is not None:
            inputs = tf.nn.dropout(inputs, keep_prob)

    outputs, last_state = tf.nn.dynamic_rnn(cell=cell, inputs=inputs, initial_state=initial_state)
    output = tf.reshape(outputs, [-1, rnn_size])

    weights = tf.Variable(tf.truncated_normal([rnn_size, vector_length + 1]))
    bias = tf.Variable(tf.zeros([vector_length + 1]))
    logits = tf.nn.bias_add(tf.matmul(output, weights), bias)

    if output_data is not None:
        reshape = tf.reshape(output_data, [-1])
        labels = tf.one_hot(reshape, depth=vector_length + 1)
        # softmax + 交叉熵
        loss = tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=logits)

        total_loss = tf.reduce_mean(loss)
        # 动态设置学习率
        lr = tf.train.exponential_decay(learning_rate, tf.Variable(0), 100, 0.96, staircase=True)
        # 梯度下降优化器
        train_op = tf.train.AdamOptimizer(lr).minimize(total_loss)

        end_points['initial_state'] = initial_state
        end_points['output'] = output
        end_points['train_op'] = train_op
        end_points['total_loss'] = total_loss
        end_points['loss'] = loss
        end_points['last_state'] = last_state
    else:
        prediction = tf.nn.softmax(logits)

        end_points['initial_state'] = initial_state
        end_points['last_state'] = last_state
        end_points['prediction'] = prediction

    return end_points

def run_training():
    # 加载训练数据
    poems = load_poems(file_path)
    # 处理数据
    words, dict_words, vector = process_poems(poems)
    # 批量处理,获取输入
    data_x, data_y = generate_batch(batch_size, vector, dict_words)

    input_data = tf.placeholder(tf.int32, [batch_size, None])
    output_data = tf.placeholder(tf.int32, [batch_size, None])
    # RNN神经网络
    end_points = rnn_model(input_data, output_data, len(vector))

    saver = tf.train.Saver(tf.global_variables())
    init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
    with tf.Session() as sess:
        sess.run(init_op)
        start_epoch = 0
        checkpoint = tf.train.latest_checkpoint(model_dir)
        if checkpoint:
            saver.restore(sess, checkpoint)
            print("## restore from the checkpoint {0}".format(checkpoint))
            start_epoch += int(checkpoint.split('-')[-1])

        writer = tf.summary.FileWriter('/Users/fupeng/Development/workspace/poems/log', sess.graph)

        print('## start training...')
        try:
            for epoch in range(start_epoch, epochs):
                n = 0
                chunk = len(vector) // batch_size
                for batch in range(chunk):
                    loss, _, _ = sess.run([
                        end_points['total_loss'],
                        end_points['last_state'],
                        end_points['train_op']
                    ], feed_dict={input_data: data_x[n], output_data: data_y[n]})
                    n += 1
                    print('batch: %d, training loss: %.6f' % (batch, loss))
                if epoch % 10 == 0:
                    saver.save(sess, os.path.join(model_dir, model_prefix), global_step=epoch)
        except KeyboardInterrupt:
            saver.save(sess, os.path.join(model_dir, model_prefix), global_step=epoch)
            writer.close()

def main(_):
    run_training()


if __name__ == '__main__':
    tf.app.run()
