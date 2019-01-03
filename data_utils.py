#!/usr/bin/python
# -*- coding:utf-8 -*-

"""Utilities for tokenizing text, create vocabulary and so on"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gzip
import os
import re
import tarfile

from six.moves import urllib

from tensorflow.python.platform import gfile

# Special vocabulary symbols - we always put them at the start.
_PAD = b"_PAD"
_GO = b"_GO"
_EOS = b"_EOS"
_UNK = b"_UNK"
_START_VOCAB = [_PAD, _GO, _EOS, _UNK]

PAD_ID = 0
GO_ID = 1
EOS_ID = 2
UNK_ID = 3

'''
1.create_vocabulary:获取高频词汇
2.initialize_vocabulary:根据高频词汇获取vocab_id, 及其反向字典id_vocab
3.data_to_token_ids:根据vocab_id处理新来的句子
'''

#将原始文章先清洗、分词保存以留备用
# Regular expressions used to tokenize.
#表明原文在处理时似乎是没有去掉标点的;其实原文只做了以下预处理；也没有去停用词
'''
特殊字符：去除特殊字符，如：“「，」,￥,…”；
括号内的内容：如表情符，【嘻嘻】，【哈哈】
日期：替换日期标签为TAG_DATE，如：***年*月*日，****年*月，等等
超链接URL：替换为标签TAG_URL；
删除全角的英文：替换为标签TAG_NAME_EN；
替换数字：TAG_NUMBER；
在对文本进行了预处理后，准备训练语料： 我们的Source序列，是新闻的正文，待预测的Target序列是新闻的标题。
我们截取正文的分词个数到MAX_LENGTH_ENC=120个词，是为了训练的效果正文部分不宜过长。标题部分截取到MIN_LENGTH_ENC = 30，即生成标题不超过30个词
原文：https://blog.csdn.net/rockingdingo/article/details/55224282 
'''
_WORD_SPLIT = re.compile(b"([.,!?\"':;)(])")
_DIGIT_RE = re.compile(rb"\d")

def basic_tokenizer(sentence):
  #南 都 讯 记!者 刘?凡 周 昌和 任 笑 一 继 推出 日 票 后 TAG_NAME_EN 深圳 今后 将 设 地铁 TAG_NAME_EN 头 等 车厢 TAG_NAME_EN 设 坐 票制
  """Very basic tokenizer: split the sentence into a list of tokens."""
  words = []
  #将每一句的句首和句尾的空白字符(换行符)去掉，然后按空格分割
  for space_separated_fragment in sentence.strip().split():
    print('space_separated_fragment',space_separated_fragment)
    #extend() 函数用于在列表末尾一次性追加另一个序列中的多个值（用新列表扩展原来的列表)
    words.extend(re.split(_WORD_SPLIT, space_separated_fragment))
    print('words',words)#words ['南', '都', '讯', '记', '!', '者', '刘', '?', '凡', '周', '昌和'],取其中某一步的words
  return [w for w in words if w]#w不为空就返回words中的w,组合成列表sentence_split ['南', '都', '讯', '记', '!', '者', '刘', '?', '凡', '周', '昌和', '任', '笑', '一', '继', '推出',

def create_vocabulary(vocabulary_path, data_path, max_vocabulary_size,
                      tokenizer=None, normalize_digits=True):
  """Create vocabulary file (if it does not exist yet) from data file.

  Data file is assumed to contain one sentence per line. Each sentence is
  tokenized and digits are normalized (if normalize_digits is set).
  Vocabulary contains the most-frequent tokens up to max_vocabulary_size.
  We write it to vocabulary_path in a one-token-per-line format, so that later
  token in the first line gets id=0, second line gets id=1, and so on.

  Args:
    vocabulary_path: path where the vocabulary will be created.
    data_path: data file that will be used to create vocabulary.
    max_vocabulary_size: limit on the size of the created vocabulary.
    tokenizer: a function to use to tokenize each data sentence;
      if None, basic_tokenizer will be used.
    normalize_digits: Boolean; if true, all digits are replaced by 0s.
  """
  if not gfile.Exists(vocabulary_path):
    print("Creating vocabulary %s from data %s" % (vocabulary_path, data_path))
    vocab = {}  #(词，词频)对
    with gfile.GFile(data_path, mode="rb") as f:
      counter = 0
      for line in f:
        counter += 1
        if counter % 100000 == 0:
          print("  processing line %d" % counter)
        tokens = tokenizer(line) if tokenizer else basic_tokenizer(line)
        for w in tokens:
          #分词后将每个词中的数字替换为0，如果开启normalize_digits
          word = re.sub(_DIGIT_RE, b"0", w) if normalize_digits else w

          #统计每个词以及出现的次数
          if word in vocab:
            vocab[word] += 1
          else:
            vocab[word] = 1
      #开始列表相加；字段按照值排序(逆序)后，返回键的列表dict.get(key,default=None)获取键对应的值,default -- 如果指定键的值不存在时，返回该默认值值。
      vocab_list = _START_VOCAB + sorted(vocab, key=vocab.get, reverse=True)
      #前面一步表示按词频从高到低排列，下一步表示如果词汇量大于50000，则取前50000个词汇
      if len(vocab_list) > max_vocabulary_size:
        vocab_list = vocab_list[:max_vocabulary_size]
      with gfile.GFile(vocabulary_path, mode="wb") as vocab_file:
        for w in vocab_list:
          vocab_file.write(w + b"\n")

def initialize_vocabulary(vocabulary_path):
  """Initialize vocabulary from file.

  We assume the vocabulary is stored one-item-per-line, so a file:
    dog
    cat
  will result in a vocabulary {"dog": 0, "cat": 1}, and this function will
  also return the reversed-vocabulary ["dog", "cat"].

  Args:
    vocabulary_path: path to the file containing the vocabulary.

  Returns:
    a pair: the vocabulary (a dictionary mapping string to integers), and
    the reversed vocabulary (a list, which reverses the vocabulary mapping).

  Raises:
    ValueError: if the provided vocabulary_path does not exist.
  """
  if gfile.Exists(vocabulary_path):
    rev_vocab = []
    with gfile.GFile(vocabulary_path, mode="rb") as f:
      rev_vocab.extend(f.readlines())
    rev_vocab = [line.strip() for line in rev_vocab]
    vocab = dict([(x, y) for (y, x) in enumerate(rev_vocab)])
    #vocab：{"dog": 0, "cat": 1}  rev_vocab：["dog", "cat"]
    return vocab, rev_vocab
  else:
    raise ValueError("Vocabulary file %s not found.", vocabulary_path)

def sentence_to_token_ids(sentence, vocabulary,
                          tokenizer=None, normalize_digits=True):
  """Convert a string to list of integers representing token-ids.

  For example, a sentence "I have a dog" may become tokenized into
  ["I", "have", "a", "dog"] and with vocabulary {"I": 1, "have": 2,
  "a": 4, "dog": 7"} this function will return [1, 2, 4, 7].

  Args:
    sentence: the sentence in bytes format to convert to token-ids.
    vocabulary: a dictionary mapping tokens to integers.
    tokenizer: a function to use to tokenize each sentence;
      if None, basic_tokenizer will be used.
    normalize_digits: Boolean; if true, all digits are replaced by 0s.

  Returns:
    a list of integers, the token-ids for the sentence.
  """
  
  if tokenizer:
    words = tokenizer(sentence)
  else:
    words = basic_tokenizer(sentence)
  if not normalize_digits:
    #dict.get(key,default=None)获取键对应的值,default -- 如果指定键的值不存在时，返回该默认值值。
    #对于一个新句子，如果原来的词汇表中不存在该词，则返回unk_id;即未出现的词永远都对应unk_id
    return [vocabulary.get(w, UNK_ID) for w in words]
  # Normalize digits by 0 before looking words up in the vocabulary.
  return [vocabulary.get(re.sub(_DIGIT_RE, b"0", w), UNK_ID) for w in words]

#将前两个处理步骤合并到一起，处理新来的sentence
def data_to_token_ids(data_path, target_path, vocabulary_path,
                      tokenizer=None, normalize_digits=True):
  """Tokenize data file and turn into token-ids using given vocabulary file.

  This function loads data line-by-line from data_path, calls the above
  sentence_to_token_ids, and saves the result to target_path. See comment
  for sentence_to_token_ids on the details of token-ids format.

  Args:
    data_path: path to the data file in one-sentence-per-line format.
    target_path: path where the file with token-ids will be created.
    vocabulary_path: path to the vocabulary file.
    tokenizer: a function to use to tokenize each sentence;
      if None, basic_tokenizer will be used.
    normalize_digits: Boolean; if true, all digits are replaced by 0s.
  """
  if not gfile.Exists(target_path):
    print("Tokenizing data in %s" % data_path)
    vocab, _ = initialize_vocabulary(vocabulary_path)
    with gfile.GFile(data_path, mode="rb") as data_file:
      with gfile.GFile(target_path, mode="w") as tokens_file:
        counter = 0
        for line in data_file:
          counter += 1
          if counter % 100000 == 0:
            print("  tokenizing line %d" % counter)
          token_ids = sentence_to_token_ids(line, vocab, tokenizer,
                                            normalize_digits)
          tokens_file.write(" ".join([str(tok) for tok in token_ids]) + "\n")


def prepare_headline_data(data_dir, vocabulary_size, tokenizer=None):
  """Get news headline data into data_dir, create vocabularies and tokenize data.
  
  Args:
    data_dir: directory in which the data sets will be stored.
    vocabulary_size: size of the vocabulary to create and use.
    tokenizer: a function to use to tokenize each data sentence;
      if None, basic_tokenizer will be used.
  
  Returns:
    A tuple of 6 elements:
      (1) path to the token-ids for source context training data-set,
      (2) path to the token-ids for destination headline training data-set,
      (3) path to the token-ids for source context development data-set,
      (4) path to the token-ids for destination headline development data-set,
      (5) path to the src/dest vocabulary file,
      (6) path to the src/dest vocabulary file.
  """
  train_path = os.path.join(data_dir, "train")
  src_train_path = os.path.join(train_path, "content-train.txt")
  dest_train_path = os.path.join(train_path, "title-train.txt")

  dev_path = os.path.join(data_dir, "dev")
  src_dev_path = os.path.join(dev_path, "content-train.txt")
  dest_dev_path = os.path.join(dev_path, "title-train.txt")

  # Create vocabularies of the appropriate sizes.
  vocab_path = os.path.join(data_dir, "vocab")
  #取前5000个高频的词;只使用了内容中的词汇
  create_vocabulary(vocab_path, src_train_path, vocabulary_size, tokenizer)

  # Create token ids for the training data.
  src_train_ids_path = os.path.join(train_path, "content_train_id.txt")
  dest_train_ids_path = os.path.join(train_path, "title_train_id.txt")
  data_to_token_ids(src_train_path, src_train_ids_path, vocab_path, tokenizer)
  data_to_token_ids(dest_train_path, dest_train_ids_path, vocab_path, tokenizer)

  # Create token ids for the development data.
  src_dev_ids_path = os.path.join(dev_path, "content_dev_id.txt")
  dest_dev_ids_path = os.path.join(dev_path, "title_dev_id.txt")
  data_to_token_ids(src_dev_path, src_dev_ids_path, vocab_path, tokenizer)
  data_to_token_ids(dest_dev_path, dest_dev_ids_path, vocab_path, tokenizer)

  return (src_train_ids_path, dest_train_ids_path,
          src_dev_ids_path, dest_dev_ids_path,
          vocab_path, vocab_path)

if __name__=='__main__':
  with open('data/dev/content-train.txt') as file_data:
    for index,each in enumerate(file_data):
      if index>0:
        break
      sentence=each
      print('sentence\n',sentence)
      sentence_split=basic_tokenizer(sentence)
      print('sentence_split',sentence_split)
