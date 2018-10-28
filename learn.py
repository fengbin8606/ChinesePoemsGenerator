# str ="line1-abckd \nline2-sdf \ttsdf"
# print(str.split())
import collections

model_prefix = 'poems'
model_dir = 'model/'
file_path = "111.txt"
begin_token = 'B'
end_token = 'E'
batch_size = 64
rnn_size = 64
num_layers = 2
keep_prob = 0.5
learning_rate = 0.1
epochs = 50

# 训练模型
def load_poems():
    # 用于存放处理后的所有诗歌
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
    print(line)
    print(len(line))
    print(poems)
    poems = sorted(poems, key=lambda l: len(l))
    print('poems count is %s' % (len(poems)))
    print(poems)

    all_words = []
    for poem in poems:
        all_words += [word for word in poem]

    # 统计每个字的频数
    count = collections.Counter(all_words)
    print(count.items())
    sort = sorted(count.items(), key=lambda x: -x[1])
    print(sort)
    words, num = zip(*sort)
    print(words)
    print(num)
    words = words[:len(words)] + (' ',)
    print(words)
    dict_words = dict(zip(words, range(len(words))))
    print(dict_words)
    vector = [list(map(lambda word: dict_words.get(word, len(words)), poem)) for poem in poems]
    print(vector)
    return poems

load_poems()

