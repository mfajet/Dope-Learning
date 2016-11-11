import tensorflow as tf
import midi
import numpy as np
import collections
import math

midiFile = midi.read_midifile('Dope-Learning-master/midik/1080-01.mid')
#print midiFile
tracks = midiFile[1:len(midiFile)]
#First track 
#print len(tracks[0])

#NoteEvent
#print tracks[0][0]

#event = tracks[0][0]

#get the note, can find out which one it is from table
#note = event.pitch

#print note

track0 = tracks[0]
track0 = track0[0:len(track0)-1]
for i in range(len(track0)):
	noteEvent = track0[i]
	track0[i] = (noteEvent.pitch, noteEvent.tick)

notes = list()

#print len(track0)
#for i in range(0, len(track0)-1, 2):
#	noteEvent = tracks[0][i]
#	notes.append(noteEvent.pitch)

#print notes

counter = collections.Counter(track0)
count_pairs = sorted(counter.items(), key = lambda x: (-x[1], x[0]))
notes, _ = list(zip(*count_pairs))
notes_to_id = dict(zip(notes, range(len(notes))))
vocab_size = len(notes_to_id)

train_notes_ids = [notes_to_id[note] for note in track0]

batch_size = 5
num_steps = 5
hidden_size = 128
embed_sz = 128
learning_rate = 0.0001

inpt = tf.placeholder(tf.int32, [batch_size, num_steps])
output = tf.placeholder(tf.int32, [batch_size, num_steps])
keep_prob = tf.placeholder(tf.float32)

E = tf.Variable(tf.random_uniform([vocab_size, embed_sz], -1.0, 1.0))
embd = tf.nn.embedding_lookup(E, inpt)

lstm = tf.nn.rnn_cell.BasicLSTMCell(hidden_size, state_is_tuple = True)
num_layers = 2
cell = tf.nn.rnn_cell.MultiRNNCell([lstm]*num_layers, state_is_tuple=True)
init_state_0 = tf.placeholder(tf.float32, [None, hidden_size])
init_state_1 = tf.placeholder(tf.float32, [None, hidden_size])
init_state_2 = tf.placeholder(tf.float32, [None, hidden_size])
init_state_3 = tf.placeholder(tf.float32, [None, hidden_size])
firstTuple = tf.nn.rnn_cell.LSTMStateTuple(init_state_0, init_state_1)
secondTuple = tf.nn.rnn_cell.LSTMStateTuple(init_state_2, init_state_3)
init_state = [firstTuple, secondTuple]
W1 = tf.Variable(tf.truncated_normal([hidden_size, vocab_size], stddev = 0.1))
B1 = tf.Variable(tf.random_uniform([vocab_size], -1.0, 1.0))

new_embeddings = tf.nn.dropout(embd, keep_prob)
outputs, state = tf.nn.dynamic_rnn(cell, new_embeddings, initial_state = init_state)
firstState = state[0][0]
secondState = state[0][1]
thirdState = state[1][0]
fourthState = state[1][1]
reshapedOutput = tf.reshape(outputs, [batch_size*num_steps, hidden_size])
logits = tf.matmul(reshapedOutput, W1)+B1

loss = tf.nn.seq2seq.sequence_loss_by_example([logits], [tf.reshape(output, [-1])], [tf.ones([batch_size*num_steps])])
loss = tf.reduce_sum(loss)
loss = loss/batch_size
train_step = tf.train.AdamOptimizer(learning_rate).minimize(loss)

num_epochs = 50
init = tf.initialize_all_variables()
sess = tf.Session()
sess.run(init)

for i in range(num_epochs):
	print ("Epoch %d!!!" % (i+1))	
	total_error = 0.0
	x = 0
	count = 0
	state1 = sess.run(lstm.zero_state(batch_size, tf.float32))
	state2 = sess.run(lstm.zero_state(batch_size, tf.float32))
	while((x+batch_size*num_steps) < len(train_notes_ids)):
		count += num_steps
		inputs = train_notes_ids[x:x+batch_size*num_steps]
		inputs = np.reshape(inputs, [batch_size, num_steps])
		outputs = train_notes_ids[x+1:x+batch_size*num_steps+1]
		outputs = np.reshape(outputs, [batch_size, num_steps])
		x += batch_size*num_steps
		feed = {inpt: inputs, output: outputs, keep_prob: 0.5, init_state_0: state1[0], init_state_1: state1[1], init_state_2: state2[0], init_state_3: state2[1]}
		err, state1[0], state1[1], state2[0], state2[1], _ = sess.run([loss, firstState, secondState, thirdState, fourthState, train_step], feed) 
		total_error += err
		print math.exp(total_error/count)
		